#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <algorithm>

// Enums Canônicos do Sistema de Itens do Aion Classic (Fiel ao Classic)
enum ItemQuality : uint8_t {
    ITEM_QUALITY_JUNK       = 0, // Cinza
    ITEM_QUALITY_COMMON     = 1, // Branco
    ITEM_QUALITY_RARE       = 2, // Verde
    ITEM_QUALITY_LEGENDARY  = 3, // Azul
    ITEM_QUALITY_UNIQUE     = 4, // Amarelo (Fabled / Unique)
    ITEM_QUALITY_MYTHIC     = 5  // Laranja (Eternal / Mythic)
};

enum ItemCategory : uint8_t {
    ITEM_CAT_WEAPON         = 0,
    ITEM_CAT_ARMOR          = 1,
    ITEM_CAT_ACCESSORY      = 2,
    ITEM_CAT_CONSUMABLE     = 3,
    ITEM_CAT_MATERIAL       = 4,
    ITEM_CAT_QUEST          = 5,
    ITEM_CAT_STIGMA         = 6,
    ITEM_CAT_GODSTONE       = 7,
    ITEM_CAT_WING           = 8,
    ITEM_CAT_ENCHANT_STONE  = 9,
    ITEM_CAT_MANASTONE      = 10
};

enum WeaponType : uint8_t {
    WEAPON_NONE         = 0,
    WEAPON_DAGGER       = 1,
    WEAPON_SWORD        = 2,
    WEAPON_GREATSWORD   = 3,
    WEAPON_POLEARM      = 4,
    WEAPON_BOW          = 5,
    WEAPON_MACE         = 6,
    WEAPON_STAFF        = 7,
    WEAPON_SPELLBOOK    = 8,
    WEAPON_ORB          = 9,
    WEAPON_SHIELD       = 10,
    WEAPON_CHAINBLADE   = 11
};

enum ArmorType : uint8_t {
    ARMOR_NONE    = 0,
    ARMOR_ROBE    = 1,
    ARMOR_LEATHER = 2,
    ARMOR_CHAIN   = 3,
    ARMOR_PLATE   = 4
};

typedef struct {
    uint32_t manastoneId;
    uint32_t statType;    // CreatureAttrIndex
    int32_t  statValue;
} ManastoneSocket;

typedef struct {
    uint32_t godstoneId;
    uint32_t procRatePer1000;
    uint32_t effectSkillId;
    uint32_t effectDurationMs;
    int32_t  damageValue;
} GodstoneData;

typedef struct {
    uint32_t itemId;
    uint32_t count;
} RecipeIngredient;

// Classe base canônica de itens do jogo extraída do RTTI (.?AVItem@@)
class Item {
public:
    Item(uint32_t itemId, const std::string& name, ItemQuality quality = ITEM_QUALITY_COMMON, ItemCategory category = ITEM_CAT_MATERIAL);
    virtual ~Item();

    uint32_t GetItemId() const { return m_itemId; }
    const std::string& GetName() const { return m_name; }
    ItemQuality GetQuality() const { return m_quality; }
    ItemCategory GetCategory() const { return m_category; }

    uint32_t GetRequiredLevel() const { return m_requiredLevel; }
    void SetRequiredLevel(uint32_t lvl) { m_requiredLevel = lvl; }

    int64_t GetBasePrice() const { return m_basePrice; }
    void SetBasePrice(int64_t price) { m_basePrice = price; }

protected:
    uint32_t     m_itemId;
    std::string  m_name;
    ItemQuality  m_quality;
    ItemCategory m_category;
    uint32_t     m_requiredLevel;
    int64_t      m_basePrice;
};

// Item do inventário com quantidade, slot, encantamento e fusão (.?AVInventoryItem@@)
class InventoryItem : public Item {
public:
    InventoryItem(uint32_t itemId, const std::string& name, uint32_t count = 1, int32_t slot = -1,
                  ItemQuality quality = ITEM_QUALITY_COMMON, ItemCategory category = ITEM_CAT_MATERIAL);
    virtual ~InventoryItem();

    uint32_t GetCount() const { return m_count; }
    void SetCount(uint32_t count) { m_count = count; }

