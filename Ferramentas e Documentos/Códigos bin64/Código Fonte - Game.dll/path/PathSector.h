#pragma once
#include <cstdint>
#include <vector>
#include "../ai/AIObject.h" // Vec3F

// Nó de navegação para busca de caminhos (A*) extraído do RTTI (.?AVPathFindNode@@)
class PathFindNode {
public:
    PathFindNode(uint32_t id, const Vec3F& pos);
    ~PathFindNode();

    uint32_t GetId() const { return m_id; }
    const Vec3F& GetPosition() const { return m_position; }

    void AddNeighbor(PathFindNode* pNeighbor, float distance);
    const std::vector<std::pair<PathFindNode*, float>>& GetNeighbors() const { return m_neighbors; }

private:
    uint32_t m_id;
    Vec3F m_position;
    std::vector<std::pair<PathFindNode*, float>> m_neighbors;
};

// Ponto de navegação no mapa (.?AVNavigationPoint@@)
class NavigationPoint {
public:
    NavigationPoint(float x, float y, float z, uint32_t flag = 0);
    Vec3F position;
    uint32_t flag;
};

// Classe base canônica de setor de malha de navegação extraída do RTTI (.?AVPathSector@@)
class PathSector {
public:
    PathSector(int32_t sectorX, int32_t sectorY);
    virtual ~PathSector();

    int32_t GetSectorX() const { return m_sectorX; }
    int32_t GetSectorY() const { return m_sectorY; }

    virtual float GetHeight(float localX, float localY) const = 0;
    virtual bool IsWalkable(float localX, float localY) const = 0;
    virtual const char* GetSectorType() const = 0;

protected:
    int32_t m_sectorX;
    int32_t m_sectorY;
};

// Setor plano uniforme (.?AVFlatPathSector@@)
class FlatPathSector : public PathSector {
public:
    FlatPathSector(int32_t sectorX, int32_t sectorY, float flatZ);
    virtual ~FlatPathSector();

    virtual float GetHeight(float localX, float localY) const override { return m_flatZ; }
    virtual bool IsWalkable(float localX, float localY) const override { return true; }
    virtual const char* GetSectorType() const override { return "FlatPathSector"; }

protected:
    float m_flatZ;
};

// Setor plano com ligação a setores adjacentes (.?AVFlatPathSectorWithLink@@)
class FlatPathSectorWithLink : public FlatPathSector {
public:
    FlatPathSectorWithLink(int32_t sectorX, int32_t sectorY, float flatZ);
    virtual ~FlatPathSectorWithLink();

    virtual const char* GetSectorType() const override { return "FlatPathSectorWithLink"; }
};
