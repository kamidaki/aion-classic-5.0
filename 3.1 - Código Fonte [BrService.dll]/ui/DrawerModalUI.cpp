#include "DrawerModalUI.h"
#include "UICommon.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../core/I18n.h"
#include "../cvar/CVarManager.h"
#include "../config/BrConfig.h"
#include "../model3d/CryModelBridge.h"
#include "../combo/ComboUI.h"
#include "../combo/ComboTypes.h"
#include "../network/WebSocketClient.h"
#include <algorithm>
#include <cmath>

namespace BrService {

static const wchar_t* kDrawerClassName = L"BrService_DrawerModal";
static int s_modalW = 460;
static int s_modalH = 580;
static bool s_isSettingsOpen = false;

static bool s_draggingFov = false;
static bool s_draggingCam = false;
static bool s_draggingOpacity = false;
static bool s_draggingComboOpacity = false;

// Main View Rects
static RECT s_closeBtnRect = { 0, 0, 0, 0 };
static RECT s_settingsBtnRect = { 0, 0, 0, 0 };
static RECT s_resetBtnRect = { 0, 0, 0, 0 };
static RECT s_fovSliderRect = { 0, 0, 0, 0 };
static RECT s_camSliderRect = { 0, 0, 0, 0 };
static RECT s_fps60Rect = { 0, 0, 0, 0 };
static RECT s_fps144Rect = { 0, 0, 0, 0 };
static RECT s_fpsMaxRect = { 0, 0, 0, 0 };
static RECT s_tbToggleRect = { 0, 0, 0, 0 };
static RECT s_anisoToggleRect = { 0, 0, 0, 0 };

// Settings View Rects
static RECT s_presetNormalRect = { 0, 0, 0, 0 };
static RECT s_presetWideRect = { 0, 0, 0, 0 };
static RECT s_presetCompactRect = { 0, 0, 0, 0 };
static RECT s_widthMinusRect = { 0, 0, 0, 0 };
static RECT s_widthPlusRect = { 0, 0, 0, 0 };
static RECT s_heightMinusRect = { 0, 0, 0, 0 };
static RECT s_heightPlusRect = { 0, 0, 0, 0 };
static RECT s_opacitySliderRect = { 0, 0, 0, 0 };
static RECT s_compactToggleRect = { 0, 0, 0, 0 };
static RECT s_hideConsoleToggleRect = { 0, 0, 0, 0 };
static RECT s_comboToggleRect = { 0, 0, 0, 0 };
static RECT s_comboOpacitySliderRect = { 0, 0, 0, 0 };
static RECT s_comboScale70Rect = { 0, 0, 0, 0 };
static RECT s_comboScale100Rect = { 0, 0, 0, 0 };
static RECT s_comboScale130Rect = { 0, 0, 0, 0 };
static RECT s_comboScaleMinusRect = { 0, 0, 0, 0 };
static RECT s_comboScalePlusRect = { 0, 0, 0, 0 };
static RECT s_saveSettingsBtnRect = { 0, 0, 0, 0 };

bool DrawerModalUI::Initialize(HINSTANCE hInst) {
    s_modalW = std::clamp(g_drawerW.load(), 400, 640);
    s_modalH = std::clamp(g_drawerH.load(), 480, 780);

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
        L"Painel Academy",
        WS_POPUP,
        0, 0, s_modalW, s_modalH,
        nullptr, nullptr, hInst, nullptr
    );

    if (!g_hDrawerModalWnd) {
        LogError("Falha ao criar janela DrawerModal: %lu", GetLastError());
        return false;
    }

    LogInfo("DrawerModalUI inicializado com sucesso (%dx%d, Opacidade=%d).",
            s_modalW, s_modalH, g_drawerOpacity.load());
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
        SetTimer(g_hDrawerModalWnd, 1, 33, nullptr); // ~30 FPS timer
        Repaint();
    }
}

void DrawerModalUI::Close() {
    g_isDrawerOpen = false;
    s_isSettingsOpen = false;
    if (g_hDrawerModalWnd) {
        KillTimer(g_hDrawerModalWnd, 1);
        ShowWindow(g_hDrawerModalWnd, SW_HIDE);
    }
    BrConfig::Save();
}

void DrawerModalUI::Hide() {
    if (g_hDrawerModalWnd && IsWindow(g_hDrawerModalWnd)) {
        KillTimer(g_hDrawerModalWnd, 1);
        ShowWindow(g_hDrawerModalWnd, SW_HIDE);
    }
}

void DrawerModalUI::RestoreIfOpen() {
    if (!g_featConsole.load()) return;
    if (g_isDrawerOpen.load() && g_hDrawerModalWnd && !g_isLoadingScreen.load() && g_isGameActive.load()) {
        ShowWindow(g_hDrawerModalWnd, SW_SHOWNOACTIVATE);
        SetTimer(g_hDrawerModalWnd, 1, 33, nullptr);
        Repaint();
    }
}

bool DrawerModalUI::IsOpen() {
    return g_isDrawerOpen.load();
}

