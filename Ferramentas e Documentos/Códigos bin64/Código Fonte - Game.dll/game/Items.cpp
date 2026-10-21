#include "Items.h"
#include "../core/GameLog.h"

// Item
Item::Item(uint32_t itemId, const std::string& name) : m_itemId(itemId), m_name(name) {}
Item::~Item() {}

// InventoryItem
InventoryItem::InventoryItem(uint32_t itemId, const std::string& name, uint32_t count, int32_t slot)
    : Item(itemId, name), m_count(count), m_slot(slot) {}
InventoryItem::~InventoryItem() {}

// ItemObject
ItemObject::ItemObject(uint32_t objectId, uint32_t itemId, const std::string& name, float x, float y, float z)
    : Item(itemId, name), m_objectId(objectId), m_x(x), m_y(y), m_z(z) {}
ItemObject::~ItemObject() {}

// RecipeItem
RecipeItem::RecipeItem(uint32_t recipeId, const std::string& name, uint32_t craftedItemId)
    : Item(recipeId, name), m_craftedItemId(craftedItemId) {}
RecipeItem::~RecipeItem() {}

// TradeItem
TradeItem::TradeItem(uint32_t itemId, const std::string& name, uint32_t count, int64_t priceKinah)
    : Item(itemId, name), m_count(count), m_priceKinah(priceKinah) {}
TradeItem::~TradeItem() {}

// BuffItem
BuffItem::BuffItem(uint32_t buffId, const std::string& name, uint32_t durationSeconds)
    : m_buffId(buffId), m_name(name), m_durationSeconds(durationSeconds) {}
BuffItem::~BuffItem() {}

// SkillItem
SkillItem::SkillItem(uint32_t skillId, uint32_t skillLevel, const std::string& name)
    : m_skillId(skillId), m_skillLevel(skillLevel), m_name(name) {}
SkillItem::~SkillItem() {}
