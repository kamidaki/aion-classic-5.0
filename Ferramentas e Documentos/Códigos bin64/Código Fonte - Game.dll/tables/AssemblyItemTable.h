#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>

struct AssemblyItemData {
    uint32_t id;
    uint32_t resultItemId;
    uint32_t resultItemCount;
    uint32_t requiredSkillId;
    uint32_t requiredSkillLevel;
    std::vector<std::pair<uint32_t, uint32_t>> parts;
};

// Tabela canônica de montagem/combinação de itens extraída do RTTI (.?AVAssemblyItemTable@@)
class AssemblyItemTable {
public:
    AssemblyItemTable();
    ~AssemblyItemTable();

    bool LoadTable();
    const AssemblyItemData* GetTemplate(uint32_t id) const;
    bool HasTemplate(uint32_t id) const;

private:
    std::unordered_map<uint32_t, AssemblyItemData> m_templates;
};
