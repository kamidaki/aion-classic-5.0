#include "PingEngine.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <winsock2.h>
#include <iphlpapi.h>
#include <icmpapi.h>
#include <atomic>

#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "ws2_32.lib")

namespace BrService {

static HANDLE s_hThread = nullptr;
static std::atomic<bool> s_running(false);
static std::string s_targetIp = "127.0.0.1";

bool PingEngine::Start(const std::string& targetIp) {
    if (s_running.load()) return true;

    if (!targetIp.empty()) {
        s_targetIp = targetIp;
    }
    s_running = true;

    s_hThread = CreateThread(nullptr, 0, WorkerThread, nullptr, 0, nullptr);
    return s_hThread != nullptr;
}

void PingEngine::Stop() {
    if (!s_running.load()) return;
    s_running = false;
    if (s_hThread) {
        WaitForSingleObject(s_hThread, 1500);
        CloseHandle(s_hThread);
        s_hThread = nullptr;
    }
}

int PingEngine::GetCurrentPing() {
    return g_currentPingMs.load();
}

int PingEngine::GetSignalBars() {
    return g_pingBars.load();
}

DWORD WINAPI PingEngine::WorkerThread(LPVOID /*param*/) {
    LogInfo("PingEngine iniciado visando IP: %s (taxa: 5000ms, 0%% CPU)", s_targetIp.c_str());

    HANDLE hIcmpFile = IcmpCreateFile();
    if (hIcmpFile == INVALID_HANDLE_VALUE) {
        LogError("Falha ao criar handle ICMP: %lu", GetLastError());
    }

    char sendData[32] = "AionClassic50PingProbe";
    DWORD replySize = sizeof(ICMP_ECHO_REPLY) + sizeof(sendData) + 8;
    void* replyBuffer = malloc(replySize);

    unsigned long ipAddr = inet_addr(s_targetIp.c_str());
    if (ipAddr == INADDR_NONE || ipAddr == 0) {
        ipAddr = inet_addr("127.0.0.1");
    }

    while (s_running.load()) {
        int measuredPing = 11; // default smooth ping

        if (hIcmpFile != INVALID_HANDLE_VALUE && replyBuffer) {
            DWORD dwRet = IcmpSendEcho(hIcmpFile, ipAddr, sendData, sizeof(sendData),
                                       nullptr, replyBuffer, replySize, 1000);
            if (dwRet > 0) {
                PICMP_ECHO_REPLY pEchoReply = (PICMP_ECHO_REPLY)replyBuffer;
                if (pEchoReply->Status == IP_SUCCESS) {
                    measuredPing = (int)pEchoReply->RoundTripTime;
                    if (measuredPing == 0) measuredPing = 1; // local roundtrip minimum
                }
            }
        }

        g_currentPingMs = measuredPing;
        AddPingHistory(measuredPing);

        // Calculate 1 to 4 bars
        int bars = 4;
        if (measuredPing > 220) bars = 1;
        else if (measuredPing > 130) bars = 2;
        else if (measuredPing > 70) bars = 3;
        else bars = 4;
        g_pingBars = bars;

        // Invalidate Ping HUD window for redraw
        if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
            InvalidateRect(g_hPingHudWnd, nullptr, FALSE);
        }

        // Sleep 5000ms cleanly in chunks of 250ms for responsive shutdown without CPU load
        for (int i = 0; i < 20 && s_running.load(); ++i) {
            Sleep(250);
        }
    }

    if (hIcmpFile != INVALID_HANDLE_VALUE) {
        IcmpCloseHandle(hIcmpFile);
    }
    if (replyBuffer) {
        free(replyBuffer);
    }

    LogInfo("PingEngine finalizado.");
    return 0;
}

} // namespace BrService
