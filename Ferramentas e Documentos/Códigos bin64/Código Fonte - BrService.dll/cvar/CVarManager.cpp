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
// g_cvarLock / g_csInitialized kept for ABI safety but no longer used for
// per-call locking — we rely on atomics throughout.
static CRITICAL_SECTION g_cvarLock;
static bool g_csInitialized = false;

// ---------------------------------------------------------------------------
// Native CryEngine Offsets (Aion Classic 5.0 x64)
// Verified from CrySystem.dll reverse engineering:
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
static constexpr size_t kVtableCVarOnChanged     = 0x078 / 8; // (15)

// ---------------------------------------------------------------------------
// Last-applied shadow values — change detection to prevent redundant writes.
// Initialized to sentinel values that will never match a valid user setting,
// ensuring the first apply always goes through.
// ---------------------------------------------------------------------------
static std::atomic<float> s_lastFov{-1.0f};
static std::atomic<float> s_lastCamMax{-1.0f};
static std::atomic<int>   s_lastMaxFps{-1};
static std::atomic<int>   s_lastTripleBuf{-1}; // -1 = unset, 0 = off, 1 = on

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

        // Direct member read (faster, avoids vtable call)
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
// CVar pointer cache — avoids repeated vtable string lookups per frame.
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
// ExecuteNativeCommand — used as the primary application path.
// Calling ExecuteString on CryConsole is the most reliable way to propagate
// a CVar change through all engine subsystems (including registered listeners).
// We do NOT also do the direct memory write + vtable call — that was the
// source of redundant processing. ExecuteString alone is sufficient when the
// CVar is not VF_READONLY; in that case the direct flag-strip + vtable path
// is used as the write path, followed by a single ExecuteString notification.
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
// SetNativeCVarFloat / SetNativeCVarInt
//
// Strategy: strip read-only flags, write directly to the value pointers,
// then call the vtable Set() so the engine's internal state is consistent,
// then fire OnChanged so all registered listeners receive the notification.
// We do NOT call ExecuteString in addition — that path was causing double
// application which manifested as engine stutters on rapid changes.
// ---------------------------------------------------------------------------
static bool SetNativeCVarFloat(uintptr_t pConsole, const char* name, float val) {
    if (!pConsole) return false;
    bool directSuccess = false;
    __try {
        uintptr_t pCVar = GetNativeCVarCached(pConsole, name);
        if (pCVar && !IsBadReadPtr(reinterpret_cast<void*>(pCVar), sizeof(void*))) {
            // Strip VF_READONLY (0x800), VF_CHEAT_NOCHECK (0x80000), VF_NET_SYNCED (0x02)
            uint32_t* pFlags = reinterpret_cast<uint32_t*>(pCVar + 0x98);
            if (!IsBadWritePtr(pFlags, sizeof(uint32_t))) {
                *pFlags &= ~(0x80800u | 0x800u | 0x02u);
            }

            // Direct value pointer write (offset 0xB0 = float*, 0xA8 = int*)
            uintptr_t pFloatPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xB0);
            if (pFloatPtr && !IsBadWritePtr(reinterpret_cast<void*>(pFloatPtr), sizeof(float))) {
                *reinterpret_cast<float*>(pFloatPtr) = val;
                directSuccess = true;
            }
            uintptr_t pIntPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xA8);
            if (pIntPtr && !IsBadWritePtr(reinterpret_cast<void*>(pIntPtr), sizeof(int))) {
                *reinterpret_cast<int*>(pIntPtr) = static_cast<int>(val);
            }

            // Vtable Set(float) + OnChanged notification
            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 16)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, float)>(pVtable[kVtableCVarSetFloat]);
                if (fnSet) fnSet(reinterpret_cast<void*>(pCVar), val);
                auto fnOnChanged = reinterpret_cast<void(__fastcall*)(void*, int)>(pVtable[kVtableCVarOnChanged]);
                if (fnOnChanged) fnOnChanged(reinterpret_cast<void*>(pCVar), 8);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
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

            uintptr_t pIntPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xA8);
            if (pIntPtr && !IsBadWritePtr(reinterpret_cast<void*>(pIntPtr), sizeof(int))) {
                *reinterpret_cast<int*>(pIntPtr) = val;
                directSuccess = true;
            }
            uintptr_t pFloatPtr = *reinterpret_cast<uintptr_t*>(pCVar + 0xB0);
            if (pFloatPtr && !IsBadWritePtr(reinterpret_cast<void*>(pFloatPtr), sizeof(float))) {
                *reinterpret_cast<float*>(pFloatPtr) = static_cast<float>(val);
            }

            uintptr_t* pVtable = *reinterpret_cast<uintptr_t**>(pCVar);
            if (pVtable && !IsBadReadPtr(pVtable, sizeof(void*) * 16)) {
                auto fnSet = reinterpret_cast<void(__fastcall*)(void*, int)>(pVtable[kVtableCVarSetInt]);
                if (fnSet) fnSet(reinterpret_cast<void*>(pCVar), val);
                auto fnOnChanged = reinterpret_cast<void(__fastcall*)(void*, int)>(pVtable[kVtableCVarOnChanged]);
                if (fnOnChanged) fnOnChanged(reinterpret_cast<void*>(pCVar), 8);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    return directSuccess;
}

