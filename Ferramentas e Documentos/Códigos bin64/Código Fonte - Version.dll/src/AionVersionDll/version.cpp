#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include <commctrl.h>
#pragma comment(lib, "comctl32.lib")
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <algorithm>
#include <unordered_set>
#include <mutex>
#include <atomic>
#include "exports.h"
#include "detours.h"
#include "siel_hammer_fix.h"
#include "quna_fix.h"
#include "harp_fix.h"
#include "charge_fix.h"
#include "inventory_fix.h"
#include "globaltrade_fix.h"
#include "hair_color_fix.h"
#include "multiserver_fix.h"

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

            // Clamp scanning range to valid committed memory pages via VirtualQuery
            MEMORY_BASIC_INFORMATION mbi = { 0 };
            if (VirtualQuery(s, &mbi, sizeof(mbi)) && mbi.State == MEM_COMMIT) {
                size_t committedBytes = (BYTE*)mbi.BaseAddress + mbi.RegionSize - s;
                if (sz > (DWORD)committedBytes) {
                    sz = (DWORD)committedBytes;
                }
            } else {
                continue;
            }
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

            // Clamp scanning range to valid committed memory pages via VirtualQuery
            MEMORY_BASIC_INFORMATION mbi = { 0 };
            if (VirtualQuery(s, &mbi, sizeof(mbi)) && mbi.State == MEM_COMMIT) {
                size_t committedBytes = (BYTE*)mbi.BaseAddress + mbi.RegionSize - s;
                if (sz > (DWORD)committedBytes) {
                    sz = (DWORD)committedBytes;
                }
            } else {
                continue;
            }
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

static std::atomic<bool> s_allTargetModulesPatched{ false };

static void PatchAllLoadedLanguageModules() {
    if (s_allTargetModulesPatched.load(std::memory_order_relaxed)) {
        return;
    }

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
    size_t loadedTargetCount = 0;
    for (const wchar_t* name : moduleNames) {
        HMODULE h = GetModuleHandleW(name);
        if (h) {
            loadedTargetCount++;
            if (_wcsicmp(name, L"game.dll") == 0) {
                InstallSielHammerFix(h);
                InstallQunaFix(h);
                InstallHarpFix(h);
                InstallChargeFix(h);
                InstallInventoryFix(h);
                InstallGlobalTradeFix(h);
                InstallHairColorFix(h);
                InstallMultiServerFix(h);
            }
            PatchLanguageTableInModule(h);
            BypassCountryCheckInCryEngineModule(h);
        }
    }
    if (hMain && loadedTargetCount == _countof(moduleNames)) {
        s_allTargetModulesPatched.store(true, std::memory_order_release);
    }
}

static decltype(LoadLibraryA)* real_LoadLibraryA = LoadLibraryA;
static HMODULE WINAPI zzLoadLibraryA(LPCSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryA(lpLibFileName);
    if (h) {
        PatchAllLoadedLanguageModules();
        HarpOnModuleLoaded(h);
    }
    return h;
}

static decltype(LoadLibraryExA)* real_LoadLibraryExA = LoadLibraryExA;
static HMODULE WINAPI zzLoadLibraryExA(LPCSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExA(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchAllLoadedLanguageModules();
        HarpOnModuleLoaded(h);
    }
    return h;
}

static decltype(LoadLibraryW)* real_LoadLibraryW = LoadLibraryW;
static HMODULE WINAPI zzLoadLibraryW(LPCWSTR lpLibFileName) {
    HMODULE h = real_LoadLibraryW(lpLibFileName);
    if (h) {
        PatchAllLoadedLanguageModules();
        HarpOnModuleLoaded(h);
    }
    return h;
}

