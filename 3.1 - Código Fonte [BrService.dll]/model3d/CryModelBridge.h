#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objidl.h>
#include <gdiplus.h>
#include <cstdint>
#include <vector>

namespace BrService {

#pragma pack(push, 1)
struct BridgeFrameHeader {
    uint32_t magic;         // 0x41434D42 ('ACMB')
    uint32_t width;
    uint32_t height;
    uint32_t pitch;
    uint32_t frameIndex;
    uint32_t npcId;
    float    yaw;
    float    pitchAngle;
    float    zoom;
    uint32_t status;        // 0 = Idle, 1 = Rendering, 2 = Ready
    uint64_t timestamp;
};
#pragma pack(pop)

class CryModelBridge {
public:
    static bool Initialize();
    static void Shutdown();

    static void SetTargetNpc(uint32_t npcId);
    static void SetTargetEntity(uint32_t modelId, uint8_t entityType, uint8_t race, float yaw);
    static void RenderThumbnail(Gdiplus::Graphics& g, float x, float y, float width, float height);

    static bool IsFrameBufferConnected();

private:
    static void EnsureSharedMemory();
    static void RequestNpcModelOverPipe(uint32_t npcId);
    static void LoadFallbackMesh(uint32_t npcId);
};

} // namespace BrService
