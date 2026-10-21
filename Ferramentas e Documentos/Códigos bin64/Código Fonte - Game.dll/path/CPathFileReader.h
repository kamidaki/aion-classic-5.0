#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
#include "PathSector.h" // PathFindNode, Vec3F

// Leitor canônico de malha de navegação e arquivos de caminho do Aion (.?AVCPathFileReader@@)
class CPathFileReader {
public:
    CPathFileReader();
    ~CPathFileReader();

    // 8.1 Carregamento e Decodificação de Malhas Binárias
    bool LoadPathFile(const std::string& filePath);
    bool DecodeHeader(const uint8_t* pData, size_t dataSize);
    bool DecompressDelta1Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]);
    bool DecompressDelta2Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]);

    // Busca de Caminhos (Pathfinding)
    bool FindPath(float startX, float startY, float startZ, float endX, float endY, float endZ, std::vector<PathFindNode>& outPath);

    // 8.3 Traçado de Linha de Visão (Line of Sight - LoS) via Raycasting 3D
    bool CheckLineOfSight(const Vec3F& from, const Vec3F& to, float stepSize = 0.5f) const;
    void AddObstacle(const Vec3F& minBounds, const Vec3F& maxBounds);
    void ClearObstacles();

    size_t GetNodeCount() const { return m_nodes.size(); }
    const std::string& GetLoadedFile() const { return m_loadedFile; }

private:
    std::string m_loadedFile;
    uint32_t m_magic;
    uint32_t m_version;
    uint32_t m_sectorCountX;
    uint32_t m_sectorCountY;
    float    m_baseScale;

    std::vector<PathFindNode> m_nodes;
    std::vector<std::pair<Vec3F, Vec3F>> m_obstacles;
};
