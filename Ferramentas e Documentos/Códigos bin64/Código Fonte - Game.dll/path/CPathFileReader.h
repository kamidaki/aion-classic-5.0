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
#include "../ai/AIObject.h" // Vec3F

#pragma pack(push, 1)
// 8.1.1 Cabeçalho Canônico de Arquivo .path
struct PathFileHeader {
    uint32_t magic;         // 'PATH' (0x48544150)
    uint32_t version;       // ex: 2
    uint32_t sectorCountX;  // Quantidade de setores em X (ex: 64)
    uint32_t sectorCountY;  // Quantidade de setores em Y (ex: 64)
    float    baseScale;     // Escala de altura
    uint32_t offsetTablePos;// Posição da tabela de offsets
};
#pragma pack(pop)

struct PathNode {
    float x, y, z;
    uint32_t flags;
};

// Caixa delimitadora de obstáculo 3D (paredes, rochas, construções)
struct PathObstacleBox {
    Vec3F minBounds;
    Vec3F maxBounds;
};

// Leitor canônico de malha de navegação e arquivos de caminho do Aion (.?AVCPathFileReader@@)
class CPathFileReader {
public:
    CPathFileReader();
    ~CPathFileReader();

    // 8.1 Carregamento e Decodificação de Malhas Binárias
    bool LoadPathFile(const std::string& filePath);
    bool DecodeHeader(const uint8_t* pData, size_t dataSize, PathFileHeader& outHeader);
    bool DecompressDelta1Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]);
    bool DecompressDelta2Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]);

    // Busca de Caminhos (Pathfinding)
    bool FindPath(float startX, float startY, float startZ, float endX, float endY, float endZ, std::vector<PathNode>& outPath);

    // 8.3 Traçado de Linha de Visão (Line of Sight - LoS) via Raycasting 3D
    bool CheckLineOfSight(const Vec3F& from, const Vec3F& to, float stepSize = 0.5f) const;
    void AddObstacle(const Vec3F& minBounds, const Vec3F& maxBounds);
    void ClearObstacles();

    size_t GetNodeCount() const { return m_nodes.size(); }
    size_t GetObstacleCount() const { return m_obstacles.size(); }

private:
    std::string m_loadedFile;
    std::vector<PathNode> m_nodes;
    std::vector<PathObstacleBox> m_obstacles;
    PathFileHeader m_header;
};
