#include "AiCharTable.h"
#include "../core/GameLog.h"

bool AiCharTable::LoadTable() {
    GameLog_Info("AiCharTable::LoadTable carregando templates de NPCs e monstros...");

    // Templates canônicos de teste do Aion Classic
    m_templates[203001] = {203001, "Kalis", 10, 5000, 2000, 1, 1.5f, 6.0f};
    m_templates[203002] = {203002, "Spatalos", 50, 100000, 50000, 1, 1.5f, 6.0f};
    m_templates[700001] = {700001, "Training Dummy", 1, 999999, 0, 0, 0.0f, 0.0f};

    m_bLoaded = true;
    GameLog_Info("AiCharTable::LoadTable concluido (%zu templates registrados).", m_templates.size());
    return true;
}

const AiCharTemplate* AiCharTable::GetTemplate(uint32_t npcId) const {
    auto it = m_templates.find(npcId);
    if (it != m_templates.end()) {
        return &it->second;
    }
    return nullptr;
}
