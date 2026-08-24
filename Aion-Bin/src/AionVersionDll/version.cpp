#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include "exports.h"
#include <stdio.h>
#include <stdarg.h>
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

typedef void (*Fn_SubmitCredentials)(void* pThis, const wchar_t* username, const wchar_t* password, int flag);
static Fn_SubmitCredentials real_SubmitCredentials = nullptr;

static void hooked_SubmitCredentials(void* pThis, const wchar_t* username, const wchar_t* password, int flag) {
    FILE* logF = nullptr;
    fopen_s(&logF, "version_hook.log", "a");
    if (logF) {
        fprintf(logF, "[version.dll] >>> HOOK: SubmitCredentials(this=%p, user='%ls', flag=%d)\n",
            pThis, username ? username : L"(null)", flag);
        fclose(logF);
    }
    real_SubmitCredentials(pThis, username, password, flag);
}

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

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    real_SubmitCredentials = (Fn_SubmitCredentials)(base + 0x1419C0);
    DetourAttach(&(PVOID&)real_SubmitCredentials, hooked_SubmitCredentials);
    DetourTransactionCommit();

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

    // 1b. Variavel de estado do login em 0x14BB6F8 = 3 (AUTHED_READY).
    //
    // Este patch existia SO no binario distribuido: nenhuma versao do version.cpp no historico o
    // tem, e a compilacao a partir do fonte o perdia. Descoberto comparando o version_hook.log da
    // DLL distribuida (que registra "Set login state variable ... to 3") com o da recompilada
    // (que nao registra). O commit 8bc6c18 descreve o offset.
    {
        unsigned int* estadoLogin = (unsigned int*)(base + 0x14BB6F8);
        DWORD oldProtect;
        if (VirtualProtect(estadoLogin, sizeof(unsigned int), PAGE_EXECUTE_READWRITE, &oldProtect)) {
            *estadoLogin = 3;
            VirtualProtect(estadoLogin, sizeof(unsigned int), oldProtect, &oldProtect);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Set login state variable at %p to 3 (AUTHED_READY)!\n", estadoLogin);
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

    // 5. Direct Login Gate at 0x12247E (74 33 -> EB 33)
    // Forces the client to take the direct credentials extraction path instead of the GF STS path
    unsigned char* directLoginGate = base + 0x12247E;
    if (directLoginGate[0] == 0x74 && directLoginGate[1] == 0x33) {
        DWORD oldP;
        if (VirtualProtect(directLoginGate, 2, PAGE_EXECUTE_READWRITE, &oldP)) {
            directLoginGate[0] = 0xEB; // JMP short 0x1224B3
            VirtualProtect(directLoginGate, 2, oldP, &oldP);
            FlushInstructionCache(GetCurrentProcess(), directLoginGate, 2);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Direct Login Gate at %p (0x12247E) to unconditional JMP!\n", directLoginGate);
                fflush(logF);
            }
        }
    }

    // 6. Direct Credentials Extraction Gate at 0x122515 (0F 84 74 01 00 00 -> 6 NOPs)
    // Prevents jumping to the legacy server table check and forces direct extraction of account & password
    unsigned char* extractGate = base + 0x122515;
    if (extractGate[0] == 0x0F && extractGate[1] == 0x84) {
        DWORD oldP;
        if (VirtualProtect(extractGate, 6, PAGE_EXECUTE_READWRITE, &oldP)) {
            memset(extractGate, 0x90, 6);
            VirtualProtect(extractGate, 6, oldP, &oldP);
            FlushInstructionCache(GetCurrentProcess(), extractGate, 6);
            if (logF) {
                fprintf(logF, "[version.dll] SUCCESS: Patched Direct Credentials Extraction Gate at %p (0x122515) with NOPs!\n", extractGate);
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

// =====================================================================================
// Instrumentacao de socket.
//
// Existe para responder UMA pergunta: o cliente le o socket de login?
//
// Medido pela janela do TCP, ele nao le -- em 10 conexoes os bytes do servidor ficaram
// parados no buffer, nas portas 2106 e 13001. Mas a janela so diz que ninguem consumiu;
// nao diz se o cliente chegou a CHAMAR recv e falhou, ou se nunca chamou.
//
// Estes hooks separam os dois casos. Se `recv`/`WSARecv` aparecerem no log com o socket
// da conexao de login, ele tenta ler e algo falha. Se nao aparecerem, o socket nunca e
// atendido -- e o problema esta antes, na maquina de estados do cliente.
// =====================================================================================

static void SockLog(const char* fmt, ...) {
    FILE* f = nullptr;
    fopen_s(&f, "version_hook.log", "a");
    if (!f) return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(f, fmt, ap);
    va_end(ap);
    fflush(f);
    fclose(f);
}

typedef int (WSAAPI* Fn_connect)(SOCKET, const struct sockaddr*, int);
typedef int (WSAAPI* Fn_recv)(SOCKET, char*, int, int);
typedef int (WSAAPI* Fn_send)(SOCKET, const char*, int, int);
typedef int (WSAAPI* Fn_WSARecv)(SOCKET, LPWSABUF, DWORD, LPDWORD, LPDWORD, LPWSAOVERLAPPED, LPWSAOVERLAPPED_COMPLETION_ROUTINE);
typedef int (WSAAPI* Fn_WSASend)(SOCKET, LPWSABUF, DWORD, LPDWORD, DWORD, LPWSAOVERLAPPED, LPWSAOVERLAPPED_COMPLETION_ROUTINE);
typedef int (WSAAPI* Fn_closesocket)(SOCKET);

static Fn_connect     real_connect     = connect;
static Fn_recv        real_recv        = recv;
static Fn_send        real_send        = send;
static Fn_WSARecv     real_WSARecv     = WSARecv;
static Fn_WSASend     real_WSASend     = WSASend;
static Fn_closesocket real_closesocket = closesocket;

static int WSAAPI hooked_connect(SOCKET s, const struct sockaddr* name, int namelen) {
    if (name && name->sa_family == AF_INET) {
        const sockaddr_in* a = (const sockaddr_in*)name;
        unsigned char* ip = (unsigned char*)&a->sin_addr;
        SockLog("[version.dll] connect(socket=%llu, IP=%u.%u.%u.%u, Port=%u)\n",
                (unsigned long long)s, ip[0], ip[1], ip[2], ip[3], ntohs(a->sin_port));
    }
    return real_connect(s, name, namelen);
}

static int WSAAPI hooked_recv(SOCKET s, char* buf, int len, int flags) {
    int r = real_recv(s, buf, len, flags);
    if (r == SOCKET_ERROR) {
        // 10035 = WSAEWOULDBLOCK, nao ha dado AINDA (socket nao-bloqueante)
        // 10053 = conexao abortada pelo proprio processo
        // 10054 = conexao resetada pelo outro lado
        // 10060 = timeout
        int err = WSAGetLastError();
        SockLog("[version.dll] recv(socket=%llu, pediu=%d) -> FALHOU WSA=%d\n",
                (unsigned long long)s, len, err);
        WSASetLastError(err);
    } else {
        SockLog("[version.dll] recv(socket=%llu, pediu=%d) -> %d\n",
                (unsigned long long)s, len, r);
    }
    return r;
}

static int WSAAPI hooked_WSARecv(SOCKET s, LPWSABUF bufs, DWORD count, LPDWORD recvd,
                                 LPDWORD flags, LPWSAOVERLAPPED ov,
                                 LPWSAOVERLAPPED_COMPLETION_ROUTINE cr) {
    int r = real_WSARecv(s, bufs, count, recvd, flags, ov, cr);
    if (r == SOCKET_ERROR) {
        int err = WSAGetLastError();
        SockLog("[version.dll] WSARecv(socket=%llu, buffers=%lu) -> FALHOU WSA=%d\n",
                (unsigned long long)s, count, err);
        WSASetLastError(err);
    } else {
        SockLog("[version.dll] WSARecv(socket=%llu, buffers=%lu) -> %d, recebeu=%lu\n",
                (unsigned long long)s, count, r, recvd ? *recvd : 0);
    }
    return r;
}

static int WSAAPI hooked_send(SOCKET s, const char* buf, int len, int flags) {
    SockLog("[version.dll] send(socket=%llu, len=%d, primeiro=0x%02X)\n",
            (unsigned long long)s, len, len > 0 ? (unsigned char)buf[0] : 0);
    return real_send(s, buf, len, flags);
}

static int WSAAPI hooked_WSASend(SOCKET s, LPWSABUF bufs, DWORD count, LPDWORD sent,
                                 DWORD flags, LPWSAOVERLAPPED ov,
                                 LPWSAOVERLAPPED_COMPLETION_ROUTINE cr) {
    unsigned long total = 0;
    unsigned char primeiro = 0;
    if (bufs && count > 0) {
        for (DWORD i = 0; i < count; i++) total += bufs[i].len;
        if (bufs[0].len > 0 && bufs[0].buf) primeiro = (unsigned char)bufs[0].buf[0];
    }
    SockLog("[version.dll] WSASend(socket=%llu, len=%lu, opcode=0x%02X)\n",
            (unsigned long long)s, total, primeiro);
    return real_WSASend(s, bufs, count, sent, flags, ov, cr);
}

static int WSAAPI hooked_closesocket(SOCKET s) {
    SockLog("[version.dll] closesocket(socket=%llu)\n", (unsigned long long)s);
    return real_closesocket(s);
}

static void InstallSocketInstrumentation() {
    DetourAttach(&(PVOID&)real_connect, hooked_connect);
    DetourAttach(&(PVOID&)real_recv, hooked_recv);
    DetourAttach(&(PVOID&)real_send, hooked_send);
    DetourAttach(&(PVOID&)real_WSARecv, hooked_WSARecv);
    DetourAttach(&(PVOID&)real_WSASend, hooked_WSASend);
    DetourAttach(&(PVOID&)real_closesocket, hooked_closesocket);
}

static void InstallPatch() {
    PreloadDXVK();

    DetourTransactionBegin();
    DetourUpdateThread(GetCurrentThread());
    InstallIpFix();
    InstallGraphicsOptionsFixAndCameraFix();
    InstallShaderFix();
    InstallSocketInstrumentation();
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
