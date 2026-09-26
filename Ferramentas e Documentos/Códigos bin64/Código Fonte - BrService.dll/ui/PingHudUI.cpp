#include "PingHudUI.h"
#include "DrawerModalUI.h"
#include "UICommon.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include <gdiplus.h>
#include <string>
#include <algorithm>

namespace BrService {

static const wchar_t* kPingHudClassName = L"BrService_PingHud";
static int s_hudWidth  = 120;
static int s_hudHeight = 32;
static bool s_iconHovered = false;
static RECT s_dpsMeterIconRect = { 0, 0, 0, 0 };

// Reusable buffer cache (eliminates per-frame GDI allocations)
static HDC     s_hudMemDC      = nullptr;
static HBITMAP s_hudBitmap     = nullptr;
static HBITMAP s_hudOldBitmap  = nullptr;
static int     s_hudBufW       = 0;
static int     s_hudBufH       = 0;

static void EnsureHudBuffer(HDC screenDC, int width, int height) {
    if (s_hudMemDC && s_hudBufW == width && s_hudBufH == height) return;
    if (s_hudMemDC) {
        if (s_hudOldBitmap) SelectObject(s_hudMemDC, s_hudOldBitmap);
        if (s_hudBitmap)    DeleteObject(s_hudBitmap);
        DeleteDC(s_hudMemDC);
    }
    s_hudMemDC = CreateCompatibleDC(screenDC);
    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize        = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth       = width;
    bmi.bmiHeader.biHeight      = -height;
    bmi.bmiHeader.biPlanes      = 1;
    bmi.bmiHeader.biBitCount    = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    void* pBits = nullptr;
    s_hudBitmap    = CreateDIBSection(screenDC, &bmi, DIB_RGB_COLORS, &pBits, nullptr, 0);
    s_hudOldBitmap = (HBITMAP)SelectObject(s_hudMemDC, s_hudBitmap);
    s_hudBufW = width;
    s_hudBufH = height;
}

static void ReleaseHudBuffer() {
    if (s_hudMemDC) {
        if (s_hudOldBitmap) SelectObject(s_hudMemDC, s_hudOldBitmap);
        if (s_hudBitmap)    DeleteObject(s_hudBitmap);
        DeleteDC(s_hudMemDC);
    }
    s_hudMemDC     = nullptr;
    s_hudBitmap    = nullptr;
    s_hudOldBitmap = nullptr;
    s_hudBufW = s_hudBufH = 0;
}

static Gdiplus::Font* s_hudFontPing = nullptr;

static void EnsureHudFonts() {
    if (!s_hudFontPing) s_hudFontPing = new Gdiplus::Font(L"Segoe UI", 10.0f, Gdiplus::FontStyleBold);
}

static void ReleaseHudFonts() {
    if (s_hudFontPing) { delete s_hudFontPing; s_hudFontPing = nullptr; }
}

bool PingHudUI::Initialize(HINSTANCE hInst) {
    WNDCLASSEXW wc = { 0 };
    wc.cbSize       = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc  = WndProc;
    wc.hInstance    = hInst;
    wc.hCursor      = LoadCursor(nullptr, IDC_ARROW);
    wc.lpszClassName = kPingHudClassName;

    if (!RegisterClassExW(&wc)) {
        DWORD err = GetLastError();
        if (err != ERROR_CLASS_ALREADY_EXISTS) {
            LogError("Falha ao registrar classe PingHud: %lu", err);
            return false;
        }
    }

    g_hPingHudWnd = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
        kPingHudClassName,
        L"Aion Ping HUD",
        WS_POPUP,
        0, 0, s_hudWidth, s_hudHeight,
        nullptr, nullptr, hInst, nullptr
    );

    if (!g_hPingHudWnd) {
        LogError("Falha ao criar janela PingHud: %lu", GetLastError());
        return false;
    }

    ShowWindow(g_hPingHudWnd, SW_HIDE);
    LogInfo("PingHudUI inicializado com sucesso.");
    return true;
}

void PingHudUI::Shutdown() {
    ReleaseHudBuffer();
    ReleaseHudFonts();
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        DestroyWindow(g_hPingHudWnd);
        g_hPingHudWnd = nullptr;
    }
}

bool PingHudUI::IsAllowedToDisplay() {
    if (!g_featDpsMeterUI.load() && !g_featPingUi.load()) return false;
    HWND hGame = g_gameHwnd.load();
    if (!hGame || !IsWindow(hGame) || IsIconic(hGame)) return false;
    if (g_isLoadingScreen.load() || !g_isGameActive.load()) return false;
    return true;
}