// ---------------------------------------------------------------------------
// ApplyFov — apply all FOV-related CVars atomically.
// Only called when fov value has actually changed vs. last applied.
// ---------------------------------------------------------------------------
static void ApplyFov(uintptr_t pConsole, float fov) {
    SetNativeCVarFloat(pConsole, "delete_0721_g_minfov", fov);
    SetNativeCVarFloat(pConsole, "delete_0721_g_midFov", fov);
    SetNativeCVarFloat(pConsole, "delete_0721_g_maxFov", fov);
    SetNativeCVarFloat(pConsole, "fov",       fov);
    SetNativeCVarFloat(pConsole, "fov_angle", fov);
    SetNativeCVarFloat(pConsole, "g_minFov",  fov);
    SetNativeCVarFloat(pConsole, "g_maxFov",  fov);
    SetNativeCVarFloat(pConsole, "g_midFov",  fov);
}

// ---------------------------------------------------------------------------
// ApplyCamMax
// ---------------------------------------------------------------------------
static void ApplyCamMax(uintptr_t pConsole, float cam) {
    SetNativeCVarFloat(pConsole, "delete_0721_g_camMax", cam);
    SetNativeCVarFloat(pConsole, "g_camMax",         cam);
    SetNativeCVarFloat(pConsole, "cb_cam_max_dist",  cam);
    SetNativeCVarFloat(pConsole, "g_cam_p_max",      cam);
    SetNativeCVarFloat(pConsole, "cam_max_distance", cam);
}

// ---------------------------------------------------------------------------
// ApplyMaxFps
// ---------------------------------------------------------------------------
static void ApplyMaxFps(uintptr_t pConsole, int fps) {
    SetNativeCVarInt(pConsole, "delete_0721_g_maxfps", fps);
    SetNativeCVarInt(pConsole, "g_maxfps",      fps);
    SetNativeCVarInt(pConsole, "sys_fixedframe", 0);
}

// ---------------------------------------------------------------------------
// ApplyTripleBuffering
// ---------------------------------------------------------------------------
static void ApplyTripleBuffering(uintptr_t pConsole, bool enable) {
    SetNativeCVarInt(pConsole, "d3d9_TripleBuffering", enable ? 1 : 0);
}

// ---------------------------------------------------------------------------
// WorkerApplyAll
//
// Called from the background worker thread on wake. Uses change detection:
// only applies CVars whose current desired value differs from the last value
// successfully written to the engine. This ensures the worker is a true
// no-op in steady state (0% CPU overhead between changes).
//
// Engine performance CVars (r_EnvCMupdateInterval etc.) are applied once
// on the first successful engine contact, then never touched again.
// ---------------------------------------------------------------------------
static void WorkerApplyAll() {
    uintptr_t pConsole = GetNativeConsole();
    if (!pConsole) return;

    static bool s_loggedFound = false;
    if (!s_loggedFound) {
        s_loggedFound = true;
        LogInfo("CVarManager: Console CryEngine adquirido (0x%p). Modo change-detection ativado.", (void*)pConsole);

        // One-time engine performance tweaks — applied exactly once after console becomes available.
        ExecuteNativeCommand(pConsole, "r_EnvCMupdateInterval 0.1");
        ExecuteNativeCommand(pConsole, "r_EnvTexUpdateInterval 0.1");
        ExecuteNativeCommand(pConsole, "sys_fixedframe 0");
    }

    // FOV — only apply if changed since last apply
    if (g_featFov.load()) {
        float fov = std::clamp(g_cvarFov.load(), 60.0f, 120.0f);
        float lastFov = s_lastFov.load(std::memory_order_relaxed);
        if (fov != lastFov) {
            ApplyFov(pConsole, fov);
            s_lastFov.store(fov, std::memory_order_relaxed);
        }
    }

    // Camera Max — only apply if changed
    if (g_featCamMax.load()) {
        float cam = std::clamp(g_cvarCamMax.load(), 5.0f, 50.0f);
        float lastCam = s_lastCamMax.load(std::memory_order_relaxed);
        if (cam != lastCam) {
            ApplyCamMax(pConsole, cam);
            s_lastCamMax.store(cam, std::memory_order_relaxed);
        }
    }

    // FPS — only apply if changed
    if (g_featFpsUnlock.load()) {
        int fps = g_cvarMaxFps.load();
        int lastFps = s_lastMaxFps.load(std::memory_order_relaxed);
        if (fps != lastFps) {
            ApplyMaxFps(pConsole, fps);
            s_lastMaxFps.store(fps, std::memory_order_relaxed);
        }
    }

    // Triple Buffering — only apply if changed
    {
        int tb = g_cvarTripleBuffering.load() ? 1 : 0;
        int lastTb = s_lastTripleBuf.load(std::memory_order_relaxed);
        if (tb != lastTb) {
            ApplyTripleBuffering(pConsole, tb != 0);
            s_lastTripleBuf.store(tb, std::memory_order_relaxed);
        }
    }
}

