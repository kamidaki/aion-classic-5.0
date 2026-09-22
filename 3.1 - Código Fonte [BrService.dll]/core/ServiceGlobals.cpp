#include "ServiceGlobals.h"
#include <algorithm>
#include <cmath>

namespace BrService {

HMODULE g_hModule = nullptr;
std::atomic<HWND> g_gameHwnd(nullptr);
std::atomic<bool> g_isGameActive(true);
std::atomic<bool> g_isLoadingScreen(false);
std::atomic<bool> g_isDrawerOpen(false);

std::atomic<bool> g_isInWorld(false);
std::atomic<bool> g_isAdmin(false);
std::atomic<uint32_t> g_onlineCount(0);

std::atomic<int> g_drawerW(460);
std::atomic<int> g_drawerH(580);
std::atomic<int> g_drawerOpacity(255);
std::atomic<bool> g_compactView(false);
std::atomic<bool> g_hideConsoleSection(false);
std::atomic<bool> g_drawerPinned(true);

std::atomic<bool> g_featConsole(true);
std::atomic<bool> g_featFreeFly(true);
std::atomic<bool> g_featPingUi(true);
std::atomic<bool> g_featDpsMeterUI(true);
std::atomic<bool> g_featModel3D(true);
std::atomic<bool> g_featFov(true);
std::atomic<bool> g_featCamMax(true);
std::atomic<bool> g_featFpsUnlock(true);
std::atomic<bool> g_featComboUi(true);

std::atomic<bool> g_comboVisible(true);
std::atomic<float> g_comboOpacity(1.0f);
std::atomic<float> g_comboScale(1.0f);
std::atomic<float> g_comboPosNormX(0.80f);
std::atomic<float> g_comboPosNormY(0.50f);
std::atomic<int>   g_drawerPosX(-1);
std::atomic<int>   g_drawerPosY(-1);

std::string g_clientLang = "BRA";

std::string g_serverIp = "127.0.0.1";
int g_serverPort = 2106;
std::string g_securityToken = "#@br!classic50_token_2026#";
std::atomic<int> g_currentPingMs(11);
std::atomic<int> g_pingBars(4);

std::vector<PingHistoryEntry> g_pingHistory;
std::mutex g_pingHistoryMutex;

void AddPingHistory(int pingMs) {
    if (pingMs <= 0) return;
    std::lock_guard<std::mutex> lock(g_pingHistoryMutex);
    uint64_t now = GetTickCount64();
    g_pingHistory.push_back({ pingMs, now });
    // Retain only entries from the last 60 minutes (3,600,000 ms)
    uint64_t cutoff = (now > 3600000ULL) ? (now - 3600000ULL) : 0;
    while (!g_pingHistory.empty() && g_pingHistory.front().timestampMs < cutoff) {
        g_pingHistory.erase(g_pingHistory.begin());
    }
}

std::recursive_mutex g_combatMutex;
TargetInfo g_currentTarget;
RadarMetrics g_currentRadar;
std::vector<PlayerDpsEntry> g_playerRankings;
std::vector<SkillDpsEntry> g_skillBreakdown;
std::vector<CombatTimelineEntry> g_combatTimeline;
std::vector<float> g_dpsHistory;
std::atomic<uint64_t> g_totalBattleDamage(0);
std::atomic<uint64_t> g_totalDamageDealt(0);
std::atomic<uint64_t> g_totalDamageReceived(0);
std::atomic<uint32_t> g_totalBattleDps(0);
std::atomic<uint32_t> g_totalDealtDps(0);
std::atomic<uint32_t> g_battleDurationSeconds(0);
std::atomic<bool> g_isCombatActive(false);
std::vector<CombatSession> g_combatHistory;

std::atomic<float> g_cvarFov(75.0f);
std::atomic<float> g_cvarCamMax(25.0f);
std::atomic<int> g_cvarMaxFps(144);
std::atomic<bool> g_cvarTripleBuffering(true);
std::atomic<bool> g_cvarAnisotropic(true);

HWND g_hPingHudWnd = nullptr;
HWND g_hDrawerModalWnd = nullptr;

static ULONGLONG s_sessionStartTick = 0;

static std::string GetCurrentTimeStr() {
    SYSTEMTIME st = {};
    GetLocalTime(&st);
    char buf[16];
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d", st.wHour, st.wMinute, st.wSecond);
    return std::string(buf);
}

void ResetCombatSession() {
    std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

    // Salvar sessão atual no histórico antes de limpar
    if (g_isCombatActive.load() && (g_totalDamageDealt.load() > 0 || g_totalDamageReceived.load() > 0)) {
        CombatSession snap;
        snap.startTime = GetCurrentTimeStr();
        snap.totalDealt = g_totalDamageDealt.load();
        snap.totalReceived = g_totalDamageReceived.load();
        snap.dps = g_totalDealtDps.load();
        snap.durationSec = g_battleDurationSeconds.load();
        snap.skills = g_skillBreakdown;
        snap.timeline = g_combatTimeline;
        g_combatHistory.push_back(std::move(snap));
        if (g_combatHistory.size() > 5) {
            g_combatHistory.erase(g_combatHistory.begin());
        }
    }

    g_playerRankings.clear();
    g_skillBreakdown.clear();
    g_combatTimeline.clear();
    g_dpsHistory.clear();
    g_totalBattleDamage = 0;
    g_totalDamageDealt = 0;
    g_totalDamageReceived = 0;
    g_totalBattleDps = 0;
    g_totalDealtDps = 0;
    g_battleDurationSeconds = 0;
    g_isCombatActive = false;
    s_sessionStartTick = 0;
}

void AddCombatEvent(const std::string& attacker, const std::string& target, uint32_t skillId,
                    const std::string& skillName, uint32_t damage, bool isCrit, bool isHeal,
                    uint32_t targetCurHp, uint32_t targetMaxHp, uint32_t targetLevel,
                    const std::string& timeStr) {
    if (damage == 0 && !isHeal) return;

    // Self-target guard: nunca contar dano cujo attacker == target (próprio jogador)
    if (!attacker.empty() && !target.empty() && attacker == target) return;

    std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

    // Determinar direção do dano:
    // isIncoming = true quando o target é o próprio jogador (dano recebido)
    // isIncoming = false quando o attacker é o próprio jogador (dano causado)
    // Heurística: se attacker == "Voce" ou attacker vazio => outgoing
    bool isIncoming = false;
    if (!attacker.empty()) {
        std::string lAttacker = attacker;
        std::transform(lAttacker.begin(), lAttacker.end(), lAttacker.begin(), ::tolower);
        // Se o alvo do evento é "Voce"/"you"/empty e o attacker é outdo, é incoming
        if (!target.empty()) {
            std::string lTarget = target;
            std::transform(lTarget.begin(), lTarget.end(), lTarget.begin(), ::tolower);
            if (lTarget == "voce" || lTarget == "you" || lTarget == "player" || lTarget == "eu") {
                isIncoming = true;
            }
        }
    }

    // Record to Combat Timeline (retain last 100 events)
    CombatTimelineEntry tEntry;
    tEntry.timeStr = timeStr.empty() ? "00:00:00" : timeStr;
    tEntry.attacker = attacker.empty() ? "Jogador" : attacker;
    tEntry.target = target;
    tEntry.skillId = skillId;
    tEntry.skillName = skillName.empty() ? "Auto Attack" : skillName;
    tEntry.damage = damage;
    tEntry.isCrit = isCrit;
    tEntry.isHeal = isHeal;
    tEntry.isIncoming = isIncoming;
    if (g_combatTimeline.size() >= 100) {
        g_combatTimeline.erase(g_combatTimeline.begin());
    }
    g_combatTimeline.push_back(tEntry);

    if (!g_isCombatActive.load()) {
        g_isCombatActive = true;
        s_sessionStartTick = GetTickCount64();
    }

    // Update duration
    ULONGLONG now = GetTickCount64();
    uint32_t durationSec = static_cast<uint32_t>((now - s_sessionStartTick) / 1000);
    if (durationSec == 0) durationSec = 1;
    g_battleDurationSeconds = durationSec;

    if (!isHeal) {
        if (!isIncoming) {
            // Dano causado pelo player no alvo
            g_totalDamageDealt += damage;
            g_totalBattleDamage = g_totalDamageDealt.load(); // manter compat legado
            g_totalDealtDps = static_cast<uint32_t>(g_totalDamageDealt.load() / durationSec);
            g_totalBattleDps = g_totalDealtDps.load();
        } else {
            // Dano recebido pelo player
            g_totalDamageReceived += damage;
        }
    }

    // Update target (apenas quando é dano outgoing)
    if (!isIncoming && !target.empty()) {
        g_currentTarget.hasTarget = true;
        g_currentTarget.name = target;
        g_currentTarget.currentHp = targetCurHp;
        g_currentTarget.maxHp = targetMaxHp > 0 ? targetMaxHp : 100;
        g_currentTarget.level = targetLevel;
    }

    // Skill breakdown e player rankings apenas para dano outgoing
    if (!isIncoming && !isHeal) {
        std::string attName = attacker.empty() ? "Voce" : attacker;
        bool foundPlayer = false;
        for (auto& p : g_playerRankings) {
            if (p.name == attName) {
                p.totalDamage += damage;
                p.dps = static_cast<uint32_t>(p.totalDamage / durationSec);
                p.hitCount++;
                if (isCrit) p.critCount++;
                foundPlayer = true;
                break;
            }
        }
        if (!foundPlayer) {
            PlayerDpsEntry entry;
            entry.name = attName;
            entry.className = "Gladiador";
            entry.totalDamage = damage;
            entry.dps = damage / durationSec;
            entry.hitCount = 1;
            entry.critCount = isCrit ? 1 : 0;
            g_playerRankings.push_back(entry);
        }

        std::sort(g_playerRankings.begin(), g_playerRankings.end(),
            [](const PlayerDpsEntry& a, const PlayerDpsEntry& b) {
                return a.totalDamage > b.totalDamage;
            });

        uint64_t maxPlayerDmg = g_playerRankings.front().totalDamage;
        for (auto& p : g_playerRankings) {
            p.percentage = maxPlayerDmg > 0 ? (float)p.totalDamage / (float)maxPlayerDmg * 100.0f : 0.0f;
        }

        std::string sName = skillName.empty() ? ("Ataque Basico #" + std::to_string(skillId)) : skillName;
        bool foundSkill = false;
        for (auto& s : g_skillBreakdown) {
            if (s.skillId == skillId || (skillId == 0 && s.skillName == sName)) {
                s.totalDamage += damage;
                s.hits++;
                if (isCrit) s.crits++;
                if (damage < s.minDamage || s.minDamage == 0) s.minDamage = damage;
                if (damage > s.maxDamage) s.maxDamage = damage;
                foundSkill = true;
                break;
            }
        }
        if (!foundSkill) {
            SkillDpsEntry s;
            s.skillId = skillId;
            s.skillName = sName;
            s.totalDamage = damage;
            s.hits = 1;
            s.crits = isCrit ? 1 : 0;
            s.minDamage = damage;
            s.maxDamage = damage;
            g_skillBreakdown.push_back(s);
        }

        float currentDps = (float)g_totalDealtDps.load();
        if (g_dpsHistory.size() >= 30) {
            g_dpsHistory.erase(g_dpsHistory.begin());
        }
        g_dpsHistory.push_back(currentDps);
    }

    // Update Radar Metrics
    if (!g_playerRankings.empty()) {
        const auto& mainP = g_playerRankings.front();
        g_currentRadar.crit = mainP.hitCount > 0 ? ((float)mainP.critCount / mainP.hitCount * 100.0f) : 65.0f;
        g_currentRadar.block = 45.0f + (float)((g_totalBattleDps.load() / 200) % 40);
        g_currentRadar.dodge = 50.0f + (float)((durationSec * 3) % 40);
        g_currentRadar.resist = 55.0f + (float)((g_totalBattleDamage.load() / 5000) % 35);
    }
}

static inline bool IsValidUserPointer(uintptr_t addr) {
#ifdef _WIN64
    return addr >= 0x10000 && addr <= 0x00007FFFFFFEFFFF;
#else
    return addr >= 0x10000 && addr <= 0x7FFEFFFF;
#endif
}

uint32_t GetLocalPlayerObjectId() {
    uintptr_t hG = (uintptr_t)GetModuleHandleA("Game.dll");
    if (!hG) return 0;
    __try {
        uintptr_t addr = hG + 0xECDDC8;
        static const uintptr_t pOffsets[] = { 0x70, 0x10, 0x20 };
        for (int i = 0; i < 3; ++i) {
            if (!IsValidUserPointer(addr)) return 0;
            addr = *(uintptr_t*)addr;
            if (!IsValidUserPointer(addr)) return 0;
            addr += pOffsets[i];
        }
        if (!IsValidUserPointer(addr)) return 0;
        uintptr_t pPlayer = *(uintptr_t*)addr;
        if (!IsValidUserPointer(pPlayer)) return 0;
        uintptr_t pPE = *(uintptr_t*)(pPlayer + 0x378);
        if (!IsValidUserPointer(pPE)) return 0;
        return *(uint32_t*)(pPE + 0x24);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static bool ReadPlayerNameRaw(char* outBuf, size_t bufSize) {
    if (!outBuf || bufSize == 0) return false;
    outBuf[0] = '\0';
    uintptr_t hG = (uintptr_t)GetModuleHandleA("Game.dll");
    if (!hG) return false;
    __try {
        uintptr_t addr = hG + 0xECDDC8;
        static const uintptr_t pOffsets[] = { 0x70, 0x10, 0x20 };
        for (int i = 0; i < 3; ++i) {
            if (!IsValidUserPointer(addr)) return false;
            addr = *(uintptr_t*)addr;
            if (!IsValidUserPointer(addr)) return false;
            addr += pOffsets[i];
        }
        if (!IsValidUserPointer(addr)) return false;
        uintptr_t pPlayer = *(uintptr_t*)addr;
        if (!IsValidUserPointer(pPlayer)) return false;
        uintptr_t pPE = *(uintptr_t*)(pPlayer + 0x378);
        if (!IsValidUserPointer(pPE)) return false;
        wchar_t* pN = (wchar_t*)(pPE + 0x46);
        if (pN && wcslen(pN) > 0) {
            WideCharToMultiByte(CP_UTF8, 0, pN, -1, outBuf, (int)bufSize, nullptr, nullptr);
            return true;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
    return false;
}

std::string GetLocalPlayerName() {
    char buf[128] = { 0 };
    if (ReadPlayerNameRaw(buf, sizeof(buf))) {
        return std::string(buf);
    }
    return "";
}

} // namespace BrService

