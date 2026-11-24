#include "FlyPathTable.h"
#include "../core/GameLog.h"

FlyPathTable::FlyPathTable() : m_bLoaded(false) {
    LoadTable();
}

FlyPathTable::~FlyPathTable() {
    m_paths.clear();
}

bool FlyPathTable::LoadTable() {
    m_paths.clear();
    m_paths[1] = 10001;
    m_paths[2] = 10002;
    m_bLoaded = true;
    GameLog_Info("FlyPathTable carregada com sucesso (%zu rotas).", m_paths.size());
    return true;
}

bool FlyPathTable::HasFlyPath(uint32_t id) const {
    return m_paths.find(id) != m_paths.end();
}
