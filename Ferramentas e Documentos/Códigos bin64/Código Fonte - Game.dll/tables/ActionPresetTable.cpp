#include "ActionPresetTable.h"
#include "../core/GameLog.h"

bool ActionPresetTable::LoadTable() {
    GameLog_Info("ActionPresetTable::LoadTable carregando presets de acoes...");

    // Presets canônicos padrão do Aion
    m_presets[1]  = {1,  "Action_Attack",  1, 1};
    m_presets[2]  = {2,  "Action_ToggleFly", 1, 2};
    m_presets[3]  = {3,  "Action_Rest",    1, 3};
    m_presets[4]  = {4,  "Action_Jump",    1, 4};

    m_bLoaded = true;
    GameLog_Info("ActionPresetTable::LoadTable concluido (%zu presets registrados).", m_presets.size());
    return true;
}

const ActionPresetEntry* ActionPresetTable::GetPreset(uint32_t presetId) const {
    auto it = m_presets.find(presetId);
    if (it != m_presets.end()) {
        return &it->second;
    }
    return nullptr;
}

void ActionPresetTable::SetPreset(uint32_t presetId, const std::string& name, uint32_t type, uint32_t actionId) {
    m_presets[presetId] = {presetId, name, type, actionId};
}
