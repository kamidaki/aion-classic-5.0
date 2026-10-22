#include "Items.h"
#include "../core/GameLog.h"
#include <cmath>

// Item
Item::Item(uint32_t itemId, const std::string& name, ItemQuality quality, ItemCategory category)
    : m_itemId(itemId)
    , m_name(name)
    , m_quality(quality)
    , m_category(category)
    , m_requiredLevel(1)
    , m_basePrice(100)
{
}

Item::~Item() {}

// InventoryItem
InventoryItem::InventoryItem(uint32_t itemId, const std::string& name, uint32_t count, int32_t slot,
                             ItemQuality quality, ItemCategory category)
    : Item(itemId, name, quality, category)
    , m_count(count)
    , m_slot(slot)
    , m_weaponType(WEAPON_NONE)
    , m_armorType(ARMOR_NONE)
    , m_enchantLevel(0)
    , m_maxSockets(4)
    , m_bFused(false)
    , m_fusedSecondaryItemId(0)
    , m_fusedAttackBonus(0)
    , m_bSoulbound(false)
{
}

InventoryItem::~InventoryItem() {}

bool InventoryItem::IsTwoHandedWeapon() const {
    switch (m_weaponType) {
    case WEAPON_GREATSWORD:
    case WEAPON_POLEARM:
    case WEAPON_BOW:
    case WEAPON_STAFF:
    case WEAPON_SPELLBOOK:
    case WEAPON_ORB:
    case WEAPON_CHAINBLADE:
        return true;
    default:
        return false;
    }
}

bool InventoryItem::CanEnchant() const {
    if (m_category != ITEM_CAT_WEAPON && m_category != ITEM_CAT_ARMOR) return false;
    // Cap máximo de encantamento do Aion Classic é +15
    return m_enchantLevel < 15;
}

bool InventoryItem::AttemptEnchant(uint32_t stoneLevel, uint32_t catalystBonusRate, float rnd0to100) {
    if (!CanEnchant()) {
        GameLog_Warn("InventoryItem::AttemptEnchant: Item '%s' (ID=%u) nao pode ser encantado (Cap +15 atingido)", m_name.c_str(), m_itemId);
        return false;
    }

    // Fórmula Canônica Aion Classic de Encantamento:
    // Taxa Base = 50% + (Nível da Pedra - Nível Requerido do Item) * 5% + Bônus Suplemento
    int32_t levelDelta = static_cast<int32_t>(stoneLevel) - static_cast<int32_t>(m_requiredLevel);
    float successRate = 50.0f + (levelDelta * 5.0f) + static_cast<float>(catalystBonusRate);

    // Penalidade para níveis altos (+10 a +15)
    if (m_enchantLevel >= 10) {
        successRate -= (m_enchantLevel - 9) * 4.0f;
    }

    // Clamping da taxa entre 5% e 95%
    successRate = (std::max)(5.0f, (std::min)(95.0f, successRate));

    bool isSuccess = (rnd0to100 < successRate);
    if (isSuccess) {
        m_enchantLevel++;
        GameLog_Info("[ENCANTAMENTO SUCESSO] Item '%s' avancou para +%u! (Taxa: %.1f%%, Roll: %.1f)",
            m_name.c_str(), m_enchantLevel, successRate, rnd0to100);
        return true;
    } else {
        // Regra Normal Classic: Falha reduz 1 nível (itens nunca quebram no Classic)
        if (m_enchantLevel > 0) m_enchantLevel--;
        GameLog_Warn("[ENCANTAMENTO FALHA] Item '%s' regrediu para +%u (Taxa: %.1f%%, Roll: %.1f)",
            m_name.c_str(), m_enchantLevel, successRate, rnd0to100);
        return false;
    }
}

bool InventoryItem::CanSocketManastone() const {
    if (m_category != ITEM_CAT_WEAPON && m_category != ITEM_CAT_ARMOR) return false;
    return m_manastones.size() < m_maxSockets;
}

