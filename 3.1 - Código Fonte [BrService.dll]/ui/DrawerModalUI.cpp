#include "DrawerModalUI.h"
#include "UICommon.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../cvar/CVarManager.h"
#include "../config/BrConfig.h"
#include "../model3d/CryModelBridge.h"
#include <algorithm>

namespace BrService {

static const wchar_t* kDrawerClassName = L"BrService_DrawerModal";
static int s_modalW = 460;
static int s_modalH = 680;
static bool s_draggingFov = false;
static bool s_draggingCam = false;
static RECT s_closeBtnRect = { 0, 0, 0, 0 };
static RECT s_resetBtnRect = { 0, 0, 0, 0 };
static RECT s_fovSliderRect = { 0, 0, 0, 0 };
static RECT s_camSliderRect = { 0, 0, 0, 0 };
static RECT s_fps60Rect = { 0, 0, 0, 0 };
static RECT s_fps144Rect = { 0, 0, 0, 0 };
static RECT s_fpsMaxRect = { 0, 0, 0, 0 };
static RECT s_tbToggleRect = { 0, 0, 0, 0 };
static RECT s_anisoToggleRect = { 0, 0, 0, 0 };

bool DrawerModalUI::Initialize(HINSTANCE hInst) {
    WNDCLASSEXW wc = { sizeof(WNDCLASSEXW) };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = kDrawerClassName;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.style = CS_HREDRAW | CS_VREDRAW;

    if (!RegisterClassExW(&wc)) {
        DWORD err = GetLastError();
        if (err != ERROR_CLASS_ALREADY_EXISTS) {
            LogError("Falha ao registrar classe DrawerModal: %lu", err);
            return false;
        }
    }

    g_hDrawerModalWnd = CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
        kDrawerClassName,
        L"Aion Combat Analysis & Console",
        WS_POPUP,
        0, 0, s_modalW, s_modalH,
        nullptr, nullptr, hInst, nullptr
    );

    if (!g_hDrawerModalWnd) {
        LogError("Falha ao criar janela DrawerModal: %lu", GetLastError());
        return false;
    }

    LogInfo("DrawerModalUI inicializado com sucesso.");
    return true;
}

void DrawerModalUI::Shutdown() {
    if (g_hDrawerModalWnd && IsWindow(g_hDrawerModalWnd)) {
        DestroyWindow(g_hDrawerModalWnd);
        g_hDrawerModalWnd = nullptr;
    }
}

void DrawerModalUI::Toggle() {
    if (!g_featConsole.load()) return;
    if (g_isDrawerOpen.load()) Close();
    else Open();
}

void DrawerModalUI::Open() {
    if (!g_featConsole.load()) return;
    g_isDrawerOpen = true;
    if (g_hDrawerModalWnd && !g_isLoadingScreen.load() && g_isGameActive.load()) {
        ShowWindow(g_hDrawerModalWnd, SW_SHOWNOACTIVATE);
        SetTimer(g_hDrawerModalWnd, 1, 33, nullptr); // ~30 FPS timer for 3D model rotation & charts
        Repaint();
    }
}

void DrawerModalUI::Close() {
    g_isDrawerOpen = false;
    if (g_hDrawerModalWnd) {
        KillTimer(g_hDrawerModalWnd, 1);
        ShowWindow(g_hDrawerModalWnd, SW_HIDE);
    }
    BrConfig::Save();
}

bool DrawerModalUI::IsOpen() {
    return g_isDrawerOpen.load();
}

