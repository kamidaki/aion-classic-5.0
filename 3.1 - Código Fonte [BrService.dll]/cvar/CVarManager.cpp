#include "CVarManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <atomic>

namespace BrService {

// Worker state
static HANDLE g_hWorkerThread = nullptr;
static HANDLE g_hWakeEvent = nullptr;
static volatile LONG g_stopWorker = 0;
static CRITICAL_SECTION g_cvarLock;
static bool g_csInitialized = false;

// Native CryEngine Offsets (Aion Classic 5.0 x64)
// Verified from CrySystem.dll reverse engineering:
// 1. ISystem* global pointer is stored at CrySystem.dll + 0x2A11E8 (set in CreateSystemInterface -> RVA 0x1A1B4)
static constexpr uintptr_t kCrySystemISystemRva   = 0x2A11E8;
// 2. Inside CSystem (implementing ISystem), offset 0x26F0 directly holds IConsole* (CXConsole instance)
static constexpr uintptr_t kISystemConsoleOffset  = 0x26F0;
// 3. ISystem vtable:
static constexpr size_t kVtableISystemGetConsole  = 0x158 / 8; // (43) ISystem::GetIConsole() -> returns pConsole
// 4. CXConsole vtable (implementing IConsole):
static constexpr size_t kVtableGetCVar             = 0x0C8 / 8; // (25) IConsole::GetCVar(const char*, bool)
static constexpr size_t kVtableExecuteString       = 0x128 / 8; // (37) IConsole::ExecuteString(const char*, bool, bool)
// 5. CXConsoleVariable vtable (implementing ICVar):
static constexpr size_t kVtableCVarGetIVal        = 0x008 / 8; // (1) ICVar::GetIVal()
static constexpr size_t kVtableCVarGetFVal        = 0x010 / 8; // (2) ICVar::GetFVal()
static constexpr size_t kVtableCVarGetStr         = 0x018 / 8; // (3) ICVar::GetString()
static constexpr size_t kVtableCVarSetInt         = 0x020 / 8; // (4) ICVar::Set(int)
static constexpr size_t kVtableCVarSetFloat       = 0x028 / 8; // (5) ICVar::Set(float)
static constexpr size_t kVtableCVarSetStr         = 0x030 / 8; // (6) ICVar::Set(const char*)
static constexpr size_t kVtableCVarOnChanged      = 0x078 / 8; // (15) ICVar::OnChanged(int)

static uintptr_t GetNativeConsole() {
    uintptr_t hCry = reinterpret_cast<uintptr_t>(GetModuleHandleA("CrySystem.dll"));
    if (!hCry) return 0;

    __try {
        uintptr_t* ppISystem = reinterpret_cast<uintptr_t*>(hCry + kCrySystemISystemRva);
        if (!ppISystem || !*ppISystem) return 0;

        uintptr_t pISystem = *ppISystem;
        if (pISystem < 0x10000 || IsBadReadPtr(reinterpret_cast<void*>(pISystem), sizeof(void*))) return 0;

        // Directly read console pointer from ISystem member
        uintptr_t pConsole = *reinterpret_cast<uintptr_t*>(pISystem + kISystemConsoleOffset);
        if (pConsole && pConsole >= 0x10000 && !IsBadReadPtr(reinterpret_cast<void*>(pConsole), sizeof(void*))) {
            return pConsole;
        }

        // Fallback: call ISystem::GetIConsole (vtable index 43, offset 0x158)
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pISystem);
        if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 45)) {
            auto fnGetConsole = reinterpret_cast<uintptr_t(__fastcall*)(void*)>(pVtable[kVtableISystemGetConsole]);
            if (fnGetConsole) {
                return fnGetConsole(reinterpret_cast<void*>(pISystem));
            }
        }
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static uintptr_t GetNativeCVar(uintptr_t pConsole, const char* name) {
    if (!pConsole || !name) return 0;

    __try {
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pConsole);
        if (!pVtable || IsBadReadPtr(pVtable, sizeof(void*) * 30)) return 0;

        auto fnGetCVar = reinterpret_cast<uintptr_t(__fastcall*)(void*, const char*, bool)>(
            pVtable[kVtableGetCVar]);
        if (!fnGetCVar) return 0;

        return fnGetCVar(reinterpret_cast<void*>(pConsole), name, true);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static bool ExecuteNativeCommand(const char* cmd) {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole || !cmd || !cmd[0]) return false;

    __try {
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pConsole);
        if (!pVtable || IsBadReadPtr(pVtable, sizeof(void*) * 40)) return false;

        auto fnExec = reinterpret_cast<void(__fastcall*)(void*, const char*, bool, bool)>(
            pVtable[kVtableExecuteString]);
        if (!fnExec) return false;

        fnExec(reinterpret_cast<void*>(pConsole), cmd, false, false);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static bool SetNativeCVarFloat(const char* name, float val) {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return false;

    bool directSuccess = false;
    __try {
        uintptr_t pCVar = GetNativeCVar(pConsole, name);
        if (pCVar && !IsBadReadPtr(reinterpret_cast<void*>(pCVar), sizeof(void*))) {
            // 1. Limpar flags restritivas como VF_READONLY (0x800) e 0x80000
            uint32_t* pFlags = reinterpret_cast<uint32_t*>(pCVar + 0x98);
            if (!IsBadWritePtr(pFlags, sizeof(uint32_t))) {
                *pFlags &= ~(0x80800 | 0x800 | 0x02);
            }

            // 2. Modificação direta nos ponteiros de valor da memória (offset 0xB0 = float*, 0xA8 = int*)
            uintptr_t pFloatPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xB0);
            if (pFloatPtr && !IsBadWritePtr(reinterpret_cast<void*>(pFloatPtr), sizeof(float))) {
                *reinterpret_cast<float*>(pFloatPtr) = val;
                directSuccess = true;
            }

            uintptr_t pIntPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xA8);
            if (pIntPtr && !IsBadWritePtr(reinterpret_cast<void*>(pIntPtr), sizeof(int))) {
                *reinterpret_cast<int*>(pIntPtr) = static_cast<int>(val);
            }

            // 3. Chamada de vtable Set(float) e notificação OnChanged
            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 16)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, float)>(
                    pVtable[kVtableCVarSetFloat]);
                if (fnSet) {
                    fnSet(reinterpret_cast<void*>(pCVar), val);
                }

                auto fnOnChanged = reinterpret_cast<void(__fastcall*)(void*, int)>(
                    pVtable[kVtableCVarOnChanged]);
                if (fnOnChanged) {
                    fnOnChanged(reinterpret_cast<void*>(pCVar), 8);
                }
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }

    // Notificar subsistemas do motor através da string de console
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "%s %f", name, val);
    ExecuteNativeCommand(cmd);
    return directSuccess;
}

