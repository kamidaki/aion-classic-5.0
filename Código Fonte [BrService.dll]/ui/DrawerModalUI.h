#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

namespace BrService {

class DrawerModalUI {
public:
    static bool Initialize(HINSTANCE hInst);
    static void Shutdown();

    static void Toggle();
    static void Open();
    static void Close();
    static bool IsOpen();

    static void UpdatePosition(int gameX, int gameY, int gameW, int gameH);
    static void Repaint();

private:
    static LRESULT CALLBACK WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
    static void Paint(HWND hwnd);
};

} // namespace BrService