    int32_t GetSlot() const { return m_slot; }
    void SetSlot(int32_t slot) { m_slot = slot; }

    // Tipos de Equipamento Classic
    WeaponType GetWeaponType() const { return m_weaponType; }
    void SetWeaponType(WeaponType wt) { m_weaponType = wt; }

    ArmorType GetArmorType() const { return m_armorType; }
    void SetArmorType(ArmorType at) { m_armorType = at; }

    bool IsTwoHandedWeapon() const;

    // Encantamento Classic (Cap +15, sem risco de quebra de item, perda de 1 nível na falha)
    uint32_t GetEnchantLevel() const { return m_enchantLevel; }
    void SetEnchantLevel(uint32_t lvl) { m_enchantLevel = (std::min)(lvl, 15u); }
    bool CanEnchant() const;
    bool AttemptEnchant(uint32_t stoneLevel, uint32_t catalystBonusRate = 0, float rnd0to100 = 50.0f);

    // Pedras de Maná Classic (Manastones: falha quebra as pedras já socketadas)
    uint32_t GetMaxSockets() const { return m_maxSockets; }
    void SetMaxSockets(uint32_t maxS) { m_maxSockets = (std::min)(maxS, 6u); }
    uint32_t GetUsedSockets() const { return static_cast<uint32_t>(m_manastones.size()); }
    const std::vector<ManastoneSocket>& GetManastones() const { return m_manastones; }

    bool CanSocketManastone() const;
    bool AttemptSocketManastone(const ManastoneSocket& stone, float rnd0to100 = 50.0f);
    void RemoveAllManastones();

    // Pedra Divina (Godstone)
    bool HasGodstone() const { return m_godstone.godstoneId != 0; }
    const GodstoneData& GetGodstone() const { return m_godstone; }
    bool SocketGodstone(const GodstoneData& godstone);
    bool CheckGodstoneProc(float rnd0to1000) const;

    // Fusão de Armas Classic (Armsfusion / Arms Combining)
    bool CanArmsfuseWith(const InventoryItem& secondaryWeapon) const;
    bool PerformArmsfusion(const InventoryItem& secondaryWeapon);
    bool IsFused() const { return m_bFused; }
    uint32_t GetFusedSecondaryId() const { return m_fusedSecondaryItemId; }

    // Vinculação
    bool IsSoulbound() const { return m_bSoulbound; }
    void SetSoulbound(bool bound) { m_bSoulbound = bound; }
    bool IsTradeable() const { return !m_bSoulbound; }

private:
    uint32_t                    m_count;
    int32_t                     m_slot;
    WeaponType                  m_weaponType;
    ArmorType                   m_armorType;
    uint32_t                    m_enchantLevel;
    uint32_t                    m_maxSockets;
    std::vector<ManastoneSocket> m_manastones;
    GodstoneData                m_godstone;
    bool                        m_bFused;
    uint32_t                    m_fusedSecondaryItemId;
    int32_t                     m_fusedAttackBonus;
    bool                        m_bSoulbound;
};

// Objeto de item dropado no chão (.?AVItemObject@@)
class ItemObject : public Item {
public:
    ItemObject(uint32_t objectId, uint32_t itemId, const std::string& name, float x, float y, float z,
               uint32_t ownerId = 0, uint32_t count = 1);
    virtual ~ItemObject();

    uint32_t GetObjectId() const { return m_objectId; }
    uint32_t GetOwnerId() const { return m_ownerId; }
    uint32_t GetCount() const { return m_count; }
    void GetPosition(float& x, float& y, float& z) const { x = m_x; y = m_y; z = m_z; }

    bool CanBeLootedBy(uint32_t looterId, bool isInSameParty = false) const;
    void Update(float deltaSec);
    bool IsExpired() const { return m_despawnTimer <= 0.0f; }

private:
    uint32_t m_objectId;
    float    m_x, m_y, m_z;
    uint32_t m_ownerId;
    uint32_t m_count;
    float    m_lootFreeForAllTimer;
    float    m_despawnTimer;
};

