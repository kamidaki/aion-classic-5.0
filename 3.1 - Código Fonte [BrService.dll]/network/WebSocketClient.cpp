#include "WebSocketClient.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../core/I18n.h"
#include "../database/CombatDb.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../model3d/CryModelBridge.h"
#include "../combo/ComboUI.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <atomic>
#include <chrono>
#include <mutex>
#include <vector>

namespace BrService {

static HANDLE s_hThread = nullptr;
static std::atomic<bool> s_running(false);
static std::atomic<bool> s_connected(false);
static std::string s_wsHost = "127.0.0.1";
static int s_wsPort = 2130;
static SOCKET s_currentSock = INVALID_SOCKET;
static std::mutex s_sendMutex;

bool WebSocketClient::SendTextMessage(const std::string& msg) {
    std::lock_guard<std::mutex> lock(s_sendMutex);
    if (s_currentSock == INVALID_SOCKET || !s_connected.load()) return false;

    // RFC 6455 Client Masked Text Frame
    std::vector<uint8_t> frame;
    frame.push_back(0x81); // FIN + Text

    size_t len = msg.size();
    if (len <= 125) {
        frame.push_back(static_cast<uint8_t>(len | 0x80)); // masked
    } else if (len <= 65535) {
        frame.push_back(126 | 0x80);
        frame.push_back(static_cast<uint8_t>((len >> 8) & 0xFF));
        frame.push_back(static_cast<uint8_t>(len & 0xFF));
    } else {
        frame.push_back(127 | 0x80);
        for (int i = 7; i >= 0; --i) {
            frame.push_back(static_cast<uint8_t>((len >> (i * 8)) & 0xFF));
        }
    }

    uint8_t mask[4] = { 0x4B, 0x9A, 0x2C, 0xF1 };
    frame.insert(frame.end(), mask, mask + 4);

    for (size_t i = 0; i < len; ++i) {
        frame.push_back(static_cast<uint8_t>(msg[i]) ^ mask[i % 4]);
    }

    int sent = send(s_currentSock, reinterpret_cast<const char*>(frame.data()), static_cast<int>(frame.size()), 0);
    return sent > 0;
}

static std::string ExtractJsonString(const std::string& json, const std::string& key) {
    std::string pattern = "\"" + key + "\":\"";
    size_t pos = json.find(pattern);
    if (pos == std::string::npos) return "";
    pos += pattern.length();
    size_t end = json.find("\"", pos);
    if (end == std::string::npos) return "";
    return json.substr(pos, end - pos);
}

static uint32_t ExtractJsonUint(const std::string& json, const std::string& key, uint32_t fallback = 0) {
    std::string pattern = "\"" + key + "\":";
    size_t pos = json.find(pattern);
    if (pos == std::string::npos) return fallback;
    pos += pattern.length();
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    try {
        return static_cast<uint32_t>(std::stoul(json.substr(pos)));
    } catch (...) {
        return fallback;
    }
}

static bool ExtractJsonBool(const std::string& json, const std::string& key, bool fallback = false) {
    std::string pattern = "\"" + key + "\":";
    size_t pos = json.find(pattern);
    if (pos == std::string::npos) return fallback;
    pos += pattern.length();
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    if (json.compare(pos, 4, "true") == 0) return true;
    if (json.compare(pos, 5, "false") == 0) return false;
    return fallback;
}

bool WebSocketClient::Start(const std::string& host, int port) {
    if (s_running.load()) return true;

    if (!host.empty()) s_wsHost = host;
    if (port > 0) s_wsPort = port;

    s_running = true;
    s_hThread = CreateThread(nullptr, 0, ClientThread, nullptr, 0, nullptr);
    return s_hThread != nullptr;
}

void WebSocketClient::Stop() {
    s_running = false;
    s_connected = false;
    {
        std::lock_guard<std::mutex> lock(s_sendMutex);
        if (s_currentSock != INVALID_SOCKET) {
            closesocket(s_currentSock);
            s_currentSock = INVALID_SOCKET;
        }
    }
    if (s_hThread) {
        WaitForSingleObject(s_hThread, 2000);
        CloseHandle(s_hThread);
        s_hThread = nullptr;
    }
}

bool WebSocketClient::IsConnected() {
    return s_connected.load();
}

void WebSocketClient::HandleIncomingPayload(const std::string& payload) {
    // 1. Player State Updates
    if (payload.find("\"PLAYER_STATE\"") != std::string::npos) {
        bool inGame = ExtractJsonBool(payload, "inGame", false);
        bool isLoading = ExtractJsonBool(payload, "isLoading", false);
        bool isAdmin = ExtractJsonBool(payload, "isAdmin", false);
        uint32_t onlineCount = ExtractJsonUint(payload, "onlineCount", 0);

        g_isInWorld = inGame;
        g_isLoadingScreen = isLoading;
        g_isAdmin = isAdmin;
        g_onlineCount = onlineCount;

        LogInfo("WebSocket PLAYER_STATE recebido: inGame=%d, isLoading=%d, isAdmin=%d, online=%u",
                inGame, isLoading, isAdmin, onlineCount);

        if (!inGame || isLoading) {
            PingHudUI::Hide();
            DrawerModalUI::Hide();
        } else {
            PingHudUI::Show();
            PingHudUI::Repaint();
        }
        return;
    }

    // 2. Real-Time Target Selection Updates
    if (payload.find("\"TARGET_INFO\"") != std::string::npos) {
        bool hasTarget = ExtractJsonBool(payload, "hasTarget", false);
        std::lock_guard<std::recursive_mutex> lock(g_combatMutex);
        if (!hasTarget) {
            g_currentTarget.hasTarget = false;
            g_currentTarget.targetId = 0;
            g_currentTarget.name.clear();
            g_currentTarget.level = 0;
            g_currentTarget.currentHp = 0;
            g_currentTarget.maxHp = 0;
            g_currentTarget.modelId = 0;
            g_currentTarget.isNpc = false;
            g_currentTarget.rating.clear();
            g_currentTarget.race.clear();
            CryModelBridge::SetTargetEntity(0, 0, 0, 0.0f);
        } else {
            g_currentTarget.hasTarget = true;
            g_currentTarget.targetId = ExtractJsonUint(payload, "targetId", 0);
            g_currentTarget.name = ExtractJsonString(payload, "name");
            g_currentTarget.level = ExtractJsonUint(payload, "level", 0);
            g_currentTarget.currentHp = ExtractJsonUint(payload, "currentHp", 0);
            g_currentTarget.maxHp = ExtractJsonUint(payload, "maxHp", 100);
            g_currentTarget.isNpc = ExtractJsonBool(payload, "isNpc", true);
            g_currentTarget.modelId = ExtractJsonUint(payload, "modelId", 0);
            g_currentTarget.aiName = ExtractJsonString(payload, "aiName");
            g_currentTarget.attack = ExtractJsonUint(payload, "attack", 0);
            g_currentTarget.pdef = ExtractJsonUint(payload, "pdef", 0);
            g_currentTarget.mres = ExtractJsonUint(payload, "mres", 0);
            g_currentTarget.rating = ExtractJsonString(payload, "rating");
            if (g_currentTarget.rating.empty()) g_currentTarget.rating = "NORMAL";
            g_currentTarget.race = ExtractJsonString(payload, "race");
            if (g_currentTarget.race.empty()) g_currentTarget.race = "NONE";

            // OBRIGATORIAMENTE E INEGOCIAVELMENTE SÓ EXIBE O MODELO 3D QUANDO O ALVO FOR NPC (NUNCA JOGADOR OU A SI MESMO)
            if (g_featModel3D.load() && g_currentTarget.isNpc && g_currentTarget.modelId > 0) {
                CryModelBridge::SetTargetNpc(g_currentTarget.modelId);
            } else {
                CryModelBridge::SetTargetEntity(0, 0, 0, 0.0f);
            }
        }

        if (g_hDrawerModalWnd && IsWindow(g_hDrawerModalWnd) && g_isDrawerOpen.load()) {
            InvalidateRect(g_hDrawerModalWnd, nullptr, FALSE);
        }
        return;
    }

    // 3. COMBO_EVENT
    if (payload.find("\"COMBO_EVENT\"") != std::string::npos) {
        std::string ev = ExtractJsonString(payload, "event");
        int hits = (int)ExtractJsonUint(payload, "hits", 0);
        int hitDamage = (int)ExtractJsonUint(payload, "hitDamage", 0);
        int totalDamage = (int)ExtractJsonUint(payload, "totalDamage", 0);
        int timeoutMs = (int)ExtractJsonUint(payload, "timeoutMs", 3000);
        std::string title = ExtractJsonString(payload, "title");
        g_ComboUI.OnEvent(ev, hits, title, hitDamage, totalDamage, timeoutMs);
        return;
    }

    // 4. ACTION_POINT_GAINED (Pontos de Participação)
    if (payload.find("\"ACTION_POINT_GAINED\"") != std::string::npos) {
        int pts = (int)ExtractJsonUint(payload, "pointsEarned", 1);
        if (IsEnglish()) {
            g_ComboUI.ShowNotification("+" + std::to_string(pts) + " Participation Point!");
        } else {
            g_ComboUI.ShowNotification("+" + std::to_string(pts) + " Ponto de Participação!");
        }
        return;
    }

    // 5. ACTION_NEW_RECORD
    if (payload.find("\"ACTION_NEW_RECORD\"") != std::string::npos) {
        int rec = (int)ExtractJsonUint(payload, "recordHits", 0);
        if (IsEnglish()) {
            g_ComboUI.ShowNotification("New Combo Record: " + std::to_string(rec) + " Hits!");
        } else {
            g_ComboUI.ShowNotification("Novo Recorde de Combo: " + std::to_string(rec) + " Golpes!");
        }
        return;
    }

    // 6. ACTION_ABNORMAL_STATE
    if (payload.find("\"ACTION_ABNORMAL_STATE\"") != std::string::npos) {
        std::string stateName = ExtractJsonString(payload, "stateName");
        std::string stateType = ExtractJsonString(payload, "stateType");
        NotificationType nType = NotificationType::Normal;
        if (stateType == "STUN") nType = NotificationType::AbnormalStun;
        else if (stateType == "PARALYZE") nType = NotificationType::AbnormalParalyzed;
        else if (stateType == "SILENCE") nType = NotificationType::AbnormalSilenced;
        else if (stateType == "SNARE" || stateType == "ROOT") nType = NotificationType::AbnormalBlink;
        else if (stateType == "POISON") nType = NotificationType::AbnormalPoison;
        else if (stateType == "BLEED") nType = NotificationType::AbnormalBleed;
        else if (stateType == "FEAR") nType = NotificationType::AbnormalFear;
        else if (stateType == "SLEEP") nType = NotificationType::AbnormalSleep;
        else if (stateType == "BLIND") nType = NotificationType::AbnormalBlind;
        else if (stateType == "DISEASE") nType = NotificationType::AbnormalDisease;
        else if (stateType == "CURSE") nType = NotificationType::AbnormalCurse;
        else if (stateType == "CONFUSE") nType = NotificationType::AbnormalConfuse;
        g_ComboUI.ShowAbnormalState(stateName, nType);
        return;
    }

    // 3. Combat Event (Damage/Heal Telemetry)
    if (payload.find("\"COMBAT_EVENT\"") == std::string::npos &&
        payload.find("\"type\":\"damage\"") == std::string::npos) {
        return;
    }

    std::string timeStr = ExtractJsonString(payload, "time");
    std::string attacker = ExtractJsonString(payload, "attacker");
    if (attacker.empty()) attacker = ExtractJsonString(payload, "attackerName");
    std::string target = ExtractJsonString(payload, "target");
    if (target.empty()) target = ExtractJsonString(payload, "targetName");
    std::string skillName = ExtractJsonString(payload, "skillName");

    uint32_t skillId = ExtractJsonUint(payload, "skillId", 0);
    uint32_t damage = ExtractJsonUint(payload, "damage", 0);
    bool isCrit = ExtractJsonBool(payload, "isCrit", false);
    bool isHeal = ExtractJsonBool(payload, "isHeal", false);
    uint32_t targetCurHp = ExtractJsonUint(payload, "targetHp", 0);
    uint32_t targetMaxHp = ExtractJsonUint(payload, "targetMaxHp", 100);
    uint32_t targetLevel = ExtractJsonUint(payload, "targetLevel", 55);

    uint32_t targetId = ExtractJsonUint(payload, "targetId", 0);
    uint32_t modelId = ExtractJsonUint(payload, "modelId", 0);
    bool isNpc = ExtractJsonBool(payload, "isNpc", true);
    std::string rating = ExtractJsonString(payload, "rating");
    std::string race = ExtractJsonString(payload, "race");

    // Atualiza dados autoritativos do alvo APENAS se o alvo atual for o mesmo da telemetria de combate
    if (targetId > 0 && g_currentTarget.hasTarget && g_currentTarget.targetId == targetId) {
        std::lock_guard<std::recursive_mutex> lock(g_combatMutex);
        g_currentTarget.currentHp = targetCurHp;
        if (targetMaxHp > 0) g_currentTarget.maxHp = targetMaxHp;
        if (targetLevel > 0) g_currentTarget.level = targetLevel;
        if (modelId > 0) g_currentTarget.modelId = modelId;
        g_currentTarget.isNpc = isNpc;
        if (!rating.empty()) g_currentTarget.rating = rating;
        if (!race.empty()) g_currentTarget.race = race;
        if (g_featModel3D.load() && g_currentTarget.isNpc && g_currentTarget.modelId > 0) {
            CryModelBridge::SetTargetNpc(g_currentTarget.modelId);
        }
    }

    // Update in-memory telemetry and timeline
    AddCombatEvent(attacker, target, skillId, skillName, damage, isCrit, isHeal, targetCurHp, targetMaxHp, targetLevel, timeStr);

    // Record to SQLite local history
    auto now = std::chrono::system_clock::now();
    uint64_t ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();

    StoredCombatEvent ev;
    ev.timestamp = ms;
    ev.attacker = attacker;
    ev.target = target;
    ev.skillId = skillId;
    ev.skillName = skillName;
    ev.damage = damage;
    ev.isCrit = isCrit;
    ev.isHeal = isHeal;
    CombatDb::RecordEventAsync(ev);

    // Trigger modal redraw if visible
    if (g_hDrawerModalWnd && IsWindow(g_hDrawerModalWnd) && g_isDrawerOpen.load()) {
        InvalidateRect(g_hDrawerModalWnd, nullptr, FALSE);
    }
}

DWORD WINAPI WebSocketClient::ClientThread(LPVOID /*param*/) {
    LogInfo("WebSocketClient iniciado visando ws://%s:%d/telemetry", s_wsHost.c_str(), s_wsPort);

    while (s_running.load()) {
        SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (sock == INVALID_SOCKET) {
            Sleep(3000);
            continue;
        }

        sockaddr_in saddr = {};
        saddr.sin_family = AF_INET;
        saddr.sin_port = htons(static_cast<u_short>(s_wsPort));
        saddr.sin_addr.s_addr = inet_addr(s_wsHost.c_str());
        if (saddr.sin_addr.s_addr == INADDR_NONE || saddr.sin_addr.s_addr == 0) {
            saddr.sin_addr.s_addr = inet_addr("127.0.0.1");
        }

        // Connect timeout
        DWORD timeout = 2500;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));

