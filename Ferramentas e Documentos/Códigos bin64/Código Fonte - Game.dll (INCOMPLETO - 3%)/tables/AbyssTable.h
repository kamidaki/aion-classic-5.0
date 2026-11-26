#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <string>

typedef struct {
    uint32_t rankId;
    std::string rankTitle;
    uint32_t requiredAp;
    uint32_t quotaRankLimit;
} AbyssRankData;

// Tabela canônica de rankings do Abyss do Aion Classic (100% AP e Quotas de Posição da Raça, Zero GP)
class AbyssTable {
public:
    static AbyssTable& GetInstance() {
        static AbyssTable instance;
        return instance;
    }

    bool LoadTable();
    const AbyssRankData* GetRank(uint32_t rankId) const;

private:
    AbyssTable() : m_bLoaded(false) {}
    bool m_bLoaded;
    std::unordered_map<uint32_t, AbyssRankData> m_ranks;
};
