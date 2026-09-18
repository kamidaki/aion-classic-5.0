#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include <stdint.h>
#include <string>
#include <algorithm>
#include <unordered_set>
#include "exports.h"
#include "detours.h"
#include "siel_hammer_fix.h"

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
static std::unordered_set<HMODULE> s_scannedLangModules;
static std::unordered_set<HMODULE> s_scannedCountryModules;
static std::unordered_set<HMODULE> s_scannedCrcModules;
static SRWLOCK s_patchLock = SRWLOCK_INIT;

static bool BypassTableCrcInModule(HMODULE hMod) {
    if (!hMod) return false;

    __try {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
        if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x10000000) return false;

        PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return false;

        BYTE* base = (BYTE*)hMod;
        bool patchedAny = false;
        PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
        for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
            if (!(sec->Characteristics & IMAGE_SCN_MEM_EXECUTE))
                continue;

            BYTE* s = base + sec->VirtualAddress;
            DWORD sz = sec->Misc.VirtualSize;
            if (sz < 16) continue;
            BYTE* s_end = s + sz - 14;

            for (BYTE* p = s; p <= s_end; p++) {
                // Check pattern: 39 AC 24 70 01 00 00 0F 85 (cmp dword ptr [rsp + 0x170], ebp; jne ...)
                if (p[0] == 0x39 && p[1] == 0xAC && p[2] == 0x24 && p[3] == 0x70 &&
                    p[4] == 0x01 && p[5] == 0x00 && p[6] == 0x00 &&
                    p[7] == 0x0F && p[8] == 0x85) {
                    
                    DWORD oldProtect = 0;
                    if (VirtualProtect(p + 7, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memset(p + 7, 0x90, 6); // 6 NOPs: bypass jne fail_handler
                        VirtualProtect(p + 7, 6, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 12;
                }
            }
        }
        return patchedAny;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static bool BypassCountryCheckInModule(HMODULE hMod) {
    if (!hMod) return false;

    __try {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
        if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x10000000) return false;

        PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return false;

        BYTE* base = (BYTE*)hMod;
        bool patchedAny = false;
        PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
        for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
            if (!(sec->Characteristics & IMAGE_SCN_MEM_EXECUTE))
                continue;

            BYTE* s = base + sec->VirtualAddress;
            DWORD sz = sec->Misc.VirtualSize;
            if (sz < 32) continue;
            BYTE* s_end = s + sz - 18;

            for (BYTE* p = s; p <= s_end; p++) {
                // Check if candidate starts with: 3B C1 0F 85 (cmp eax, ecx; jne ...)
                if (p[0] == 0x3B && p[1] == 0xC1 && p[2] == 0x0F && p[3] == 0x85) {
                    
                    // Pattern 1 (18-byte): 3B C1 0F 85 [disp1] 41 83 [reg] FF 0F 84 [disp2] (x64 CryEngine: r14d / r11d)
                    if (p[8] == 0x41 && p[9] == 0x83 && (p[10] & 0xF8) == 0xF8 && p[11] == 0xFF && p[12] == 0x0F && p[13] == 0x84) {
                        int32_t disp1 = *(int32_t*)(p + 4);
                        int32_t disp2 = *(int32_t*)(p + 14);
                        BYTE* target1 = p + 8 + disp1;
                        BYTE* target2 = p + 18 + disp2;

                        if (target1 == target2 && target1 >= base && target1 < base + nt->OptionalHeader.SizeOfImage) {
                            DWORD oldProtect = 0;
                            if (VirtualProtect(p + 2, 16, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                                memset(p + 2, 0x90, 6);   // NOP jne target
                                memset(p + 12, 0x90, 6);  // NOP je target
                                VirtualProtect(p + 2, 16, oldProtect, &oldProtect);
                                patchedAny = true;
                            }
                            p += 17;
                            continue;
                        }
                    }

                    // Pattern 2 (17-byte): 3B C1 0F 85 [disp1] 83 [reg] FF 0F 84 [disp2] (x86 or x64 ebx/esi)
                    if (p[8] == 0x83 && (p[9] & 0xF8) == 0xF8 && p[10] == 0xFF && p[11] == 0x0F && p[12] == 0x84) {
                        int32_t disp1 = *(int32_t*)(p + 4);
                        int32_t disp2 = *(int32_t*)(p + 13);
                        BYTE* target1 = p + 8 + disp1;
                        BYTE* target2 = p + 17 + disp2;

                        if (target1 == target2 && target1 >= base && target1 < base + nt->OptionalHeader.SizeOfImage) {
                            DWORD oldProtect = 0;
                            if (VirtualProtect(p + 2, 15, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                                memset(p + 2, 0x90, 6);   // NOP jne target
                                memset(p + 11, 0x90, 6);  // NOP je target
                                VirtualProtect(p + 2, 15, oldProtect, &oldProtect);
                                patchedAny = true;
                            }
                            p += 16;
                            continue;
                        }
                    }
                }
            }
        }
        return patchedAny;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static bool PatchLanguageTableInModule(HMODULE hMod) {
    if (!hMod) return false;

    __try {
        PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hMod;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
        if (dos->e_lfanew <= 0 || dos->e_lfanew > 0x10000000) return false;

        PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((BYTE*)hMod + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return false;

        BYTE* base = (BYTE*)hMod;
        bool patchedAny = false;

#if defined(_M_AMD64)
        // Direct fast-path: Game.dll (64-bit) known PLK offset at 0xd5ee88
        if (nt->OptionalHeader.SizeOfImage > 0xd5ee90) {
            BYTE* pPlk = base + 0xd5ee88;
            if (memcmp(pPlk, "PLK\0", 4) == 0) {
                DWORD oldProtect = 0;
                if (VirtualProtect(pPlk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(pPlk, "BRA\0", 4);
                    VirtualProtect(pPlk, 4, oldProtect, &oldProtect);
                    patchedAny = true;
                }
            } else if (memcmp(pPlk, "BRA\0", 4) == 0) {
                patchedAny = true;
            }
        }

        // Direct fast-path: CryMovie.dll (64-bit) known PLK offset at 0xa6b50
        if (nt->OptionalHeader.SizeOfImage > 0xa6b58) {
            BYTE* pPlk = base + 0xa6b50;
            if (memcmp(pPlk, "PLK\0", 4) == 0) {
                DWORD oldProtect = 0;
                if (VirtualProtect(pPlk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(pPlk, "BRA\0", 4);
                    VirtualProtect(pPlk, 4, oldProtect, &oldProtect);
                    patchedAny = true;
                }
            } else if (memcmp(pPlk, "BRA\0", 4) == 0) {
                patchedAny = true;
            }
        }

        // Direct fast-path: CrySystem.dll (64-bit) known PLK/BRA offset at 0x2018b8
        if (nt->OptionalHeader.SizeOfImage > 0x2018c0) {
            BYTE* pPlk = base + 0x2018b8;
            if (memcmp(pPlk, "PLK\0", 4) == 0) {
                DWORD oldProtect = 0;
                if (VirtualProtect(pPlk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                    memcpy(pPlk, "BRA\0", 4);
                    VirtualProtect(pPlk, 4, oldProtect, &oldProtect);
                    patchedAny = true;
                }
            } else if (memcmp(pPlk, "BRA\0", 4) == 0) {
                patchedAny = true;
            }
        }
#endif

        const char p1_prefix[] = "KOR\0ENU\0ENG\0DEU\0FRA\0ITA\0ESN\0"; // 28 bytes
        const char p2_suffix[] = "ESN\0ITA\0FRA\0DEU\0ENG\0ENU\0KOR\0"; // 28 bytes
        const char p_movie[]   = "KOR\0TRK\0PLK\0ITA\0ESN\0FRA\0DEU\0ENU\0"; // 32 bytes
        const size_t patternLen = 32;

        PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
        for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
            if (!(sec->Characteristics & (IMAGE_SCN_MEM_READ | IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_CNT_CODE)))
                continue;

            BYTE* s = base + sec->VirtualAddress;
            DWORD sz = sec->Misc.VirtualSize;
            if (sz < 8) continue;
            BYTE* s_end = s + sz - 8;

            for (BYTE* p = s; p <= s_end; p++) {
                // High-performance filter: skip any non-candidate bytes immediately
                if (*p != 'P' && *p != 'K' && *p != 'I' && *p != 'E') continue;

                // Check Classic pattern: PLK\0 + ESN\0ITA\0FRA\0DEU\0ENG\0ENU\0KOR\0
                if (*p == 'P' && p <= s + sz - patternLen && memcmp(p, "PLK\0", 4) == 0 && memcmp(p + 4, p2_suffix, 28) == 0) {
                    DWORD oldProtect = 0;
                    if (VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(p, "BRA\0", 4);
                        VirtualProtect(p, 4, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 31;
                    continue;
                }
                // Check primary 32-byte 5.0+ pattern (KOR...PLK)
                if (*p == 'K' && p <= s + sz - patternLen && memcmp(p, p1_prefix, 28) == 0 && memcmp(p + 28, "PLK\0", 4) == 0) {
                    BYTE* plk = p + 28;
                    DWORD oldProtect = 0;
                    if (VirtualProtect(plk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(plk, "BRA\0", 4);
                        VirtualProtect(plk, 4, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 31;
                    continue;
                }
                // Check CryMovie pattern: KOR\0TRK\0PLK\0ITA\0ESN\0FRA\0DEU\0ENU\0
                if (*p == 'K' && p <= s + sz - patternLen && memcmp(p, p_movie, 32) == 0) {
                    BYTE* plk = p + 8;
                    DWORD oldProtect = 0;
                    if (VirtualProtect(plk, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(plk, "BRA\0", 4);
                        VirtualProtect(plk, 4, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 31;
                    continue;
                }
                // Check Game.dll / short pattern: PLK\0ESN\0, PLK\0TRK\0, PLK\0ITA\0
                if (*p == 'P' && (memcmp(p, "PLK\0ESN\0", 8) == 0 || memcmp(p, "PLK\0TRK\0", 8) == 0 || memcmp(p, "PLK\0ITA\0", 8) == 0)) {
                    DWORD oldProtect = 0;
                    if (VirtualProtect(p, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(p, "BRA\0", 4);
                        VirtualProtect(p, 4, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 3;
                    continue;
                }
                // Check CryMovie.dll pattern: ITA\0PLK\0 or ESN\0PLK\0
                if ((*p == 'I' || *p == 'E') && (memcmp(p, "ITA\0PLK\0", 8) == 0 || memcmp(p, "ESN\0PLK\0", 8) == 0)) {
                    DWORD oldProtect = 0;
                    if (VirtualProtect(p + 4, 4, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(p + 4, "BRA\0", 4);
                        VirtualProtect(p + 4, 4, oldProtect, &oldProtect);
                        patchedAny = true;
                    }
                    p += 7;
                    continue;
                }
            }
        }
        return patchedAny;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
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
        L"game.dll",
        L"xrenderd3d9.dll",
        L"SendLogClient.exe"
    };
    HMODULE hMain = GetModuleHandleW(nullptr);
    if (hMain) {
        AcquireSRWLockExclusive(&s_patchLock);
        bool langDone = s_scannedLangModules.count(hMain) > 0;
        bool countryDone = s_scannedCountryModules.count(hMain) > 0;
        bool crcDone = s_scannedCrcModules.count(hMain) > 0;
        ReleaseSRWLockExclusive(&s_patchLock);

        if (!langDone && PatchLanguageTableInModule(hMain)) {
            AcquireSRWLockExclusive(&s_patchLock);
            s_scannedLangModules.insert(hMain);
            ReleaseSRWLockExclusive(&s_patchLock);
        }
        if (!countryDone && BypassCountryCheckInModule(hMain)) {
            AcquireSRWLockExclusive(&s_patchLock);
            s_scannedCountryModules.insert(hMain);
            ReleaseSRWLockExclusive(&s_patchLock);
        }
        if (!crcDone && BypassTableCrcInModule(hMain)) {
            AcquireSRWLockExclusive(&s_patchLock);
            s_scannedCrcModules.insert(hMain);
            ReleaseSRWLockExclusive(&s_patchLock);
        }
    }
    for (const wchar_t* name : moduleNames) {
        HMODULE h = GetModuleHandleW(name);
        if (h) {
            if (_wcsicmp(name, L"game.dll") == 0) InstallSielHammerFix(h);
            AcquireSRWLockExclusive(&s_patchLock);
            bool langDone = s_scannedLangModules.count(h) > 0;
            bool countryDone = s_scannedCountryModules.count(h) > 0;
            bool crcDone = s_scannedCrcModules.count(h) > 0;
            ReleaseSRWLockExclusive(&s_patchLock);

            if (!langDone && PatchLanguageTableInModule(h)) {
                AcquireSRWLockExclusive(&s_patchLock);
                s_scannedLangModules.insert(h);
                ReleaseSRWLockExclusive(&s_patchLock);
            }
            if (!countryDone && BypassCountryCheckInModule(h)) {
                AcquireSRWLockExclusive(&s_patchLock);
                s_scannedCountryModules.insert(h);
                ReleaseSRWLockExclusive(&s_patchLock);
            }
            if (!crcDone && BypassTableCrcInModule(h)) {
                AcquireSRWLockExclusive(&s_patchLock);
                s_scannedCrcModules.insert(h);
                ReleaseSRWLockExclusive(&s_patchLock);
            }
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
static int WINAPI zzMessageBoxW(HWND hWnd, LPCWSTR lpText, LPCWSTR lpCaption, UINT uType) {
    if (lpText && wcsstr(lpText, L"unavailable in your country")) {
        return IDOK;
    }
    return real_MessageBoxW(hWnd, lpText, lpCaption, uType);
}

static decltype(GetPrivateProfileIntA)* real_GetPrivateProfileIntA = GetPrivateProfileIntA;
static UINT WINAPI zzGetPrivateProfileIntA(LPCSTR lpAppName, LPCSTR lpKeyName, INT nDefault, LPCSTR lpFileName) {
    if (lpKeyName && _stricmp(lpKeyName, "ValidTableDump") == 0) {
        return 0; // Force disable binary table dump so localized XML strings are always loaded
    }
    return real_GetPrivateProfileIntA(lpAppName, lpKeyName, nDefault, lpFileName);
}

static decltype(GetPrivateProfileIntW)* real_GetPrivateProfileIntW = GetPrivateProfileIntW;
static UINT WINAPI zzGetPrivateProfileIntW(LPCWSTR lpAppName, LPCWSTR lpKeyName, INT nDefault, LPCWSTR lpFileName) {
    if (lpKeyName && _wcsicmp(lpKeyName, L"ValidTableDump") == 0) {
        return 0; // Force disable binary table dump so localized XML strings are always loaded
    }
    return real_GetPrivateProfileIntW(lpAppName, lpKeyName, nDefault, lpFileName);
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
    }
    return const_cast<LPSTR>(s_hookedCmdA.c_str());
}

static decltype(GetCommandLineW)* real_GetCommandLineW = GetCommandLineW;
static LPWSTR WINAPI zzGetCommandLineW() {
    static std::wstring s_hookedCmdW;
    if (s_hookedCmdW.empty()) {
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
    DetourAttach(&(PVOID&)real_GetPrivateProfileIntA, zzGetPrivateProfileIntA);
    DetourAttach(&(PVOID&)real_GetPrivateProfileIntW, zzGetPrivateProfileIntW);
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

