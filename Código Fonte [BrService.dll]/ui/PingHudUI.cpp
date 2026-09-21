#include "PingHudUI.h"
#include "DrawerModalUI.h"
#include "UICommon.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"

namespace BrService {

static const wchar_t* kPingHudClassName = L"BrService_PingHud";
static bool s_iconHovered = false;
static int s_hudWidth = 140;
static int s_hudHeight = 32;

bool PingHudUI::Initialize(HINSTANCE hInst) {
    WNDCLASSEXW wc = { sizeof(WNDCLASSEXW) };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = kPingHudClassName;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.style = CS_HREDRAW | CS_VREDRAW;

    if (!RegisterClassExW(&wc)) {
        DWORD err = GetLastError();
        if (err != ERROR_CLASS_ALREADY_EXISTS) {
            LogError("Falha ao registrar classe PingHud: %lu", err);
            return false;
        }
    }

    g_hPingHudWnd = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
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

    Repaint();
    LogInfo("PingHudUI inicializado com sucesso.");
    return true;
}

void PingHudUI::Shutdown() {
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        DestroyWindow(g_hPingHudWnd);
        g_hPingHudWnd = nullptr;
    }
}

void PingHudUI::Show() {
    if (g_hPingHudWnd && !g_isLoadingScreen.load() && g_isGameActive.load()) {
        ShowWindow(g_hPingHudWnd, SW_SHOWNOACTIVATE);
        Repaint();
    }
}

void PingHudUI::Hide() {
    if (g_hPingHudWnd) {
        ShowWindow(g_hPingHudWnd, SW_HIDE);
    }
}

void PingHudUI::UpdatePosition(int gameX, int gameY, int gameW, int gameH) {
    if (!g_hPingHudWnd) return;

    // Position at bottom-right corner, 18px from right and 20px from bottom (Aion 2 location)
    int hudX = gameX + gameW - s_hudWidth - 18;
    int hudY = gameY + gameH - s_hudHeight - 20;

    SetWindowPos(g_hPingHudWnd, HWND_TOPMOST, hudX, hudY, s_hudWidth, s_hudHeight,
                 SWP_NOACTIVATE | (g_isLoadingScreen.load() || !g_isGameActive.load() ? SWP_HIDEWINDOW : SWP_SHOWWINDOW));
    Repaint();
}

void PingHudUI::Repaint() {
    if (!g_hPingHudWnd || !IsWindow(g_hPingHudWnd)) return;
    Paint(g_hPingHudWnd);
}

void PingHudUI::Paint(HWND hwnd) {
    HDC screenDC = GetDC(nullptr);
    HDC memDC = CreateCompatibleDC(screenDC);

    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = s_hudWidth;
    bmi.bmiHeader.biHeight = -s_hudHeight; // top-down DIB
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;

    void* pBits = nullptr;
    HBITMAP hBitmap = CreateDIBSection(screenDC, &bmi, DIB_RGB_COLORS, &pBits, nullptr, 0);
    HBITMAP hOldBitmap = (HBITMAP)SelectObject(memDC, hBitmap);

    {
        Gdiplus::Graphics g(memDC);
        g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
        g.SetTextRenderingHint(Gdiplus::TextRenderingHintClearTypeGridFit);

        // Clear transparent
        g.Clear(Gdiplus::Color(0, 0, 0, 0));

        // 1. Shugo Console Icon (Left of ping bars)
        // Icon rect: x=8, y=6, w=20, h=20
        float iconX = 8.0f;
        float iconY = 6.0f;
        float iconSize = 20.0f;

        Gdiplus::Color iconCol = s_iconHovered ? UICommon::ColGoldAccent : Gdiplus::Color(220, 180, 190, 205);
        Gdiplus::Pen iconPen(iconCol, 1.6f);

        // Terminal/Console box
        UICommon::DrawRoundRectangle(g, &iconPen, iconX, iconY, iconSize, iconSize - 2.0f, 3.0f);
        // Prompt chevron '>' inside icon
        g.DrawLine(&iconPen, iconX + 4.5f, iconY + 5.0f, iconX + 8.5f, iconY + 8.5f);
        g.DrawLine(&iconPen, iconX + 8.5f, iconY + 8.5f, iconX + 4.5f, iconY + 12.0f);
        // Cursor line '_'
        g.DrawLine(&iconPen, iconX + 11.0f, iconY + 12.0f, iconX + 15.5f, iconY + 12.0f);

        // 2. Vertical Ping Signal Bars (Exact Aion 2 proportions)
        int bars = g_pingBars.load();
        int pingMs = g_currentPingMs.load();

        Gdiplus::Color barActiveCol = UICommon::ColNeonGreen;
        if (pingMs > 220) barActiveCol = Gdiplus::Color(255, 230, 60, 60);      // Red
        else if (pingMs > 130) barActiveCol = Gdiplus::Color(255, 235, 185, 45); // Yellow

        Gdiplus::Color barInactiveCol(70, 80, 90, 100);

        float barX = 36.0f;
        float barWidth = 3.0f;
        float barGap = 2.0f;
        float baseBottomY = 22.0f;
        float barHeights[4] = { 5.0f, 8.0f, 11.0f, 15.0f };

        for (int i = 0; i < 4; ++i) {
            float bx = barX + i * (barWidth + barGap);
            float bh = barHeights[i];
            float by = baseBottomY - bh;

            Gdiplus::Color col = (i < bars) ? barActiveCol : barInactiveCol;
            Gdiplus::SolidBrush b(col);
            g.FillRectangle(&b, bx, by, barWidth, bh);
        }

        // 3. Ping Text (e.g. "11ms")
        wchar_t pingStr[32];
        swprintf_s(pingStr, L"%dms", pingMs);

        Gdiplus::Font font(L"Segoe UI", 11.0f, Gdiplus::FontStyleBold);
        Gdiplus::SolidBrush textBrush(barActiveCol);

        Gdiplus::PointF textPt(barX + 4 * (barWidth + barGap) + 4.0f, 6.0f);
        g.DrawString(pingStr, -1, &font, textPt, &textBrush);
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

    SelectObject(memDC, hOldBitmap);
    DeleteObject(hBitmap);
    DeleteDC(memDC);
    ReleaseDC(nullptr, screenDC);
}

LRESULT CALLBACK PingHudUI::WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_MOUSEMOVE: {
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        bool hovered = (mx >= 6 && mx <= 30 && my >= 4 && my <= 26);
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
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);
        // Click on Console Icon
        if (mx >= 6 && mx <= 32 && my >= 4 && my <= 28) {
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
