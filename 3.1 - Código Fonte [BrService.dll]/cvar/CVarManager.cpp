#include "CVarManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <atomic>

namespace BrService {

// 64-bit CryEngine CVar layout offsets
static constexpr size_t kCVarNameOffset   = 8;
static constexpr size_t kCVarIntOffset    = 184;
static constexpr size_t kCVarFloatOffset  = 188;
static constexpr size_t kCVarStringOffset = 192;
static constexpr uintptr_t kVirtualMemoryMax = 0x7fffffff0000ull;

// Worker state
static HANDLE g_hWorkerThread = nullptr;
static HANDLE g_hWakeEvent = nullptr;
static volatile LONG g_stopWorker = 0;
static CRITICAL_SECTION g_cvarLock;
static bool g_csInitialized = false;

// Cached CVar memory addresses
static BYTE* g_pCvarFov    = nullptr;
static BYTE* g_pCvarCam    = nullptr;
static BYTE* g_pCvarFps    = nullptr;
static BYTE* g_pCvarTriple = nullptr;
static BYTE* g_pCvarAniso  = nullptr;
static BYTE* g_pCvarFreeFly= nullptr;

static DWORD g_lastScanFov    = 0;
static DWORD g_lastScanCam    = 0;
static DWORD g_lastScanFps    = 0;
static DWORD g_lastScanTriple = 0;
static DWORD g_lastScanAniso  = 0;
static DWORD g_lastScanFreeFly= 0;

static bool IsGameReady() {
    return GetModuleHandleA("game.dll") != nullptr &&
           GetModuleHandleA("crysystem.dll") != nullptr &&
           GetModuleHandleA("XRenderD3D9.dll") != nullptr;
}

static bool CvarNameMatches(const char* name, BYTE* p) {
    if (!name || !p) return false;
    const size_t len = strlen(name);
    __try {
        const BYTE flag = p[kCVarNameOffset];
        if (flag != 0 && flag != 1) return false;
        if (memcmp(p + kCVarNameOffset + 1, name, len) != 0) return false;
        return p[kCVarNameOffset + 1 + len] == '\0';
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static BYTE* ScanCVarAddress(const char* name) {
    BYTE* address = nullptr;
    MEMORY_BASIC_INFORMATION mbi = {};
    const size_t len = strlen(name);

    while (VirtualQuery(address, &mbi, sizeof(mbi)) == sizeof(mbi)) {
        if (reinterpret_cast<uintptr_t>(address) >= kVirtualMemoryMax) {
            break;
        }

        BYTE* base = static_cast<BYTE*>(mbi.BaseAddress);
        const SIZE_T size = mbi.RegionSize;

        if (mbi.State == MEM_COMMIT &&
            mbi.Type == MEM_PRIVATE &&
            mbi.Protect == PAGE_READWRITE &&
            size > (kCVarNameOffset + len + 1)) {

            BYTE* end = base + size - (kCVarNameOffset + len + 1);
            __try {
                for (BYTE* p = base; p < end; p += 16) {
                    const BYTE flag = p[kCVarNameOffset];
                    if (flag == 0 || flag == 1) {
                        if (memcmp(p + kCVarNameOffset + 1, name, len) == 0 &&
                            p[kCVarNameOffset + 1 + len] == '\0') {
                            return p;
                        }
                    }
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {
            }
        }

        BYTE* next = base + size;
        if (next <= address) break;
        address = next;
    }
    return nullptr;
}

static bool ApplyIntFloat(BYTE* base, int iVal, float fVal) {
    if (!base) return false;
    char txt[64] = {};
    if (fVal == static_cast<float>(iVal)) {
        snprintf(txt, sizeof(txt), "%d", iVal);
    } else {
        snprintf(txt, sizeof(txt), "%.3f", static_cast<double>(fVal));
    }
    __try {
        *reinterpret_cast<int*>(base + kCVarIntOffset) = iVal;
        *reinterpret_cast<float*>(base + kCVarFloatOffset) = fVal;
        strcpy_s(reinterpret_cast<char*>(base + kCVarStringOffset), 64, txt);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static void WorkerApplyAll() {
    if (!IsGameReady()) return;

    DWORD now = GetTickCount();

    // 1. Panoramic FOV (g_minFov)
    if (g_featFov.load()) {
        float fov = std::clamp(g_cvarFov.load(), 60.0f, 120.0f);
        BYTE* p = g_pCvarFov;
        if (!p || !CvarNameMatches("g_minFov", p)) {
            if (now - g_lastScanFov > 8000) {
                g_lastScanFov = now;
                g_pCvarFov = ScanCVarAddress("g_minFov");
                p = g_pCvarFov;
                if (p) LogInfo("CVar g_minFov localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                float cur = *reinterpret_cast<float*>(p + kCVarFloatOffset);
                if (cur != fov) {
                    ApplyIntFloat(p, static_cast<int>(fov), fov);
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }

    // 2. Camera Max Zoom (g_camMax)
    if (g_featCamMax.load()) {
        float cam = std::clamp(g_cvarCamMax.load(), 5.0f, 45.0f);
        BYTE* p = g_pCvarCam;
        if (!p || !CvarNameMatches("g_camMax", p)) {
            if (now - g_lastScanCam > 8000) {
                g_lastScanCam = now;
                g_pCvarCam = ScanCVarAddress("g_camMax");
                p = g_pCvarCam;
                if (p) LogInfo("CVar g_camMax localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                float cur = *reinterpret_cast<float*>(p + kCVarFloatOffset);
                if (cur != cam) {
                    ApplyIntFloat(p, static_cast<int>(cam), cam);
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }

    // 3. Framerate Cap (g_maxfps)
    if (g_featFpsUnlock.load()) {
        int fps = g_cvarMaxFps.load();
        BYTE* p = g_pCvarFps;
        if (!p || !CvarNameMatches("g_maxfps", p)) {
            if (now - g_lastScanFps > 8000) {
                g_lastScanFps = now;
                g_pCvarFps = ScanCVarAddress("g_maxfps");
                p = g_pCvarFps;
                if (p) LogInfo("CVar g_maxfps localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                int cur = *reinterpret_cast<int*>(p + kCVarIntOffset);
                if (cur != fps) {
                    ApplyIntFloat(p, fps, static_cast<float>(fps));
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }

    // 4. Triple Buffering (d3d9_TripleBuffering)
    {
        int tb = g_cvarTripleBuffering.load() ? 1 : 0;
        BYTE* p = g_pCvarTriple;
        if (!p || !CvarNameMatches("d3d9_TripleBuffering", p)) {
            if (now - g_lastScanTriple > 8000) {
                g_lastScanTriple = now;
                g_pCvarTriple = ScanCVarAddress("d3d9_TripleBuffering");
                p = g_pCvarTriple;
                if (p) LogInfo("CVar d3d9_TripleBuffering localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                int cur = *reinterpret_cast<int*>(p + kCVarIntOffset);
                if (cur != tb) {
                    ApplyIntFloat(p, tb, static_cast<float>(tb));
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }

    // 5. Anisotropic Filtering (r_Texture_Anisotropic_Level)
    {
        int aniso = g_cvarAnisotropic.load() ? 16 : 0;
        BYTE* p = g_pCvarAniso;
        if (!p || !CvarNameMatches("r_Texture_Anisotropic_Level", p)) {
            if (now - g_lastScanAniso > 8000) {
                g_lastScanAniso = now;
                g_pCvarAniso = ScanCVarAddress("r_Texture_Anisotropic_Level");
                p = g_pCvarAniso;
                if (p) LogInfo("CVar r_Texture_Anisotropic_Level localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                int cur = *reinterpret_cast<int*>(p + kCVarIntOffset);
                if (cur != aniso) {
                    ApplyIntFloat(p, aniso, static_cast<float>(aniso));
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }

    // 6. Free Fly (g_freefly)
    {
        int ff = g_featFreeFly.load() ? 1 : 0;
        BYTE* p = g_pCvarFreeFly;
        if (!p || !CvarNameMatches("g_freefly", p)) {
            if (now - g_lastScanFreeFly > 8000) {
                g_lastScanFreeFly = now;
                g_pCvarFreeFly = ScanCVarAddress("g_freefly");
                p = g_pCvarFreeFly;
                if (p) LogInfo("CVar g_freefly localizado em: %p", p);
            } else {
                p = nullptr;
            }
        }
        if (p) {
            __try {
                int cur = *reinterpret_cast<int*>(p + kCVarIntOffset);
                if (cur != ff) {
                    ApplyIntFloat(p, ff, static_cast<float>(ff));
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) {}
        }
    }
}

static DWORD WINAPI CVarWorkerThreadProc(LPVOID) {
    const DWORD intervalMs = 1500;
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
        LogInfo("CVarManager worker thread iniciada.");
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
    g_cvarFov = fov;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetCameraMax(float maxDist) {
    g_cvarCamMax = maxDist;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetMaxFps(int fps) {
    g_cvarMaxFps = fps;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetTripleBuffering(bool enable) {
    g_cvarTripleBuffering = enable;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetAnisotropic(bool enable) {
    g_cvarAnisotropic = enable;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::SetFreeFly(bool enable) {
    g_featFreeFly = enable;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ApplyAll() {
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

void CVarManager::ResyncOnMapChange() {
    g_lastScanFov = g_lastScanCam = g_lastScanFps = g_lastScanTriple = g_lastScanAniso = g_lastScanFreeFly = 0;
    if (g_hWakeEvent) SetEvent(g_hWakeEvent);
}

bool CVarManager::IsWorkerRunning() {
    return g_hWorkerThread != nullptr;
}

} // namespace BrService
