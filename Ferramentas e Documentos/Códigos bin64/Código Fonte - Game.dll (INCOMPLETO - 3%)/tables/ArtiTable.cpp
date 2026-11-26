#include "ArtiTable.h"
#include "../core/GameLog.h"

ArtiTable::ArtiTable() {
    LoadTable();
}

ArtiTable::~ArtiTable() {
    m_artifacts.clear();
}

bool ArtiTable::LoadTable() {
    m_artifacts.clear();

    // Artefatos canônicos do Reshanta (Core, Sul, Norte)
    ArtiData coreArti{};
    coreArti.id = 1;
    coreArti.name = "Hellfire Artifact";
    coreArti.skillId = 18001;
    coreArti.requiredItemId = 186000030; // Temporal Stone
    coreArti.requiredItemCount = 1;
    coreArti.cooldownSeconds = 300;
    coreArti.targetFaction = 0;
    m_artifacts[coreArti.id] = coreArti;

    ArtiData shieldArti{};
    shieldArti.id = 2;
    shieldArti.name = "Aegis Artifact";
    shieldArti.skillId = 18002;
    shieldArti.requiredItemId = 186000030;
    shieldArti.requiredItemCount = 1;
    shieldArti.cooldownSeconds = 300;
    shieldArti.targetFaction = 1;
    m_artifacts[shieldArti.id] = shieldArti;

    GameLog_Info("ArtiTable carregada com sucesso (%zu artefatos)", m_artifacts.size());
    return true;
}

const ArtiData* ArtiTable::GetArtiTemplate(uint32_t id) const {
    auto it = m_artifacts.find(id);
    if (it != m_artifacts.end()) {
        return &it->second;
    }
    return nullptr;
}
