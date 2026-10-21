#include "ComplexPathSector.h"
#include <cmath>

ComplexPathSector::ComplexPathSector(int32_t sectorX, int32_t sectorY)
    : PathSector(sectorX, sectorY)
{
}

ComplexPathSector::~ComplexPathSector() {
}

float ComplexPathSector::GetHeight(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0) gx = 0; if (gx > 63) gx = 63;
    if (gy < 0) gy = 0; if (gy > 63) gy = 63;

    const auto& layers = m_cells[gy][gx].layers;
    if (layers.empty()) return 0.0f;
    return layers[0].maxZ;
}

bool ComplexPathSector::IsWalkable(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0 || gx > 63 || gy < 0 || gy > 63) return false;

    const auto& layers = m_cells[gy][gx].layers;
    if (layers.empty()) return false;
    return layers[0].walkable;
}

float ComplexPathSector::GetHeightAtLayer(float localX, float localY, float currentZ) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0) gx = 0; if (gx > 63) gx = 63;
    if (gy < 0) gy = 0; if (gy > 63) gy = 63;

    const auto& layers = m_cells[gy][gx].layers;
    if (layers.empty()) return currentZ;

    float bestZ = layers[0].maxZ;
    float minDiff = std::abs(currentZ - bestZ);

    for (size_t i = 1; i < layers.size(); ++i) {
        float diff = std::abs(currentZ - layers[i].maxZ);
        if (diff < minDiff) {
            minDiff = diff;
            bestZ = layers[i].maxZ;
        }
    }
    return bestZ;
}

void ComplexPathSector::AddLayer(int gridX, int gridY, float minZ, float maxZ, bool walkable) {
    if (gridX >= 0 && gridX < 64 && gridY >= 0 && gridY < 64) {
        m_cells[gridY][gridX].layers.push_back({ minZ, maxZ, walkable });
    }
}