static decltype(LoadLibraryExW)* real_LoadLibraryExW = LoadLibraryExW;
static HMODULE WINAPI zzLoadLibraryExW(LPCWSTR lpLibFileName, HANDLE hFile, DWORD dwFlags) {
    HMODULE h = real_LoadLibraryExW(lpLibFileName, hFile, dwFlags);
    if (h && !(dwFlags & (LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE))) {
        PatchAllLoadedLanguageModules();
        HarpOnModuleLoaded(h);
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
// Opcao inteira na linha de comando: "-probability" nao pode casar com "-probability2".
template <typename C>
static bool HasCmdOption(const std::basic_string<C>& cmd, const C* opt) {
    const std::basic_string<C> o(opt);
    for (size_t p = cmd.find(o); p != std::basic_string<C>::npos; p = cmd.find(o, p + 1)) {
        size_t end = p + o.size();
        if (end == cmd.size() || cmd[end] == C(' ') || cmd[end] == C(':'))
            return true;
    }
    return false;
}

// No Aion.bin, -probability liga o bit 82 do bitset de conteudo e -probability2 o bit 102. O Game.dll testa o 102 antes de colocar
// "Ctrl + clique: ver conteudo/probabilidade" no tooltip de caixas e de abrir a janela nativa (dlg_disassembly_info) com os itens e as chances.
template <typename C>
static void AppendProbabilityOptions(std::basic_string<C>& cmd) {
    static const C probability[] = { '-','p','r','o','b','a','b','i','l','i','t','y',0 };
    static const C probability2[] = { '-','p','r','o','b','a','b','i','l','i','t','y','2',0 };
    static const C space[] = { ' ',0 };
    if (!HasCmdOption(cmd, probability))
        cmd += std::basic_string<C>(space) + probability;
    if (!HasCmdOption(cmd, probability2))
        cmd += std::basic_string<C>(space) + probability2;
}

// =========================================================================
// WebPort Runtime Mode Detection, Shared Input State & Process Protection
// =========================================================================
static bool s_isWebPort = false;
static DWORD s_mainThreadId = 0;
static std::atomic<bool> s_adminShutdownRequested{ false };
static HWND s_hGameWindow = NULL;

#pragma pack(push, 1)
struct AionWebPortInputState {
    uint32_t magic;                  // 0x41494E50 ("AINP")
    uint32_t version;                // 1
    int32_t  virtualX;               // Client-space cursor X
    int32_t  virtualY;               // Client-space cursor Y
    int32_t  clientWidth;            // Virtual client width (default 1920)
    int32_t  clientHeight;           // Virtual client height (default 1080)
    uint32_t mouseButtons;           // Bit 0: LBUTTON, Bit 1: RBUTTON, Bit 2: MBUTTON
    uint32_t modifiers;              // Bit 0: SHIFT, Bit 1: CTRL, Bit 2: ALT
    uint8_t  keyStates[256];         // 0x80 if pressed, 0x00 if released
    uint64_t activeHCursor;          // Most recent HCURSOR set by Game.dll via SetCursor
    int32_t  cursorVisible;          // Cursor visibility state
    uint32_t cursorShapeId;          // Sequential cursor shape ID (1..N)
    uint32_t interceptedExitCount;   // Incremented whenever a player exit is blocked
    uint32_t lastExitReason;         // 1=ExitProcess, 2=TerminateProcess, 3=WM_CLOSE, 4=PostQuitMessage, 5=DestroyWindow
    uint32_t returnToLoginRequested; // Polled by host engine to redirect session to login
    uint32_t focusIsolated;          // 1 when browser window has focus, 0 when blurred
    uint64_t lastInputTimestampMs;   // Timestamp of most recent input event
    char     activeSessionId[64];    // Current active session ID
    uint8_t  reserved[632];          // Pad to 1024 bytes total
};
#pragma pack(pop)
static_assert(sizeof(AionWebPortInputState) == 1024, "AionWebPortInputState must be exactly 1024 bytes");

static HANDLE s_hInputMapFile = NULL;
static AionWebPortInputState* s_pInputState = nullptr;
static SRWLOCK s_cursorMapLock = SRWLOCK_INIT;
static uint64_t s_knownCursors[128] = {};
static uint32_t s_knownCursorCount = 0;

static AionWebPortInputState* GetWebPortInputState() {
    if (s_pInputState) return s_pInputState;
    static SRWLOCK s_initLock = SRWLOCK_INIT;
    AcquireSRWLockExclusive(&s_initLock);
    if (!s_pInputState) {
        s_hInputMapFile = CreateFileMappingA(
            INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
            0, sizeof(AionWebPortInputState), "Local\\AionWebPortInputState"
        );
        if (s_hInputMapFile) {
            bool alreadyExists = (GetLastError() == ERROR_ALREADY_EXISTS);
            void* pView = MapViewOfFile(s_hInputMapFile, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(AionWebPortInputState));
            if (pView) {
                s_pInputState = reinterpret_cast<AionWebPortInputState*>(pView);
                if (!alreadyExists || s_pInputState->magic != 0x41494E50) {
                    memset(s_pInputState, 0, sizeof(AionWebPortInputState));
                    s_pInputState->magic = 0x41494E50;
                    s_pInputState->version = 1;
                    s_pInputState->virtualX = 960;
                    s_pInputState->virtualY = 540;
                    s_pInputState->clientWidth = 1920;
                    s_pInputState->clientHeight = 1080;
                    s_pInputState->cursorVisible = 1;
                    s_pInputState->cursorShapeId = 1;
                    s_pInputState->focusIsolated = 1;
                    strcpy_s(s_pInputState->activeSessionId, "default");
                }
            }
        }
    }
    ReleaseSRWLockExclusive(&s_initLock);
    return s_pInputState;
}

static void RecordInterceptedPlayerExit(uint32_t reasonCode, const char* sourceDesc) {
    AionWebPortInputState* pState = GetWebPortInputState();
    uint32_t count = 1;
    const char* sessionId = "unknown";
    if (pState) {
        count = InterlockedIncrement((volatile LONG*)&pState->interceptedExitCount);
        pState->lastExitReason = reasonCode;
        pState->returnToLoginRequested = 1;
        pState->mouseButtons = 0;
        pState->modifiers = 0;
        memset(pState->keyStates, 0, sizeof(pState->keyStates));
        if (pState->activeSessionId[0]) {
            sessionId = pState->activeSessionId;
        }
    }
    char logBuf[512];
    sprintf_s(
        logBuf,
        "[AION_VERSION_DLL] WebPort Shared Process Protection: Blocked player exit (%s, reason=%u, count=%u) on PID=%lu Thread=%lu Session=%s. Shared Aion.bin preserved; redirecting session to login.\n",
        sourceDesc ? sourceDesc : "Unknown",
        reasonCode,
        count,
        GetCurrentProcessId(),
        GetCurrentThreadId(),
        sessionId
    );
    OutputDebugStringA(logBuf);
}

extern "C" __declspec(dllexport) bool WINAPI IsWebPortClient() {
    return s_isWebPort;
}

extern "C" __declspec(dllexport) uint32_t WINAPI GetInterceptedExitCount() {
    AionWebPortInputState* pState = GetWebPortInputState();
    return pState ? pState->interceptedExitCount : 0;
}

extern "C" __declspec(dllexport) void WINAPI SetActiveWebSessionId(LPCSTR sessionId) {
    AionWebPortInputState* pState = GetWebPortInputState();
    if (pState && sessionId) {
        strncpy_s(pState->activeSessionId, sizeof(pState->activeSessionId), sessionId, _TRUNCATE);
    }
}

extern "C" __declspec(dllexport) bool WINAPI TriggerSessionReturnToLogin() {
    RecordInterceptedPlayerExit(6, "TriggerSessionReturnToLogin");
    return true;
}

static void InitializeWebPortHooks() {
    GetWebPortInputState();
    OutputDebugStringA("[AION_VERSION_DLL] WebPort execution mode ACTIVE (-webPort detected). Shared input state and process protection enabled.\n");
}

static decltype(GetCommandLineA)* real_GetCommandLineA = GetCommandLineA;
static LPSTR WINAPI zzGetCommandLineA() {
    static std::string s_hookedCmdA;
    static std::once_flag s_flagA;
    std::call_once(s_flagA, []() {
        LPSTR cmd = real_GetCommandLineA();
        s_hookedCmdA = cmd ? cmd : "";
        AppendProbabilityOptions(s_hookedCmdA);

        // Detect -webPort parameter (case-insensitive)
        std::string lowerCmdA = s_hookedCmdA;
        std::transform(lowerCmdA.begin(), lowerCmdA.end(), lowerCmdA.begin(), ::tolower);
        if (lowerCmdA.find("-webport") != std::string::npos) {
            s_isWebPort = true;
            InitializeWebPortHooks();
        }

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
        if (s_isWebPort && s_hookedCmdA.find("-webPort") == std::string::npos && s_hookedCmdA.find("-webport") == std::string::npos) {
            s_hookedCmdA += " -webPort";
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
        AppendProbabilityOptions(s_hookedCmdW);

        // Detect -webPort parameter (case-insensitive)
        std::wstring lowerCmdW = s_hookedCmdW;
        std::transform(lowerCmdW.begin(), lowerCmdW.end(), lowerCmdW.begin(), ::tolower);
        if (lowerCmdW.find(L"-webport") != std::wstring::npos) {
            s_isWebPort = true;
            InitializeWebPortHooks();
        }

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
        if (s_isWebPort && s_hookedCmdW.find(L"-webPort") == std::wstring::npos && s_hookedCmdW.find(L"-webport") == std::wstring::npos) {
            s_hookedCmdW += L" -webPort";
        }
    });
    return const_cast<LPWSTR>(s_hookedCmdW.c_str());
}

// =========================================================================
// Subclassed Game Window Procedure for Shared Process Protection
// Uses standard ComCtl32 SetWindowSubclass/DefSubclassProc to safely isolate
// the shared Aion.bin process without recursion or global proc pointer races.
// =========================================================================
#define AION_WEBPORT_SUBCLASS_ID 0x57454250 // 'WEBP'

static LRESULT CALLBACK WebPortSubclassProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam, UINT_PTR uIdSubclass, DWORD_PTR dwRefData) {
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed)) {
        if (uMsg == WM_CLOSE) {
            RecordInterceptedPlayerExit(3, "WndProc(WM_CLOSE)");
            return 0;
        }
        if (uMsg == WM_SYSCOMMAND && ((wParam & 0xFFF0) == SC_CLOSE)) {
            RecordInterceptedPlayerExit(3, "WndProc(SC_CLOSE)");
            return 0;
        }
        if (uMsg == WM_DESTROY || uMsg == WM_NCDESTROY || uMsg == WM_QUIT) {
            RecordInterceptedPlayerExit(3, "WndProc(WM_DESTROY/QUIT)");
            return 0;
        }
    }
    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

static void EnsureGameWindowSubclassed(HWND hWnd) {
    if (!s_isWebPort || !hWnd) return;
    SetWindowSubclass(hWnd, WebPortSubclassProc, AION_WEBPORT_SUBCLASS_ID, 0);
}

static decltype(SetWindowLongA)* real_SetWindowLongA = SetWindowLongA;
static LONG WINAPI zzSetWindowLongA(_In_ HWND hWnd, _In_ int nIndex, _In_ LONG dwNewLong) {
    if (!s_gfxEnabled) {
        EnableHighQualityGraphicsOptions();
        s_gfxEnabled = true;
    }
    return real_SetWindowLongA(hWnd, nIndex, dwNewLong);
}

// =========================================================================
// Silent WebPort Clientless Window Interception & Virtual Cursor/Input Hooks
// Restricts off-screen displacement and subclassing strictly to the Aion
// game window ("AIONClientWndClass1.0", "CryENGINE", "AION").
// =========================================================================
static bool IsAionWindowClassA(LPCSTR lpClassName) {
    if (!lpClassName || ((uintptr_t)lpClassName < 0x10000)) return false;
    char lower[128] = { 0 };
    strncpy_s(lower, lpClassName, _TRUNCATE);
    for (int i = 0; lower[i]; i++) lower[i] = (char)::tolower(lower[i]);
    return (strstr(lower, "aionclient") != nullptr || strstr(lower, "cryengine") != nullptr || strstr(lower, "aion") != nullptr);
}

static bool IsAionWindowClassW(LPCWSTR lpClassName) {
    if (!lpClassName || ((uintptr_t)lpClassName < 0x10000)) return false;
    wchar_t lower[128] = { 0 };
    wcsncpy_s(lower, lpClassName, _TRUNCATE);
    for (int i = 0; lower[i]; i++) lower[i] = (wchar_t)::towlower(lower[i]);
    return (wcsstr(lower, L"aionclient") != nullptr || wcsstr(lower, L"cryengine") != nullptr || wcsstr(lower, L"aion") != nullptr);
}

static bool IsTargetGameWindow(HWND hWnd) {
    if (!hWnd) return false;
    char cls[128] = { 0 };
    if (GetClassNameA(hWnd, cls, sizeof(cls)) > 0) {
        for (int i = 0; cls[i]; i++) cls[i] = (char)::tolower(cls[i]);
        if (strstr(cls, "aionclient") != nullptr || strstr(cls, "cryengine") != nullptr || strstr(cls, "aion") != nullptr) {
            return true;
        }
    }
    return false;
}

static decltype(CreateWindowExA)* real_CreateWindowExA = CreateWindowExA;
static HWND WINAPI zzCreateWindowExA(
    DWORD dwExStyle, LPCSTR lpClassName, LPCSTR lpWindowName, DWORD dwStyle,
    int X, int Y, int nWidth, int nHeight,
    HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, LPVOID lpParam
) {
    bool isGameWnd = s_isWebPort && !hWndParent && IsAionWindowClassA(lpClassName);
    if (isGameWnd) {
        dwStyle &= ~WS_VISIBLE;
        dwStyle |= WS_POPUP;
        dwExStyle |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE;
        X = -32000;
        Y = -32000;
    }
    HWND hWnd = real_CreateWindowExA(dwExStyle, lpClassName, lpWindowName, dwStyle, X, Y, nWidth, nHeight, hWndParent, hMenu, hInstance, lpParam);
    if (s_isWebPort && !hWndParent && hWnd) {
        if (isGameWnd || (!s_hGameWindow && IsTargetGameWindow(hWnd))) {
            s_hGameWindow = hWnd;
            AionWebPortInputState* pState = GetWebPortInputState();
            if (pState && nWidth > 0 && nHeight > 0) {
                pState->clientWidth = nWidth;
                pState->clientHeight = nHeight;
            }
            EnsureGameWindowSubclassed(hWnd);
        }
    }
    return hWnd;
}

static decltype(CreateWindowExW)* real_CreateWindowExW = CreateWindowExW;
static HWND WINAPI zzCreateWindowExW(
    DWORD dwExStyle, LPCWSTR lpClassName, LPCWSTR lpWindowName, DWORD dwStyle,
    int X, int Y, int nWidth, int nHeight,
    HWND hWndParent, HMENU hMenu, HINSTANCE hInstance, LPVOID lpParam
) {
    bool isGameWnd = s_isWebPort && !hWndParent && IsAionWindowClassW(lpClassName);
    if (isGameWnd) {
        dwStyle &= ~WS_VISIBLE;
        dwStyle |= WS_POPUP;
        dwExStyle |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE;
        X = -32000;
        Y = -32000;
    }
    HWND hWnd = real_CreateWindowExW(dwExStyle, lpClassName, lpWindowName, dwStyle, X, Y, nWidth, nHeight, hWndParent, hMenu, hInstance, lpParam);
    if (s_isWebPort && !hWndParent && hWnd) {
        if (isGameWnd || (!s_hGameWindow && IsTargetGameWindow(hWnd))) {
            s_hGameWindow = hWnd;
            AionWebPortInputState* pState = GetWebPortInputState();
            if (pState && nWidth > 0 && nHeight > 0) {
                pState->clientWidth = nWidth;
                pState->clientHeight = nHeight;
            }
            EnsureGameWindowSubclassed(hWnd);
        }
    }
    return hWnd;
}

static decltype(ShowWindow)* real_ShowWindow = ShowWindow;
static BOOL WINAPI zzShowWindow(HWND hWnd, int nCmdShow) {
    if (s_isWebPort && s_hGameWindow && hWnd == s_hGameWindow) {
        return real_ShowWindow(hWnd, SW_HIDE);
    }
    return real_ShowWindow(hWnd, nCmdShow);
}

static decltype(SetWindowPos)* real_SetWindowPos = SetWindowPos;
static BOOL WINAPI zzSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags) {
    if (s_isWebPort && s_hGameWindow && hWnd == s_hGameWindow) {
        uFlags &= ~SWP_SHOWWINDOW;
        uFlags |= SWP_HIDEWINDOW | SWP_NOACTIVATE | SWP_NOZORDER;
        X = -32000;
        Y = -32000;
        if (cx > 0 && cy > 0) {
            AionWebPortInputState* pState = GetWebPortInputState();
            if (pState) {
                pState->clientWidth = cx;
                pState->clientHeight = cy;
            }
        }
    }
    return real_SetWindowPos(hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags);
}

