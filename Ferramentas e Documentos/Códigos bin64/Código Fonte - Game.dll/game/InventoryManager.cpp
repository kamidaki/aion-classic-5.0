#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "InventoryManager.h"
#include "../core/GameLog.h"
#include <cstdlib>
#include <algorithm>

InventoryManager& InventoryManager::GetInstance() {
    static InventoryManager s_instance;
    return s_instance;
}

InventoryManager::InventoryManager()
    : m_kinah(0)
    , m_ap(0)
    , m_maxCubeSlots(27)
    , m_nextListingId(1)
{
}

InventoryManager::~InventoryManager() {
    Shutdown();
}

bool InventoryManager::Initialize(size_t initialCubeSlots) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    m_maxCubeSlots = (initialCubeSlots > 108) ? 108 : initialCubeSlots;
    m_bag.clear();
    m_bag.resize(m_maxCubeSlots);
    m_equipment.clear();
    m_personalWarehouse.clear();
    m_accountWarehouse.clear();
    m_legionWarehouse.clear();
    m_brokerListings.clear();
    m_kinah = 10000;
    m_ap = 0;
    GameLog_Info("InventoryManager inicializado (%zu slots de cubo, %lld Kinah).", m_maxCubeSlots, m_kinah);
    return true;
}

void InventoryManager::Shutdown() {
    std::lock_guard<std::mutex> lock(m_invMutex);
    m_bag.clear();
    m_equipment.clear();
    m_personalWarehouse.clear();
    m_accountWarehouse.clear();
    m_legionWarehouse.clear();
    m_brokerListings.clear();
    m_kinah = 0;
    m_ap = 0;
}

void InventoryManager::AddKinah(int64_t amount) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (amount > 0) {
        m_kinah += amount;
        GameLog_Info("InventoryManager: +%lld Kinah (Total: %lld)", amount, m_kinah);
    }
}

bool InventoryManager::SubKinah(int64_t amount) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (amount <= 0 || m_kinah < amount) return false;
    m_kinah -= amount;
    GameLog_Info("InventoryManager: -%lld Kinah (Total: %lld)", amount, m_kinah);
    return true;
}

void InventoryManager::AddAp(uint32_t amount) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    m_ap += amount;
    GameLog_Info("InventoryManager: +%u AP (Total: %u)", amount, m_ap);
}

bool InventoryManager::SubAp(uint32_t amount) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (amount == 0 || m_ap < amount) return false;
    m_ap -= amount;
    GameLog_Info("InventoryManager: -%u AP (Total: %u)", amount, m_ap);
    return true;
}

// -------------------------------------------------------------
// 6.2 Cubo e Expansão (27 até 108 slots)
// -------------------------------------------------------------
bool InventoryManager::ExpandCube(size_t additionalSlots) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (m_maxCubeSlots >= 108) {
        GameLog_Info("InventoryManager: Cubo ja atingiu o teto maximo de 108 slots.");
        return false;
    }
    size_t newTotal = m_maxCubeSlots + additionalSlots;
    if (newTotal > 108) newTotal = 108;
    m_maxCubeSlots = newTotal;
    m_bag.resize(m_maxCubeSlots);
    GameLog_Info("InventoryManager: Cubo expandido para %zu slots!", m_maxCubeSlots);
    return true;
}

bool InventoryManager::AddItem(uint32_t itemId, uint32_t count, const std::string& name, uint32_t itemLevel, uint8_t quality) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    for (auto& slot : m_bag) {
        if (slot.itemId == itemId) {
            slot.count += count;
            return true;
        }
    }

    for (size_t i = 0; i < m_bag.size(); ++i) {
        if (m_bag[i].itemId == 0) {
            m_bag[i].objectId = static_cast<uint32_t>(100000 + i);
            m_bag[i].itemId = itemId;
            m_bag[i].count = count;
            m_bag[i].name = name;
            m_bag[i].itemLevel = itemLevel;
            m_bag[i].itemQuality = quality;
            m_bag[i].enchantLevel = 0;
            m_bag[i].maxSockets = (quality >= 3) ? 5 : 4;
            m_bag[i].hasGodstone = false;
            m_bag[i].isTwoHandedWeapon = false;
            m_bag[i].armsfusion.isFused = false;
            return true;
        }
    }
    return false;
}

bool InventoryManager::RemoveItem(uint32_t itemId, uint32_t count) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    for (auto& slot : m_bag) {
        if (slot.itemId == itemId) {
            if (slot.count >= count) {
                slot.count -= count;
                if (slot.count == 0) {
                    slot = ItemSlotInfo();
                }
                return true;
            }
        }
    }
    return false;
}