bool InventoryItem::AttemptSocketManastone(const ManastoneSocket& stone, float rnd0to100) {
    if (!CanSocketManastone()) {
        GameLog_Warn("InventoryItem::AttemptSocketManastone: Sem slots livres em '%s'", m_name.c_str());
        return false;
    }

    // Taxa canônica por slot: Slot 1=85%, Slot 2=75%, Slot 3=65%, Slot 4=55%, Slot 5=45%, Slot 6=35%
    size_t currentSlot = m_manastones.size();
    float successRate = 85.0f - (currentSlot * 10.0f);
    if (successRate < 20.0f) successRate = 20.0f;

    if (rnd0to100 < successRate) {
        m_manastones.push_back(stone);
        GameLog_Info("[MANASTONE SUCESSO] Pedra inserida no slot %zu de '%s' (Taxa: %.1f%%)",
            currentSlot + 1, m_name.c_str(), successRate);
        return true;
    } else {
        // Regra Punitiva Classic: Todas as pedras anteriores quebram!
        size_t brokenCount = m_manastones.size();
        m_manastones.clear();
        GameLog_Warn("[MANASTONE FALHA] Falha no slot %zu! %zu pedras anteriores foram destruidas!",
            currentSlot + 1, brokenCount);
        return false;
    }
}

void InventoryItem::RemoveAllManastones() {
    m_manastones.clear();
    GameLog_Info("InventoryItem::RemoveAllManastones: Todas as pedras de '%s' foram removidas", m_name.c_str());
}

bool InventoryItem::SocketGodstone(const GodstoneData& godstone) {
    if (m_category != ITEM_CAT_WEAPON || m_weaponType == WEAPON_SHIELD) {
        GameLog_Warn("InventoryItem::SocketGodstone: Apenas armas ofensivas suportam Pedra Divina");
        return false;
    }
    m_godstone = godstone;
    GameLog_Info("InventoryItem::SocketGodstone: Pedra Divina ID=%u acoplada a '%s' (Proc: %.1f%%)",
        godstone.godstoneId, m_name.c_str(), godstone.procRatePer1000 / 10.0f);
    return true;
}

bool InventoryItem::CheckGodstoneProc(float rnd0to1000) const {
    if (!HasGodstone()) return false;
    return rnd0to1000 < static_cast<float>(m_godstone.procRatePer1000);
}

bool InventoryItem::CanArmsfuseWith(const InventoryItem& secondaryWeapon) const {
    // 1. Ambas devem ser armas de duas mãos
    if (!IsTwoHandedWeapon() || !secondaryWeapon.IsTwoHandedWeapon()) return false;
    // 2. Devem ser do mesmo tipo de arma (e.g. Greatsword com Greatsword)
    if (m_weaponType != secondaryWeapon.GetWeaponType()) return false;
    // 3. A arma primária não pode estar fundida
    if (m_bFused) return false;
    // 4. A arma secundária não pode estar fundida
    if (secondaryWeapon.IsFused()) return false;
    // 5. O nível da primária deve ser maior ou igual ao da secundária
    if (m_requiredLevel < secondaryWeapon.GetRequiredLevel()) return false;

    return true;
}

bool InventoryItem::PerformArmsfusion(const InventoryItem& secondaryWeapon) {
    if (!CanArmsfuseWith(secondaryWeapon)) {
        GameLog_Warn("InventoryItem::PerformArmsfusion: Fusao invalida entre '%s' e '%s'",
            m_name.c_str(), secondaryWeapon.GetName().c_str());
        return false;
    }

    m_bFused = true;
    m_fusedSecondaryItemId = secondaryWeapon.GetItemId();

    // Bônus de 10% do ataque base da secundária
    m_fusedAttackBonus = static_cast<int32_t>(secondaryWeapon.GetBasePrice() / 50);
    if (m_fusedAttackBonus < 15) m_fusedAttackBonus = 15;

    // Slots adicionais de pedras de maná da secundária
    m_maxSockets = (std::min)(6u, m_maxSockets + secondaryWeapon.GetMaxSockets() / 2);

    // Herda as pedras de maná já socketadas na secundária
    for (const auto& stone : secondaryWeapon.GetManastones()) {
        if (m_manastones.size() < m_maxSockets) {
            m_manastones.push_back(stone);
        }
    }

    GameLog_Info("[ARMSFUSION SUCESSO] Arma '%s' fundida com '%s'! Slots Max: %u, Bonus Atk: +%d",
        m_name.c_str(), secondaryWeapon.GetName().c_str(), m_maxSockets, m_fusedAttackBonus);
    return true;
}

// ItemObject
ItemObject::ItemObject(uint32_t objectId, uint32_t itemId, const std::string& name,
                       float x, float y, float z, uint32_t ownerId, uint32_t count)
    : Item(itemId, name)
    , m_objectId(objectId)
    , m_x(x), m_y(y), m_z(z)
    , m_ownerId(ownerId)
    , m_count(count)
    , m_lootFreeForAllTimer(15.0f)
    , m_despawnTimer(60.0f)
{
}

