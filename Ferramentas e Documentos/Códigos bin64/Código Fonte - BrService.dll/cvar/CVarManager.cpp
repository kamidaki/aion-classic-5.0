#include "CVarManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <atomic>
#include <unordered_map>
#include <string>

namespace BrService {

// ---------------------------------------------------------------------------
// Worker thread state
// ---------------------------------------------------------------------------
static HANDLE g_hWorkerThread = nullptr;
static HANDLE g_hWakeEvent    = nullptr;
static volatile LONG g_stopWorker = 0;
static CRITICAL_SECTION g_cvarLock;
static bool g_csInitialized = false;

// ---------------------------------------------------------------------------
// Native CryEngine Offsets (Aion Classic 5.0 x64)
//   1. ISystem* global pointer at CrySystem.dll + 0x2A11E8
//   2. CSystem::m_pConsole at ISystem + 0x26F0
//   3. Vtable indices documented below.
// ---------------------------------------------------------------------------
static constexpr uintptr_t kCrySystemISystemRva  = 0x2A11E8;
static constexpr uintptr_t kISystemConsoleOffset = 0x26F0;
static constexpr size_t kVtableISystemGetConsole = 0x158 / 8; // (43)
static constexpr size_t kVtableGetCVar           = 0x0C8 / 8; // (25)
static constexpr size_t kVtableExecuteString     = 0x128 / 8; // (37)
static constexpr size_t kVtableCVarSetInt        = 0x020 / 8; // (4)
static constexpr size_t kVtableCVarSetFloat      = 0x028 / 8; // (5)

// ---------------------------------------------------------------------------
// Last-applied shadow values — change detection to prevent redundant writes.
// ---------------------------------------------------------------------------
static std::atomic<float> s_lastFov{-1.0f};
static std::atomic<float> s_lastCamMax{-1.0f};
static std::atomic<int>   s_lastMaxFps{-1};

// ---------------------------------------------------------------------------
// GetNativeConsole
// ---------------------------------------------------------------------------
static uintptr_t GetNativeConsole() {
    uintptr_t hCry = reinterpret_cast<uintptr_t>(GetModuleHandleA("CrySystem.dll"));
    if (!hCry) return 0;

    __try {
        uintptr_t* ppISystem = reinterpret_cast<uintptr_t*>(hCry + kCrySystemISystemRva);
        if (!ppISystem || !*ppISystem) return 0;

        uintptr_t pISystem = *ppISystem;
        if (pISystem < 0x10000 || IsBadReadPtr(reinterpret_cast<void*>(pISystem), sizeof(void*))) return 0;

        // Direct member read
        uintptr_t pConsole = *reinterpret_cast<uintptr_t*>(pISystem + kISystemConsoleOffset);
        if (pConsole >= 0x10000 && !IsBadReadPtr(reinterpret_cast<void*>(pConsole), sizeof(void*))) {
            return pConsole;
        }

        // Fallback: vtable call ISystem::GetIConsole
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

// ---------------------------------------------------------------------------
// CVar pointer cache
// ---------------------------------------------------------------------------
static uintptr_t s_cachedConsole = 0;
static std::unordered_map<std::string, uintptr_t> s_cvarCache;
static SRWLOCK s_cvarCacheLock = SRWLOCK_INIT;

static uintptr_t GetNativeCVar(uintptr_t pConsole, const char* name) {
    if (!pConsole || !name) return 0;
    __try {
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pConsole);
        if (!pVtable || IsBadReadPtr(pVtable, sizeof(void*) * 30)) return 0;
        auto fnGetCVar = reinterpret_cast<uintptr_t(__fastcall*)(void*, const char*, bool)>(pVtable[kVtableGetCVar]);
        if (!fnGetCVar) return 0;
        return fnGetCVar(reinterpret_cast<void*>(pConsole), name, true);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static uintptr_t GetNativeCVarCached(uintptr_t pConsole, const char* name) {
    if (!pConsole || !name) return 0;
    AcquireSRWLockShared(&s_cvarCacheLock);
    if (pConsole == s_cachedConsole) {
        auto it = s_cvarCache.find(name);
        if (it != s_cvarCache.end()) {
            uintptr_t ptr = it->second;
            ReleaseSRWLockShared(&s_cvarCacheLock);
            return ptr;
        }
    }
    ReleaseSRWLockShared(&s_cvarCacheLock);

    uintptr_t pCVar = GetNativeCVar(pConsole, name);
    if (pCVar) {
        AcquireSRWLockExclusive(&s_cvarCacheLock);
        if (pConsole != s_cachedConsole) {
            s_cachedConsole = pConsole;
            s_cvarCache.clear();
        }
        s_cvarCache[name] = pCVar;
        ReleaseSRWLockExclusive(&s_cvarCacheLock);
    }
    return pCVar;
}

// ---------------------------------------------------------------------------
// ExecuteNativeCommand
// ---------------------------------------------------------------------------
static bool ExecuteNativeCommand(uintptr_t pConsole, const char* cmd) {
    if (!pConsole || !cmd || !cmd[0]) return false;
    __try {
        uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pConsole);
        if (!pVtable || IsBadReadPtr(pVtable, sizeof(void*) * 40)) return false;
        auto fnExec = reinterpret_cast<void(__fastcall*)(void*, const char*, bool, bool)>(pVtable[kVtableExecuteString]);
        if (!fnExec) return false;
        fnExec(reinterpret_cast<void*>(pConsole), cmd, false, false);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// ---------------------------------------------------------------------------
// Clean, safe CVar setters (No arbitrary memory writes, no bogus callbacks)
// ---------------------------------------------------------------------------
static bool SetNativeCVarFloat(uintptr_t pConsole, const char* name, float val) {
    if (!pConsole) return false;
    bool directSuccess = false;
    __try {
        uintptr_t pCVar = GetNativeCVarCached(pConsole, name);
        if (pCVar && !IsBadReadPtr(reinterpret_cast<void*>(pCVar), sizeof(void*))) {
            // Strip protection flags: VF_READONLY (0x800), VF_CHEAT_NOCHECK (0x80000), VF_NET_SYNCED (0x02)
            uint32_t* pFlags = reinterpret_cast<uint32_t*>(pCVar + 0x98);
            if (!IsBadWritePtr(pFlags, sizeof(uint32_t))) {
                *pFlags &= ~(0x80800u | 0x800u | 0x02u);
            }

            // Official vtable Set(float)
            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 10)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, float)>(pVtable[kVtableCVarSetFloat]);
                if (fnSet) {
                    fnSet(reinterpret_cast<void*>(pCVar), val);
                    directSuccess = true;
                }
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}

    // Fallback sync via command string
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "%s %f", name, val);
    ExecuteNativeCommand(pConsole, cmd);
    return directSuccess;
}

static bool SetNativeCVarInt(uintptr_t pConsole, const char* name, int val) {
    if (!pConsole) return false;
    bool directSuccess = false;
    __try {
        uintptr_t pCVar = GetNativeCVarCached(pConsole, name);
        if (pCVar && !IsBadReadPtr(reinterpret_cast<void*>(pCVar), sizeof(void*))) {
            uint32_t* pFlags = reinterpret_cast<uint32_t*>(pCVar + 0x98);
            if (!IsBadWritePtr(pFlags, sizeof(uint32_t))) {
                *pFlags &= ~(0x80800u | 0x800u | 0x02u);
            }

            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 10)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, int)>(pVtable[kVtableCVarSetInt]);
                if (fnSet) {
                    fnSet(reinterpret_cast<void*>(pCVar), val);
                    directSuccess = true;
                }
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}

    char cmd[128];
    snprintf(cmd, sizeof(cmd), "%s %d", name, val);
    ExecuteNativeCommand(pConsole, cmd);
    return directSuccess;
}

// ---------------------------------------------------------------------------
// ApplyFov
// ---------------------------------------------------------------------------
static void ApplyFov(uintptr_t pConsole, float fov) {
    SetNativeCVarFloat(pConsole, "delete_0721_g_minfov", fov);
    SetNativeCVarFloat(pConsole, "delete_0721_g_midFov", fov);
    SetNativeCVarFloat(pConsole, "delete_0721_g_maxFov", fov);
    SetNativeCVarFloat(pConsole, "fov",                 fov);
    SetNativeCVarFloat(pConsole, "fov_angle",           fov);
    SetNativeCVarFloat(pConsole, "g_minFov",            fov);
    SetNativeCVarFloat(pConsole, "g_maxFov",            fov);
    SetNativeCVarFloat(pConsole, "g_midFov",            fov);
}

// ---------------------------------------------------------------------------
// ApplyCamMax
// ---------------------------------------------------------------------------
static void ApplyCamMax(uintptr_t pConsole, float cam) {
    SetNativeCVarFloat(pConsole, "delete_0721_g_camMax", cam);
    SetNativeCVarFloat(pConsole, "g_camMax",            cam);
    SetNativeCVarFloat(pConsole, "cb_cam_max_dist",     cam);
    SetNativeCVarFloat(pConsole, "g_cam_p_max",         cam);
    SetNativeCVarFloat(pConsole, "cam_max_distance",    cam);
}

// ---------------------------------------------------------------------------
// ApplyMaxFps
// ---------------------------------------------------------------------------
static void ApplyMaxFps(uintptr_t pConsole, int fps) {
    SetNativeCVarInt(pConsole, "delete_0721_g_maxfps", fps);
    SetNativeCVarInt(pConsole, "g_maxfps",             fps);
    SetNativeCVarInt(pConsole, "sys_fixedframe",        0);
}

// ---------------------------------------------------------------------------
// WorkerApplyAll
// ---------------------------------------------------------------------------
static void WorkerApplyAll() {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return;

    static bool s_loggedFound = false;
    if (!s_loggedFound) {
        s_loggedFound = true;
        LogInfo("CVarManager: Console CryEngine adquirido (0x%p).", (void*)pConsole);
    }

    // FOV
    if (g_featFov.load()) {
        float fov = std::clamp(g_cvarFov.load(), 60.0f, 120.0f);
        float lastFov = s_lastFov.load(std::memory_order_relaxed);
        if (fov != lastFov) {
            ApplyFov(pConsole, fov);
            s_lastFov.store(fov, std::memory_order_relaxed);
        }
    }

    // Camera Max
    if (g_featCamMax.load()) {
        float cam = std::clamp(g_cvarCamMax.load(), 5.0f, 50.0f);
        float lastCam = s_lastCamMax.load(std::memory_order_relaxed);
        if (cam != lastCam) {
            ApplyCamMax(pConsole, cam);
            s_lastCamMax.store(cam, std::memory_order_relaxed);
        }
    }

    // FPS Cap
    if (g_featFpsUnlock.load()) {
        int fps = g_cvarMaxFps.load();
        int lastFps = s_lastMaxFps.load(std::memory_order_relaxed);
        if (fps != lastFps) {
            ApplyMaxFps(pConsole, fps);
            s_lastMaxFps.store(fps, std::memory_order_relaxed);
        }
    }
}

// ---------------------------------------------------------------------------
// Worker thread proc
// ---------------------------------------------------------------------------
static DWORD WINAPI CVarWorkerThreadProc(LPVOID) {
    bool initialApplied = false;
    while (!InterlockedCompareExchange(&g_stopWorker, 0, 0)) {
        if (!initialApplied) {
            uintptr_t pConsole = GetNativeConsole();
            if (pConsole != 0) {
                s_lastFov.store(-1.0f, std::memory_order_relaxed);
                s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
                s_lastMaxFps.store(-1, std::memory_order_relaxed);
                WorkerApplyAll();
                initialApplied = true;
                LogInfo("CVarManager: CVars aplicados com sucesso.");
            }
        } else {
            WorkerApplyAll();
        }

        DWORD waitTime = initialApplied ? INFINITE : 1500;
        if (g_hWakeEvent) {
            WaitForSingleObject(g_hWakeEvent, waitTime);
        } else {
            Sleep(waitTime);
        }
    }
    return 0;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
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
    }
    return true;
}

void CVarManager::Shutdown() {
    InterlockedExchange(&g_stopWorker, 1);
    if (g_hWakeEvent) {
        SetEvent(g_hWakeEvent);
    }
    if (g_hWorkerThread) {
        WaitForSingleObject(g_hWorkerThread, 250);
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
    AcquireSRWLockExclusive(&s_cvarCacheLock);
    s_cvarCache.clear();
    s_cachedConsole = 0;
    ReleaseSRWLockExclusive(&s_cvarCacheLock);
}

void CVarManager::SetFov(float fov) {
    float clamped = std::clamp(fov, 60.0f, 120.0f);
    g_cvarFov.store(clamped, std::memory_order_relaxed);

    float last = s_lastFov.load(std::memory_order_relaxed);
    if (clamped == last) return;

    uintptr_t pConsole = GetNativeConsole();
    if (pConsole) {
        ApplyFov(pConsole, clamped);
        s_lastFov.store(clamped, std::memory_order_relaxed);
    }
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetCameraMax(float maxDist) {
    float clamped = std::clamp(maxDist, 5.0f, 50.0f);
    g_cvarCamMax.store(clamped, std::memory_order_relaxed);

    float last = s_lastCamMax.load(std::memory_order_relaxed);
    if (clamped == last) return;

    uintptr_t pConsole = GetNativeConsole();
    if (pConsole) {
        ApplyCamMax(pConsole, clamped);
        s_lastCamMax.store(clamped, std::memory_order_relaxed);
    }
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetMaxFps(int fps) {
    g_cvarMaxFps.store(fps, std::memory_order_relaxed);

    int last = s_lastMaxFps.load(std::memory_order_relaxed);
    if (fps == last) return;

    uintptr_t pConsole = GetNativeConsole();
    if (pConsole) {
        ApplyMaxFps(pConsole, fps);
        s_lastMaxFps.store(fps, std::memory_order_relaxed);
    }
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetTripleBuffering(bool enable) {
    g_cvarTripleBuffering.store(enable, std::memory_order_relaxed);
    // Triple buffering removed from D3D9 manipulation to prevent swapchain desync and UI flickering
}

void CVarManager::ApplyAll() {
    s_lastFov.store(-1.0f, std::memory_order_relaxed);
    s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
    s_lastMaxFps.store(-1, std::memory_order_relaxed);
    WorkerApplyAll();
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ResyncOnMapChange() {
    s_lastFov.store(-1.0f, std::memory_order_relaxed);
    s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
    s_lastMaxFps.store(-1, std::memory_order_relaxed);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

bool CVarManager::IsWorkerRunning() {
    return g_hWorkerThread != nullptr;
}

} // namespace BrService