const ItemSlotInfo* InventoryManager::GetBagItem(size_t slotIndex) const {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (slotIndex < m_bag.size() && m_bag[slotIndex].itemId != 0) {
        return &m_bag[slotIndex];
    }
    return nullptr;
}

ItemSlotInfo* InventoryManager::GetBagItemModifiable(size_t slotIndex) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (slotIndex < m_bag.size() && m_bag[slotIndex].itemId != 0) {
        return &m_bag[slotIndex];
    }
    return nullptr;
}

// -------------------------------------------------------------
// 6.2 Armazéns (Personal, Account, Legion)
// -------------------------------------------------------------
bool InventoryManager::AddToWarehouse(uint8_t warehouseType, const ItemSlotInfo& item) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    std::vector<ItemSlotInfo>* wh = nullptr;
    size_t capacity = 0;

    switch (warehouseType) {
        case 0: wh = &m_personalWarehouse; capacity = 96; break;
        case 1: wh = &m_accountWarehouse; capacity = 32; break;
        case 2: wh = &m_legionWarehouse; capacity = 128; break;
        default: return false;
    }

    if (wh->size() >= capacity) return false;
    wh->push_back(item);
    return true;
}

bool InventoryManager::RemoveFromWarehouse(uint8_t warehouseType, size_t slotIndex, ItemSlotInfo& outItem) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    std::vector<ItemSlotInfo>* wh = nullptr;

    switch (warehouseType) {
        case 0: wh = &m_personalWarehouse; break;
        case 1: wh = &m_accountWarehouse; break;
        case 2: wh = &m_legionWarehouse; break;
        default: return false;
    }

    if (slotIndex >= wh->size()) return false;
    outItem = (*wh)[slotIndex];
    wh->erase(wh->begin() + slotIndex);
    return true;
}

size_t InventoryManager::GetWarehouseItemCount(uint8_t warehouseType) const {
    std::lock_guard<std::mutex> lock(m_invMutex);
    switch (warehouseType) {
        case 0: return m_personalWarehouse.size();
        case 1: return m_accountWarehouse.size();
        case 2: return m_legionWarehouse.size();
        default: return 0;
    }
}

// -------------------------------------------------------------
// 6.1 Gestão dos 16 Slots de Equipamento Corporal
// -------------------------------------------------------------
bool InventoryManager::EquipItem(size_t bagSlot, EquipSlot equipSlot) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (bagSlot >= m_bag.size() || m_bag[bagSlot].itemId == 0) return false;

    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    ItemSlotInfo itemToEquip = m_bag[bagSlot];
    m_bag[bagSlot] = ItemSlotInfo(); // Remove da bolsa

    auto it = m_equipment.find(slotIdx);
    if (it != m_equipment.end()) {
        // Desequipa o item antigo e coloca de volta na bolsa
        for (auto& bSlot : m_bag) {
            if (bSlot.itemId == 0) {
                bSlot = it->second;
                break;
            }
        }
    }

    m_equipment[slotIdx] = itemToEquip;
    GameLog_Info("InventoryManager: Item=%u (%s) equipado no Slot=%u", itemToEquip.itemId, itemToEquip.name.c_str(), slotIdx);
    return true;
}

bool InventoryManager::UnequipItem(EquipSlot equipSlot) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    auto it = m_equipment.find(slotIdx);
    if (it == m_equipment.end()) return false;

    // Busca slot livre na bolsa
    for (auto& bSlot : m_bag) {
        if (bSlot.itemId == 0) {
            bSlot = it->second;
            m_equipment.erase(it);
            GameLog_Info("InventoryManager: Item desequipado do Slot=%u para bolsa", slotIdx);
            return true;
        }
    }
    return false; // Bolsa cheia
}

const ItemSlotInfo* InventoryManager::GetEquippedItem(EquipSlot equipSlot) const {
    std::lock_guard<std::mutex> lock(m_invMutex);
    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    auto it = m_equipment.find(slotIdx);
    if (it != m_equipment.end()) {
        return &it->second;
    }
    return nullptr;
}