static bool SetNativeCVarInt(const char* name, int val) {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return false;

    bool directSuccess = false;
    __try {
        uintptr_t pCVar = GetNativeCVar(pConsole, name);
        if (pCVar && !IsBadReadPtr(reinterpret_cast<void*>(pCVar), sizeof(void*))) {
            // 1. Limpar flags restritivas como VF_READONLY (0x800) e 0x80000
            uint32_t* pFlags = reinterpret_cast<uint32_t*>(pCVar + 0x98);
            if (!IsBadWritePtr(pFlags, sizeof(uint32_t))) {
                *pFlags &= ~(0x80800 | 0x800 | 0x02);
            }

            // 2. Modificação direta nos ponteiros de valor da memória (offset 0xA8 = int*, 0xB0 = float*)
            uintptr_t pIntPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xA8);
            if (pIntPtr && !IsBadWritePtr(reinterpret_cast<void*>(pIntPtr), sizeof(int))) {
                *reinterpret_cast<int*>(pIntPtr) = val;
                directSuccess = true;
            }

            uintptr_t pFloatPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xB0);
            if (pFloatPtr && !IsBadWritePtr(reinterpret_cast<void*>(pFloatPtr), sizeof(float))) {
                *reinterpret_cast<float*>(pFloatPtr) = static_cast<float>(val);
            }

            // 3. Chamada de vtable Set(int) no índice 4 (offset 0x20) e notificação OnChanged
            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 16)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, int)>(
                    pVtable[kVtableCVarSetInt]);
                if (fnSet) {
                    fnSet(reinterpret_cast<void*>(pCVar), val);
                }

                auto fnOnChanged = reinterpret_cast<void(__fastcall*)(void*, int)>(
                    pVtable[kVtableCVarOnChanged]);
                if (fnOnChanged) {
                    fnOnChanged(reinterpret_cast<void*>(pCVar), 8);
                }
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }

    // Notificar subsistemas do motor através da string de console
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "%s %d", name, val);
    ExecuteNativeCommand(cmd);
    return directSuccess;
}