// Item de receita de artesanato (.?AVRecipeItem@@)
class RecipeItem : public Item {
public:
    RecipeItem(uint32_t recipeId, const std::string& name, uint32_t craftedItemId,
               uint32_t requiredCraftSkill = 0, uint32_t skillLevel = 1, uint32_t comboItemId = 0);
    virtual ~RecipeItem();

    uint32_t GetCraftedItemId() const { return m_craftedItemId; }
    uint32_t GetRequiredSkill() const { return m_requiredSkill; }
    uint32_t GetRequiredSkillLevel() const { return m_requiredSkillLevel; }
    uint32_t GetComboItemId() const { return m_comboItemId; }

    void AddIngredient(uint32_t itemId, uint32_t count);
    const std::vector<RecipeIngredient>& GetIngredients() const { return m_ingredients; }

    bool CanCraft(uint32_t playerSkillId, uint32_t playerSkillLevel) const;
    bool RollCriticalCraft(float rnd0to100) const;

private:
    uint32_t                       m_craftedItemId;
    uint32_t                       m_requiredSkill;
    uint32_t                       m_requiredSkillLevel;
    uint32_t                       m_comboItemId;
    std::vector<RecipeIngredient>  m_ingredients;
};

// Item em transação/comércio (.?AVTradeItem@@)
class TradeItem : public Item {
public:
    TradeItem(uint32_t itemId, const std::string& name, uint32_t count, int64_t priceKinah, bool isTaxable = true);
    virtual ~TradeItem();

    uint32_t GetCount() const { return m_count; }
    void SetCount(uint32_t count) { m_count = count; }

    int64_t GetPriceKinah() const { return m_priceKinah; }
    int64_t GetTotalPrice(float taxRate = 0.05f) const;

private:
    uint32_t m_count;
    int64_t  m_priceKinah;
    bool     m_isTaxable;
};

// Item de buff de status (.?AVBuffItem@@)
class BuffItem {
public:
    BuffItem(uint32_t buffId, const std::string& name, uint32_t durationSeconds,
             uint32_t effectAttr = 0, int32_t attrValue = 0);
    virtual ~BuffItem();

    uint32_t GetBuffId() const { return m_buffId; }
    uint32_t GetDuration() const { return m_durationSeconds; }
    uint32_t GetRemainingTime() const { return m_remainingTime; }
    uint32_t GetEffectAttr() const { return m_effectAttr; }
    int32_t  GetAttrValue() const { return m_attrValue; }

    void Update(float deltaSec);
    bool IsExpired() const { return m_remainingTime == 0; }
    void ResetDuration() { m_remainingTime = m_durationSeconds; }

private:
    uint32_t    m_buffId;
    std::string m_name;
    uint32_t    m_durationSeconds;
    uint32_t    m_remainingTime;
    uint32_t    m_effectAttr;
    int32_t     m_attrValue;
};

// Item/Slot de Habilidade (.?AVSkillItem@@)
class SkillItem {
public:
    SkillItem(uint32_t skillId, uint32_t skillLevel, const std::string& name,
              uint32_t cooldownMs = 0, uint32_t mpCost = 0, uint32_t dpCost = 0);
    virtual ~SkillItem();

    uint32_t GetSkillId() const { return m_skillId; }
    uint32_t GetSkillLevel() const { return m_skillLevel; }
    void SetSkillLevel(uint32_t lvl) { m_skillLevel = lvl; }
    const std::string& GetName() const { return m_name; }

    uint32_t GetCooldownMs() const { return m_cooldownMs; }
    uint32_t GetRemainingCooldownMs() const { return m_remainingCooldownMs; }
    bool IsReady() const { return m_remainingCooldownMs == 0; }

    uint32_t GetMpCost() const { return m_mpCost; }
    uint32_t GetDpCost() const { return m_dpCost; }

    void TriggerCooldown();
    void Update(uint32_t deltaMs);
    void ResetCooldown() { m_remainingCooldownMs = 0; }

private:
    uint32_t    m_skillId;
    uint32_t    m_skillLevel;
    std::string m_name;
    uint32_t    m_cooldownMs;
    uint32_t    m_remainingCooldownMs;
    uint32_t    m_mpCost;
    uint32_t    m_dpCost;
};
