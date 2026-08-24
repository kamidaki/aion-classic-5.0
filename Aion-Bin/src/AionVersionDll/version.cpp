#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>
#include <string>
#include <algorithm>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  Version.dll - Production Mod & Telemetry Hook for Aion Classic
// =========================================================================

static bool s_gfxEnabled = false;

void VersionLog(const char* fmt, ...) {
    static CRITICAL_SECTION s_cs;
    static bool s_csInit = false;
    if (!s_csInit) {
        InitializeCriticalSection(&s_cs);
        s_csInit = true;
    }
    EnterCriticalSection(&s_cs);
    FILE* f = nullptr;
    fopen_s(&f, "version_hook.log", "a");
    if (f) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(f, "[%04d-%02d-%02d %02d:%02d:%02d.%03d] [version.dll] ",
            st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
        va_list args;
        va_start(args, fmt);
        vfprintf(f, fmt, args);
        va_end(args);
        fprintf(f, "\n");
        fflush(f);
        fclose(f);
    }
    LeaveCriticalSection(&s_cs);
}

static void EnableHighQualityGraphicsOptions() {
    HMODULE hCry = GetModuleHandleW(L"crysystem");
    if (!hCry) {
        VersionLog("[GRAPHICS] crysystem module not found/loaded yet.");
        return;
    }

    MEMORY_BASIC_INFORMATION mbi = {};
    if (!VirtualQuery((char*)hCry + 0x1000, &mbi, sizeof(mbi))) {
        VersionLog("[GRAPHICS] VirtualQuery on crysystem failed.");
        return;
    }

    if (!(mbi.AllocationProtect & 0xF0)) {
        VersionLog("[GRAPHICS] crysystem memory is not executable.");
        return;
    }

    DWORD oldProtect;
    if (!VirtualProtect(mbi.BaseAddress, mbi.RegionSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        VersionLog("[GRAPHICS] VirtualProtect on crysystem failed.");
        return;
    }

    char* c = (char*)mbi.BaseAddress;
    char* end = c + mbi.RegionSize - sizeof(DWORD);
    bool patched = false;

    for (; c < end; c++) {
        DWORD* d = (DWORD*)c;
        if (*d == 1920 * 1200) {
            *d = 4096 * 4096;
            char* e = c - 0x100;
            char* e_end = c + 0x100;
            e_end = min(end, e_end);
            for (; e < e_end; e++) {
                DWORD* d2 = (DWORD*)e;
                if (*d2 == 2560 * 1600) {
                    *d2 = 4096 * 4096;
                    break;
                }
            }
            patched = true;
            break;
        }
    }

    VirtualProtect(mbi.BaseAddress, mbi.RegionSize, oldProtect, &oldProtect);
    VersionLog("[GRAPHICS] High quality graphics resolution limits unlocked to 4096x4096: %s",
        patched ? "SUCCESS" : "ALREADY_APPLIED/NOT_FOUND");
}

void InstallOrUpdateCameraFix(HWND hWnd);
void InstallIpFix();
void InstallShaderFix();
void Install64BitStackFix();

// Hook functions for command line injection and resolution border adjustments
static decltype(GetCommandLineA)* real_GetCommandLineA = GetCommandLineA;
static LPSTR WINAPI zzGetCommandLineA() {
    static std::string s_hookedCmdA;
    if (s_hookedCmdA.empty()) {
        LPSTR cmd = real_GetCommandLineA();
        s_hookedCmdA = cmd ? cmd : "";
        if (s_hookedCmdA.find("-classic") == std::string::npos) {
            s_hookedCmdA += " -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu";
        }
        VersionLog("[CMDLINE] Hooked GetCommandLineA: %s", s_hookedCmdA.c_str());
    }
    return const_cast<LPSTR>(s_hookedCmdA.c_str());
}

static decltype(GetCommandLineW)* real_GetCommandLineW = GetCommandLineW;
static LPWSTR WINAPI zzGetCommandLineW() {
    static std::wstring s_hookedCmdW;
    if (s_hookedCmdW.empty()) {
        LPWSTR cmd = real_GetCommandLineW();
        s_hookedCmdW = cmd ? cmd : L"";
        if (s_hookedCmdW.find(L"-classic") == std::wstring::npos) {
            s_hookedCmdW += L" -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu";
        }
        VersionLog("[CMDLINE] Hooked GetCommandLineW: %ls", s_hookedCmdW.c_str());
    }
    return const_cast<LPWSTR>(s_hookedCmdW.c_str());
}

static decltype(CreateWindowExA)* real_CreateWindowExA = CreateWindowExA;
static HWND WINAPI zzCreateWindowExA(DWORD dwExStyle, LPCSTR lpClassName, LPCSTR lpWindowName, DWORD dwStyle, int X, int Y, int nWidth, int nHeight, HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, LPVOID lpParam) {
    if (lpClassName && ((ULONG_PTR)lpClassName > 0xFFFF) && (strcmp(lpClassName, "AION") == 0 || strcmp(lpClassName, "CryGame") == 0)) {
        if ((dwStyle & WS_CAPTION) && !(dwStyle & WS_MAXIMIZE) && !(dwStyle & WS_MINIMIZE)) {
            RECT rect = {0, 0, nWidth, nHeight};
            AdjustWindowRectEx(&rect, dwStyle, FALSE, dwExStyle);
            nWidth = rect.right - rect.left;
            nHeight = rect.bottom - rect.top;
            VersionLog("[GRAPHICS] CreateWindowExA adjusted window size to %dx%d", nWidth, nHeight);
        }
    }
    return real_CreateWindowExA(dwExStyle, lpClassName, lpWindowName, dwStyle, X, Y, nWidth, nHeight, hWndParent, hMenu, hInstance, lpParam);
}

static decltype(CreateWindowExW)* real_CreateWindowExW = CreateWindowExW;
static HWND WINAPI zzCreateWindowExW(DWORD dwExStyle, LPCWSTR lpClassName, LPCWSTR lpWindowName, DWORD dwStyle, int X, int Y, int nWidth, int nHeight, HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, LPVOID lpParam) {
    if (lpClassName && ((ULONG_PTR)lpClassName > 0xFFFF) && (wcscmp(lpClassName, L"AION") == 0 || wcscmp(lpClassName, L"CryGame") == 0)) {
        if ((dwStyle & WS_CAPTION) && !(dwStyle & WS_MAXIMIZE) && !(dwStyle & WS_MINIMIZE)) {
            RECT rect = {0, 0, nWidth, nHeight};
            AdjustWindowRectEx(&rect, dwStyle, FALSE, dwExStyle);
            nWidth = rect.right - rect.left;
            nHeight = rect.bottom - rect.top;
            VersionLog("[GRAPHICS] CreateWindowExW adjusted window size to %dx%d", nWidth, nHeight);
        }
    }
    return real_CreateWindowExW(dwExStyle, lpClassName, lpWindowName, dwStyle, X, Y, nWidth, nHeight, hWndParent, hMenu, hInstance, lpParam);
}

static decltype(SetWindowPos)* real_SetWindowPos = SetWindowPos;
static BOOL WINAPI zzSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags) {
    char className[256];
    if (!(uFlags & SWP_NOSIZE) && GetClassNameA(hWnd, className, sizeof(className)) && 
        (strcmp(className, "AION") == 0 || strcmp(className, "CryGame") == 0)) {
        
        DWORD style = GetWindowLongA(hWnd, GWL_STYLE);
        if ((style & WS_CAPTION) && !(style & WS_MAXIMIZE) && !(style & WS_MINIMIZE)) {
            if ((cx == 1024 && cy == 768) || (cx == 1280 && (cy == 720 || cy == 800 || cy == 1024)) ||
                (cx == 1366 && cy == 768) || (cx == 1440 && cy == 900) || (cx == 1600 && (cy == 900 || cy == 1200)) ||
                (cx == 1680 && cy == 1050) || (cx == 1920 && (cy == 1080 || cy == 1200)) ||
                (cx == 2560 && (cy == 1080 || cy == 1440 || cy == 1600)) || (cx == 3440 && cy == 1440) ||
                (cx == 3840 && cy == 2160)) {
                
                RECT rect = {0, 0, cx, cy};
                DWORD exStyle = GetWindowLongA(hWnd, GWL_EXSTYLE);
                AdjustWindowRectEx(&rect, style, FALSE, exStyle);
                cx = rect.right - rect.left;
                cy = rect.bottom - rect.top;
                VersionLog("[GRAPHICS] SetWindowPos adjusted window size to %dx%d (client: %dx%d)", cx, cy, rect.right, rect.bottom);
            }
        }
    }
    return real_SetWindowPos(hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags);
}