void DrawerModalUI::UpdatePosition(int gameX, int gameY, int gameW, int gameH) {
    if (!g_hDrawerModalWnd) return;

    s_modalW = std::clamp(g_drawerW.load(), 400, 640);
    s_modalH = std::clamp(g_drawerH.load(), 480, 780);
    if (s_modalH > gameH - 30) s_modalH = gameH - 30;

    int modalX = gameX + 24; // 24px detachment from left edge
    int modalY = gameY + (gameH - s_modalH) / 2; // Centered vertically

    bool shouldBeVisible = g_featConsole.load() && g_isDrawerOpen.load() && g_isInWorld.load() && !g_isLoadingScreen.load() && g_isGameActive.load();
    SetWindowPos(g_hDrawerModalWnd, HWND_TOPMOST, modalX, modalY, s_modalW, s_modalH,
                 SWP_NOACTIVATE | (shouldBeVisible ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
    if (shouldBeVisible) {
        Repaint();
    }
}

void DrawerModalUI::ResizeDrawer(int newW, int newH) {
    g_drawerW = std::clamp(newW, 400, 640);
    g_drawerH = std::clamp(newH, 480, 780);

    HWND hGame = g_gameHwnd.load();
    if (hGame && IsWindow(hGame)) {
        RECT gr = {};
        GetWindowRect(hGame, &gr);
        UpdatePosition(gr.left, gr.top, gr.right - gr.left, gr.bottom - gr.top);
    } else {
        s_modalW = g_drawerW.load();
        s_modalH = g_drawerH.load();
        Repaint();
    }
    BrConfig::Save();
}

void DrawerModalUI::Repaint() {
    if (!g_hDrawerModalWnd || !IsWindow(g_hDrawerModalWnd)) return;
    Paint(g_hDrawerModalWnd);
}

// Helper: Programmatic sleek gear icon
static void DrawGearIcon(Gdiplus::Graphics& g, float cx, float cy, float radius, Gdiplus::Pen* pen) {
    float innerR = radius * 0.45f;
    float toothLen = radius * 0.35f;
    g.DrawEllipse(pen, cx - innerR, cy - innerR, innerR * 2.0f, innerR * 2.0f);

    const int numTeeth = 6;
    for (int i = 0; i < numTeeth; ++i) {
        float angle = i * (3.14159265f / 3.0f);
        float x1 = cx + cosf(angle) * (innerR + 1.0f);
        float y1 = cy + sinf(angle) * (innerR + 1.0f);
        float x2 = cx + cosf(angle) * (innerR + toothLen + 1.0f);
        float y2 = cy + sinf(angle) * (innerR + toothLen + 1.0f);
        g.DrawLine(pen, x1, y1, x2, y2);
    }
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

        float W = static_cast<float>(s_modalW);
        float H = static_cast<float>(s_modalH);

        // 1. Dark Glassmorphism Backdrop with Rounded Corners (16px)
        Gdiplus::SolidBrush bgBrush(UICommon::ColGlassBack);
        UICommon::FillRoundRectangle(g, &bgBrush, 2.0f, 2.0f, W - 4.0f, H - 4.0f, 16.0f);

        // Subtle Gold Trim Border
        Gdiplus::Pen borderPen(UICommon::ColGoldDim, 1.4f);
        UICommon::DrawRoundRectangle(g, &borderPen, 2.0f, 2.0f, W - 4.0f, H - 4.0f, 16.0f);

        // 2. Title Bar / Header
        Gdiplus::SolidBrush headerBrush(UICommon::ColGlassHeader);
        UICommon::FillRoundRectangle(g, &headerBrush, 3.0f, 3.0f, W - 6.0f, 44.0f, 14.0f);

        Gdiplus::Font fontTitle(L"Segoe UI", 10.5f, Gdiplus::FontStyleBold);
        Gdiplus::SolidBrush textWhite(UICommon::ColTextWhite);
        Gdiplus::SolidBrush textGold(UICommon::ColGoldAccent);
        Gdiplus::SolidBrush textMuted(UICommon::ColTextMuted);

        g.DrawString(I18n::TitlePanel(), -1, &fontTitle, Gdiplus::PointF(16.0f, 12.0f), &textGold);

        Gdiplus::Font fontSubTitle(L"Segoe UI", 8.5f, Gdiplus::FontStyleRegular);
        if (s_isSettingsOpen) {
            g.DrawString(I18n::SubtitleSettings(), -1, &fontSubTitle, Gdiplus::PointF(160.0f, 14.0f), &textMuted);
        } else {
            g.DrawString(I18n::TitleDpsMeter(), -1, &fontSubTitle, Gdiplus::PointF(160.0f, 14.0f), &textMuted);
        }

        // Settings Button [⚙]
        s_settingsBtnRect = { s_modalW - 68, 10, s_modalW - 44, 34 };
        Gdiplus::SolidBrush settingsBg(s_isSettingsOpen ? Gdiplus::Color(80, 215, 170, 50) : Gdiplus::Color(35, 60, 70, 85));
        UICommon::FillRoundRectangle(g, &settingsBg, (float)s_settingsBtnRect.left, (float)s_settingsBtnRect.top, 24.0f, 24.0f, 4.0f);
        Gdiplus::Pen gearPen(s_isSettingsOpen ? UICommon::ColGoldAccent : UICommon::ColTextMuted, 1.6f);
        DrawGearIcon(g, (float)s_settingsBtnRect.left + 12.0f, (float)s_settingsBtnRect.top + 12.0f, 6.0f, &gearPen);

        // Close Button [X]
        s_closeBtnRect = { s_modalW - 38, 10, s_modalW - 14, 34 };
        Gdiplus::Pen closePen(UICommon::ColTextMuted, 1.8f);
        g.DrawLine(&closePen, (float)s_closeBtnRect.left + 6, (float)s_closeBtnRect.top + 6,
                              (float)s_closeBtnRect.right - 6, (float)s_closeBtnRect.bottom - 6);
        g.DrawLine(&closePen, (float)s_closeBtnRect.right - 6, (float)s_closeBtnRect.top + 6,
                              (float)s_closeBtnRect.left + 6, (float)s_closeBtnRect.bottom - 6);

        // Separator line under header
        Gdiplus::Pen sepPen(Gdiplus::Color(45, 200, 205, 220), 1.0f);
        g.DrawLine(&sepPen, 16.0f, 48.0f, W - 16.0f, 48.0f);

        float curY = 56.0f;
        Gdiplus::Font fontSection(L"Segoe UI", 8.5f, Gdiplus::FontStyleBold);
        Gdiplus::Font fontLabel(L"Segoe UI", 8.0f, Gdiplus::FontStyleRegular);
        Gdiplus::Font fontSubLabel(L"Segoe UI", 7.5f, Gdiplus::FontStyleRegular);
        Gdiplus::SolidBrush trackBrush(Gdiplus::Color(50, 80, 90, 110));
        Gdiplus::SolidBrush thumbBrush(UICommon::ColGoldAccent);

        // =========================================================================
        // VIEW A: SETTINGS OVERLAY
        // =========================================================================
        if (s_isSettingsOpen) {
            // Zero out main view rects
            s_resetBtnRect = s_fovSliderRect = s_camSliderRect = s_fps60Rect = s_fps144Rect = s_fpsMaxRect = s_tbToggleRect = s_anisoToggleRect = { 0, 0, 0, 0 };

            g.DrawString(I18n::TitleSettings(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
            curY += 22.0f;

            // 1. Window Dimensions
            wchar_t dimBuf[64];
            swprintf_s(dimBuf, I18n::PanelDimensions(), s_modalW, s_modalH);
            g.DrawString(dimBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);
            curY += 20.0f;

            // Presets
            auto drawPresetBtn = [&](RECT& r, int x, int w, const wchar_t* txt, bool active) {
                r = { x, (int)curY, x + w, (int)curY + 22 };
                Gdiplus::SolidBrush b(active ? Gdiplus::Color(100, 215, 170, 50) : Gdiplus::Color(40, 60, 70, 85));
                UICommon::FillRoundRectangle(g, &b, (float)r.left, (float)r.top, (float)(r.right - r.left), 22.0f, 4.0f);
                Gdiplus::SolidBrush t(active ? UICommon::ColTextWhite : UICommon::ColTextMuted);
                g.DrawString(txt, -1, &fontSubLabel, Gdiplus::PointF((float)r.left + 8, (float)r.top + 4), &t);
            };

            bool isNormal = (s_modalW == 460 && s_modalH == 580);
            bool isWide = (s_modalW == 560 && s_modalH == 680);
            bool isCompact = (s_modalW == 420 && s_modalH == 500);

            drawPresetBtn(s_presetNormalRect, 16, 120, I18n::PresetDefault(), isNormal);
            drawPresetBtn(s_presetWideRect, 144, 120, I18n::PresetWide(), isWide);
            drawPresetBtn(s_presetCompactRect, 272, 130, I18n::PresetCompact(), isCompact);
            curY += 28.0f;

            // Manual adjustments row
            g.DrawString(I18n::FineTune(), -1, &fontSubLabel, Gdiplus::PointF(16.0f, curY + 2), &textMuted);

            auto drawStepBtn = [&](RECT& r, int x, const wchar_t* txt) {
                r = { x, (int)curY, x + 24, (int)curY + 18 };
                Gdiplus::SolidBrush b(Gdiplus::Color(50, 70, 80, 95));
                UICommon::FillRoundRectangle(g, &b, (float)r.left, (float)r.top, 24.0f, 18.0f, 3.0f);
                g.DrawString(txt, -1, &fontLabel, Gdiplus::PointF((float)r.left + 6, (float)r.top + 1), &textWhite);
            };

            g.DrawString(I18n::Width(), -1, &fontSubLabel, Gdiplus::PointF(85.0f, curY + 2), &textWhite);
            drawStepBtn(s_widthMinusRect, 135, L"-");
            drawStepBtn(s_widthPlusRect, 165, L"+");

            g.DrawString(I18n::Height(), -1, &fontSubLabel, Gdiplus::PointF(210.0f, curY + 2), &textWhite);
            drawStepBtn(s_heightMinusRect, 250, L"-");
            drawStepBtn(s_heightPlusRect, 280, L"+");
            curY += 28.0f;

            // 2. Opacity Slider
            int opPct = static_cast<int>((g_drawerOpacity.load() / 255.0f) * 100.0f);
            wchar_t opBuf[64];
            swprintf_s(opBuf, I18n::PanelOpacity(), opPct);
            g.DrawString(opBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

            s_opacitySliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
            g.FillRectangle(&trackBrush, (float)s_opacitySliderRect.left, (float)s_opacitySliderRect.top,
                            (float)(s_opacitySliderRect.right - s_opacitySliderRect.left), 8.0f);

            float opNorm = (g_drawerOpacity.load() - 120.0f) / (255.0f - 120.0f);
            opNorm = std::clamp(opNorm, 0.0f, 1.0f);
            float thumbOpX = s_opacitySliderRect.left + opNorm * (s_opacitySliderRect.right - s_opacitySliderRect.left - 12);
            g.FillEllipse(&thumbBrush, thumbOpX, (float)s_opacitySliderRect.top - 2.0f, 12.0f, 12.0f);
            curY += 28.0f;

            // 3. View mode toggles
            g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
            curY += 12.0f;
            g.DrawString(I18n::DisplayModes(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
            curY += 22.0f;

            // Compact mode toggle
            s_compactToggleRect = { 16, (int)curY, 200, (int)curY + 22 };
            bool comp = g_compactView.load();
            Gdiplus::SolidBrush compBrush(comp ? Gdiplus::Color(80, 45, 210, 45) : Gdiplus::Color(35, 75, 85, 95));
            UICommon::FillRoundRectangle(g, &compBrush, (float)s_compactToggleRect.left, (float)s_compactToggleRect.top, 184.0f, 22.0f, 4.0f);
            g.DrawString(comp ? I18n::CompactModeActive() : I18n::CompactModeInactive(), -1, &fontSubLabel,
                         Gdiplus::PointF((float)s_compactToggleRect.left + 8, (float)s_compactToggleRect.top + 4), &textWhite);

            g.DrawString(I18n::CompactModeDesc(), -1, &fontSubLabel, Gdiplus::PointF(212.0f, curY + 4), &textMuted);
            curY += 28.0f;

            // Hide console toggle
            s_hideConsoleToggleRect = { 16, (int)curY, 200, (int)curY + 22 };
            bool hideCon = g_hideConsoleSection.load();
            Gdiplus::SolidBrush hideBrush(hideCon ? Gdiplus::Color(80, 45, 210, 45) : Gdiplus::Color(35, 75, 85, 95));
            UICommon::FillRoundRectangle(g, &hideBrush, (float)s_hideConsoleToggleRect.left, (float)s_hideConsoleToggleRect.top, 184.0f, 22.0f, 4.0f);
            g.DrawString(hideCon ? I18n::HideConsoleActive() : I18n::HideConsoleInactive(), -1, &fontSubLabel,
                         Gdiplus::PointF((float)s_hideConsoleToggleRect.left + 8, (float)s_hideConsoleToggleRect.top + 4), &textWhite);

            g.DrawString(I18n::HideConsoleDesc(), -1, &fontSubLabel, Gdiplus::PointF(212.0f, curY + 4), &textMuted);
            curY += 28.0f;

            // 4. Combo UI Settings
            g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
            curY += 12.0f;
            g.DrawString(I18n::ComboUiSection(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
            curY += 22.0f;

            // Toggle Show/Hide
            s_comboToggleRect = { 16, (int)curY, 200, (int)curY + 22 };
            bool comboVis = g_comboVisible.load();
            Gdiplus::SolidBrush comboVisBrush(comboVis ? Gdiplus::Color(80, 45, 210, 45) : Gdiplus::Color(35, 75, 85, 95));
            UICommon::FillRoundRectangle(g, &comboVisBrush, (float)s_comboToggleRect.left, (float)s_comboToggleRect.top, 184.0f, 22.0f, 4.0f);
            g.DrawString(comboVis ? I18n::ComboUiToggleActive() : I18n::ComboUiToggleInactive(), -1, &fontSubLabel,
                         Gdiplus::PointF((float)s_comboToggleRect.left + 8, (float)s_comboToggleRect.top + 4), &textWhite);

            g.DrawString(I18n::ComboUiToggleDesc(), -1, &fontSubLabel, Gdiplus::PointF(212.0f, curY + 4), &textMuted);
            curY += 28.0f;

            // Opacity Slider
            float curComboOp = GetComboOverlayOpacity();
            int comboOpPct = static_cast<int>(curComboOp * 100.0f + 0.5f);
            wchar_t comboOpBuf[64];
            swprintf_s(comboOpBuf, I18n::ComboUiOpacity(), comboOpPct);
            g.DrawString(comboOpBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

            s_comboOpacitySliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
            g.FillRectangle(&trackBrush, (float)s_comboOpacitySliderRect.left, (float)s_comboOpacitySliderRect.top,
                            (float)(s_comboOpacitySliderRect.right - s_comboOpacitySliderRect.left), 8.0f);

            float comboOpNorm = (curComboOp - 0.10f) / (1.0f - 0.10f);
            comboOpNorm = std::clamp(comboOpNorm, 0.0f, 1.0f);
            float thumbComboOpX = s_comboOpacitySliderRect.left + comboOpNorm * (s_comboOpacitySliderRect.right - s_comboOpacitySliderRect.left - 12);
            g.FillEllipse(&thumbBrush, thumbComboOpX, (float)s_comboOpacitySliderRect.top - 2.0f, 12.0f, 12.0f);
            curY += 28.0f;

            // Scale Presets & Step Buttons
            float normX = 0.8f, normY = 0.5f, curScale = 1.0f;
            GetComboOverlayLayout(&normX, &normY, &curScale);
            int scalePct = static_cast<int>(curScale * 100.0f + 0.5f);
            wchar_t scaleBuf[64];
            swprintf_s(scaleBuf, I18n::ComboUiScale(), scalePct);
            g.DrawString(scaleBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);
            curY += 20.0f;

            drawPresetBtn(s_comboScale70Rect, 16, 70, L"70%", (scalePct >= 68 && scalePct <= 72));
            drawPresetBtn(s_comboScale100Rect, 94, 70, L"100%", (scalePct >= 98 && scalePct <= 102));
            drawPresetBtn(s_comboScale130Rect, 172, 70, L"130%", (scalePct >= 128 && scalePct <= 132));

            g.DrawString(I18n::FineTune(), -1, &fontSubLabel, Gdiplus::PointF(255.0f, curY + 2), &textMuted);
            drawStepBtn(s_comboScaleMinusRect, 320, L"-");
            drawStepBtn(s_comboScalePlusRect, 350, L"+");
            curY += 32.0f;

            // 5. Save & Close Button
            s_saveSettingsBtnRect = { 16, (int)H - 46, (int)W - 16, (int)H - 14 };
            Gdiplus::LinearGradientBrush saveBtnBrush(
                Gdiplus::PointF(16.0f, (float)s_saveSettingsBtnRect.top),
                Gdiplus::PointF(W - 16.0f, (float)s_saveSettingsBtnRect.top),
                Gdiplus::Color(220, 215, 170, 50),
                Gdiplus::Color(220, 175, 130, 30)
            );
            UICommon::FillRoundRectangle(g, &saveBtnBrush, (float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top,
                                         (float)(s_saveSettingsBtnRect.right - s_saveSettingsBtnRect.left), 32.0f, 6.0f);

            Gdiplus::Font btnFont(L"Segoe UI", 9.0f, Gdiplus::FontStyleBold);
            Gdiplus::SolidBrush btnText(Gdiplus::Color(255, 18, 14, 6));
            Gdiplus::StringFormat centerFmt;
            centerFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
            centerFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
            Gdiplus::RectF btnRectF((float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top,
                                   (float)(s_saveSettingsBtnRect.right - s_saveSettingsBtnRect.left), 32.0f);
            g.DrawString(I18n::SaveAndClose(), -1, &btnFont, btnRectF, &centerFmt, &btnText);

        } else {
            // Zero out settings rects
            s_presetNormalRect = s_presetWideRect = s_presetCompactRect = s_widthMinusRect = s_widthPlusRect =
                s_heightMinusRect = s_heightPlusRect = s_opacitySliderRect = s_compactToggleRect =
                s_hideConsoleToggleRect = s_comboToggleRect = s_comboOpacitySliderRect = s_comboScale70Rect =
                s_comboScale100Rect = s_comboScale130Rect = s_comboScaleMinusRect = s_comboScalePlusRect =
                s_saveSettingsBtnRect = { 0, 0, 0, 0 };

            // =========================================================================
            // VIEW B: MAIN DASHBOARD
            // =========================================================================

            // Section 1: Shugo Console (Motor Gráfico) - if not hidden
            if (!g_hideConsoleSection.load() && g_featConsole.load()) {
                g.DrawString(I18n::ShugoEngineTitle(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
                curY += 20.0f;

                // FOV Slider
                if (g_featFov.load()) {
                    wchar_t fovBuf[64];
                    swprintf_s(fovBuf, L"%ls%.0f°", I18n::FovLabel(), g_cvarFov.load());
                    g.DrawString(fovBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

                    s_fovSliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
                    g.FillRectangle(&trackBrush, (float)s_fovSliderRect.left, (float)s_fovSliderRect.top,
                                    (float)(s_fovSliderRect.right - s_fovSliderRect.left), 8.0f);

                    float fovPct = (g_cvarFov.load() - 60.0f) / (120.0f - 60.0f);
                    fovPct = std::clamp(fovPct, 0.0f, 1.0f);
                    float thumbX = s_fovSliderRect.left + fovPct * (s_fovSliderRect.right - s_fovSliderRect.left - 12);
                    g.FillEllipse(&thumbBrush, thumbX, (float)s_fovSliderRect.top - 2.0f, 12.0f, 12.0f);
                    curY += 20.0f;
                } else {
                    s_fovSliderRect = { 0, 0, 0, 0 };
                }

                // CamMax Slider
                if (g_featCamMax.load()) {
                    wchar_t camBuf[64];
                    swprintf_s(camBuf, L"%ls%.0fm", I18n::CamMaxLabel(), g_cvarCamMax.load());
                    g.DrawString(camBuf, -1, &fontLabel, Gdiplus::PointF(16.0f, curY), &textWhite);

                    s_camSliderRect = { 180, (int)curY + 2, s_modalW - 24, (int)curY + 12 };
                    g.FillRectangle(&trackBrush, (float)s_camSliderRect.left, (float)s_camSliderRect.top,
                                    (float)(s_camSliderRect.right - s_camSliderRect.left), 8.0f);

                    float camPct = (g_cvarCamMax.load() - 5.0f) / (45.0f - 5.0f);
                    camPct = std::clamp(camPct, 0.0f, 1.0f);
                    float thumbCamX = s_camSliderRect.left + camPct * (s_camSliderRect.right - s_camSliderRect.left - 12);
                    g.FillEllipse(&thumbBrush, thumbCamX, (float)s_camSliderRect.top - 2.0f, 12.0f, 12.0f);
                    curY += 22.0f;
                } else {
                    s_camSliderRect = { 0, 0, 0, 0 };
                }

                // FPS limiters & toggles
                if (g_featFpsUnlock.load()) {
                    g.DrawString(I18n::FpsCapLabel(), -1, &fontLabel, Gdiplus::PointF(16.0f, curY + 2), &textWhite);

                    auto drawFpsBtn = [&](RECT& r, int x, int val, const wchar_t* txt) {
                        r = { x, (int)curY, x + 38, (int)curY + 18 };
                        bool active = (g_cvarMaxFps.load() == val);
                        Gdiplus::SolidBrush b(active ? Gdiplus::Color(100, 215, 170, 50) : Gdiplus::Color(40, 60, 70, 85));
                        UICommon::FillRoundRectangle(g, &b, (float)r.left, (float)r.top, (float)(r.right - r.left), 18.0f, 3.0f);
                        Gdiplus::SolidBrush t(active ? UICommon::ColTextWhite : UICommon::ColTextMuted);
                        g.DrawString(txt, -1, &fontLabel, Gdiplus::PointF((float)r.left + 5, (float)r.top + 2), &t);
                    };

                    drawFpsBtn(s_fps60Rect, 52, 60, L"60");
                    drawFpsBtn(s_fps144Rect, 94, 144, L"144");
                    drawFpsBtn(s_fpsMaxRect, 136, 0, L"MAX");

                    // Triple Buffering & Anisotropic
                    s_tbToggleRect = { 186, (int)curY, 276, (int)curY + 18 };
                    bool tb = g_cvarTripleBuffering.load();
                    Gdiplus::SolidBrush tbBrush(tb ? Gdiplus::Color(60, 45, 230, 45) : Gdiplus::Color(30, 80, 80, 80));
                    UICommon::FillRoundRectangle(g, &tbBrush, (float)s_tbToggleRect.left, (float)s_tbToggleRect.top, (float)(s_tbToggleRect.right - s_tbToggleRect.left), 18.0f, 3.0f);
                    g.DrawString(tb ? L"✔ TriBuffer" : L"✖ TriBuffer", -1, &fontSubLabel, Gdiplus::PointF((float)s_tbToggleRect.left + 6, (float)s_tbToggleRect.top + 2), &textWhite);

                    s_anisoToggleRect = { 284, (int)curY, 376, (int)curY + 18 };
                    bool aniso = g_cvarAnisotropic.load();
                    Gdiplus::SolidBrush anisoBrush(aniso ? Gdiplus::Color(60, 45, 230, 45) : Gdiplus::Color(30, 80, 80, 80));
                    UICommon::FillRoundRectangle(g, &anisoBrush, (float)s_anisoToggleRect.left, (float)s_anisoToggleRect.top, (float)(s_anisoToggleRect.right - s_anisoToggleRect.left), 18.0f, 3.0f);
                    g.DrawString(aniso ? (IsEnglish() ? L"✔ 16x Aniso" : L"✔ 16x Aniso") : (IsEnglish() ? L"✖ 16x Aniso" : L"✖ 16x Aniso"), -1, &fontSubLabel, Gdiplus::PointF((float)s_anisoToggleRect.left + 6, (float)s_anisoToggleRect.top + 2), &textWhite);

                    curY += 26.0f;
                } else {
                    s_fps60Rect = s_fps144Rect = s_fpsMaxRect = s_tbToggleRect = s_anisoToggleRect = { 0, 0, 0, 0 };
                }

                g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
                curY += 10.0f;
            } else {
                s_fovSliderRect = s_camSliderRect = s_fps60Rect = s_fps144Rect = s_fpsMaxRect = s_tbToggleRect = s_anisoToggleRect = { 0, 0, 0, 0 };
            }

            // Section 2: Combat Analysis & Target Data
            if (g_featDpsMeterUI.load()) {
                std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

                // Target Banner & Dynamic Stats
                Gdiplus::Font fontTarget(L"Segoe UI", 9.5f, Gdiplus::FontStyleBold);
                Gdiplus::Font fontTargetStats(L"Segoe UI", 7.5f, Gdiplus::FontStyleRegular);

                if (g_currentTarget.hasTarget) {
                    float targetX = 16.0f;
                    UICommon::DrawTargetEmblemDisk(g, targetX, curY + 1.0f, 16.0f, g_currentTarget.rating, g_currentTarget.race, g_currentTarget.isNpc);
                    targetX += 22.0f;

                    std::wstring targetTitle = I18n::TargetLabel() + std::wstring(g_currentTarget.name.begin(), g_currentTarget.name.end());
                    if (g_currentTarget.level > 0) {
                        targetTitle += L" [Lv. " + std::to_wstring(g_currentTarget.level) + L"]";
                    }
                    g.DrawString(targetTitle.c_str(), -1, &fontTarget, Gdiplus::PointF(targetX, curY), &textWhite);

                    // Extra target stats chips
                    wchar_t statsBuf[128];
                    std::wstring wAi(g_currentTarget.aiName.begin(), g_currentTarget.aiName.end());
                    swprintf_s(statsBuf, L"AI: %ls | ATK: %u  DEF: %u  M.RES: %u",
                               wAi.c_str(), g_currentTarget.attack, g_currentTarget.pdef, g_currentTarget.mres);
                    g.DrawString(statsBuf, -1, &fontTargetStats, Gdiplus::PointF(W - 250.0f, curY + 2.0f), &textGold);

                    curY += 18.0f;

                    // Health bar with exact HP numbers and percentage
                    float hpW = W - 32.0f;
                    Gdiplus::SolidBrush hpBg(Gdiplus::Color(60, 30, 35, 45));
                    UICommon::FillRoundRectangle(g, &hpBg, 16.0f, curY, hpW, 12.0f, 2.0f);

                    float hpPct = (g_currentTarget.maxHp > 0) ? (float)g_currentTarget.currentHp / (float)g_currentTarget.maxHp : 0.0f;
                    hpPct = std::clamp(hpPct, 0.0f, 1.0f);

                    if (hpPct > 0.0f && g_currentTarget.currentHp > 0) {
                        Gdiplus::SolidBrush hpFill(Gdiplus::Color(255, 220, 50, 60)); // Crimson HP
                        UICommon::FillRoundRectangle(g, &hpFill, 16.0f, curY, hpW * hpPct, 12.0f, 2.0f);

                        wchar_t hpText[64];
                        swprintf_s(hpText, L"%ls / %ls (%.1f%%)",
                                   UICommon::FormatNumber(g_currentTarget.currentHp).c_str(),
                                   UICommon::FormatNumber(g_currentTarget.maxHp).c_str(),
                                   hpPct * 100.0f);
                        Gdiplus::StringFormat cFmt;
                        cFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
                        cFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
                        Gdiplus::RectF hpRect(16.0f, curY, hpW, 12.0f);
                        g.DrawString(hpText, -1, &fontSubLabel, hpRect, &cFmt, &textWhite);
                    } else {
                        // Dead target
                        Gdiplus::StringFormat cFmt;
                        cFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
                        cFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
                        Gdiplus::RectF hpRect(16.0f, curY, hpW, 12.0f);
                        g.DrawString(I18n::TargetDefeated(), -1, &fontSubLabel, hpRect, &cFmt, &textMuted);
                    }
                } else {
                    g.DrawString(I18n::TargetNone(), -1, &fontTarget, Gdiplus::PointF(16.0f, curY), &textMuted);
                    curY += 18.0f;

                    float hpW = W - 32.0f;
                    Gdiplus::SolidBrush hpBg(Gdiplus::Color(40, 30, 35, 45));
                    UICommon::FillRoundRectangle(g, &hpBg, 16.0f, curY, hpW, 12.0f, 2.0f);

                    Gdiplus::StringFormat cFmt;
                    cFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
                    cFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
                    Gdiplus::RectF hpRect(16.0f, curY, hpW, 12.0f);
                    g.DrawString(IsEnglish() ? L"Awaiting target selection in-game..." : L"Aguardando seleção de alvo no jogo...", -1, &fontSubLabel, hpRect, &cFmt, &textMuted);
                }
                curY += 18.0f;

                // Combat Highlight Cards
                float cardW = (W - 32.0f - 16.0f) / 3.0f;
                auto drawMetricCard = [&](float cx, const wchar_t* title, const std::wstring& val, Gdiplus::Color valCol) {
                    Gdiplus::SolidBrush cardBg(Gdiplus::Color(40, 20, 26, 36));
                    UICommon::FillRoundRectangle(g, &cardBg, cx, curY, cardW, 40.0f, 5.0f);
                    Gdiplus::Pen cardBorder(Gdiplus::Color(40, 180, 190, 210), 1.0f);
                    UICommon::DrawRoundRectangle(g, &cardBorder, cx, curY, cardW, 40.0f, 5.0f);

                    Gdiplus::Font fT(L"Segoe UI", 7.0f, Gdiplus::FontStyleRegular);
                    g.DrawString(title, -1, &fT, Gdiplus::PointF(cx + 6, curY + 4), &textMuted);

                    Gdiplus::Font fV(L"Segoe UI", 10.5f, Gdiplus::FontStyleBold);
                    Gdiplus::SolidBrush bV(valCol);
                    g.DrawString(val.c_str(), -1, &fV, Gdiplus::PointF(cx + 6, curY + 16), &bV);
                };

                drawMetricCard(16.0f, I18n::BattleDuration(), UICommon::FormatTime(g_battleDurationSeconds.load()), UICommon::ColTextWhite);
                drawMetricCard(16.0f + cardW + 8.0f, I18n::GroupDps(), UICommon::FormatNumber(g_totalBattleDps.load()), UICommon::ColGoldAccent);
                drawMetricCard(16.0f + (cardW + 8.0f) * 2.0f, I18n::TotalDamage(), UICommon::FormatNumber(g_totalBattleDamage.load()), UICommon::ColNeonGreen);
                curY += 46.0f;

                // Reset Action Button
                s_resetBtnRect = { 16, (int)curY, (int)W - 16, (int)curY + 24 };
                Gdiplus::LinearGradientBrush btnBrush(
                    Gdiplus::PointF(16.0f, curY), Gdiplus::PointF(W - 16.0f, curY),
                    Gdiplus::Color(210, 215, 170, 50),
                    Gdiplus::Color(210, 175, 130, 30)
                );
                UICommon::FillRoundRectangle(g, &btnBrush, (float)s_resetBtnRect.left, (float)s_resetBtnRect.top,
                                             (float)(s_resetBtnRect.right - s_resetBtnRect.left), 24.0f, 4.0f);

                Gdiplus::Font resetBtnFont(L"Segoe UI", 8.5f, Gdiplus::FontStyleBold);
                Gdiplus::SolidBrush resetBtnText(Gdiplus::Color(255, 18, 14, 6));
                Gdiplus::StringFormat centerFmt;
                centerFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
                centerFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
                Gdiplus::RectF resetRectF((float)s_resetBtnRect.left, (float)s_resetBtnRect.top,
                                         (float)(s_resetBtnRect.right - s_resetBtnRect.left), 24.0f);
                g.DrawString(IsEnglish() ? L"⚡ [Ctrl + X] Start / Reset DPS Analysis" : L"⚡ [Ctrl + X] Iniciar / Resetar Análise", -1, &resetBtnFont, resetRectF, &centerFmt, &resetBtnText);
                curY += 30.0f;

                // Visual Charts: Fibonacci Curve & 4-Axis Radar (if NOT in compact mode)
                if (!g_compactView.load()) {
                    float chartH = 80.0f;
                    float fiboW = W * 0.55f;
                    g.DrawString(IsEnglish() ? L"BURST PROGRESSION (FIBONACCI)" : L"PROGRESSÃO BURST (FIBONACCI)", -1, &fontSubLabel, Gdiplus::PointF(16.0f, curY), &textMuted);
                    UICommon::DrawFibonacciCurve(g, 16.0f, curY + 12.0f, fiboW, chartH - 14.0f, g_fibonacciCurve);

                    float radarCx = W - 70.0f;
                    float radarCy = curY + chartH * 0.48f;
                    UICommon::DrawRadarChart4Axis(g, radarCx, radarCy, 30.0f,
                                                  g_currentRadar.crit, g_currentRadar.block,
                                                  g_currentRadar.dodge, g_currentRadar.resist);

                    curY += chartH + 6.0f;
                    g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
                    curY += 6.0f;
                }

                // Combat Timeline (Real-time Log)
                g.DrawString(I18n::TitleTimeline(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
                curY += 16.0f;

                size_t tSize = g_combatTimeline.size();
                int maxEntries = g_compactView.load() ? 5 : 3;
                int startIdx = (tSize > (size_t)maxEntries) ? static_cast<int>(tSize - maxEntries) : 0;

                if (tSize == 0) {
                    g.DrawString(I18n::NoCombatEvents(), -1, &fontSubLabel, Gdiplus::PointF(20.0f, curY + 2), &textMuted);
                    curY += 18.0f;
                } else {
                    for (int i = startIdx; i < static_cast<int>(tSize); ++i) {
                        const auto& evt = g_combatTimeline[i];
                        std::wstring wTime(evt.timeStr.begin(), evt.timeStr.end());
                        std::wstring wAtt(evt.attacker.begin(), evt.attacker.end());
                        std::wstring wSkill(evt.skillName.begin(), evt.skillName.end());

                        UICommon::DrawSkillIconBadge(g, 18.0f, curY + 1.0f, 13.0f, evt.skillId, evt.skillName);
                        float lineX = 36.0f;

                        wchar_t logLine[128];
                        if (evt.isCrit) {
                            swprintf_s(logLine, L"[%ls] %ls -> %ls: %ls (CRIT!)",
                                       wTime.c_str(), wAtt.c_str(), wSkill.c_str(), UICommon::FormatNumber(evt.damage).c_str());
                            Gdiplus::SolidBrush critBrush(UICommon::ColGoldAccent);
                            g.DrawString(logLine, -1, &fontSubLabel, Gdiplus::PointF(lineX, curY), &critBrush);
                        } else if (evt.isHeal) {
                            swprintf_s(logLine, L"[%ls] %ls -> %ls: +%ls (%ls)",
                                       wTime.c_str(), wAtt.c_str(), wSkill.c_str(), UICommon::FormatNumber(evt.damage).c_str(),
                                       IsEnglish() ? L"HEAL" : L"CURA");
                            Gdiplus::SolidBrush healBrush(UICommon::ColNeonGreen);
                            g.DrawString(logLine, -1, &fontSubLabel, Gdiplus::PointF(lineX, curY), &healBrush);
                        } else {
                            swprintf_s(logLine, L"[%ls] %ls -> %ls: %ls",
                                       wTime.c_str(), wAtt.c_str(), wSkill.c_str(), UICommon::FormatNumber(evt.damage).c_str());
                            g.DrawString(logLine, -1, &fontSubLabel, Gdiplus::PointF(lineX, curY), &textWhite);
                        }
                        curY += 15.0f;
                    }
                }

                curY += 4.0f;
                g.DrawLine(&sepPen, 16.0f, curY, W - 16.0f, curY);
                curY += 8.0f;

                // Player & Skill Rankings Table
                g.DrawString(I18n::TitleDpsMeter(), -1, &fontSection, Gdiplus::PointF(16.0f, curY), &textGold);
                curY += 16.0f;

                // Table Header
                Gdiplus::Font fTh(L"Segoe UI", 7.5f, Gdiplus::FontStyleBold);
                g.DrawString(I18n::ColPlayer(), -1, &fTh, Gdiplus::PointF(18.0f, curY), &textMuted);
                g.DrawString(I18n::ColDamage(), -1, &fTh, Gdiplus::PointF(160.0f, curY), &textMuted);
                g.DrawString(I18n::ColDps(), -1, &fTh, Gdiplus::PointF(245.0f, curY), &textMuted);
                g.DrawString(L"%", -1, &fTh, Gdiplus::PointF(300.0f, curY), &textMuted);
                curY += 14.0f;

                // Table Rows
                Gdiplus::Font fRow(L"Segoe UI", 8.0f, Gdiplus::FontStyleRegular);
                int rowsDrawn = 0;
                float rowHeight = 20.0f;

                for (const auto& player : g_playerRankings) {
                    if (rowsDrawn >= 4 || curY + rowHeight > H - 80.0f) break;

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
                    g.DrawString(pctBuf, -1, &fRow, Gdiplus::PointF(300.0f, curY + 2), &textMuted);

                    curY += rowHeight;
                    rowsDrawn++;
                }

                if (rowsDrawn == 0) {
                    g.DrawString(I18n::NoDamageRecorded(), -1, &fRow, Gdiplus::PointF(20.0f, curY + 2), &textMuted);
                    curY += 20.0f;
                }
            } else {
                s_resetBtnRect = { 0, 0, 0, 0 };
            }

            // 3D Model Miniature Preview in Lower-Right Corner (Only if NOT compact)
            if (g_featModel3D.load() && !g_compactView.load()) {
                float previewW = 96.0f;
                float previewH = 96.0f;
                float previewX = W - previewW - 14.0f;
                float previewY = H - previewH - 12.0f;

                CryModelBridge::RenderThumbnail(g, previewX, previewY, previewW, previewH);
            }
        }
    }

    // Blend to layered window with user configurable opacity
    POINT ptSrc = { 0, 0 };
    SIZE szWindow = { s_modalW, s_modalH };
    BLENDFUNCTION blend = {};
    blend.BlendOp = AC_SRC_OVER;
    blend.BlendFlags = 0;
    blend.SourceConstantAlpha = static_cast<BYTE>(std::clamp(g_drawerOpacity.load(), 120, 255));
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

        // Settings Button Toggle
        if (mx >= s_settingsBtnRect.left && mx <= s_settingsBtnRect.right &&
            my >= s_settingsBtnRect.top && my <= s_settingsBtnRect.bottom) {
            s_isSettingsOpen = !s_isSettingsOpen;
            Repaint();
            return 0;
        }

        // --- SETTINGS VIEW ACTIONS ---
        if (s_isSettingsOpen) {
            if (mx >= s_presetNormalRect.left && mx <= s_presetNormalRect.right &&
                my >= s_presetNormalRect.top && my <= s_presetNormalRect.bottom) {
                ResizeDrawer(460, 580);
                return 0;
            }
            if (mx >= s_presetWideRect.left && mx <= s_presetWideRect.right &&
                my >= s_presetWideRect.top && my <= s_presetWideRect.bottom) {
                ResizeDrawer(560, 680);
                return 0;
            }
            if (mx >= s_presetCompactRect.left && mx <= s_presetCompactRect.right &&
                my >= s_presetCompactRect.top && my <= s_presetCompactRect.bottom) {
                ResizeDrawer(420, 500);
                return 0;
            }

            // Width step
            if (mx >= s_widthMinusRect.left && mx <= s_widthMinusRect.right &&
                my >= s_widthMinusRect.top && my <= s_widthMinusRect.bottom) {
                ResizeDrawer(s_modalW - 20, s_modalH);
                return 0;
            }
            if (mx >= s_widthPlusRect.left && mx <= s_widthPlusRect.right &&
                my >= s_widthPlusRect.top && my <= s_widthPlusRect.bottom) {
                ResizeDrawer(s_modalW + 20, s_modalH);
                return 0;
            }

            // Height step
            if (mx >= s_heightMinusRect.left && mx <= s_heightMinusRect.right &&
                my >= s_heightMinusRect.top && my <= s_heightMinusRect.bottom) {
                ResizeDrawer(s_modalW, s_modalH - 20);
                return 0;
            }
            if (mx >= s_heightPlusRect.left && mx <= s_heightPlusRect.right &&
                my >= s_heightPlusRect.top && my <= s_heightPlusRect.bottom) {
                ResizeDrawer(s_modalW, s_modalH + 20);
                return 0;
            }

            // Opacity slider start
            if (mx >= s_opacitySliderRect.left && mx <= s_opacitySliderRect.right &&
                my >= s_opacitySliderRect.top - 6 && my <= s_opacitySliderRect.bottom + 6) {
                s_draggingOpacity = true;
                SetCapture(hwnd);
                return 0;
            }

            // Compact mode toggle
            if (mx >= s_compactToggleRect.left && mx <= s_compactToggleRect.right &&
                my >= s_compactToggleRect.top && my <= s_compactToggleRect.bottom) {
                g_compactView = !g_compactView.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }

            // Hide console toggle
            if (mx >= s_hideConsoleToggleRect.left && mx <= s_hideConsoleToggleRect.right &&
                my >= s_hideConsoleToggleRect.top && my <= s_hideConsoleToggleRect.bottom) {
                g_hideConsoleSection = !g_hideConsoleSection.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }

            // Combo UI Show / Hide Toggle
            if (mx >= s_comboToggleRect.left && mx <= s_comboToggleRect.right &&
                my >= s_comboToggleRect.top && my <= s_comboToggleRect.bottom) {
                bool newVis = !g_comboVisible.load();
                g_comboVisible = newVis;
                g_ComboUI.RequestLayoutRefresh();
                WebSocketClient::SendTextMessage(std::string("SET_COMBO_VISIBILITY:") + (newVis ? "1" : "0"));
                BrConfig::Save();
                Repaint();
                return 0;
            }

            // Combo UI Opacity Slider Start
            if (mx >= s_comboOpacitySliderRect.left && mx <= s_comboOpacitySliderRect.right &&
                my >= s_comboOpacitySliderRect.top - 6 && my <= s_comboOpacitySliderRect.bottom + 6) {
                s_draggingComboOpacity = true;
                SetCapture(hwnd);
                return 0;
            }

            // Combo UI Scale Presets & Step Buttons
            float normX = 0.8f, normY = 0.5f, curScale = 1.0f;
            GetComboOverlayLayout(&normX, &normY, &curScale);

            auto applyScale = [&](float targetScale) {
                targetScale = std::clamp(targetScale, 0.55f, 1.60f);
                SetComboOverlayLayout(normX, normY, targetScale);
                g_comboScale = targetScale;
                g_ComboUI.RequestLayoutRefresh();
                BrConfig::Save();
                Repaint();
            };

            if (mx >= s_comboScale70Rect.left && mx <= s_comboScale70Rect.right &&
                my >= s_comboScale70Rect.top && my <= s_comboScale70Rect.bottom) {
                applyScale(0.70f);
                return 0;
            }
            if (mx >= s_comboScale100Rect.left && mx <= s_comboScale100Rect.right &&
                my >= s_comboScale100Rect.top && my <= s_comboScale100Rect.bottom) {
                applyScale(1.00f);
                return 0;
            }
            if (mx >= s_comboScale130Rect.left && mx <= s_comboScale130Rect.right &&
                my >= s_comboScale130Rect.top && my <= s_comboScale130Rect.bottom) {
                applyScale(1.30f);
                return 0;
            }
            if (mx >= s_comboScaleMinusRect.left && mx <= s_comboScaleMinusRect.right &&
                my >= s_comboScaleMinusRect.top && my <= s_comboScaleMinusRect.bottom) {
                applyScale(curScale - 0.05f);
                return 0;
            }
            if (mx >= s_comboScalePlusRect.left && mx <= s_comboScalePlusRect.right &&
                my >= s_comboScalePlusRect.top && my <= s_comboScalePlusRect.bottom) {
                applyScale(curScale + 0.05f);
                return 0;
            }

            // Save & Close Settings button
            if (mx >= s_saveSettingsBtnRect.left && mx <= s_saveSettingsBtnRect.right &&
                my >= s_saveSettingsBtnRect.top && my <= s_saveSettingsBtnRect.bottom) {
                s_isSettingsOpen = false;
                BrConfig::Save();
                Repaint();
                return 0;
            }

            return 0;
        }

        // --- MAIN VIEW ACTIONS ---
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
        if (s_draggingOpacity) {
            float pct = (float)(mx - s_opacitySliderRect.left) / (float)(s_opacitySliderRect.right - s_opacitySliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            int op = static_cast<int>(120 + pct * (255 - 120));
            g_drawerOpacity = op;
            Repaint();
        } else if (s_draggingComboOpacity) {
            float pct = (float)(mx - s_comboOpacitySliderRect.left) / (float)(s_comboOpacitySliderRect.right - s_comboOpacitySliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float newOp = 0.10f + pct * (1.0f - 0.10f);
            SetComboOverlayOpacity(newOp);
            g_comboOpacity = newOp;
            g_ComboUI.RequestLayoutRefresh();
            Repaint();
        } else if (s_draggingFov) {
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
        if (s_draggingFov || s_draggingCam || s_draggingOpacity || s_draggingComboOpacity) {
            s_draggingFov = false;
            s_draggingCam = false;
            s_draggingOpacity = false;
            s_draggingComboOpacity = false;
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