ItemObject::~ItemObject() {}

bool ItemObject::CanBeLootedBy(uint32_t looterId, bool isInSameParty) const {
    if (m_despawnTimer <= 0.0f) return false;
    if (m_ownerId == 0) return true;
    if (looterId == m_ownerId) return true;
    if (isInSameParty) return true;
    if (m_lootFreeForAllTimer <= 0.0f) return true;
    return false;
}

void ItemObject::Update(float deltaSec) {
    if (m_lootFreeForAllTimer > 0.0f) {
        m_lootFreeForAllTimer -= deltaSec;
    }
    if (m_despawnTimer > 0.0f) {
        m_despawnTimer -= deltaSec;
    }
}

// RecipeItem
RecipeItem::RecipeItem(uint32_t recipeId, const std::string& name, uint32_t craftedItemId,
                       uint32_t requiredCraftSkill, uint32_t skillLevel, uint32_t comboItemId)
    : Item(recipeId, name, ITEM_QUALITY_COMMON, ITEM_CAT_MATERIAL)
    , m_craftedItemId(craftedItemId)
    , m_requiredSkill(requiredCraftSkill)
    , m_requiredSkillLevel(skillLevel)
    , m_comboItemId(comboItemId)
{
}

RecipeItem::~RecipeItem() {}

void RecipeItem::AddIngredient(uint32_t itemId, uint32_t count) {
    RecipeIngredient ing;
    ing.itemId = itemId;
    ing.count = count;
    m_ingredients.push_back(ing);
}

bool RecipeItem::CanCraft(uint32_t playerSkillId, uint32_t playerSkillLevel) const {
    if (m_requiredSkill != 0 && playerSkillId != m_requiredSkill) return false;
    return playerSkillLevel >= m_requiredSkillLevel;
}

bool RecipeItem::RollCriticalCraft(float rnd0to100) const {
    if (m_comboItemId == 0) return false;
    // 15% de chance base de proc nobre (Noble Craft)
    return rnd0to100 < 15.0f;
}

// TradeItem
TradeItem::TradeItem(uint32_t itemId, const std::string& name, uint32_t count, int64_t priceKinah, bool isTaxable)
    : Item(itemId, name)
    , m_count(count)
    , m_priceKinah(priceKinah)
    , m_isTaxable(isTaxable)
{
}

TradeItem::~TradeItem() {}

int64_t TradeItem::GetTotalPrice(float taxRate) const {
    int64_t subTotal = m_priceKinah * m_count;
    if (m_isTaxable && taxRate > 0.0f) {
        int64_t tax = static_cast<int64_t>(subTotal * taxRate);
        return subTotal + tax;
    }
    return subTotal;
}

// BuffItem
BuffItem::BuffItem(uint32_t buffId, const std::string& name, uint32_t durationSeconds,
                   uint32_t effectAttr, int32_t attrValue)
    : m_buffId(buffId)
    , m_name(name)
    , m_durationSeconds(durationSeconds)
    , m_remainingTime(durationSeconds)
    , m_effectAttr(effectAttr)
    , m_attrValue(attrValue)
{
}

BuffItem::~BuffItem() {}

void BuffItem::Update(float deltaSec) {
    if (m_remainingTime > 0) {
        uint32_t sec = static_cast<uint32_t>(deltaSec);
        if (sec >= m_remainingTime) {
            m_remainingTime = 0;
        } else {
            m_remainingTime -= sec;
        }
    }
}

// SkillItem
SkillItem::SkillItem(uint32_t skillId, uint32_t skillLevel, const std::string& name,
                     uint32_t cooldownMs, uint32_t mpCost, uint32_t dpCost)
    : m_skillId(skillId)
    , m_skillLevel(skillLevel)
    , m_name(name)
    , m_cooldownMs(cooldownMs)
    , m_remainingCooldownMs(0)
    , m_mpCost(mpCost)
    , m_dpCost(dpCost)
{
}

SkillItem::~SkillItem() {}

void SkillItem::TriggerCooldown() {
    m_remainingCooldownMs = m_cooldownMs;
}

void SkillItem::Update(uint32_t deltaMs) {
    if (m_remainingCooldownMs > 0) {
        if (deltaMs >= m_remainingCooldownMs) {
            m_remainingCooldownMs = 0;
        } else {
            m_remainingCooldownMs -= deltaMs;
        }
    }
}
