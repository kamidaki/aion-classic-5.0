#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include <stdint.h>
#include <string>
#include <algorithm>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  Version.dll - Mod & Compatibility Hook for Aion Classic
// =========================================================================
//  Features:
//  1. Graphics quality unlock (4096x4096 resolution support in CrySystem).
//  2. High core-count CPU affinity stability fix (32+ cores).
//  3. Window sizing / border adjustments for modern resolutions.
//  4. Official IP spoofing for private emulator connectivity.
//  5. Clean command line bypasses for official-only telemetry/shops.
//  6. Native L10N BRA (Portuguese-Brazil) language support injection.
// =========================================================================

static bool s_gfxEnabled = false;

static void BypassCountryCheckInModule(HMODULE hMod) {
    if (!hMod) return;

    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;

    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return;

    BYTE* base = (BYTE*)hMod;
    PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        if (!(sec->Characteristics & IMAGE_SCN_MEM_EXECUTE))
            continue;

        BYTE* s = base + sec->VirtualAddress;
        DWORD sz = sec->Misc.VirtualSize;
        if (sz < 32) continue;
        BYTE* s_end = s + sz - 20;

        for (BYTE* p = s; p <= s_end; p++) {
            // Match \x3b\xc1\x0f\x85 (cmp eax, ecx; jne ...)
            if (p[0] == 0x3B && p[1] == 0xC1 && p[2] == 0x0F && p[3] == 0x85) {
                // Check if \x83\xf8\x02 (cmp eax, 2) appears in previous 30 bytes
                BYTE* pre_start = (p - 30 >= s) ? (p - 30) : s;
                bool has_cmp = false;
                for (BYTE* q = pre_start; q < p; q++) {
                    if (q[0] == 0x83 && q[1] == 0xF8 && q[2] == 0x02) {
                        has_cmp = true;
                        break;
                    }
                }
                if (!has_cmp) continue;

                int32_t disp = *(int32_t*)(p + 4);
                BYTE* err_target = p + 8 + disp;
                if (err_target >= base && err_target < base + nt->OptionalHeader.SizeOfImage - 6) {
                    // Check if error block starts with 41 B9 10 (mov r9d, 0x10)
                    if (err_target[0] == 0x41 && err_target[1] == 0xB9 && err_target[2] == 0x10) {
                        DWORD oldProtect = 0;
                        // Patch 1: NOP the jne (6 bytes: 0x0F 0x85 [disp32])
                        if (VirtualProtect(p + 2, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                            memset(p + 2, 0x90, 6);
                            VirtualProtect(p + 2, 6, oldProtect, &oldProtect);
                        }

                        // Patch 2: Search within next 16 bytes for 0x0F 0x84 (je ...) and NOP it
                        for (int k = 8; k < 20 && (p + k + 6 <= s_end); k++) {
                            if (p[k] == 0x0F && p[k + 1] == 0x84) {
                                if (VirtualProtect(p + k, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                                    memset(p + k, 0x90, 6);
                                    VirtualProtect(p + k, 6, oldProtect, &oldProtect);
                                }
                                break;
                            }
                        }

                        // Patch 3: At err_target, patch with ret (0xC3) so it can never trigger exit
                        if (VirtualProtect(err_target, 1, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                            err_target[0] = 0xC3; // ret
                            VirtualProtect(err_target, 1, oldProtect, &oldProtect);
                        }
                    }
                }
            }
        }
    }
}

static void PatchLanguageTableInModule(HMODULE hMod) {
    if (!hMod) return;

    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;

    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return;

    const char pattern[] = "KOR\0ENU\0ENG\0DEU\0FRA\0ITA\0ESN\0PLK\0";
    const size_t patternLen = 32;

    BYTE* base = (BYTE*)hMod;
    PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        if (!(sec->Characteristics & (IMAGE_SCN_MEM_READ | IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_CNT_CODE)))
            continue;

        BYTE* s = base + sec->VirtualAddress;
        DWORD sz = sec->Misc.VirtualSize;
        if (sz < 8) continue;
        BYTE* s_end = s + sz - 8;

        for (BYTE* p = s; p <= s_end; p++) {
            // Check primary 32-byte pattern (Aion.bin, CrySystem, CryFont, CrySoundSystem, XRenderD3D9)
            if (p + patternLen <= base + sec->VirtualAddress + sz && p[0] == 'K' && memcmp(p, pattern, patternLen) == 0) {
                BYTE* plk = p + 28;
                DWORD oldProtect = 0;
                if (VirtualProtect(plk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(plk, "BRA\0", 4);
                    VirtualProtect(plk, 4, oldProtect, &oldProtect);
                }
            }
            // Check Game.dll pattern: PLK\0ESN\0 or PLK\0TRK\0
            else if (memcmp(p, "PLK\0ESN\0", 8) == 0 || memcmp(p, "PLK\0TRK\0", 8) == 0) {
                DWORD oldProtect = 0;
                if (VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(p, "BRA\0", 4);
                    VirtualProtect(p, 4, oldProtect, &oldProtect);
                }
            }
            // Check CryMovie.dll pattern: ITA\0PLK\0 or ESN\0PLK\0
            else if (memcmp(p, "ITA\0PLK\0", 8) == 0 || memcmp(p, "ESN\0PLK\0", 8) == 0) {
                DWORD oldProtect = 0;
                if (VirtualProtect(p + 4, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(p + 4, "BRA\0", 4);
                    VirtualProtect(p + 4, 4, oldProtect, &oldProtect);
                }
            }
        }
    }
}

static void PatchAllLoadedLanguageModules() {
    HMODULE mods[] = {
        GetModuleHandleW(nullptr),
        GetModuleHandleW(L"crysystem.dll"),
        GetModuleHandleW(L"cryfont.dll"),
        GetModuleHandleW(L"crymovie.dll"),
        GetModuleHandleW(L"crysoundsystem.dll"),
        GetModuleHandleW(L"game.dll"),
        GetModuleHandleW(L"xrenderd3d9.dll")
    };
    for (HMODULE h : mods) {
        if (h) {
            PatchLanguageTableInModule(h);
            BypassCountryCheckInModule(h);
        }
    }
}

static decltype(LoadLibraryA)* real_LoadLibraryA = LoadLibraryA;
static HMODULE WINAPI zzLoadLibraryA(LPCSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryA(lpLibFileName);
    if (h) {
        PatchLanguageTableInModule(h);
        BypassCountryCheckInModule(h);
    }
    return h;
}

static decltype(LoadLibraryExA)* real_LoadLibraryExA = LoadLibraryExA;
static HMODULE WINAPI zzLoadLibraryExA(LPCSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExA(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchLanguageTableInModule(h);
        BypassCountryCheckInModule(h);
    }
    return h;
}

static decltype(LoadLibraryW)* real_LoadLibraryW = LoadLibraryW;
static HMODULE WINAPI zzLoadLibraryW(LPCWSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryW(lpLibFileName);
    if (h) {
        PatchLanguageTableInModule(h);
        BypassCountryCheckInModule(h);
    }
    return h;
}

static decltype(LoadLibraryExW)* real_LoadLibraryExW = LoadLibraryExW;
static HMODULE WINAPI zzLoadLibraryExW(LPCWSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExW(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchLanguageTableInModule(h);
        BypassCountryCheckInModule(h);
    }
    return h;
}

static decltype(MessageBoxA)* real_MessageBoxA = MessageBoxA;
static int WINAPI zzMessageBoxA(HWND hWnd, LPCSTR lpText, LPCSTR lpCaption, UINT uType) {
    if (lpText && strstr(lpText, "unavailable in your country")) {
        return IDOK;
    }
    return real_MessageBoxA(hWnd, lpText, lpCaption, uType);
}

static decltype(MessageBoxW)* real_MessageBoxW = MessageBoxW;
static int WINAPI zzMessageBoxW(HWND hWnd, LPCWSTR lpText, LPCWSTR lpCaption, UINT uType) {
    if (lpText && wcsstr(lpText, L"unavailable in your country")) {
        return IDOK;
    }
    return real_MessageBoxW(hWnd, lpText, lpCaption, uType);
}

static void EnableHighQualityGraphicsOptions() {
    HMODULE hCry = GetModuleHandleW(L"crysystem");
    if (!hCry) return;

    MEMORY_BASIC_INFORMATION mbi = {};
    if (!VirtualQuery((char*)hCry + 0x1000, &mbi, sizeof(mbi))) return;
    if (!(mbi.AllocationProtect & 0xF0)) return;

    DWORD oldProtect;
    if (!VirtualProtect(mbi.BaseAddress, mbi.RegionSize, PAGE_EXECUTE_READWRITE, &oldProtect)) return;

    char* c = (char*)mbi.BaseAddress;
    char* end = c + mbi.RegionSize - sizeof(DWORD);

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
            break;
        }
    }

    VirtualProtect(mbi.BaseAddress, mbi.RegionSize, oldProtect, &oldProtect);
}

void InstallIpFix();
void InstallShaderFix();
void Install64BitStackFix();

// =========================================================================
// Command Line Injection Hook
// Automatically appends official bypass arguments to ensure clean startup.
// =========================================================================
static decltype(GetCommandLineA)* real_GetCommandLineA = GetCommandLineA;
static LPSTR WINAPI zzGetCommandLineA() {
    static std::string s_hookedCmdA;
    if (s_hookedCmdA.empty()) {
        LPSTR cmd = real_GetCommandLineA();
        s_hookedCmdA = cmd ? cmd : "";
        if (s_hookedCmdA.find("-classic") == std::string::npos) {
            s_hookedCmdA += " -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu -dwsm -probability -nospamcheck";
        }
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
            s_hookedCmdW += L" -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu -dwsm -probability -nospamcheck";
        }
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
            }
        }
    }
    return real_SetWindowPos(hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags);
}