static void WorkerApplyAll() {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return;

    static bool s_loggedFound = false;
    if (!s_loggedFound) {
        s_loggedFound = true;
        LogInfo("CVarManager: Console CryEngine adquirido com sucesso em 0x%p (CrySystem.dll). CVars sincronizados.", (void*)pConsole);
    }

    // 1. Panoramic FOV
    if (g_featFov.load()) {
        float fov = std::clamp(g_cvarFov.load(), 60.0f, 120.0f);
        SetNativeCVarFloat("delete_0721_g_minfov", fov);
        SetNativeCVarFloat("delete_0721_g_midFov", fov);
        SetNativeCVarFloat("delete_0721_g_maxFov", fov);
        SetNativeCVarFloat("fov", fov);
        SetNativeCVarFloat("fov_angle", fov);
        SetNativeCVarFloat("g_minFov", fov);
        SetNativeCVarFloat("g_maxFov", fov);
        SetNativeCVarFloat("g_midFov", fov);
    }

    // 2. Camera Max Zoom
    if (g_featCamMax.load()) {
        float cam = std::clamp(g_cvarCamMax.load(), 5.0f, 50.0f);
        SetNativeCVarFloat("delete_0721_g_camMax", cam);
        SetNativeCVarFloat("g_camMax", cam);
        SetNativeCVarFloat("cb_cam_max_dist", cam);
        SetNativeCVarFloat("g_cam_p_max", cam);
        SetNativeCVarFloat("cam_max_distance", cam);
    }

    // 3. Framerate Cap
    if (g_featFpsUnlock.load()) {
        int fps = g_cvarMaxFps.load();
        int applyFps = (fps == 0) ? 0 : fps;
        SetNativeCVarInt("delete_0721_g_maxfps", applyFps);
        SetNativeCVarInt("g_maxfps", applyFps);
        SetNativeCVarInt("sys_fixedframe", 0);
    }

    // 4. Triple Buffering
    {
        int tb = g_cvarTripleBuffering.load() ? 1 : 0;
        SetNativeCVarInt("d3d9_TripleBuffering", tb);
    }

    // 5. Anisotropic Filtering
    {
        int aniso = g_cvarAnisotropic.load() ? 16 : 0;
        SetNativeCVarInt("r_Texture_Anisotropic_Level", aniso);
        SetNativeCVarInt("d3d9_Texture_Filter_Anisotropic", g_cvarAnisotropic.load() ? 1 : 0);
    }

    // 6. Free Fly
    {
        int ff = g_featFreeFly.load() ? 1 : 0;
        SetNativeCVarInt("g_freefly", ff);
    }

    // 7. Engine Performance
    SetNativeCVarInt("sys_fixedframe", 0);
    SetNativeCVarFloat("r_EnvCMupdateInterval", 0.100000f);
    SetNativeCVarFloat("r_EnvTexUpdateInterval", 0.100000f);
}

