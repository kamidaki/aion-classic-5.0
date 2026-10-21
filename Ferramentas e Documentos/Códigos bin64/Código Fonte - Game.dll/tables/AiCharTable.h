#pragma once
#include <windows.h>
#include <cstdint>
#include <unordered_map>
#include <string>

struct AiCharTemplate {
    uint32_t npcId;
    std::string npcName;
    uint32_t level;
    uint32_t maxHp;
    uint32_t maxMp;
    uint32_t aiPatternId;
    float walkSpeed;
    float runSpeed;
};

// Tabela canônica de definições e templates de personagens/NPCs extraída do RTTI (.?AVAiCharTable@@)
class AiCharTable {
public:
    static AiCharTable& GetInstance() {
        static AiCharTable instance;
        return instance;
    }

    bool LoadTable();
    const AiCharTemplate* GetTemplate(uint32_t npcId) const;

private:
    AiCharTable() : m_bLoaded(false) {}
    bool m_bLoaded;
    std::unordered_map<uint32_t, AiCharTemplate> m_templates;
};
