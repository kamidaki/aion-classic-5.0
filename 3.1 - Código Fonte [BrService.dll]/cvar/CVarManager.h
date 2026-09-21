#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <string>
#include <unordered_map>

namespace BrService {

struct CVarDescriptor {
    std::string name;
    void* pAddress = nullptr;
    int defaultValueInt = 0;
    float defaultValueFloat = 0.0f;
};

class CVarManager {
public:
    static bool Initialize();
    static void Shutdown();

    static void SetFov(float fov);
    static void SetCameraMax(float maxDist);
    static void SetMaxFps(int fps);
    static void SetTripleBuffering(bool enable);
    static void SetAnisotropic(bool enable);

    static void ApplyAll();
    static void ResyncOnMapChange();

private:
    static void ScanCVars();
    static void* FindCVar(const char* name);
};

} // namespace BrService
