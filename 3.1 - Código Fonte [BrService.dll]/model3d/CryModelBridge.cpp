#include "CryModelBridge.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cmath>
#include <mutex>
#include <algorithm>

namespace BrService {

static std::mutex s_meshMutex;
static std::vector<ModelVertex> s_vertices;
static std::vector<ModelFace> s_faces;
static float s_rotationYaw = 0.0f;
static uint32_t s_currentNpcId = 0;
static ULONGLONG s_lastRotTime = 0;

bool CryModelBridge::Initialize() {
    std::lock_guard<std::mutex> lock(s_meshMutex);
    LoadMeshForTarget(0); // default mesh
    return true;
}

void CryModelBridge::Shutdown() {
    std::lock_guard<std::mutex> lock(s_meshMutex);
    s_vertices.clear();
    s_faces.clear();
}

void CryModelBridge::SetTargetNpc(uint32_t npcId) {
    if (s_currentNpcId == npcId) return;
    std::lock_guard<std::mutex> lock(s_meshMutex);
    s_currentNpcId = npcId;
    LoadMeshForTarget(npcId);
}

void CryModelBridge::LoadMeshForTarget(uint32_t npcId) {
    s_vertices.clear();
    s_faces.clear();

    // Procedural crystalline / dragon avatar mesh for target preview
    // Inspired by Aion Drakan / Crystal Scythe aesthetics
    const int segments = 12;
    const float height = 2.4f;
    const float radius = 0.75f;

    // Center base and apex
    s_vertices.push_back({ 0.0f, -height * 0.4f, 0.0f }); // 0: bottom
    s_vertices.push_back({ 0.0f,  height * 0.6f, 0.0f }); // 1: top

    // Middle crystal belt
    for (int i = 0; i < segments; ++i) {
        float angle = (float)i / segments * 6.2831853f;
        float r = radius * (1.0f + 0.2f * sinf(angle * 3.0f));
        float y = 0.05f * cosf(angle * 4.0f);
        s_vertices.push_back({ r * cosf(angle), y, r * sinf(angle) });
    }

    // Connect faces
    for (int i = 0; i < segments; ++i) {
        int vCurrent = 2 + i;
        int vNext = 2 + ((i + 1) % segments);

        // Bottom cap triangle
        s_faces.push_back({ 0, vCurrent, vNext });
        // Top cap triangle
        s_faces.push_back({ 1, vNext, vCurrent });
    }

    // Add decorative crystal wings/spikes
    int baseIdx = (int)s_vertices.size();
    s_vertices.push_back({ -radius * 1.8f, height * 0.3f, 0.1f });
    s_vertices.push_back({  radius * 1.8f, height * 0.3f, 0.1f });
    s_vertices.push_back({  0.0f, height * 0.85f, 0.2f });

    s_faces.push_back({ 1, baseIdx, 2 });
    s_faces.push_back({ 1, 2 + segments / 2, baseIdx + 1 });
    s_faces.push_back({ 1, baseIdx + 2, 0 });
}

void CryModelBridge::RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height) {
    std::lock_guard<std::mutex> lock(s_meshMutex);
    if (s_vertices.empty() || s_faces.empty()) return;

    ULONGLONG now = GetTickCount64();
    if (s_lastRotTime == 0) s_lastRotTime = now;
    float dt = (float)(now - s_lastRotTime) / 1000.0f;
    s_lastRotTime = now;
    if (dt > 0.1f) dt = 0.033f;

    // Slow elegant rotation (approx 20 deg / sec)
    s_rotationYaw += dt * 0.45f;
    if (s_rotationYaw > 6.2831853f) s_rotationYaw -= 6.2831853f;

    float cosY = cosf(s_rotationYaw);
    float sinY = sinf(s_rotationYaw);
    float pitch = 0.22f; // Slight tilt
    float cosP = cosf(pitch);
    float sinP = sinf(pitch);

    float centerX = x + width * 0.5f;
    float centerY = y + height * 0.52f;
    float scale = std::min(width, height) * 0.42f;

    // Project vertices
    std::vector<Gdiplus::PointF> proj(s_vertices.size());
    std::vector<float> depth(s_vertices.size());

    for (size_t i = 0; i < s_vertices.size(); ++i) {
        const auto& v = s_vertices[i];
        // Rotate Y
        float rx = v.x * cosY - v.z * sinY;
        float rz = v.x * sinY + v.z * cosY;
        // Pitch X
        float ry = v.y * cosP - rz * sinP;
        float rz2 = v.y * sinP + rz * cosP;

        float distance = 4.0f;
        float fovFactor = distance / (distance + rz2);

        proj[i].X = centerX + rx * scale * fovFactor;
        proj[i].Y = centerY - ry * scale * fovFactor; // invert Y for screen
        depth[i] = rz2;
    }

    // Sort faces by average depth (Painter's algorithm)
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
        return a.z > b.z; // Far to near
    });

    // Draw faces with translucent metallic/crystal gradient and transparent background
    Gdiplus::Pen wirePen(Gdiplus::Color(110, 212, 175, 55), 1.0f); // Gold wireframe
    Gdiplus::SolidBrush fillBrush(Gdiplus::Color(35, 180, 140, 45)); // Translucent gold

    g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);

    for (const auto& df : sortedFaces) {
        const auto& f = df.face;
        Gdiplus::PointF pts[3] = { proj[f.v1], proj[f.v2], proj[f.v3] };

        // Backface culling
        float crossZ = (pts[1].X - pts[0].X) * (pts[2].Y - pts[0].Y) -
                       (pts[1].Y - pts[0].Y) * (pts[2].X - pts[0].X);
        if (crossZ > 0.0f) {
            g.FillPolygon(&fillBrush, pts, 3);
            g.DrawPolygon(&wirePen, pts, 3);
        }
    }

    // Subdued glow ring at base of model
    Gdiplus::Pen ringPen(Gdiplus::Color(60, 212, 175, 55), 1.2f);
    g.DrawEllipse(&ringPen, centerX - width * 0.32f, centerY + height * 0.32f, width * 0.64f, height * 0.16f);
}

} // namespace BrService
