#include "CVarManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <mutex>
#include <vector>
#include <cstdio>
#include <cstring>

namespace BrService {

static std::recursive_mutex s_cvarMutex;
static std::unordered_map<std::string, void*> s_cvarMap;
static bool s_initialized = false;

// 64-bit CryEngine CVar structure offsets (Standard CryEngine 1.5 / Aion 64-bit)
static constexpr size_t CVAR_FLAG_OFFSET = 8;
static constexpr size_t CVAR_NAME_OFFSET = 9;
static constexpr size_t CVAR_INT_OFFSET  = 184;
static constexpr size_t CVAR_FLOAT_OFFSET= 188;
static constexpr size_t CVAR_STR_OFFSET  = 192;

void* CVarManager::FindCVar(const char* name) {
    if (!name) return nullptr;
    auto it = s_cvarMap.find(name);
    if (it != s_cvarMap.end()) return it->second;
    return nullptr;
}

static void WriteCVarFloat(void* pCVar, float val) {
    if (!pCVar) return;
    uint8_t* p = static_cast<uint8_t*>(pCVar);
    *reinterpret_cast<int*>(p + CVAR_INT_OFFSET) = static_cast<int>(val);
    *reinterpret_cast<float*>(p + CVAR_FLOAT_OFFSET) = val;
    sprintf_s(reinterpret_cast<char*>(p + CVAR_STR_OFFSET), 64, "%f", val);
}

static void WriteCVarInt(void* pCVar, int val) {
    if (!pCVar) return;
    uint8_t* p = static_cast<uint8_t*>(pCVar);
    *reinterpret_cast<int*>(p + CVAR_INT_OFFSET) = val;
    *reinterpret_cast<float*>(p + CVAR_FLOAT_OFFSET) = static_cast<float>(val);
    sprintf_s(reinterpret_cast<char*>(p + CVAR_STR_OFFSET), 64, "%d", val);
}

void CVarManager::ScanCVars() {
    const char* targets[] = {
        "g_minFov", "g_camMax", "g_maxfps", "g_freefly",
        "d3d9_TripleBuffering", "r_Texture_Anisotropic_Level", "r_anisotropy", "con_disable_console"
    };

    SYSTEM_INFO si;
    GetSystemInfo(&si);

    MEMORY_BASIC_INFORMATION mbi;
    uint8_t* addr = static_cast<uint8_t*>(si.lpMinimumApplicationAddress);
    uint8_t* maxAddr = static_cast<uint8_t*>(si.lpMaximumApplicationAddress);

    size_t foundCount = 0;
    size_t totalTargets = sizeof(targets) / sizeof(targets[0]);

    try {
        while (addr < maxAddr && foundCount < totalTargets) {
            if (!VirtualQuery(addr, &mbi, sizeof(mbi))) {
                addr += 0x1000;
                continue;
            }

            if ((mbi.State == MEM_COMMIT) &&
                (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE) &&
                !(mbi.Protect & PAGE_GUARD)) {

                uint8_t* pStart = static_cast<uint8_t*>(mbi.BaseAddress);
                size_t regionSize = mbi.RegionSize;

                // Scan in 16-byte steps (CryEngine heap alignment)
                for (size_t i = 0; i + 256 < regionSize; i += 16) {
                    uint8_t* candidate = pStart + i;

                    for (const char* tName : targets) {
                        if (s_cvarMap.find(tName) != s_cvarMap.end()) continue;

                        size_t len = strlen(tName);
                        // In CryEngine 64-bit: candidate[8] is boolean flag (0 or 1), candidate[9] is ASCII CVar name
                        if ((candidate[CVAR_FLAG_OFFSET] == 0 || candidate[CVAR_FLAG_OFFSET] == 1) &&
                            memcmp(candidate + CVAR_NAME_OFFSET, tName, len) == 0 &&
                            (candidate[CVAR_NAME_OFFSET + len] == '\0' || candidate[CVAR_NAME_OFFSET + len] == ' ')) {

                            s_cvarMap[tName] = candidate;
                            foundCount++;
                            LogInfo("CVar CryEngine localizado: %s no endereco %p", tName, candidate);
                        }
                    }
                }
            }

            uint8_t* nextAddr = static_cast<uint8_t*>(mbi.BaseAddress) + mbi.RegionSize;
            if (nextAddr <= addr) break;
            addr = nextAddr;
        }
    } catch (...) {
        LogError("Excecao capturada durante ScanCVars.");
    }

    LogInfo("Varredura de CVars concluida. Total encontrados: %zu/%zu", foundCount, totalTargets);
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
        WriteCVarFloat(p, fov);
    }
}

void CVarManager::SetCameraMax(float maxDist) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarCamMax = maxDist;
    void* p = FindCVar("g_camMax");
    if (p) {
        WriteCVarFloat(p, maxDist);
    }
}

void CVarManager::SetMaxFps(int fps) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarMaxFps = fps;
    void* p = FindCVar("g_maxfps");
    if (p) {
        WriteCVarInt(p, fps);
    }
}

void CVarManager::SetTripleBuffering(bool enable) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarTripleBuffering = enable;
    void* p = FindCVar("d3d9_TripleBuffering");
    if (p) {
        WriteCVarInt(p, enable ? 1 : 0);
    }
}

void CVarManager::SetAnisotropic(bool enable) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    g_cvarAnisotropic = enable;
    int val = enable ? 16 : 0;

    void* p1 = FindCVar("r_Texture_Anisotropic_Level");
    if (p1) WriteCVarInt(p1, val);

    void* p2 = FindCVar("r_anisotropy");
    if (p2) WriteCVarInt(p2, val);
}

void CVarManager::SetFreeFly(bool enable) {
    std::lock_guard<std::recursive_mutex> lock(s_cvarMutex);
    void* p = FindCVar("g_freefly");
    if (p) {
        WriteCVarInt(p, enable ? 1 : 0);
        LogInfo("g_freefly configurado em tempo real para: %d", enable ? 1 : 0);
    }
}

void CVarManager::ApplyAll() {
    if (g_featFov.load()) SetFov(g_cvarFov.load());
    if (g_featCamMax.load()) SetCameraMax(g_cvarCamMax.load());
    if (g_featFpsUnlock.load()) SetMaxFps(g_cvarMaxFps.load());
    SetTripleBuffering(g_cvarTripleBuffering.load());
    SetAnisotropic(g_cvarAnisotropic.load());
    if (g_featFreeFly.load()) {
        SetFreeFly(true);
    } else {
        SetFreeFly(false);
    }
}

void CVarManager::ResyncOnMapChange() {
    // If CVars were re-registered on map load, re-scan if needed and reapply
    if (s_cvarMap.empty()) {
        ScanCVars();
    }
    ApplyAll();
}

} // namespace BrService