static decltype(SetWindowLongA)* real_SetWindowLongA = SetWindowLongA;
static LONG WINAPI zzSetWindowLongA(_In_ HWND hWnd, _In_ int nIndex, _In_ LONG dwNewLong) {
    if (!s_gfxEnabled) {
        EnableHighQualityGraphicsOptions();
        s_gfxEnabled = true;
    }
    InstallOrUpdateCameraFix(hWnd);
    return real_SetWindowLongA(hWnd, nIndex, dwNewLong);
}

static void PreloadDXVK() {
    VersionLog("[VULKAN/DXVK] Preloading Direct3D9 translation layer (d3d9.dll)...");
    HMODULE hD3D9 = LoadLibraryW(L"d3d9.dll");
    if (hD3D9) {
        VersionLog("[VULKAN/DXVK] d3d9.dll loaded successfully at base %p", hD3D9);
        typedef const char* (*PFN_dxvkGetVersion)();
        PFN_dxvkGetVersion pfnDxvkVer = (PFN_dxvkGetVersion)GetProcAddress(hD3D9, "dxvkGetVersion");
        if (pfnDxvkVer) {
            VersionLog("[VULKAN/DXVK] DXVK Translation Layer Version: %s", pfnDxvkVer());
        } else {
            VersionLog("[VULKAN/DXVK] Direct3D9 (DXVK/Native) translation active at %p", hD3D9);
        }
    } else {
        DWORD err = GetLastError();
        VersionLog("[VULKAN/DXVK] d3d9.dll not found in local path (Error %u) - falling back to system DirectX", err);
    }

    // Inspect Vulkan Runtime
    HMODULE hVk = LoadLibraryW(L"vulkan-1.dll");
    if (hVk) {
        typedef uint32_t (*PFN_vkEnumerateInstanceVersion)(uint32_t* pApiVersion);
        PFN_vkEnumerateInstanceVersion pfnEnumVer = 
            (PFN_vkEnumerateInstanceVersion)GetProcAddress(hVk, "vkEnumerateInstanceVersion");
        if (pfnEnumVer) {
            uint32_t apiVer = 0;
            if (pfnEnumVer(&apiVer) == 0) {
                uint32_t major = (apiVer >> 22);
                uint32_t minor = (apiVer >> 12) & 0x3FF;
                uint32_t patch = apiVer & 0xFFF;
                VersionLog("[VULKAN] Vulkan Runtime detected: vulkan-1.dll at %p, Vulkan API Version %u.%u.%u",
                    hVk, major, minor, patch);
            } else {
                VersionLog("[VULKAN] Vulkan Runtime detected: vulkan-1.dll at %p", hVk);
            }
        } else {
            VersionLog("[VULKAN] Vulkan Runtime detected (Vulkan 1.0) at %p", hVk);
        }
    } else {
        VersionLog("[VULKAN] vulkan-1.dll not present in system search path.");
    }
}

