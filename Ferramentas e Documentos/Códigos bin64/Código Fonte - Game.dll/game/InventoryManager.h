#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include "Items.h"

// -------------------------------------------------------------
// 6.1 Os 16 Slots de Equipamento Corporal Canônicos
// -------------------------------------------------------------
enum class EquipSlot : uint8_t {
    MainHand     = 0,  // Slot 0: Arma Principal
    SubHand      = 1,  // Slot 1: Arma Secundária / Escudo
    Helmet       = 2,  // Slot 2: Elmo / Capacete
    Torso        = 3,  // Slot 3: Armadura de Peito
    Legs         = 4,  // Slot 4: Calça
    Shoulders    = 5,  // Slot 5: Ombreiras
    Gloves       = 6,  // Slot 6: Luvas
    Boots        = 7,  // Slot 7: Botas
    EarringLeft  = 8,  // Slot 8: Brinco Esquerdo
    EarringRight = 9,  // Slot 9: Brinco Direito
    RingLeft     = 10, // Slot 10: Anel Esquerdo
    RingRight    = 11, // Slot 11: Anel Direito
    Necklace     = 12, // Slot 12: Colar
    Belt         = 13, // Slot 13: Cinto
    Wings        = 14, // Slot 14: Asas
    Plume        = 15, // Slot 15: Pluma / Acessório Especial
    Count        = 16
};

// Estrutura de Pedra Divina (Godstone)
struct GodstoneInfo {
    uint32_t godstoneItemId;
    std::string name;
    float    procChancePercent; // ex: 1.0f para 1%, 2.0f para 2%
    uint16_t abnormalStatus;    // Stun, Silence, Paralyze, Blind...
    int32_t  procDamage;        // ex: 3700 de dano de fogo
    uint32_t durationMs;        // duração do CC em ms
};

// Estrutura de Pedra de Mana (Manastone)
struct ManastoneInfo {
    uint32_t itemId;
    std::string statType; // "Crit", "Attack", "HP", "MagicBoost", "Accuracy"
    int32_t  statValue;   // +17, +5, +85, +27...
};

// Fusão de Arma de Duas Mãos (Armsfusion)
struct ArmsfusionInfo {
    bool     isFused;
    uint32_t secondaryWeaponItemId;
    int32_t  inheritedBaseDamage; // 10% do dano base
    std::vector<ManastoneInfo> extraManastones;
};

// Item Completo com Encantamento, Soquetes e Godstone
struct ItemSlotInfo {
    uint32_t objectId;
    uint32_t itemId;
    uint32_t count;
    std::string name;
    uint32_t itemLevel;
    uint8_t  itemQuality;      // 0: Common, 1: Rare, 2: Legend, 3: Unique, 4: Epic, 5: Mythic
    int32_t  enchantLevel;     // +0 até +15
    uint8_t  maxSockets;       // 3 a 6 slots de manastone
    std::vector<ManastoneInfo> socketedManastones;
    bool     hasGodstone;
    GodstoneInfo godstone;
    bool     isTwoHandedWeapon;
    ArmsfusionInfo armsfusion;
};

// -------------------------------------------------------------
// 6.4 Casa de Leilões (Broker) e Comércio Privado
// -------------------------------------------------------------
struct BrokerListing {
    uint64_t listingId;
    uint32_t sellerPlayerId;
    ItemSlotInfo item;
    int64_t  unitPrice;
    int64_t  totalPrice;
    int64_t  depositFee; // 2% taxa de registro
    uint64_t registrationTimeMs;
};

// Sessão de Troca Segura (Trade Session)
struct TradeSession {
    uint32_t player1Id;
    uint32_t player2Id;
    std::vector<ItemSlotInfo> player1Items;
    int64_t  player1Kinah;
    bool     player1Locked;
    bool     player1Confirmed;
    std::vector<ItemSlotInfo> player2Items;
    int64_t  player2Kinah;
    bool     player2Locked;
    bool     player2Confirmed;
    bool     isTradeComplete;
};

