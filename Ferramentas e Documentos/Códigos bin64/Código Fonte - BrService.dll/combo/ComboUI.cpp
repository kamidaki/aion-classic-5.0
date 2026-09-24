#include "ComboUI.h"

HWND g_gameHwnd = nullptr;
HWND g_overlayHwnd = nullptr;
HHOOK g_windowHook = nullptr;
HANDLE g_wakeEvent = nullptr;

volatile LONG g_comboLayoutNormX10000 = 8000;
volatile LONG g_comboLayoutNormY10000 = 5000;
volatile LONG g_comboLayoutScale1000 = 1000;
volatile LONG g_comboLayoutVersion = 0;
volatile LONG g_comboOpacity1000 = 1000;

ComboRenderer g_ComboUI;

LRESULT CALLBACK CallWndProcHook(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        CWPSTRUCT* cwp = reinterpret_cast<CWPSTRUCT*>(lParam);
        if (cwp->hwnd == g_gameHwnd && g_overlayHwnd) {
            if (cwp->message == WM_WINDOWPOSCHANGING || cwp->message == WM_WINDOWPOSCHANGED ||
                cwp->message == WM_MOVE || cwp->message == WM_SIZE ||
                cwp->message == WM_DPICHANGED) {
                if (g_wakeEvent) {
                    SetEvent(g_wakeEvent);
                }
            }
        }
    }
    return CallNextHookEx(g_windowHook, nCode, wParam, lParam);
}
