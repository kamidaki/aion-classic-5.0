#include "FlyPathTable.h"
#include "../core/GameLog.h"

FlyPathTable::FlyPathTable() {
    LoadTable();
}

FlyPathTable::~FlyPathTable() {
    m_paths.clear();
}

bool FlyPathTable::LoadTable() {
    m_paths.clear();

    // Rota canônica de exemplo: Sanctum -> Verteron Observatory
    FlyPathTemplate p1{};
    p1.id = 1;
    p1.startWorldId = 110010000;
    p1.endWorldId = 110010000;
    p1.costKinah = 120;
    p1.totalTime = 15.0f;
    p1.waypoints.push_back({ Vec3F(100.0f, 100.0f, 50.0f), 0.0f });
    p1.waypoints.push_back({ Vec3F(150.0f, 200.0f, 120.0f), 5.0f });
    p1.waypoints.push_back({ Vec3F(200.0f, 300.0f, 60.0f), 15.0f });
    m_paths[p1.id] = p1;

    GameLog_Info("FlyPathTable carregada com sucesso (%zu rotas de voo)", m_paths.size());
    return true;
}

const FlyPathTemplate* FlyPathTable::GetFlyPath(uint32_t id) const {
    auto it = m_paths.find(id);
    if (it != m_paths.end()) {
        return &it->second;
    }
    return nullptr;
}
