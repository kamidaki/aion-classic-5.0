#include <algorithm>
#include <list>
#include <string>
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  IP Spoofing & Network Hook for Aion Classic Client
// =========================================================================
//  Allows connecting to unofficial/private game servers by spoofing the
//  game server IP as an official one ("70.5.0.18") during client validation,
//  while allowing real TCP connections to the targeted server IP and port.
// =========================================================================

static constexpr char officialIp[] = "70.5.0.18";
static std::list<std::string> possibleConnectIps = {};

static bool contains(const std::list<std::string>& list, const char* element) {
    return !list.empty() && std::find(list.begin(), list.end(), element) != list.end();
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
        VersionLog("[NET] lstrcpynA: spoofing server IP '%s' -> '%s' (validation bypass)", lpString2, officialIp);
        possibleConnectIps.clear();
        return real_lstrcpynA(lpString1, officialIp, iMaxLength);
    }
    return real_lstrcpynA(lpString1, lpString2, iMaxLength);
}

static decltype(connect)* real_connect = connect;
/// Standard TCP connect hook with full telemetry
static int WSAAPI zzconnect(_In_ SOCKET s, _In_reads_bytes_(namelen) const struct sockaddr FAR* name, _In_ int namelen) {
    possibleConnectIps.clear();
    char ipStr[64] = {0};
    u_short port = 0;
    if (name && namelen >= sizeof(sockaddr_in) && name->sa_family == AF_INET) {
        const sockaddr_in* sin = (const sockaddr_in*)name;
        strcpy_s(ipStr, inet_ntoa(sin->sin_addr));
        port = ntohs(sin->sin_port);
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