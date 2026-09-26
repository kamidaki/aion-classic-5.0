#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include "ComboTypes.h"
#include "ComboRenderer.h"

extern ComboRenderer g_ComboUI;

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
