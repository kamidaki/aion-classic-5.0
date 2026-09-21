#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <string>
#include <algorithm>

constexpr int COMBO_W = 680;
constexpr int COMBO_H = 320;

constexpr float COMBO_TIMEOUT_START_MS = 4000.0f;
constexpr float COMBO_TIMEOUT_FLOOR_MS = 2000.0f;
constexpr int   COMBO_TIMEOUT_LOCK_HIT = 50;

inline DWORD ComputeComboTimeoutMs(int hits) {
    if (hits <= 1) return (DWORD)COMBO_TIMEOUT_START_MS;
    if (hits >= COMBO_TIMEOUT_LOCK_HIT) return (DWORD)COMBO_TIMEOUT_FLOOR_MS;
    float stepMs = (COMBO_TIMEOUT_START_MS - COMBO_TIMEOUT_FLOOR_MS) / (float)(COMBO_TIMEOUT_LOCK_HIT - 1);
    float t = COMBO_TIMEOUT_START_MS - stepMs * (float)(hits - 1);
    if (t < COMBO_TIMEOUT_FLOOR_MS) t = COMBO_TIMEOUT_FLOOR_MS;
    return (DWORD)t;
}

inline std::string FormatNumberWithDots(int number) {
    std::string str = std::to_string(number);
    std::string result;
    int len = (int)str.length();
    for (int i = 0; i < len; ++i) {
        if (i > 0 && (len - i) % 3 == 0)
            result.push_back('.');
        result.push_back(str[i]);
    }
    return result;
}

inline int ClampInt(int value, int minValue, int maxValue) {
    if (value < minValue) return minValue;
    if (value > maxValue) return maxValue;
    return value;
}

inline float ClampFloat(float value, float minValue, float maxValue) {
    if (value < minValue) return minValue;
    if (value > maxValue) return maxValue;
    return value;
}

extern volatile LONG g_comboLayoutNormX10000;
extern volatile LONG g_comboLayoutNormY10000;
extern volatile LONG g_comboLayoutScale1000;
extern volatile LONG g_comboLayoutVersion;
extern volatile LONG g_comboOpacity1000;

inline void SetComboOverlayLayout(float normX, float normY, float scale) {
    normX = ClampFloat(normX, 0.0f, 1.0f);
    normY = ClampFloat(normY, 0.0f, 1.0f);
    scale = ClampFloat(scale, 0.55f, 1.60f);
    InterlockedExchange(&g_comboLayoutNormX10000, (LONG)(normX * 10000.0f + 0.5f));
    InterlockedExchange(&g_comboLayoutNormY10000, (LONG)(normY * 10000.0f + 0.5f));
    InterlockedExchange(&g_comboLayoutScale1000, (LONG)(scale * 1000.0f + 0.5f));
    InterlockedIncrement(&g_comboLayoutVersion);
}

inline void GetComboOverlayLayout(float* normX, float* normY, float* scale) {
    LONG x = InterlockedCompareExchange(&g_comboLayoutNormX10000, 0, 0);
    LONG y = InterlockedCompareExchange(&g_comboLayoutNormY10000, 0, 0);
    LONG s = InterlockedCompareExchange(&g_comboLayoutScale1000, 0, 0);
    if (normX) *normX = ClampFloat((float)x / 10000.0f, 0.0f, 1.0f);
    if (normY) *normY = ClampFloat((float)y / 10000.0f, 0.0f, 1.0f);
    if (scale) *scale = ClampFloat((float)s / 1000.0f, 0.55f, 1.60f);
}

inline void SetComboOverlayOpacity(float opacity) {
    opacity = ClampFloat(opacity, 0.1f, 1.0f);
    InterlockedExchange(&g_comboOpacity1000, (LONG)(opacity * 1000.0f + 0.5f));
}

inline float GetComboOverlayOpacity() {
    LONG o = InterlockedCompareExchange(&g_comboOpacity1000, 0, 0);
    return ClampFloat((float)o / 1000.0f, 0.1f, 1.0f);
}

struct ComboOverlayGeometry {
    RECT gameScreen = {};
    RECT overlayScreen = {};
    int gameW = 0;
    int gameH = 0;
    int overlayW = 1;
    int overlayH = 1;
    float normX = 0.8f;
    float normY = 0.5f;
    float scale = 1.0f;
};

inline int ComputeOverlayOriginFromCenter(int viewportStart, int viewportSize, int extent, int center) {
    if (viewportSize <= 0 || extent <= 0) return viewportStart;
    if (extent >= viewportSize) {
        return viewportStart + (viewportSize - extent) / 2;
    }
    return ClampInt(center - extent / 2, viewportStart, viewportStart + viewportSize - extent);
}

inline bool ComputeOverlayGeometry(HWND gameHwnd, ComboOverlayGeometry& outGeom) {
    RECT clientRect;
    if (!gameHwnd || !GetClientRect(gameHwnd, &clientRect)) return false;
    POINT ptTopLeft = { clientRect.left, clientRect.top };
    POINT ptBottomRight = { clientRect.right, clientRect.bottom };
    ClientToScreen(gameHwnd, &ptTopLeft);
    ClientToScreen(gameHwnd, &ptBottomRight);

    int gameW = ptBottomRight.x - ptTopLeft.x;
    int gameH = ptBottomRight.y - ptTopLeft.y;
    if (gameW <= 0 || gameH <= 0) return false;

    float normX = 0.8f;
    float normY = 0.5f;
    float scale = 1.0f;
    GetComboOverlayLayout(&normX, &normY, &scale);

    int overlayW = (std::max)(1, (int)(COMBO_W * scale + 0.5f));
    int overlayH = (std::max)(1, (int)(COMBO_H * scale + 0.5f));
    int anchorX = ptTopLeft.x + (int)(gameW * normX);
    int anchorY = ptTopLeft.y + (int)(gameH * normY);

    outGeom.gameScreen = { ptTopLeft.x, ptTopLeft.y, ptBottomRight.x, ptBottomRight.y };
    outGeom.gameW = gameW;
    outGeom.gameH = gameH;
    outGeom.overlayW = overlayW;
    outGeom.overlayH = overlayH;
    outGeom.normX = normX;
    outGeom.normY = normY;
    outGeom.scale = scale;
    outGeom.overlayScreen.left = ComputeOverlayOriginFromCenter(ptTopLeft.x, gameW, overlayW, anchorX);
    outGeom.overlayScreen.top = ComputeOverlayOriginFromCenter(ptTopLeft.y, gameH, overlayH, anchorY);
    outGeom.overlayScreen.right = outGeom.overlayScreen.left + overlayW;
    outGeom.overlayScreen.bottom = outGeom.overlayScreen.top + overlayH;
    return true;
}

enum class NotificationType {
    Normal,
    AbnormalStun,
    AbnormalParalyzed,
    AbnormalSilenced,
    AbnormalBlink,
    AbnormalPoison,
    AbnormalBleed,
    AbnormalFear,
    AbnormalSleep,
    AbnormalBlind,
    AbnormalDisease,
    AbnormalCurse,
    AbnormalConfuse
};

struct NotificationLine {
    std::string text;
    DWORD tick;
    NotificationType type;
};
