#include "CryModelBridge.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cmath>
#include <mutex>
#include <algorithm>
#include <thread>
#include <vector>

namespace BrService {

struct ModelVertex {
    float x, y, z;
};

enum FaceMaterial {
    MAT_ARMOR = 0,
    MAT_TRIM = 1,
    MAT_WINGS = 2,
    MAT_GLOW = 3,
    MAT_BODY = 4
};

struct ModelFace {
    int v1, v2, v3;
    FaceMaterial mat;
};

static std::mutex s_modelMutex;
static HANDLE s_hSharedMem = nullptr;
static void*  s_pSharedMemView = nullptr;
static uint32_t s_currentNpcId = 0;
static uint8_t  s_currentEntityType = 1;
static uint8_t  s_currentRace = 0;
static float    s_targetMemoryYaw = 0.0f;

static std::vector<ModelVertex> s_vertices;
static std::vector<ModelFace> s_faces;
static float s_rotationYaw = 0.0f;
static ULONGLONG s_lastRotTime = 0;

void CryModelBridge::EnsureSharedMemory() {
    if (!s_pSharedMemView) {
        if (!s_hSharedMem) {
            s_hSharedMem = OpenFileMappingW(FILE_MAP_READ, FALSE, L"Local\\LostAcademy_CryModel_FrameBuffer");
        }
        if (s_hSharedMem) {
            s_pSharedMemView = MapViewOfFile(s_hSharedMem, FILE_MAP_READ, 0, 0, 0);
            if (s_pSharedMemView) {
                LogInfo("CryModelBridge: Conectado ao Frame Buffer compartilhado Local\\LostAcademy_CryModel_FrameBuffer.");
            }
        }
    }
}

bool CryModelBridge::IsFrameBufferConnected() {
    EnsureSharedMemory();
    if (!s_pSharedMemView) return false;
    const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
    // Accepts both 'AION' (0x41494F4E) and 'ACMB' (0x41434D42)
    return ((h->magic == 0x41494F4E || h->magic == 0x41434D42) && h->status == 2);
}

void CryModelBridge::RequestNpcModelOverPipe(uint32_t npcId) {
    std::thread([npcId]() {
        char cmd[64];
        snprintf(cmd, sizeof(cmd), "LOAD %u\n", npcId);

        HANDLE hPipe = CreateFileA("\\\\.\\pipe\\LostAcademy_CryModelBridge",
                                   GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                                   OPEN_EXISTING, 0, nullptr);
        if (hPipe != INVALID_HANDLE_VALUE) {
            DWORD written = 0;
            WriteFile(hPipe, cmd, (DWORD)strlen(cmd), &written, nullptr);
            CloseHandle(hPipe);
        }
    }).detach();
}

bool CryModelBridge::Initialize() {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    EnsureSharedMemory();
    LoadFallbackMesh(0);
    return true;
}

void CryModelBridge::Shutdown() {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    if (s_pSharedMemView) {
        UnmapViewOfFile(s_pSharedMemView);
        s_pSharedMemView = nullptr;
    }
    if (s_hSharedMem) {
        CloseHandle(s_hSharedMem);
        s_hSharedMem = nullptr;
    }
    s_vertices.clear();
    s_faces.clear();
}

void CryModelBridge::SetTargetNpc(uint32_t npcId) {
    SetTargetEntity(npcId, 1, 0, 0.0f);
}

void CryModelBridge::SetTargetEntity(uint32_t modelId, uint8_t entityType, uint8_t race, float yaw) {
    std::lock_guard<std::mutex> lock(s_modelMutex);
    s_currentNpcId = modelId;
    s_currentEntityType = entityType;
    s_currentRace = race;
    s_targetMemoryYaw = yaw;

    RequestNpcModelOverPipe(modelId);
    LoadFallbackMesh(modelId);
}

void CryModelBridge::LoadFallbackMesh(uint32_t npcId) {
    s_vertices.clear();
    s_faces.clear();

    // Reconstruct full articulated 3D character mesh tailored to the target entity
    // Coordinates: X = right, Y = up, Z = forward
    auto addQuad = [](int v0, int v1, int v2, int v3, FaceMaterial mat) {
        s_faces.push_back({ v0, v1, v2, mat });
        s_faces.push_back({ v0, v2, v3, mat });
    };

    auto addBox = [&](float cx, float cy, float cz, float sx, float sy, float sz, FaceMaterial mat) {
        int base = (int)s_vertices.size();
        float hx = sx * 0.5f, hy = sy * 0.5f, hz = sz * 0.5f;
        s_vertices.push_back({ cx - hx, cy - hy, cz - hz });
        s_vertices.push_back({ cx + hx, cy - hy, cz - hz });
        s_vertices.push_back({ cx + hx, cy + hy, cz - hz });
        s_vertices.push_back({ cx - hx, cy + hy, cz - hz });
        s_vertices.push_back({ cx - hx, cy - hy, cz + hz });
        s_vertices.push_back({ cx + hx, cy - hy, cz + hz });
        s_vertices.push_back({ cx + hx, cy + hy, cz + hz });
        s_vertices.push_back({ cx - hx, cy + hy, cz + hz });

        addQuad(base + 0, base + 3, base + 2, base + 1, mat); // Front
        addQuad(base + 5, base + 6, base + 7, base + 4, mat); // Back
        addQuad(base + 3, base + 7, base + 6, base + 2, mat); // Top
        addQuad(base + 0, base + 1, base + 5, base + 4, mat); // Bottom
        addQuad(base + 0, base + 4, base + 7, base + 3, mat); // Left
        addQuad(base + 1, base + 2, base + 6, base + 5, mat); // Right
    };

    // 1. Torso / Chestplate
    addBox(0.0f, 0.15f, 0.0f, 0.55f, 0.65f, 0.35f, MAT_ARMOR);

    // 2. Head / Helm
    addBox(0.0f, 0.72f, 0.0f, 0.32f, 0.34f, 0.32f, MAT_BODY);
    addBox(0.0f, 0.76f, 0.08f, 0.22f, 0.12f, 0.16f, MAT_TRIM); // Visor

    // 3. Shoulders (Pauldrons)
    addBox(-0.38f, 0.45f, 0.0f, 0.26f, 0.22f, 0.28f, MAT_TRIM);
    addBox( 0.38f, 0.45f, 0.0f, 0.26f, 0.22f, 0.28f, MAT_TRIM);

    // 4. Arms
    addBox(-0.36f, 0.05f, 0.02f, 0.16f, 0.55f, 0.18f, MAT_ARMOR);
    addBox( 0.36f, 0.05f, 0.02f, 0.16f, 0.55f, 0.18f, MAT_ARMOR);

    // 5. Waist & Belt
    addBox(0.0f, -0.22f, 0.0f, 0.46f, 0.16f, 0.30f, MAT_TRIM);

    // 6. Legs & Greaves
    addBox(-0.16f, -0.65f, 0.0f, 0.18f, 0.70f, 0.22f, MAT_ARMOR);
    addBox( 0.16f, -0.65f, 0.0f, 0.18f, 0.70f, 0.22f, MAT_ARMOR);

    // 7. Weapon Silhouette (Right hand sword blade)
    addBox(0.42f, 0.25f, 0.25f, 0.06f, 0.95f, 0.12f, MAT_TRIM);

    // 8. Race-Specific 3D Wings (Elyos / Asmodian / Balaur)
    if (s_currentRace == 0) {
        // Elyos: Outstretched feathered wings
        for (int side = -1; side <= 1; side += 2) {
            float sx = (float)side;
            int wBase = (int)s_vertices.size();
            s_vertices.push_back({ sx * 0.15f, 0.30f, -0.15f });
            s_vertices.push_back({ sx * 0.75f, 0.85f, -0.35f });
            s_vertices.push_back({ sx * 1.05f, 0.40f, -0.25f });
            s_vertices.push_back({ sx * 0.65f, -0.10f, -0.15f });

            s_faces.push_back({ wBase + 0, wBase + 1, wBase + 2, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 2, wBase + 3, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 2, wBase + 1, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 3, wBase + 2, MAT_WINGS });
        }
    } else if (s_currentRace == 1) {
        // Asmodian: Dark spiked wings with claws and back mane
        for (int side = -1; side <= 1; side += 2) {
            float sx = (float)side;
            int wBase = (int)s_vertices.size();
            s_vertices.push_back({ sx * 0.12f, 0.32f, -0.12f });
            s_vertices.push_back({ sx * 0.85f, 0.95f, -0.45f });
            s_vertices.push_back({ sx * 1.15f, 0.55f, -0.35f });
            s_vertices.push_back({ sx * 0.80f, 0.05f, -0.20f });

            s_faces.push_back({ wBase + 0, wBase + 1, wBase + 2, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 2, wBase + 3, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 2, wBase + 1, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 3, wBase + 2, MAT_WINGS });
        }
        addBox(0.0f, 0.35f, -0.20f, 0.12f, 0.45f, 0.10f, MAT_GLOW);
    } else {
        // Monster / Boss / Balaur
        addBox(-0.18f, 0.95f, -0.05f, 0.08f, 0.28f, 0.08f, MAT_TRIM);
        addBox( 0.18f, 0.95f, -0.05f, 0.08f, 0.28f, 0.08f, MAT_TRIM);
        for (int side = -1; side <= 1; side += 2) {
            float sx = (float)side;
            int wBase = (int)s_vertices.size();
            s_vertices.push_back({ sx * 0.20f, 0.25f, -0.15f });
            s_vertices.push_back({ sx * 1.10f, 0.80f, -0.40f });
            s_vertices.push_back({ sx * 0.90f, -0.15f, -0.25f });

            s_faces.push_back({ wBase + 0, wBase + 1, wBase + 2, MAT_WINGS });
            s_faces.push_back({ wBase + 0, wBase + 2, wBase + 1, MAT_WINGS });
        }
    }
}

void CryModelBridge::RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height) {
    EnsureSharedMemory();

    if (s_pSharedMemView) {
        const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
        if ((h->magic == 0x41494F4E || h->magic == 0x41434D42) && h->status == 2 && h->width > 0 && h->height > 0) {
            BYTE* pPixels = reinterpret_cast<BYTE*>(s_pSharedMemView) + sizeof(BridgeFrameHeader);
            Gdiplus::Bitmap frameBmp((INT)h->width, (INT)h->height, (INT)h->pitch,
                                     PixelFormat32bppARGB, pPixels);

            g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
            g.DrawImage(&frameBmp, x, y, width, height);

            Gdiplus::Pen rimPen(Gdiplus::Color(90, 215, 170, 50), 1.2f);
            g.DrawRectangle(&rimPen, x, y, width, height);
            return;
        }
    }

    std::lock_guard<std::mutex> lock(s_modelMutex);
    if (s_vertices.empty() || s_faces.empty()) return;

    ULONGLONG now = GetTickCount64();
    if (s_lastRotTime == 0) s_lastRotTime = now;
    float dt = (float)(now - s_lastRotTime) / 1000.0f;
    s_lastRotTime = now;
    if (dt > 0.1f) dt = 0.033f;

    s_rotationYaw += dt * 0.65f;
    if (s_rotationYaw > 6.2831853f) s_rotationYaw -= 6.2831853f;

    float effectiveYaw = s_rotationYaw + s_targetMemoryYaw;
    float cosY = cosf(effectiveYaw);
    float sinY = sinf(effectiveYaw);
    float pitch = 0.18f;
    float cosP = cosf(pitch);
    float sinP = sinf(pitch);

    float centerX = x + width * 0.5f;
    float centerY = y + height * 0.52f;
    float scale = std::min(width, height) * 0.44f;

    std::vector<Gdiplus::PointF> proj(s_vertices.size());
    std::vector<float> transformedZ(s_vertices.size());
    std::vector<ModelVertex> viewSpaceVerts(s_vertices.size());

    const float distance = 4.2f;

    for (size_t i = 0; i < s_vertices.size(); ++i) {
        const auto& v = s_vertices[i];
        float rx = v.x * cosY - v.z * sinY;
        float rz = v.x * sinY + v.z * cosY;
        float ry = v.y * cosP - rz * sinP;
        float rz2 = v.y * sinP + rz * cosP;

        viewSpaceVerts[i] = { rx, ry, rz2 };

        float fovFactor = distance / (distance + rz2);
        proj[i].X = centerX + rx * scale * fovFactor;
        proj[i].Y = centerY - ry * scale * fovFactor;
        transformedZ[i] = rz2;
    }

    struct DepthFace {
        ModelFace face;
        float depth;
        float shade;
    };
    std::vector<DepthFace> sortedFaces;
    sortedFaces.reserve(s_faces.size());

    const float lx = 0.50f, ly = 0.75f, lz = 0.42f;
    const float lLen = sqrtf(lx * lx + ly * ly + lz * lz);
    const float normLx = lx / lLen, normLy = ly / lLen, normLz = lz / lLen;

    for (const auto& f : s_faces) {
        const auto& v0 = viewSpaceVerts[f.v1];
        const auto& v1 = viewSpaceVerts[f.v2];
        const auto& v2 = viewSpaceVerts[f.v3];

        float ax = v1.x - v0.x, ay = v1.y - v0.y, az = v1.z - v0.z;
        float bx = v2.x - v0.x, by = v2.y - v0.y, bz = v2.z - v0.z;
        float nx = ay * bz - az * by;
        float ny = az * bx - ax * bz;
        float nz = ax * by - ay * bx;
        float nLen = sqrtf(nx * nx + ny * ny + nz * nz);

        float shade = 0.5f;
        if (nLen > 0.0001f) {
            nx /= nLen; ny /= nLen; nz /= nLen;
            float dot = nx * normLx + ny * normLy + nz * normLz;
            shade = std::clamp(dot * 0.65f + 0.35f, 0.25f, 1.0f);
        }

        float avgZ = (transformedZ[f.v1] + transformedZ[f.v2] + transformedZ[f.v3]) / 3.0f;
        sortedFaces.push_back({ f, avgZ, shade });
    }

    std::sort(sortedFaces.begin(), sortedFaces.end(), [](const DepthFace& a, const DepthFace& b) {
        return a.depth > b.depth;
    });

    g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);

    Gdiplus::Pen circlePen(Gdiplus::Color(65, 215, 175, 55), 1.2f);
    g.DrawEllipse(&circlePen, centerX - width * 0.35f, centerY + height * 0.36f, width * 0.70f, height * 0.18f);

    Gdiplus::Pen innerCircle(Gdiplus::Color(35, 120, 180, 240), 1.0f);
    g.DrawEllipse(&innerCircle, centerX - width * 0.24f, centerY + height * 0.38f, width * 0.48f, height * 0.12f);

    for (const auto& df : sortedFaces) {
        const auto& f = df.face;
        Gdiplus::PointF pts[3] = { proj[f.v1], proj[f.v2], proj[f.v3] };

        float crossZ = (pts[1].X - pts[0].X) * (pts[2].Y - pts[0].Y) -
                       (pts[1].Y - pts[0].Y) * (pts[2].X - pts[0].X);

        if (crossZ > 0.0f || f.mat == MAT_WINGS) {
            float s = df.shade;
            Gdiplus::Color baseColor;

            switch (f.mat) {
            case MAT_ARMOR:
                baseColor = Gdiplus::Color(220, (BYTE)(175 * s), (BYTE)(185 * s), (BYTE)(200 * s));
                break;
            case MAT_TRIM:
                baseColor = Gdiplus::Color(230, (BYTE)(220 * s), (BYTE)(170 * s), (BYTE)(55 * s));
                break;
            case MAT_WINGS:
                if (s_currentRace == 0) {
                    baseColor = Gdiplus::Color(190, (BYTE)(160 * s), (BYTE)(225 * s), (BYTE)(255 * s));
                } else if (s_currentRace == 1) {
                    baseColor = Gdiplus::Color(200, (BYTE)(150 * s), (BYTE)(70 * s), (BYTE)(190 * s));
                } else {
                    baseColor = Gdiplus::Color(210, (BYTE)(215 * s), (BYTE)(45 * s), (BYTE)(55 * s));
                }
                break;
            case MAT_GLOW:
                baseColor = Gdiplus::Color(210, (BYTE)(180 * s), (BYTE)(80 * s), (BYTE)(220 * s));
                break;
            case MAT_BODY:
            default:
                baseColor = Gdiplus::Color(220, (BYTE)(200 * s), (BYTE)(175 * s), (BYTE)(160 * s));
                break;
            }

            Gdiplus::SolidBrush polyBrush(baseColor);
            g.FillPolygon(&polyBrush, pts, 3);

            Gdiplus::Pen edgePen(Gdiplus::Color(60, (BYTE)(baseColor.GetR() * 0.6f),
                                                    (BYTE)(baseColor.GetG() * 0.6f),
                                                    (BYTE)(baseColor.GetB() * 0.6f)), 0.8f);
            g.DrawPolygon(&edgePen, pts, 3);
        }
    }

    Gdiplus::Pen borderPen(Gdiplus::Color(55, 180, 195, 215), 1.0f);
    g.DrawRectangle(&borderPen, x, y, width, height);
}

} // namespace BrService
