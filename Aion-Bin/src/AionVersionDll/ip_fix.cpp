#include <algorithm>
#include <list>
#include <string>
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  IP Spoofing & Dynamic Network Hook for Aion Classic Client
// =========================================================================
//  Allows connecting to unofficial/private game servers by:
//  1. Spoofing the game server IP as official ("70.5.0.18") during internal
//     client validation (lstrcpynA).
//  2. Transparently redirecting any hardcoded official IPs to the private
//     emulator IP configured in the command line (-ip:<addr>).
//  3. Logging all TCP network operations with high precision.
// =========================================================================

static constexpr char kDefaultOfficialIp[] = "70.5.0.18";

// Lista de IPs oficiais históricos e Gameforge para reconhecimento automático
static const char* const kOfficialIps[] = {
    "70.5.0.18",      // Official NCSoft Auth / Game server IP
    "79.110.83.80",   // Official Gameforge Classic EU Login
    "79.110.83.60",   // Official Gameforge Classic EU Auth
    "79.110.83.18",   // Official Gameforge Classic EU Game
    "79.110.83.10",   // Official Gameforge Classic EU Portal
    "79.110.83.75",   // Official Gameforge Classic EU Secondary
};

static std::list<std::string> possibleConnectIps = {};

static bool contains(const std::list<std::string>& list, const char* element) {
    return !list.empty() && std::find(list.begin(), list.end(), element) != list.end();
}

static bool isOfficialIp(const char* ip) {
    if (!ip) return false;
    for (const char* off : kOfficialIps) {
        if (_stricmp(ip, off) == 0) return true;
    }
    return false;
}

static std::string GetTargetEmulatorIp() {
    LPCSTR cmd = GetCommandLineA();
    if (cmd) {
        const char* p = strstr(cmd, "-ip:");
        if (p) {
            p += 4;
            std::string ip;
            while (*p && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n' && *p != '"') {
                ip.push_back(*p++);
            }
            if (!ip.empty()) return ip;
        }
    }
    return "127.0.0.1";
}

static decltype(inet_ntoa)* real_inet_ntoa = inet_ntoa;
/// Gathers game server IPs from the server list
static char* WINAPI zzinet_ntoa(_In_ struct in_addr in) {
    char* addr = real_inet_ntoa(in);
    if (addr && !contains(possibleConnectIps, addr)) {
        possibleConnectIps.push_back(addr);
        VersionLog("[NET] inet_ntoa: registered candidate game server IP '%s'", addr);
    }
    return addr;
}

static decltype(lstrcpynA)* real_lstrcpynA = lstrcpynA;
/// Spoofs the IP copy when the client validates the server list entry against official network bounds
static LPSTR WINAPI zzlstrcpynA(_Out_writes_(iMaxLength) LPSTR lpString1, _In_ LPCSTR lpString2, _In_ int iMaxLength) {
    if (iMaxLength == 256 && lpString2 && contains(possibleConnectIps, lpString2)) {
        VersionLog("[NET] lstrcpynA: spoofing server IP '%s' -> '%s' (validation bypass)", lpString2, kDefaultOfficialIp);
        possibleConnectIps.clear();
        return real_lstrcpynA(lpString1, kDefaultOfficialIp, iMaxLength);
    }
    return real_lstrcpynA(lpString1, lpString2, iMaxLength);
}

static decltype(connect)* real_connect = connect;
/// Standard TCP connect hook with dynamic official IP redirection and full telemetry
static int WSAAPI zzconnect(_In_ SOCKET s, _In_reads_bytes_(namelen) const struct sockaddr FAR* name, _In_ int namelen) {
    possibleConnectIps.clear();
    char ipStr[64] = {0};
    u_short port = 0;
    struct sockaddr_in redirectedSin;

    if (name && namelen >= (int)sizeof(sockaddr_in) && name->sa_family == AF_INET) {
        const sockaddr_in* sin = (const sockaddr_in*)name;
        strcpy_s(ipStr, inet_ntoa(sin->sin_addr));
        port = ntohs(sin->sin_port);

        // Se o cliente tentar conectar a qualquer IP oficial conhecido (ex: fallback hardcoded),
        // redireciona de forma transparente para o IP do emulador privado informado no .bat
        if (isOfficialIp(ipStr)) {
            std::string targetIp = GetTargetEmulatorIp();
            VersionLog("[NET] connect() redirecting official IP '%s' -> private emulator IP '%s' (Port %u)",
                ipStr, targetIp.c_str(), port);

            memcpy(&redirectedSin, name, sizeof(sockaddr_in));
            redirectedSin.sin_addr.s_addr = inet_addr(targetIp.c_str());
            name = (const struct sockaddr*)&redirectedSin;
            strcpy_s(ipStr, targetIp.c_str());
        }

        VersionLog("[NET] connect() initiating: socket=%llu, Dest IP=%s, Port=%u",
            (unsigned long long)s, ipStr, port);
    } else {
        VersionLog("[NET] connect() initiating: socket=%llu, namelen=%d", (unsigned long long)s, namelen);
    }

    int result = real_connect(s, name, namelen);
    if (result == SOCKET_ERROR) {
        int err = WSAGetLastError();
        VersionLog("[NET] connect() socket=%llu to %s:%u -> FAILED (WSA Error=%d)",
            (unsigned long long)s, ipStr, port, err);
        WSASetLastError(err);
    } else {
        VersionLog("[NET] connect() socket=%llu to %s:%u -> SUCCESS",
            (unsigned long long)s, ipStr, port);
    }
    return result;
}