        if (connect(sock, (sockaddr*)&saddr, sizeof(saddr)) != 0) {
            closesocket(sock);
            Sleep(3000);
            continue;
        }

        // Send WebSocket Handshake
        char handshake[512];
        snprintf(handshake, sizeof(handshake),
                 "GET /telemetry HTTP/1.1\r\n"
                 "Host: %s:%d\r\n"
                 "Upgrade: websocket\r\n"
                 "Connection: Upgrade\r\n"
                 "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                 "Sec-WebSocket-Version: 13\r\n"
                 "X-Token: %s\r\n\r\n",
                 s_wsHost.c_str(), s_wsPort, g_securityToken.c_str());

        send(sock, handshake, (int)strlen(handshake), 0);

        char recvBuf[2048] = { 0 };
        int bytes = recv(sock, recvBuf, sizeof(recvBuf) - 1, 0);
        if (bytes <= 0 || strstr(recvBuf, "101 Switching Protocols") == nullptr) {
            closesocket(sock);
            Sleep(3000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(s_sendMutex);
            s_currentSock = sock;
        }
        s_connected = true;
        LogInfo("WebSocket conectado com sucesso ao emulador em %s:%d!", s_wsHost.c_str(), s_wsPort);

        // Auto-identificar o jogador local se ja conectado no mundo
        uint32_t lastIdentifiedCharId = GetLocalPlayerObjectId();
        if (lastIdentifiedCharId > 0) {
            std::string myName = GetLocalPlayerName();
            SendTextMessage("IDENTIFY:{\"charId\":" + std::to_string(lastIdentifiedCharId) + ",\"name\":\"" + myName + "\"}");
            LogInfo("WebSocket: Enviado IDENTIFY inicial charId=%u (%s)", lastIdentifiedCharId, myName.c_str());
        }

        SendTextMessage(std::string("SET_COMBO_VISIBILITY:") + (g_comboVisible.load() ? "1" : "0"));

        // Frame read loop com buffer continuo de alta performance (sem erase por frame)
        std::vector<uint8_t> frameBuffer;
        ULONGLONG lastIdentifyCheckTick = GetTickCount64();

        while (s_running.load()) {
            uint8_t chunk[4096];
            int n = recv(sock, (char*)chunk, sizeof(chunk), 0);
            if (n <= 0) {
                int err = WSAGetLastError();
                if (err == WSAETIMEDOUT) {
                    // Periodic identity check
                    ULONGLONG now = GetTickCount64();
                    if (now - lastIdentifyCheckTick >= 2000) {
                        lastIdentifyCheckTick = now;
                        uint32_t curId = GetLocalPlayerObjectId();
                        if (curId > 0 && curId != lastIdentifiedCharId) {
                            lastIdentifiedCharId = curId;
                            std::string myName = GetLocalPlayerName();
                            SendTextMessage("IDENTIFY:{\"charId\":" + std::to_string(curId) + ",\"name\":\"" + myName + "\"}");
                            LogInfo("WebSocket: Sincronizado IDENTIFY charId=%u (%s)", curId, myName.c_str());
                        }
                    }
                    continue;
                }
                break; // Disconnected
            }

            // Periodic identity check upon network activity
            ULONGLONG now = GetTickCount64();
            if (now - lastIdentifyCheckTick >= 2000) {
                lastIdentifyCheckTick = now;
                uint32_t curId = GetLocalPlayerObjectId();
                if (curId > 0 && curId != lastIdentifiedCharId) {
                    lastIdentifiedCharId = curId;
                    std::string myName = GetLocalPlayerName();
                    SendTextMessage("IDENTIFY:{\"charId\":" + std::to_string(curId) + ",\"name\":\"" + myName + "\"}");
                    LogInfo("WebSocket: Sincronizado IDENTIFY charId=%u (%s)", curId, myName.c_str());
                }
            }

            frameBuffer.insert(frameBuffer.end(), chunk, chunk + n);

            size_t readOffset = 0;
            while (frameBuffer.size() - readOffset >= 2) {
                uint8_t b1 = frameBuffer[readOffset + 0];
                uint8_t b2 = frameBuffer[readOffset + 1];
                int opcode = b1 & 0x0F;
                bool masked = (b2 & 0x80) != 0;
                uint64_t payloadLen = b2 & 0x7F;
                size_t headerLen = 2;

                if (payloadLen == 126) {
                    if (frameBuffer.size() - readOffset < 4) break;
                    payloadLen = (frameBuffer[readOffset + 2] << 8) | frameBuffer[readOffset + 3];
                    headerLen = 4;
                } else if (payloadLen == 127) {
                    if (frameBuffer.size() - readOffset < 10) break;
                    payloadLen = 0;
                    for (int i = 0; i < 8; i++) {
                        payloadLen = (payloadLen << 8) | frameBuffer[readOffset + 2 + i];
                    }
                    headerLen = 10;
                }

                size_t maskLen = masked ? 4 : 0;
                if (frameBuffer.size() - readOffset < headerLen + maskLen + payloadLen) break;

                uint8_t mask[4] = { 0 };
                if (masked) {
                    memcpy(mask, &frameBuffer[readOffset + headerLen], 4);
                }

                std::string payloadText;
                payloadText.resize(static_cast<size_t>(payloadLen));

                const uint8_t* payloadBytes = &frameBuffer[readOffset + headerLen + maskLen];
                for (size_t i = 0; i < payloadLen; i++) {
                    uint8_t b = payloadBytes[i];
                    if (masked) b ^= mask[i % 4];
                    payloadText[i] = (char)b;
                }

                readOffset += (headerLen + maskLen + payloadLen);

                if (opcode == 0x1) { // Text frame
                    HandleIncomingPayload(payloadText);
                } else if (opcode == 0x8) { // Close frame
                    closesocket(sock);
                    sock = INVALID_SOCKET;
                    break;
                }
            }

            if (readOffset > 0) {
                if (readOffset >= frameBuffer.size()) {
                    frameBuffer.clear();
                } else {
                    frameBuffer.erase(frameBuffer.begin(), frameBuffer.begin() + readOffset);
                }
            }

            if (sock == INVALID_SOCKET) break;
        }

        s_connected = false;
        {
            std::lock_guard<std::mutex> lock(s_sendMutex);
            s_currentSock = INVALID_SOCKET;
        }
        if (sock != INVALID_SOCKET) {
            closesocket(sock);
        }
        LogInfo("WebSocket desconectado. Tentando reconectar em 3s...");
        Sleep(3000);
    }

    return 0;
}

} // namespace BrService
