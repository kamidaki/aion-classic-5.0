#pragma once
#include <cstdint>
#include <string>
#include <vector>

enum class HitResult : uint8_t {
    Hit = 0,
    Critical = 1,
    Block = 2,
    Parry = 3,
    Dodge = 4,
    Resist = 5
};

enum class AbnormalStatus : uint16_t {
    None        = 0,
    Stun        = 1,   // Atordoamento (parada de ações)
    Stumble     = 2,   // Derrubada (habilita combos no chão)
    OpenAerial  = 3,   // Levitação / Aéreo (habilita combos aéreos)
    Spin        = 4,   // Giro (cancela canalizações)
    Silence     = 5,   // Silêncio (bloqueia magias)
    Blind       = 6,   // Cegueira (reduz precisão física drástica)
    Root        = 7,   // Enraizamento (prende pés, quebra sob dano)
    Sleep       = 8,   // Sono (incapacitação total, quebra sob dano)
    Fear        = 9,   // Medo / Terror (fuga em pânico com slow)
    Paralyze    = 10,  // Paralisia / Petrificação total (Godstone)
    Poison      = 11,  // Dano contínuo veneno
    Bleed       = 12   // Dano contínuo sangramento
};

struct AttackParams {
    uint32_t attackerId;
    uint32_t targetId;
    int32_t  attackerAttack;
    int32_t  attackerCritRate;
    int32_t  attackerAccuracy;
    int32_t  attackerMagicBoost;
    int32_t  skillId;
    int32_t  skillBaseDamage;
    float    skillMultiplier;
    bool     isMagical;
};

struct DefenseParams {
    int32_t  physicalDef;
    int32_t  magicResist;
    int32_t  block;
    int32_t  parry;
    int32_t  evasion;
    int32_t  shieldReductionPercent; // ex: 70 para 70% de redução
};

struct CombatDamageResult {
    HitResult hitResult;
    int32_t   damage;
    int32_t   blockedDamage;
    int32_t   reflectedDamage;
    AbnormalStatus appliedStatus;
    uint32_t  statusDurationMs;
    bool      statusBrokenOnDamage;
};

// Motor canônico de combate e cálculo de dano do Aion Classic
class CombatEngine {
public:
    static CombatEngine& GetInstance();

    CombatEngine();
    ~CombatEngine();

    // Cálculo Canônico de Dano e Acerto
    CombatDamageResult CalculateDamage(const AttackParams& atk, const DefenseParams& def);

    // Verificação de Sucesso de Status Anormal
    bool CheckStatusSuccess(int32_t attackerPenetration, int32_t targetResist, AbnormalStatus status);

    // Sistema Canônico de Remove Shock (Liberar Choque)
    bool CanUseRemoveShock(AbnormalStatus currentStatus) const;
    bool ExecuteRemoveShock(uint32_t playerId);

    // Regras de Comportamento dos Status Anormais
    bool BreaksOnDamage(AbnormalStatus status) const;
    bool BlocksMagicSkills(AbnormalStatus status) const;
    bool BlocksMovement(AbnormalStatus status) const;
    bool BlocksAllActions(AbnormalStatus status) const;
};

