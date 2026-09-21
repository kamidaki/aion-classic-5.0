#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>

namespace BrService {

class PingEngine {
public:
    static bool Start(const std::string& targetIp);
    static void Stop();
    static int GetCurrentPing();
    static int GetSignalBars();

private:
    static DWORD WINAPI WorkerThread(LPVOID param);
};

} // namespace BrService
