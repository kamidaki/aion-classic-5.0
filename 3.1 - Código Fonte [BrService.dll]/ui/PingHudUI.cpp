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
static int s_hudWidth = 150;
static int s_hudHeight = 32;
static bool s_iconHovered = false;
static RECT s_consoleIconRect = { 0, 0, 0, 0 };

bool PingHudUI::Initialize(HINSTANCE hInst) {
    WNDCLASSEXW wc = { 0 };
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
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
    if (g_hPingHudWnd && IsWindow(g_hPingHudWnd)) {
        DestroyWindow(g_hPingHudWnd);
        g_hPingHudWnd = nullptr;
    }
}

void PingHudUI::Show() {
    if (!g_featConsole.load() && !g_featPingUi.load()) return;
    if (g_hPingHudWnd && g_isInWorld.load() && !g_isLoadingScreen.load() && g_isGameActive.load()) {
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
    bool showPing = g_featPingUi.load();
    bool showAdminOnline = g_isAdmin.load();

    if (!showConsole && !showPing) {
        ShowWindow(g_hPingHudWnd, SW_HIDE);
        return;
    }

    // Calculate dynamic width based on visible items
    int calcW = 4;
    if (showPing) calcW += 64;
    if (showConsole) calcW += 32;
    if (showAdminOnline) calcW += 52;
    calcW += 8;
    s_hudWidth = calcW;

    // Position: Extremidade inferior esquerda (colado na quina inferior sem margem)
    int hudX = gameX;
    int hudY = gameY + gameH - s_hudHeight;

    bool shouldBeVisible = g_isInWorld.load() && !g_isLoadingScreen.load() && g_isGameActive.load();

    SetWindowPos(g_hPingHudWnd, HWND_TOPMOST, hudX, hudY, s_hudWidth, s_hudHeight,
                 SWP_NOACTIVATE | (shouldBeVisible ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
    if (shouldBeVisible) {
        Repaint();
    }
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

        bool showConsole = g_featConsole.load();
        bool showPing = g_featPingUi.load();
        bool showAdminOnline = g_isAdmin.load();

        float curX = 6.0f;

        // 1. PING (Vertical Signal Bars + ms) -> First on Left
        if (showPing) {
            int bars = g_pingBars.load();
            int pingMs = g_currentPingMs.load();

            Gdiplus::Color barActiveCol = UICommon::ColNeonGreen;
            if (pingMs > 220) barActiveCol = Gdiplus::Color(255, 230, 60, 60);      // Red
            else if (pingMs > 130) barActiveCol = Gdiplus::Color(255, 235, 185, 45); // Yellow

            Gdiplus::Color barInactiveCol(70, 80, 90, 100);

            float barWidth = 3.0f;
            float barGap = 2.0f;
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

            // Ping Text (e.g. "11ms")
            wchar_t pingStr[32];
            swprintf_s(pingStr, L"%dms", pingMs);

            Gdiplus::Font fontPing(L"Segoe UI", 10.0f, Gdiplus::FontStyleBold);
            Gdiplus::SolidBrush textBrush(barActiveCol);

            g.DrawString(pingStr, -1, &fontPing, Gdiplus::PointF(curX, 5.0f), &textBrush);

            // Thin white Fibonacci trend line under MS text (last 60 minutes, no background)
            float sparkX = curX;
            float sparkW = 36.0f;
            float sparkY = 23.0f;
            float sparkH = 5.0f;

            std::vector<Gdiplus::PointF> sparkPts;
            {
                std::lock_guard<std::mutex> lock(g_pingHistoryMutex);
                if (g_pingHistory.size() >= 2) {
                    int minP = g_pingHistory[0].pingMs;
                    int maxP = g_pingHistory[0].pingMs;
                    for (const auto& e : g_pingHistory) {
                        if (e.pingMs < minP) minP = e.pingMs;
                        if (e.pingMs > maxP) maxP = e.pingMs;
                    }
                    if (maxP - minP < 6) maxP = minP + 6;

                    size_t count = g_pingHistory.size();
                    size_t step = (count > 24) ? (count / 24) : 1;
                    for (size_t i = 0; i < count; i += step) {
                        float fx = sparkX + ((float)i / (float)(count - 1)) * sparkW;
                        float norm = (float)(g_pingHistory[i].pingMs - minP) / (float)(maxP - minP);
                        norm = std::clamp(norm, 0.0f, 1.0f);
                        float fy = sparkY + sparkH - norm * sparkH;
                        sparkPts.push_back(Gdiplus::PointF(fx, fy));
                    }
                }
            }

            if (sparkPts.size() < 2) {
                // Subtle Fibonacci progression curve when history is initializing
                static const float fibRatios[6] = { 0.236f, 0.500f, 0.382f, 0.618f, 0.382f, 0.786f };
                for (int i = 0; i < 6; ++i) {
                    float fx = sparkX + (float)i * (sparkW / 5.0f);
                    float fy = sparkY + sparkH - fibRatios[i] * sparkH;
                    sparkPts.push_back(Gdiplus::PointF(fx, fy));
                }
            }

            if (sparkPts.size() >= 2) {
                Gdiplus::Pen sparkPen(Gdiplus::Color(255, 255, 255, 255), 1.0f); // 1px pure white, no background
                g.DrawCurve(&sparkPen, sparkPts.data(), (INT)sparkPts.size(), 0.5f);
            }

            curX += 38.0f;
        }

        // 2. CONSOLE ICON (>_) -> Second
        if (showConsole) {
            float iconX = curX + 2.0f;
            float iconY = 6.0f;
            float iconSize = 20.0f;

            s_consoleIconRect = { (int)iconX - 2, (int)iconY - 2, (int)(iconX + iconSize + 2), (int)(iconY + iconSize + 2) };

            // Hit test fix: fill entire hitbox with non-zero alpha (alpha=2) so WS_EX_LAYERED registers mouse on 100% of the button area
            Gdiplus::SolidBrush hitBrush(Gdiplus::Color(2, 20, 25, 30));
            UICommon::FillRoundRectangle(g, &hitBrush, (float)s_consoleIconRect.left, (float)s_consoleIconRect.top,
                                         (float)(s_consoleIconRect.right - s_consoleIconRect.left),
                                         (float)(s_consoleIconRect.bottom - s_consoleIconRect.top), 4.0f);

            Gdiplus::Color iconCol = s_iconHovered ? UICommon::ColGoldAccent : Gdiplus::Color(220, 180, 190, 205);
            Gdiplus::Pen iconPen(iconCol, 1.6f);

            // Terminal/Console box
            UICommon::DrawRoundRectangle(g, &iconPen, iconX, iconY, iconSize, iconSize - 2.0f, 3.0f);
            // Prompt chevron '>' inside icon
            g.DrawLine(&iconPen, iconX + 4.5f, iconY + 5.0f, iconX + 8.5f, iconY + 8.5f);
            g.DrawLine(&iconPen, iconX + 8.5f, iconY + 8.5f, iconX + 4.5f, iconY + 12.0f);
            // Cursor line '_'
            g.DrawLine(&iconPen, iconX + 11.0f, iconY + 12.0f, iconX + 15.5f, iconY + 12.0f);

            curX += iconSize + 8.0f;
        } else {
            s_consoleIconRect = { 0, 0, 0, 0 };
        }

        // 3. ONLINE PLAYERS (Admin Only) -> Third
        if (showAdminOnline) {
            float adminX = curX + 2.0f;
            float adminY = 7.0f;

            // Draw small User/Admin silhouette icon in pure WHITE (Requirement 19)
            Gdiplus::Color adminCol(255, 255, 255, 255); // Pure white
            Gdiplus::Pen adminPen(adminCol, 1.3f);
            Gdiplus::SolidBrush adminBrush(adminCol);

            // Head circle
            g.DrawEllipse(&adminPen, adminX + 2.0f, adminY, 6.0f, 6.0f);
            // Shoulder arc
            g.DrawArc(&adminPen, adminX, adminY + 7.0f, 10.0f, 8.0f, 190.0f, 160.0f);

            // Online count text
            wchar_t onlineStr[32];
            swprintf_s(onlineStr, L"%u", g_onlineCount.load());

            Gdiplus::Font fontOnline(L"Segoe UI", 9.5f, Gdiplus::FontStyleBold);
            g.DrawString(onlineStr, -1, &fontOnline, Gdiplus::PointF(adminX + 13.0f, 5.0f), &adminBrush);
        }
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