// -------------------------------------------------------------
// 6.3.1 Encantamento de Itens (L1 - L120)
// -------------------------------------------------------------
bool InventoryManager::EnchantItem(EquipSlot equipSlot, uint32_t stoneLevel, float supplementBonusChance, bool& outSuccess, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    auto it = m_equipment.find(slotIdx);
    if (it == m_equipment.end()) {
        outMsg = "Nenhum equipamento presente no slot informado.";
        return false;
    }

    ItemSlotInfo& eq = it->second;
    if (eq.enchantLevel >= 15) {
        outMsg = "Equipamento ja atingiu o teto maximo de encantamento (+15).";
        return false;
    }

    // Fórmula Canônica de Chance:
    // Base 50% + (Nível da Pedra - Nível do Item) * 1.0% + Bônus de Suplemento
    float chance = 50.0f + (static_cast<float>(stoneLevel) - static_cast<float>(eq.itemLevel)) * 1.0f + supplementBonusChance;
    float maxCap = (supplementBonusChance > 0.0f) ? 95.0f : 80.0f;
    if (chance > maxCap) chance = maxCap;
    if (chance < 10.0f) chance = 10.0f;

    float roll = static_cast<float>(rand() % 100);
    if (roll < chance) {
        // Sucesso
        eq.enchantLevel = (std::min)(15, eq.enchantLevel + 1);
        outSuccess = true;
        outMsg = "Encantamento bem-sucedido! Nivel atual: +" + std::to_string(eq.enchantLevel);
    } else {
        // Falha: penalidade de -1
        eq.enchantLevel = (std::max)(0, eq.enchantLevel - 1);
        outSuccess = false;
        outMsg = "Falha no encantamento! Penalidade aplicada: +" + std::to_string(eq.enchantLevel);
    }
    return true;
}

// -------------------------------------------------------------
// 6.3.2 Pedras de Mana (Manastones)
// -------------------------------------------------------------
bool InventoryManager::SocketManastone(EquipSlot equipSlot, const ManastoneInfo& stone, float baseChance, bool& outSuccess, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    auto it = m_equipment.find(slotIdx);
    if (it == m_equipment.end()) {
        outMsg = "Equipamento nao encontrado.";
        return false;
    }

    ItemSlotInfo& eq = it->second;
    if (eq.socketedManastones.size() >= eq.maxSockets) {
        outMsg = "Todos os slots de pedra de mana estao ocupados.";
        return false;
    }

    float roll = static_cast<float>(rand() % 100);
    if (roll < baseChance) {
        // Sucesso: adiciona a pedra
        eq.socketedManastones.push_back(stone);
        outSuccess = true;
        outMsg = "Pedra de Mana inserida com sucesso! Slots preenchidos: " + std::to_string(eq.socketedManastones.size()) + "/" + std::to_string(eq.maxSockets);
    } else {
        // REGRA CANÔNICA DE AION: Falha destrói TODAS as pedras previamente inseridas na peça!
        eq.socketedManastones.clear();
        outSuccess = false;
        outMsg = "Falha ao engastar Pedra de Mana! Todas as pedras de mana do item foram destruidas!";
    }
    return true;
}

// -------------------------------------------------------------
// 6.3.3 Pedras Divinas (Godstones)
// -------------------------------------------------------------
bool InventoryManager::SocketGodstone(EquipSlot equipSlot, const GodstoneInfo& godstone, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (equipSlot != EquipSlot::MainHand && equipSlot != EquipSlot::SubHand) {
        outMsg = "Pedras Divinas so podem ser engastadas em armas.";
        return false;
    }

    uint8_t slotIdx = static_cast<uint8_t>(equipSlot);
    auto it = m_equipment.find(slotIdx);
    if (it == m_equipment.end()) {
        outMsg = "Arma nao encontrada.";
        return false;
    }

    it->second.hasGodstone = true;
    it->second.godstone = godstone;
    outMsg = "Pedra Divina (" + godstone.name + ") engastada com sucesso!";
    return true;
}

// -------------------------------------------------------------
// 6.3.4 Fusão de Armas de Duas Mãos (Armsfusion)
// -------------------------------------------------------------
bool InventoryManager::FuseTwoHandWeapons(EquipSlot mainSlot, size_t sacrificeBagSlot, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    uint8_t slotIdx = static_cast<uint8_t>(mainSlot);
    auto it = m_equipment.find(slotIdx);
    if (it == m_equipment.end()) {
        outMsg = "Arma principal nao equipada.";
        return false;
    }

    ItemSlotInfo& mainWeapon = it->second;
    if (mainWeapon.armsfusion.isFused) {
        outMsg = "Arma principal ja se encontra fundida.";
        return false;
    }

    if (sacrificeBagSlot >= m_bag.size() || m_bag[sacrificeBagSlot].itemId == 0) {
        outMsg = "Arma secundaria para sacrificio nao encontrada.";
        return false;
    }

    ItemSlotInfo& sacrificeWeapon = m_bag[sacrificeBagSlot];

    // Fusão Canônica:
    // Herda 10% do dano base da secundária e slots extras de Manastone
    mainWeapon.armsfusion.isFused = true;
    mainWeapon.armsfusion.secondaryWeaponItemId = sacrificeWeapon.itemId;
    mainWeapon.armsfusion.inheritedBaseDamage = static_cast<int32_t>(sacrificeWeapon.itemLevel * 3.5f); // 10% base
    mainWeapon.maxSockets += sacrificeWeapon.maxSockets; // Soquetes extras herdados

    // Consome a arma sacrificada da bolsa
    sacrificeWeapon = ItemSlotInfo();

    outMsg = "Fusao de Armas (Armsfusion) realizada com sucesso! Bônus de dano herdado: +" + std::to_string(mainWeapon.armsfusion.inheritedBaseDamage);
    return true;
}