static void InstallGraphicsOptionsFixAndCameraFix() {
    DetourAttach(&(PVOID&)real_SetWindowLongA, zzSetWindowLongA);
    VersionLog("[INIT] Graphics Options & Camera Fix attached.");
}

static void FixClientStartupWithHighCoreCountCpus() {
    SYSTEM_INFO info;
    GetSystemInfo(&info);
    VersionLog("[CPU] System detected %u logical processor cores.", info.dwNumberOfProcessors);
    if (info.dwNumberOfProcessors >= 32) {
        int maxCpu = min(64, (int)info.dwNumberOfProcessors) - 1;
        DWORD_PTR mask = (1ULL << maxCpu) - 1;
        SetProcessAffinityMask(GetCurrentProcess(), mask);
        VersionLog("[CPU] Process affinity set to %d cores (Mask: 0x%llX) for CryEngine stability.",
            maxCpu, (unsigned long long)mask);
    }
}

static void InstallPatch() {
    SetProcessDPIAware();
    PreloadDXVK();

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    InstallIpFix();
    InstallGraphicsOptionsFixAndCameraFix();
    InstallShaderFix();
#if defined(_M_AMD64)
    Install64BitStackFix();
    VersionLog("[INIT] 64-bit Stack Fix installed.");
#endif
    DetourAttach(&(PVOID&)real_GetCommandLineA, zzGetCommandLineA);
    DetourAttach(&(PVOID&)real_GetCommandLineW, zzGetCommandLineW);
    DetourAttach(&(PVOID&)real_CreateWindowExA, zzCreateWindowExA);
    DetourAttach(&(PVOID&)real_CreateWindowExW, zzCreateWindowExW);
    DetourAttach(&(PVOID&)real_SetWindowPos, zzSetWindowPos);
    DetourTransactionCommit();

    FixClientStartupWithHighCoreCountCpus();
}

BOOL WINAPI DllMain(_In_ HINSTANCE hinstDLL, _In_ DWORD fdwReason, _In_ LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);

        wchar_t exePath[MAX_PATH] = {0};
        GetModuleFileNameW(nullptr, exePath, MAX_PATH);
        LPCWSTR cmdLine = GetCommandLineW();

        VersionLog("================================================================================");
        VersionLog("[STARTUP] version.dll attached to Process PID=%u", GetCurrentProcessId());
        VersionLog("[STARTUP] Executable: %ls", exePath);
        VersionLog("[STARTUP] Command Line: %ls", cmdLine ? cmdLine : L"(none)");
        VersionLog("================================================================================");

        InstallPatch();
    } else if (fdwReason == DLL_PROCESS_DETACH) {
        VersionLog("[SHUTDOWN] version.dll detached from Process PID=%u", GetCurrentProcessId());
    }
    return TRUE;
}
