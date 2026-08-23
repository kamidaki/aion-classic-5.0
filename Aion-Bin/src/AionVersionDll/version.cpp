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
        fprintf(logF, "[version.dll] game.dll found at %p. Applying Network & Login patches...\n", hGame);
        fflush(logF);
    }

    bool patched = false;
    unsigned char* base = (unsigned char*)hGame;

    // 1. Patch Login Button JNE at 0x15A125 (6 bytes)
    unsigned char* directTarget = base + 0x15A125;
    if (directTarget[0] == 0x0F && directTarget[1] == 0x85) {
        DWORD oldProtect;
        if (VirtualProtect(directTarget, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
            memset(directTarget, 0x90, 6);
            VirtualProtect(directTarget, 6, oldProtect, &oldProtect);
            FlushInstructionCache(GetCurrentProcess(), directTarget, 6);
            patched = true;
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Login Button JNE at %p (0x15A125) with NOPs!\n", directTarget);
                fflush(logF);
            }
        }
    }

    // Pattern search fallback if direct offset not matched
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

    // 2. Socket Guard JEs NOP patch in 0x8439c0 (0x843E42 and 0x843E4B)
    unsigned char* je1 = base + 0x843E42;
    unsigned char* je2 = base + 0x843E4B;
    if (je1[0] == 0x74 && je2[0] == 0x74) {
        DWORD oldP;
        if (VirtualProtect(je1, 16, PAGE_EXECUTE_READWRITE, &oldP)) {
            je1[0] = 0x90; je1[1] = 0x90;
            je2[0] = 0x90; je2[1] = 0x90;
            VirtualProtect(je1, 16, oldP, &oldP);
            FlushInstructionCache(GetCurrentProcess(), je1, 16);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Socket Guard JEs at %p and %p with NOPs!\n", je1, je2);
                fflush(logF);
            }
        }
    }

    // 3. Socket State Guard NOP patch in 0x845150 (0x845207: 0F 84 8C 00 00 00 -> 6 NOPs)
    // This allows SendPacket to execute without aborting when socket state is pending/unacknowledged
    unsigned char* sendGate1 = base + 0x845207;
    if (sendGate1[0] == 0x0F && sendGate1[1] == 0x84) {
        DWORD oldP;
        if (VirtualProtect(sendGate1, 6, PAGE_EXECUTE_READWRITE, &oldP)) {
            memset(sendGate1, 0x90, 6);
            VirtualProtect(sendGate1, 6, oldP, &oldP);
            FlushInstructionCache(GetCurrentProcess(), sendGate1, 6);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched SendPacket Gate at %p (0x845207) with NOPs!\n", sendGate1);
                fflush(logF);
            }
        }
    }

    // 4. Socket Send Gate NOP patch in 0x88F250 (0x88F26C: 74 6F -> 90 90)
    // This allows raw TCP send() to execute without being dropped by the unacknowledged socket state check
    unsigned char* sendGate2 = base + 0x88F26C;
    if (sendGate2[0] == 0x74 && sendGate2[1] == 0x6F) {
        DWORD oldP;
        if (VirtualProtect(sendGate2, 2, PAGE_EXECUTE_READWRITE, &oldP)) {
            sendGate2[0] = 0x90;
            sendGate2[1] = 0x90;
            VirtualProtect(sendGate2, 2, oldP, &oldP);
            FlushInstructionCache(GetCurrentProcess(), sendGate2, 2);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Socket Send Gate at %p (0x88F26C) with NOPs!\n", sendGate2);
                fflush(logF);
            }
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

    // Launch background thread to hook game.dll login button & network socket gates
    CreateThread(nullptr, 0, LoginPatchThread, nullptr, 0, nullptr);
}

BOOL WINAPI DllMain(_In_ HINSTANCE hinstDLL, _In_ DWORD fdwReason, _In_ LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
        InstallPatch();
    }
    return TRUE;
}
