#pragma once
#include <cstdint>
#include <string>

// Classe base canônica de itens do jogo extraída do RTTI (.?AVItem@@)
class Item {
public:
    Item(uint32_t itemId, const std::string& name);
    virtual ~Item();

    uint32_t GetItemId() const { return m_itemId; }
    const std::string& GetName() const { return m_name; }

protected:
    uint32_t m_itemId;
    std::string m_name;
};

// Item do inventário com quantidade e slot (.?AVInventoryItem@@)
class InventoryItem : public Item {
public:
    InventoryItem(uint32_t itemId, const std::string& name, uint32_t count, int32_t slot);
    virtual ~InventoryItem();

    uint32_t GetCount() const { return m_count; }
    void SetCount(uint32_t count) { m_count = count; }

    int32_t GetSlot() const { return m_slot; }
    void SetSlot(int32_t slot) { m_slot = slot; }

private:
    uint32_t m_count;
    int32_t m_slot;
};

// Objeto de item dropado no chão (.?AVItemObject@@)
class ItemObject : public Item {
public:
    ItemObject(uint32_t objectId, uint32_t itemId, const std::string& name, float x, float y, float z);
    virtual ~ItemObject();

    uint32_t GetObjectId() const { return m_objectId; }

private:
    uint32_t m_objectId;
    float m_x, m_y, m_z;
};

// Item de receita de artesanato (.?AVRecipeItem@@)
class RecipeItem : public Item {
public:
    RecipeItem(uint32_t recipeId, const std::string& name, uint32_t craftedItemId);
    virtual ~RecipeItem();

    uint32_t GetCraftedItemId() const { return m_craftedItemId; }

private:
    uint32_t m_craftedItemId;
};

// Item em transação/comércio (.?AVTradeItem@@)
class TradeItem : public Item {
public:
    TradeItem(uint32_t itemId, const std::string& name, uint32_t count, int64_t priceKinah);
    virtual ~TradeItem();

    int64_t GetPriceKinah() const { return m_priceKinah; }

private:
    uint32_t m_count;
    int64_t m_priceKinah;
};

// Item de buff de status (.?AVBuffItem@@)
class BuffItem {
public:
    BuffItem(uint32_t buffId, const std::string& name, uint32_t durationSeconds);
    virtual ~BuffItem();

    uint32_t GetBuffId() const { return m_buffId; }
    uint32_t GetDuration() const { return m_durationSeconds; }

private:
    uint32_t m_buffId;
    std::string m_name;
    uint32_t m_durationSeconds;
};

// Item/Slot de Habilidade (.?AVSkillItem@@)
class SkillItem {
public:
    SkillItem(uint32_t skillId, uint32_t skillLevel, const std::string& name);
    virtual ~SkillItem();

    uint32_t GetSkillId() const { return m_skillId; }
    uint32_t GetSkillLevel() const { return m_skillLevel; }

private:
    uint32_t m_skillId;
    uint32_t m_skillLevel;
    std::string m_name;
};
