#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <memory>
#include <functional>
#include "Items.h"

// Motor Canônico de Habilidades, Árvores de Skill, Estigmas e Combos (Classic 5.0)


// .?AVSkillVertex@@
class SkillVertex {
public:
    SkillVertex() : m_skillId(0), m_tier(0), m_requiredLevel(0) {}
    SkillVertex(uint32_t id, uint32_t tier, uint32_t reqLvl)
        : m_skillId(id), m_tier(tier), m_requiredLevel(reqLvl) {}
    virtual ~SkillVertex() {}

    uint32_t GetSkillId() const { return m_skillId; }
    uint32_t GetTier() const { return m_tier; }
    uint32_t GetRequiredLevel() const { return m_requiredLevel; }

    void AddPrerequisite(uint32_t preSkillId) { m_prerequisites.push_back(preSkillId); }
    const std::vector<uint32_t>& GetPrerequisites() const { return m_prerequisites; }

private:
    uint32_t m_skillId;
    uint32_t m_tier;
    uint32_t m_requiredLevel;
    std::vector<uint32_t> m_prerequisites;
};

// .?AVSkillGraph@@
class SkillGraph {
public:
    SkillGraph();
    virtual ~SkillGraph();
    virtual const char* GetClassName() const { return "SkillGraph"; }

    bool AddVertex(const SkillVertex& vertex);
    const SkillVertex* GetVertex(uint32_t skillId) const;
    bool CanLearnSkill(uint32_t skillId, uint32_t playerLevel, const std::unordered_map<uint32_t, uint32_t>& learnedSkills) const;
    size_t GetVertexCount() const { return m_vertices.size(); }
    void Clear() { m_vertices.clear(); }

private:
    std::unordered_map<uint32_t, SkillVertex> m_vertices;
};

// .?AVChainVertex@@
class ChainVertex {
public:
    ChainVertex() : m_skillId(0), m_nextSkillId(0), m_probPercent(100), m_timeWindowMs(5000) {}
    ChainVertex(uint32_t curId, uint32_t nextId, uint32_t prob, uint32_t timeWin)
        : m_skillId(curId), m_nextSkillId(nextId), m_probPercent(prob), m_timeWindowMs(timeWin) {}
    virtual ~ChainVertex() {}

    uint32_t GetSkillId() const { return m_skillId; }
    uint32_t GetNextSkillId() const { return m_nextSkillId; }
    uint32_t GetProbability() const { return m_probPercent; }
    uint32_t GetTimeWindowMs() const { return m_timeWindowMs; }

private:
    uint32_t m_skillId;
    uint32_t m_nextSkillId;
    uint32_t m_probPercent;
    uint32_t m_timeWindowMs;
};

// .?AVChainGraph@@
class ChainGraph {
public:
    ChainGraph();
    virtual ~ChainGraph();
    virtual const char* GetClassName() const { return "ChainGraph"; }

    void AddChain(const ChainVertex& chain);
    std::vector<ChainVertex> GetNextChains(uint32_t skillId) const;
    bool HasChain(uint32_t skillId) const;
    void Clear() { m_chains.clear(); }

private:
    std::unordered_map<uint32_t, std::vector<ChainVertex>> m_chains;
};

// .?AVStigmaVertex@@
class StigmaVertex {
public:
    StigmaVertex() : m_stigmaId(0), m_slotIndex(0), m_isMajor(false), m_shardCost(0) {}
    StigmaVertex(uint32_t id, uint32_t slot, bool major, uint32_t shards)
        : m_stigmaId(id), m_slotIndex(slot), m_isMajor(major), m_shardCost(shards) {}
    virtual ~StigmaVertex() {}

    uint32_t GetStigmaId() const { return m_stigmaId; }
    uint32_t GetSlotIndex() const { return m_slotIndex; }
    bool IsMajor() const { return m_isMajor; }
    uint32_t GetShardCost() const { return m_shardCost; }

private:
    uint32_t m_stigmaId;
    uint32_t m_slotIndex;
    bool m_isMajor;
    uint32_t m_shardCost;
};

// .?AVStigmaGraph@@
class StigmaGraph {
public:
    StigmaGraph();
    virtual ~StigmaGraph();
    virtual const char* GetClassName() const { return "StigmaGraph"; }

    bool EquipStigma(uint32_t slot, const StigmaVertex& stigma);
    bool UnequipStigma(uint32_t slot);
    const StigmaVertex* GetStigma(uint32_t slot) const;
    size_t GetEquippedCount() const { return m_slots.size(); }
    void Clear() { m_slots.clear(); }

private:
    std::unordered_map<uint32_t, StigmaVertex> m_slots;
};

// UI Nodes
// .?AVUIChainNode@@
class UIChainNode {
public:
    UIChainNode() : m_skillId(0), m_remainingTimeMs(0), m_isActive(false) {}
    virtual ~UIChainNode() {}

    uint32_t m_skillId;
    uint32_t m_remainingTimeMs;
    bool m_isActive;
};

// .?AVUISkillNode@@
class UISkillNode {
public:
    UISkillNode() : m_skillId(0), m_cooldownRemainingMs(0), m_isReady(true) {}
    virtual ~UISkillNode() {}

    uint32_t m_skillId;
    uint32_t m_cooldownRemainingMs;
    bool m_isReady;
};

// .?AVUIStigmaNode@@
class UIStigmaNode {
public:
    UIStigmaNode() : m_stigmaId(0), m_slot(0), m_isLocked(false) {}
    virtual ~UIStigmaNode() {}

    uint32_t m_stigmaId;
    uint32_t m_slot;
    bool m_isLocked;
};

// .?AVIAutoSkillTestCallback@@
class IAutoSkillTestCallback {
public:
    virtual ~IAutoSkillTestCallback() {}
    virtual void OnSkillCastStart(uint32_t skillId, uint32_t castTimeMs) = 0;
    virtual void OnSkillCastSuccess(uint32_t skillId) = 0;
    virtual void OnSkillCastCancel(uint32_t skillId, uint32_t reason) = 0;
};
