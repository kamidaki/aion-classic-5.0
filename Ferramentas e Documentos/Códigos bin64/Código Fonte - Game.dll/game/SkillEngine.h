#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <chrono>
#include "CombatEngine.h"

// Enumerador canônico de Classes do Aion Classic
enum class AionPlayerClass : uint8_t {
    WARRIOR       = 0,
    GLADIATOR     = 1,
    TEMPLAR       = 2,
    SCOUT         = 3,
    ASSASSIN      = 4,
    RANGER        = 5,
    MAGE          = 6,
    SORCERER      = 7,
    SPIRIT_MASTER = 8,
    PRIEST        = 9,
    CLERIC        = 10,
    CHANTER       = 11,
    ENGINEER      = 12,
    RIDER         = 13,
    GUNNER        = 14,
    ARTIST        = 15,
    BARD          = 16,
    UNKNOWN       = 255
};

// Tipo de Estigma
enum class StigmaType : uint8_t {
    NONE     = 0,
    REGULAR  = 1, // Basic Stigma
    GREATER  = 2  // Advanced Stigma
};

// Template de Definição de Habilidade
struct SkillTemplate {
    uint32_t         skillId;
    std::string      name;
    AionPlayerClass  playerClass;
    uint32_t         minLevel;
    int32_t          mpCost;
    int32_t          dpCost;               // 0, 2000 ou 4000 DP
    uint32_t         castTimeMs;           // 0 = Instant
    uint32_t         cooldownMs;           // Recarga em ms
    float            rangeMeters;          // Alcance em metros
    bool             isMagical;            // Físico vs Mágico
    int32_t          baseDamage;           // Dano base
    float            skillMultiplier;      // Multiplicador no dano
    AbnormalStatus   appliedStatus;        // Efeito de controle / CC
    uint32_t         statusDurationMs;     // Duração do CC
    uint32_t         statusChance;         // Chance % de aplicar CC (0 a 100)
    std::string      chainCategory;        // Categoria de Chain (ex: "GLAD_FEROCIOUS")
    uint8_t          chainStep;            // Passo no Chain (1, 2, 3...)
    uint32_t         preChainSkillId;      // Skill prévia obrigatória (0 se início)
    uint32_t         chainTriggerChance;   // Probabilidade % de liberar o próximo passo (ex: 100, 50, 20)
    bool             isStigma;             // Requer pedra de estigma
    StigmaType       stigmaType;           // Regular ou Greater
    uint32_t         stigmaShardCost;      // Shards requeridos para engastar
    uint32_t         prerequisiteStigmaId; // Estigma requisito anterior na árvore (0 se raiz)
    bool             isAoE;                // Dano em Área
    float            aoeRadius;            // Raio do AoE em metros
    bool             isMantra;             // Chanter Mantra (aura passiva contínua)
};

// Estado da Janela de Chain Combo do Jogador
struct PlayerChainState {
    std::string           activeCategory;
    uint8_t               currentStep;
    uint32_t              lastExecutedSkillId;
    std::vector<uint32_t> nextAvailableSkills;
    uint64_t              expirationTimestampMs;
};

// Buff Ativo no Personagem
struct ActiveBuff {
    uint32_t    buffId;
    std::string name;
    uint64_t    startMs;
    uint32_t    durationMs;
    bool        isDeBuff;
    int32_t     statModifierAtk;
    int32_t     statModifierDef;
    int32_t     statModifierCrit;
    int32_t     statModifierSpeed;
    int32_t     dotDmgPerTick;
    int32_t     hotHealPerTick;
    uint32_t    tickIntervalMs;
    uint64_t    lastTickMs;
};

// Pedra de Estigma Engastada
struct EquippedStigma {
    uint32_t   stigmaItemId;
    uint32_t   grantedSkillId;
    StigmaType type;
    uint8_t    slotIndex;
};

