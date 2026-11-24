#pragma once
#include <cstdint>
#include <string>
#include <unordered_map>

struct ArtiData {
    uint32_t id;
    std::string name;
    uint32_t skillId;
    uint32_t requiredItemId;
    uint32_t requiredItemCount;
    uint32_t cooldownSeconds;
    uint32_t targetFaction; // 0 = Elyos, 1 = Asmodian, 2 = Balaur
};

// Tabela canônica de Artefatos do Abyss extraída do RTTI (.?AVArtiTable@@)
class ArtiTable {
public:
    ArtiTable();
    ~ArtiTable();

    bool LoadTable();
    const ArtiData* GetArtiTemplate(uint32_t id) const;

private:
    std::unordered_map<uint32_t, ArtiData> m_artifacts;
};
