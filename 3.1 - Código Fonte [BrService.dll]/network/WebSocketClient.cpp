#include "WebSocketClient.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../database/CombatDb.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <atomic>
#include <chrono>

namespace BrService {

static HANDLE s_hThread = nullptr;
static std::atomic<bool> s_running(false);
static std::atomic<bool> s_connected(false);
static std::string s_wsHost = "127.0.0.1";
static int s_wsPort = 2130;

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
    if (payload.find("\"COMBAT_EVENT\"") == std::string::npos &&
        payload.find("\"type\":\"damage\"") == std::string::npos) {
        return;
    }

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

    // Update in-memory telemetry
    AddCombatEvent(attacker, target, skillId, skillName, damage, isCrit, isHeal, targetCurHp, targetMaxHp, targetLevel);

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

        s_connected = true;
        LogInfo("WebSocket conectado com sucesso ao emulador em %s:%d!", s_wsHost.c_str(), s_wsPort);

        // Frame read loop
        std::vector<uint8_t> frameBuffer;
        while (s_running.load()) {
            uint8_t chunk[4096];
            int n = recv(sock, (char*)chunk, sizeof(chunk), 0);
            if (n <= 0) {
                int err = WSAGetLastError();
                if (err == WSAETIMEDOUT) continue;
                break; // Disconnected
            }

            frameBuffer.insert(frameBuffer.end(), chunk, chunk + n);

            while (frameBuffer.size() >= 2) {
                uint8_t b1 = frameBuffer[0];
                uint8_t b2 = frameBuffer[1];
                int opcode = b1 & 0x0F;
                bool masked = (b2 & 0x80) != 0;
                uint64_t payloadLen = b2 & 0x7F;
                size_t headerLen = 2;

                if (payloadLen == 126) {
                    if (frameBuffer.size() < 4) break;
                    payloadLen = (frameBuffer[2] << 8) | frameBuffer[3];
                    headerLen = 4;
                } else if (payloadLen == 127) {
                    if (frameBuffer.size() < 10) break;
                    payloadLen = 0;
                    for (int i = 0; i < 8; i++) {
                        payloadLen = (payloadLen << 8) | frameBuffer[2 + i];
                    }
                    headerLen = 10;
                }

                size_t maskLen = masked ? 4 : 0;
                if (frameBuffer.size() < headerLen + maskLen + payloadLen) break;

                uint8_t mask[4] = { 0 };
                if (masked) {
                    memcpy(mask, &frameBuffer[headerLen], 4);
                }

                std::string payloadText;
                payloadText.resize(static_cast<size_t>(payloadLen));

                const uint8_t* payloadBytes = &frameBuffer[headerLen + maskLen];
                for (size_t i = 0; i < payloadLen; i++) {
                    uint8_t b = payloadBytes[i];
                    if (masked) b ^= mask[i % 4];
                    payloadText[i] = (char)b;
                }

                frameBuffer.erase(frameBuffer.begin(), frameBuffer.begin() + (headerLen + maskLen + payloadLen));

                if (opcode == 0x1) { // Text frame
                    HandleIncomingPayload(payloadText);
                } else if (opcode == 0x8) { // Close frame
                    closesocket(sock);
                    sock = INVALID_SOCKET;
                    break;
                }
            }
            if (sock == INVALID_SOCKET) break;
        }

        s_connected = false;
        if (sock != INVALID_SOCKET) {
            closesocket(sock);
        }
        LogInfo("WebSocket desconectado. Tentando reconectar em 3s...");
        Sleep(3000);
    }

    return 0;
}

} // namespace BrService
