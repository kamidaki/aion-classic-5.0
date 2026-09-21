#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <vector>
#include <cstdint>

namespace BrService {

struct StoredCombatEvent {
    uint64_t timestamp = 0;
    std::string attacker;
    std::string target;
    uint32_t skillId = 0;
    std::string skillName;
    uint32_t damage = 0;
    bool isCrit = false;
    bool isHeal = false;
};

class CombatDb {
public:
    static bool Initialize();
    static void Shutdown();

    static void RecordEventAsync(const StoredCombatEvent& ev);
    static void PurgeOldRecords(int maxAgeHours = 24);

private:
    static DWORD WINAPI WorkerThread(LPVOID param);
};

} // namespace BrService
