#include <algorithm>
#include <string>
#include <cstring>
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <windows.h>
#include "exports.h"
#include "detours.h"

// =========================================================================
//  IP Spoofing & Official IP Pool for Aion Classic Client
// =========================================================================
//  Allows connecting to unofficial/private game servers by spoofing the
//  server IP as an official recognized one from the pool.
//  Includes all official NCSoft, Gameforge Classic 4.5 captures, and CHS IPs.
// =========================================================================

// Official Master IP Pool
static const char* const kOfficialIpPool[] = {
    "70.5.0.18",       // NCSoft Official Main (Classic NA/KR)
    "79.110.83.115",   // Gameforge Official Classic EU Game Server (Port 7777 - Wireshark Capture)
    "79.110.83.118",   // Gameforge Official STS Auth Gateway (Port 6600 - Wireshark Capture)
    "79.110.83.156",   // Gameforge Official HQ Services / Shop (Port 13001 - Wireshark Capture)
    "79.110.83.80",    // Gameforge Official Login Server (Port 2106)
    "79.110.83.60",    // Gameforge Official Auth / Portal
    "79.110.83.18",    // Gameforge Official Classic Game Gateway
    "79.110.83.10",    // Gameforge Official Web / Portal
    "79.110.83.75",    // Gameforge Official Chat / Community
    "106.54.175.178",  // Shanda / Tencent CHS Classic Official Gateway
    "150.158.219.159", // Shanda / Tencent CHS NP Gateway
    "64.25.35.100",    // NCSoft NA Master Auth
    "64.25.35.103",    // NCSoft NA Game Cluster
};

static constexpr char kPrimaryOfficialIp[] = "70.5.0.18";

// Zero-allocation, thread-safe candidate IP cache
static constexpr size_t MAX_CANDIDATE_IPS = 16;
static char s_candidateIps[MAX_CANDIDATE_IPS][32] = {};
static size_t s_candidateIpCount = 0;
static SRWLOCK s_candidateIpLock = SRWLOCK_INIT;

static bool HasCandidateIp(const char* ip) {
    if (!ip || !ip[0]) return false;
    AcquireSRWLockShared(&s_candidateIpLock);
    for (size_t i = 0; i < s_candidateIpCount; ++i) {
        if (strncmp(s_candidateIps[i], ip, 32) == 0) {
            ReleaseSRWLockShared(&s_candidateIpLock);
            return true;
        }
    }
    ReleaseSRWLockShared(&s_candidateIpLock);
    return false;
}

static void AddCandidateIp(const char* ip) {
    if (!ip || !ip[0]) return;
    AcquireSRWLockExclusive(&s_candidateIpLock);
    for (size_t i = 0; i < s_candidateIpCount; ++i) {
        if (strncmp(s_candidateIps[i], ip, 32) == 0) {
            ReleaseSRWLockExclusive(&s_candidateIpLock);
            return;
        }
    }
    if (s_candidateIpCount < MAX_CANDIDATE_IPS) {
        strncpy_s(s_candidateIps[s_candidateIpCount], ip, sizeof(s_candidateIps[s_candidateIpCount]) - 1);
        s_candidateIps[s_candidateIpCount][sizeof(s_candidateIps[s_candidateIpCount]) - 1] = '\0';
        s_candidateIpCount++;
    }
    ReleaseSRWLockExclusive(&s_candidateIpLock);
}

static void ClearCandidateIps() {
    AcquireSRWLockExclusive(&s_candidateIpLock);
    s_candidateIpCount = 0;
    ReleaseSRWLockExclusive(&s_candidateIpLock);
}

/// Checks if an IP is part of the recognized official server pool or official subnets
static bool isOfficialIp(const char* ip) {
    if (!ip) return false;
    for (const char* off : kOfficialIpPool) {
        if (_stricmp(ip, off) == 0) return true;
    }
    // Subnet check for Gameforge dedicated block (79.110.83.*)
    if (strncmp(ip, "79.110.83.", 10) == 0) return true;
    return false;
}

static decltype(inet_ntoa)* real_inet_ntoa = inet_ntoa;
/// Gathers candidate game server IPs from the server list
static char* WINAPI zzinet_ntoa(_In_ struct in_addr in) {
    char* addr = real_inet_ntoa(in);
    if (addr) {
        AddCandidateIp(addr);
    }
    return addr;
}

static decltype(lstrcpynA)* real_lstrcpynA = lstrcpynA;
/// Spoofs the IP copy when the client validates the server list entry against official network bounds
static LPSTR WINAPI zzlstrcpynA(_Out_writes_(iMaxLength) LPSTR lpString1, _In_ LPCSTR lpString2, _In_ int iMaxLength) {
    if (iMaxLength == 256 && lpString2) {
        if (HasCandidateIp(lpString2)) {
            ClearCandidateIps();
            return real_lstrcpynA(lpString1, kPrimaryOfficialIp, iMaxLength);
        }
    }
    return real_lstrcpynA(lpString1, lpString2, iMaxLength);
}

static decltype(gethostbyname)* real_gethostbyname = gethostbyname;
static struct hostent* WSAAPI zzgethostbyname(const char* name) {
    if (name) {
        if (strstr(name, "plaync") != nullptr || strstr(name, "ncsoft") != nullptr || strstr(name, "gameforge") != nullptr) {
            static struct hostent localHost;
            static char* localAddrList[2];
            static unsigned long localIp;
            localIp = inet_addr("127.0.0.1");
            localAddrList[0] = (char*)&localIp;
            localAddrList[1] = nullptr;
            localHost.h_name = (char*)name;
            localHost.h_aliases = nullptr;
            localHost.h_addrtype = AF_INET;
            localHost.h_length = 4;
            localHost.h_addr_list = localAddrList;
            return &localHost;
        }
    }
    return real_gethostbyname(name);
}

static decltype(connect)* real_connect = connect;
static int WSAAPI zzconnect(_In_ SOCKET s, _In_reads_bytes_(namelen) const struct sockaddr FAR* name, _In_ int namelen) {
    ClearCandidateIps();
    if (name && namelen >= sizeof(sockaddr_in) && name->sa_family == AF_INET) {
        sockaddr_in* sin = (sockaddr_in*)name;
        uint16_t port = ntohs(sin->sin_port);
        // Intercept outgoing HTTP/Shop connections to port 80 or 443 (redirect to local web server 127.0.0.1:8080)
        if (port == 80 || port == 443) {
            sockaddr_in localAddr = *sin;
            localAddr.sin_port = htons(8080);
            localAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
            return real_connect(s, (struct sockaddr*)&localAddr, sizeof(localAddr));
        }
    }
    return real_connect(s, name, namelen);
}

/// Allows connecting to unofficial game servers by spoofing the game server IP as an official one
void InstallIpFix() {
    DetourAttach(&(PVOID&)real_inet_ntoa, zzinet_ntoa);
    DetourAttach(&(PVOID&)real_lstrcpynA, zzlstrcpynA);
    DetourAttach(&(PVOID&)real_connect, zzconnect);
    DetourAttach(&(PVOID&)real_gethostbyname, zzgethostbyname);
}