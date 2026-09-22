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
    bool hasTarget = false;
    uint32_t targetId = 0;
    std::string name = "Sem Alvo";
    uint32_t level = 0;
    uint32_t currentHp = 0;
    uint32_t maxHp = 0;
    bool isNpc = true;
    uint32_t modelId = 0;
    std::string aiName = "general";
    uint32_t attack = 0;
    uint32_t pdef = 0;
    uint32_t mres = 0;
    std::string rating = "NORMAL"; // NORMAL, ELITE, HERO, LEGENDARY
    std::string race = "NONE";     // ELYOS, ASMODIANS, etc.
    float posX = 0.0f;
    float posY = 0.0f;
    float posZ = 0.0f;
    float yaw = 0.0f;
};

struct CombatTimelineEntry {
    std::string timeStr;
    std::string attacker;
    std::string target;
    uint32_t skillId = 0;
    std::string skillName;
    uint32_t damage = 0;
    bool isCrit = false;
    bool isHeal = false;
};

struct RadarMetrics {
    float crit = 45.0f;    // 0 - 100 (Crítico)
    float block = 30.0f;   // 0 - 100 (Bloqueio)
    float dodge = 25.0f;   // 0 - 100 (Esquiva)
    float resist = 35.0f;  // 0 - 100 (Resistência)
};

// Global References & Synchronization
extern HMODULE g_hModule;
extern std::atomic<HWND> g_gameHwnd;
extern std::atomic<bool> g_isGameActive;
extern std::atomic<bool> g_isLoadingScreen;
extern std::atomic<bool> g_isDrawerOpen;

// In-Game & Admin State (Sourced from GameServer via WebSocket)
extern std::atomic<bool> g_isInWorld;       // true ONLY after player spawns in world
extern std::atomic<bool> g_isAdmin;         // true if player accessLevel > 0
extern std::atomic<uint32_t> g_onlineCount; // online players count

// UI Customization State (Controlled via Settings Modal)
extern std::atomic<int> g_drawerW;          // console window width (default 460, min 400, max 640)
extern std::atomic<int> g_drawerH;          // console window height (default 580, min 480, max 780)
extern std::atomic<int> g_drawerOpacity;    // console opacity (default 255, min 120, max 255)
extern std::atomic<bool> g_compactView;     // compact mode (hides 3d model & radar)
extern std::atomic<bool> g_hideConsoleSection; // hide shugo graphics console, full dps meter

// Combo UI In-Game Settings & Flags
extern std::atomic<bool> g_featComboUi;        // -comboUi:enable|disable
extern std::atomic<bool> g_comboVisible;       // settings toggle (if false, hidden and participation points paused)
extern std::atomic<float> g_comboOpacity;      // 0.1f to 1.0f (default 1.0f)
extern std::atomic<float> g_comboScale;        // 0.55f to 1.60f (default 1.0f)
extern std::atomic<float> g_comboPosNormX;     // normalized X pos (default 0.80f)
extern std::atomic<float> g_comboPosNormY;     // normalized Y pos (default 0.50f)
extern std::atomic<int>   g_drawerPosX;        // custom window X pos (-1 for default)
extern std::atomic<int>   g_drawerPosY;        // custom window Y pos (-1 for default)

// Language Flag: "BRA" (Portuguese) or "ENG"/"ENU" (English)
extern std::string g_clientLang;

// Feature Control Flags (Controlled via Command-Line Parameters: -param:enable/disable)
extern std::atomic<bool> g_featConsole;       // -console:enable|disable
extern std::atomic<bool> g_featFreeFly;       // -freefly:enable|disable
extern std::atomic<bool> g_featPingUi;        // -pingUi:enable|disable
extern std::atomic<bool> g_featDpsMeterUI;    // -DpsMeterUI:enable|disable
extern std::atomic<bool> g_featModel3D;       // -Model3D:enable|disable
extern std::atomic<bool> g_featFov;           // -fov:enable|disable
extern std::atomic<bool> g_featCamMax;        // -camMax:enable|disable
extern std::atomic<bool> g_featFpsUnlock;     // -fpsUnlock:enable|disable

// Network & Ping State
extern std::string g_serverIp;
extern int g_serverPort;
extern std::string g_securityToken;
extern std::atomic<int> g_currentPingMs;
extern std::atomic<int> g_pingBars;

// Ping 60-minute latency history for Fibonacci trend sparkline
struct PingHistoryEntry {
    int pingMs;
    uint64_t timestampMs;
};
extern std::vector<PingHistoryEntry> g_pingHistory;
extern std::mutex g_pingHistoryMutex;
void AddPingHistory(int pingMs);

// Combat State
extern std::recursive_mutex g_combatMutex;
extern TargetInfo g_currentTarget;
extern RadarMetrics g_currentRadar;
extern std::vector<PlayerDpsEntry> g_playerRankings;
extern std::vector<SkillDpsEntry> g_skillBreakdown;
extern std::vector<float> g_dpsHistory; // DPS over time telemetry points
extern std::vector<CombatTimelineEntry> g_combatTimeline; // Real-time combat timeline
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
                    uint32_t targetCurHp, uint32_t targetMaxHp, uint32_t targetLevel,
                    const std::string& timeStr = "");

} // namespace BrService