static decltype(GetCursorPos)* real_GetCursorPos = GetCursorPos;
static BOOL WINAPI zzGetCursorPos(LPPOINT lpPoint) {
    if (s_isWebPort && lpPoint) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (pState) {
            lpPoint->x = pState->virtualX;
            lpPoint->y = pState->virtualY;
            return TRUE;
        }
    }
    return real_GetCursorPos(lpPoint);
}

static decltype(SetCursorPos)* real_SetCursorPos = SetCursorPos;
static BOOL WINAPI zzSetCursorPos(int X, int Y) {
    if (s_isWebPort) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (pState) {
            pState->virtualX = X;
            pState->virtualY = Y;
        }
        return TRUE;
    }
    return real_SetCursorPos(X, Y);
}

static decltype(ScreenToClient)* real_ScreenToClient = ScreenToClient;
static BOOL WINAPI zzScreenToClient(HWND hWnd, LPPOINT lpPoint) {
    if (s_isWebPort && s_hGameWindow && hWnd == s_hGameWindow && lpPoint) {
        // In WebPort mode, virtual cursor coordinates are already in [0..clientWidth, 0..clientHeight]
        return TRUE;
    }
    return real_ScreenToClient(hWnd, lpPoint);
}

static decltype(ClientToScreen)* real_ClientToScreen = ClientToScreen;
static BOOL WINAPI zzClientToScreen(HWND hWnd, LPPOINT lpPoint) {
    if (s_isWebPort && s_hGameWindow && hWnd == s_hGameWindow && lpPoint) {
        return TRUE;
    }
    return real_ClientToScreen(hWnd, lpPoint);
}

