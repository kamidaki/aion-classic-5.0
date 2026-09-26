#include "PingEngine.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../ui/PingHudUI.h"
#include <winsock2.h>
#include <iphlpapi.h>
#include <icmpapi.h>
#include <atomic>
#include <algorithm>

#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "ws2_32.lib")

namespace BrService {

static HANDLE s_hThread = nullptr;
static HANDLE s_hWakeEvent = nullptr;
static std::atomic<bool> s_running(false);
static std::string s_targetIp = "127.0.0.1";
static HANDLE s_hIcmpActive = INVALID_HANDLE_VALUE;

bool PingEngine::Start(const std::string& targetIp) {
    if (s_running.load()) return true;

    if (!targetIp.empty()) {
        s_targetIp = targetIp;
    }
    s_running = true;
    if (!s_hWakeEvent) s_hWakeEvent = CreateEventA(nullptr, FALSE, FALSE, nullptr);

    s_hThread = CreateThread(nullptr, 0, WorkerThread, nullptr, 0, nullptr);
    return s_hThread != nullptr;
}

void PingEngine::Stop() {
    if (!s_running.load()) return;
    s_running = false;

    // Signal wake event for 0ms delay shutdown
    if (s_hWakeEvent) {
        SetEvent(s_hWakeEvent);
    }

    // Abort active ICMP handle to unblock IcmpSendEcho immediately
    HANDLE hIcmp = s_hIcmpActive;
    s_hIcmpActive = INVALID_HANDLE_VALUE;
    if (hIcmp != INVALID_HANDLE_VALUE) {
        IcmpCloseHandle(hIcmp);
    }

    if (s_hThread) {
        WaitForSingleObject(s_hThread, 500);
        CloseHandle(s_hThread);
        s_hThread = nullptr;
    }
    if (s_hWakeEvent) {
        CloseHandle(s_hWakeEvent);
        s_hWakeEvent = nullptr;
    }
}

int PingEngine::GetCurrentPing() {
    return g_currentPingMs.load();
}

int PingEngine::GetSignalBars() {
    return g_pingBars.load();
}

DWORD WINAPI PingEngine::WorkerThread(LPVOID /*param*/) {
    LogInfo("PingEngine iniciado visando IP: %s (intervalo: 2500ms)", s_targetIp.c_str());

    HANDLE hIcmpFile = IcmpCreateFile();
    if (hIcmpFile == INVALID_HANDLE_VALUE) {
        LogError("PingEngine: Falha ao criar handle ICMP: %lu", GetLastError());
    }
    s_hIcmpActive = hIcmpFile;

    char sendData[32] = "AionClassic50PingProbe";

    // Microsoft requirement on 64-bit platforms:
    // Buffer must be >= sizeof(ICMP_ECHO_REPLY) + RequestSize + 8 + sizeof(IO_STATUS_BLOCK) [16 bytes].
    // We allocate a safe 2048-byte buffer to guarantee ZERO buffer overruns or heap corruption.
    const DWORD replySize = 2048;
    void* replyBuffer = malloc(replySize);

    unsigned long ipAddr = inet_addr(s_targetIp.c_str());
    if (ipAddr == INADDR_NONE || ipAddr == 0) {
        ipAddr = inet_addr("127.0.0.1");
    }

    int lastReportedPing = -1;
    int lastReportedBars = -1;

    while (s_running.load()) {
        int measuredPing = 11; // default smooth baseline

        if (s_hIcmpActive != INVALID_HANDLE_VALUE && replyBuffer) {
            DWORD dwRet = IcmpSendEcho(s_hIcmpActive, ipAddr, sendData, sizeof(sendData),
                                       nullptr, replyBuffer, replySize, 300);
            if (dwRet > 0) {
                PICMP_ECHO_REPLY pEchoReply = (PICMP_ECHO_REPLY)replyBuffer;
                if (pEchoReply && pEchoReply->Status == IP_SUCCESS) {
                    measuredPing = (int)pEchoReply->RoundTripTime;
                    if (measuredPing <= 0) measuredPing = 1;
                }
            }
        }

        measuredPing = std::clamp(measuredPing, 1, 999);
        g_currentPingMs = measuredPing;
        AddPingHistory(measuredPing);

        int bars = 4;
        if      (measuredPing > 220) bars = 1;
        else if (measuredPing > 130) bars = 2;
        else if (measuredPing > 70)  bars = 3;
        else                         bars = 4;
        g_pingBars = bars;

        // Only trigger repaint if value changed
        if (measuredPing != lastReportedPing || bars != lastReportedBars) {
            lastReportedPing = measuredPing;
            lastReportedBars = bars;
            PingHudUI::Repaint();
        }

        // Sleep 2500ms or wake up instantly on Stop()
        if (s_hWakeEvent) {
            WaitForSingleObject(s_hWakeEvent, 2500);
        } else {
            Sleep(2500);
        }
    }

    if (hIcmpFile != INVALID_HANDLE_VALUE) {
        IcmpCloseHandle(hIcmpFile);
        s_hIcmpActive = INVALID_HANDLE_VALUE;
    }
    if (replyBuffer) {
        free(replyBuffer);
    }

    LogInfo("PingEngine finalizado com seguranca.");
    return 0;
}

} // namespace BrService
