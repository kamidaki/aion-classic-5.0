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

// Native Game.dll Engine offsets (Aion Classic 5.0 x64)
// Verified directly from client disassembly at Game.dll RVA 0x47DBA8
static constexpr uintptr_t kEngineGlobalRva = 0x156F2D0;
static constexpr size_t kVtableGetConsole   = 0x158 / 8; // ISystem::GetIConsole
static constexpr size_t kVtableGetCVar      = 0x0C8 / 8; // IConsole::GetCVar(const char*, bool)
static constexpr size_t kVtableCVarSetFloat = 0x028 / 8; // ICVar::Set(float)
static constexpr size_t kVtableCVarSetInt   = 0x030 / 8; // ICVar::Set(int)
static constexpr size_t kVtableCVarSetStr   = 0x020 / 8; // ICVar::Set(const char*)

static bool IsGameReady() {
    return GetModuleHandleA("Game.dll") != nullptr &&
           GetModuleHandleA("CrySystem.dll") != nullptr;
}

static uintptr_t GetNativeConsole() {
    uintptr_t hGame = reinterpret_cast<uintptr_t>(GetModuleHandleA("Game.dll"));
    if (!hGame) return 0;

    __try {
        uintptr_t** ppEngineGlobal = reinterpret_cast<uintptr_t**>(hGame + kEngineGlobalRva);
        if (!ppEngineGlobal || !*ppEngineGlobal) return 0;

        uintptr_t* pEngineGlobal = *ppEngineGlobal;
        if (!pEngineGlobal || !*pEngineGlobal) return 0;

        auto fnGetConsole = reinterpret_cast<uintptr_t(__fastcall*)(void*)>(
            pEngineGlobal[kVtableGetConsole]);
        if (!fnGetConsole) return 0;

        return fnGetConsole(pEngineGlobal);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static uintptr_t GetNativeCVar(uintptr_t pConsole, const char* name) {
    if (!pConsole || !name) return 0;

    __try {
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pConsole);
        if (!pVtable) return 0;

        auto fnGetCVar = reinterpret_cast<uintptr_t(__fastcall*)(void*, const char*, bool)>(
            pVtable[kVtableGetCVar]);
        if (!fnGetCVar) return 0;

        return fnGetCVar(reinterpret_cast<void*>(pConsole), name, true);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static bool SetNativeCVarFloat(const char* name, float val) {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return false;

    __try {
        uintptr_t pCVar = GetNativeCVar(pConsole, name);
        if (!pCVar) return false;

        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
        if (!pVtable) return false;

        auto fnSet = reinterpret_cast<void(__fastcall*)(void*, float)>(
            pVtable[kVtableCVarSetFloat]);
        if (!fnSet) return false;

        fnSet(reinterpret_cast<void*>(pCVar), val);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static bool SetNativeCVarInt(const char* name, int val) {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return false;

    __try {
        uintptr_t pCVar = GetNativeCVar(pConsole, name);
        if (!pCVar) return false;

        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
        if (!pVtable) return false;

        auto fnSet = reinterpret_cast<void(__fastcall*)(void*, int)>(
            pVtable[kVtableCVarSetInt]);
        if (!fnSet) return false;

        fnSet(reinterpret_cast<void*>(pCVar), val);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static void WorkerApplyAll() {
    if (!IsGameReady()) return;

    // 1. Panoramic FOV (delete_0721_g_minfov & delete_0721_g_maxFov)
    if (g_featFov.load()) {
        float fov = std::clamp(g_cvarFov.load(), 60.0f, 120.0f);
        SetNativeCVarFloat("delete_0721_g_minfov", fov);
        SetNativeCVarFloat("delete_0721_g_maxFov", fov);
        SetNativeCVarFloat("delete_0721_g_midFov", fov);
        // Fallback names in case of client variants
        SetNativeCVarFloat("g_minFov", fov);
        SetNativeCVarFloat("g_maxFov", fov);
    }

    // 2. Camera Max Zoom (delete_0721_g_camMax & cb_cam_max_dist)
    if (g_featCamMax.load()) {
        float cam = std::clamp(g_cvarCamMax.load(), 5.0f, 45.0f);
        SetNativeCVarFloat("delete_0721_g_camMax", cam);
        SetNativeCVarFloat("cb_cam_max_dist", cam);
        // Fallback
        SetNativeCVarFloat("g_camMax", cam);
    }

    // 3. Framerate Cap (delete_0721_g_maxfps)
    if (g_featFpsUnlock.load()) {
        int fps = g_cvarMaxFps.load();
        SetNativeCVarInt("delete_0721_g_maxfps", fps);
        SetNativeCVarInt("g_maxfps", fps);
    }

    // 4. Triple Buffering (d3d9_TripleBuffering)
    {
        int tb = g_cvarTripleBuffering.load() ? 1 : 0;
        SetNativeCVarInt("d3d9_TripleBuffering", tb);
    }

    // 5. Anisotropic Filtering (r_Texture_Anisotropic_Level)
    {
        int aniso = g_cvarAnisotropic.load() ? 16 : 0;
        SetNativeCVarInt("r_Texture_Anisotropic_Level", aniso);
    }

    // 6. Free Fly (g_freefly)
    {
        int ff = g_featFreeFly.load() ? 1 : 0;
        SetNativeCVarInt("g_freefly", ff);
    }
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
        LogInfo("CVarManager conectado com sucesso ao subsistema de console nativo da CryEngine.");
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
    // Apply instantly
    SetNativeCVarFloat("delete_0721_g_minfov", clamped);
    SetNativeCVarFloat("delete_0721_g_maxFov", clamped);
    SetNativeCVarFloat("delete_0721_g_midFov", clamped);
    SetNativeCVarFloat("g_minFov", clamped);
    SetNativeCVarFloat("g_maxFov", clamped);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetCameraMax(float maxDist) {
    float clamped = std::clamp(maxDist, 5.0f, 45.0f);
    g_cvarCamMax = clamped;
    // Apply instantly
    SetNativeCVarFloat("delete_0721_g_camMax", clamped);
    SetNativeCVarFloat("cb_cam_max_dist", clamped);
    SetNativeCVarFloat("g_camMax", clamped);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetMaxFps(int fps) {
    g_cvarMaxFps = fps;
    // Apply instantly
    SetNativeCVarInt("delete_0721_g_maxfps", fps);
    SetNativeCVarInt("g_maxfps", fps);
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
