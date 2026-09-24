#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include "ComboTypes.h"
#include "ComboRenderer.h"

extern HWND g_gameHwnd;
extern HWND g_overlayHwnd;
extern HHOOK g_windowHook;
extern HANDLE g_wakeEvent;

extern ComboRenderer g_ComboUI;

LRESULT CALLBACK CallWndProcHook(int nCode, WPARAM wParam, LPARAM lParam);

inline void ComputeOverlayRect(HWND gameHwnd, RECT& out) {
    ComboOverlayGeometry geom;
    if (ComputeOverlayGeometry(gameHwnd, geom)) {
        out = geom.overlayScreen;
    } else {
        out = { 0, 0, COMBO_W, COMBO_H };
    }
}

inline bool IsForegroundInGameProcess(HWND gameHwnd, HWND foregroundHwnd) {
    if (!gameHwnd || !foregroundHwnd) return false;
    DWORD gamePid = 0;
    DWORD foregroundPid = 0;
    GetWindowThreadProcessId(gameHwnd, &gamePid);
    GetWindowThreadProcessId(foregroundHwnd, &foregroundPid);
    return gamePid != 0 && gamePid == foregroundPid;
}