static decltype(send)* real_send = send;
static int WSAAPI zzsend(_In_ SOCKET s, _In_reads_bytes_(len) const char FAR* buf, _In_ int len, _In_ int flags) {
    int r = real_send(s, buf, len, flags);
    if (r == SOCKET_ERROR) {
        int err = WSAGetLastError();
        VersionLog("[NET] send() socket=%llu, len=%d -> ERROR (WSA Error=%d)", (unsigned long long)s, len, err);
        WSASetLastError(err);
    } else {
        unsigned char op = (len > 2 && buf) ? (unsigned char)buf[2] : 0;
        VersionLog("[NET] send() socket=%llu, bytesSent=%d, opcode=0x%02X", (unsigned long long)s, r, op);
    }
    return r;
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
    int r = real_WSASend(s, lpBuffers, dwBufferCount, lpNumberOfBytesSent, dwFlags, lpOverlapped, lpCompletionRoutine);
    DWORD total = 0;
    unsigned char op = 0;
    if (lpBuffers && dwBufferCount > 0) {
        for (DWORD i = 0; i < dwBufferCount; i++) total += lpBuffers[i].len;
        if (lpBuffers[0].len > 2 && lpBuffers[0].buf) op = (unsigned char)lpBuffers[0].buf[2];
    }
    if (r == SOCKET_ERROR) {
        int err = WSAGetLastError();
        VersionLog("[NET] WSASend() socket=%llu, totalLen=%lu -> ERROR (WSA Error=%d)", (unsigned long long)s, total, err);
        WSASetLastError(err);
    } else {
        VersionLog("[NET] WSASend() socket=%llu, totalLen=%lu, opcode=0x%02X, sent=%lu",
            (unsigned long long)s, total, op, lpNumberOfBytesSent ? *lpNumberOfBytesSent : total);
    }
    return r;
}

static decltype(recv)* real_recv = recv;
static int WSAAPI zzrecv(_In_ SOCKET s, _Out_writes_bytes_to_(len, return) char FAR* buf, _In_ int len, _In_ int flags) {
    int r = real_recv(s, buf, len, flags);
    if (r == SOCKET_ERROR) {
        int err = WSAGetLastError();
        if (err != WSAEWOULDBLOCK) {
            VersionLog("[NET] recv() socket=%llu, requested=%d -> ERROR (WSA Error=%d)", (unsigned long long)s, len, err);
        }
        WSASetLastError(err);
    } else if (r > 0) {
        unsigned char op = (r > 2 && buf) ? (unsigned char)buf[2] : 0;
        VersionLog("[NET] recv() socket=%llu, recvd=%d, opcode=0x%02X", (unsigned long long)s, r, op);
    }
    return r;
}

static decltype(WSARecv)* real_WSARecv = WSARecv;
static int WSAAPI zzWSARecv(
    _In_ SOCKET s,
    _In_reads_(dwBufferCount) LPWSABUF lpBuffers,
    _In_ DWORD dwBufferCount,
    _Out_opt_ LPDWORD lpNumberOfBytesRecvd,
    _Inout_ LPDWORD lpFlags,
    _Inout_opt_ LPWSAOVERLAPPED lpOverlapped,
    _In_opt_ LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine
) {
    int r = real_WSARecv(s, lpBuffers, dwBufferCount, lpNumberOfBytesRecvd, lpFlags, lpOverlapped, lpCompletionRoutine);
    if (r == SOCKET_ERROR) {
        int err = WSAGetLastError();
        if (err != WSAEWOULDBLOCK) {
            VersionLog("[NET] WSARecv() socket=%llu -> ERROR (WSA Error=%d)", (unsigned long long)s, err);
        }
        WSASetLastError(err);
    } else {
        DWORD recvd = lpNumberOfBytesRecvd ? *lpNumberOfBytesRecvd : 0;
        unsigned char op = 0;
        if (recvd > 2 && lpBuffers && dwBufferCount > 0 && lpBuffers[0].buf) {
            op = (unsigned char)lpBuffers[0].buf[2];
        }
        VersionLog("[NET] WSARecv() socket=%llu, recvd=%lu, opcode=0x%02X", (unsigned long long)s, recvd, op);
    }
    return r;
}

static decltype(closesocket)* real_closesocket = closesocket;
static int WSAAPI zzclosesocket(_In_ SOCKET s) {
    VersionLog("[NET] closesocket() socket=%llu closed", (unsigned long long)s);
    return real_closesocket(s);
}

/// Installs IP-Fix and Socket hooks
void InstallIpFix() {
    DetourAttach(&(PVOID&)real_inet_ntoa, zzinet_ntoa);
    DetourAttach(&(PVOID&)real_lstrcpynA, zzlstrcpynA);
    DetourAttach(&(PVOID&)real_connect, zzconnect);
    DetourAttach(&(PVOID&)real_send, zzsend);
    DetourAttach(&(PVOID&)real_WSASend, zzWSASend);
    DetourAttach(&(PVOID&)real_recv, zzrecv);
    DetourAttach(&(PVOID&)real_WSARecv, zzWSARecv);
    DetourAttach(&(PVOID&)real_closesocket, zzclosesocket);
    VersionLog("[INIT] Network & IP-Fix hooks installed successfully.");
}