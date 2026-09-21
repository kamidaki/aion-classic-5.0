#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <cstdint>
#include <vector>

namespace BrService {

struct ModelVertex {
    float x, y, z;
};

struct ModelFace {
    int v1, v2, v3;
};

class CryModelBridge {
public:
    static bool Initialize();
    static void Shutdown();

    static void SetTargetNpc(uint32_t npcId);
    static void RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height);

private:
    static void LoadMeshForTarget(uint32_t npcId);
};

} // namespace BrService
