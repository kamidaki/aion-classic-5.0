#include "DrawerModalUI.h"
#include "UICommon.h"
#include "IconManager.h"
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
#include <vector>

namespace BrService {

static const wchar_t* kDrawerClassName = L"BrService_DrawerModal";
static int s_modalW = 760;
static int s_modalH = 560;

// Tab navigation state (Sidebar)
enum class DrawerTab {
    Display = 0,
    DpsMeter,
    ComboUi,
    Engine,
    Advanced
};
static DrawerTab s_activeTab = DrawerTab::Display;

// Dragging states
static bool s_isDraggingWindow = false;
static POINT s_dragStartCursor = { 0, 0 };
static POINT s_dragStartPos = { 0, 0 };

static bool s_draggingOpacity = false;
static bool s_draggingComboScale = false;
static bool s_draggingFov = false;
static bool s_draggingCam = false;

// Header & Window control rects
static RECT s_headerDragRect = { 0, 0, 0, 0 };
static RECT s_helpBtnRect = { 0, 0, 0, 0 };
static RECT s_minimizeBtnRect = { 0, 0, 0, 0 };
static RECT s_closeBtnRect = { 0, 0, 0, 0 };

// Sidebar Tab rects
static RECT s_tabDisplayRect = { 0, 0, 0, 0 };
static RECT s_tabDpsMeterRect = { 0, 0, 0, 0 };
static RECT s_tabComboRect = { 0, 0, 0, 0 };
static RECT s_tabEngineRect = { 0, 0, 0, 0 };
static RECT s_tabAdvancedRect = { 0, 0, 0, 0 };
static RECT s_resetDefaultsRect = { 0, 0, 0, 0 };

// Column 1: Display & Engine Preferences rects
static RECT s_presetDefaultRect = { 0, 0, 0, 0 };
static RECT s_presetWideRect = { 0, 0, 0, 0 };
static RECT s_presetCompactRect = { 0, 0, 0, 0 };
static RECT s_opacitySliderRect = { 0, 0, 0, 0 };
static RECT s_compactToggleRect = { 0, 0, 0, 0 };
static RECT s_consoleToggleRect = { 0, 0, 0, 0 };
static RECT s_comboToggleRect = { 0, 0, 0, 0 };
static RECT s_comboScaleSliderRect = { 0, 0, 0, 0 };
static RECT s_comboPosTopRect = { 0, 0, 0, 0 };
static RECT s_comboPosMidRightRect = { 0, 0, 0, 0 };
static RECT s_comboPosCenterRect = { 0, 0, 0, 0 };
static RECT s_comboPosLeftRect = { 0, 0, 0, 0 };
static RECT s_fovSliderRect = { 0, 0, 0, 0 };
static RECT s_camSliderRect = { 0, 0, 0, 0 };
static RECT s_fps60Rect = { 0, 0, 0, 0 };
static RECT s_fps144Rect = { 0, 0, 0, 0 };
static RECT s_fpsMaxRect = { 0, 0, 0, 0 };
static RECT s_tbToggleRect = { 0, 0, 0, 0 };
static RECT s_anisoToggleRect = { 0, 0, 0, 0 };
static RECT s_saveSettingsBtnRect = { 0, 0, 0, 0 };

// Column 2: DPS & Target rects
static RECT s_targetDropdownRect = { 0, 0, 0, 0 };
static RECT s_resetCombatBtnRect = { 0, 0, 0, 0 };
static RECT s_targetCardCloseRect = { 0, 0, 0, 0 };

struct MemoryTargetRaw {
    bool valid;
    uint32_t objId;
    uint32_t modelId;
    uint8_t type;
    uint8_t race;
    wchar_t name[128];
    int hp;
    int maxHp;
    float px, py, pz, yaw;
};

static bool ReadTargetMemoryRaw(MemoryTargetRaw* outRaw) {
    if (!outRaw) return false;
    outRaw->valid = false;

    uintptr_t hGame = (uintptr_t)GetModuleHandleA("Game.dll");
    if (!hGame) return false;

    __try {
        uintptr_t* pTarget = (uintptr_t*)(hGame + 0xECE610);
        if (!pTarget || !*pTarget) return false;

        uintptr_t targetPtr = *pTarget;
        uintptr_t* pEntityData = (uintptr_t*)(targetPtr + 0x378);
        if (!pEntityData || !*pEntityData) return false;
        uintptr_t entityData = *pEntityData;

        outRaw->hp = *(int*)(entityData + 0x147C);
        outRaw->maxHp = *(int*)(entityData + 0x1478);
        outRaw->type = *(uint8_t*)(entityData + 0x38);
        outRaw->race = *(uint8_t*)(entityData + 0x39);
        outRaw->modelId = *(uint32_t*)(entityData + 0x20);
        outRaw->objId = *(uint32_t*)(entityData + 0x24);

        wchar_t* pName = (wchar_t*)(entityData + 0x46);
        if (pName) {
            wcsncpy_s(outRaw->name, pName, _TRUNCATE);
        } else {
            outRaw->name[0] = L'\0';
        }

        outRaw->px = *(float*)(targetPtr + 0x3C);
        outRaw->py = *(float*)(targetPtr + 0x40);
        outRaw->pz = *(float*)(targetPtr + 0x44);
        outRaw->yaw = *(float*)(targetPtr + 0x48);
        outRaw->valid = true;
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// Requirement 13: Safely enrich target info without wiping authoritative target data
static bool UpdateTargetFromGameMemory() {
    MemoryTargetRaw raw = {};
    bool ok = ReadTargetMemoryRaw(&raw);
    if (ok && raw.valid && raw.objId != 0) {
        std::lock_guard<std::recursive_mutex> lock(g_combatMutex);
        g_currentTarget.hasTarget = true;
        g_currentTarget.targetId = raw.objId;
        g_currentTarget.modelId = raw.modelId;
        g_currentTarget.isNpc = (raw.type != 0);

        if (wcslen(raw.name) > 0) {
            char utf8Buf[256] = { 0 };
            WideCharToMultiByte(CP_UTF8, 0, raw.name, -1, utf8Buf, sizeof(utf8Buf), nullptr, nullptr);
            g_currentTarget.name = utf8Buf;
        }

        if (raw.maxHp > 0) {
            g_currentTarget.currentHp = (raw.hp >= 0) ? raw.hp : 0;
            g_currentTarget.maxHp = raw.maxHp;
        }

        if (raw.race == 0) g_currentTarget.race = "ELYOS";
        else if (raw.race == 1) g_currentTarget.race = "ASMODIANS";
        else if (raw.race == 2) g_currentTarget.race = "BALAUR";

        g_currentTarget.posX = raw.px;
        g_currentTarget.posY = raw.py;
        g_currentTarget.posZ = raw.pz;
        g_currentTarget.yaw = raw.yaw;
        return true;
    }
    // Never reset g_currentTarget when memory reading is inactive!
    return false;
}

bool DrawerModalUI::Initialize(HINSTANCE hInst) {
    IconManager::Initialize();

    if (g_drawerW.load() < 600) g_drawerW = 760;
    if (g_drawerH.load() < 500) g_drawerH = 560;

    s_modalW = std::clamp(g_drawerW.load(), 540, 960);
    s_modalH = std::clamp(g_drawerH.load(), 480, 800);

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
        L"Academy Show - DPS Meter",
        WS_POPUP,
        0, 0, s_modalW, s_modalH,
        nullptr, nullptr, hInst, nullptr
    );

    if (!g_hDrawerModalWnd) {
        LogError("Falha ao criar janela DrawerModal: %lu", GetLastError());
        return false;
    }

    LogInfo("DrawerModalUI (Modelo 3) inicializado com sucesso (%dx%d, Opacidade=%d).",
            s_modalW, s_modalH, g_drawerOpacity.load());
    return true;
}

void DrawerModalUI::Shutdown() {
    IconManager::Shutdown();
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
        SetTimer(g_hDrawerModalWnd, 1, 33, nullptr);
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

    s_modalW = std::clamp(g_drawerW.load(), 540, 960);
    s_modalH = std::clamp(g_drawerH.load(), 480, 800);
    if (s_modalH > gameH - 30) s_modalH = gameH - 30;

    int modalX = g_drawerPosX.load();
    int modalY = g_drawerPosY.load();

    // Default positioning if not saved: centered in game client
    if (modalX < 0 || modalY < 0) {
        modalX = gameX + (gameW - s_modalW) / 2;
        modalY = gameY + (gameH - s_modalH) / 2;
        if (modalX < gameX + 10) modalX = gameX + 10;
        if (modalY < gameY + 10) modalY = gameY + 10;
        g_drawerPosX = modalX;
        g_drawerPosY = modalY;
    }

    bool shouldBeVisible = g_featConsole.load() && g_isDrawerOpen.load() && g_isInWorld.load() && !g_isLoadingScreen.load() && g_isGameActive.load();
    SetWindowPos(g_hDrawerModalWnd, HWND_TOPMOST, modalX, modalY, s_modalW, s_modalH,
                 SWP_NOACTIVATE | (shouldBeVisible ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
    if (shouldBeVisible) {
        Repaint();
    }
}

void DrawerModalUI::ResizeDrawer(int newW, int newH) {
    g_drawerW = std::clamp(newW, 540, 960);
    g_drawerH = std::clamp(newH, 480, 800);
    s_modalW = g_drawerW.load();
    s_modalH = g_drawerH.load();

    HWND hGame = g_gameHwnd.load();
    if (hGame && IsWindow(hGame)) {
        RECT gr = {};
        GetWindowRect(hGame, &gr);
        UpdatePosition(gr.left, gr.top, gr.right - gr.left, gr.bottom - gr.top);
    } else {
        Repaint();
    }
    BrConfig::Save();
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

        // Clear transparent (Requirement 12: allows 3D model to float past borders)
        g.Clear(Gdiplus::Color(0, 0, 0, 0));

        // Dimensions of the main white card
        float cardX = 4.0f;
        float cardY = 4.0f;
        // Leave room on the right for the floating 3D model & target card
        float cardW = (float)s_modalW - 135.0f;
        float cardH = (float)s_modalH - 8.0f;

        // 1. Main Card Shadow & Background (Model 3 White/Off-White Card)
        Gdiplus::SolidBrush shadowBrush(Gdiplus::Color(25, 15, 23, 42));
        UICommon::FillRoundRectangle(g, &shadowBrush, cardX + 3.0f, cardY + 4.0f, cardW, cardH, 14.0f);

        Gdiplus::SolidBrush cardBg(UICommon::ColModel3Card);
        UICommon::FillRoundRectangle(g, &cardBg, cardX, cardY, cardW, cardH, 14.0f);

        Gdiplus::Pen cardBorder(UICommon::ColModel3Border, 1.2f);
        UICommon::DrawRoundRectangle(g, &cardBorder, cardX, cardY, cardW, cardH, 14.0f);

        // 2. HEADER
        s_headerDragRect = { (int)cardX, (int)cardY, (int)(cardX + cardW - 100.0f), (int)(cardY + 46.0f) };

        // Blue Icon Badge
        float iconBoxX = cardX + 14.0f;
        float iconBoxY = cardY + 11.0f;
        float iconBoxSize = 26.0f;
        Gdiplus::SolidBrush iconBg(UICommon::ColModel3Blue);
        UICommon::FillRoundRectangle(g, &iconBg, iconBoxX, iconBoxY, iconBoxSize, iconBoxSize, 6.0f);

        // Icon Graphic: stylized diamond with arrow / shield
        Gdiplus::Pen iconPen(UICommon::ColModel3Card, 2.0f);
        Gdiplus::PointF diamondPts[4] = {
            Gdiplus::PointF(iconBoxX + 13.0f, iconBoxY + 5.0f),
            Gdiplus::PointF(iconBoxX + 21.0f, iconBoxY + 13.0f),
            Gdiplus::PointF(iconBoxX + 13.0f, iconBoxY + 21.0f),
            Gdiplus::PointF(iconBoxX + 5.0f, iconBoxY + 13.0f)
        };
        g.DrawPolygon(&iconPen, diamondPts, 4);
        g.DrawLine(&iconPen, iconBoxX + 13.0f, iconBoxY + 8.0f, iconBoxX + 13.0f, iconBoxY + 18.0f);

        // Title & Subtitle
        Gdiplus::Font fontTitle(L"Segoe UI", 11.0f, Gdiplus::FontStyleBold);
        Gdiplus::Font fontSubTitle(L"Segoe UI", 7.8f, Gdiplus::FontStyleRegular);
        Gdiplus::SolidBrush textDark(UICommon::ColModel3TextDark);
        Gdiplus::SolidBrush textMuted(UICommon::ColModel3TextMuted);

        float titleX = iconBoxX + iconBoxSize + 10.0f;
        g.DrawString(L"ACADEMY SHOW", -1, &fontTitle, Gdiplus::PointF(titleX, cardY + 9.0f), &textDark);
        g.DrawString(L"DPS Meter & Combat Metrics", -1, &fontSubTitle, Gdiplus::PointF(titleX, cardY + 25.0f), &textMuted);

        // Header Right Buttons: [ ? ] [ - ] [ X ]
        auto drawHeaderBtn = [&](RECT& r, int bx, int by, const wchar_t* symbol) {
            r = { bx, by, bx + 24, by + 24 };
            Gdiplus::SolidBrush bBg(UICommon::ColModel3Card);
            UICommon::FillRoundRectangle(g, &bBg, (float)bx, (float)by, 24.0f, 24.0f, 5.0f);
            Gdiplus::Pen bPen(UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &bPen, (float)bx, (float)by, 24.0f, 24.0f, 5.0f);

            Gdiplus::Font fBtn(L"Segoe UI", 8.5f, Gdiplus::FontStyleBold);
            Gdiplus::StringFormat sFmt;
            sFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
            sFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
            Gdiplus::RectF rF((float)bx, (float)by, 24.0f, 24.0f);
            g.DrawString(symbol, -1, &fBtn, rF, &sFmt, &textMuted);
        };

        int btnBaseX = (int)(cardX + cardW - 88.0f);
        int btnBaseY = (int)(cardY + 12.0f);
        drawHeaderBtn(s_helpBtnRect, btnBaseX, btnBaseY, L"?");
        drawHeaderBtn(s_minimizeBtnRect, btnBaseX + 28, btnBaseY, L"−");
        drawHeaderBtn(s_closeBtnRect, btnBaseX + 56, btnBaseY, L"×");

        // Subtle header divider line
        Gdiplus::Pen sepPen(UICommon::ColModel3Border, 1.0f);
        g.DrawLine(&sepPen, cardX + 12.0f, cardY + 46.0f, cardX + cardW - 12.0f, cardY + 46.0f);

        // 3. SIDEBAR NAVIGATION (Left Column)
        float sideX = cardX + 8.0f;
        float sideY = cardY + 54.0f;
        float sideW = 108.0f;
        float sideH = cardH - 62.0f;

        // Subtle sidebar right divider line
        g.DrawLine(&sepPen, sideX + sideW + 4.0f, sideY, sideX + sideW + 4.0f, sideY + sideH);

        // Sidebar Navigation Tabs
        struct NavTabItem {
            DrawerTab tab;
            const wchar_t* label;
            const wchar_t* icon;
            RECT* pRect;
        };

        NavTabItem navTabs[] = {
            { DrawerTab::Display,  L"Display",    L"▣", &s_tabDisplayRect },
            { DrawerTab::DpsMeter, L"DPS Meter",   L"▥", &s_tabDpsMeterRect },
            { DrawerTab::ComboUi,  L"Combo UI",    L"⚔", &s_tabComboRect },
            { DrawerTab::Engine,   L"Engine",      L"⚙", &s_tabEngineRect },
            { DrawerTab::Advanced, L"Advanced",    L"⚡", &s_tabAdvancedRect }
        };

        float curTabY = sideY + 4.0f;
        Gdiplus::Font fontTab(L"Segoe UI", 8.2f, Gdiplus::FontStyleRegular);
        Gdiplus::Font fontTabBold(L"Segoe UI", 8.2f, Gdiplus::FontStyleBold);
        Gdiplus::SolidBrush textWhite(UICommon::ColModel3Card);

        for (const auto& item : navTabs) {
            bool isActive = (s_activeTab == item.tab);
            *(item.pRect) = { (int)sideX, (int)curTabY, (int)(sideX + sideW), (int)(curTabY + 30.0f) };

            if (isActive) {
                // Vibrant Blue pill with connecting indicator
                Gdiplus::SolidBrush activeBg(UICommon::ColModel3Blue);
                UICommon::FillRoundRectangle(g, &activeBg, sideX, curTabY, sideW, 30.0f, 6.0f);

                // Small right connector triangle
                Gdiplus::PointF arrowPts[3] = {
                    Gdiplus::PointF(sideX + sideW, curTabY + 10.0f),
                    Gdiplus::PointF(sideX + sideW + 4.0f, curTabY + 15.0f),
                    Gdiplus::PointF(sideX + sideW, curTabY + 20.0f)
                };
                g.FillPolygon(&activeBg, arrowPts, 3);

                g.DrawString(item.icon, -1, &fontTabBold, Gdiplus::PointF(sideX + 10.0f, curTabY + 6.0f), &textWhite);
                g.DrawString(item.label, -1, &fontTabBold, Gdiplus::PointF(sideX + 28.0f, curTabY + 6.0f), &textWhite);
            } else {
                g.DrawString(item.icon, -1, &fontTab, Gdiplus::PointF(sideX + 10.0f, curTabY + 6.0f), &textMuted);
                g.DrawString(item.label, -1, &fontTab, Gdiplus::PointF(sideX + 28.0f, curTabY + 6.0f), &textDark);
            }
            curTabY += 36.0f;
        }

        // Sidebar Bottom: [ Reset to Default ]
        s_resetDefaultsRect = { (int)sideX, (int)(cardY + cardH - 36.0f), (int)(sideX + sideW), (int)(cardY + cardH - 12.0f) };
        Gdiplus::SolidBrush rBg(UICommon::ColModel3Bg);
        UICommon::FillRoundRectangle(g, &rBg, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sideW, 24.0f, 4.0f);
        Gdiplus::Pen rPen(UICommon::ColModel3Border, 1.0f);
        UICommon::DrawRoundRectangle(g, &rPen, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sideW, 24.0f, 4.0f);

        Gdiplus::Font fReset(L"Segoe UI", 7.2f, Gdiplus::FontStyleRegular);
        Gdiplus::StringFormat cFmt;
        cFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
        cFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
        Gdiplus::RectF rResetF((float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sideW, 24.0f);
        g.DrawString(L"Reset to Default", -1, &fReset, rResetF, &cFmt, &textMuted);

        // 4. MAIN CONTENT AREA (Split 2 Columns matching Model 3)
        float mainAreaX = sideX + sideW + 14.0f;
        float mainAreaY = sideY + 2.0f;
        float mainAreaW = (cardX + cardW - 10.0f) - mainAreaX;
        float colGap = 16.0f;
        float col1W = std::floor(mainAreaW * 0.44f);
        float col2W = mainAreaW - col1W - colGap;
        float col2X = mainAreaX + col1W + colGap;

        // Middle vertical divider line
        g.DrawLine(&sepPen, mainAreaX + col1W + colGap * 0.5f, mainAreaY, mainAreaX + col1W + colGap * 0.5f, mainAreaY + sideH);

        // Section Typography
        Gdiplus::Font fontColTitle(L"Segoe UI", 7.8f, Gdiplus::FontStyleBold);
        Gdiplus::Font fontLabel(L"Segoe UI", 7.8f, Gdiplus::FontStyleRegular);
        Gdiplus::Font fontSubLabel(L"Segoe UI", 7.2f, Gdiplus::FontStyleRegular);
        Gdiplus::Font fontValue(L"Segoe UI", 12.0f, Gdiplus::FontStyleBold);
        Gdiplus::SolidBrush textBlue(UICommon::ColModel3Blue);
        Gdiplus::SolidBrush textDarkSlate(UICommon::ColModel3TextDark);
        Gdiplus::SolidBrush textLightSlate(UICommon::ColModel3TextLight);

        // =========================================================================
        // COLUMN 1: DISPLAY & ENGINE PREFERENCES
        // =========================================================================
        float c1Y = mainAreaY;
        g.DrawString(L"DISPLAY & ENGINE PREFERENCES", -1, &fontColTitle, Gdiplus::PointF(mainAreaX, c1Y), &textBlue);
        c1Y += 20.0f;

        // Panel Size Segmented Pills
        g.DrawString(L"Panel Size", -1, &fontLabel, Gdiplus::PointF(mainAreaX, c1Y), &textDarkSlate);
        c1Y += 16.0f;

        auto drawSegmentPill = [&](RECT& r, float px, float py, float pw, float ph,
                                   const wchar_t* title, const wchar_t* sub, bool active) {
            r = { (int)px, (int)py, (int)(px + pw), (int)(py + ph) };
            Gdiplus::SolidBrush pBg(active ? UICommon::ColModel3BlueLight : UICommon::ColModel3Bg);
            UICommon::FillRoundRectangle(g, &pBg, px, py, pw, ph, 4.0f);
            Gdiplus::Pen pPen(active ? UICommon::ColModel3BlueBorder : UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &pPen, px, py, pw, ph, 4.0f);

            Gdiplus::SolidBrush tB(active ? UICommon::ColModel3BlueHover : UICommon::ColModel3TextDark);
            Gdiplus::SolidBrush sB(active ? UICommon::ColModel3BlueHover : UICommon::ColModel3TextLight);
            Gdiplus::Font fT(L"Segoe UI", 7.2f, active ? Gdiplus::FontStyleBold : Gdiplus::FontStyleRegular);
            Gdiplus::Font fS(L"Segoe UI", 6.2f, Gdiplus::FontStyleRegular);

            Gdiplus::RectF rt(px, py + 2.0f, pw, 12.0f);
            Gdiplus::RectF rs(px, py + 14.0f, pw, 10.0f);
            g.DrawString(title, -1, &fT, rt, &cFmt, &tB);
            g.DrawString(sub, -1, &fS, rs, &cFmt, &sB);
        };

        float pillW = std::floor((col1W - 8.0f) / 3.0f);
        bool isDefault = (s_modalW == 760 && s_modalH == 560);
        bool isWide = (s_modalW == 880 && s_modalH == 660);
        bool isCompact = (s_modalW == 540 && s_modalH == 500);

        drawSegmentPill(s_presetDefaultRect, mainAreaX, c1Y, pillW, 28.0f, L"Default", L"460×580", isDefault);
        drawSegmentPill(s_presetWideRect, mainAreaX + pillW + 4.0f, c1Y, pillW, 28.0f, L"Wide", L"560×680", isWide);
        drawSegmentPill(s_presetCompactRect, mainAreaX + (pillW + 4.0f) * 2.0f, c1Y, pillW, 28.0f, L"Compact", L"420×500", isCompact);
        c1Y += 34.0f;

        // Opacity Slider
        int opPct = static_cast<int>((g_drawerOpacity.load() / 255.0f) * 100.0f);
        wchar_t opText[32];
        swprintf_s(opText, L"%d%%", opPct);
        g.DrawString(L"Opacity", -1, &fontLabel, Gdiplus::PointF(mainAreaX, c1Y), &textDarkSlate);

        Gdiplus::RectF opValRect(mainAreaX + col1W - 40.0f, c1Y, 40.0f, 14.0f);
        Gdiplus::StringFormat rAlign;
        rAlign.SetAlignment(Gdiplus::StringAlignmentFar);
        g.DrawString(opText, -1, &fontSubLabel, opValRect, &rAlign, &textMuted);
        c1Y += 16.0f;

        s_opacitySliderRect = { (int)mainAreaX, (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 12.0f) };
        Gdiplus::SolidBrush trackBg(UICommon::ColModel3Border);
        UICommon::FillRoundRectangle(g, &trackBg, mainAreaX, c1Y + 4.0f, col1W, 4.0f, 2.0f);

        float opNorm = std::clamp((g_drawerOpacity.load() - 120.0f) / (255.0f - 120.0f), 0.0f, 1.0f);
        if (opNorm > 0.01f) {
            Gdiplus::SolidBrush fillBlue(UICommon::ColModel3Blue);
            UICommon::FillRoundRectangle(g, &fillBlue, mainAreaX, c1Y + 4.0f, col1W * opNorm, 4.0f, 2.0f);
        }
        float thumbOpX = mainAreaX + opNorm * (col1W - 12.0f);
        Gdiplus::SolidBrush thumbB(UICommon::ColModel3Blue);
        g.FillEllipse(&thumbB, thumbOpX, c1Y, 12.0f, 12.0f);
        c1Y += 18.0f;

        // Display Modes Subtitle & Toggles
        g.DrawString(L"Display Modes", -1, &fontLabel, Gdiplus::PointF(mainAreaX, c1Y), &textDarkSlate);
        c1Y += 18.0f;

        s_compactToggleRect = { (int)(mainAreaX + col1W - 90.0f), (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 18.0f) };
        g.DrawString(L"Compact Mode", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 2.0f), &textMuted);
        UICommon::DrawModernSwitch(g, (float)s_compactToggleRect.left, (float)s_compactToggleRect.top,
                                   g_compactView.load(), L"Enabled", L"Disabled");
        c1Y += 24.0f;

        s_consoleToggleRect = { (int)(mainAreaX + col1W - 90.0f), (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 18.0f) };
        g.DrawString(L"Graphic Console", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 2.0f), &textMuted);
        UICommon::DrawModernSwitch(g, (float)s_consoleToggleRect.left, (float)s_consoleToggleRect.top,
                                   !g_hideConsoleSection.load(), L"Visible", L"Hidden");
        c1Y += 26.0f;

        // Combo UI & Participation Points Section
        g.DrawString(L"Combo UI & Participation Points", -1, &fontLabel, Gdiplus::PointF(mainAreaX, c1Y), &textDarkSlate);
        c1Y += 18.0f;

        s_comboToggleRect = { (int)(mainAreaX + col1W - 90.0f), (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 18.0f) };
        g.DrawString(L"Combo UI", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 2.0f), &textMuted);
        UICommon::DrawModernSwitch(g, (float)s_comboToggleRect.left, (float)s_comboToggleRect.top,
                                   g_comboVisible.load(), L"Enabled", L"Disabled");
        c1Y += 22.0f;

        // Scale Slider
        float curComboScale = g_comboScale.load();
        int scalePct = static_cast<int>(curComboScale * 100.0f + 0.5f);
        wchar_t scaleText[32];
        swprintf_s(scaleText, L"%d%%", scalePct);
        g.DrawString(L"Scale", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y), &textMuted);
        Gdiplus::RectF scValRect(mainAreaX + col1W - 40.0f, c1Y, 40.0f, 14.0f);
        g.DrawString(scaleText, -1, &fontSubLabel, scValRect, &rAlign, &textMuted);
        c1Y += 14.0f;

        s_comboScaleSliderRect = { (int)mainAreaX, (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 12.0f) };
        UICommon::FillRoundRectangle(g, &trackBg, mainAreaX, c1Y + 4.0f, col1W, 4.0f, 2.0f);
        float scNorm = std::clamp((curComboScale - 0.55f) / (1.60f - 0.55f), 0.0f, 1.0f);
        if (scNorm > 0.01f) {
            Gdiplus::SolidBrush fillBlue(UICommon::ColModel3Blue);
            UICommon::FillRoundRectangle(g, &fillBlue, mainAreaX, c1Y + 4.0f, col1W * scNorm, 4.0f, 2.0f);
        }
        float thumbScX = mainAreaX + scNorm * (col1W - 12.0f);
        g.FillEllipse(&thumbB, thumbScX, c1Y, 12.0f, 12.0f);
        c1Y += 18.0f;

        // Position Segmented Buttons: Top, Mid-Right, Center, Mid-Left
        g.DrawString(L"Position", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y), &textMuted);
        c1Y += 14.0f;

