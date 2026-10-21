#pragma once
#include "PathSector.h"
#include <vector>

// Setor simples com grade de elevação 64x64 (.?AVSimplePathSector@@)
class SimplePathSector : public PathSector {
public:
    SimplePathSector(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector();

    virtual float GetHeight(float localX, float localY) const override;
    virtual bool IsWalkable(float localX, float localY) const override;
    virtual const char* GetSectorType() const override { return "SimplePathSector"; }

    void SetHeightAt(int gridX, int gridY, float height);

protected:
    float m_baseZ;
    float m_grid[64][64];
    bool  m_walkable[64][64];
};

// Variação comprimida de 1 bit (.?AVSimplePathSector1BitIndexZ@@)
class SimplePathSector1BitIndexZ : public SimplePathSector {
public:
    SimplePathSector1BitIndexZ(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector1BitIndexZ();
    virtual const char* GetSectorType() const override { return "SimplePathSector1BitIndexZ"; }
};

// Variação de 1 bit com link (.?AVSimplePathSector1BitIndexZWithLink@@)
class SimplePathSector1BitIndexZWithLink : public SimplePathSector1BitIndexZ {
public:
    SimplePathSector1BitIndexZWithLink(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector1BitIndexZWithLink();
    virtual const char* GetSectorType() const override { return "SimplePathSector1BitIndexZWithLink"; }
};

// Variação comprimida de 1 byte delta (.?AVSimplePathSector1ByteDeltaZ@@)
class SimplePathSector1ByteDeltaZ : public SimplePathSector {
public:
    SimplePathSector1ByteDeltaZ(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector1ByteDeltaZ();
    virtual const char* GetSectorType() const override { return "SimplePathSector1ByteDeltaZ"; }
};

// Variação de 1 byte delta com link (.?AVSimplePathSector1ByteDeltaZWithLink@@)
class SimplePathSector1ByteDeltaZWithLink : public SimplePathSector1ByteDeltaZ {
public:
    SimplePathSector1ByteDeltaZWithLink(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector1ByteDeltaZWithLink();
    virtual const char* GetSectorType() const override { return "SimplePathSector1ByteDeltaZWithLink"; }
};

// Variação de 2 bits (.?AVSimplePathSector2BitIndexZ@@)
class SimplePathSector2BitIndexZ : public SimplePathSector {
public:
    SimplePathSector2BitIndexZ(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector2BitIndexZ();
    virtual const char* GetSectorType() const override { return "SimplePathSector2BitIndexZ"; }
};

// Variação de 2 bits com link (.?AVSimplePathSector2BitIndexZWithLink@@)
class SimplePathSector2BitIndexZWithLink : public SimplePathSector2BitIndexZ {
public:
    SimplePathSector2BitIndexZWithLink(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector2BitIndexZWithLink();
    virtual const char* GetSectorType() const override { return "SimplePathSector2BitIndexZWithLink"; }
};

// Variação de 2 bytes delta (.?AVSimplePathSector2ByteDeltaZ@@)
class SimplePathSector2ByteDeltaZ : public SimplePathSector {
public:
    SimplePathSector2ByteDeltaZ(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector2ByteDeltaZ();
    virtual const char* GetSectorType() const override { return "SimplePathSector2ByteDeltaZ"; }
};

// Variação de 2 bytes delta com link (.?AVSimplePathSector2ByteDeltaZWithLink@@)
class SimplePathSector2ByteDeltaZWithLink : public SimplePathSector2ByteDeltaZ {
public:
    SimplePathSector2ByteDeltaZWithLink(int32_t sectorX, int32_t sectorY, float baseZ);
    virtual ~SimplePathSector2ByteDeltaZWithLink();
    virtual const char* GetSectorType() const override { return "SimplePathSector2ByteDeltaZWithLink"; }
};
