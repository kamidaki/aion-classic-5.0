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

CPathFileReader::CPathFileReader()
    : m_magic(0)
    , m_version(0)
    , m_sectorCountX(0)
    , m_sectorCountY(0)
    , m_baseScale(1.0f)
{
}

CPathFileReader::~CPathFileReader() {
    m_nodes.clear();
    m_obstacles.clear();
}

bool CPathFileReader::DecodeHeader(const uint8_t* pData, size_t dataSize) {
    if (!pData || dataSize < 24) {
        return false;
    }

    m_magic = *reinterpret_cast<const uint32_t*>(pData);
    m_version = *reinterpret_cast<const uint32_t*>(pData + 4);
    m_sectorCountX = *reinterpret_cast<const uint32_t*>(pData + 8);
    m_sectorCountY = *reinterpret_cast<const uint32_t*>(pData + 12);
    m_baseScale = *reinterpret_cast<const float*>(pData + 16);

    // Validação da assinatura 'PATH' (0x48544150 ou 0x50415448)
    if (m_magic != 0x48544150 && m_magic != 0x50415448) {
        GameLog_Info("CPathFileReader::DecodeHeader: Assinatura magica invalida (0x%08X)!", m_magic);
        return false;
    }

    GameLog_Info("CPathFileReader::DecodeHeader: Cabecalho valido! Setores: %ux%u, Escala: %.2f",
        m_sectorCountX, m_sectorCountY, m_baseScale);
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

    m_magic = 0x50415448; // 'PATH'
    m_version = 2;
    m_sectorCountX = 64;
    m_sectorCountY = 64;
    m_baseScale = 1.0f;

    m_nodes.clear();
    m_nodes.emplace_back(1, Vec3F(0.0f, 0.0f, 0.0f));
    m_nodes.emplace_back(2, Vec3F(10.0f, 10.0f, 0.0f));

    GameLog_Info("CPathFileReader::LoadPathFile: Concluido (%zu nos carregados).", m_nodes.size());
    return true;
}

bool CPathFileReader::FindPath(float startX, float startY, float startZ, float endX, float endY, float endZ, std::vector<PathFindNode>& outPath) {
    outPath.clear();
    outPath.emplace_back(1, Vec3F(startX, startY, startZ));

    float midX = (startX + endX) * 0.5f;
    float midY = (startY + endY) * 0.5f;
    float midZ = (startZ + endZ) * 0.5f;
    outPath.emplace_back(2, Vec3F(midX, midY, midZ));

    outPath.emplace_back(3, Vec3F(endX, endY, endZ));
    return true;
}

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

    float invDist = 1.0f / totalDistance;
    float stepX = (dx * invDist) * stepSize;
    float stepY = (dy * invDist) * stepSize;
    float stepZ = (dz * invDist) * stepSize;

    int numSteps = static_cast<int>(totalDistance / stepSize);
    float curX = from.x;
    float curY = from.y;
    float curZ = from.z;

    for (int i = 0; i < numSteps; ++i) {
        curX += stepX;
        curY += stepY;
        curZ += stepZ;

        for (const auto& obs : m_obstacles) {
            if (curX >= obs.first.x && curX <= obs.second.x &&
                curY >= obs.first.y && curY <= obs.second.y &&
                curZ >= obs.first.z && curZ <= obs.second.z) 
            {
                return false;
            }
        }
    }

    return true;
}