        float posBtnW = std::floor((col1W - 9.0f) / 4.0f);
        float curNormX = g_comboPosNormX.load();
        float curNormY = g_comboPosNormY.load();
        bool isTop = (curNormY < 0.25f);
        bool isMidRight = (!isTop && curNormX > 0.65f);
        bool isCenter = (!isTop && curNormX >= 0.35f && curNormX <= 0.65f);
        bool isLeft = (!isTop && curNormX < 0.35f);

        auto drawPosBtn = [&](RECT& r, float px, const wchar_t* lbl, bool active) {
            r = { (int)px, (int)c1Y, (int)(px + posBtnW), (int)(c1Y + 22.0f) };
            Gdiplus::SolidBrush b(active ? UICommon::ColModel3Blue : UICommon::ColModel3Bg);
            UICommon::FillRoundRectangle(g, &b, px, c1Y, posBtnW, 22.0f, 3.0f);
            Gdiplus::Pen p(active ? UICommon::ColModel3Blue : UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &p, px, c1Y, posBtnW, 22.0f, 3.0f);

            Gdiplus::SolidBrush t(active ? UICommon::ColModel3Card : UICommon::ColModel3TextDark);
            Gdiplus::Font f(L"Segoe UI", 6.8f, active ? Gdiplus::FontStyleBold : Gdiplus::FontStyleRegular);
            Gdiplus::RectF rf(px, c1Y + 2.0f, posBtnW, 18.0f);
            g.DrawString(lbl, -1, &f, rf, &cFmt, &t);
        };

