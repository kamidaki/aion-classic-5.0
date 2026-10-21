#pragma once
#include "PathSector.h"
#include <vector>

struct ComplexPathLayer {
    float minZ;
    float maxZ;
    bool walkable;
};

struct ComplexPathCell {
    std::vector<ComplexPathLayer> layers;
};

// Setor complexo com múltiplas camadas verticais (pontes, túneis) extraído do RTTI (.?AVComplexPathSector@@)
class ComplexPathSector : public PathSector {
public:
    ComplexPathSector(int32_t sectorX, int32_t sectorY);
    virtual ~ComplexPathSector();

    virtual float GetHeight(float localX, float localY) const override;
    virtual bool IsWalkable(float localX, float localY) const override;
    virtual const char* GetSectorType() const override { return "ComplexPathSector"; }

    float GetHeightAtLayer(float localX, float localY, float currentZ) const;
    void AddLayer(int gridX, int gridY, float minZ, float maxZ, bool walkable);

private:
    ComplexPathCell m_cells[64][64];
};
