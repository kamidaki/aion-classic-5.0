#include "CryModelBridge.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cmath>
#include <mutex>
#include <algorithm>
#include <thread>

namespace BrService {

struct ModelVertex {
    float x, y, z;
};

struct ModelFace {
    int v1, v2, v3;
};

static std::mutex s_modelMutex;
static HANDLE s_hSharedMem = nullptr;
static void*  s_pSharedMemView = nullptr;
static uint32_t s_currentNpcId = 0;

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
                LogInfo("CryModelBridge: Conectado com sucesso ao Frame Buffer compartilhado Local\\LostAcademy_CryModel_FrameBuffer.");
            }
        }
    }
}

bool CryModelBridge::IsFrameBufferConnected() {
    EnsureSharedMemory();
    if (!s_pSharedMemView) return false;
    const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
    return (h->magic == 0x41434D42 && h->status == 2);
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
    if (s_currentNpcId == npcId) return;
    std::lock_guard<std::mutex> lock(s_modelMutex);
    s_currentNpcId = npcId;
    RequestNpcModelOverPipe(npcId);
    LoadFallbackMesh(npcId);
}

void CryModelBridge::LoadFallbackMesh(uint32_t npcId) {
    s_vertices.clear();
    s_faces.clear();

    const int segments = 12;
    const float height = 2.4f;
    const float radius = 0.75f;

    s_vertices.push_back({ 0.0f, -height * 0.45f, 0.0f }); // 0: bottom
    s_vertices.push_back({ 0.0f,  height * 0.65f, 0.0f }); // 1: top

    for (int i = 0; i < segments; ++i) {
        float angle = (float)i / segments * 6.2831853f;
        float r = radius * (1.0f + 0.2f * sinf(angle * 3.0f));
        float y = 0.05f * cosf(angle * 4.0f);
        s_vertices.push_back({ r * cosf(angle), y, r * sinf(angle) });
    }

    for (int i = 0; i < segments; ++i) {
        int vCurrent = 2 + i;
        int vNext = 2 + ((i + 1) % segments);
        s_faces.push_back({ 0, vCurrent, vNext });
        s_faces.push_back({ 1, vNext, vCurrent });
    }

    int baseIdx = (int)s_vertices.size();
    s_vertices.push_back({ -radius * 1.8f, height * 0.3f, 0.1f });
    s_vertices.push_back({  radius * 1.8f, height * 0.3f, 0.1f });
    s_vertices.push_back({  0.0f, height * 0.85f, 0.2f });

    s_faces.push_back({ 1, baseIdx, 2 });
    s_faces.push_back({ 1, 2 + segments / 2, baseIdx + 1 });
    s_faces.push_back({ 1, baseIdx + 2, 0 });
}

void CryModelBridge::RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height) {
    EnsureSharedMemory();

    if (s_pSharedMemView) {
        const BridgeFrameHeader* h = reinterpret_cast<const BridgeFrameHeader*>(s_pSharedMemView);
        if (h->magic == 0x41434D42 && h->status == 2 && h->width > 0 && h->height > 0) {
            BYTE* pPixels = reinterpret_cast<BYTE*>(s_pSharedMemView) + sizeof(BridgeFrameHeader);
            Gdiplus::Bitmap frameBmp((INT)h->width, (INT)h->height, (INT)h->pitch,
                                     PixelFormat32bppARGB, pPixels);

            g.SetInterpolationMode(Gdiplus::InterpolationModeHighQualityBicubic);
            g.DrawImage(&frameBmp, x, y, width, height);

            // Subtle gold rim around the 3D frame
            Gdiplus::Pen rimPen(Gdiplus::Color(80, 215, 170, 50), 1.2f);
            g.DrawRectangle(&rimPen, x, y, width, height);
            return;
        }
    }

    // Fallback: 3D shaded polygon mesh
    std::lock_guard<std::mutex> lock(s_modelMutex);
    if (s_vertices.empty() || s_faces.empty()) return;

    ULONGLONG now = GetTickCount64();
    if (s_lastRotTime == 0) s_lastRotTime = now;
    float dt = (float)(now - s_lastRotTime) / 1000.0f;
    s_lastRotTime = now;
    if (dt > 0.1f) dt = 0.033f;

    s_rotationYaw += dt * 0.50f;
    if (s_rotationYaw > 6.2831853f) s_rotationYaw -= 6.2831853f;

    float cosY = cosf(s_rotationYaw);
    float sinY = sinf(s_rotationYaw);
    float pitch = 0.20f;
    float cosP = cosf(pitch);
    float sinP = sinf(pitch);

    float centerX = x + width * 0.5f;
    float centerY = y + height * 0.52f;
    float scale = std::min(width, height) * 0.42f;

    std::vector<Gdiplus::PointF> proj(s_vertices.size());
    std::vector<float> depth(s_vertices.size());

    for (size_t i = 0; i < s_vertices.size(); ++i) {
        const auto& v = s_vertices[i];
        float rx = v.x * cosY - v.z * sinY;
        float rz = v.x * sinY + v.z * cosY;
        float ry = v.y * cosP - rz * sinP;
        float rz2 = v.y * sinP + rz * cosP;

        float distance = 4.0f;
        float fovFactor = distance / (distance + rz2);

        proj[i].X = centerX + rx * scale * fovFactor;
        proj[i].Y = centerY - ry * scale * fovFactor;
        depth[i] = rz2;
    }

    struct DepthFace {
        ModelFace face;
        float z;
    };
    std::vector<DepthFace> sortedFaces;
    sortedFaces.reserve(s_faces.size());

    for (const auto& f : s_faces) {
        float avgZ = (depth[f.v1] + depth[f.v2] + depth[f.v3]) / 3.0f;
        sortedFaces.push_back({ f, avgZ });
    }

    std::sort(sortedFaces.begin(), sortedFaces.end(), [](const DepthFace& a, const DepthFace& b) {
        return a.z > b.z;
    });

    Gdiplus::Pen wirePen(Gdiplus::Color(140, 215, 175, 60), 1.0f);
    Gdiplus::SolidBrush fillBrush(Gdiplus::Color(55, 190, 145, 50));

    g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);

    for (const auto& df : sortedFaces) {
        const auto& f = df.face;
        Gdiplus::PointF pts[3] = { proj[f.v1], proj[f.v2], proj[f.v3] };

        float crossZ = (pts[1].X - pts[0].X) * (pts[2].Y - pts[0].Y) -
                       (pts[1].Y - pts[0].Y) * (pts[2].X - pts[0].X);
        if (crossZ > 0.0f) {
            g.FillPolygon(&fillBrush, pts, 3);
            g.DrawPolygon(&wirePen, pts, 3);
        }
    }

    Gdiplus::Pen ringPen(Gdiplus::Color(70, 215, 175, 60), 1.2f);
    g.DrawEllipse(&ringPen, centerX - width * 0.32f, centerY + height * 0.32f, width * 0.64f, height * 0.16f);
}

} // namespace BrService