static decltype(GetWindowRect)* real_GetWindowRect = GetWindowRect;
static BOOL WINAPI zzGetWindowRect(HWND hWnd, LPRECT lpRect) {
    if (s_isWebPort && s_hGameWindow && hWnd == s_hGameWindow && lpRect) {
        RECT clientRc = { 0, 0, 1920, 1080 };
        if (hWnd && GetClientRect(hWnd, &clientRc) && (clientRc.right - clientRc.left) > 0) {
            lpRect->left = 0;
            lpRect->top = 0;
            lpRect->right = clientRc.right - clientRc.left;
            lpRect->bottom = clientRc.bottom - clientRc.top;
            AionWebPortInputState* pState = GetWebPortInputState();
            if (pState) {
                pState->clientWidth = lpRect->right;
                pState->clientHeight = lpRect->bottom;
            }
            return TRUE;
        }
        AionWebPortInputState* pState = GetWebPortInputState();
        lpRect->left = 0;
        lpRect->top = 0;
        lpRect->right = (pState && pState->clientWidth > 0) ? pState->clientWidth : 1920;
        lpRect->bottom = (pState && pState->clientHeight > 0) ? pState->clientHeight : 1080;
        return TRUE;
    }
    return real_GetWindowRect(hWnd, lpRect);
}

