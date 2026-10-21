#include "ComplexPathSector.h"
#include <cmath>
#include <cstring>

ComplexPathSector::ComplexPathSector(int32_t sectorX, int32_t sectorY)
    : PathSector(sectorX, sectorY)
{
    std::memset(m_heights, 0, sizeof(m_heights));
    std::memset(m_walkable, 1, sizeof(m_walkable));
}

ComplexPathSector::~ComplexPathSector() {
}

float ComplexPathSector::GetHeight(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0) gx = 0; if (gx > 63) gx = 63;
    if (gy < 0) gy = 0; if (gy > 63) gy = 63;

    return m_heights[gy][gx];
}

bool ComplexPathSector::IsWalkable(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0 || gx > 63 || gy < 0 || gy > 63) return false;

    return m_walkable[gy][gx];
}

float ComplexPathSector::GetHeightAtLayer(float localX, float localY, float currentZ) const {
    float h = GetHeight(localX, localY);
    return (std::abs(currentZ - h) < 5.0f) ? h : currentZ;
}

void ComplexPathSector::AddLayer(int gridX, int gridY, float minZ, float maxZ, bool walkable) {
    if (gridX >= 0 && gridX < 64 && gridY >= 0 && gridY < 64) {
        m_heights[gridY][gridX] = maxZ;
        m_walkable[gridY][gridX] = walkable;
    }
}
