#include "CombatMath.h"

// DamageNumberGroup
DamageNumberGroup::DamageNumberGroup() {}
DamageNumberGroup::~DamageNumberGroup() {}

uint32_t DamageNumberGroup::CalculatePhysicalDamage(
    float attack, float skillMultiplier, float targetDefense,
    bool isCritical, bool isBlocked, bool isParried, bool isPvp,
    float blockReduceRatio, float randomVariance) 
{
    // Fórmula oficial Aion Classic 5.0 (AttackUtil & StatFunctions):
    // Dano Base = (Ataque * Multiplicador - Defesa / 10) * Variação
    float baseDmg = (attack * skillMultiplier) - (targetDefense / 10.0f);
    if (baseDmg < 1.0f) baseDmg = 1.0f;
    baseDmg *= randomVariance;

    // Modificadores de status de combate
    if (isCritical) {
        baseDmg *= 1.5f; // Multiplicador padrão de crítico físico
    }
    if (isParried) {
        baseDmg *= 0.6f; // Aparar reduz dano em 40% (resta 60%)
    }
    if (isBlocked) {
        baseDmg *= (1.0f - blockReduceRatio); // Bloqueio com escudo reduz pelo índice do escudo
    }
    if (isPvp) {
        baseDmg *= 0.5f; // Redução padrão PVP de 50%
    }

    if (baseDmg < 1.0f) baseDmg = 1.0f;
    return static_cast<uint32_t>(std::round(baseDmg));
}

uint32_t DamageNumberGroup::CalculateMagicalDamage(
    float magicBoost, float skillMultiplier, float magicSuppression,
    float elementalResist, bool isCritical, bool isPvp) 
{
    // Fórmula oficial Aion Classic 5.0:
    // Dano Mágico = (Poder Mágico * Multiplicador - Supressão Mágica) * (1 - Resistência Elemental)
    float baseDmg = (magicBoost * skillMultiplier) - (magicSuppression / 10.0f);
    if (baseDmg < 1.0f) baseDmg = 1.0f;

    // Resistência Elemental: cada 10 pontos = 1% de redução (max 80%)
    float resistRatio = std::min(0.8f, std::max(0.0f, elementalResist / 1000.0f));
    baseDmg *= (1.0f - resistRatio);

    if (isCritical) {
        baseDmg *= 1.5f;
    }
    if (isPvp) {
        baseDmg *= 0.5f; // Redução de dano mágico em PVP
    }

    if (baseDmg < 1.0f) baseDmg = 1.0f;
    return static_cast<uint32_t>(std::round(baseDmg));
}

bool DamageNumberGroup::CheckPhysicalHit(float accuracy, float evasion, float rnd0to1000) {
    // Evasão = (Evasão - Precisão) / 10 %, clamped [50 (5%), 950 (95%)]
    float dodgeRate = (evasion - accuracy);
    if (dodgeRate < 50.0f) dodgeRate = 50.0f;
    if (dodgeRate > 950.0f) dodgeRate = 950.0f;
    return rnd0to1000 >= dodgeRate;
}

bool DamageNumberGroup::CheckPhysicalCritical(float critRate, float strikeResist, float rnd0to1000, bool isPvp) {
    // Crítico = (Crítico - Resistência Crítica) / 10 %
    float rate = (critRate - strikeResist);
    if (rate < 0.0f) rate = 0.0f;
    float maxCap = isPvp ? 500.0f : 800.0f; // Cap de 50% em PVP
    if (rate > maxCap) rate = maxCap;
    return rnd0to1000 < rate;
}

bool DamageNumberGroup::CheckBlock(float accuracy, float block, float rnd0to1000) {
    // Bloqueio com Escudo: cap em 50% (500/1000)
    float rate = block - accuracy;
    if (rate < 0.0f) rate = 0.0f;
    if (rate > 500.0f) rate = 500.0f;
    return rnd0to1000 < rate;
}

bool DamageNumberGroup::CheckParry(float accuracy, float parry, float rnd0to1000) {
    // Aparar: cap em 40% (400/1000)
    float rate = parry - accuracy;
    if (rate < 0.0f) rate = 0.0f;
    if (rate > 400.0f) rate = 400.0f;
    return rnd0to1000 < rate;
}

bool DamageNumberGroup::CheckMagicalResist(float mResist, float mAccuracy, float rnd0to1000, bool isPvp) {
    // Resistência Mágica: cada 100 delta = 10%
    float rate = mResist - mAccuracy;
    if (rate < 0.0f) rate = 0.0f;
    if (isPvp && rate > 500.0f) rate = 500.0f; // Cap de 50% em PVP
    if (rate > 1000.0f) rate = 1000.0f;
    return rnd0to1000 < rate;
}

// AbnormalStatusGroup
AbnormalStatusGroup::AbnormalStatusGroup() {}
AbnormalStatusGroup::~AbnormalStatusGroup() { Clear(); }

bool AbnormalStatusGroup::ApplyEffect(const AbnormalStatusParam& param) {
    for (auto& eff : m_activeEffects) {
        if (eff.effectId == param.effectId) {
            eff = param;
            eff.elapsedMs = 0;
            eff.nextTickMs = param.tickIntervalMs;
            return true;
        }
    }
    AbnormalStatusParam act = param;
    act.elapsedMs = 0;
    act.nextTickMs = param.tickIntervalMs;
    m_activeEffects.push_back(act);
    return true;
}

bool AbnormalStatusGroup::RemoveEffect(uint32_t effectId) {
    for (auto it = m_activeEffects.begin(); it != m_activeEffects.end(); ++it) {
        if (it->effectId == effectId) {
            m_activeEffects.erase(it);
            return true;
        }
    }
    return false;
}

void AbnormalStatusGroup::UpdateTicks(uint32_t deltaMs, std::function<void(uint32_t effectId, int32_t tickVal)> onTick) {
    for (auto it = m_activeEffects.begin(); it != m_activeEffects.end(); ) {
        it->elapsedMs += deltaMs;
        if (it->tickIntervalMs > 0 && it->elapsedMs >= it->nextTickMs) {
            if (onTick) {
                onTick(it->effectId, it->valuePerTick);
            }
            it->nextTickMs += it->tickIntervalMs;
        }
        if (it->durationMs > 0 && it->elapsedMs >= it->durationMs) {
            it = m_activeEffects.erase(it);
        } else {
            ++it;
        }
    }
}

void AbnormalStatusGroup::Clear() {
    m_activeEffects.clear();
}

bool AbnormalStatusGroup::HasEffect(uint32_t effectId) const {
    for (const auto& eff : m_activeEffects) {
        if (eff.effectId == effectId) return true;
    }
    return false;
}