// -------------------------------------------------------------
// 6.4 Casa de Leilões (Broker)
// -------------------------------------------------------------
uint64_t InventoryManager::BrokerList(uint32_t sellerId, size_t bagSlot, int64_t unitPrice, uint32_t count, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    if (bagSlot >= m_bag.size() || m_bag[bagSlot].itemId == 0 || m_bag[bagSlot].count < count) {
        outMsg = "Item invalido ou quantidade insuficiente.";
        return 0;
    }

    int64_t totalPrice = unitPrice * count;
    int64_t depositFee = static_cast<int64_t>(totalPrice * 0.02f); // 2% taxa de registro
    if (depositFee < 10) depositFee = 10;

    if (m_kinah < depositFee) {
        outMsg = "Kinah insuficiente para pagar a taxa de deposito do Broker (2%).";
        return 0;
    }

    m_kinah -= depositFee;

    ItemSlotInfo listedItem = m_bag[bagSlot];
    listedItem.count = count;

    // Deduz da bolsa
    m_bag[bagSlot].count -= count;
    if (m_bag[bagSlot].count == 0) {
        m_bag[bagSlot] = ItemSlotInfo();
    }

    uint64_t id = m_nextListingId++;
    BrokerListing listing = {};
    listing.listingId = id;
    listing.sellerPlayerId = sellerId;
    listing.item = listedItem;
    listing.unitPrice = unitPrice;
    listing.totalPrice = totalPrice;
    listing.depositFee = depositFee;
    m_brokerListings[id] = listing;

    outMsg = "Item listado com sucesso no Broker! ID: " + std::to_string(id);
    return id;
}

bool InventoryManager::BrokerBuy(uint32_t buyerId, uint64_t listingId, std::string& outMsg) {
    std::lock_guard<std::mutex> lock(m_invMutex);
    auto it = m_brokerListings.find(listingId);
    if (it == m_brokerListings.end()) {
        outMsg = "Anúncio expirado ou ja vendido.";
        return false;
    }

    BrokerListing listing = it->second;
    if (m_kinah < listing.totalPrice) {
        outMsg = "Kinah insuficiente para comprar o item.";
        return false;
    }

    // Busca espaço na bolsa do comprador
    bool added = false;
    for (auto& bSlot : m_bag) {
        if (bSlot.itemId == 0) {
            bSlot = listing.item;
            added = true;
            break;
        }
    }

    if (!added) {
        outMsg = "Cubo cheio! Nao ha espaco para receber o item comprado.";
        return false;
    }

    m_kinah -= listing.totalPrice;
    m_brokerListings.erase(it);

    outMsg = "Compra efetuada com sucesso no Broker!";
    return true;
}

// -------------------------------------------------------------
// 6.4 Comércio Privado (Trade)
// -------------------------------------------------------------
TradeSession InventoryManager::CreateTradeSession(uint32_t p1, uint32_t p2) {
    TradeSession session = {};
    session.player1Id = p1;
    session.player2Id = p2;
    session.player1Locked = false;
    session.player1Confirmed = false;
    session.player2Locked = false;
    session.player2Confirmed = false;
    session.isTradeComplete = false;
    return session;
}

bool InventoryManager::LockTrade(TradeSession& session, uint32_t playerId) {
    if (playerId == session.player1Id) {
        session.player1Locked = true;
    } else if (playerId == session.player2Id) {
        session.player2Locked = true;
    } else {
        return false;
    }
    return true;
}

bool InventoryManager::ConfirmTrade(TradeSession& session, uint32_t playerId) {
    if (!session.player1Locked || !session.player2Locked) {
        return false; // Ambos devem travar os itens antes de confirmar
    }

    if (playerId == session.player1Id) {
        session.player1Confirmed = true;
    } else if (playerId == session.player2Id) {
        session.player2Confirmed = true;
    }

    if (session.player1Confirmed && session.player2Confirmed) {
        session.isTradeComplete = true;
        GameLog_Info("TradeSession: Troca concluida com sucesso entre Jogador %u e Jogador %u!", session.player1Id, session.player2Id);
    }
    return true;
}
