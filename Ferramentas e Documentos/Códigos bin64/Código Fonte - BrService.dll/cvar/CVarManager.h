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

    // Real-time CVar update APIs (apply immediately + notify worker).
    // Change-detection: if the new value equals the last-applied value,
    // no engine call is made. This eliminates redundant writes and prevents
    // stuttering from rapid slider movement.
    static void SetFov(float fov);
    static void SetCameraMax(float maxDist);
    static void SetMaxFps(int fps);
    static void SetTripleBuffering(bool enable);

    static void ApplyAll();
    static void ResyncOnMapChange();
    static bool IsWorkerRunning();
};

} // namespace BrService
