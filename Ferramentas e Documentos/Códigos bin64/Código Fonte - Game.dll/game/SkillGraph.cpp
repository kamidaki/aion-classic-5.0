#include "SkillGraph.h"

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
ChainGraph::ChainGraph() {}
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

// StigmaGraph
StigmaGraph::StigmaGraph() {}
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
