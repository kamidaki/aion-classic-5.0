#include "AssemblyItemTable.h"
#include "../core/GameLog.h"

AssemblyItemTable::AssemblyItemTable() {
    LoadTable();
}

AssemblyItemTable::~AssemblyItemTable() {
    m_templates.clear();
}

bool AssemblyItemTable::LoadTable() {
    m_templates.clear();

    // Registra receitas canônicas padrão de montagem
    AssemblyItemData testMorph{};
    testMorph.id = 1001;
    testMorph.resultItemId = 160000001;
    testMorph.resultItemCount = 1;
    testMorph.requiredSkillId = 30001;
    testMorph.requiredSkillLevel = 1;
    testMorph.parts.push_back({ 152000001, 3 });
    m_templates[testMorph.id] = testMorph;

    GameLog_Info("AssemblyItemTable carregada com sucesso (%zu templates)", m_templates.size());
    return true;
}

const AssemblyItemData* AssemblyItemTable::GetTemplate(uint32_t id) const {
    auto it = m_templates.find(id);
    if (it != m_templates.end()) {
        return &it->second;
    }
    return nullptr;
}

bool AssemblyItemTable::HasTemplate(uint32_t id) const {
    return m_templates.find(id) != m_templates.end();
}