// ---------------------------------------------------------------------------
// Worker thread proc
// Waits indefinitely on the wake event (0% CPU in idle).
// During initial engine startup, polls every 1500ms until CrySystem is ready.
// After first successful apply, switches to pure event-driven mode.
// ---------------------------------------------------------------------------
static DWORD WINAPI CVarWorkerThreadProc(LPVOID) {
    bool initialApplied = false;
    while (!InterlockedCompareExchange(&g_stopWorker, 0, 0)) {
        if (!initialApplied) {
            uintptr_t pConsole = GetNativeConsole();
            if (pConsole != 0) {
                // Reset shadow values so all CVars are applied fresh on first contact
                s_lastFov.store(-1.0f, std::memory_order_relaxed);
                s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
                s_lastMaxFps.store(-1, std::memory_order_relaxed);
                s_lastTripleBuf.store(-1, std::memory_order_relaxed);
                WorkerApplyAll();
                initialApplied = true;
                LogInfo("CVarManager: CVars aplicados. Modo event-driven ativo (0%% CPU em idle).");
            }
        } else {
            WorkerApplyAll();
        }

        // Wait for a change notification (INFINITE when initialized; 1500ms during startup polling)
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
        LogInfo("CVarManager: Worker thread iniciado. Aguardando CrySystem...");
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
    AcquireSRWLockExclusive(&s_cvarCacheLock);
    s_cvarCache.clear();
    s_cachedConsole = 0;
    ReleaseSRWLockExclusive(&s_cvarCacheLock);
}

// ---------------------------------------------------------------------------
// SetFov — Instant real-time update.
//
// Design:
//   1. Clamp and store the new desired value atomically.
//   2. Compare against last-applied value. If identical, do nothing (no-op
//      for rapid slider movement at the same quantized value).
//   3. Apply directly to engine on the calling thread (UI/message thread)
//      for zero-latency response.
//   4. Wake the background worker so it re-confirms the value on next cycle.
//
// This eliminates the original double-apply (direct write + ExecuteString
// in both SetFov AND WorkerApplyAll) that caused stuttering. The engine now
// receives each unique value exactly once.
// ---------------------------------------------------------------------------
void CVarManager::SetFov(float fov) {
    float clamped = std::clamp(fov, 60.0f, 120.0f);
    g_cvarFov.store(clamped, std::memory_order_relaxed);

    // Change detection: skip engine call if value is identical to last applied
    float last = s_lastFov.load(std::memory_order_relaxed);
    if (clamped == last) return;

    uintptr_t pConsole = GetNativeConsole();
    if (pConsole) {
        ApplyFov(pConsole, clamped);
        s_lastFov.store(clamped, std::memory_order_relaxed);
    }
    // Wake worker to re-sync on next cycle (handles deferred engine readiness)
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

    int desired = enable ? 1 : 0;
    int last = s_lastTripleBuf.load(std::memory_order_relaxed);
    if (desired == last) return;

    uintptr_t pConsole = GetNativeConsole();
    if (pConsole) {
        ApplyTripleBuffering(pConsole, enable);
        s_lastTripleBuf.store(desired, std::memory_order_relaxed);
    }
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ApplyAll() {
    // Force re-apply all values by resetting shadow cache
    s_lastFov.store(-1.0f, std::memory_order_relaxed);
    s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
    s_lastMaxFps.store(-1, std::memory_order_relaxed);
    s_lastTripleBuf.store(-1, std::memory_order_relaxed);
    WorkerApplyAll();
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ResyncOnMapChange() {
    // Force full re-apply after a map/zone change (engine may reset CVars)
    s_lastFov.store(-1.0f, std::memory_order_relaxed);
    s_lastCamMax.store(-1.0f, std::memory_order_relaxed);
    s_lastMaxFps.store(-1, std::memory_order_relaxed);
    s_lastTripleBuf.store(-1, std::memory_order_relaxed);
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

bool CVarManager::IsWorkerRunning() {
    return g_hWorkerThread != nullptr;
}

} // namespace BrService
