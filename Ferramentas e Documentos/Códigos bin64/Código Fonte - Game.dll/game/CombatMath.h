#pragma once
#include <cstdint>
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
#include <functional>
#include "Items.h"

// Enum canônico de índices de atributos de criaturas extraído do RTTI (.?AW4CreatureAttrIndex@@)
enum CreatureAttrIndex : uint32_t {
    ATTR_MAX_HP = 0,
    ATTR_MAX_MP,
    ATTR_MAX_DP,
    ATTR_HP_REGEN,
    ATTR_MP_REGEN,
    ATTR_PHYSICAL_ATTACK,
    ATTR_PHYSICAL_DEFENSE,
    ATTR_PHYSICAL_ACCURACY,
    ATTR_EVASION,
    ATTR_PARRY,
    ATTR_BLOCK,
    ATTR_PHYSICAL_CRITICAL,
    ATTR_STRIKE_RESIST,
    ATTR_STRIKE_FORTIFY,
    ATTR_MAGICAL_ATTACK,
    ATTR_MAGICAL_DEFENSE,
    ATTR_MAGICAL_ACCURACY,
    ATTR_MAGICAL_RESIST,
    ATTR_MAGICAL_BOOST,
    ATTR_MAGICAL_SUPPRESSION,
    ATTR_MAGICAL_CRITICAL,
    ATTR_SPELL_RESIST,
    ATTR_SPEED,
    ATTR_FLY_SPEED,
    ATTR_ATTACK_SPEED,
    ATTR_PVP_PHYSICAL_ATTACK,
    ATTR_PVP_PHYSICAL_DEFENSE,
    ATTR_PVP_MAGICAL_ATTACK,
    ATTR_PVP_MAGICAL_DEFENSE,
    ATTR_COUNT
};

// .?AVDamageNumberGroup@@
class DamageNumberGroup {
public:
    DamageNumberGroup();
    virtual ~DamageNumberGroup();

    enum DamageType {
        DAMAGE_NORMAL = 0,
        DAMAGE_CRITICAL,
        DAMAGE_BLOCKED,
        DAMAGE_PARRIED,
        DAMAGE_DODGED,
        DAMAGE_RESISTED,
        DAMAGE_HEAL,
        DAMAGE_MP_HEAL
    };

    // Multiplicadores e taxas canônicas de armas oficiais (19 tipos)
    static float GetWeaponCritMultiplier(WeaponType weaponType);
    static void  GetWeaponDamageVariance(WeaponType weaponType, float& outMin, float& outMax);
    static float GetWeaponBaseAttackSpeed(WeaponType weaponType);

    // Fórmulas Oficiais Aion Classic 5.0 (AttackUtil & StatFunctions)
    static uint32_t CalculatePhysicalDamage(
        float attack, float skillMultiplier, float targetDefense,
        bool isCritical, bool isBlocked, bool isParried, bool isPvp,
        float blockReduceRatio = 0.5f, float randomVariance = 1.0f,
        float customCritMultiplier = 0.0f);

    static uint32_t CalculateMagicalDamage(
        float magicBoost, float skillMultiplier, float magicSuppression,
        float elementalResist, bool isCritical, bool isPvp);

    static bool CheckPhysicalHit(float accuracy, float evasion, float rnd0to1000);
    static bool CheckPhysicalCritical(float critRate, float strikeResist, float rnd0to1000, bool isPvp);
    static bool CheckBlock(float accuracy, float block, float rnd0to1000);
    static bool CheckParry(float accuracy, float parry, float rnd0to1000);
    static bool CheckMagicalResist(float mResist, float mAccuracy, float rnd0to1000, bool isPvp);
};

// .?AUAbnormalStatusParam@@
struct AbnormalStatusParam {
    uint32_t effectId;
    uint32_t durationMs;
    uint32_t tickIntervalMs;
    int32_t  valuePerTick;
    uint32_t targetAttr;
    int32_t  attrModifier;
    bool     isDebuff;
    bool     isDispelable;
    uint32_t elapsedMs;
    uint32_t nextTickMs;

    AbnormalStatusParam()
        : effectId(0), durationMs(0), tickIntervalMs(0), valuePerTick(0)
        , targetAttr(0), attrModifier(0), isDebuff(false), isDispelable(true)
        , elapsedMs(0), nextTickMs(0) {}
};

// .?AVAbnormalStatusGroup@@
class AbnormalStatusGroup {
public:
    AbnormalStatusGroup();
    virtual ~AbnormalStatusGroup();

    bool ApplyEffect(const AbnormalStatusParam& param);
    bool RemoveEffect(uint32_t effectId);
    void UpdateTicks(uint32_t deltaMs, std::function<void(uint32_t effectId, int32_t tickVal)> onTick);
    void Clear();

    bool HasEffect(uint32_t effectId) const;
    size_t GetActiveEffectCount() const { return m_activeEffects.size(); }

private:
    std::vector<AbnormalStatusParam> m_activeEffects;
};