static SHORT QueryWebPortVirtualKey(int vKey) {
    AionWebPortInputState* pState = GetWebPortInputState();
    if (!pState || pState->focusIsolated == 0) {
        return 0;
    }
    if (vKey == VK_LBUTTON) return (pState->mouseButtons & 0x01) ? (SHORT)0x8000 : 0;
    if (vKey == VK_RBUTTON) return (pState->mouseButtons & 0x02) ? (SHORT)0x8000 : 0;
    if (vKey == VK_MBUTTON) return (pState->mouseButtons & 0x04) ? (SHORT)0x8000 : 0;
    if (vKey == VK_SHIFT || vKey == VK_LSHIFT || vKey == VK_RSHIFT) {
        return ((pState->modifiers & 0x01) || (pState->keyStates[VK_SHIFT] & 0x80)) ? (SHORT)0x8000 : 0;
    }
    if (vKey == VK_CONTROL || vKey == VK_LCONTROL || vKey == VK_RCONTROL) {
        return ((pState->modifiers & 0x02) || (pState->keyStates[VK_CONTROL] & 0x80)) ? (SHORT)0x8000 : 0;
    }
    if (vKey == VK_MENU || vKey == VK_LMENU || vKey == VK_RMENU) {
        return ((pState->modifiers & 0x04) || (pState->keyStates[VK_MENU] & 0x80)) ? (SHORT)0x8000 : 0;
    }
    if (vKey >= 0 && vKey < 256) {
        return (pState->keyStates[vKey] & 0x80) ? (SHORT)0x8000 : 0;
    }
    return 0;
}

static decltype(GetAsyncKeyState)* real_GetAsyncKeyState = GetAsyncKeyState;
static SHORT WINAPI zzGetAsyncKeyState(int vKey) {
    if (s_isWebPort) {
        return QueryWebPortVirtualKey(vKey);
    }
    return real_GetAsyncKeyState(vKey);
}

static decltype(GetKeyState)* real_GetKeyState = GetKeyState;
static SHORT WINAPI zzGetKeyState(int nVirtKey) {
    if (s_isWebPort) {
        return QueryWebPortVirtualKey(nVirtKey);
    }
    return real_GetKeyState(nVirtKey);
}

static decltype(GetForegroundWindow)* real_GetForegroundWindow = GetForegroundWindow;
static HWND WINAPI zzGetForegroundWindow() {
    if (s_isWebPort) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (pState && pState->focusIsolated == 0) {
            return NULL;
        }
        if (s_hGameWindow) return s_hGameWindow;
    }
    return real_GetForegroundWindow();
}

static decltype(GetActiveWindow)* real_GetActiveWindow = GetActiveWindow;
static HWND WINAPI zzGetActiveWindow() {
    if (s_isWebPort) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (pState && pState->focusIsolated == 0) {
            return NULL;
        }
        if (s_hGameWindow) return s_hGameWindow;
    }
    return real_GetActiveWindow();
}

static decltype(GetFocus)* real_GetFocus = GetFocus;
static HWND WINAPI zzGetFocus() {
    HWND hFocus = real_GetFocus();
    if (hFocus) return hFocus;
    if (s_isWebPort && s_hGameWindow) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (!pState || pState->focusIsolated != 0) {
            return s_hGameWindow;
        }
    }
    return NULL;
}

static decltype(SetCursor)* real_SetCursor = SetCursor;
static HCURSOR WINAPI zzSetCursor(HCURSOR hCursor) {
    if (s_isWebPort) {
        AionWebPortInputState* pState = GetWebPortInputState();
        if (pState && hCursor != NULL) {
            uint64_t hVal = (uint64_t)(uintptr_t)hCursor;
            pState->activeHCursor = hVal;
            AcquireSRWLockExclusive(&s_cursorMapLock);
            uint32_t shapeId = 0;
            for (uint32_t i = 0; i < s_knownCursorCount; i++) {
                if (s_knownCursors[i] == hVal) {
                    shapeId = i + 1;
                    break;
                }
            }
            if (shapeId == 0 && s_knownCursorCount < 128) {
                s_knownCursors[s_knownCursorCount] = hVal;
                shapeId = ++s_knownCursorCount;
            }
            ReleaseSRWLockExclusive(&s_cursorMapLock);
            if (shapeId > 0) {
                pState->cursorShapeId = shapeId;
            }
        }
    }
    return real_SetCursor(hCursor);
}

