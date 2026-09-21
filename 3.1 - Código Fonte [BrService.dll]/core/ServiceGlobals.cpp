#include "ServiceGlobals.h"
#include <algorithm>
#include <cmath>

namespace BrService {

HMODULE g_hModule = nullptr;
std::atomic<HWND> g_gameHwnd(nullptr);
std::atomic<bool> g_isGameActive(true);
std::atomic<bool> g_isLoadingScreen(false);
std::atomic<bool> g_isDrawerOpen(false);

std::atomic<bool> g_featConsole(true);
std::atomic<bool> g_featFreeFly(true);
std::atomic<bool> g_featPingUi(true);
std::atomic<bool> g_featDpsMeterUI(true);
std::atomic<bool> g_featModel3D(true);
std::atomic<bool> g_featFov(true);
std::atomic<bool> g_featCamMax(true);
std::atomic<bool> g_featFpsUnlock(true);

std::string g_serverIp = "127.0.0.1";
int g_serverPort = 2106;
std::string g_securityToken = "#@br!classic50_token_2026#";
std::atomic<int> g_currentPingMs(11);
std::atomic<int> g_pingBars(4);

std::recursive_mutex g_combatMutex;
TargetInfo g_currentTarget;
RadarMetrics g_currentRadar;
std::vector<PlayerDpsEntry> g_playerRankings;
std::vector<SkillDpsEntry> g_skillBreakdown;
std::vector<float> g_fibonacciCurve = { 0.1f, 0.25f, 0.4f, 0.6f, 0.85f, 1.0f, 0.9f, 0.75f, 0.8f, 0.95f };
std::atomic<uint64_t> g_totalBattleDamage(0);
std::atomic<uint32_t> g_totalBattleDps(0);
std::atomic<uint32_t> g_battleDurationSeconds(0);
std::atomic<bool> g_isCombatActive(false);

std::atomic<float> g_cvarFov(75.0f);
std::atomic<float> g_cvarCamMax(25.0f);
std::atomic<int> g_cvarMaxFps(144);
std::atomic<bool> g_cvarTripleBuffering(true);
std::atomic<bool> g_cvarAnisotropic(true);

HWND g_hPingHudWnd = nullptr;
HWND g_hDrawerModalWnd = nullptr;

static ULONGLONG s_sessionStartTick = 0;

void ResetCombatSession() {
    std::lock_guard<std::recursive_mutex> lock(g_combatMutex);
    g_playerRankings.clear();
    g_skillBreakdown.clear();
    g_fibonacciCurve = { 0.1f, 0.2f, 0.35f, 0.55f, 0.8f, 1.0f };
    g_totalBattleDamage = 0;
    g_totalBattleDps = 0;
    g_battleDurationSeconds = 0;
    g_isCombatActive = false;
    s_sessionStartTick = 0;
}

void AddCombatEvent(const std::string& attacker, const std::string& target, uint32_t skillId,
                    const std::string& skillName, uint32_t damage, bool isCrit, bool isHeal,
                    uint32_t targetCurHp, uint32_t targetMaxHp, uint32_t targetLevel) {
    if (damage == 0 && !isHeal) return;

    std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

    if (!g_isCombatActive.load()) {
        g_isCombatActive = true;
        s_sessionStartTick = GetTickCount64();
    }

    // Update duration & total damage
    ULONGLONG now = GetTickCount64();
    uint32_t durationSec = static_cast<uint32_t>((now - s_sessionStartTick) / 1000);
    if (durationSec == 0) durationSec = 1;
    g_battleDurationSeconds = durationSec;

    if (!isHeal) {
        g_totalBattleDamage += damage;
        g_totalBattleDps = static_cast<uint32_t>(g_totalBattleDamage.load() / durationSec);
    }

    // Update target
    if (!target.empty()) {
        g_currentTarget.name = target;
        g_currentTarget.currentHp = targetCurHp;
        g_currentTarget.maxHp = targetMaxHp > 0 ? targetMaxHp : 100;
        g_currentTarget.level = targetLevel;
    }

    // Update Player Rankings
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

    // Sort player rankings by total damage descending
    std::sort(g_playerRankings.begin(), g_playerRankings.end(),
        [](const PlayerDpsEntry& a, const PlayerDpsEntry& b) {
            return a.totalDamage > b.totalDamage;
        });

    uint64_t maxPlayerDmg = g_playerRankings.front().totalDamage;
    for (auto& p : g_playerRankings) {
        p.percentage = maxPlayerDmg > 0 ? (float)p.totalDamage / (float)maxPlayerDmg * 100.0f : 0.0f;
    }

    // Update Skills Breakdown
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

    // Update Fibonacci Burst Curve (moving window of relative DPS points)
    float normalizedDps = (float)g_totalBattleDps.load();
    if (g_fibonacciCurve.size() > 20) {
        g_fibonacciCurve.erase(g_fibonacciCurve.begin());
    }
    float peak = 1.0f;
    for (float f : g_fibonacciCurve) if (f > peak) peak = f;
    g_fibonacciCurve.push_back(normalizedDps);

    // Update Radar Metrics
    if (!g_playerRankings.empty()) {
        const auto& mainP = g_playerRankings.front();
        g_currentRadar.critRate = mainP.hitCount > 0 ? ((float)mainP.critCount / mainP.hitCount * 100.0f) : 35.0f;
        g_currentRadar.burst = std::min(100.0f, (float)(g_totalBattleDps.load() % 1000) / 10.0f + 50.0f);
        g_currentRadar.sustain = std::min(100.0f, 60.0f + (float)(durationSec % 40));
        g_currentRadar.accuracy = 98.5f;
        g_currentRadar.efficiency = std::min(100.0f, (g_currentRadar.critRate * 0.4f + g_currentRadar.burst * 0.6f));
    }
}

} // namespace BrService