void PingHudUI::Show() {
    if (!IsAllowedToDisplay()) {
        Hide();
        return;
    }
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        if (!IsWindowVisible(g_hPingHudWnd)) {
            ShowWindow(g_hPingHudWnd, SW_SHOWNOACTIVATE);
        }
        Paint(g_hPingHudWnd);
    }
}

void PingHudUI::Hide() {
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        if (IsWindowVisible(g_hPingHudWnd)) {
            ShowWindow(g_hPingHudWnd, SW_HIDE);
        }
    }
}

void PingHudUI::UpdatePosition(int gameX, int gameY, int gameW, int gameH) {
    if (!g_hPingHudWnd || !IsWindow(g_hPingHudWnd)) return;

    bool showDpsMeter = g_featDpsMeterUI.load();
    bool showPing     = g_featPingUi.load();

    if (!showDpsMeter && !showPing) {
        Hide();
        return;
    }

    int calcW = 4;
    if (showPing)     calcW += 64;
    if (showDpsMeter) calcW += 32;
    calcW += 8;
    s_hudWidth = calcW;

    int hudX = gameX;
    int hudY = gameY + gameH - s_hudHeight;

    bool shouldBeVisible = IsAllowedToDisplay();

    static int s_prevX = -9999, s_prevY = -9999, s_prevW = -9999, s_prevH = -9999;
    static int s_prevVis = -1;

    int curVis = shouldBeVisible ? 1 : 0;
    if (hudX != s_prevX || hudY != s_prevY || s_hudWidth != s_prevW || s_hudHeight != s_prevH || curVis != s_prevVis) {
        s_prevX = hudX; s_prevY = hudY; s_prevW = s_hudWidth; s_prevH = s_hudHeight; s_prevVis = curVis;
        SetWindowPos(g_hPingHudWnd, nullptr, hudX, hudY, s_hudWidth, s_hudHeight,
                     SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOOWNERZORDER | SWP_ASYNCWINDOWPOS | (shouldBeVisible ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
        if (shouldBeVisible) {
            Paint(g_hPingHudWnd);
        }
    }
}

void PingHudUI::Repaint() {
    if (!g_hPingHudWnd || !IsWindow(g_hPingHudWnd)) return;
    Paint(g_hPingHudWnd);
}

void PingHudUI::Paint(HWND hwnd) {
    HDC screenDC = GetDC(nullptr);
    EnsureHudBuffer(screenDC, s_hudWidth, s_hudHeight);
    HDC memDC = s_hudMemDC;
    if (!memDC) {
        ReleaseDC(nullptr, screenDC);
        return;
    }
    EnsureHudFonts();

    {
        Gdiplus::Graphics g(memDC);
        g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
        g.SetTextRenderingHint(Gdiplus::TextRenderingHintClearTypeGridFit);

        g.Clear(Gdiplus::Color(0, 0, 0, 0));

        bool showDpsMeter = g_featDpsMeterUI.load();
        bool showPing     = g_featPingUi.load();

        float curX = 6.0f;

        // 1. PING (Signal Bars + ms text)
        if (showPing) {
            int bars   = g_pingBars.load();
            int pingMs = g_currentPingMs.load();

            Gdiplus::Color barActiveCol = UICommon::ColNeonGreen;
            if      (pingMs > 220) barActiveCol = Gdiplus::Color(255, 230, 60,  60);   // Red
            else if (pingMs > 130) barActiveCol = Gdiplus::Color(255, 235, 185, 45);   // Yellow

            Gdiplus::Color barInactiveCol(70, 80, 90, 100);

            float barWidth = 3.0f;
            float barGap   = 2.0f;
            float baseBottomY = 22.0f;
            float barHeights[4] = { 5.0f, 8.0f, 11.0f, 15.0f };

            for (int i = 0; i < 4; ++i) {
                float bx = curX + i * (barWidth + barGap);
                float bh = barHeights[i];
                float by = baseBottomY - bh;
                Gdiplus::Color col = (i < bars) ? barActiveCol : barInactiveCol;
                Gdiplus::SolidBrush b(col);
                g.FillRectangle(&b, bx, by, barWidth, bh);
            }

            curX += 4 * (barWidth + barGap) + 3.0f;

            wchar_t pingStr[32];
            swprintf_s(pingStr, L"%dms", pingMs);
            Gdiplus::SolidBrush textBrush(barActiveCol);
            g.DrawString(pingStr, -1, s_hudFontPing, Gdiplus::PointF(curX, 5.0f), &textBrush);

            curX += 38.0f;
        }

        // 2. DPS METER / DASHBOARD ICON (Metrics Chart) — Pure White
        if (showDpsMeter) {
            float iconX    = curX + 2.0f;
            float iconY    = 6.0f;
            float iconSize = 20.0f;

            s_dpsMeterIconRect = {
                (int)iconX - 2, (int)iconY - 2,
                (int)(iconX + iconSize + 2), (int)(iconY + iconSize + 2)
            };

            // Hit test background with non-zero alpha so layered window registers clicks
            Gdiplus::SolidBrush hitBrush(Gdiplus::Color(2, 20, 25, 30));
            UICommon::FillRoundRectangle(g, &hitBrush,
                (float)s_dpsMeterIconRect.left, (float)s_dpsMeterIconRect.top,
                (float)(s_dpsMeterIconRect.right  - s_dpsMeterIconRect.left),
                (float)(s_dpsMeterIconRect.bottom - s_dpsMeterIconRect.top), 4.0f);

            // Constant pure white / hover highlight
            Gdiplus::Color iconCol = s_iconHovered
                ? Gdiplus::Color(255, 255, 255, 255)
                : Gdiplus::Color(220, 255, 255, 255);

            Gdiplus::Pen iconPen(iconCol, 1.6f);
            UICommon::DrawRoundRectangle(g, &iconPen, iconX, iconY, iconSize, iconSize - 2.0f, 3.0f);

            // 3-bar histogram metrics icon
            Gdiplus::SolidBrush barBrush(iconCol);
            g.FillRectangle(&barBrush, iconX + 4.0f,  iconY + 9.5f, 2.2f, 4.5f);
            g.FillRectangle(&barBrush, iconX + 8.5f,  iconY + 6.5f, 2.2f, 7.5f);
            g.FillRectangle(&barBrush, iconX + 13.0f, iconY + 4.0f, 2.2f, 10.0f);

            curX += iconSize + 8.0f;
        } else {
            s_dpsMeterIconRect = { 0, 0, 0, 0 };
        }
    }

    POINT ptSrc = { 0, 0 };
    SIZE szWindow = { s_hudWidth, s_hudHeight };
    BLENDFUNCTION blend = {};
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = 255;
    blend.AlphaFormat = AC_SRC_ALPHA;

    UpdateLayeredWindow(hwnd, screenDC, nullptr, &szWindow, memDC, &ptSrc, 0, &blend, ULW_ALPHA);
    ReleaseDC(nullptr, screenDC);
}

LRESULT CALLBACK PingHudUI::WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_PAINT: {
        PAINTSTRUCT ps;
        BeginPaint(hwnd, &ps);
        Paint(hwnd);
        EndPaint(hwnd, &ps);
        return 0;
    }

    // T04/T05: Handle cross-thread UI commands posted from WebSocket/PingEngine threads.
    // These messages are POSTED (not sent), so they're processed here on WatchdogThread.
    case WM_BRSERVICE_REPAINT:
        Paint(hwnd);
        return 0;

    case WM_BRSERVICE_SHOW:
        if (!IsWindowVisible(hwnd) && IsAllowedToDisplay()) {
            ShowWindow(hwnd, SW_SHOWNOACTIVATE);
        }
        Paint(hwnd);
        return 0;

    case WM_BRSERVICE_HIDE:
        if (IsWindowVisible(hwnd)) {
            ShowWindow(hwnd, SW_HIDE);
        }
        return 0;

    case WM_MOUSEMOVE: {
        if (!g_featDpsMeterUI.load()) return 0;
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        POINT pt = { mx, my };
        bool hovered = PtInRect(&s_dpsMeterIconRect, pt) != FALSE;
        if (hovered != s_iconHovered) {
            s_iconHovered = hovered;
            Paint(hwnd);
        }
        TRACKMOUSEEVENT tme = { sizeof(TRACKMOUSEEVENT), TME_LEAVE, hwnd, 0 };
        TrackMouseEvent(&tme);
        return 0;
    }
    case WM_MOUSELEAVE: {
        if (s_iconHovered) {
            s_iconHovered = false;
            Paint(hwnd);
        }
        return 0;
    }
    case WM_LBUTTONDOWN: {
        if (!g_featDpsMeterUI.load()) return 0;
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        POINT pt = { mx, my };
        if (PtInRect(&s_dpsMeterIconRect, pt)) {
            DrawerModalUI::Toggle();
        }
        return 0;
    }
    case WM_DESTROY:
        return 0;
    default:
        return DefWindowProcW(hwnd, uMsg, wParam, lParam);
    }
}

} // namespace BrService