typedef HRESULT(WINAPI* PFN_DirectInput8Create)(HINSTANCE, DWORD, REFIID, LPVOID*, LPUNKNOWN);
static PFN_DirectInput8Create real_DirectInput8Create = nullptr;
static HRESULT WINAPI zzDirectInput8Create(HINSTANCE hinst, DWORD dwVersion, REFIID riidltf, LPVOID* ppvOut, LPUNKNOWN punkOuter) {
    if (s_isWebPort) {
        // In WebPort mode, return S_OK with *ppvOut = nullptr.
        // CryInput.dll's CXKeyboard::Init (0x1800015e0) checks if (*ppvOut != NULL), skips creating
        // the physical DirectInput8 keyboard device, and returns 1 (success), eliminating physical
        // keyboard polling leaks across multi-monitor windows while keeping Win32 virtual key dispatch!
        if (ppvOut) {
            *ppvOut = nullptr;
        }
        OutputDebugStringA("[AION_VERSION_DLL] WebPort: DirectInput8 hardware keyboard polling disabled for multi-monitor focus isolation.\n");
        return S_OK;
    }
    return real_DirectInput8Create(hinst, dwVersion, riidltf, ppvOut, punkOuter);
}

// =========================================================================
// Dual Execution Mode & Shared Process Termination Interception
// Preserves conventional Windows client behavior when -webPort is NOT passed.
// In -webPort mode: intercepts player-initiated process exits (WM_CLOSE,
// PostQuitMessage, DestroyWindow, ExitProcess(0), TerminateProcess(self, 0))
// to keep the shared Aion.bin process alive while isolating session logout.
// =========================================================================
static decltype(PostQuitMessage)* real_PostQuitMessage = PostQuitMessage;
static void WINAPI zzPostQuitMessage(int nExitCode) {
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed)) {
        RecordInterceptedPlayerExit(4, "PostQuitMessage");
        return;
    }
    real_PostQuitMessage(nExitCode);
}

static decltype(DestroyWindow)* real_DestroyWindow = DestroyWindow;
static BOOL WINAPI zzDestroyWindow(HWND hWnd) {
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed) && hWnd && (hWnd == s_hGameWindow || IsTargetGameWindow(hWnd))) {
        RecordInterceptedPlayerExit(5, "DestroyWindow(s_hGameWindow)");
        return TRUE;
    }
    return real_DestroyWindow(hWnd);
}

static decltype(ExitProcess)* real_ExitProcess = ExitProcess;

static void WebPortPreventMainThreadExit(UINT uExitCode) {
    if (s_mainThreadId != 0 && GetCurrentThreadId() != s_mainThreadId) {
        ExitThread(0);
    }
    // Main engine thread: caller assumes noreturn.
    // Entering message pump loop keeps the Win32 window, message queue, and DirectX context alive!
    while (!s_adminShutdownRequested.load(std::memory_order_relaxed)) {
        MSG msg;
        while (PeekMessageW(&msg, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        Sleep(16);
    }
    if (real_ExitProcess) {
        real_ExitProcess(uExitCode);
    }
}

static void WINAPI zzExitProcess(UINT uExitCode) {
    char dbg[256];
    sprintf_s(dbg, "[AION_HOOK_CALL] zzExitProcess: uExitCode=%u (0x%08X), TID=%lu, mainTID=%lu, isWebPort=%d\n", uExitCode, uExitCode, GetCurrentThreadId(), s_mainThreadId, (int)s_isWebPort);
    OutputDebugStringA(dbg);
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed)) {
        // Forward only truly fatal system exceptions / crash codes (STATUS_ACCESS_VIOLATION, etc.)
        if (uExitCode >= 0xC0000000 || uExitCode == 0x40000015) {
            OutputDebugStringA("[AION_VERSION_DLL] WebPort: Fatal exception code detected. Forwarding to real ExitProcess.\n");
            real_ExitProcess(uExitCode);
            return;
        }

        RecordInterceptedPlayerExit(1, "ExitProcess");
        WebPortPreventMainThreadExit(uExitCode);
        return;
    }
    real_ExitProcess(uExitCode);
}

static decltype(TerminateProcess)* real_TerminateProcess = TerminateProcess;
static BOOL WINAPI zzTerminateProcess(HANDLE hProcess, UINT uExitCode) {
    char dbg[256];
    sprintf_s(dbg, "[AION_HOOK_CALL] zzTerminateProcess: hProcess=%p, uExitCode=%u (0x%08X), TID=%lu, isWebPort=%d\n", hProcess, uExitCode, uExitCode, GetCurrentThreadId(), (int)s_isWebPort);
    OutputDebugStringA(dbg);
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed) &&
        (hProcess == NULL || hProcess == GetCurrentProcess() || GetProcessId(hProcess) == GetCurrentProcessId())) {
        if (uExitCode >= 0xC0000000 || uExitCode == 0x40000015) {
            OutputDebugStringA("[AION_VERSION_DLL] WebPort: Fatal exception TerminateProcess detected. Forwarding.\n");
            return real_TerminateProcess(hProcess, uExitCode);
        }
        RecordInterceptedPlayerExit(2, "TerminateProcess(self)");
        WebPortPreventMainThreadExit(uExitCode);
        return TRUE;
    }
    return real_TerminateProcess(hProcess, uExitCode);
}

