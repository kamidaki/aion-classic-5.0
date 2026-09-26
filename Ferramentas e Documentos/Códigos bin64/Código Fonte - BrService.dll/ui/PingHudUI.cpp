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
static RECT s_consoleIconRect = { 0, 0, 0, 0 };

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

// Persistent font cache (eliminates DirectWrite/GDI churn)
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

    // Default hidden until GameServer signals in-world spawn
    ShowWindow(g_hPingHudWnd, SW_HIDE);
    LogInfo("PingHudUI inicializado com sucesso (aguardando entrada no mundo).");
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
    if (!g_featConsole.load() && !g_featPingUi.load()) return false;
    if (!g_isInWorld.load() || g_isLoadingScreen.load() || !g_isGameActive.load()) return false;
    return true;
}

void PingHudUI::Show() {
    if (!IsAllowedToDisplay()) {
        Hide();
        return;
    }
    if (g_hPingHudWnd) {
        if (!IsWindowVisible(g_hPingHudWnd)) {
            ShowWindow(g_hPingHudWnd, SW_SHOWNOACTIVATE);
            Repaint();
        }
    }
}

void PingHudUI::Hide() {
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        ShowWindow(g_hPingHudWnd, SW_HIDE);
    }
}

void PingHudUI::UpdatePosition(int gameX, int gameY, int gameW, int gameH) {
    if (!g_hPingHudWnd || !IsWindow(g_hPingHudWnd)) return;

    bool showConsole = g_featConsole.load();
    bool showPing    = g_featPingUi.load();

    if (!showConsole && !showPing) {
        ShowWindow(g_hPingHudWnd, SW_HIDE);
        return;
    }

    // Calculate dynamic width based on visible items (no online count)
    int calcW = 4;
    if (showPing)    calcW += 64;
    if (showConsole) calcW += 32;
    calcW += 8;
    s_hudWidth = calcW;

    // Position: bottom-left corner of game client area
    int hudX = gameX;
    int hudY = gameY + gameH - s_hudHeight;

    bool shouldBeVisible = IsAllowedToDisplay();

    SetWindowPos(g_hPingHudWnd, HWND_TOPMOST, hudX, hudY, s_hudWidth, s_hudHeight,
                 SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS | (shouldBeVisible ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
    if (shouldBeVisible) {
        InvalidateRect(g_hPingHudWnd, nullptr, FALSE);
    }
}

void PingHudUI::Repaint() {
    if (!g_hPingHudWnd || !IsWindow(g_hPingHudWnd)) return;
    InvalidateRect(g_hPingHudWnd, nullptr, FALSE);
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

        // Clear transparent
        g.Clear(Gdiplus::Color(0, 0, 0, 0));

        bool showConsole = g_featConsole.load();
        bool showPing    = g_featPingUi.load();

        float curX = 6.0f;

        // 1. PING (Vertical Signal Bars + ms) — First on Left
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

        // 2. CONSOLE ICON (>_) — Pure white (no per-frame color logic)
        if (showConsole) {
            float iconX   = curX + 2.0f;
            float iconY   = 6.0f;
            float iconSize = 20.0f;

            s_consoleIconRect = {
                (int)iconX - 2, (int)iconY - 2,
                (int)(iconX + iconSize + 2), (int)(iconY + iconSize + 2)
            };

            // Hit test fix: fill hitbox with non-zero alpha so layered window registers mouse
            Gdiplus::SolidBrush hitBrush(Gdiplus::Color(2, 20, 25, 30));
            UICommon::FillRoundRectangle(g, &hitBrush,
                (float)s_consoleIconRect.left, (float)s_consoleIconRect.top,
                (float)(s_consoleIconRect.right  - s_consoleIconRect.left),
                (float)(s_consoleIconRect.bottom - s_consoleIconRect.top), 4.0f);

            // Console icon is always pure white. Hover state adds a slight brightness
            // but the base color is 255,255,255 per requirement.
            // Note: NOT using any runtime color computation — pure constant white.
            Gdiplus::Color iconCol = s_iconHovered
                ? Gdiplus::Color(255, 255, 255, 255)   // Hovered: opaque white
                : Gdiplus::Color(220, 255, 255, 255);  // Normal:  slightly transparent white

            Gdiplus::Pen iconPen(iconCol, 1.6f);

            // Terminal/Console box
            UICommon::DrawRoundRectangle(g, &iconPen, iconX, iconY, iconSize, iconSize - 2.0f, 3.0f);
            // Prompt chevron '>' inside icon
            g.DrawLine(&iconPen, iconX + 4.5f, iconY + 5.0f,  iconX + 8.5f, iconY + 8.5f);
            g.DrawLine(&iconPen, iconX + 8.5f, iconY + 8.5f,  iconX + 4.5f, iconY + 12.0f);
            // Cursor line '_'
            g.DrawLine(&iconPen, iconX + 11.0f, iconY + 12.0f, iconX + 15.5f, iconY + 12.0f);

            curX += iconSize + 8.0f;
        } else {
            s_consoleIconRect = { 0, 0, 0, 0 };
        }

        // Online player count section has been completely removed.
        (void)curX;
    }

    // Blend to layered window
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
    case WM_MOUSEMOVE: {
        if (!g_featConsole.load()) return 0;
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        POINT pt = { mx, my };
        bool hovered = PtInRect(&s_consoleIconRect, pt) != FALSE;
        if (hovered != s_iconHovered) {
            s_iconHovered = hovered;
            Repaint();
        }
        TRACKMOUSEEVENT tme = { sizeof(TRACKMOUSEEVENT), TME_LEAVE, hwnd, 0 };
        TrackMouseEvent(&tme);
        return 0;
    }
    case WM_MOUSELEAVE: {
        if (s_iconHovered) {
            s_iconHovered = false;
            Repaint();
        }
        return 0;
    }
    case WM_LBUTTONDOWN: {
        if (!g_featConsole.load()) return 0;
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        POINT pt = { mx, my };
        if (PtInRect(&s_consoleIconRect, pt)) {
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