static DWORD WINAPI CVarWorkerThreadProc(LPVOID) {
    const DWORD intervalMs = 1200;
    while (!InterlockedCompareExchange(&g_stopWorker, 0, 0)) {
        WorkerApplyAll();
        if (g_hWakeEvent) {
            WaitForSingleObject(g_hWakeEvent, intervalMs);
        } else {
            Sleep(intervalMs);
        }
    }
    return 0;
}

bool CVarManager::Initialize() {
    if (!g_csInitialized) {
        InitializeCriticalSection(&g_cvarLock);
        g_csInitialized = true;
    }

    InterlockedExchange(&g_stopWorker, 0);

    if (!g_hWakeEvent) {
        g_hWakeEvent = CreateEvent(nullptr, FALSE, FALSE, nullptr);
    }

    if (!g_hWorkerThread) {
        g_hWorkerThread = CreateThread(nullptr, 0, CVarWorkerThreadProc, nullptr, 0, nullptr);
        LogInfo("CVarManager: Worker thread iniciado com sucesso. Aguardando inicializacao do CrySystem...");
    }
    return true;
}

void CVarManager::Shutdown() {
    InterlockedExchange(&g_stopWorker, 1);
    if (g_hWakeEvent) {
        SetEvent(g_hWakeEvent);
    }
    if (g_hWorkerThread) {
        WaitForSingleObject(g_hWorkerThread, 2000);
        CloseHandle(g_hWorkerThread);
        g_hWorkerThread = nullptr;
    }
    if (g_hWakeEvent) {
        CloseHandle(g_hWakeEvent);
        g_hWakeEvent = nullptr;
    }
    if (g_csInitialized) {
        DeleteCriticalSection(&g_cvarLock);
        g_csInitialized = false;
    }
}

void CVarManager::SetFov(float fov) {
    float clamped = std::clamp(fov, 60.0f, 120.0f);
    g_cvarFov = clamped;
    SetNativeCVarFloat("delete_0721_g_minfov", clamped);
    SetNativeCVarFloat("delete_0721_g_midFov", clamped);
    SetNativeCVarFloat("delete_0721_g_maxFov", clamped);
    SetNativeCVarFloat("fov", clamped);
    SetNativeCVarFloat("fov_angle", clamped);
    SetNativeCVarFloat("g_minFov", clamped);
    SetNativeCVarFloat("g_maxFov", clamped);
    SetNativeCVarFloat("g_midFov", clamped);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetCameraMax(float maxDist) {
    float clamped = std::clamp(maxDist, 5.0f, 50.0f);
    g_cvarCamMax = clamped;
    SetNativeCVarFloat("delete_0721_g_camMax", clamped);
    SetNativeCVarFloat("g_camMax", clamped);
    SetNativeCVarFloat("cb_cam_max_dist", clamped);
    SetNativeCVarFloat("g_cam_p_max", clamped);
    SetNativeCVarFloat("cam_max_distance", clamped);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetMaxFps(int fps) {
    g_cvarMaxFps = fps;
    int applyFps = (fps == 0) ? 0 : fps;
    SetNativeCVarInt("delete_0721_g_maxfps", applyFps);
    SetNativeCVarInt("g_maxfps", applyFps);
    SetNativeCVarInt("sys_fixedframe", 0);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetTripleBuffering(bool enable) {
    g_cvarTripleBuffering = enable;
    SetNativeCVarInt("d3d9_TripleBuffering", enable ? 1 : 0);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetAnisotropic(bool enable) {
    g_cvarAnisotropic = enable;
    SetNativeCVarInt("r_Texture_Anisotropic_Level", enable ? 16 : 0);
    SetNativeCVarInt("d3d9_Texture_Filter_Anisotropic", enable ? 1 : 0);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetFreeFly(bool enable) {
    g_featFreeFly = enable;
    SetNativeCVarInt("g_freefly", enable ? 1 : 0);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ApplyAll() {
    WorkerApplyAll();
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ResyncOnMapChange() {
    WorkerApplyAll();
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

bool CVarManager::IsWorkerRunning() {
    return g_hWorkerThread != nullptr;
}

} // namespace BrService
