#include "SkillGraph.h"
#include "Player.h"

// SkillGraph
SkillGraph::SkillGraph() {}
SkillGraph::~SkillGraph() { Clear(); }

bool SkillGraph::AddVertex(const SkillVertex& vertex) {
    m_vertices[vertex.GetSkillId()] = vertex;
    return true;
}

const SkillVertex* SkillGraph::GetVertex(uint32_t skillId) const {
    auto it = m_vertices.find(skillId);
    return it != m_vertices.end() ? &it->second : nullptr;
}

bool SkillGraph::CanLearnSkill(uint32_t skillId, uint32_t playerLevel, const std::unordered_map<uint32_t, uint32_t>& learnedSkills) const {
    const SkillVertex* v = GetVertex(skillId);
    if (!v) return false;
    if (playerLevel < v->GetRequiredLevel()) return false;
    for (uint32_t preId : v->GetPrerequisites()) {
        if (learnedSkills.find(preId) == learnedSkills.end()) {
            return false;
        }
    }
    return true;
}

// ChainGraph
ChainGraph::ChainGraph() : SkillGraph() {}
ChainGraph::~ChainGraph() { Clear(); }

void ChainGraph::AddChain(const ChainVertex& chain) {
    m_chains[chain.GetSkillId()].push_back(chain);
}

std::vector<ChainVertex> ChainGraph::GetNextChains(uint32_t skillId) const {
    auto it = m_chains.find(skillId);
    return it != m_chains.end() ? it->second : std::vector<ChainVertex>();
}

bool ChainGraph::HasChain(uint32_t skillId) const {
    return m_chains.find(skillId) != m_chains.end();
}

bool ChainGraph::CanTriggerChain(uint32_t currentSkillId, uint32_t nextSkillId, uint8_t playerClass, uint8_t weaponType, uint32_t currentGauge) const {
    auto it = m_chains.find(currentSkillId);
    if (it == m_chains.end()) {
        return false;
    }

    bool chainExists = false;
    for (const auto& cv : it->second) {
        if (cv.GetNextSkillId() == nextSkillId) {
            chainExists = true;
            break;
        }
    }
    if (!chainExists) {
        return false;
    }

    // Validação de requisitos de combate por classe (Aion Classic 5.0)
    switch (playerClass) {
    case CLASS_THUNDERER:
        // Thunderer / Soul Reaper / Revenant: combos encadeados exigem Chainsword (DimensionSword)
        if (weaponType != WEAPON_DIMENSIONSWORD && weaponType != WEAPON_NONE) {
            return false;
        }
        break;

    case CLASS_BATTLEMASTER:
    case CLASS_STRIKER:
        // Striker / BattleMaster: combos de artes marciais exigem Gauntlet
        if (weaponType != WEAPON_GAUNTLET && weaponType != WEAPON_NONE) {
            return false;
        }
        break;

    case CLASS_LUMINES:
    case CLASS_ORCHESTRATOR:
        // Lumines / Trovador: acordes e correntes melódicas exigem Harpa
        if (weaponType != WEAPON_HARP && weaponType != WEAPON_NONE) {
            return false;
        }
        break;

    case CLASS_GUNNER:
    case CLASS_ENGINEER:
        // Gunner: Pistolas duplas ou Canhão de Éter
        if (weaponType != WEAPON_1GUN && weaponType != WEAPON_2GUN &&
            weaponType != WEAPON_AETHERCANNON && weaponType != WEAPON_NONE) {
            return false;
        }
        // Canhão não pode disparar combos se o medidor de calor estiver superaquecido (>= 100)
        if (weaponType == WEAPON_AETHERCANNON && currentGauge >= 100) {
            return false;
        }
        break;

    default:
        break;
    }

    return true;
}

// StigmaGraph
StigmaGraph::StigmaGraph() : SkillGraph() {}
StigmaGraph::~StigmaGraph() { Clear(); }

bool StigmaGraph::EquipStigma(uint32_t slot, const StigmaVertex& stigma) {
    if (slot > 12) return false; // Max 12 slots de estigma no Classic 5.0
    m_slots[slot] = stigma;
    return true;
}

bool StigmaGraph::UnequipStigma(uint32_t slot) {
    auto it = m_slots.find(slot);
    if (it != m_slots.end()) {
        m_slots.erase(it);
        return true;
    }
    return false;
}

const StigmaVertex* StigmaGraph::GetStigma(uint32_t slot) const {
    auto it = m_slots.find(slot);
    return it != m_slots.end() ? &it->second : nullptr;
}
