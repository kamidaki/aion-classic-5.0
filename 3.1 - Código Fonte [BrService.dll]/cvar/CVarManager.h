#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <string>

namespace BrService {

class CVarManager {
public:
    static bool Initialize();
    static void Shutdown();

    // Instant CVar update APIs
    static void SetFov(float fov);
    static void SetCameraMax(float maxDist);
    static void SetMaxFps(int fps);
    static void SetTripleBuffering(bool enable);
    static void SetAnisotropic(bool enable);
    static void SetFreeFly(bool enable);

    static void ApplyAll();
    static void ResyncOnMapChange();
    static bool IsWorkerRunning();
};

} // namespace BrService
