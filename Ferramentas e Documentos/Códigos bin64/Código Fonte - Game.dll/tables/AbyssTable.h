#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <string>

struct AbyssRankEntry {
    uint32_t rankId;
    std::string rankTitle;
    uint32_t requiredAp;
    uint32_t requiredGp;
};

// Tabela canônica de rankings do Abyss extraída do RTTI (.?AVAbyssTable@@ / .?AVAbyssRankTable@@)
class AbyssTable {
public:
    static AbyssTable& GetInstance() {
        static AbyssTable instance;
        return instance;
    }

    bool LoadTable();
    const AbyssRankEntry* GetRank(uint32_t rankId) const;

private:
    AbyssTable() : m_bLoaded(false) {}
    bool m_bLoaded;
    std::unordered_map<uint32_t, AbyssRankEntry> m_ranks;
};
