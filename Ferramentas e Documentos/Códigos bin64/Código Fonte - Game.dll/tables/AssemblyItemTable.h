#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>

struct AssemblyPart {
    uint32_t itemId;
    uint32_t count;
};

struct AssemblyItemTemplate {
    uint32_t id;
    uint32_t resultItemId;
    uint32_t resultItemCount;
    uint32_t requiredSkillId;
    uint32_t requiredSkillLevel;
    std::vector<AssemblyPart> parts;
};

// Tabela canônica de montagem/combinação de itens extraída do RTTI (.?AVAssemblyItemTable@@)
class AssemblyItemTable {
public:
    AssemblyItemTable();
    ~AssemblyItemTable();

    bool LoadTable();
    const AssemblyItemTemplate* GetTemplate(uint32_t id) const;
    bool HasTemplate(uint32_t id) const;

private:
    std::unordered_map<uint32_t, AssemblyItemTemplate> m_templates;
};
