#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <algorithm>
#include <unordered_set>
#include <mutex>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  Version.dll - Mod & Compatibility Hook for Aion Classic 5.0
// =========================================================================
//  Features:
//  1. Graphics quality unlock (4096x4096 resolution support in CrySystem).
//  2. High core-count CPU affinity stability fix (32+ cores).
//  3. Official IP spoofing for private emulator connectivity.
//  4. Official mandatory command line injection for telemetry/shops bypass.
//  5. Native L10N BRA (Portuguese-Brazil) language support injection.
//  6. CryEngine country check bypass.
//  7. 64-bit VEH and stack alignment fix for Windows 10/11 Themida (x64).
//  * Note: Vulkan/DXVK and MouseFix are explicitly excluded for production.
// =========================================================================

static bool s_gfxEnabled = false;
static std::unordered_set<HMODULE> s_scannedLangModules;
static std::unordered_set<HMODULE> s_scannedCountryModules;
static SRWLOCK s_patchLock = SRWLOCK_INIT;

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
#if defined(_M_AMD64)
void Install64BitStackFix();
#endif

// =========================================================================
// Dynamic Language & Region Injection (Lost Academy canonical pattern)
// =========================================================================

static void PatchLanguageTableInModule(HMODULE hMod) {
    if (!hMod) return;

    AcquireSRWLockExclusive(&s_patchLock);
    if (s_scannedLangModules.find(hMod) != s_scannedLangModules.end()) {
        ReleaseSRWLockExclusive(&s_patchLock);
        return;
    }
    s_scannedLangModules.insert(hMod);
    ReleaseSRWLockExclusive(&s_patchLock);

    __try {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;
        if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x10000000) return;

        PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return;

        const char p1_prefix[] = "KOR\0ENU\0ENG\0DEU\0FRA\0ITA\0ESN\0"; // 28 bytes
        const char p2_suffix[] = "ESN\0ITA\0FRA\0DEU\0ENG\0ENU\0KOR\0"; // 28 bytes
        const char p_movie[]   = "KOR\0TRK\0PLK\0ITA\0ESN\0FRA\0DEU\0ENU\0"; // 32 bytes
        const size_t patternLen = 32;

        BYTE* base = (BYTE*)hMod;
        PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
        for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
            if (!(sec->Characteristics & (IMAGE_SCN_MEM_READ | IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_CNT_CODE)))
                continue;

            BYTE* s = base + sec->VirtualAddress;
            DWORD sz = sec->Misc.VirtualSize;
            if (sz < patternLen) continue;
            BYTE* s_end = s + sz - patternLen;

            for (BYTE* p = s; p <= s_end; p++) {
                // Check Classic pattern: PLK\0 + ESN\0ITA\0FRA\0DEU\0ENG\0ENU\0KOR\0
                if (p[0] == 'P' && memcmp(p, "PLK\0", 4) == 0 && memcmp(p + 4, p2_suffix, 28) == 0) {
                    DWORD oldProtect = 0;
                    if (VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(p, "BRA\0", 4);
                        VirtualProtect(p, 4, oldProtect, &oldProtect);
                    }
                    p += 31;
                    continue;
                }
                // Check 5.0+ pattern: KOR\0ENU\0ENG\0DEU\0FRA\0ITA\0ESN\0 + PLK\0
                if (p[0] == 'K' && memcmp(p, p1_prefix, 28) == 0 && memcmp(p + 28, "PLK\0", 4) == 0) {
                    BYTE* plk = p + 28;
                    DWORD oldProtect = 0;
                    if (VirtualProtect(plk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(plk, "BRA\0", 4);
                        VirtualProtect(plk, 4, oldProtect, &oldProtect);
                    }
                    p += 31;
                    continue;
                }
                // Check CryMovie pattern: KOR\0TRK\0PLK\0ITA\0ESN\0FRA\0DEU\0ENU\0
                if (p[0] == 'K' && memcmp(p, p_movie, 32) == 0) {
                    BYTE* plk = p + 8;
                    DWORD oldProtect = 0;
                    if (VirtualProtect(plk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(plk, "BRA\0", 4);
                        VirtualProtect(plk, 4, oldProtect, &oldProtect);
                    }
                    p += 31;
                    continue;
                }
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

static void BypassCountryCheckInCryEngineModule(HMODULE hMod) {
    if (!hMod) return;

    AcquireSRWLockExclusive(&s_patchLock);
    if (s_scannedCountryModules.find(hMod) != s_scannedCountryModules.end()) {
        ReleaseSRWLockExclusive(&s_patchLock);
        return;
    }
    s_scannedCountryModules.insert(hMod);
    ReleaseSRWLockExclusive(&s_patchLock);

    __try {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;
        if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x10000000) return;

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
            BYTE* s_end = s + sz - 18;

            for (BYTE* p = s; p <= s_end; p++) {
                // Strict 17-byte pattern: 3B C1 0F 85 [disp1] 83 FB FF 0F 84 [disp2]
                if (p[0] == 0x3B && p[1] == 0xC1 && p[2] == 0x0F && p[3] == 0x85 &&
                    p[8] == 0x83 && p[9] == 0xFB && p[10] == 0xFF && p[11] == 0x0F && p[12] == 0x84) {
                    
                    int32_t disp1 = *(int32_t*)(p + 4);
                    int32_t disp2 = *(int32_t*)(p + 13);
                    BYTE* target1 = p + 8 + disp1;
                    BYTE* target2 = p + 17 + disp2;

                    if (target1 == target2 && target1 >= base && target1 < base + nt->OptionalHeader.SizeOfImage) {
                        DWORD oldProtect = 0;
                        if (VirtualProtect(p + 2, 15, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                            memset(p + 2, 0x90, 6);   // NOP jne error
                            memset(p + 11, 0x90, 6);  // NOP je error
                            VirtualProtect(p + 2, 15, oldProtect, &oldProtect);
                        }
                        return;
                    }
                }
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

static void PatchAllLoadedLanguageModules() {
    static const wchar_t* const moduleNames[] = {
        L"crysystem.dll",
        L"cryfont.dll",
        L"crymovie.dll",
        L"crysoundsystem.dll",
        L"cry3dengine.dll",
        L"cryanimation.dll",
        L"cryentitysystem.dll",
        L"cryphysics.dll",
        L"cryscriptsystem.dll",
        L"crynetwork.dll",
        L"cryaisystem.dll",
        L"game.dll"
    };

    HMODULE hMain = GetModuleHandleW(nullptr);
    if (hMain) {
        PatchLanguageTableInModule(hMain);
        BypassCountryCheckInCryEngineModule(hMain);
    }
    for (const wchar_t* name : moduleNames) {
        HMODULE h = GetModuleHandleW(name);
        if (h) {
            PatchLanguageTableInModule(h);
            BypassCountryCheckInCryEngineModule(h);
        }
    }
}

static decltype(LoadLibraryA)* real_LoadLibraryA = LoadLibraryA;
static HMODULE WINAPI zzLoadLibraryA(LPCSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryA(lpLibFileName);
    if (h) {
        PatchAllLoadedLanguageModules();
    }
    return h;
}

static decltype(LoadLibraryExA)* real_LoadLibraryExA = LoadLibraryExA;
static HMODULE WINAPI zzLoadLibraryExA(LPCSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExA(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchAllLoadedLanguageModules();
    }
    return h;
}

static decltype(LoadLibraryW)* real_LoadLibraryW = LoadLibraryW;
static HMODULE WINAPI zzLoadLibraryW(LPCWSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryW(lpLibFileName);
    if (h) {
        PatchAllLoadedLanguageModules();
    }
    return h;
}

static decltype(LoadLibraryExW)* real_LoadLibraryExW = LoadLibraryExW;
static HMODULE WINAPI zzLoadLibraryExW(LPCWSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExW(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchAllLoadedLanguageModules();
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
static int WINAPI zzMessageBoxW(_In_opt_ HWND hWnd, _In_opt_ LPCWSTR lpText, _In_opt_ LPCWSTR lpCaption, _In_ UINT uType) {
    if (lpText) {
        if (!wcsncmp(lpText, L"Your PC", 7)) {
            return IDOK;
        }
        if (wcsstr(lpText, L"unavailable in your country")) {
            return IDOK;
        }
    }
    return real_MessageBoxW(hWnd, lpText, lpCaption, uType);
}

// =========================================================================
// Command Line Injection Hook
// Appends official mandatory bypass arguments and normalizes -lang:BRA
// =========================================================================
static decltype(GetCommandLineA)* real_GetCommandLineA = GetCommandLineA;
static LPSTR WINAPI zzGetCommandLineA() {
    static std::string s_hookedCmdA;
    static std::once_flag s_flagA;
    std::call_once(s_flagA, []() {
        LPSTR cmd = real_GetCommandLineA();
        s_hookedCmdA = cmd ? cmd : "";
        size_t p = 0;
        while ((p = s_hookedCmdA.find("-LANG:", p)) != std::string::npos) {
            s_hookedCmdA.replace(p, 6, "-lang:");
            p += 6;
        }
        p = 0;
        while ((p = s_hookedCmdA.find("-Lang:", p)) != std::string::npos) {
            s_hookedCmdA.replace(p, 6, "-lang:");
            p += 6;
        }
        p = 0;
        while ((p = s_hookedCmdA.find("-lang:bra", p)) != std::string::npos) {
            s_hookedCmdA.replace(p, 9, "-lang:BRA");
            p += 9;
        }
        if (s_hookedCmdA.find("-lang:BRA") != std::string::npos) {
            p = s_hookedCmdA.find("-cc:1");
            if (p != std::string::npos) {
                s_hookedCmdA.replace(p, 5, "-cc:2");
            }
            p = s_hookedCmdA.find("-CC:1");
            if (p != std::string::npos) {
                s_hookedCmdA.replace(p, 5, "-cc:2");
            }
        }
        if (s_hookedCmdA.find("-classic") == std::string::npos) {
            s_hookedCmdA += " -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu -dwsm -probability -nospamcheck";
        }
    });
    return const_cast<LPSTR>(s_hookedCmdA.c_str());
}

static decltype(GetCommandLineW)* real_GetCommandLineW = GetCommandLineW;
static LPWSTR WINAPI zzGetCommandLineW() {
    static std::wstring s_hookedCmdW;
    static std::once_flag s_flagW;
    std::call_once(s_flagW, []() {
        LPWSTR cmd = real_GetCommandLineW();
        s_hookedCmdW = cmd ? cmd : L"";
        size_t p = 0;
        while ((p = s_hookedCmdW.find(L"-LANG:", p)) != std::wstring::npos) {
            s_hookedCmdW.replace(p, 6, L"-lang:");
            p += 6;
        }
        p = 0;
        while ((p = s_hookedCmdW.find(L"-Lang:", p)) != std::wstring::npos) {
            s_hookedCmdW.replace(p, 6, L"-lang:");
            p += 6;
        }
        p = 0;
        while ((p = s_hookedCmdW.find(L"-lang:bra", p)) != std::wstring::npos) {
            s_hookedCmdW.replace(p, 9, L"-lang:BRA");
            p += 9;
        }
        if (s_hookedCmdW.find(L"-lang:BRA") != std::wstring::npos) {
            p = s_hookedCmdW.find(L"-cc:1");
            if (p != std::wstring::npos) {
                s_hookedCmdW.replace(p, 5, L"-cc:2");
            }
            p = s_hookedCmdW.find(L"-CC:1");
            if (p != std::wstring::npos) {
                s_hookedCmdW.replace(p, 5, L"-cc:2");
            }
        }
        if (s_hookedCmdW.find(L"-classic") == std::wstring::npos) {
            s_hookedCmdW += L" -noweb -classic -nowebshop -dnpshop -st -dpetition -hidepromo -nosatab -nosarefund -disabletempbanner -disabledevaschedule -old_charInstance -charnamemenu -dwsm -probability -nospamcheck";
        }
    });
    return const_cast<LPWSTR>(s_hookedCmdW.c_str());
}

static decltype(SetWindowLongA)* real_SetWindowLongA = SetWindowLongA;
static LONG WINAPI zzSetWindowLongA(_In_ HWND hWnd, _In_ int nIndex, _In_ LONG dwNewLong) {
    if (!s_gfxEnabled) {
        EnableHighQualityGraphicsOptions();
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
    // Early language table patch for main module
    PatchLanguageTableInModule(GetModuleHandleW(nullptr));
    BypassCountryCheckInCryEngineModule(GetModuleHandleW(nullptr));
    PatchAllLoadedLanguageModules();

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
    DetourTransactionCommit();

    FixClientStartupWithHighCoreCountCpus();
}

BOOL WINAPI DllMain(_In_ HINSTANCE hinstDLL, _In_ DWORD fdwReason, _In_ LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);

        // Pin version.dll in memory so it is NEVER unloaded by dynamic FreeLibrary calls
        HMODULE hSelf = nullptr;
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN, (LPCWSTR)hinstDLL, &hSelf);

        InstallPatch();

        // Spawn early language monitor thread (surveillance for 30s during client load)
        HANDLE hLangThread = CreateThread(nullptr, 0, [](LPVOID) -> DWORD {
            for (int i = 0; i < 300; i++) {
                PatchAllLoadedLanguageModules();
                Sleep(100);
            }
            return 0;
        }, nullptr, 0, nullptr);
        if (hLangThread) {
            CloseHandle(hLangThread);
        }
    }
    return TRUE;
}
