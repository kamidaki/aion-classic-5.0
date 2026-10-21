#include "PathSector.h"
#include "../core/GameLog.h"

// PathFindNode
PathFindNode::PathFindNode(uint32_t id, const Vec3F& pos)
    : m_id(id), m_position(pos)
{
}

PathFindNode::~PathFindNode() {
    m_neighbors.clear();
}

void PathFindNode::AddNeighbor(PathFindNode* pNeighbor, float distance) {
    if (pNeighbor) {
        m_neighbors.push_back({ pNeighbor, distance });
    }
}

// NavigationPoint
NavigationPoint::NavigationPoint(float x, float y, float z, uint32_t f)
    : position(x, y, z), flag(f)
{
}

// PathSector
PathSector::PathSector(int32_t sectorX, int32_t sectorY)
    : m_sectorX(sectorX), m_sectorY(sectorY)
{
}

PathSector::~PathSector() {
}

// FlatPathSector
FlatPathSector::FlatPathSector(int32_t sectorX, int32_t sectorY, float flatZ)
    : PathSector(sectorX, sectorY), m_flatZ(flatZ)
{
}

FlatPathSector::~FlatPathSector() {
}

// FlatPathSectorWithLink
FlatPathSectorWithLink::FlatPathSectorWithLink(int32_t sectorX, int32_t sectorY, float flatZ)
    : FlatPathSector(sectorX, sectorY, flatZ)
{
}

FlatPathSectorWithLink::~FlatPathSectorWithLink() {
}

// TerrainPathSector
TerrainPathSector::TerrainPathSector(int32_t sectorX, int32_t sectorY)
    : PathSector(sectorX, sectorY)
{
}

TerrainPathSector::~TerrainPathSector() {
}

float TerrainPathSector::GetHeight(float localX, float localY) const {
    (void)localX;
    (void)localY;
    return 0.0f;
}

bool TerrainPathSector::IsWalkable(float localX, float localY) const {
    (void)localX;
    (void)localY;
    return true;
}

// TerrainPathSectorWithLink
TerrainPathSectorWithLink::TerrainPathSectorWithLink(int32_t sectorX, int32_t sectorY)
    : TerrainPathSector(sectorX, sectorY)
{
}

TerrainPathSectorWithLink::~TerrainPathSectorWithLink() {
}
