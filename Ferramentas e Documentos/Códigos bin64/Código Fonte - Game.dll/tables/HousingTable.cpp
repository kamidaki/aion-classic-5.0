#include "HousingTable.h"
#include "../core/GameLog.h"

// Implementação de HousingBuildingTable
HousingBuildingTable::HousingBuildingTable() {
    LoadTable();
}

HousingBuildingTable::~HousingBuildingTable() {
    m_buildings.clear();
}

bool HousingBuildingTable::LoadTable() {
    m_buildings.clear();

    HousingBuildingTemplate b1{ 1, "Studio Apartment", 1, 0, 16 };
    HousingBuildingTemplate b2{ 2, "House", 2, 50000, 32 };
    HousingBuildingTemplate b3{ 3, "Mansion", 3, 200000, 64 };
    HousingBuildingTemplate b4{ 4, "Estate", 4, 1000000, 128 };

    m_buildings[b1.id] = b1;
    m_buildings[b2.id] = b2;
    m_buildings[b3.id] = b3;
    m_buildings[b4.id] = b4;

    GameLog_Info("HousingBuildingTable carregada com sucesso (%zu construções)", m_buildings.size());
    return true;
}

const HousingBuildingTemplate* HousingBuildingTable::GetBuilding(uint32_t id) const {
    auto it = m_buildings.find(id);
    if (it != m_buildings.end()) {
        return &it->second;
    }
    return nullptr;
}

// Implementação de HousingAddressTable
HousingAddressTable::HousingAddressTable() {
    LoadTable();
}

HousingAddressTable::~HousingAddressTable() {
    m_addresses.clear();
}

bool HousingAddressTable::LoadTable() {
    m_addresses.clear();

    HousingAddressTemplate a1{ 10001, 700010000, 1, Vec3F(500.0f, 600.0f, 200.0f), 1 };
    HousingAddressTemplate a2{ 10002, 700010000, 2, Vec3F(550.0f, 620.0f, 205.0f), 1 };

    m_addresses[a1.addressId] = a1;
    m_addresses[a2.addressId] = a2;

    GameLog_Info("HousingAddressTable carregada com sucesso (%zu endereços)", m_addresses.size());
    return true;
}

const HousingAddressTemplate* HousingAddressTable::GetAddress(uint32_t addressId) const {
    auto it = m_addresses.find(addressId);
    if (it != m_addresses.end()) {
        return &it->second;
    }
    return nullptr;
}
