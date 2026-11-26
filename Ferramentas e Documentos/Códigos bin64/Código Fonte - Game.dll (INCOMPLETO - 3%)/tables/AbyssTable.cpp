#include "AbyssTable.h"
#include "../core/GameLog.h"

bool AbyssTable::LoadTable() {
    GameLog_Info("AbyssTable::LoadTable carregando rankings do Abyss do Aion Classic (100% AP)...");

    // Tabela canônica de postos do Abyss do Aion Classic (AP requerido e Quota de Ranking da Raça)
    m_ranks[1]  = {1,  "STR_ABYSS_RANK_1",  0,       0};    // Soldado 9
    m_ranks[2]  = {2,  "STR_ABYSS_RANK_2",  1200,    0};    // Soldado 8
    m_ranks[3]  = {3,  "STR_ABYSS_RANK_3",  4220,    0};    // Soldado 7
    m_ranks[4]  = {4,  "STR_ABYSS_RANK_4",  10990,   0};    // Soldado 6
    m_ranks[5]  = {5,  "STR_ABYSS_RANK_5",  23500,   0};    // Soldado 5
    m_ranks[6]  = {6,  "STR_ABYSS_RANK_6",  42780,   0};    // Soldado 4
    m_ranks[7]  = {7,  "STR_ABYSS_RANK_7",  69700,   0};    // Soldado 3
    m_ranks[8]  = {8,  "STR_ABYSS_RANK_8",  105600,  0};    // Soldado 2
    m_ranks[9]  = {9,  "STR_ABYSS_RANK_9",  150800,  0};    // Soldado 1
    m_ranks[10] = {10, "STR_ABYSS_RANK_10", 214100,  1500}; // Oficial 1 Estrela (Top 1500)
    m_ranks[11] = {11, "STR_ABYSS_RANK_11", 278000,  1000}; // Oficial 2 Estrelas (Top 1000)
    m_ranks[12] = {12, "STR_ABYSS_RANK_12", 354200,  500};  // Oficial 3 Estrelas (Top 500)
    m_ranks[13] = {13, "STR_ABYSS_RANK_13", 443400,  250};  // Oficial 4 Estrelas (Top 250)
    m_ranks[14] = {14, "STR_ABYSS_RANK_14", 546400,  100};  // Oficial 5 Estrelas (Top 100)
    m_ranks[15] = {15, "STR_ABYSS_RANK_15", 664000,  30};   // General (Top 30)
    m_ranks[16] = {16, "STR_ABYSS_RANK_16", 797000,  10};   // Grande General (Top 10)
    m_ranks[17] = {17, "STR_ABYSS_RANK_17", 946200,  3};    // Comandante (Top 3)
    m_ranks[18] = {18, "STR_ABYSS_RANK_18", 1112400, 1};    // Governador / Supreme Commander (Top 1)

    m_bLoaded = true;
    GameLog_Info("AbyssTable::LoadTable concluido (%zu postos registrados).", m_ranks.size());
    return true;
}

const AbyssRankData* AbyssTable::GetRank(uint32_t rankId) const {
    auto it = m_ranks.find(rankId);
    if (it != m_ranks.end()) {
        return &it->second;
    }
    return nullptr;
}