typedef VOID(NTAPI* PFN_RtlExitUserProcess)(UINT uExitCode);
static PFN_RtlExitUserProcess real_RtlExitUserProcess = nullptr;
static VOID NTAPI zzRtlExitUserProcess(UINT uExitCode) {
    char dbg[256];
    sprintf_s(dbg, "[AION_HOOK_CALL] zzRtlExitUserProcess: uExitCode=%u (0x%08X), TID=%lu, isWebPort=%d\n", uExitCode, uExitCode, GetCurrentThreadId(), (int)s_isWebPort);
    OutputDebugStringA(dbg);
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed)) {
        if (uExitCode >= 0xC0000000 || uExitCode == 0x40000015) {
            OutputDebugStringA("[AION_VERSION_DLL] WebPort: Fatal exception RtlExitUserProcess detected. Forwarding.\n");
            real_RtlExitUserProcess(uExitCode);
            return;
        }
        RecordInterceptedPlayerExit(7, "RtlExitUserProcess");
        WebPortPreventMainThreadExit(uExitCode);
        return;
    }
    real_RtlExitUserProcess(uExitCode);
}

typedef LONG(NTAPI* PFN_NtTerminateProcess)(HANDLE ProcessHandle, LONG ExitStatus);
static PFN_NtTerminateProcess real_NtTerminateProcess = nullptr;
static LONG NTAPI zzNtTerminateProcess(HANDLE ProcessHandle, LONG ExitStatus) {
    char dbg[256];
    sprintf_s(dbg, "[AION_HOOK_CALL] zzNtTerminateProcess: ProcessHandle=%p, ExitStatus=0x%08X, TID=%lu, isWebPort=%d\n", ProcessHandle, ExitStatus, GetCurrentThreadId(), (int)s_isWebPort);
    OutputDebugStringA(dbg);
    if (s_isWebPort && !s_adminShutdownRequested.load(std::memory_order_relaxed) &&
        (ProcessHandle == NULL || ProcessHandle == GetCurrentProcess() || GetProcessId(ProcessHandle) == GetCurrentProcessId())) {
        if ((DWORD)ExitStatus >= 0xC0000000 || (DWORD)ExitStatus == 0x40000015) {
            OutputDebugStringA("[AION_VERSION_DLL] WebPort: Fatal exception NtTerminateProcess detected. Forwarding.\n");
            return real_NtTerminateProcess(ProcessHandle, ExitStatus);
        }
        RecordInterceptedPlayerExit(8, "NtTerminateProcess(self)");
        WebPortPreventMainThreadExit((UINT)ExitStatus);
        return 0; // STATUS_SUCCESS
    }
    return real_NtTerminateProcess(ProcessHandle, ExitStatus);
}

extern "C" __declspec(dllexport) void WINAPI RequestHostShutdown(UINT uExitCode) {
    s_adminShutdownRequested.store(true, std::memory_order_release);
    OutputDebugStringA("[AION_VERSION_DLL] WebPort: Administrative Host Shutdown requested.\n");
    if (s_hGameWindow) {
        RemoveWindowSubclass(s_hGameWindow, WebPortSubclassProc, AION_WEBPORT_SUBCLASS_ID);
    }
    if (real_ExitProcess) {
        real_ExitProcess(uExitCode);
    } else {
        ExitProcess(uExitCode);
    }
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
    // Early check for -webPort in raw command line
    LPCWSTR cmdW = GetCommandLineW();
    if (cmdW) {
        std::wstring rawW(cmdW);
        std::transform(rawW.begin(), rawW.end(), rawW.begin(), ::tolower);
        if (rawW.find(L"-webport") != std::wstring::npos) {
            s_isWebPort = true;
            InitializeWebPortHooks();
        }
    }

    // Early language table patch for main module
    PatchLanguageTableInModule(GetModuleHandleW(nullptr));
    BypassCountryCheckInCryEngineModule(GetModuleHandleW(nullptr));
    PatchAllLoadedLanguageModules();

    HMODULE hDinput8 = LoadLibraryW(L"dinput8.dll");
    if (hDinput8) {
        real_DirectInput8Create = (PFN_DirectInput8Create)GetProcAddress(hDinput8, "DirectInput8Create");
    }
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (hNtdll) {
        real_RtlExitUserProcess = (PFN_RtlExitUserProcess)GetProcAddress(hNtdll, "RtlExitUserProcess");
        real_NtTerminateProcess = (PFN_NtTerminateProcess)GetProcAddress(hNtdll, "NtTerminateProcess");
    }

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    InstallIpFix();
    InstallShaderFix();
#if defined(_M_AMD64)
    Install64BitStackFix();
#endif
    if (real_DirectInput8Create) {
        DetourAttach(&(PVOID&)real_DirectInput8Create, zzDirectInput8Create);
    }
    if (real_RtlExitUserProcess) {
        DetourAttach(&(PVOID&)real_RtlExitUserProcess, zzRtlExitUserProcess);
    }
    if (real_NtTerminateProcess) {
        DetourAttach(&(PVOID&)real_NtTerminateProcess, zzNtTerminateProcess);
    }
    DetourAttach(&(PVOID&)real_SetWindowLongA, zzSetWindowLongA);
    DetourAttach(&(PVOID&)real_CreateWindowExA, zzCreateWindowExA);
    DetourAttach(&(PVOID&)real_CreateWindowExW, zzCreateWindowExW);
    DetourAttach(&(PVOID&)real_ShowWindow, zzShowWindow);
    DetourAttach(&(PVOID&)real_SetWindowPos, zzSetWindowPos);
    DetourAttach(&(PVOID&)real_GetCursorPos, zzGetCursorPos);
    DetourAttach(&(PVOID&)real_SetCursorPos, zzSetCursorPos);
    DetourAttach(&(PVOID&)real_ScreenToClient, zzScreenToClient);
    DetourAttach(&(PVOID&)real_ClientToScreen, zzClientToScreen);
    DetourAttach(&(PVOID&)real_GetWindowRect, zzGetWindowRect);
    DetourAttach(&(PVOID&)real_GetAsyncKeyState, zzGetAsyncKeyState);
    DetourAttach(&(PVOID&)real_GetKeyState, zzGetKeyState);
    DetourAttach(&(PVOID&)real_GetForegroundWindow, zzGetForegroundWindow);
    DetourAttach(&(PVOID&)real_GetActiveWindow, zzGetActiveWindow);
    DetourAttach(&(PVOID&)real_GetFocus, zzGetFocus);
    DetourAttach(&(PVOID&)real_SetCursor, zzSetCursor);
    DetourAttach(&(PVOID&)real_LoadLibraryA, zzLoadLibraryA);
    DetourAttach(&(PVOID&)real_LoadLibraryExA, zzLoadLibraryExA);
    DetourAttach(&(PVOID&)real_LoadLibraryW, zzLoadLibraryW);
    DetourAttach(&(PVOID&)real_LoadLibraryExW, zzLoadLibraryExW);
    DetourAttach(&(PVOID&)real_MessageBoxA, zzMessageBoxA);
    DetourAttach(&(PVOID&)real_MessageBoxW, zzMessageBoxW);
    DetourAttach(&(PVOID&)real_GetCommandLineA, zzGetCommandLineA);
    DetourAttach(&(PVOID&)real_GetCommandLineW, zzGetCommandLineW);
    DetourAttach(&(PVOID&)real_PostQuitMessage, zzPostQuitMessage);
    DetourAttach(&(PVOID&)real_DestroyWindow, zzDestroyWindow);
    DetourAttach(&(PVOID&)real_ExitProcess, zzExitProcess);
    DetourAttach(&(PVOID&)real_TerminateProcess, zzTerminateProcess);
    DetourTransactionCommit();

    FixClientStartupWithHighCoreCountCpus();
}