static decltype(SetWindowLongA)* real_SetWindowLongA = SetWindowLongA;
static LONG WINAPI zzSetWindowLongA(_In_ HWND hWnd, _In_ int nIndex, _In_ LONG dwNewLong) {
    if (!s_gfxEnabled) {
        EnableHighQualityGraphicsOptions();
        PatchAllLoadedLanguageModules();
        s_gfxEnabled = true;
    }
    return real_SetWindowLongA(hWnd, nIndex, dwNewLong);
}

static void FixClientStartupWithHighCoreCountCpus() {
    SYSTEM_INFO info;
    GetSystemInfo(&info);
    if (info.dwNumberOfProcessors >= 32) {
        int maxCpu = min(64, (int)info.dwNumberOfProcessors) - 1;
        DWORD_PTR mask = (1ULL << maxCpu) - 1;
        SetProcessAffinityMask(GetCurrentProcess(), mask);
    }
}

static void InstallPatch() {
    SetProcessDPIAware();

    PatchLanguageTableInModule(GetModuleHandleW(nullptr));
    BypassCountryCheckInModule(GetModuleHandleW(nullptr));

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    InstallIpFix();
    InstallShaderFix();
#if defined(_M_AMD64)
    Install64BitStackFix();
#endif
    DetourAttach(&(PVOID&)real_SetWindowLongA, zzSetWindowLongA);
    DetourAttach(&(PVOID&)real_LoadLibraryA, zzLoadLibraryA);
    DetourAttach(&(PVOID&)real_LoadLibraryExA, zzLoadLibraryExA);
    DetourAttach(&(PVOID&)real_LoadLibraryW, zzLoadLibraryW);
    DetourAttach(&(PVOID&)real_LoadLibraryExW, zzLoadLibraryExW);
    DetourAttach(&(PVOID&)real_MessageBoxA, zzMessageBoxA);
    DetourAttach(&(PVOID&)real_MessageBoxW, zzMessageBoxW);
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
        InstallPatch();
    }
    return TRUE;
}
