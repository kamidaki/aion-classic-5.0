#pragma once
#include <cstdint>
#include <string>
#include <unordered_map>
#include "../ai/AIObject.h" // Vec3F

struct HousingBuildingTemplate {
    uint32_t id;
    std::string name;
    uint32_t buildingType; // House, Mansion, Estate, Palace
    uint32_t rentCostPerWeek;
    uint32_t storageCapacity;
};

struct HousingAddressTemplate {
    uint32_t addressId;
    uint32_t mapId;
    uint32_t buildingId;
    Vec3F doorPosition;
    uint32_t zoneId;
};

// Tabelas canônicas do sistema habitacional extraídas do RTTI
// .?AVHousingBuildingTable@@
class HousingBuildingTable {
public:
    HousingBuildingTable();
    ~HousingBuildingTable();

    bool LoadTable();
    const HousingBuildingTemplate* GetBuilding(uint32_t id) const;

private:
    std::unordered_map<uint32_t, HousingBuildingTemplate> m_buildings;
};

// .?AVHousingAddressTable@@
class HousingAddressTable {
public:
    HousingAddressTable();
    ~HousingAddressTable();

    bool LoadTable();
    const HousingAddressTemplate* GetAddress(uint32_t addressId) const;

private:
    std::unordered_map<uint32_t, HousingAddressTemplate> m_addresses;
};
