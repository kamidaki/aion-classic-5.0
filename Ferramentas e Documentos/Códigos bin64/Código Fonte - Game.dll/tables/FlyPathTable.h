#pragma once
#include <cstdint>
#include <vector>
#include <unordered_map>
#include "../ai/AIObject.h" // Vec3F

struct FlyPathNode {
    Vec3F position;
    float time;
};

struct FlyPathTemplate {
    uint32_t id;
    uint32_t startWorldId;
    uint32_t endWorldId;
    uint32_t costKinah;
    float totalTime;
    std::vector<FlyPathNode> waypoints;
};

// Tabela canônica de rotas de voo e teleporte de voo extraída do RTTI (.?AVFlyPathTable@@)
class FlyPathTable {
public:
    FlyPathTable();
    ~FlyPathTable();

    bool LoadTable();
    const FlyPathTemplate* GetFlyPath(uint32_t id) const;

private:
    std::unordered_map<uint32_t, FlyPathTemplate> m_paths;
};