static LONG WINAPI WebPortVectoredExceptionHandler(PEXCEPTION_POINTERS pEx) {
    if (pEx && pEx->ExceptionRecord) {
        DWORD code = pEx->ExceptionRecord->ExceptionCode;
        // Ignore normal C++ exceptions (MSVC throw/catch), thread-name events, and benign RPC statuses
        if (code == 0xE06D7363 || // MSVC C++ Exception
            code == 0x406D1388 || // Thread naming exception
            code == 0x000006BA || // RPC_S_SERVER_UNAVAILABLE
            code == 0x800706BA || // HRESULT from RPC_S_SERVER_UNAVAILABLE
            code == 0x40010006 || // DBG_PRINTEXCEPTION_C
            code == 0x4001000A)   // DBG_PRINTEXCEPTION_WIDE_C
        {
            return EXCEPTION_CONTINUE_SEARCH;
        }

        if (code == 0xC00000FD || code == 0xC0000005 || code == 0xC000001D || code == 0xC0000025 || code == 0xC0000008) {
            char buf[512];
            HMODULE hMod = NULL;
            GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS, (LPCSTR)pEx->ExceptionRecord->ExceptionAddress, &hMod);
            char modName[MAX_PATH] = "Unknown";
            uintptr_t rva = 0;
            if (hMod) {
                GetModuleFileNameA(hMod, modName, MAX_PATH);
                rva = (uintptr_t)pEx->ExceptionRecord->ExceptionAddress - (uintptr_t)hMod;
            }
            sprintf_s(buf, "[AION_CRASH_TRAP] Code=0x%08X at %p (Mod: %s + 0x%zX)! Target=%p, RW=%lu\n",
                code,
                pEx->ExceptionRecord->ExceptionAddress,
                modName,
                rva,
                (void*)pEx->ExceptionRecord->ExceptionInformation[1],
                (ULONG)pEx->ExceptionRecord->ExceptionInformation[0]);
            OutputDebugStringA(buf);

            PVOID frames[16];
            USHORT count = CaptureStackBackTrace(0, 16, frames, NULL);
            for (USHORT i = 0; i < count; i++) {
                HMODULE fMod = NULL;
                GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS, (LPCSTR)frames[i], &fMod);
                char fName[MAX_PATH] = "Unknown";
                uintptr_t fRva = 0;
                if (fMod) {
                    GetModuleFileNameA(fMod, fName, MAX_PATH);
                    fRva = (uintptr_t)frames[i] - (uintptr_t)fMod;
                }
                char frameBuf[512];
                sprintf_s(frameBuf, "  [Frame %u] %p (%s + 0x%zX)\n", i, frames[i], fName, fRva);
                OutputDebugStringA(frameBuf);
            }
        }
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

BOOL WINAPI DllMain(_In_ HINSTANCE hinstDLL, _In_ DWORD fdwReason, _In_ LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        AddVectoredExceptionHandler(1, WebPortVectoredExceptionHandler);
        s_mainThreadId = GetCurrentThreadId();
        DisableThreadLibraryCalls(hinstDLL);

        // Pin version.dll in memory so it is NEVER unloaded by dynamic FreeLibrary calls
        HMODULE hSelf = nullptr;
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN, (LPCWSTR)hinstDLL, &hSelf);

        InstallPatch();

        // Spawn early language monitor thread (surveillance for 30s during client load)
        HANDLE hLangThread = CreateThread(nullptr, 0, [](LPVOID) -> DWORD {
            for (int i = 0; i < 300; i++) {
                PatchAllLoadedLanguageModules();
                if (s_allTargetModulesPatched.load(std::memory_order_relaxed)) {
                    break;
                }
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
