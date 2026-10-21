#include "SimplePathSector.h"
#include <cmath>

// SimplePathSector
SimplePathSector::SimplePathSector(int32_t sectorX, int32_t sectorY, float baseZ)
    : PathSector(sectorX, sectorY), m_baseZ(baseZ)
{
    for (int y = 0; y < 64; ++y) {
        for (int x = 0; x < 64; ++x) {
            m_grid[y][x] = baseZ;
            m_walkable[y][x] = true;
        }
    }
}

SimplePathSector::~SimplePathSector() {
}

float SimplePathSector::GetHeight(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0) gx = 0; if (gx > 63) gx = 63;
    if (gy < 0) gy = 0; if (gy > 63) gy = 63;
    return m_grid[gy][gx];
}

bool SimplePathSector::IsWalkable(float localX, float localY) const {
    int gx = static_cast<int>(localX);
    int gy = static_cast<int>(localY);
    if (gx < 0 || gx > 63 || gy < 0 || gy > 63) return false;
    return m_walkable[gy][gx];
}

void SimplePathSector::SetHeightAt(int gridX, int gridY, float height) {
    if (gridX >= 0 && gridX < 64 && gridY >= 0 && gridY < 64) {
        m_grid[gridY][gridX] = height;
    }
}

// 1BitIndexZ
SimplePathSector1BitIndexZ::SimplePathSector1BitIndexZ(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector(sectorX, sectorY, baseZ) {}
SimplePathSector1BitIndexZ::~SimplePathSector1BitIndexZ() {}

// 1BitIndexZWithLink
SimplePathSector1BitIndexZWithLink::SimplePathSector1BitIndexZWithLink(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector1BitIndexZ(sectorX, sectorY, baseZ) {}
SimplePathSector1BitIndexZWithLink::~SimplePathSector1BitIndexZWithLink() {}

// 1ByteDeltaZ
SimplePathSector1ByteDeltaZ::SimplePathSector1ByteDeltaZ(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector(sectorX, sectorY, baseZ) {}
SimplePathSector1ByteDeltaZ::~SimplePathSector1ByteDeltaZ() {}

// 1ByteDeltaZWithLink
SimplePathSector1ByteDeltaZWithLink::SimplePathSector1ByteDeltaZWithLink(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector1ByteDeltaZ(sectorX, sectorY, baseZ) {}
SimplePathSector1ByteDeltaZWithLink::~SimplePathSector1ByteDeltaZWithLink() {}

// 2BitIndexZ
SimplePathSector2BitIndexZ::SimplePathSector2BitIndexZ(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector(sectorX, sectorY, baseZ) {}
SimplePathSector2BitIndexZ::~SimplePathSector2BitIndexZ() {}

// 2BitIndexZWithLink
SimplePathSector2BitIndexZWithLink::SimplePathSector2BitIndexZWithLink(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector2BitIndexZ(sectorX, sectorY, baseZ) {}
SimplePathSector2BitIndexZWithLink::~SimplePathSector2BitIndexZWithLink() {}

// 2ByteDeltaZ
SimplePathSector2ByteDeltaZ::SimplePathSector2ByteDeltaZ(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector(sectorX, sectorY, baseZ) {}
SimplePathSector2ByteDeltaZ::~SimplePathSector2ByteDeltaZ() {}

// 2ByteDeltaZWithLink
SimplePathSector2ByteDeltaZWithLink::SimplePathSector2ByteDeltaZWithLink(int32_t sectorX, int32_t sectorY, float baseZ)
    : SimplePathSector2ByteDeltaZ(sectorX, sectorY, baseZ) {}
SimplePathSector2ByteDeltaZWithLink::~SimplePathSector2ByteDeltaZWithLink() {}
