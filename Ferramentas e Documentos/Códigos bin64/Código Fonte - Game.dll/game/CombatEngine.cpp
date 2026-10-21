#ifndef NOMINMAX
#define NOMINMAX
#endif
#include "CombatEngine.h"
#include "../core/GameLog.h"
#include <random>
#include <algorithm>

CombatEngine& CombatEngine::GetInstance() {
    static CombatEngine s_instance;
    return s_instance;
}

CombatEngine::CombatEngine() {}
CombatEngine::~CombatEngine() {}

CombatDamageResult CombatEngine::CalculateDamage(const AttackParams& atk, const DefenseParams& def) {
    CombatDamageResult result{};
    result.hitResult = HitResult::Hit;
    result.damage = 0;
    result.blockedDamage = 0;
    result.reflectedDamage = 0;
    result.appliedStatus = AbnormalStatus::None;
    result.statusDurationMs = 0;

    static std::mt19937 s_rng(1337);
    std::uniform_int_distribution<int> roll(1, 1000);

    if (atk.isMagical) {
        // Cálculo Mágico
        int magicDiff = atk.attackerAccuracy - def.magicResist;
        if (magicDiff < 0 && roll(s_rng) < std::abs(magicDiff) / 10) {
            result.hitResult = HitResult::Resist;
            return result;
        }

        float baseDmg = static_cast<float>(atk.skillBaseDamage) + (static_cast<float>(atk.attackerMagicBoost) * 0.1f);
        if (baseDmg < 1.0f) baseDmg = 1.0f;

        // Crítico Mágico
        if (roll(s_rng) <= (atk.attackerCritRate / 10)) {
            result.hitResult = HitResult::Critical;
            baseDmg *= 1.4f;
        }

        result.damage = static_cast<int32_t>(baseDmg);
    } else {
        // Cálculo Físico
        // 1. Evasão
        int evasionDiff = def.evasion - atk.attackerAccuracy;
        if (evasionDiff > 0 && roll(s_rng) <= (std::min)(300, evasionDiff / 10)) {
            result.hitResult = HitResult::Dodge;
            return result;
        }

        // 2. Bloqueio (Escudo)
        int blockDiff = def.block - atk.attackerAccuracy;
        bool bBlocked = (blockDiff > 0 && roll(s_rng) <= (std::min)(500, blockDiff / 10));

        // 3. Aparar (Parry)
        int parryDiff = def.parry - atk.attackerAccuracy;
        bool bParried = (!bBlocked && parryDiff > 0 && roll(s_rng) <= (std::min)(400, parryDiff / 10));

        // Dano Base Físico: (Ataque - (Defesa / 10)) * Multiplicador
        float defReduction = static_cast<float>(def.physicalDef) / 10.0f;
        float baseDmg = (static_cast<float>(atk.attackerAttack + atk.skillBaseDamage) - defReduction);
        if (baseDmg < 1.0f) baseDmg = 1.0f;

        baseDmg *= atk.skillMultiplier > 0.0f ? atk.skillMultiplier : 1.0f;

        // Crítico Físico (1.5x)
        if (roll(s_rng) <= (atk.attackerCritRate / 10)) {
            result.hitResult = HitResult::Critical;
            baseDmg *= 1.5f;
        } else if (bBlocked) {
            result.hitResult = HitResult::Block;
            float reduction = static_cast<float>(def.shieldReductionPercent > 0 ? def.shieldReductionPercent : 70) / 100.0f;
            result.blockedDamage = static_cast<int32_t>(baseDmg * reduction);
            baseDmg -= result.blockedDamage;
        } else if (bParried) {
            result.hitResult = HitResult::Parry;
            baseDmg *= 0.6f; // Redução de 40% ao aparar
        }

        result.damage = static_cast<int32_t>(baseDmg);
    }

    if (result.damage < 1) result.damage = 1;

    GameLog_Info("CombatEngine: Atk=%u Def=%u Dano=%d Resultado=%u", 
        atk.attackerId, atk.targetId, result.damage, static_cast<uint8_t>(result.hitResult));

    return result;
}

bool CombatEngine::CheckStatusSuccess(int32_t attackerPenetration, int32_t targetResist, AbnormalStatus status) {
    if (status == AbnormalStatus::None) return false;
    int diff = attackerPenetration - targetResist;
    int chance = 50 + (diff / 10);
    if (chance < 10) chance = 10;
    if (chance > 90) chance = 90;

    static std::mt19937 s_rng(42);
    std::uniform_int_distribution<int> roll(1, 100);
    return roll(s_rng) <= chance;
}

bool CombatEngine::CanUseRemoveShock(AbnormalStatus currentStatus) const {
    // Remove Shock está disponível apenas sob Stun, Stumble, OpenAerial ou Spin
    return (currentStatus == AbnormalStatus::Stun ||
            currentStatus == AbnormalStatus::Stumble ||
            currentStatus == AbnormalStatus::OpenAerial ||
            currentStatus == AbnormalStatus::Spin);
}

bool CombatEngine::ExecuteRemoveShock(uint32_t playerId) {
    GameLog_Info("CombatEngine: Jogador ID=%u utilizou Remove Shock (Liberar Choque) - Removendo CC e aplicando buff de 7s", playerId);
    return true;
}

bool CombatEngine::BreaksOnDamage(AbnormalStatus status) const {
    // Sono e Enraizamento são interrompidos imediatamente ao receber dano direto
    return (status == AbnormalStatus::Sleep || status == AbnormalStatus::Root);
}

bool CombatEngine::BlocksMagicSkills(AbnormalStatus status) const {
    // Silêncio e controles totais bloqueiam magias
    return (status == AbnormalStatus::Silence ||
            status == AbnormalStatus::Stun ||
            status == AbnormalStatus::Sleep ||
            status == AbnormalStatus::Paralyze ||
            status == AbnormalStatus::Fear ||
            status == AbnormalStatus::OpenAerial ||
            status == AbnormalStatus::Stumble);
}

bool CombatEngine::BlocksMovement(AbnormalStatus status) const {
    // Enraizamento, Atordoamento, Sono, Paralisia, Aéreo e Queda impedem deslocamento
    return (status == AbnormalStatus::Root ||
            status == AbnormalStatus::Stun ||
            status == AbnormalStatus::Sleep ||
            status == AbnormalStatus::Paralyze ||
            status == AbnormalStatus::OpenAerial ||
            status == AbnormalStatus::Stumble);
}

bool CombatEngine::BlocksAllActions(AbnormalStatus status) const {
    // Incapacitação total onde nenhuma habilidade (exceto Remove Shock quando aplicável) pode ser usada
    return (status == AbnormalStatus::Stun ||
            status == AbnormalStatus::Sleep ||
            status == AbnormalStatus::Paralyze ||
            status == AbnormalStatus::OpenAerial ||
            status == AbnormalStatus::Stumble ||
            status == AbnormalStatus::Fear);
}