// Resultado da Execução de uma Skill
struct SkillCastResult {
    bool        success;
    std::string failureReason;
    int32_t     damageDealt;
    int32_t     hpHealed;
    int32_t     mpConsumed;
    int32_t     dpConsumed;
    bool        chainTriggered;
    uint32_t    nextChainSkillId;
    AbnormalStatus statusApplied;
};

// Motor Principal de Habilidades, Chains, DP e Estigmas
class SkillEngine {
public:
    static SkillEngine& GetInstance();

    SkillEngine();
    ~SkillEngine();

    // Inicialização da Tabela de Habilidades Canônicas
    void InitializeSkills();

    // Consulta de Template
    const SkillTemplate* GetSkillTemplate(uint32_t skillId) const;

    // Execução de Habilidade
    SkillCastResult CastSkill(
        uint32_t casterId,
        AionPlayerClass casterClass,
        uint32_t casterLevel,
        int32_t& casterMp,
        int32_t& casterDp,
        uint32_t targetId,
        uint32_t skillId,
        float distanceToTarget,
        const DefenseParams& targetDef,
        uint64_t currentTimeMs
    );

    // Sistema de Chains (Combos Encadeados)
    bool CanExecuteChainStep(uint32_t playerId, uint32_t skillId, uint64_t currentTimeMs) const;
    void ResetChain(uint32_t playerId);
    const PlayerChainState* GetChainState(uint32_t playerId) const;
    void UpdateExpiredChains(uint64_t currentTimeMs);

    // Sistema de Divine Power (DP)
    int32_t CalculateMonsterKillDp(uint32_t playerLevel, uint32_t monsterLevel, uint8_t monsterRank) const;
    int32_t CalculatePvpKillDp(uint32_t playerLevel, uint32_t victimLevel, uint32_t victimAbyssRank) const;
    bool CanUseDpSkill(int32_t currentDp, uint32_t skillId) const;

    // Sistema de Slots e Especialização de Estigmas
    uint8_t GetMaxRegularStigmaSlots(uint32_t level, bool questCompleted) const;
    uint8_t GetMaxGreaterStigmaSlots(uint32_t level, bool questCompleted) const;
    bool CanEquipStigma(
        AionPlayerClass playerClass,
        uint32_t playerLevel,
        bool regularQuestCompleted,
        bool greaterQuestCompleted,
        const std::vector<EquippedStigma>& currentStigmas,
        uint32_t stigmaSkillId,
        uint32_t playerShards,
        int64_t playerKinah,
        std::string& outErrorMessage
    ) const;

    // Sistema de Mantras do Chanter (Máximo de 3 ativos simultâneos)
    bool RegisterChanterMantra(uint32_t chanterId, uint32_t mantraSkillId, std::vector<uint32_t>& activeMantras);

    // Cooldowns
    bool IsOnCooldown(uint32_t playerId, uint32_t skillId, uint64_t currentTimeMs) const;
    void TriggerCooldown(uint32_t playerId, uint32_t skillId, uint32_t durationMs, uint64_t currentTimeMs);

#ifdef GetClassName
#undef GetClassName
#endif

    // Utilitários de Classe
    static const char* GetPlayerClassName(AionPlayerClass pClass);
    static AionPlayerClass GetStartingClass(AionPlayerClass pClass);
    static bool IsStartingClass(AionPlayerClass pClass);

private:
    std::unordered_map<uint32_t, SkillTemplate> m_skills;
    std::unordered_map<uint32_t, PlayerChainState> m_playerChains;
    std::unordered_map<uint64_t, uint64_t> m_cooldowns; // Key: (playerId << 32) | skillId -> expirationMs

    void RegisterSkill(const SkillTemplate& skill);
    void RegisterGladiatorSkills();
    void RegisterTemplarSkills();
    void RegisterAssassinSkills();
    void RegisterRangerSkills();
    void RegisterSorcererSkills();
    void RegisterSpiritmasterSkills();
    void RegisterClericSkills();
    void RegisterChanterSkills();
};