// Gerenciador de Inventário, Cubo, Armazéns, Encantamentos e Economia
class InventoryManager {
public:
    static InventoryManager& GetInstance();

    InventoryManager();
    ~InventoryManager();

    bool Initialize(size_t initialCubeSlots = 27);
    void Shutdown();

    // Gestão de Moedas (Kinah & AP)
    int64_t GetKinah() const { return m_kinah; }
    void AddKinah(int64_t amount);
    bool SubKinah(int64_t amount);

    uint32_t GetAp() const { return m_ap; }
    void AddAp(uint32_t amount);
    bool SubAp(uint32_t amount);

    // 6.2 Cubo e Expansão (27 até 108 slots)
    bool AddItem(uint32_t itemId, uint32_t count, const std::string& name, uint32_t itemLevel = 1, uint8_t quality = 1);
    bool RemoveItem(uint32_t itemId, uint32_t count);
    const ItemSlotInfo* GetBagItem(size_t slotIndex) const;
    ItemSlotInfo* GetBagItemModifiable(size_t slotIndex);
    size_t GetMaxCubeSlots() const { return m_maxCubeSlots; }
    bool ExpandCube(size_t additionalSlots = 9);

    // 6.2 Armazéns (Personal, Account, Legion)
    bool AddToWarehouse(uint8_t warehouseType, const ItemSlotInfo& item); // 0: Personal, 1: Account, 2: Legion
    bool RemoveFromWarehouse(uint8_t warehouseType, size_t slotIndex, ItemSlotInfo& outItem);
    size_t GetWarehouseItemCount(uint8_t warehouseType) const;

    // 6.1 Equipamentos Corporais (16 Slots)
    bool EquipItem(size_t bagSlot, EquipSlot equipSlot);
    bool UnequipItem(EquipSlot equipSlot);
    const ItemSlotInfo* GetEquippedItem(EquipSlot equipSlot) const;

    // 6.3.1 Encantamento de Itens (L1 - L120)
    bool EnchantItem(EquipSlot equipSlot, uint32_t stoneLevel, float supplementBonusChance, bool& outSuccess, std::string& outMsg);

    // 6.3.2 Pedras de Mana (Manastones)
    bool SocketManastone(EquipSlot equipSlot, const ManastoneInfo& stone, float baseChance, bool& outSuccess, std::string& outMsg);

    // 6.3.3 Pedras Divinas (Godstones)
    bool SocketGodstone(EquipSlot equipSlot, const GodstoneInfo& godstone, std::string& outMsg);

    // 6.3.4 Fusão de Armas de Duas Mãos (Armsfusion)
    bool FuseTwoHandWeapons(EquipSlot mainSlot, size_t sacrificeBagSlot, std::string& outMsg);

    // 6.4 Casa de Leilões (Broker)
    uint64_t BrokerList(uint32_t sellerId, size_t bagSlot, int64_t unitPrice, uint32_t count, std::string& outMsg);
    bool BrokerBuy(uint32_t buyerId, uint64_t listingId, std::string& outMsg);

    // 6.4 Comércio Privado (Trade)
    TradeSession CreateTradeSession(uint32_t p1, uint32_t p2);
    bool LockTrade(TradeSession& session, uint32_t playerId);
    bool ConfirmTrade(TradeSession& session, uint32_t playerId);

private:
    int64_t m_kinah;
    uint32_t m_ap;
    size_t m_maxCubeSlots; // De 27 a 108 slots
    std::vector<ItemSlotInfo> m_bag;
    std::unordered_map<uint8_t, ItemSlotInfo> m_equipment;

    // Armazéns
    std::vector<ItemSlotInfo> m_personalWarehouse; // até 96 slots
    std::vector<ItemSlotInfo> m_accountWarehouse;  // até 32 slots
    std::vector<ItemSlotInfo> m_legionWarehouse;   // até 128 slots

    // Broker
    std::unordered_map<uint64_t, BrokerListing> m_brokerListings;
    uint64_t m_nextListingId;

    mutable std::mutex m_invMutex;
};
