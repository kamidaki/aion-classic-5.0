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
    std::string rating = "NORMAL";
    std::string race = "NONE";
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
    bool isIncoming = false;
};

struct CombatSession {
    std::string startTime;
    uint64_t totalDealt = 0;
    uint64_t totalReceived = 0;
    uint32_t dps = 0;
    uint32_t durationSec = 0;
    std::vector<SkillDpsEntry> skills;
    std::vector<CombatTimelineEntry> timeline;
};

struct RadarMetrics {
    float crit = 45.0f;
    float block = 30.0f;
    float dodge = 25.0f;
    float resist = 35.0f;
};

// Global References & Synchronization
extern HMODULE g_hModule;
extern std::atomic<HWND> g_gameHwnd;
extern std::atomic<bool> g_isGameActive;
extern std::atomic<bool> g_isLoadingScreen;
extern std::atomic<bool> g_isDrawerOpen;

// In-Game & Admin State (Sourced 100% from GameServer via WebSocket)
extern std::atomic<bool> g_isInWorld;
extern std::atomic<bool> g_isAdmin;
extern std::atomic<uint32_t> g_localPlayerId;
extern std::string g_localPlayerName;
void SetLocalPlayerIdentity(uint32_t id, const std::string& name);
uint32_t GetLocalPlayerId();
std::string GetLocalPlayerName();

// UI Customization State
extern std::atomic<int> g_drawerW;
extern std::atomic<int> g_drawerH;
extern std::atomic<int> g_drawerOpacity;
extern std::atomic<bool> g_compactView;
extern std::atomic<bool> g_drawerPinned;

// Combo UI In-Game Settings & Flags
extern std::atomic<bool>  g_featComboUi;
extern std::atomic<bool>  g_comboVisible;
extern std::atomic<float> g_comboOpacity;
extern std::atomic<float> g_comboScale;
extern std::atomic<float> g_comboPosNormX;
extern std::atomic<float> g_comboPosNormY;
extern std::atomic<int>   g_drawerPosX;
extern std::atomic<int>   g_drawerPosY;

// Language Flag
extern std::string g_clientLang;

// Feature Control Flags
extern std::atomic<bool> g_featPingUi;
extern std::atomic<bool> g_featDpsMeterUI;

// Network & Ping State
extern std::string g_serverIp;
extern int g_serverPort;
extern std::string g_securityToken;
extern std::atomic<int> g_currentPingMs;
extern std::atomic<int> g_pingBars;

// Ping history
struct PingHistoryEntry {
    int pingMs;
    uint64_t timestampMs;
};
extern std::vector<PingHistoryEntry> g_pingHistory;
extern std::mutex g_pingHistoryMutex;
void AddPingHistory(int pingMs);

// Combat State (100% sourced from WebSocket GameServer events)
extern std::recursive_mutex g_combatMutex;
extern TargetInfo g_currentTarget;
extern RadarMetrics g_currentRadar;
extern std::vector<PlayerDpsEntry> g_playerRankings;
extern std::vector<SkillDpsEntry> g_skillBreakdown;
extern std::vector<float> g_dpsHistory;
extern std::vector<CombatTimelineEntry> g_combatTimeline;
extern std::atomic<uint64_t> g_totalBattleDamage;
extern std::atomic<uint64_t> g_totalDamageDealt;
extern std::atomic<uint64_t> g_totalDamageReceived;
extern std::atomic<uint32_t> g_totalBattleDps;
extern std::atomic<uint32_t> g_totalDealtDps;
extern std::atomic<uint32_t> g_battleDurationSeconds;
extern std::atomic<bool> g_isCombatActive;
extern std::vector<CombatSession> g_combatHistory;

// HWNDs of Layered Windows
extern HWND g_hPingHudWnd;
extern HWND g_hDrawerModalWnd;
extern std::atomic<HWND> g_hComboWnd;

void ResetCombatSession();
void AddCombatEvent(const std::string& attacker, const std::string& target, uint32_t skillId,
                    const std::string& skillName, uint32_t damage, bool isCrit, bool isHeal,
                    uint32_t targetCurHp, uint32_t targetMaxHp, uint32_t targetLevel,
                    const std::string& timeStr = "");

} // namespace BrService
