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

static DWORD WINAPI LoginPatchThread(LPVOID) {
    FILE* logF = nullptr;
    fopen_s(&logF, "version_hook.log", "a");
    if (logF) {
        fprintf(logF, "[version.dll] LoginPatchThread started.\n");
        fflush(logF);
    }

    HMODULE hGame = nullptr;
    for (int i = 0; i < 1800; i++) {
        hGame = GetModuleHandle(L"game.dll");
        if (hGame) break;
        Sleep(100);
    }

    if (!hGame) {
        if (logF) {
            fprintf(logF, "[version.dll] game.dll not found after 180s.\n");
            fclose(logF);
        }
        return 0;
    }

    if (logF) {
        fprintf(logF, "[version.dll] game.dll found at %p. Applying Login Button patch...\n", hGame);
        fflush(logF);
    }

    bool patched = false;
    unsigned char* base = (unsigned char*)hGame;

    // 1. Try direct offset 0x15A125 first
    unsigned char* directTarget = base + 0x15A125;
    if (directTarget[0] == 0x0F && directTarget[1] == 0x85) {
        DWORD oldProtect;
        if (VirtualProtect(directTarget, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
            memset(directTarget, 0x90, 6);
            VirtualProtect(directTarget, 6, oldProtect, &oldProtect);
            FlushInstructionCache(GetCurrentProcess(), directTarget, 6);
            patched = true;
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Login Button JNE at direct offset %p with NOPs!\n", directTarget);
                fflush(logF);
            }
        }
    }

    // 2. Pattern search fallback if direct offset not matched
    if (!patched) {
        MEMORY_BASIC_INFORMATION mbi = {};
        unsigned char* p = base;
        while (VirtualQuery(p, &mbi, sizeof(mbi))) {
            if ((mbi.State == MEM_COMMIT) && 
                (mbi.Protect == PAGE_EXECUTE_READ || mbi.Protect == PAGE_EXECUTE_READWRITE || mbi.Protect == PAGE_EXECUTE_WRITECOPY)) {
                
                unsigned char* block = (unsigned char*)mbi.BaseAddress;
                size_t len = mbi.RegionSize;
                
                for (size_t i = 0; i + 24 < len; i++) {
                    if (block[i] == 0x80 && block[i+1] == 0x3D && block[i+6] == 0x03 &&
                        block[i+7] == 0x0F && block[i+8] == 0xB7 && block[i+9] == 0xF0 &&
                        block[i+10] == 0x66 && block[i+11] == 0x89 && block[i+12] == 0x05 &&
                        block[i+17] == 0x0F && block[i+18] == 0x85) {
                        
                        DWORD oldProtect;
                        if (VirtualProtect(&block[i+17], 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                            memset(&block[i+17], 0x90, 6);
                            VirtualProtect(&block[i+17], 6, oldProtect, &oldProtect);
                            FlushInstructionCache(GetCurrentProcess(), &block[i+17], 6);
                            patched = true;
                            if (logF) {
                                fprintf(logF, "[version.dll] SUCCESS: Patched Login Button JNE at pattern %p with NOPs!\n", &block[i+17]);
                                fflush(logF);
                            }
                        }
                        break;
                    }
                }
            }
            if (patched) break;
            p += mbi.RegionSize;
            if (p < base || p > base + 0x3000000) break;
        }
    }

    // 3. Also set the state variable to 3 (AUTHED_READY)
    unsigned char* stateVar = base + 0x14BB6F8;
    DWORD oldProt;
    if (VirtualProtect(stateVar, 1, PAGE_EXECUTE_READWRITE, &oldProt)) {
        *stateVar = 3;
        VirtualProtect(stateVar, 1, oldProt, &oldProt);
        if (logF) {
            fprintf(logF, "[version.dll] SUCCESS: Set login state variable at %p to 3 (AUTHED_READY)!\n", stateVar);
            fflush(logF);
        }
    }

    if (logF) {
        fclose(logF);
    }
    return 0;
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

    // Launch background thread to hook game.dll login button check
    CreateThread(nullptr, 0, LoginPatchThread, nullptr, 0, nullptr);
}

BOOL WINAPI DllMain(_In_ HINSTANCE hinstDLL, _In_ DWORD fdwReason, _In_ LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
        InstallPatch();
    }
    return TRUE;
}
