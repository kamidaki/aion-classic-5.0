#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>

namespace BrService {

class WebSocketClient {
public:
    static bool Start(const std::string& host, int port);
    static void Stop();
    static bool IsConnected();

private:
    static DWORD WINAPI ClientThread(LPVOID param);
    static void HandleIncomingPayload(const std::string& payload);
};

} // namespace BrService