        drawPosBtn(s_comboPosTopRect, mainAreaX, L"Top", isTop);
        drawPosBtn(s_comboPosMidRightRect, mainAreaX + posBtnW + 3.0f, L"Mid-Right", isMidRight);
        drawPosBtn(s_comboPosCenterRect, mainAreaX + (posBtnW + 3.0f) * 2.0f, L"Center", isCenter);
        drawPosBtn(s_comboPosLeftRect, mainAreaX + (posBtnW + 3.0f) * 3.0f, L"Mid-Left", isLeft);
        c1Y += 30.0f;

        // Engine & Rendering Controls (FOV, Cam, FPS, TriBuffer, Aniso)
        if (s_activeTab == DrawerTab::Engine || col1W >= 180.0f) {
            g.DrawString(L"Engine & Graphics", -1, &fontLabel, Gdiplus::PointF(mainAreaX, c1Y), &textDarkSlate);
            c1Y += 18.0f;

            // FOV Slider
            wchar_t fovText[32];
            swprintf_s(fovText, L"%.0f°", g_cvarFov.load());
            g.DrawString(L"Panoramic FOV", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y), &textMuted);
            Gdiplus::RectF fovRect(mainAreaX + col1W - 40.0f, c1Y, 40.0f, 14.0f);
            g.DrawString(fovText, -1, &fontSubLabel, fovRect, &rAlign, &textMuted);
            c1Y += 14.0f;

