#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

namespace BrService {

class ServiceWorker {
public:
    static bool Start();
    static void Stop();

private:
    static DWORD WINAPI WatchdogThread(LPVOID param);
    static HWND FindGameWindow();
    static bool CheckLoadingScreen(HWND hwnd);
};

} // namespace BrService
