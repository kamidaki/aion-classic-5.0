#include "exports.h"
#include <stdio.h>
#include "detours.h"

static bool s_gfxEnabled = false;

static void EnableHighQualityGraphicsOptions() {
    MEMORY_BASIC_INFORMATION mbi = {};
    if (!VirtualQuery(GetModuleHandle(L"crysystem") + 0x1000, &mbi, sizeof(mbi))) {
        return;
    }

    if (!(mbi.AllocationProtect & 0xF0)) {
        return;
    }

    DWORD oldProtect;
    if (!VirtualProtect(mbi.BaseAddress, mbi.RegionSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        return;
    }

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

void InstallOrUpdateCameraFix(HWND hWnd);
void InstallIpFix();
void InstallShaderFix();
void Install64BitStackFix();

static bool s_loginFixInstalled = false;

static void InstallLoginButtonFix() {
    HMODULE hGame = GetModuleHandle(L"game.dll");
    if (!hGame) {
        return;
    }

    MEMORY_BASIC_INFORMATION mbi = {};
    unsigned char* p = (unsigned char*)hGame;
    
    // Scan executable sections of game.dll
    while (VirtualQuery(p, &mbi, sizeof(mbi))) {
        if ((mbi.State == MEM_COMMIT) && 
            (mbi.Protect == PAGE_EXECUTE_READ || mbi.Protect == PAGE_EXECUTE_READWRITE || mbi.Protect == PAGE_EXECUTE_WRITECOPY)) {
            
            unsigned char* block = (unsigned char*)mbi.BaseAddress;
            size_t len = mbi.RegionSize;
            
            for (size_t i = 0; i + 24 < len; i++) {
                // Pattern at 0x15A110:
                // 80 3D xx xx xx xx 03 0F B7 F0 66 89 05 xx xx xx xx 0F 85
                if (block[i] == 0x80 && block[i+1] == 0x3D && block[i+6] == 0x03 &&
                    block[i+7] == 0x0F && block[i+8] == 0xB7 && block[i+9] == 0xF0 &&
                    block[i+10] == 0x66 && block[i+11] == 0x89 && block[i+12] == 0x05 &&
                    block[i+17] == 0x0F && block[i+18] == 0x85) {
                    
                    DWORD oldProtect;
                    if (VirtualProtect(&block[i+17], 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        // NOP out the 6-byte conditional jump: 0F 85 xx xx xx xx -> 90 90 90 90 90 90
                        memset(&block[i+17], 0x90, 6);
                        VirtualProtect(&block[i+17], 6, oldProtect, &oldProtect);
                        FlushInstructionCache(GetCurrentProcess(), &block[i+17], 6);
                    }
                    return;
                }
            }
        }
        p += mbi.RegionSize;
        if (p < (unsigned char*)hGame || p > (unsigned char*)hGame + 0x3000000) {
            break;
        }
    }
}

static decltype(SetWindowLongA)* real_SetWindowLongA = SetWindowLongA;
static LONG WINAPI zzSetWindowLongA(_In_ HWND hWnd, _In_ int nIndex, _In_ LONG dwNewLong) {
    if (!s_gfxEnabled) {
        EnableHighQualityGraphicsOptions();
        s_gfxEnabled = true;
    }
    if (!s_loginFixInstalled) {
        InstallLoginButtonFix();
        s_loginFixInstalled = true;
    }
    InstallOrUpdateCameraFix(hWnd);
    return real_SetWindowLongA(hWnd, nIndex, dwNewLong);
}


static void PreloadDXVK() {
    LoadLibrary(L"d3d9.dll");
}

static void InstallGraphicsOptionsFixAndCameraFix() {
    // enable disabled graphics settings on high resolutions and install camera fix
    DetourAttach(&(PVOID&)real_SetWindowLongA, zzSetWindowLongA);
}

static void FixClientStartupWithHighCoreCountCpus() {
    SYSTEM_INFO info;
    GetSystemInfo(&info);
    if (info.dwNumberOfProcessors >= 32) {
        int maxCpu = min(64, info.dwNumberOfProcessors) - 1;
        DWORD_PTR mask = (1ULL << maxCpu) - 1;
        SetProcessAffinityMask(GetCurrentProcess(), mask);
    }
}

static void InstallPatch() {
    PreloadDXVK();

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    InstallIpFix();
    InstallGraphicsOptionsFixAndCameraFix();
    InstallShaderFix();
#if defined(_M_AMD64)
    Install64BitStackFix();
#endif
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
