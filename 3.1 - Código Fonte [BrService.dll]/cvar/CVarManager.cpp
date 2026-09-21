#include "CVarManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <mutex>
#include <vector>

namespace BrService {

static std::recursive_mutex s_cvarMutex;
static std::unordered_map<std::string, void*> s_cvarMap;
static bool s_initialized = false;

// 64-bit CryEngine CVar structure offsets
static constexpr size_t OFFSET_NAME = 8;
static constexpr size_t OFFSET_INT  = 184;
static constexpr size_t OFFSET_FLOAT= 188;
static constexpr size_t OFFSET_STR  = 192;

void* CVarManager::FindCVar(const char* name) {
    if (!name) return nullptr;
    auto it = s_cvarMap.find(name);
    if (it != s_cvarMap.end()) return it->second;
    return nullptr;
}

void CVarManager::ScanCVars() {
    // Scan heap/committed pages for standard CryEngine CVars
    const char* targets[] = {
        "g_maxfps", "g_minFov", "g_camMax", "d3d9_TripleBuffering", "r_anisotropy", "r_TexturesStreaming"
    };

    SYSTEM_INFO si;
    GetSystemInfo(&si);

    MEMORY_BASIC_INFORMATION mbi;
    uint8_t* addr = (uint8_t*)si.lpMinimumApplicationAddress;
    uint8_t* maxAddr = (uint8_t*)si.lpMaximumApplicationAddress;

    size_t foundCount = 0;
    size_t totalTargets = sizeof(targets) / sizeof(targets[0]);

    try {
        while (addr < maxAddr && foundCount < totalTargets) {
            if (!VirtualQuery(addr, &mbi, sizeof(mbi))) {
                addr += 0x1000;
                continue;
            }

            if ((mbi.State == MEM_COMMIT) && (mbi.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE)) && !(mbi.Protect & PAGE_GUARD)) {
                uint8_t* pStart = (uint8_t*)mbi.BaseAddress;
                size_t regionSize = mbi.RegionSize;

                for (size_t i = 0; i + 256 < regionSize; i += 8) {
                    uint8_t* candidate = pStart + i;

                    for (const char* tName : targets) {
                        if (s_cvarMap.find(tName) != s_cvarMap.end()) continue;

                        size_t len = strlen(tName);
                        // Match name at candidate + OFFSET_NAME
                        if (memcmp(candidate + OFFSET_NAME, tName, len) == 0 && candidate[OFFSET_NAME + len] == '\0') {
                            s_cvarMap[tName] = candidate;
                            foundCount++;
                            LogInfo("CVar encontrado: %s no endereco %p", tName, candidate);
                        }
                    }
                }
            }

            uint8_t* nextAddr = (uint8_t*)mbi.BaseAddress + mbi.RegionSize;
            if (nextAddr <= addr) break;
            addr = nextAddr;
        }
    } catch (...) {
        LogError("Excecao capturada durante ScanCVars.");
    }
}

bool CVarManager::Initialize() {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    if (s_initialized) return true;

    ScanCVars();
    s_initialized = true;
    ApplyAll();
    return true;
}

void CVarManager::Shutdown() {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    s_cvarMap.clear();
    s_initialized = false;
}

void CVarManager::SetFov(float fov) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarFov = fov;
    void* p = FindCVar("g_minFov");
    if (p) {
        *(float*)((uint8_t*)p + OFFSET_FLOAT) = fov;
        *(int*)((uint8_t*)p + OFFSET_INT) = static_cast<int>(fov);
        snprintf((char*)((uint8_t*)p + OFFSET_STR), 32, "%.1f", fov);
    }
}

void CVarManager::SetCameraMax(float maxDist) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarCamMax = maxDist;
    void* p = FindCVar("g_camMax");
    if (p) {
        *(float*)((uint8_t*)p + OFFSET_FLOAT) = maxDist;
        *(int*)((uint8_t*)p + OFFSET_INT) = static_cast<int>(maxDist);
        snprintf((char*)((uint8_t*)p + OFFSET_STR), 32, "%.1f", maxDist);
    }
}

void CVarManager::SetMaxFps(int fps) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarMaxFps = fps;
    void* p = FindCVar("g_maxfps");
    if (p) {
        *(int*)((uint8_t*)p + OFFSET_INT) = fps;
        *(float*)((uint8_t*)p + OFFSET_FLOAT) = static_cast<float>(fps);
        snprintf((char*)((uint8_t*)p + OFFSET_STR), 32, "%d", fps);
    }
}

void CVarManager::SetTripleBuffering(bool enable) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarTripleBuffering = enable;
    void* p = FindCVar("d3d9_TripleBuffering");
    if (p) {
        *(int*)((uint8_t*)p + OFFSET_INT) = enable ? 1 : 0;
        *(float*)((uint8_t*)p + OFFSET_FLOAT) = enable ? 1.0f : 0.0f;
    }
}

void CVarManager::SetAnisotropic(bool enable) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarAnisotropic = enable;
    void* p = FindCVar("r_anisotropy");
    if (p) {
        int val = enable ? 16 : 0;
        *(int*)((uint8_t*)p + OFFSET_INT) = val;
        *(float*)((uint8_t*)p + OFFSET_FLOAT) = static_cast<float>(val);
    }
}

void CVarManager::ApplyAll() {
    SetFov(g_cvarFov.load());
    SetCameraMax(g_cvarCamMax.load());
    SetMaxFps(g_cvarMaxFps.load());
    SetTripleBuffering(g_cvarTripleBuffering.load());
    SetAnisotropic(g_cvarAnisotropic.load());
}

void CVarManager::ResyncOnMapChange() {
    // If CVars were reallocated or reset by map change, re-apply
    ApplyAll();
}

} // namespace BrService
