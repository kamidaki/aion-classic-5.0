#include <algorithm>
#include <list>
#include <string>
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include "detours.h"

static decltype(connect)* real_connect = connect;
static int WSAAPI zzconnect(_In_ SOCKET s, _In_reads_bytes_(namelen) const struct sockaddr FAR* name, _In_ int namelen) {
    if (name && namelen >= sizeof(sockaddr_in)) {
        sockaddr_in sin = *(const sockaddr_in*)name;
        char ipBuf[64] = {0};
        strcpy_s(ipBuf, inet_ntoa(sin.sin_addr));
        u_short port = ntohs(sin.sin_port);

        // Portas do emulador que NAO podem ser desviadas.
        //
        // A regra abaixo forcava para 2106 toda conexao de loopback que nao fosse 7777 ou 10241.
        // Com isso a 6600 caia na rede: o cliente tentava abrir o STS e ia parar no login server.
        //
        // Isso importa porque, na captura do servidor oficial, o cliente **so responde ao HQ
        // depois que o STS termina** -- ele recebe o AUTH_GREETING na 13001, abre a 6600 0,18s
        // depois, faz ~3s de handshake e so entao manda as credenciais na 13001. Sem STS ele fica
        // esperando para sempre, que e exatamente o travamento observado.
        const bool porta_do_emulador =
            port == 7777 || port == 10241 || port == 2106 || port == 6600 || port == 13001;

        if ((strcmp(ipBuf, "127.0.0.1") == 0 || strcmp(ipBuf, "0.0.0.0") == 0) && !porta_do_emulador) {
            port = 2106;
            sin.sin_port = htons(2106);
        }

        FILE* logF = nullptr;
        fopen_s(&logF, "version_hook.log", "a");
        if (logF) {
            fprintf(logF, "[version.dll] connect(socket=%llu, IP=%s, Port=%u)\n", (unsigned long long)s, ipBuf, port);
            fclose(logF);
        }
        return real_connect(s, (const sockaddr*)&sin, sizeof(sin));
    }
    return real_connect(s, name, namelen);
}

static decltype(send)* real_send = send;
static int WSAAPI zzsend(_In_ SOCKET s, _In_reads_bytes_(len) const char FAR* buf, _In_ int len, _In_ int flags) {
    FILE* logF = nullptr;
    fopen_s(&logF, "version_hook.log", "a");
    if (logF) {
        fprintf(logF, "[version.dll] send(socket=%llu, len=%d, opcode=0x%02X)\n", 
            (unsigned long long)s, len, (len > 2 ? (unsigned char)buf[2] : 0));
        fclose(logF);
    }
    return real_send(s, buf, len, flags);
}

static decltype(WSASend)* real_WSASend = WSASend;
static int WSAAPI zzWSASend(
    _In_ SOCKET s,
    _In_reads_(dwBufferCount) LPWSABUF lpBuffers,
    _In_ DWORD dwBufferCount,
    _Out_opt_ LPDWORD lpNumberOfBytesSent,
    _In_ DWORD dwFlags,
    _Inout_opt_ LPWSAOVERLAPPED lpOverlapped,
    _In_opt_ LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine
) {
    FILE* logF = nullptr;
    fopen_s(&logF, "version_hook.log", "a");
    if (logF) {
        DWORD totalLen = 0;
        unsigned char firstOp = 0;
        if (lpBuffers && dwBufferCount > 0) {
            totalLen = lpBuffers[0].len;
            if (lpBuffers[0].len > 2) {
                firstOp = (unsigned char)lpBuffers[0].buf[2];
            }
        }
        fprintf(logF, "[version.dll] WSASend(socket=%llu, len=%lu, opcode=0x%02X)\n", 
            (unsigned long long)s, totalLen, firstOp);
        fclose(logF);
    }
    return real_WSASend(s, lpBuffers, dwBufferCount, lpNumberOfBytesSent, dwFlags, lpOverlapped, lpCompletionRoutine);
}

/// Allows connecting to unofficial game servers without altering loopback IPs
void InstallIpFix() {
    DetourAttach(&(PVOID&)real_connect, zzconnect);
    DetourAttach(&(PVOID&)real_send, zzsend);
    DetourAttach(&(PVOID&)real_WSASend, zzWSASend);
}