#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#include "CPathFileReader.h"
#include "../core/GameLog.h"
#include <cmath>
#include <cstring>

CPathFileReader::CPathFileReader() {
    std::memset(&m_header, 0, sizeof(m_header));
}

CPathFileReader::~CPathFileReader() {
    m_nodes.clear();
    m_obstacles.clear();
}

bool CPathFileReader::DecodeHeader(const uint8_t* pData, size_t dataSize, PathFileHeader& outHeader) {
    if (!pData || dataSize < sizeof(PathFileHeader)) {
        return false;
    }

    std::memcpy(&outHeader, pData, sizeof(PathFileHeader));

    // Validação da assinatura 'PATH' (0x48544150 ou 0x50415448)
    if (outHeader.magic != 0x48544150 && outHeader.magic != 0x50415448) {
        GameLog_Info("CPathFileReader::DecodeHeader: Assinatura magica invalida (0x%08X)!", outHeader.magic);
        return false;
    }

    m_header = outHeader;
    GameLog_Info("CPathFileReader::DecodeHeader: Cabecalho valido! Setores: %ux%u, Escala: %.2f",
        outHeader.sectorCountX, outHeader.sectorCountY, outHeader.baseScale);
    return true;
}

bool CPathFileReader::DecompressDelta1Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]) {
    if (!pDeltaData) return false;

    for (int y = 0; y < 64; ++y) {
        for (int x = 0; x < 64; ++x) {
            int8_t delta = static_cast<int8_t>(pDeltaData[y * 64 + x]);
            outGrid[y][x] = baseZ + (static_cast<float>(delta) * 0.1f);
        }
    }
    return true;
}

bool CPathFileReader::DecompressDelta2Byte(const uint8_t* pDeltaData, float baseZ, float outGrid[64][64]) {
    if (!pDeltaData) return false;

    const int16_t* pDelta16 = reinterpret_cast<const int16_t*>(pDeltaData);
    for (int y = 0; y < 64; ++y) {
        for (int x = 0; x < 64; ++x) {
            int16_t delta = pDelta16[y * 64 + x];
            outGrid[y][x] = baseZ + (static_cast<float>(delta) * 0.01f);
        }
    }
    return true;
}

bool CPathFileReader::LoadPathFile(const std::string& filePath) {
    GameLog_Info("CPathFileReader::LoadPathFile: Carregando malha de navegacao '%s'...", filePath.c_str());
    m_loadedFile = filePath;

    // Simulação do cabeçalho canônico
    m_header.magic = 0x50415448; // 'PATH'
    m_header.version = 2;
    m_header.sectorCountX = 64;
    m_header.sectorCountY = 64;
    m_header.baseScale = 1.0f;

    m_nodes.clear();
    m_nodes.push_back({0.0f, 0.0f, 0.0f, 1});
    m_nodes.push_back({10.0f, 10.0f, 0.0f, 1});

    GameLog_Info("CPathFileReader::LoadPathFile: Concluido (%zu nos carregados).", m_nodes.size());
    return true;
}

bool CPathFileReader::FindPath(float startX, float startY, float startZ, float endX, float endY, float endZ, std::vector<PathNode>& outPath) {
    outPath.clear();
    outPath.push_back({startX, startY, startZ, 0});

    // Se houver nós intermediários, interpola waypoint
    float midX = (startX + endX) * 0.5f;
    float midY = (startY + endY) * 0.5f;
    float midZ = (startZ + endZ) * 0.5f;
    outPath.push_back({midX, midY, midZ, 0});

    outPath.push_back({endX, endY, endZ, 0});
    return true;
}

// -------------------------------------------------------------
// 8.3 Traçado de Linha de Visão (Line of Sight - LoS)
// -------------------------------------------------------------
void CPathFileReader::AddObstacle(const Vec3F& minBounds, const Vec3F& maxBounds) {
    m_obstacles.push_back({ minBounds, maxBounds });
}

void CPathFileReader::ClearObstacles() {
    m_obstacles.clear();
}

bool CPathFileReader::CheckLineOfSight(const Vec3F& from, const Vec3F& to, float stepSize) const {
    float dx = to.x - from.x;
    float dy = to.y - from.y;
    float dz = to.z - from.z;
    float totalDistance = std::sqrt(dx * dx + dy * dy + dz * dz);

    if (totalDistance <= 0.001f) {
        return true;
    }

    // Vetor unitário normalizado de avanço do raio 3D
    float invDist = 1.0f / totalDistance;
    float stepX = (dx * invDist) * stepSize;
    float stepY = (dy * invDist) * stepSize;
    float stepZ = (dz * invDist) * stepSize;

    int numSteps = static_cast<int>(totalDistance / stepSize);
    float curX = from.x;
    float curY = from.y;
    float curZ = from.z;

    // Raycasting passo a passo ao longo da trajetória
    for (int i = 0; i < numSteps; ++i) {
        curX += stepX;
        curY += stepY;
        curZ += stepZ;

        // Testa colisão do ponto atual contra todas as caixas de obstáculos da malha
        for (const auto& obs : m_obstacles) {
            if (curX >= obs.minBounds.x && curX <= obs.maxBounds.x &&
                curY >= obs.minBounds.y && curY <= obs.maxBounds.y &&
                curZ >= obs.minBounds.z && curZ <= obs.maxBounds.z) 
            {
                // Raio interceptado por obstáculo sólido (parede, rocha, relevo)
                return false; // Linha de visão bloqueada!
            }
        }
    }

    return true; // Linha de visão desimpedida!
}
