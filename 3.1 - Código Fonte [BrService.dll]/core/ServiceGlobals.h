#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <cstdint>

namespace BrService {

// Telemetry & Combat Structures
struct PlayerDpsEntry {
    std::string name;
    std::string className;
    uint64_t totalDamage = 0;
    uint32_t dps = 0;
    float percentage = 0.0f;
    uint32_t critCount = 0;
    uint32_t hitCount = 0;
};

struct SkillDpsEntry {
    uint32_t skillId = 0;
    std::string skillName;
    uint64_t totalDamage = 0;
    uint32_t hits = 0;
    uint32_t crits = 0;
    uint32_t minDamage = 0;
    uint32_t maxDamage = 0;
};

struct TargetInfo {
    uint32_t targetId = 0;
    std::string name = "Sem Alvo";
    uint32_t level = 0;
    uint32_t currentHp = 0;
    uint32_t maxHp = 0;
    bool isNpc = true;
};

struct RadarMetrics {
    float burst = 75.0f;      // 0 - 100
    float sustain = 65.0f;    // 0 - 100
    float critRate = 45.0f;   // 0 - 100
    float accuracy = 98.0f;   // 0 - 100
    float efficiency = 80.0f; // 0 - 100
};

// Global References & Synchronization
extern HMODULE g_hModule;
extern std::atomic<HWND> g_gameHwnd;
extern std::atomic<bool> g_isGameActive;
extern std::atomic<bool> g_isLoadingScreen;
extern std::atomic<bool> g_isDrawerOpen;

// Network & Ping State
extern std::string g_serverIp;
extern int g_serverPort;
extern std::string g_securityToken;
extern std::atomic<int> g_currentPingMs;
extern std::atomic<int> g_pingBars;

// Combat State
extern std::recursive_mutex g_combatMutex;
extern TargetInfo g_currentTarget;
extern RadarMetrics g_currentRadar;
extern std::vector<PlayerDpsEntry> g_playerRankings;
extern std::vector<SkillDpsEntry> g_skillBreakdown;
extern std::vector<float> g_fibonacciCurve; // Burst progression normalized
extern std::atomic<uint64_t> g_totalBattleDamage;
extern std::atomic<uint32_t> g_totalBattleDps;
extern std::atomic<uint32_t> g_battleDurationSeconds;
extern std::atomic<bool> g_isCombatActive;

// Shugo Console State
extern std::atomic<float> g_cvarFov;
extern std::atomic<float> g_cvarCamMax;
extern std::atomic<int> g_cvarMaxFps;
extern std::atomic<bool> g_cvarTripleBuffering;
extern std::atomic<bool> g_cvarAnisotropic;

// HWNDs of Layered Windows
extern HWND g_hPingHudWnd;
extern HWND g_hDrawerModalWnd;

void ResetCombatSession();
void AddCombatEvent(const std::string& attacker, const std::string& target, uint32_t skillId,
                    const std::string& skillName, uint32_t damage, bool isCrit, bool isHeal,
                    uint32_t targetCurHp, uint32_t targetMaxHp, uint32_t targetLevel);

} // namespace BrService