void DrawerModalUI::UpdatePosition(int gameX, int gameY, int gameW, int gameH) {
    if (!g_hDrawerModalWnd) return;

    // Height = 60% of game window height, vertically centered
    s_modalH = static_cast<int>(gameH * 0.60f);
    if (s_modalH < 480) s_modalH = 480;

    int modalX = gameX + 24; // Detached by 24px from left lateral edge
    int modalY = gameY + (gameH - s_modalH) / 2; // Centered vertically

    SetWindowPos(g_hDrawerModalWnd, HWND_TOPMOST, modalX, modalY, s_modalW, s_modalH,
                 SWP_NOACTIVATE | (g_isDrawerOpen.load() && !g_isLoadingScreen.load() && g_isGameActive.load() ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
    Repaint();
}

void DrawerModalUI::Repaint() {
    if (!g_hDrawerModalWnd || !IsWindow(g_hDrawerModalWnd)) return;
    Paint(g_hDrawerModalWnd);
}

void DrawerModalUI::Paint(HWND hwnd) {
    HDC screenDC = GetDC(nullptr);
    HDC memDC = CreateCompatibleDC(screenDC);

    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = s_modalW;
    bmi.bmiHeader.biHeight = -s_modalH;
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

        float W = (float)s_modalW;
        float H = (float)s_modalH;

        // 1. Dark Glassmorphism Backdrop with Rounded Corners (16px)
        Gdiplus::SolidBrush bgBrush(UICommon::ColGlassBack);
        UICommon::FillRoundRectangle(g, &bgBrush, 2.0f, 2.0f, W - 4.0f, H - 4.0f, 16.0f);

        // Subtle Gold Trim Border
        Gdiplus::Pen borderPen(UICommon::ColGoldDim, 1.4f);
        UICommon::DrawRoundRectangle(g, &borderPen, 2.0f, 2.0f, W - 4.0f, H - 4.0f, 16.0f);

        // 2. Title Bar / Header (Aion 2 Style)
        Gdiplus::SolidBrush headerBrush(UICommon::ColGlassHeader);
        UICommon::FillRoundRectangle(g, &headerBrush, 3.0f, 3.0f, W - 6.0f, 44.0f, 14.0f);

        // Title text & Icon
        Gdiplus::Font fontTitle(L"Segoe UI", 10.5f, Gdiplus::FontStyleBold);
        Gdiplus::SolidBrush textWhite(UICommon::ColTextWhite);
        Gdiplus::SolidBrush textGold(UICommon::ColGoldAccent);
        Gdiplus::SolidBrush textMuted(UICommon::ColTextMuted);

        g.DrawString(L"AION CLASSIC 5.0", -1, &fontTitle, Gdiplus::PointF(16.0f, 12.0f), &textGold);

        Gdiplus::Font fontSubTitle(L"Segoe UI", 8.5f, Gdiplus::FontStyleRegular);
        g.DrawString(L"| Combat Analysis & Console", -1, &fontSubTitle, Gdiplus::PointF(138.0f, 14.0f), &textMuted);

        // Close Button [X]
        s_closeBtnRect = { s_modalW - 38, 10, s_modalW - 14, 34 };
        Gdiplus::Pen closePen(UICommon::ColTextMuted, 1.8f);
        g.DrawLine(&closePen, (float)s_closeBtnRect.left + 6, (float)s_closeBtnRect.top + 6,
                              (float)s_closeBtnRect.right - 6, (float)s_closeBtnRect.bottom - 6);
        g.DrawLine(&closePen, (float)s_closeBtnRect.right - 6, (float)s_closeBtnRect.top + 6,
                              (float)s_closeBtnRect.left + 6, (float)s_closeBtnRect.bottom - 6);

        // Separator line
        Gdiplus::Pen sepPen(Gdiplus::Color(45, 200, 205, 220), 1.0f);
        g.DrawLine(&sepPen, 16.0f, 48.0f, W - 16.0f, 48.0f);

        // 3. Top Section: Shugo Console Controls
        float curY = 54.0f;
        Gdiplus::Font fontSection(L"Segoe UI", 8.5f, Gdiplus::FontStyleBold);
        Gdiplus::Font fontLabel(L"Segoe UI", 8.0f, Gdiplus::FontStyleRegular);
        Gdiplus::SolidBrush trackBrush(Gdiplus::Color(50, 80, 90, 110));
        Gdiplus::SolidBrush thumbBrush(UICommon::ColGoldAccent);

        g.DrawString(L"SHUGO CONSOLE (MOTOR GRÁFICO)", -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
        curY += 20.0f;

        // FOV Slider (if enabled)
        if (g_featFov.load()) {
            wchar_t fovBuf[64];
            swprintf_s(fovBuf, L"Campo de Visão (FOV): %.0f°", g_cvarFov.load());
            g.DrawString(fovBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

            s_fovSliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
            g.FillRectangle(&trackBrush, (float)s_fovSliderRect.left, (float)s_fovSliderRect.top, (float)(s_fovSliderRect.right - s_fovSliderRect.left), 8.0f);

            float fovPct = (g_cvarFov.load() - 60.0f) / (120.0f - 60.0f);
            fovPct = std::clamp(fovPct, 0.0f, 1.0f);
            float thumbX = s_fovSliderRect.left + fovPct * (s_fovSliderRect.right - s_fovSliderRect.left - 12);
            g.FillEllipse(&thumbBrush, thumbX, (float)s_fovSliderRect.top - 2.0f, 12.0f, 12.0f);
            curY += 22.0f;
        } else {
            s_fovSliderRect = { 0, 0, 0, 0 };
        }

        // CamMax Slider (if enabled)
        if (g_featCamMax.load()) {
            wchar_t camBuf[64];
            swprintf_s(camBuf, L"Distância da Câmera: %.0fm", g_cvarCamMax.load());
            g.DrawString(camBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

            s_camSliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
            g.FillRectangle(&trackBrush, (float)s_camSliderRect.left, (float)s_camSliderRect.top, (float)(s_camSliderRect.right - s_camSliderRect.left), 8.0f);

            float camPct = (g_cvarCamMax.load() - 5.0f) / (45.0f - 5.0f);
            camPct = std::clamp(camPct, 0.0f, 1.0f);
            float thumbCamX = s_camSliderRect.left + camPct * (s_camSliderRect.right - s_camSliderRect.left - 12);
            g.FillEllipse(&thumbBrush, thumbCamX, (float)s_camSliderRect.top - 2.0f, 12.0f, 12.0f);
            curY += 24.0f;
        } else {
            s_camSliderRect = { 0, 0, 0, 0 };
        }

        // FPS Limiters & Toggles in a compact row (if enabled)
        if (g_featFpsUnlock.load()) {
            g.DrawString(L"FPS Máx:", -1, &fontLabel, Gdiplus::PointF(16.0f, curY + 2), &textWhite);

            auto drawFpsBtn = [&](RECT& r, int x, int val, const wchar_t* txt) {
                r = { x, (int)curY, x + 38, (int)curY + 18 };
                bool active = (g_cvarMaxFps.load() == val);
                Gdiplus::SolidBrush b(active ? Gdiplus::Color(100, 215, 170, 50) : Gdiplus::Color(40, 60, 70, 85));
                UICommon::FillRoundRectangle(g, &b, (float)r.left, (float)r.top, (float)(r.right - r.left), 18.0f, 3.0f);
                Gdiplus::SolidBrush t(active ? UICommon::ColTextWhite : UICommon::ColTextMuted);
                g.DrawString(txt, -1, &fontLabel, Gdiplus::PointF((float)r.left + 5, (float)r.top + 2), &t);
            };

            drawFpsBtn(s_fps60Rect, 72, 60, L"60");
            drawFpsBtn(s_fps144Rect, 114, 144, L"144");
            drawFpsBtn(s_fpsMaxRect, 156, 0, L"MAX");

            // Triple Buffering & Anisotropic
            s_tbToggleRect = { 216, (int)curY, 320, (int)curY + 18 };
            bool tb = g_cvarTripleBuffering.load();
            Gdiplus::SolidBrush tbBrush(tb ? Gdiplus::Color(60, 45, 230, 45) : Gdiplus::Color(30, 80, 80, 80));
            UICommon::FillRoundRectangle(g, &tbBrush, (float)s_tbToggleRect.left, (float)s_tbToggleRect.top, (float)(s_tbToggleRect.right - s_tbToggleRect.left), 18.0f, 3.0f);
            g.DrawString(tb ? L"✔ TriBuffer" : L"✖ TriBuffer", -1, &fontLabel, Gdiplus::PointF((float)s_tbToggleRect.left + 6, (float)s_tbToggleRect.top + 2), &textWhite);

            s_anisoToggleRect = { 328, (int)curY, 436, (int)curY + 18 };
            bool aniso = g_cvarAnisotropic.load();
            Gdiplus::SolidBrush anisoBrush(aniso ? Gdiplus::Color(60, 45, 230, 45) : Gdiplus::Color(30, 80, 80, 80));
            UICommon::FillRoundRectangle(g, &anisoBrush, (float)s_anisoToggleRect.left, (float)s_anisoToggleRect.top, (float)(s_anisoToggleRect.right - s_anisoToggleRect.left), 18.0f, 3.0f);
            g.DrawString(aniso ? L"✔ 16x Aniso" : L"✖ 16x Aniso", -1, &fontLabel, Gdiplus::PointF((float)s_anisoToggleRect.left + 6, (float)s_anisoToggleRect.top + 2), &textWhite);

            curY += 28.0f;
        } else {
            s_fps60Rect = s_fps144Rect = s_fpsMaxRect = s_tbToggleRect = s_anisoToggleRect = { 0, 0, 0, 0 };
        }

        g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
        curY += 10.0f;

        // 4. Main Section: DPS METER (if enabled)
        if (g_featDpsMeterUI.load()) {
            std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

            // Target Banner
            Gdiplus::Font fontTarget(L"Segoe UI", 9.5f, Gdiplus::FontStyleBold);
            std::wstring targetTitle = L"Alvo: " + std::wstring(g_currentTarget.name.begin(), g_currentTarget.name.end());
            if (g_currentTarget.level > 0) {
                targetTitle += L" [Lv. " + std::to_wstring(g_currentTarget.level) + L"]";
            }
            g.DrawString(targetTitle.c_str(), -1, &fontTarget, Gdiplus::PointF(16.0f, curY), &textWhite);

            // Health bar under target
            curY += 18.0f;
            float hpW = W - 32.0f;
            Gdiplus::SolidBrush hpBg(Gdiplus::Color(60, 30, 35, 45));
            UICommon::FillRoundRectangle(g, &hpBg, 16.0f, curY, hpW, 8.0f, 2.0f);

            float hpPct = g_currentTarget.maxHp > 0 ? (float)g_currentTarget.currentHp / (float)g_currentTarget.maxHp : 1.0f;
            hpPct = std::clamp(hpPct, 0.0f, 1.0f);
            if (hpPct > 0.0f) {
                Gdiplus::SolidBrush hpFill(Gdiplus::Color(255, 220, 50, 60)); // Crimson HP
                UICommon::FillRoundRectangle(g, &hpFill, 16.0f, curY, hpW * hpPct, 8.0f, 2.0f);
            }
            curY += 16.0f;

            // Combat Highlight Cards (Time, DPS, Total Damage, Golden Button)
            float cardW = (W - 32.0f - 24.0f) / 3.0f;
            auto drawMetricCard = [&](float cx, const wchar_t* title, const std::wstring& val, Gdiplus::Color valCol) {
                Gdiplus::SolidBrush cardBg(Gdiplus::Color(40, 20, 26, 36));
                UICommon::FillRoundRectangle(g, &cardBg, cx, curY, cardW, 44.0f, 6.0f);
                Gdiplus::Pen cardBorder(Gdiplus::Color(40, 180, 190, 210), 1.0f);
                UICommon::DrawRoundRectangle(g, &cardBorder, cx, curY, cardW, 44.0f, 6.0f);

                Gdiplus::Font fT(L"Segoe UI", 7.5f, Gdiplus::FontStyleRegular);
                g.DrawString(title, -1, &fT, Gdiplus::PointF(cx + 8, curY + 5), &textMuted);

                Gdiplus::Font fV(L"Segoe UI", 11.0f, Gdiplus::FontStyleBold);
                Gdiplus::SolidBrush bV(valCol);
                g.DrawString(val.c_str(), -1, &fV, Gdiplus::PointF(cx + 8, curY + 18), &bV);
            };

            drawMetricCard(16.0f, L"TEMPO DE BATALHA", UICommon::FormatTime(g_battleDurationSeconds.load()), UICommon::ColTextWhite);
            drawMetricCard(16.0f + cardW + 12.0f, L"DPS TOTAL", UICommon::FormatNumber(g_totalBattleDps.load()), UICommon::ColGoldAccent);
            drawMetricCard(16.0f + (cardW + 12.0f) * 2.0f, L"DANO TOTAL", UICommon::FormatNumber(g_totalBattleDamage.load()), UICommon::ColNeonGreen);
            curY += 52.0f;

            // Golden Start/Reset Action Button (Ctrl + X)
            s_resetBtnRect = { 16, (int)curY, (int)W - 16, (int)curY + 28 };
            Gdiplus::LinearGradientBrush btnBrush(
                Gdiplus::PointF(16.0f, curY), Gdiplus::PointF(W - 16.0f, curY),
                Gdiplus::Color(220, 215, 170, 50),
                Gdiplus::Color(220, 175, 130, 30)
            );
            UICommon::FillRoundRectangle(g, &btnBrush, (float)s_resetBtnRect.left, (float)s_resetBtnRect.top, (float)(s_resetBtnRect.right - s_resetBtnRect.left), 28.0f, 5.0f);

            Gdiplus::Font btnFont(L"Segoe UI", 9.0f, Gdiplus::FontStyleBold);
            Gdiplus::SolidBrush btnText(Gdiplus::Color(255, 18, 14, 6)); // Dark readable text on gold
            Gdiplus::StringFormat centerFmt;
            centerFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
            centerFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
            Gdiplus::RectF btnRectF((float)s_resetBtnRect.left, (float)s_resetBtnRect.top, (float)(s_resetBtnRect.right - s_resetBtnRect.left), 28.0f);
            g.DrawString(L"⚡ [Ctrl + X] Iniciar / Resetar Análise", -1, &btnFont, btnRectF, &centerFmt, &btnText);
            curY += 36.0f;

            // Visual Charts Row: Fibonacci Curve (left) + Radar Chart (right)
            float chartH = 92.0f;
            float fiboW = 230.0f;
            g.DrawString(L"PROGRESSÃO BURST (FIBONACCI)", -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textMuted);
            UICommon::DrawFibonacciCurve(g, 16.0f, curY + 14.0f, fiboW, chartH - 18.0f, g_fibonacciCurve);

            // Radar Chart on the right
            float radarCx = W - 95.0f;
            float radarCy = curY + chartH * 0.52f;
            UICommon::DrawRadarChart(g, radarCx, radarCy, 34.0f,
                                    g_currentRadar.burst, g_currentRadar.sustain,
                                    g_currentRadar.critRate, g_currentRadar.accuracy, g_currentRadar.efficiency);

            curY += chartH + 8.0f;
            g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
            curY += 8.0f;

            // Player & Skill Rankings Table
            g.DrawString(L"CLASSIFICAÇÃO DE COMBATE / SKILLS", -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
            curY += 18.0f;

            // Table Header
            Gdiplus::Font fTh(L"Segoe UI", 7.5f, Gdiplus::FontStyleBold);
            g.DrawString(L"JOGADOR / SKILL", -1, &fTh, Gdiplus::PointF(18.0f, curY), &textMuted);
            g.DrawString(L"DANO TOTAL", -1, &fTh, Gdiplus::PointF(160.0f, curY), &textMuted);
            g.DrawString(L"DPS", -1, &fTh, Gdiplus::PointF(245.0f, curY), &textMuted);
            g.DrawString(L"PARTIC.", -1, &fTh, Gdiplus::PointF(295.0f, curY), &textMuted);
            curY += 14.0f;

            // Table Rows
            Gdiplus::Font fRow(L"Segoe UI", 8.0f, Gdiplus::FontStyleRegular);
            int rowsDrawn = 0;
            float rowHeight = 22.0f;

            for (const auto& player : g_playerRankings) {
                if (rowsDrawn >= 4 || curY + rowHeight > H - 120.0f) break;

                // Background bar representing damage share
                float barW = 120.0f * (player.percentage / 100.0f);
                Gdiplus::SolidBrush barB(Gdiplus::Color(45, 215, 65, 75));
                UICommon::FillRoundRectangle(g, &barB, 16.0f, curY, barW, rowHeight - 2.0f, 3.0f);

                std::wstring wName(player.name.begin(), player.name.end());
                g.DrawString(wName.c_str(), -1, &fRow, Gdiplus::PointF(20.0f, curY + 2), &textWhite);

                std::wstring wDmg = UICommon::FormatNumber(player.totalDamage);
                g.DrawString(wDmg.c_str(), -1, &fRow, Gdiplus::PointF(160.0f, curY + 2), &textGold);

                std::wstring wDps = UICommon::FormatNumber(player.dps);
                g.DrawString(wDps.c_str(), -1, &fRow, Gdiplus::PointF(245.0f, curY + 2), &textWhite);

                wchar_t pctBuf[32];
                swprintf_s(pctBuf, L"%.0f%%", player.percentage);
                g.DrawString(pctBuf, -1, &fRow, Gdiplus::PointF(298.0f, curY + 2), &textMuted);

                curY += rowHeight;
                rowsDrawn++;
            }

            // If no players yet, show mock row
            if (rowsDrawn == 0) {
                g.DrawString(L"Aguardando acoes de combate...", -1, &fRow, Gdiplus::PointF(20.0f, curY + 4), &textMuted);
                curY += 24.0f;
            }
        } else {
            s_resetBtnRect = { 0, 0, 0, 0 };
        }

        // 5. 3D Model Miniature Preview in Lower-Right Corner (if enabled)
        if (g_featModel3D.load()) {
            float previewW = 110.0f;
            float previewH = 110.0f;
            float previewX = W - previewW - 14.0f;
            float previewY = H - previewH - 12.0f;

            CryModelBridge::RenderThumbnail(g, previewX, previewY, previewW, previewH);
        }
    }

    // Blend to layered window
    POINT ptSrc = { 0, 0 };
    SIZE szWindow = { s_modalW, s_modalH };
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

LRESULT CALLBACK DrawerModalUI::WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_TIMER:
        Repaint();
        return 0;

    case WM_LBUTTONDOWN: {
        int mx = LOWORD(lParam);
        int my = HIWORD(lParam);

        // Close Button
        if (mx >= s_closeBtnRect.left && mx <= s_closeBtnRect.right &&
            my >= s_closeBtnRect.top && my <= s_closeBtnRect.bottom) {
            Close();
            return 0;
        }

        // Reset Button
        if (mx >= s_resetBtnRect.left && mx <= s_resetBtnRect.right &&
            my >= s_resetBtnRect.top && my <= s_resetBtnRect.bottom) {
            ResetCombatSession();
            Repaint();
            return 0;
        }

        // FPS Limiters
        auto checkFpsBtn = [&](RECT& r, int fps) {
            if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                CVarManager::SetMaxFps(fps);
                Repaint();
                return true;
            }
            return false;
        };
        if (checkFpsBtn(s_fps60Rect, 60)) return 0;
        if (checkFpsBtn(s_fps144Rect, 144)) return 0;
        if (checkFpsBtn(s_fpsMaxRect, 0)) return 0;

        // Toggles
        if (mx >= s_tbToggleRect.left && mx <= s_tbToggleRect.right &&
            my >= s_tbToggleRect.top && my <= s_tbToggleRect.bottom) {
            CVarManager::SetTripleBuffering(!g_cvarTripleBuffering.load());
            Repaint();
            return 0;
        }

        if (mx >= s_anisoToggleRect.left && mx <= s_anisoToggleRect.right &&
            my >= s_anisoToggleRect.top && my <= s_anisoToggleRect.bottom) {
            CVarManager::SetAnisotropic(!g_cvarAnisotropic.load());
            Repaint();
            return 0;
        }

        // Sliders Dragging Start
        if (mx >= s_fovSliderRect.left && mx <= s_fovSliderRect.right &&
            my >= s_fovSliderRect.top - 6 && my <= s_fovSliderRect.bottom + 6) {
            s_draggingFov = true;
            SetCapture(hwnd);
        } else if (mx >= s_camSliderRect.left && mx <= s_camSliderRect.right &&
                   my >= s_camSliderRect.top - 6 && my <= s_camSliderRect.bottom + 6) {
            s_draggingCam = true;
            SetCapture(hwnd);
        }
        return 0;
    }

    case WM_MOUSEMOVE: {
        int mx = LOWORD(lParam);
        if (s_draggingFov) {
            float pct = (float)(mx - s_fovSliderRect.left) / (float)(s_fovSliderRect.right - s_fovSliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float fov = 60.0f + pct * (120.0f - 60.0f);
            CVarManager::SetFov(fov);
            Repaint();
        } else if (s_draggingCam) {
            float pct = (float)(mx - s_camSliderRect.left) / (float)(s_camSliderRect.right - s_camSliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float cam = 5.0f + pct * (45.0f - 5.0f);
            CVarManager::SetCameraMax(cam);
            Repaint();
        }
        return 0;
    }

    case WM_LBUTTONUP: {
        if (s_draggingFov || s_draggingCam) {
            s_draggingFov = false;
            s_draggingCam = false;
            ReleaseCapture();
            BrConfig::Save();
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