            s_fovSliderRect = { (int)mainAreaX, (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 12.0f) };
            UICommon::FillRoundRectangle(g, &trackBg, mainAreaX, c1Y + 4.0f, col1W, 4.0f, 2.0f);
            float fovNorm = std::clamp((g_cvarFov.load() - 60.0f) / (120.0f - 60.0f), 0.0f, 1.0f);
            if (fovNorm > 0.01f) {
                Gdiplus::SolidBrush fillBlue(UICommon::ColModel3Blue);
                UICommon::FillRoundRectangle(g, &fillBlue, mainAreaX, c1Y + 4.0f, col1W * fovNorm, 4.0f, 2.0f);
            }
            float thumbFovX = mainAreaX + fovNorm * (col1W - 12.0f);
            g.FillEllipse(&thumbB, thumbFovX, c1Y, 12.0f, 12.0f);
            c1Y += 18.0f;

            // CamMax Slider
            wchar_t camText[32];
            swprintf_s(camText, L"%.0fm", g_cvarCamMax.load());
            g.DrawString(L"Camera Zoom", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y), &textMuted);
            Gdiplus::RectF camRect(mainAreaX + col1W - 40.0f, c1Y, 40.0f, 14.0f);
            g.DrawString(camText, -1, &fontSubLabel, camRect, &rAlign, &textMuted);
            c1Y += 14.0f;

            s_camSliderRect = { (int)mainAreaX, (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 12.0f) };
            UICommon::FillRoundRectangle(g, &trackBg, mainAreaX, c1Y + 4.0f, col1W, 4.0f, 2.0f);
            float camNorm = std::clamp((g_cvarCamMax.load() - 5.0f) / (45.0f - 5.0f), 0.0f, 1.0f);
            if (camNorm > 0.01f) {
                Gdiplus::SolidBrush fillBlue(UICommon::ColModel3Blue);
                UICommon::FillRoundRectangle(g, &fillBlue, mainAreaX, c1Y + 4.0f, col1W * camNorm, 4.0f, 2.0f);
            }
            float thumbCamX = mainAreaX + camNorm * (col1W - 12.0f);
            g.FillEllipse(&thumbB, thumbCamX, c1Y, 12.0f, 12.0f);
            c1Y += 18.0f;

            // FPS Cap Buttons [ 60 ] [ 144 ] [ MAX ]
            g.DrawString(L"FPS Cap", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 3.0f), &textMuted);
            float fpsW = 34.0f;
            auto drawFpsCap = [&](RECT& r, float px, int fpsVal, const wchar_t* txt) {
                r = { (int)px, (int)c1Y, (int)(px + fpsW), (int)(c1Y + 20.0f) };
                bool active = (g_cvarMaxFps.load() == fpsVal);
                Gdiplus::SolidBrush b(active ? UICommon::ColModel3Blue : UICommon::ColModel3Bg);
                UICommon::FillRoundRectangle(g, &b, px, c1Y, fpsW, 20.0f, 3.0f);
                Gdiplus::Pen p(active ? UICommon::ColModel3Blue : UICommon::ColModel3Border, 1.0f);
                UICommon::DrawRoundRectangle(g, &p, px, c1Y, fpsW, 20.0f, 3.0f);

                Gdiplus::SolidBrush t(active ? UICommon::ColModel3Card : UICommon::ColModel3TextDark);
                Gdiplus::Font f(L"Segoe UI", 6.8f, active ? Gdiplus::FontStyleBold : Gdiplus::FontStyleRegular);
                Gdiplus::RectF rf(px, c1Y + 2.0f, fpsW, 16.0f);
                g.DrawString(txt, -1, &f, rf, &cFmt, &t);
            };

            float fpsStartX = mainAreaX + col1W - (fpsW * 3.0f + 8.0f);
            drawFpsCap(s_fps60Rect, fpsStartX, 60, L"60");
            drawFpsCap(s_fps144Rect, fpsStartX + fpsW + 4.0f, 144, L"144");
            drawFpsCap(s_fpsMaxRect, fpsStartX + (fpsW + 4.0f) * 2.0f, 0, L"MAX");
            c1Y += 26.0f;

            // Triple Buffer & Anisotropic
            s_tbToggleRect = { (int)(mainAreaX + col1W - 88.0f), (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 18.0f) };
            g.DrawString(L"Triple Buffer", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 2.0f), &textMuted);
            UICommon::DrawModernSwitch(g, (float)s_tbToggleRect.left, (float)s_tbToggleRect.top,
                                       g_cvarTripleBuffering.load(), L"ON", L"OFF");
            c1Y += 24.0f;

            s_anisoToggleRect = { (int)(mainAreaX + col1W - 46.0f), (int)c1Y, (int)(mainAreaX + col1W), (int)(c1Y + 20.0f) };
            g.DrawString(L"Anisotropic", -1, &fontSubLabel, Gdiplus::PointF(mainAreaX, c1Y + 2.0f), &textMuted);
            bool anisoActive = g_cvarAnisotropic.load();
            Gdiplus::SolidBrush anisoBg(anisoActive ? UICommon::ColModel3Blue : UICommon::ColModel3Bg);
            UICommon::FillRoundRectangle(g, &anisoBg, (float)s_anisoToggleRect.left, c1Y, 46.0f, 20.0f, 3.0f);
            Gdiplus::Pen anisoPen(anisoActive ? UICommon::ColModel3Blue : UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &anisoPen, (float)s_anisoToggleRect.left, c1Y, 46.0f, 20.0f, 3.0f);
            Gdiplus::SolidBrush anisoText(anisoActive ? UICommon::ColModel3Card : UICommon::ColModel3TextDark);
            Gdiplus::Font anisoFont(L"Segoe UI", 6.8f, Gdiplus::FontStyleBold);
            Gdiplus::RectF anisoRectF((float)s_anisoToggleRect.left, c1Y + 2.0f, 46.0f, 16.0f);
            g.DrawString(anisoActive ? L"16x" : L"OFF", -1, &anisoFont, anisoRectF, &cFmt, &anisoText);
            c1Y += 28.0f;
        }

        // Bottom Action Button: [ ✓ Save & Close ]
        s_saveSettingsBtnRect = { (int)mainAreaX, (int)(cardY + cardH - 36.0f), (int)(mainAreaX + col1W), (int)(cardY + cardH - 10.0f) };
        Gdiplus::SolidBrush saveBg(UICommon::ColModel3Blue);
        UICommon::FillRoundRectangle(g, &saveBg, (float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top, col1W, 26.0f, 5.0f);

        Gdiplus::Font fSave(L"Segoe UI", 8.2f, Gdiplus::FontStyleBold);
        Gdiplus::RectF rSaveF((float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top, col1W, 26.0f);
        g.DrawString(L"✓ Save & Close", -1, &fSave, rSaveF, &cFmt, &textWhite);

        // =========================================================================
        // COLUMN 2: DPS METER & COMBAT METRICS
        // =========================================================================
        float c2Y = mainAreaY;
        g.DrawString(L"DPS METER & COMBAT METRICS", -1, &fontColTitle, Gdiplus::PointF(col2X, c2Y), &textBlue);
        c2Y += 18.0f;

        // Target Dropdown / Banner
        UpdateTargetFromGameMemory();
        std::lock_guard<std::recursive_mutex> lock(g_combatMutex);

        s_targetDropdownRect = { (int)col2X, (int)c2Y, (int)(col2X + col2W), (int)(c2Y + 26.0f) };
        Gdiplus::SolidBrush dropBg(UICommon::ColModel3Bg);
        UICommon::FillRoundRectangle(g, &dropBg, col2X, c2Y, col2W, 26.0f, 5.0f);
        Gdiplus::Pen dropBorder(UICommon::ColModel3Border, 1.0f);
        UICommon::DrawRoundRectangle(g, &dropBorder, col2X, c2Y, col2W, 26.0f, 5.0f);

        std::wstring targetDisplayName = g_currentTarget.hasTarget
            ? UICommon::Utf8ToWide(g_currentTarget.name)
            : L"Training Dummy";
        std::wstring targetBannerText = L"Target: " + targetDisplayName;
        if (g_currentTarget.hasTarget && g_currentTarget.level > 0) {
            targetBannerText += L" (Lv. " + std::to_wstring(g_currentTarget.level) + L")";
        }

        Gdiplus::Font fontTargetDrop(L"Segoe UI", 8.0f, Gdiplus::FontStyleBold);
        g.DrawString(targetBannerText.c_str(), -1, &fontTargetDrop, Gdiplus::PointF(col2X + 10.0f, c2Y + 5.0f), &textDarkSlate);

        // Chevron down icon
        Gdiplus::Font fontChevron(L"Segoe UI", 7.5f, Gdiplus::FontStyleBold);
        g.DrawString(L"∨", -1, &fontChevron, Gdiplus::PointF(col2X + col2W - 18.0f, c2Y + 5.0f), &textMuted);
        c2Y += 34.0f;

        // Big 3 Metrics: Time, Group DPS, Total Damage
        float metricCardW = std::floor((col2W - 12.0f) / 3.0f);
        auto drawMetricCard = [&](float mx, const wchar_t* mLabel, const std::wstring& mVal) {
            Gdiplus::SolidBrush mBg(UICommon::ColModel3Bg);
            UICommon::FillRoundRectangle(g, &mBg, mx, c2Y, metricCardW, 44.0f, 5.0f);
            Gdiplus::Pen mPen(UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &mPen, mx, c2Y, metricCardW, 44.0f, 5.0f);

            Gdiplus::Font fMLabel(L"Segoe UI", 7.0f, Gdiplus::FontStyleRegular);
            g.DrawString(mLabel, -1, &fMLabel, Gdiplus::PointF(mx + 8.0f, c2Y + 5.0f), &textMuted);

            Gdiplus::Font fMVal(L"Segoe UI", 11.5f, Gdiplus::FontStyleBold);
            g.DrawString(mVal.c_str(), -1, &fMVal, Gdiplus::PointF(mx + 8.0f, c2Y + 20.0f), &textDarkSlate);
        };

        drawMetricCard(col2X, L"Time", UICommon::FormatTime(g_battleDurationSeconds.load()));
        drawMetricCard(col2X + metricCardW + 6.0f, L"Group DPS", UICommon::FormatNumber(g_totalBattleDps.load()));
        drawMetricCard(col2X + (metricCardW + 6.0f) * 2.0f, L"Total Damage", UICommon::FormatNumber(g_totalBattleDamage.load()));
        c2Y += 52.0f;

        // DPS Over Time Spline Chart (Requirement 8 & 9: Clean Minimal Spline)
        g.DrawString(L"DPS Over Time", -1, &fontLabel, Gdiplus::PointF(col2X, c2Y), &textDarkSlate);
        c2Y += 16.0f;

        float chartH = 68.0f;
        UICommon::DrawDpsSplineChart(g, col2X, c2Y, col2W, chartH, g_dpsHistory, g_battleDurationSeconds.load());
        c2Y += chartH + 12.0f;

        // Damage Breakdown (Requirement 10 & 14: Skill Icons & Real Breakdown)
        g.DrawString(L"Damage Breakdown", -1, &fontLabel, Gdiplus::PointF(col2X, c2Y), &textDarkSlate);
        c2Y += 18.0f;

        struct DisplaySkillItem {
            std::string name;
            uint32_t skillId;
            uint64_t damage;
            float pct;
        };
        std::vector<DisplaySkillItem> skillItems;

        uint64_t totalBreakdownDmg = 0;
        for (const auto& sk : g_skillBreakdown) totalBreakdownDmg += sk.totalDamage;
        if (totalBreakdownDmg == 0) totalBreakdownDmg = g_totalBattleDamage.load();

        if (!g_skillBreakdown.empty()) {
            for (size_t i = 0; i < g_skillBreakdown.size() && i < 4; ++i) {
                const auto& sk = g_skillBreakdown[i];
                float p = totalBreakdownDmg > 0 ? ((float)sk.totalDamage / (float)totalBreakdownDmg * 100.0f) : 0.0f;
                skillItems.push_back({ sk.skillName, sk.skillId, sk.totalDamage, p });
            }
        } else {
            // Default elegant entries if awaiting combat
            skillItems.push_back({ "Auto Attack", 0, 19782, 31.2f });
            skillItems.push_back({ "Moreth Promise", 1102, 17641, 27.8f });
            skillItems.push_back({ "Critical Strike", 1205, 14923, 23.5f });
            skillItems.push_back({ "Other Effects", 0, 11016, 17.5f });
        }

        float skillRowH = 17.0f;
        for (const auto& item : skillItems) {
            // Skill Icon
            IconManager::DrawSkillIcon(g, col2X, c2Y + 1.0f, 13.0f, item.skillId, item.name);

            // Skill Name
            std::wstring wSkillName = UICommon::Utf8ToWide(item.name);
            Gdiplus::Font fSkill(L"Segoe UI", 7.2f, Gdiplus::FontStyleRegular);
            g.DrawString(wSkillName.c_str(), -1, &fSkill, Gdiplus::PointF(col2X + 17.0f, c2Y), &textDarkSlate);

            // Blue pill progress bar
            float barStartX = col2X + col2W * 0.45f;
            float barMaxW = col2W * 0.28f;
            float barW = barMaxW * std::clamp(item.pct / 100.0f, 0.05f, 1.0f);

            Gdiplus::SolidBrush barBg(UICommon::ColModel3Border);
            UICommon::FillRoundRectangle(g, &barBg, barStartX, c2Y + 4.0f, barMaxW, 5.0f, 2.5f);

            Gdiplus::SolidBrush barFill(UICommon::ColModel3Blue);
            UICommon::FillRoundRectangle(g, &barFill, barStartX, c2Y + 4.0f, barW, 5.0f, 2.5f);

            // Percentage
            wchar_t pctBuf[16];
            swprintf_s(pctBuf, L"%.1f%%", item.pct);
            Gdiplus::Font fSub(L"Segoe UI", 6.8f, Gdiplus::FontStyleRegular);
            g.DrawString(pctBuf, -1, &fSub, Gdiplus::PointF(barStartX + barMaxW + 8.0f, c2Y + 1.0f), &textMuted);

            // Absolute Damage
            std::wstring dmgStr = UICommon::FormatNumber(item.damage);
            Gdiplus::RectF dmgRect(col2X + col2W - 55.0f, c2Y + 1.0f, 55.0f, 14.0f);
            g.DrawString(dmgStr.c_str(), -1, &fSub, dmgRect, &rAlign, &textDarkSlate);

            c2Y += skillRowH;
        }
        c2Y += 6.0f;

        // Combat Log (Last 5) - Requirement 11: Compact and professional
        g.DrawString(L"Combat Log (Last 5)", -1, &fontLabel, Gdiplus::PointF(col2X, c2Y), &textDarkSlate);
        c2Y += 16.0f;

        size_t tSize = g_combatTimeline.size();
        if (tSize == 0) {
            // Demonstration rows matching Model 3 reference
            struct DemoLog { const wchar_t* t; const wchar_t* desc; const wchar_t* dmg; };
            DemoLog logs[] = {
                { L"21:05:12", L"Brawler → Moreth Promise (Effect)", L"827" },
                { L"21:05:13", L"Brawler → Auto Attack", L"215" },
                { L"21:05:13", L"Brawler → Moreth Promise (Effect)", L"827" },
                { L"21:05:14", L"Critical Strike 1,408 dmg", L"156" },
                { L"21:05:15", L"Moreth Promise (Effect) activated", L"116" }
            };
            for (const auto& l : logs) {
                Gdiplus::Font fLog(L"Segoe UI", 6.8f, Gdiplus::FontStyleRegular);
                g.DrawString(L"🕒", -1, &fLog, Gdiplus::PointF(col2X, c2Y), &textBlue);
                wchar_t lineBuf[128];
                swprintf_s(lineBuf, L"%ls  %ls", l.t, l.desc);
                g.DrawString(lineBuf, -1, &fLog, Gdiplus::PointF(col2X + 14.0f, c2Y), &textMuted);
                Gdiplus::RectF dRect(col2X + col2W - 40.0f, c2Y, 40.0f, 12.0f);
                g.DrawString(l.dmg, -1, &fLog, dRect, &rAlign, &textDarkSlate);
                c2Y += 14.0f;
            }
        } else {
            int startIdx = (tSize > 5) ? static_cast<int>(tSize - 5) : 0;
            for (int i = startIdx; i < static_cast<int>(tSize); ++i) {
                const auto& evt = g_combatTimeline[i];
                std::wstring wTime = UICommon::Utf8ToWide(evt.timeStr);
                std::wstring wAtt = UICommon::Utf8ToWide(evt.attacker);
                std::wstring wSkill = UICommon::Utf8ToWide(evt.skillName);

                Gdiplus::Font fLog(L"Segoe UI", 6.8f, Gdiplus::FontStyleRegular);
                g.DrawString(L"🕒", -1, &fLog, Gdiplus::PointF(col2X, c2Y), &textBlue);

                wchar_t logLine[128];
                swprintf_s(logLine, L"%ls  %ls → %ls", wTime.c_str(), wAtt.c_str(), wSkill.c_str());
                g.DrawString(logLine, -1, &fLog, Gdiplus::PointF(col2X + 14.0f, c2Y), &textMuted);

                std::wstring wDmg = UICommon::FormatNumber(evt.damage);
                Gdiplus::RectF dRect(col2X + col2W - 40.0f, c2Y, 40.0f, 12.0f);
                Gdiplus::SolidBrush dmgBrush(evt.isCrit ? UICommon::ColGoldAccent : UICommon::ColModel3TextDark);
                g.DrawString(wDmg.c_str(), -1, &fLog, dRect, &rAlign, &dmgBrush);
                c2Y += 14.0f;
            }
        }

        // =========================================================================
        // 5. FLOATING 3D MODEL & TARGET CARD (Bottom-Right Overlapping Edge)
        // =========================================================================
        // Requirement 12 & 31: Model sits overlapping the window edge
        if (g_featModel3D.load() && !g_compactView.load()) {
            float modelW = 160.0f;
            float modelH = 190.0f;
            float modelX = (float)s_modalW - 170.0f;
            float modelY = (float)s_modalH - 245.0f;

            // Render Target 3D Model (or Player character fallback if no target)
            if (g_currentTarget.hasTarget) {
                uint8_t raceCode = (g_currentTarget.race == "ELYOS" ? 0 : (g_currentTarget.race == "ASMODIANS" ? 1 : 2));
                CryModelBridge::SetTargetEntity(g_currentTarget.modelId, g_currentTarget.isNpc ? 1 : 0, raceCode, g_currentTarget.yaw);
            } else {
                CryModelBridge::SetTargetEntity(0, 0, 0, 0); // Player character fallback
            }

            CryModelBridge::RenderThumbnail(g, modelX, modelY, modelW, modelH);

            // Floating Target Card Underneath the Pedestal
            float tCardW = 165.0f;
            float tCardH = 68.0f;
            float tCardX = (float)s_modalW - 175.0f;
            float tCardY = (float)s_modalH - 85.0f;

            // Target card shadow & background
            Gdiplus::SolidBrush tCardShadow(Gdiplus::Color(35, 15, 23, 42));
            UICommon::FillRoundRectangle(g, &tCardShadow, tCardX + 2.0f, tCardY + 3.0f, tCardW, tCardH, 7.0f);

            Gdiplus::SolidBrush tCardBg(UICommon::ColModel3Card);
            UICommon::FillRoundRectangle(g, &tCardBg, tCardX, tCardY, tCardW, tCardH, 7.0f);
            Gdiplus::Pen tCardBorder(UICommon::ColModel3Border, 1.0f);
            UICommon::DrawRoundRectangle(g, &tCardBorder, tCardX, tCardY, tCardW, tCardH, 7.0f);

            // Target Name
            std::wstring tcName = g_currentTarget.hasTarget
                ? UICommon::Utf8ToWide(g_currentTarget.name)
                : L"TRAINING DUMMY";
            std::transform(tcName.begin(), tcName.end(), tcName.begin(), ::towupper);

            Gdiplus::Font fTcName(L"Segoe UI", 8.2f, Gdiplus::FontStyleBold);
            g.DrawString(tcName.c_str(), -1, &fTcName, Gdiplus::PointF(tCardX + 10.0f, tCardY + 8.0f), &textDarkSlate);

            // Close button [×] on target card
            s_targetCardCloseRect = { (int)(tCardX + tCardW - 20.0f), (int)(tCardY + 6.0f), (int)(tCardX + tCardW - 6.0f), (int)(tCardY + 20.0f) };
            Gdiplus::Font fTcClose(L"Segoe UI", 7.0f, Gdiplus::FontStyleRegular);
            g.DrawString(L"×", -1, &fTcClose, Gdiplus::PointF(tCardX + tCardW - 18.0f, tCardY + 6.0f), &textLightSlate);

            // Subtitle: Rank / Level / Class
            std::wstring tcSub;
            if (g_currentTarget.hasTarget) {
                tcSub = L"Rank " + UICommon::Utf8ToWide(g_currentTarget.rating) + L" - " + UICommon::Utf8ToWide(g_currentTarget.race);
                if (g_currentTarget.level > 0) {
                    tcSub += L" (Lv. " + std::to_wstring(g_currentTarget.level) + L")";
                }
            } else {
                tcSub = L"Rank 8 - Brawler";
            }

            Gdiplus::Font fTcSub(L"Segoe UI", 6.8f, Gdiplus::FontStyleRegular);
            g.DrawString(tcSub.c_str(), -1, &fTcSub, Gdiplus::PointF(tCardX + 10.0f, tCardY + 22.0f), &textMuted);

            // Crimson / Red HP Bar with centered %
            float tHpW = tCardW - 20.0f;
            float tHpH = 16.0f;
            float tHpX = tCardX + 10.0f;
            float tHpY = tCardY + 38.0f;

            float hpFrac = (g_currentTarget.hasTarget && g_currentTarget.maxHp > 0)
                ? (float)g_currentTarget.currentHp / (float)g_currentTarget.maxHp
                : 1.0f;
            hpFrac = std::clamp(hpFrac, 0.0f, 1.0f);

            Gdiplus::SolidBrush hpBg(Gdiplus::Color(255, 254, 226, 226)); // Soft light red
            UICommon::FillRoundRectangle(g, &hpBg, tHpX, tHpY, tHpW, tHpH, 3.0f);

            if (hpFrac > 0.0f) {
                Gdiplus::SolidBrush hpFill(UICommon::ColModel3HpRed);
                UICommon::FillRoundRectangle(g, &hpFill, tHpX, tHpY, tHpW * hpFrac, tHpH, 3.0f);
            }

            wchar_t hpPctText[32];
            swprintf_s(hpPctText, L"%.0f%%", hpFrac * 100.0f);
            Gdiplus::Font fHpPct(L"Segoe UI", 7.2f, Gdiplus::FontStyleBold);
            Gdiplus::RectF hpRectF(tHpX, tHpY + 1.0f, tHpW, tHpH);
            g.DrawString(hpPctText, -1, &fHpPct, hpRectF, &cFmt, &textWhite);
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

        // 1. Header Close Button [ X ]
        if (mx >= s_closeBtnRect.left && mx <= s_closeBtnRect.right &&
            my >= s_closeBtnRect.top && my <= s_closeBtnRect.bottom) {
            Close();
            return 0;
        }

        // Header Minimize Button [ - ]
        if (mx >= s_minimizeBtnRect.left && mx <= s_minimizeBtnRect.right &&
            my >= s_minimizeBtnRect.top && my <= s_minimizeBtnRect.bottom) {
            Close();
            return 0;
        }

        // Header Help Button [ ? ]
        if (mx >= s_helpBtnRect.left && mx <= s_helpBtnRect.right &&
            my >= s_helpBtnRect.top && my <= s_helpBtnRect.bottom) {
            s_activeTab = (s_activeTab == DrawerTab::Advanced) ? DrawerTab::Display : DrawerTab::Advanced;
            Repaint();
            return 0;
        }

        // Target Card Close [ X ]
        if (mx >= s_targetCardCloseRect.left && mx <= s_targetCardCloseRect.right &&
            my >= s_targetCardCloseRect.top && my <= s_targetCardCloseRect.bottom) {
            std::lock_guard<std::recursive_mutex> lock(g_combatMutex);
            g_currentTarget.hasTarget = false;
            Repaint();
            return 0;
        }

        // 2. Sidebar Navigation Tabs
        auto checkTab = [&](RECT& r, DrawerTab t) {
            if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                s_activeTab = t;
                Repaint();
                return true;
            }
            return false;
        };

        if (checkTab(s_tabDisplayRect, DrawerTab::Display)) return 0;
        if (checkTab(s_tabDpsMeterRect, DrawerTab::DpsMeter)) return 0;
        if (checkTab(s_tabComboRect, DrawerTab::ComboUi)) return 0;
        if (checkTab(s_tabEngineRect, DrawerTab::Engine)) return 0;
        if (checkTab(s_tabAdvancedRect, DrawerTab::Advanced)) return 0;

        // Reset to Default Button
        if (mx >= s_resetDefaultsRect.left && mx <= s_resetDefaultsRect.right &&
            my >= s_resetDefaultsRect.top && my <= s_resetDefaultsRect.bottom) {
            ResizeDrawer(760, 560);
            g_drawerOpacity = 255;
            g_compactView = false;
            g_hideConsoleSection = false;
            g_comboVisible = true;
            g_comboScale = 1.0f;
            g_comboPosNormX = 0.80f;
            g_comboPosNormY = 0.50f;
            CVarManager::SetFov(75.0f);
            CVarManager::SetCameraMax(25.0f);
            CVarManager::SetMaxFps(144);
            CVarManager::SetTripleBuffering(true);
            CVarManager::SetAnisotropic(true);
            ResetCombatSession();
            BrConfig::Save();
            Repaint();
            return 0;
        }

        // 3. Panel Size Presets
        if (mx >= s_presetDefaultRect.left && mx <= s_presetDefaultRect.right &&
            my >= s_presetDefaultRect.top && my <= s_presetDefaultRect.bottom) {
            ResizeDrawer(760, 560);
            return 0;
        }
        if (mx >= s_presetWideRect.left && mx <= s_presetWideRect.right &&
            my >= s_presetWideRect.top && my <= s_presetWideRect.bottom) {
            ResizeDrawer(880, 660);
            return 0;
        }
        if (mx >= s_presetCompactRect.left && mx <= s_presetCompactRect.right &&
            my >= s_presetCompactRect.top && my <= s_presetCompactRect.bottom) {
            ResizeDrawer(540, 500);
            return 0;
        }

        // 4. Opacity Slider Drag Start
        if (mx >= s_opacitySliderRect.left && mx <= s_opacitySliderRect.right &&
            my >= s_opacitySliderRect.top - 6 && my <= s_opacitySliderRect.bottom + 6) {
            s_draggingOpacity = true;
            SetCapture(hwnd);
            return 0;
        }

        // 5. Toggles
        if (mx >= s_compactToggleRect.left && mx <= s_compactToggleRect.right &&
            my >= s_compactToggleRect.top && my <= s_compactToggleRect.bottom) {
            g_compactView = !g_compactView.load();
            BrConfig::Save();
            Repaint();
            return 0;
        }

        if (mx >= s_consoleToggleRect.left && mx <= s_consoleToggleRect.right &&
            my >= s_consoleToggleRect.top && my <= s_consoleToggleRect.bottom) {
            g_hideConsoleSection = !g_hideConsoleSection.load();
            BrConfig::Save();
            Repaint();
            return 0;
        }

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

        // Combo Scale Slider
        if (mx >= s_comboScaleSliderRect.left && mx <= s_comboScaleSliderRect.right &&
            my >= s_comboScaleSliderRect.top - 6 && my <= s_comboScaleSliderRect.bottom + 6) {
            s_draggingComboScale = true;
            SetCapture(hwnd);
            return 0;
        }

        // Combo Position Buttons
        auto applyComboPos = [&](float tx, float ty) {
            SetComboOverlayLayout(tx, ty, g_comboScale.load());
            g_comboPosNormX = tx;
            g_comboPosNormY = ty;
            g_ComboUI.RequestLayoutRefresh();
            BrConfig::Save();
            Repaint();
        };

        if (mx >= s_comboPosTopRect.left && mx <= s_comboPosTopRect.right &&
            my >= s_comboPosTopRect.top && my <= s_comboPosTopRect.bottom) {
            applyComboPos(0.50f, 0.12f);
            return 0;
        }
        if (mx >= s_comboPosMidRightRect.left && mx <= s_comboPosMidRightRect.right &&
            my >= s_comboPosMidRightRect.top && my <= s_comboPosMidRightRect.bottom) {
            applyComboPos(0.80f, 0.50f);
            return 0;
        }
        if (mx >= s_comboPosCenterRect.left && mx <= s_comboPosCenterRect.right &&
            my >= s_comboPosCenterRect.top && my <= s_comboPosCenterRect.bottom) {
            applyComboPos(0.50f, 0.50f);
            return 0;
        }
        if (mx >= s_comboPosLeftRect.left && mx <= s_comboPosLeftRect.right &&
            my >= s_comboPosLeftRect.top && my <= s_comboPosLeftRect.bottom) {
            applyComboPos(0.20f, 0.50f);
            return 0;
        }

        // Engine Sliders & Toggles
        if (mx >= s_fovSliderRect.left && mx <= s_fovSliderRect.right &&
            my >= s_fovSliderRect.top - 6 && my <= s_fovSliderRect.bottom + 6) {
            s_draggingFov = true;
            SetCapture(hwnd);
            return 0;
        }
        if (mx >= s_camSliderRect.left && mx <= s_camSliderRect.right &&
            my >= s_camSliderRect.top - 6 && my <= s_camSliderRect.bottom + 6) {
            s_draggingCam = true;
            SetCapture(hwnd);
            return 0;
        }

        auto checkFpsCap = [&](RECT& r, int fps) {
            if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                CVarManager::SetMaxFps(fps);
                Repaint();
                return true;
            }
            return false;
        };
        if (checkFpsCap(s_fps60Rect, 60)) return 0;
        if (checkFpsCap(s_fps144Rect, 144)) return 0;
        if (checkFpsCap(s_fpsMaxRect, 0)) return 0;

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

        // Save & Close Button
        if (mx >= s_saveSettingsBtnRect.left && mx <= s_saveSettingsBtnRect.right &&
            my >= s_saveSettingsBtnRect.top && my <= s_saveSettingsBtnRect.bottom) {
            Close();
            return 0;
        }

        // 6. Window Dragging (Requirement 16: Free repositioning by clicking Header)
        if (mx >= s_headerDragRect.left && mx <= s_headerDragRect.right &&
            my >= s_headerDragRect.top && my <= s_headerDragRect.bottom) {
            s_isDraggingWindow = true;
            GetCursorPos(&s_dragStartCursor);
            RECT wr = {};
            GetWindowRect(hwnd, &wr);
            s_dragStartPos.x = wr.left;
            s_dragStartPos.y = wr.top;
            SetCapture(hwnd);
            return 0;
        }

        return 0;
    }

    case WM_MOUSEMOVE: {
        int mx = LOWORD(lParam);

        if (s_isDraggingWindow) {
            POINT curPt = {};
            GetCursorPos(&curPt);
            int newX = s_dragStartPos.x + (curPt.x - s_dragStartCursor.x);
            int newY = s_dragStartPos.y + (curPt.y - s_dragStartCursor.y);

            g_drawerPosX = newX;
            g_drawerPosY = newY;
            SetWindowPos(hwnd, HWND_TOPMOST, newX, newY, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE);
            return 0;
        }

        if (s_draggingOpacity && (s_opacitySliderRect.right > s_opacitySliderRect.left)) {
            float pct = (float)(mx - s_opacitySliderRect.left) / (float)(s_opacitySliderRect.right - s_opacitySliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            int op = static_cast<int>(120 + pct * (255 - 120));
            g_drawerOpacity = op;
            Repaint();
        } else if (s_draggingComboScale && (s_comboScaleSliderRect.right > s_comboScaleSliderRect.left)) {
            float pct = (float)(mx - s_comboScaleSliderRect.left) / (float)(s_comboScaleSliderRect.right - s_comboScaleSliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float scale = 0.55f + pct * (1.60f - 0.55f);
            SetComboOverlayLayout(g_comboPosNormX.load(), g_comboPosNormY.load(), scale);
            g_comboScale = scale;
            g_ComboUI.RequestLayoutRefresh();
            Repaint();
        } else if (s_draggingFov && (s_fovSliderRect.right > s_fovSliderRect.left)) {
            float pct = (float)(mx - s_fovSliderRect.left) / (float)(s_fovSliderRect.right - s_fovSliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float fov = 60.0f + pct * (120.0f - 60.0f);
            CVarManager::SetFov(fov);
            Repaint();
        } else if (s_draggingCam && (s_camSliderRect.right > s_camSliderRect.left)) {
            float pct = (float)(mx - s_camSliderRect.left) / (float)(s_camSliderRect.right - s_camSliderRect.left);
            pct = std::clamp(pct, 0.0f, 1.0f);
            float cam = 5.0f + pct * (45.0f - 5.0f);
            CVarManager::SetCameraMax(cam);
            Repaint();
        }
        return 0;
    }

    case WM_LBUTTONUP: {
        if (s_isDraggingWindow) {
            s_isDraggingWindow = false;
            ReleaseCapture();
            BrConfig::Save();
            return 0;
        }

        if (s_draggingOpacity || s_draggingComboScale || s_draggingFov || s_draggingCam) {
            s_draggingOpacity = false;
            s_draggingComboScale = false;
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
