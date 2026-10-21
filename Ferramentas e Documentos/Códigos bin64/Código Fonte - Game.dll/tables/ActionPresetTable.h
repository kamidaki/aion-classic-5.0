#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <string>

struct ActionPresetEntry {
    uint32_t presetId;
    std::string actionName;
    uint32_t actionType; // 0=Skill, 1=Emote, 2=Macro, 3=Item
    uint32_t actionId;
};

// Tabela canônica de atalhos e predefinições de ações do jogador extraída do RTTI (.?AVActionPresetTable@@)
class ActionPresetTable {
public:
    static ActionPresetTable& GetInstance() {
        static ActionPresetTable instance;
        return instance;
    }

    bool LoadTable();
    const ActionPresetEntry* GetPreset(uint32_t presetId) const;
    void SetPreset(uint32_t presetId, const std::string& name, uint32_t type, uint32_t actionId);

private:
    ActionPresetTable() : m_bLoaded(false) {}
    bool m_bLoaded;
    std::unordered_map<uint32_t, ActionPresetEntry> m_presets;
};
