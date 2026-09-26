#include "DrawerModalUI.h"
#include "UICommon.h"
#include "IconManager.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../core/I18n.h"
#include "../cvar/CVarManager.h"
#include "../config/BrConfig.h"
#include "../combo/ComboUI.h"
#include "../combo/ComboTypes.h"
#include "../network/WebSocketClient.h"
#include <algorithm>
#include <cmath>
#include <vector>
#include <string>
#include <unordered_map>

namespace BrService {

static const wchar_t* kDrawerClassName = L"BrService_DrawerModal";
static int s_modalW = 760;
static int s_modalH = 560;

// Reusable DIB/DC buffer cache to eliminate per-frame allocations
static HDC s_drawerMemDC = nullptr;
static HBITMAP s_drawerBitmap = nullptr;
static HBITMAP s_drawerOldBitmap = nullptr;
static int s_drawerBufW = 0;
static int s_drawerBufH = 0;

static void EnsureDrawerBuffer(HDC screenDC, int width, int height) {
    if (s_drawerMemDC && s_drawerBufW == width && s_drawerBufH == height) return;
    if (s_drawerMemDC) {
        if (s_drawerOldBitmap) SelectObject(s_drawerMemDC, s_drawerOldBitmap);
        if (s_drawerBitmap) DeleteObject(s_drawerBitmap);
        DeleteDC(s_drawerMemDC);
    }
    s_drawerMemDC = CreateCompatibleDC(screenDC);
    BITMAPINFO bmi = {};
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = width;
    bmi.bmiHeader.biHeight = -height;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    void* pvBits = nullptr;
    s_drawerBitmap = CreateDIBSection(screenDC, &bmi, DIB_RGB_COLORS, &pvBits, NULL, 0);
    s_drawerOldBitmap = (HBITMAP)SelectObject(s_drawerMemDC, s_drawerBitmap);
    s_drawerBufW = width;
    s_drawerBufH = height;
}

static void ReleaseDrawerBuffer() {
    if (s_drawerMemDC) {
        if (s_drawerOldBitmap) SelectObject(s_drawerMemDC, s_drawerOldBitmap);
        if (s_drawerBitmap) DeleteObject(s_drawerBitmap);
        DeleteDC(s_drawerMemDC);
    }
    s_drawerMemDC = nullptr;
    s_drawerBitmap = nullptr;
    s_drawerOldBitmap = nullptr;
    s_drawerBufW = s_drawerBufH = 0;
}

// Persistent Segoe UI font cache to eliminate DirectWrite/GDI churn
struct DrawerFontKey {
    int sizeX10;
    bool bold;
    bool operator==(const DrawerFontKey& o) const { return sizeX10 == o.sizeX10 && bold == o.bold; }
};
struct DrawerFontKeyHash {
    size_t operator()(const DrawerFontKey& k) const { return (size_t)(k.sizeX10 * 2 + (k.bold ? 1 : 0)); }
};
static std::unordered_map<DrawerFontKey, Gdiplus::Font*, DrawerFontKeyHash> s_drawerFontCache;

static Gdiplus::Font* GetSegoeFont(float size, bool bold = false) {
    DrawerFontKey k = { (int)(size * 10.0f + 0.5f), bold };
    auto it = s_drawerFontCache.find(k);
    if (it != s_drawerFontCache.end()) return it->second;

    Gdiplus::Font* font = new Gdiplus::Font(L"Segoe UI", size, bold ? Gdiplus::FontStyleBold : Gdiplus::FontStyleRegular);
    s_drawerFontCache[k] = font;
    return font;
}

static void ReleaseDrawerFonts() {
    for (auto& pair : s_drawerFontCache) {
        delete pair.second;
    }
    s_drawerFontCache.clear();
}

enum class DrawerTab { Display = 0, DpsMeter, ComboUi, Engine, Advanced };
static DrawerTab s_activeTab = DrawerTab::Display;

// Theme: 0=Light 1=Dark 2=Gray 3=Navy
static int s_theme = 0;

static Gdiplus::Color ThemeBg() {
    switch(s_theme) {
        case 1: return UICommon::ColThemeDarkBg;
        case 2: return UICommon::ColThemeGrayBg;
        case 3: return UICommon::ColThemeNavyBg;
        default: return UICommon::ColModel3Bg;
    }
}
static Gdiplus::Color ThemeCard() {
    switch(s_theme) {
        case 1: return UICommon::ColThemeDarkCard;
        case 2: return UICommon::ColThemeGrayCard;
        case 3: return UICommon::ColThemeNavyCard;
        default: return UICommon::ColModel3Card;
    }
}
static Gdiplus::Color ThemeBorder() {
    switch(s_theme) {
        case 1: return UICommon::ColThemeDarkBorder;
        case 2: return Gdiplus::Color(255, 110, 118, 138);
        case 3: return Gdiplus::Color(255, 38, 60, 130);
        default: return UICommon::ColModel3Border;
    }
}
static Gdiplus::Color ThemeTextDark() {
    switch(s_theme) {
        case 1: return UICommon::ColThemeDarkText;
        case 2: return Gdiplus::Color(255, 240, 242, 248);
        case 3: return Gdiplus::Color(255, 220, 230, 255);
        default: return UICommon::ColModel3TextDark;
    }
}
static Gdiplus::Color ThemeTextMuted() {
    switch(s_theme) {
        case 1: return Gdiplus::Color(255, 140, 148, 168);
        case 2: return Gdiplus::Color(255, 185, 190, 205);
        case 3: return Gdiplus::Color(255, 130, 150, 200);
        default: return UICommon::ColModel3TextMuted;
    }
}

static bool s_isDraggingWindow = false;
static POINT s_dragStartCursor = { 0, 0 };
static POINT s_dragStartPos = { 0, 0 };
static POINT s_mousePos = { -1, -1 };

static bool s_draggingOpacity = false;
static bool s_draggingComboScale = false;
static bool s_draggingComboOpacity = false;
static bool s_draggingFov = false;
static bool s_draggingCam = false;

// Navigation & Header Rectangles
static RECT s_headerDragRect = {};
static RECT s_helpBtnRect = {}, s_minimizeBtnRect = {}, s_closeBtnRect = {};
static RECT s_tabDisplayRect = {}, s_tabDpsMeterRect = {}, s_tabComboRect = {}, s_tabEngineRect = {}, s_tabAdvancedRect = {};
static RECT s_resetDefaultsRect = {};

// Tab Display Rectangles
static RECT s_presetDefaultRect = {}, s_presetWideRect = {}, s_presetCompactRect = {}, s_opacitySliderRect = {};
static RECT s_compactToggleRect = {}, s_consoleToggleRect = {}, s_comboToggleRect = {}, s_comboScaleSliderRect = {};
static RECT s_comboPosTopRect = {}, s_comboPosMidRightRect = {}, s_comboPosCenterRect = {}, s_comboPosLeftRect = {};
static RECT s_saveSettingsBtnRect = {}, s_targetDropdownRect = {}, s_resetCombatBtnRect = {};
static RECT s_targetCardRect = {}, s_targetCardCloseRect = {}, s_advSecureAreaToggle = {};

// Tab DPS Meter Rectangles & State
static int s_selectedCombatIndex = -1; // -1 = Live Combat; 0..N-1 = index in g_combatHistory
static RECT s_combatLiveBtnRect = {};
static RECT s_combatHistBtnRects[5] = {};
static RECT s_dpsResetRect = {};

// Tab Combo UI Rectangles
static RECT s_comboTabToggleRect = {}, s_comboTabScaleSlider = {}, s_comboTabOpacitySlider = {};
static RECT s_comboTabPosTop = {}, s_comboTabPosMidRight = {}, s_comboTabPosCenter = {}, s_comboTabPosLeft = {};

// Tab Engine Rectangles
static RECT s_engFovSlider = {}, s_engCamSlider = {};
static RECT s_engFps60Rect = {}, s_engFps144Rect = {}, s_engFpsMaxRect = {};
static RECT s_engTbToggleRect = {}, s_engConsoleRect = {};

// Tab Advanced Rectangles
static RECT s_advOpacitySlider = {}, s_advPresetDefault = {}, s_advPresetWide = {}, s_advPresetCompact = {};
static RECT s_advThemeLight = {}, s_advThemeDark = {}, s_advThemeGray = {}, s_advThemeNavy = {};
static RECT s_advPinnedToggle = {};
static RECT s_advCompactToggle = {}, s_advConsoleToggle = {};
static RECT s_advFovToggle = {}, s_advCamToggle = {}, s_advFpsToggle = {};

struct MemoryTargetRaw {
    bool valid;
    uint32_t objId, modelId;
    uint8_t type, race;
    wchar_t name[128];
    int hp, maxHp;
    float px, py, pz, yaw;
};

static inline bool IsValidUserPointer(uintptr_t addr) {
#ifdef _WIN64
    return addr >= 0x10000 && addr <= 0x00007FFFFFFEFFFF;
#else
    return addr >= 0x10000 && addr <= 0x7FFEFFFF;
#endif
}

static bool ReadTargetMemoryRaw(MemoryTargetRaw* o) {
    if (!o) return false;
    o->valid = false;
    uintptr_t hG = (uintptr_t)GetModuleHandleA("Game.dll");
    if (!hG) return false;

    __try {
        uintptr_t targetBase = hG + 0xECE610;
        if (!IsValidUserPointer(targetBase)) return false;
        uintptr_t tp = *(uintptr_t*)targetBase;
        if (!IsValidUserPointer(tp)) return false;

        // Validar e filtrar self-target (jogador selecionando a si mesmo)
        uintptr_t addr = hG + 0xECDDC8;
        static const uintptr_t pOffsets[] = { 0x70, 0x10, 0x20 };
        for (int i = 0; i < 3; ++i) {
            if (!IsValidUserPointer(addr)) break;
            addr = *(uintptr_t*)addr;
            if (!IsValidUserPointer(addr)) break;
            addr += pOffsets[i];
        }
        uintptr_t pPlayer = (IsValidUserPointer(addr)) ? *(uintptr_t*)addr : 0;
        if (pPlayer != 0 && tp == pPlayer) {
            // Jogador com target em si mesmo -> tratar como sem alvo
            return false;
        }

        uintptr_t entityPtrAddr = tp + 0x378;
        if (!IsValidUserPointer(entityPtrAddr)) return false;
        uintptr_t e = *(uintptr_t*)entityPtrAddr;
        if (!IsValidUserPointer(e)) return false;

        o->objId = *(uint32_t*)(e + 0x24);
        o->modelId = *(uint32_t*)(e + 0x20);

        if (pPlayer != 0) {
            uintptr_t pPEAddr = pPlayer + 0x378;
            if (IsValidUserPointer(pPEAddr)) {
                uintptr_t pPE = *(uintptr_t*)pPEAddr;
                if (IsValidUserPointer(pPE) && *(uint32_t*)(pPE + 0x24) == o->objId) {
                    // ObjId do target coincide com o próprio jogador
                    return false;
                }
            }
        }

        o->hp = *(int*)(e + 0x147C);
        o->maxHp = *(int*)(e + 0x1478);
        o->type = *(uint8_t*)(e + 0x38);
        o->race = *(uint8_t*)(e + 0x39);

        wchar_t* pN = (wchar_t*)(e + 0x46);
        if (IsValidUserPointer((uintptr_t)pN)) wcsncpy_s(o->name, pN, _TRUNCATE);
        else o->name[0] = L'\0';

        o->px = *(float*)(tp + 0x3C);
        o->py = *(float*)(tp + 0x40);
        o->pz = *(float*)(tp + 0x44);
        o->yaw = *(float*)(tp + 0x48);
        o->valid = true;
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static bool UpdateTargetFromGameMemory() {
    MemoryTargetRaw r = {};
    if (ReadTargetMemoryRaw(&r) && r.valid && r.objId != 0) {
        std::lock_guard<std::recursive_mutex> lk(g_combatMutex);
        g_currentTarget.hasTarget = true;
        g_currentTarget.targetId = r.objId;
        g_currentTarget.modelId = r.modelId;
        g_currentTarget.isNpc = (r.type != 0);

        if (wcslen(r.name) > 0) {
            char b[256] = {};
            WideCharToMultiByte(CP_UTF8, 0, r.name, -1, b, sizeof(b), nullptr, nullptr);
            g_currentTarget.name = b;
        }
        if (r.maxHp > 0) {
            g_currentTarget.currentHp = (r.hp >= 0) ? r.hp : 0;
            g_currentTarget.maxHp = r.maxHp;
        }
        if (r.race == 0) g_currentTarget.race = "ELYOS";
        else if (r.race == 1) g_currentTarget.race = "ASMODIANS";
        else g_currentTarget.race = "BALAUR";

        g_currentTarget.posX = r.px;
        g_currentTarget.posY = r.py;
        g_currentTarget.posZ = r.pz;
        g_currentTarget.yaw = r.yaw;
        return true;
    } else {
        // Se a engine indica que não há alvo ativo selecionado (ou é o próprio jogador)
        uintptr_t hG = (uintptr_t)GetModuleHandleA("Game.dll");
        if (hG) {
            uintptr_t targetBase = hG + 0xECE610;
            if (IsValidUserPointer(targetBase)) {
                uintptr_t tp = *(uintptr_t*)targetBase;
                if (!tp) {
                    std::lock_guard<std::recursive_mutex> lk(g_combatMutex);
                    g_currentTarget.hasTarget = false;
                    g_currentTarget.targetId = 0;
                    g_currentTarget.modelId = 0;
                    g_currentTarget.isNpc = false;
                    g_currentTarget.name.clear();
                    return false;
                }
            }
        }
    }
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
        DWORD e = GetLastError();
        if (e != ERROR_CLASS_ALREADY_EXISTS) {
            LogError("Falha DrawerModal RegisterClass: %lu", e);
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
        LogError("Falha criar DrawerModal: %lu", GetLastError());
        return false;
    }

    LogInfo("DrawerModalUI inicializado (%dx%d Op=%d Tema=%d Pinned=%d).",
            s_modalW, s_modalH, g_drawerOpacity.load(), s_theme, g_drawerPinned.load() ? 1 : 0);
    return true;
}

void DrawerModalUI::Shutdown() {
    IconManager::Shutdown();
    ReleaseDrawerBuffer();
    ReleaseDrawerFonts();
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

static void UpdateDrawerTimer() {
    if (!g_hDrawerModalWnd || !g_isDrawerOpen.load()) return;
    UINT interval = (s_activeTab == DrawerTab::Display && g_currentTarget.hasTarget) ? 40 : 250;
    SetTimer(g_hDrawerModalWnd, 1, interval, nullptr);
}

void DrawerModalUI::Open() {
    if (!g_featConsole.load()) return;
    g_isDrawerOpen = true;
    bool canShow = !g_isLoadingScreen.load() && g_isGameActive.load();
    if (g_hDrawerModalWnd && canShow) {
        ShowWindow(g_hDrawerModalWnd, SW_SHOWNOACTIVATE);
        UpdateDrawerTimer();
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
    bool canShow = g_isDrawerOpen.load() && g_hDrawerModalWnd && !g_isLoadingScreen.load() && g_isGameActive.load();
    if (canShow) {
        if (!IsWindowVisible(g_hDrawerModalWnd)) {
            ShowWindow(g_hDrawerModalWnd, SW_SHOWNOACTIVATE);
            UpdateDrawerTimer();
            Repaint();
        }
    } else {
        Hide();
    }
}

bool DrawerModalUI::IsOpen() {
    return g_isDrawerOpen.load();
}

void DrawerModalUI::UpdatePosition(int gX, int gY, int gW, int gH) {
    if (!g_hDrawerModalWnd || !IsWindow(g_hDrawerModalWnd)) return;
    s_modalW = std::clamp(g_drawerW.load(), 540, 960);
    s_modalH = std::clamp(g_drawerH.load(), 480, 800);
    if (s_modalH > gH - 30) s_modalH = gH - 30;

    int mX = g_drawerPosX.load(), mY2 = g_drawerPosY.load();
    if (mX < 0 || mY2 < 0) {
        mX = gX + (gW - s_modalW) / 2;
        mY2 = gY + (gH - s_modalH) / 2;
        if (mX < gX + 10) mX = gX + 10;
        if (mY2 < gY + 10) mY2 = gY + 10;
        g_drawerPosX = mX;
        g_drawerPosY = mY2;
    }

    if (g_drawerPinned.load()) {
        int minX = gX;
        int maxX = gX + gW - s_modalW;
        int minY = gY;
        int maxY = gY + gH - s_modalH;
        if (maxX >= minX) mX = std::clamp(mX, minX, maxX);
        if (maxY >= minY) mY2 = std::clamp(mY2, minY, maxY);
        g_drawerPosX = mX;
        g_drawerPosY = mY2;
    }

    bool v = g_featConsole.load() && g_isDrawerOpen.load() && !g_isLoadingScreen.load() && g_isGameActive.load();

    static int s_prevX = -9999, s_prevY = -9999, s_prevW = -9999, s_prevH = -9999;
    static int s_prevVis = -1;
    int curVis = v ? 1 : 0;

    if (mX != s_prevX || mY2 != s_prevY || s_modalW != s_prevW || s_modalH != s_prevH || curVis != s_prevVis) {
        s_prevX = mX; s_prevY = mY2; s_prevW = s_modalW; s_prevH = s_modalH; s_prevVis = curVis;
        SetWindowPos(g_hDrawerModalWnd, HWND_TOPMOST, mX, mY2, s_modalW, s_modalH,
                     SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS | (v ? SWP_SHOWWINDOW : SWP_HIDEWINDOW));
        if (v) {
            UpdateDrawerTimer();
            InvalidateRect(g_hDrawerModalWnd, nullptr, FALSE);
        } else {
            KillTimer(g_hDrawerModalWnd, 1);
        }
    }
}

void DrawerModalUI::ResizeDrawer(int nW, int nH) {
    g_drawerW = std::clamp(nW, 540, 960);
    g_drawerH = std::clamp(nH, 480, 800);
    s_modalW = g_drawerW.load();
    s_modalH = g_drawerH.load();

    HWND hG = g_gameHwnd.load();
    if (hG && IsWindow(hG)) {
        RECT gr = {};
        GetWindowRect(hG, &gr);
        UpdatePosition(gr.left, gr.top, gr.right - gr.left, gr.bottom - gr.top);
    } else {
        Repaint();
    }
    BrConfig::Save();
}

void DrawerModalUI::Repaint() {
    if (!g_hDrawerModalWnd || !IsWindow(g_hDrawerModalWnd)) return;
    InvalidateRect(g_hDrawerModalWnd, nullptr, FALSE);
}

void DrawerModalUI::Paint(HWND hwnd) {
    HDC sc = GetDC(nullptr);
    EnsureDrawerBuffer(sc, s_modalW, s_modalH);
    HDC mc = s_drawerMemDC;
    if (!mc) {
        ReleaseDC(nullptr, sc);
        return;
    }

    {
        Gdiplus::Graphics g(mc);
        g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
        g.SetTextRenderingHint(Gdiplus::TextRenderingHintClearTypeGridFit);
        g.Clear(Gdiplus::Color(0, 0, 0, 0));

        Gdiplus::Color cBg = ThemeBg(), cCd = ThemeCard(), cBr = ThemeBorder();
        Gdiplus::Color cTD = ThemeTextDark(), cTM = ThemeTextMuted(), cBl = UICommon::ColModel3Blue;
        Gdiplus::SolidBrush bTD(cTD), bTM(cTM), bBl(cBl), bWh(cCd);
        Gdiplus::Pen spn(cBr, 1.0f);

        float cX = 4, cY = 4, cW = (float)s_modalW - 8, cH = (float)s_modalH - 8;

        // Fundo com sombra suave e borda moderna
        {
            Gdiplus::SolidBrush sh(Gdiplus::Color(25, 15, 23, 42));
            UICommon::FillRoundRectangle(g, &sh, cX + 3, cY + 4, cW, cH, 14);
        }
        {
            Gdiplus::SolidBrush bg(cCd);
            UICommon::FillRoundRectangle(g, &bg, cX, cY, cW, cH, 14);
            Gdiplus::Pen bp(cBr, 1.2f);
            UICommon::DrawRoundRectangle(g, &bp, cX, cY, cW, cH, 14);
        }

        // ================= HEADER =================
        s_headerDragRect = { (int)cX, (int)cY, (int)(cX + cW - 100), (int)(cY + 46) };
        float iX = cX + 14, iY = cY + 11, iS = 26;
        {
            Gdiplus::SolidBrush ib(cBl);
            UICommon::FillRoundRectangle(g, &ib, iX, iY, iS, iS, 6);
            Gdiplus::Pen ip(cCd, 2);
            Gdiplus::PointF pts[4] = { { iX + 13, iY + 5 }, { iX + 21, iY + 13 }, { iX + 13, iY + 21 }, { iX + 5, iY + 13 } };
            g.DrawPolygon(&ip, pts, 4);
            g.DrawLine(&ip, iX + 13, iY + 8, iX + 13, iY + 18);
        }

        Gdiplus::Font& fT = *GetSegoeFont(11.0f, true);
        Gdiplus::Font& fS = *GetSegoeFont(7.8f, false);
        g.DrawString(L"ACADEMY SHOW", -1, &fT, Gdiplus::PointF(iX + iS + 10, cY + 9), &bTD);
        g.DrawString(L"DPS Meter & Combat Metrics", -1, &fS, Gdiplus::PointF(iX + iS + 10, cY + 25), &bTM);

        auto dHB = [&](RECT& r, int bx, int by, const wchar_t* s2) {
            r = { bx, by, bx + 24, by + 24 };
            Gdiplus::SolidBrush bb(cCd);
            UICommon::FillRoundRectangle(g, &bb, (float)bx, (float)by, 24, 24, 5);
            Gdiplus::Pen bp2(cBr, 1);
            UICommon::DrawRoundRectangle(g, &bp2, (float)bx, (float)by, 24, 24, 5);
            Gdiplus::Font& bf = *GetSegoeFont(8.5f, true);
            Gdiplus::StringFormat sf;
            sf.SetAlignment(Gdiplus::StringAlignmentCenter);
            sf.SetLineAlignment(Gdiplus::StringAlignmentCenter);
            g.DrawString(s2, -1, &bf, Gdiplus::RectF((float)bx, (float)by, 24, 24), &sf, &bTM);
        };

        int bBX = (int)(cX + cW - 88), bBY = (int)(cY + 12);
        dHB(s_helpBtnRect, bBX, bBY, L"?");
        dHB(s_minimizeBtnRect, bBX + 28, bBY, L"\u2212");
        dHB(s_closeBtnRect, bBX + 56, bBY, L"\u00D7");
        g.DrawLine(&spn, cX + 12, cY + 46, cX + cW - 12, cY + 46);

        // ================= SIDEBAR (NAVBAR) =================
        float sX = cX + 8, sY = cY + 54, sW = 108, sH = cH - 62;
        g.DrawLine(&spn, sX + sW + 4, sY, sX + sW + 4, sY + sH);

        struct NT { DrawerTab t; const wchar_t* l; const wchar_t* i; RECT* r; };
        NT nvs[] = {
            { DrawerTab::Display, L"Display", L"\u25A3", &s_tabDisplayRect },
            { DrawerTab::DpsMeter, L"DPS Meter", L"\u25A5", &s_tabDpsMeterRect },
            { DrawerTab::ComboUi, L"Combo UI", L"\u2694", &s_tabComboRect },
            { DrawerTab::Engine, L"Engine", L"\u2699", &s_tabEngineRect },
            { DrawerTab::Advanced, L"Advanced", L"\u26A1", &s_tabAdvancedRect }
        };

        Gdiplus::Font& ftb = *GetSegoeFont(8.2f, false);
        Gdiplus::Font& ftbb = *GetSegoeFont(8.2f, true);
        float ctY = sY + 4;

        for (auto& n : nvs) {
            bool ac = (s_activeTab == n.t);
            *(n.r) = { (int)sX, (int)ctY, (int)(sX + sW), (int)(ctY + 30) };
            if (ac) {
                Gdiplus::SolidBrush ab(cBl);
                UICommon::FillRoundRectangle(g, &ab, sX, ctY, sW, 30, 6);
                Gdiplus::PointF ap[3] = { { sX + sW, ctY + 10 }, { sX + sW + 4, ctY + 15 }, { sX + sW, ctY + 20 } };
                g.FillPolygon(&ab, ap, 3);
                Gdiplus::SolidBrush wh(cCd);
                g.DrawString(n.i, -1, &ftbb, Gdiplus::PointF(sX + 10, ctY + 6), &wh);
                g.DrawString(n.l, -1, &ftbb, Gdiplus::PointF(sX + 28, ctY + 6), &wh);
            } else {
                g.DrawString(n.i, -1, &ftb, Gdiplus::PointF(sX + 10, ctY + 6), &bTM);
                g.DrawString(n.l, -1, &ftb, Gdiplus::PointF(sX + 28, ctY + 6), &bTD);
            }
            ctY += 36;
        }

        s_resetDefaultsRect = { (int)sX, (int)(cY + cH - 36), (int)(sX + sW), (int)(cY + cH - 12) };
        {
            Gdiplus::SolidBrush rb(cBg);
            UICommon::FillRoundRectangle(g, &rb, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sW, 24, 4);
            Gdiplus::Pen rp(cBr, 1);
            UICommon::DrawRoundRectangle(g, &rp, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sW, 24, 4);
            Gdiplus::Font& fr = *GetSegoeFont(7.2f, false);
            Gdiplus::StringFormat cf;
            cf.SetAlignment(Gdiplus::StringAlignmentCenter);
            cf.SetLineAlignment(Gdiplus::StringAlignmentCenter);
            g.DrawString(L"Reset Defaults", -1, &fr, Gdiplus::RectF((float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, sW, 24), &cf, &bTM);
        }

        // ================= MAIN CONTENT AREA =================
        float mX = sX + sW + 14, mY = sY + 2, mW2 = (cX + cW - 10) - mX, mH2 = sH - 4;
        Gdiplus::Font& fCT = *GetSegoeFont(8.2f, true);
        Gdiplus::Font& fLb = *GetSegoeFont(7.8f, false);
        Gdiplus::Font& fSb = *GetSegoeFont(7.2f, false);
        Gdiplus::StringFormat cf2;
        cf2.SetAlignment(Gdiplus::StringAlignmentCenter);
        cf2.SetLineAlignment(Gdiplus::StringAlignmentCenter);
        Gdiplus::StringFormat rA;
        rA.SetAlignment(Gdiplus::StringAlignmentFar);

        auto dSl = [&](RECT& r2, float sx, float sy, float sw, float nv, const wchar_t* lb, const wchar_t* vl) {
            if (lb && lb[0]) g.DrawString(lb, -1, &fLb, Gdiplus::PointF(sx, sy), &bTD);
            if (vl && vl[0]) g.DrawString(vl, -1, &fSb, Gdiplus::RectF(sx + sw - 44, sy, 44, 14), &rA, &bTM);
            sy += 16;
            r2 = { (int)sx, (int)sy, (int)(sx + sw), (int)(sy + 12) };
            Gdiplus::SolidBrush tr(cBr);
            UICommon::FillRoundRectangle(g, &tr, sx, sy + 4, sw, 4, 2);
            if (nv > 0.01f) {
                Gdiplus::SolidBrush fl(cBl);
                UICommon::FillRoundRectangle(g, &fl, sx, sy + 4, sw * nv, 4, 2);
            }
            Gdiplus::SolidBrush th(cBl);
            g.FillEllipse(&th, sx + nv * (sw - 12.0f), sy, 12.0f, 12.0f);
        };

        auto dTR = [&](RECT& r2, float sx, float sy, float sw, const wchar_t* lb, bool ac) -> float {
            r2 = { (int)(sx + sw - 90), (int)sy, (int)(sx + sw), (int)(sy + 18) };
            g.DrawString(lb, -1, &fSb, Gdiplus::PointF(sx, sy + 2), &bTM);
            UICommon::DrawModernSwitch(g, (float)r2.left, (float)r2.top, ac, L"ON", L"OFF");
            return sy + 26;
        };

        auto dPl = [&](RECT& r2, float px, float py, float pw, float ph, const wchar_t* tx, bool ac) {
            r2 = { (int)px, (int)py, (int)(px + pw), (int)(py + ph) };
            Gdiplus::SolidBrush b(ac ? cBl : cBg);
            UICommon::FillRoundRectangle(g, &b, px, py, pw, ph, 4);
            Gdiplus::Pen p2(ac ? cBl : cBr, 1);
            UICommon::DrawRoundRectangle(g, &p2, px, py, pw, ph, 4);
            Gdiplus::SolidBrush t(ac ? cCd : cTD);
            Gdiplus::Font& f = *GetSegoeFont(7.2f, ac);
            g.DrawString(tx, -1, &f, Gdiplus::RectF(px, py + 2, pw, ph - 4), &cf2, &t);
        };

        // ================= TAB 0: DISPLAY (OVERVIEW) =================
        if (s_activeTab == DrawerTab::Display) {
            UpdateTargetFromGameMemory();
            std::lock_guard<std::recursive_mutex> lk(g_combatMutex);

            // Two-column layout: Display preferences | DPS Meter & Combat Metrics
            float cg = 14.0f;
            float c1W = std::floor(mW2 * 0.47f);
            float c2W = mW2 - c1W - cg;
            float c2X = mX + c1W + cg;

            g.DrawLine(&spn, mX + c1W + cg * 0.5f, mY, mX + c1W + cg * 0.5f, mY + mH2);

            // COLUMN 1: DISPLAY & ENGINE PREFERENCES
            float c1Y = mY;
            g.DrawString(L"DISPLAY & ENGINE PREFERENCES", -1, &fCT, Gdiplus::PointF(mX, c1Y), &bBl);
            c1Y += 20;

            g.DrawString(L"Panel Size", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 16;
            float pW = std::floor((c1W - 8) / 3.0f);
            auto dPresetBtn = [&](RECT& r2, float px, float py, float pw, float ph, const wchar_t* title, const wchar_t* sub, bool ac) {
                r2 = { (int)px, (int)py, (int)(px + pw), (int)(py + ph) };
                Gdiplus::SolidBrush b(ac ? cBl : cBg);
                UICommon::FillRoundRectangle(g, &b, px, py, pw, ph, 4);
                Gdiplus::Pen p2(ac ? cBl : cBr, 1);
                UICommon::DrawRoundRectangle(g, &p2, px, py, pw, ph, 4);
                Gdiplus::SolidBrush tt(ac ? cCd : cTD);
                Gdiplus::SolidBrush ts(ac ? Gdiplus::Color(220, 240, 255) : cTM);
                Gdiplus::Font& ft = *GetSegoeFont(7.2f, ac);
                Gdiplus::Font& fs2 = *GetSegoeFont(6.2f, false);
                g.DrawString(title, -1, &ft, Gdiplus::RectF(px, py + 2, pw, 13), &cf2, &tt);
                g.DrawString(sub, -1, &fs2, Gdiplus::RectF(px, py + 15, pw, 12), &cf2, &ts);
            };

            dPresetBtn(s_presetDefaultRect, mX, c1Y, pW, 30, L"Default", L"460x580", (s_modalW == 760 && s_modalH == 560));
            dPresetBtn(s_presetWideRect, mX + pW + 4, c1Y, pW, 30, L"Wide", L"560x680", (s_modalW == 880 && s_modalH == 660));
            dPresetBtn(s_presetCompactRect, mX + (pW + 4) * 2, c1Y, pW, 30, L"Compact", L"420x500", (s_modalW == 540 && s_modalH == 500));
            c1Y += 36;

            {
                float n = std::clamp((g_drawerOpacity.load() - 120.0f) / 135.0f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%d%%", (int)(n * 100 + 0.5f));
                dSl(s_opacitySliderRect, mX, c1Y, c1W, n, L"Opacity", b);
                c1Y += 32;
            }

            g.DrawString(L"Display Modes", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            c1Y = dTR(s_compactToggleRect, mX, c1Y, c1W, L"Compact Mode", g_compactView.load());
            c1Y = dTR(s_consoleToggleRect, mX, c1Y, c1W, L"Graphic Console", !g_hideConsoleSection.load());

            g.DrawString(L"Combo UI & Participation Points", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            c1Y = dTR(s_comboToggleRect, mX, c1Y, c1W, L"Combo UI", g_comboVisible.load());
            {
                float sc = g_comboScale.load(), n = std::clamp((sc - 0.55f) / 1.05f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%.0f%%", sc * 100);
                dSl(s_comboScaleSliderRect, mX, c1Y, c1W, n, L"Scale", b);
                c1Y += 30;
            }

            g.DrawString(L"Position", -1, &fSb, Gdiplus::PointF(mX, c1Y), &bTM);
            c1Y += 14;
            float pbW = std::floor((c1W - 9) / 4.0f), cnx = g_comboPosNormX.load(), cny = g_comboPosNormY.load();
            bool iT = cny < 0.25f, iMR = !iT && cnx > 0.65f, iC = !iT && cnx >= 0.35f && cnx <= 0.65f, iML = !iT && cnx < 0.35f;
            dPl(s_comboPosTopRect, mX, c1Y, pbW, 22, L"Top", iT);
            dPl(s_comboPosMidRightRect, mX + pbW + 3, c1Y, pbW, 22, L"Mid-R", iMR);
            dPl(s_comboPosCenterRect, mX + (pbW + 3) * 2, c1Y, pbW, 22, L"Center", iC);
            dPl(s_comboPosLeftRect, mX + (pbW + 3) * 3, c1Y, pbW, 22, L"Mid-L", iML);
            c1Y += 28;

            g.DrawString(L"Secure Area Overlay", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            c1Y = dTR(s_advSecureAreaToggle, mX, c1Y, c1W, L"Secure Area UI", true);

            float bW_half = std::floor((c1W - 8) / 2.0f);
            s_resetDefaultsRect = { (int)mX, (int)(cY + cH - 36), (int)(mX + bW_half), (int)(cY + cH - 10) };
            {
                Gdiplus::SolidBrush rb(cBg);
                UICommon::FillRoundRectangle(g, &rb, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, bW_half, 26, 5);
                Gdiplus::Pen rp(cBr, 1);
                UICommon::DrawRoundRectangle(g, &rp, (float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, bW_half, 26, 5);
                Gdiplus::Font& fr = *GetSegoeFont(7.2f, false);
                g.DrawString(L"Reset to Default", -1, &fr, Gdiplus::RectF((float)s_resetDefaultsRect.left, (float)s_resetDefaultsRect.top, bW_half, 26), &cf2, &bTM);
            }

            s_saveSettingsBtnRect = { (int)(mX + bW_half + 8), (int)(cY + cH - 36), (int)(mX + c1W), (int)(cY + cH - 10) };
            {
                Gdiplus::SolidBrush sb(cBl);
                UICommon::FillRoundRectangle(g, &sb, (float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top, bW_half, 26, 5);
                Gdiplus::Font& sf2 = *GetSegoeFont(7.5f, true);
                g.DrawString(L"\u2713 Save & Close", -1, &sf2, Gdiplus::RectF((float)s_saveSettingsBtnRect.left, (float)s_saveSettingsBtnRect.top, bW_half, 26), &cf2, &bWh);
            }

            // COLUMN 2: DPS METER & COMBAT METRICS
            float c2Y = mY;
            g.DrawString(L"DPS METER & COMBAT METRICS", -1, &fCT, Gdiplus::PointF(c2X, c2Y), &bBl);
            c2Y += 18;

            s_targetDropdownRect = { (int)c2X, (int)c2Y, (int)(c2X + c2W), (int)(c2Y + 26) };
            {
                Gdiplus::SolidBrush db(cBg);
                UICommon::FillRoundRectangle(g, &db, c2X, c2Y, c2W, 26, 5);
                Gdiplus::Pen dp(cBr, 1);
                UICommon::DrawRoundRectangle(g, &dp, c2X, c2Y, c2W, 26, 5);
                std::wstring tn = g_currentTarget.hasTarget ? UICommon::Utf8ToWide(g_currentTarget.name) : L"(Nenhum Alvo)";
                g.DrawString((L"Target: " + tn).c_str(), -1, &fLb, Gdiplus::PointF(c2X + 10, c2Y + 5), &bTD);
                g.DrawString(L"\u25BE", -1, &fLb, Gdiplus::PointF(c2X + c2W - 18, c2Y + 5), &bTM);
            }
            c2Y += 32;

            // 3 Metrics Cards: Time, Group DPS, Total Damage (Matching Image 2)
            float mWm = std::floor((c2W - 12) / 3.0f);
            auto dM = [&](float mx2, const wchar_t* lb, const std::wstring& vl) {
                Gdiplus::SolidBrush mb(cBg);
                UICommon::FillRoundRectangle(g, &mb, mx2, c2Y, mWm, 44, 5);
                Gdiplus::Pen mp(cBr, 1);
                UICommon::DrawRoundRectangle(g, &mp, mx2, c2Y, mWm, 44, 5);
                Gdiplus::Font& fl = *GetSegoeFont(6.8f, false);
                g.DrawString(lb, -1, &fl, Gdiplus::PointF(mx2 + 6, c2Y + 4), &bTM);
                Gdiplus::Font& fv = *GetSegoeFont(10.5f, true);
                g.DrawString(vl.c_str(), -1, &fv, Gdiplus::PointF(mx2 + 6, c2Y + 18), &bTD);
            };

            dM(c2X, L"Time", UICommon::FormatTime(g_battleDurationSeconds.load()));
            dM(c2X + (mWm + 6), L"Group DPS", UICommon::FormatNumber(g_totalDealtDps.load()));
            dM(c2X + (mWm + 6) * 2, L"Total Damage", UICommon::FormatNumber(g_totalDamageDealt.load()));
            c2Y += 50;

            g.DrawString(L"DPS Over Time", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
            c2Y += 15;
            UICommon::DrawDpsSplineChart(g, c2X, c2Y, c2W, 52, g_dpsHistory, g_battleDurationSeconds.load());
            c2Y += 62;

            g.DrawString(L"Damage Breakdown", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
            c2Y += 15;
            uint64_t tb = g_totalDamageDealt.load();
            size_t ns = std::min(g_skillBreakdown.size(), (size_t)4);
            if (ns > 0) {
                for (size_t i = 0; i < ns; ++i) {
                    auto& sk = g_skillBreakdown[i];
                    float p = tb > 0 ? (float)sk.totalDamage / tb * 100.0f : 0.0f;
                    IconManager::DrawSkillIcon(g, c2X, c2Y + 1, 13, sk.skillId, sk.skillName);
                    Gdiplus::Font& fsk = *GetSegoeFont(7.2f, false);
                    g.DrawString(UICommon::Utf8ToWide(sk.skillName).c_str(), -1, &fsk, Gdiplus::PointF(c2X + 17, c2Y), &bTD);
                    float bSX = c2X + c2W * 0.45f, bMW = c2W * 0.26f, bW = bMW * std::clamp(p / 100.0f, 0.05f, 1.0f);
                    Gdiplus::SolidBrush bg2(cBr);
                    UICommon::FillRoundRectangle(g, &bg2, bSX, c2Y + 4, bMW, 5, 2.5f);
                    Gdiplus::SolidBrush bf(cBl);
                    UICommon::FillRoundRectangle(g, &bf, bSX, c2Y + 4, bW, 5, 2.5f);
                    wchar_t pb[16];
                    swprintf_s(pb, L"%.1f%%", p);
                    g.DrawString(pb, -1, &fsk, Gdiplus::PointF(bSX + bMW + 4, c2Y + 1), &bTM);
                    g.DrawString(UICommon::FormatNumber(sk.totalDamage).c_str(), -1, &fsk, Gdiplus::RectF(c2X + c2W - 40, c2Y + 1, 40, 14), &rA, &bTD);
                    c2Y += 16;
                }
            } else {
                Gdiplus::Font& fn = *GetSegoeFont(7.5f, false);
                g.DrawString(L"Awaiting combat...", -1, &fn, Gdiplus::PointF(c2X, c2Y), &bTM);
                c2Y += 16;
            }
            c2Y += 4;

            // Combat Log (Last 5) - Matching Image 2
            g.DrawString(L"Combat Log (Last 5)", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
            c2Y += 15;
            size_t tSz = g_combatTimeline.size();
            size_t nLog = std::min(tSz, (size_t)5);
            if (nLog > 0) {
                Gdiplus::Font& fLg = *GetSegoeFont(6.8f, false);
                for (size_t i = 0; i < nLog; ++i) {
                    const auto& ev = g_combatTimeline[tSz - nLog + i];
                    IconManager::DrawSkillIcon(g, c2X, c2Y + 1, 11, ev.skillId, ev.skillName);

                    std::wstring desc = UICommon::Utf8ToWide(ev.timeStr + " " + ev.attacker + " - " + ev.skillName);
                    if (ev.isCrit) desc += L" (Crit!)";
                    g.DrawString(desc.c_str(), -1, &fLg, Gdiplus::PointF(c2X + 15, c2Y), &bTD);

                    Gdiplus::SolidBrush db3(ev.isCrit ? UICommon::ColGoldAccent : cTM);
                    g.DrawString(UICommon::FormatNumber(ev.damage).c_str(), -1, &fLg, Gdiplus::RectF(c2X + c2W - 35, c2Y, 35, 12), &rA, &db3);
                    c2Y += 13;
                }
            } else {
                Gdiplus::Font& fn = *GetSegoeFont(7.0f, false);
                g.DrawString(L"No events recorded.", -1, &fn, Gdiplus::PointF(c2X, c2Y), &bTM);
            }

            s_resetCombatBtnRect = { (int)c2X, (int)(cY + cH - 36), (int)(c2X + c2W), (int)(cY + cH - 10) };
            {
                Gdiplus::SolidBrush rb2(cBg);
                UICommon::FillRoundRectangle(g, &rb2, (float)s_resetCombatBtnRect.left, (float)s_resetCombatBtnRect.top, c2W, 26, 5);
                Gdiplus::Pen rp2(cBr, 1);
                UICommon::DrawRoundRectangle(g, &rp2, (float)s_resetCombatBtnRect.left, (float)s_resetCombatBtnRect.top, c2W, 26, 5);
                Gdiplus::Font& frs = *GetSegoeFont(8.2f, true);
                g.DrawString(L"\u21BA Reset Combat", -1, &frs, Gdiplus::RectF((float)s_resetCombatBtnRect.left, (float)s_resetCombatBtnRect.top, c2W, 26), &cf2, &bTD);
            }

        }
        // ================= TAB 1: DPS METER & HISTÓRICO =================
        else if (s_activeTab == DrawerTab::DpsMeter) {
            std::lock_guard<std::recursive_mutex> lk(g_combatMutex);

            float y = mY;
            g.DrawString(L"DPS METER & COMBAT HISTORY", -1, &fCT, Gdiplus::PointF(mX, y), &bBl);
            y += 20;

            // Seletor de Sessões de Combate (Histórico dos últimos combates)
            float selX = mX, selH = 22.0f;
            float btnLiveW = 76.0f;
            dPl(s_combatLiveBtnRect, selX, y, btnLiveW, selH, L"\u25CF Ao Vivo", (s_selectedCombatIndex == -1));
            selX += btnLiveW + 6.0f;

            for (int i = 0; i < 5; ++i) {
                if (i < (int)g_combatHistory.size()) {
                    wchar_t hBtn[32];
                    swprintf_s(hBtn, L"Luta #%d (%hs)", i + 1, g_combatHistory[i].startTime.c_str());
                    float bw = 92.0f;
                    dPl(s_combatHistBtnRects[i], selX, y, bw, selH, hBtn, (s_selectedCombatIndex == i));
                    selX += bw + 6.0f;
                } else {
                    s_combatHistBtnRects[i] = {};
                }
            }
            y += 30;

            // Dados da sessão selecionada (ou live se -1)
            uint32_t dur = 0, dps = 0;
            uint64_t dealt = 0, recv = 0;
            std::vector<SkillDpsEntry> curSkills;
            std::vector<CombatTimelineEntry> curTimeline;

            if (s_selectedCombatIndex == -1) {
                dur = g_battleDurationSeconds.load();
                dps = g_totalDealtDps.load();
                dealt = g_totalDamageDealt.load();
                recv = g_totalDamageReceived.load();
                curSkills = g_skillBreakdown;
                curTimeline = g_combatTimeline;
            } else if (s_selectedCombatIndex >= 0 && s_selectedCombatIndex < (int)g_combatHistory.size()) {
                const auto& sess = g_combatHistory[s_selectedCombatIndex];
                dur = sess.durationSec;
                dps = sess.dps;
                dealt = sess.totalDealt;
                recv = sess.totalReceived;
                curSkills = sess.skills;
                curTimeline = sess.timeline;
            }

            // 4 Metrics Cards: Duração, DPS Causado, Dano Causado, Dano Recebido
            float mWm = std::floor((mW2 - 18) / 4.0f);
            auto dM = [&](float mx2, const wchar_t* lb, const std::wstring& vl) {
                Gdiplus::SolidBrush mb(cBg);
                UICommon::FillRoundRectangle(g, &mb, mx2, y, mWm, 44, 5);
                Gdiplus::Pen mp(cBr, 1);
                UICommon::DrawRoundRectangle(g, &mp, mx2, y, mWm, 44, 5);
                Gdiplus::Font& fl = *GetSegoeFont(6.8f, false);
                g.DrawString(lb, -1, &fl, Gdiplus::PointF(mx2 + 6, y + 4), &bTM);
                Gdiplus::Font& fv = *GetSegoeFont(11.5f, true);
                g.DrawString(vl.c_str(), -1, &fv, Gdiplus::PointF(mx2 + 6, y + 18), &bTD);
            };

            dM(mX, L"Duracao", UICommon::FormatTime(dur));
            dM(mX + (mWm + 6), L"DPS Causado", UICommon::FormatNumber(dps));
            dM(mX + (mWm + 6) * 2, L"Dano Causado", UICommon::FormatNumber(dealt));
            dM(mX + (mWm + 6) * 3, L"Dano Recebido", UICommon::FormatNumber(recv));
            y += 52;

            g.DrawString(L"DPS Over Time", -1, &fLb, Gdiplus::PointF(mX, y), &bTD);
            y += 16;
            UICommon::DrawDpsSplineChart(g, mX, y, mW2, 70, (s_selectedCombatIndex == -1) ? g_dpsHistory : std::vector<float>(), dur);
            y += 82;

            g.DrawString(L"Skill Breakdown (Dano Causado)", -1, &fLb, Gdiplus::PointF(mX, y), &bTD);
            y += 18;

            float hfW = (mW2 - 10) * 0.5f;
            uint64_t tb = dealt;
            size_t sc2 = std::min(curSkills.size(), (size_t)6);
            if (sc2 > 0) {
                for (size_t i = 0; i < sc2; ++i) {
                    float co = (i % 2 == 0) ? 0 : hfW + 10, ry = y + (i / 2) * 18.0f;
                    auto& sk = curSkills[i];
                    float p = tb > 0 ? (float)sk.totalDamage / tb * 100.0f : 0.0f;
                    IconManager::DrawSkillIcon(g, mX + co, ry + 1, 13, sk.skillId, sk.skillName);
                    Gdiplus::Font& fs = *GetSegoeFont(7.2f, false);
                    g.DrawString(UICommon::Utf8ToWide(sk.skillName).c_str(), -1, &fs, Gdiplus::PointF(mX + co + 16, ry), &bTD);
                    wchar_t pb[16];
                    swprintf_s(pb, L"%.1f%%", p);
                    g.DrawString(pb, -1, &fs, Gdiplus::RectF(mX + co + hfW - 36, ry, 36, 14), &rA, &bTM);
                }
                y += ((sc2 + 1) / 2) * 18.0f + 6;
            } else {
                Gdiplus::Font& fn = *GetSegoeFont(7.5f, false);
                g.DrawString(L"No skill data yet.", -1, &fn, Gdiplus::PointF(mX, y), &bTM);
                y += 18;
            }

            g.DrawLine(&spn, mX, y, mX + mW2, y);
            y += 6;

            g.DrawString(L"Combat Log (Ultimos Eventos)", -1, &fLb, Gdiplus::PointF(mX, y), &bTD);
            y += 16;
            size_t tSz = curTimeline.size();
            if (!tSz) {
                Gdiplus::Font& fn = *GetSegoeFont(7.5f, false);
                g.DrawString(L"No events yet.", -1, &fn, Gdiplus::PointF(mX, y), &bTM);
            } else {
                int si = (tSz > 7) ? (int)(tSz - 7) : 0;
                for (int i = si; i < (int)tSz && y < mY + mH2 - 34; ++i) {
                    auto& ev = curTimeline[i];
                    Gdiplus::Font& fl = *GetSegoeFont(6.8f, false);

                    // Badge de direção do dano
                    if (ev.isIncoming) {
                        Gdiplus::SolidBrush recBadge(Gdiplus::Color(255, 239, 68, 68));
                        g.DrawString(L"\u25C0", -1, &fl, Gdiplus::PointF(mX, y), &recBadge);
                    } else {
                        Gdiplus::SolidBrush dealBadge(cBl);
                        g.DrawString(L"\u25B6", -1, &fl, Gdiplus::PointF(mX, y), &dealBadge);
                    }

                    IconManager::DrawSkillIcon(g, mX + 13, y + 1, 11, ev.skillId, ev.skillName);

                    wchar_t ln[160];
                    swprintf_s(ln, L"%ls  %ls \u2192 %ls",
                               UICommon::Utf8ToWide(ev.timeStr).c_str(),
                               UICommon::Utf8ToWide(ev.attacker).c_str(),
                               UICommon::Utf8ToWide(ev.skillName).c_str());
                    g.DrawString(ln, -1, &fl, Gdiplus::PointF(mX + 28, y), &bTM);

                    Gdiplus::SolidBrush db2(ev.isCrit ? UICommon::ColGoldAccent : (ev.isIncoming ? Gdiplus::Color(255, 239, 68, 68) : cTD));
                    g.DrawString(UICommon::FormatNumber(ev.damage).c_str(), -1, &fl, Gdiplus::RectF(mX + mW2 - 55, y, 55, 12), &rA, &db2);
                    y += 14;
                }
            }

            s_dpsResetRect = { (int)mX, (int)(cY + cH - 36), (int)(mX + mW2), (int)(cY + cH - 10) };
            {
                Gdiplus::SolidBrush drb(cBl);
                UICommon::FillRoundRectangle(g, &drb, (float)s_dpsResetRect.left, (float)s_dpsResetRect.top, mW2, 26, 5);
                Gdiplus::Font& drf = *GetSegoeFont(8.2f, true);
                g.DrawString(L"\u21BA Reset Combat Session (Salvar & Limpar)", -1, &drf, Gdiplus::RectF((float)s_dpsResetRect.left, (float)s_dpsResetRect.top, mW2, 26), &cf2, &bWh);
            }
        }
        // ================= TAB 2: COMBO UI =================
        else if (s_activeTab == DrawerTab::ComboUi) {
            float y = mY;
            g.DrawString(L"COMBO UI SETTINGS", -1, &fCT, Gdiplus::PointF(mX, y), &bBl);
            y += 22;

            float cg = 14, c1W = std::floor(mW2 * 0.48f), c2W = mW2 - c1W - cg, c2X = mX + c1W + cg;
            g.DrawLine(&spn, mX + c1W + cg * 0.5f, y, mX + c1W + cg * 0.5f, mY + mH2);

            float c1Y = y;
            g.DrawString(L"Enable / Disable", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            c1Y = dTR(s_comboTabToggleRect, mX, c1Y, c1W, L"Combo UI Active", g_comboVisible.load());
            c1Y += 4;

            {
                float sc = g_comboScale.load(), n = std::clamp((sc - 0.55f) / 1.05f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%.0f%%", sc * 100);
                g.DrawString(L"Scale", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
                c1Y += 2;
                dSl(s_comboTabScaleSlider, mX, c1Y, c1W, n, L"", b);
                c1Y += 34;
            }
            {
                float op = g_comboOpacity.load(), n = std::clamp((op - 0.1f) / 0.9f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%.0f%%", op * 100);
                g.DrawString(L"Opacity", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
                c1Y += 2;
                dSl(s_comboTabOpacitySlider, mX, c1Y, c1W, n, L"", b);
                c1Y += 34;
            }

            g.DrawString(L"Position Preset", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 16;
            float pbW = std::floor((c1W - 9) / 4.0f), cnx = g_comboPosNormX.load(), cny = g_comboPosNormY.load();
            bool iT = cny < 0.25f, iMR = !iT && cnx > 0.65f, iC = !iT && cnx >= 0.35f && cnx <= 0.65f, iML = !iT && cnx < 0.35f;
            dPl(s_comboTabPosTop, mX, c1Y, pbW, 24, L"Top", iT);
            dPl(s_comboTabPosMidRight, mX + pbW + 3, c1Y, pbW, 24, L"Mid-R", iMR);
            dPl(s_comboTabPosCenter, mX + (pbW + 3) * 2, c1Y, pbW, 24, L"Ctr", iC);
            dPl(s_comboTabPosLeft, mX + (pbW + 3) * 3, c1Y, pbW, 24, L"Mid-L", iML);

            float c2Y = y;
            g.DrawString(L"COMBO REPORT", -1, &fCT, Gdiplus::PointF(c2X, c2Y), &bBl);
            c2Y += 18;
            {
                std::lock_guard<std::recursive_mutex> lk2(g_combatMutex);
                if (g_combatTimeline.empty()) {
                    Gdiplus::Font& fn = *GetSegoeFont(7.5f, false);
                    g.DrawString(L"No combo data yet.", -1, &fn, Gdiplus::PointF(c2X, c2Y), &bTM);
                } else {
                    g.DrawString(L"Recent Skill Chain:", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
                    c2Y += 16;
                    int si = (int)g_combatTimeline.size() > 8 ? (int)g_combatTimeline.size() - 8 : 0;
                    for (int i = si; i < (int)g_combatTimeline.size() && c2Y < mY + mH2 - 30; ++i) {
                        auto& ev = g_combatTimeline[i];
                        Gdiplus::Font& fl = *GetSegoeFont(7.0f, false);
                        IconManager::DrawSkillIcon(g, c2X, c2Y, 12, ev.skillId, ev.skillName);
                        g.DrawString(UICommon::Utf8ToWide(ev.skillName).c_str(), -1, &fl, Gdiplus::PointF(c2X + 15, c2Y), &bTD);
                        Gdiplus::SolidBrush db3(ev.isCrit ? UICommon::ColGoldAccent : cTM);
                        g.DrawString(UICommon::FormatNumber(ev.damage).c_str(), -1, &fl, Gdiplus::RectF(c2X + c2W - 45, c2Y, 45, 12), &rA, &db3);
                        c2Y += 14;
                    }
                }
            }
        }
        // ================= TAB 3: ENGINE (SHUGO CONSOLE) =================
        else if (s_activeTab == DrawerTab::Engine) {
            float y = mY;
            g.DrawString(L"ENGINE & GRAPHICS CONSOLE", -1, &fCT, Gdiplus::PointF(mX, y), &bBl);
            y += 22;

            float cg = 14, c1W = std::floor(mW2 * 0.50f), c2W = mW2 - c1W - cg, c2X = mX + c1W + cg;
            g.DrawLine(&spn, mX + c1W + cg * 0.5f, y, mX + c1W + cg * 0.5f, mY + mH2);

            float c1Y = y;
            g.DrawString(L"Camera & View", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            {
                float fv = g_cvarFov.load(), n = std::clamp((fv - 60.0f) / 60.0f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%.0f\u00B0", fv);
                dSl(s_engFovSlider, mX, c1Y, c1W, n, L"Panoramic FOV", b);
                c1Y += 34;
            }
            {
                float cm = g_cvarCamMax.load(), n = std::clamp((cm - 5.0f) / 40.0f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%.0fm", cm);
                dSl(s_engCamSlider, mX, c1Y, c1W, n, L"Camera Zoom", b);
                c1Y += 34;
            }


            s_engConsoleRect = { (int)(mX + c1W - 90), (int)c1Y, (int)(mX + c1W), (int)(c1Y + 18) };
            g.DrawString(L"Graphic Console HUD", -1, &fSb, Gdiplus::PointF(mX, c1Y + 2), &bTM);
            UICommon::DrawModernSwitch(g, (float)s_engConsoleRect.left, (float)s_engConsoleRect.top, !g_hideConsoleSection.load(), L"Visible", L"Hidden");
            c1Y += 30;

            float c2Y = y;
            g.DrawString(L"Performance", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
            c2Y += 18;
            float fW = 36, fY = c2Y;
            g.DrawString(L"FPS Cap", -1, &fSb, Gdiplus::PointF(c2X, fY + 3), &bTM);
            float fSX = c2X + c2W - (fW * 3 + 8);
            dPl(s_engFps60Rect, fSX, fY, fW, 22, L"60", (g_cvarMaxFps.load() == 60));
            dPl(s_engFps144Rect, fSX + fW + 4, fY, fW, 22, L"144", (g_cvarMaxFps.load() == 144));
            dPl(s_engFpsMaxRect, fSX + (fW + 4) * 2, fY, fW, 22, L"MAX", (g_cvarMaxFps.load() == 0));
            c2Y += 30;

            s_engTbToggleRect = { (int)(c2X + c2W - 90), (int)c2Y, (int)(c2X + c2W), (int)(c2Y + 18) };
            g.DrawString(L"Triple Buffer", -1, &fSb, Gdiplus::PointF(c2X, c2Y + 2), &bTM);
            UICommon::DrawModernSwitch(g, (float)s_engTbToggleRect.left, (float)s_engTbToggleRect.top, g_cvarTripleBuffering.load(), L"ON", L"OFF");
            c2Y += 28;

            {
                Gdiplus::SolidBrush ib2(cBg);
                UICommon::FillRoundRectangle(g, &ib2, c2X, c2Y, c2W, 52, 6);
                Gdiplus::Pen ip2(cBr, 1);
                UICommon::DrawRoundRectangle(g, &ip2, c2X, c2Y, c2W, 52, 6);
                Gdiplus::Font& fi = *GetSegoeFont(7.0f, false);
                float iy = c2Y + 6;
                g.DrawString(L"Comandos aplicados diretamente em memoria.", -1, &fi, Gdiplus::PointF(c2X + 8, iy), &bTM);
                iy += 14;
                g.DrawString(L"FOV e Cam persistem entre sessoes do jogo.", -1, &fi, Gdiplus::PointF(c2X + 8, iy), &bTM);
                iy += 14;
                g.DrawString(L"CryEngine CVar: change-detection, 0% CPU idle.", -1, &fi, Gdiplus::PointF(c2X + 8, iy), &bBl);
            }
        }
        // ================= TAB 4: ADVANCED =================
        else if (s_activeTab == DrawerTab::Advanced) {
            float y = mY;
            g.DrawString(L"ADVANCED CONFIGURATION", -1, &fCT, Gdiplus::PointF(mX, y), &bBl);
            y += 22;

            float cg = 14, c1W = std::floor(mW2 * 0.50f), c2W = mW2 - c1W - cg, c2X = mX + c1W + cg;
            g.DrawLine(&spn, mX + c1W + cg * 0.5f, y, mX + c1W + cg * 0.5f, mY + mH2);

            float c1Y = y;
            g.DrawString(L"Window Size", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 16;
            float pW = std::floor((c1W - 8) / 3.0f);
            dPl(s_advPresetDefault, mX, c1Y, pW, 28, L"Default", (s_modalW == 760 && s_modalH == 560));
            dPl(s_advPresetWide, mX + pW + 4, c1Y, pW, 28, L"Wide", (s_modalW == 880 && s_modalH == 660));
            dPl(s_advPresetCompact, mX + (pW + 4) * 2, c1Y, pW, 28, L"Compact", (s_modalW == 540 && s_modalH == 500));
            c1Y += 36;

            {
                float n = std::clamp((g_drawerOpacity.load() - 120.0f) / 135.0f, 0.0f, 1.0f);
                wchar_t b[16];
                swprintf_s(b, L"%d%%", (int)(n * 100 + 0.5f));
                dSl(s_advOpacitySlider, mX, c1Y, c1W, n, L"Window Opacity", b);
                c1Y += 34;
            }

            g.DrawString(L"Color Theme", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 16;
            float thW = std::floor((c1W - 12) / 4.0f), thH = 32;
            struct ThO { int id; const wchar_t* nm; Gdiplus::Color sw; };
            ThO ths[] = {
                { 0, L"Light", Gdiplus::Color(255, 248, 250, 252) },
                { 1, L"Dark",  Gdiplus::Color(255, 25, 28, 38) },
                { 2, L"Gray",  Gdiplus::Color(255, 88, 95, 112) },
                { 3, L"Navy",  Gdiplus::Color(255, 20, 40, 100) }
            };
            RECT* thRs[] = { &s_advThemeLight, &s_advThemeDark, &s_advThemeGray, &s_advThemeNavy };
            for (int i = 0; i < 4; ++i) {
                float tx = mX + i * (thW + 4);
                *thRs[i] = { (int)tx, (int)c1Y, (int)(tx + thW), (int)(c1Y + thH) };
                bool ac = (s_theme == ths[i].id);
                Gdiplus::SolidBrush sb2(ths[i].sw);
                UICommon::FillRoundRectangle(g, &sb2, tx, c1Y, thW, thH - 14, 4);
                if (ac) {
                    Gdiplus::Pen ap2(cBl, 2);
                    UICommon::DrawRoundRectangle(g, &ap2, tx, c1Y, thW, thH - 14, 4);
                    Gdiplus::Pen ck(cBl, 2);
                    g.DrawLine(&ck, tx + thW * 0.3f, c1Y + (thH - 14) * 0.55f, tx + thW * 0.45f, c1Y + (thH - 14) * 0.75f);
                    g.DrawLine(&ck, tx + thW * 0.45f, c1Y + (thH - 14) * 0.75f, tx + thW * 0.7f, c1Y + (thH - 14) * 0.30f);
                } else {
                    Gdiplus::Pen np(cBr, 1);
                    UICommon::DrawRoundRectangle(g, &np, tx, c1Y, thW, thH - 14, 4);
                }
                Gdiplus::Font& tf = *GetSegoeFont(6.8f, ac);
                Gdiplus::SolidBrush tt(cTD);
                g.DrawString(ths[i].nm, -1, &tf, Gdiplus::RectF(tx, c1Y + thH - 14, thW, 13), &cf2, &tt);
            }
            c1Y += thH + 8;

            // FIXAR JANELA NO JOGO (PINNED - Requisito 6)
            g.DrawString(L"Janela Fixa no Jogo", -1, &fLb, Gdiplus::PointF(mX, c1Y), &bTD);
            c1Y += 18;
            c1Y = dTR(s_advPinnedToggle, mX, c1Y, c1W, L"PINNED Mode", g_drawerPinned.load());
            {
                Gdiplus::Font& fsSub = *GetSegoeFont(6.8f, false);
                g.DrawString(L"Se ativo: trava arrasto dentro do jogo e oculta ao perder foco.", -1, &fsSub, Gdiplus::PointF(mX, c1Y - 4), &bTM);
                c1Y += 14;
            }

            // Coluna Direita: Feature Flags
            float c2Y = y;
            g.DrawString(L"Feature Flags", -1, &fLb, Gdiplus::PointF(c2X, c2Y), &bTD);
            c2Y += 18;
            auto dFT = [&](RECT& r2, float sx, float sy, const wchar_t* lb, bool ac) -> float {
                r2 = { (int)(sx + c2W - 90), (int)sy, (int)(sx + c2W), (int)(sy + 18) };
                g.DrawString(lb, -1, &fSb, Gdiplus::PointF(sx, sy + 2), &bTM);
                UICommon::DrawModernSwitch(g, (float)r2.left, (float)r2.top, ac, L"ON", L"OFF");
                return sy + 26;
            };

            c2Y = dFT(s_advCompactToggle, c2X, c2Y, L"Compact View", g_compactView.load());
            c2Y = dFT(s_advConsoleToggle, c2X, c2Y, L"Graphic HUD", !g_hideConsoleSection.load());
            c2Y = dFT(s_advFovToggle, c2X, c2Y, L"FOV Control", g_featFov.load());
            c2Y = dFT(s_advCamToggle, c2X, c2Y, L"Cam Max", g_featCamMax.load());
            c2Y = dFT(s_advFpsToggle, c2X, c2Y, L"FPS Unlock", g_featFpsUnlock.load());
            (void)c2Y;
        }
    }

    POINT pts = { 0, 0 };
    SIZE szW = { s_modalW, s_modalH };
    BLENDFUNCTION bl = {};
    bl.BlendOp = AC_SRC_OVER;
    bl.SourceConstantAlpha = (BYTE)std::clamp(g_drawerOpacity.load(), 120, 255);
    bl.AlphaFormat = AC_SRC_ALPHA;

    UpdateLayeredWindow(hwnd, sc, nullptr, &szW, mc, &pts, 0, &bl, ULW_ALPHA);
    ReleaseDC(nullptr, sc);
}

LRESULT CALLBACK DrawerModalUI::WndProc(HWND hwnd, UINT uMsg, WPARAM wParam, LPARAM lParam) {
    switch (uMsg) {
    case WM_TIMER:
        Repaint();
        return 0;

    case WM_LBUTTONDOWN: {
        int mx = LOWORD(lParam), my = HIWORD(lParam);

        if (mx >= s_closeBtnRect.left && mx <= s_closeBtnRect.right && my >= s_closeBtnRect.top && my <= s_closeBtnRect.bottom) {
            Close();
            return 0;
        }
        if (mx >= s_minimizeBtnRect.left && mx <= s_minimizeBtnRect.right && my >= s_minimizeBtnRect.top && my <= s_minimizeBtnRect.bottom) {
            Close();
            return 0;
        }
        if (mx >= s_helpBtnRect.left && mx <= s_helpBtnRect.right && my >= s_helpBtnRect.top && my <= s_helpBtnRect.bottom) {
            s_activeTab = (s_activeTab == DrawerTab::Advanced) ? DrawerTab::Display : DrawerTab::Advanced;
            UpdateDrawerTimer();
            Repaint();
            return 0;
        }

        // Navegação de Tabs
        auto chT = [&](RECT& r, DrawerTab t) {
            if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                s_activeTab = t;
                UpdateDrawerTimer();
                Repaint();
                return true;
            }
            return false;
        };

        if (chT(s_tabDisplayRect, DrawerTab::Display)) return 0;
        if (chT(s_tabDpsMeterRect, DrawerTab::DpsMeter)) return 0;
        if (chT(s_tabComboRect, DrawerTab::ComboUi)) return 0;
        if (chT(s_tabEngineRect, DrawerTab::Engine)) return 0;
        if (chT(s_tabAdvancedRect, DrawerTab::Advanced)) return 0;

        if (mx >= s_resetDefaultsRect.left && mx <= s_resetDefaultsRect.right && my >= s_resetDefaultsRect.top && my <= s_resetDefaultsRect.bottom) {
            ResizeDrawer(760, 560);
            g_drawerOpacity = 255;
            g_compactView = false;
            g_hideConsoleSection = false;
            g_drawerPinned = true;
            g_comboVisible = true;
            g_comboScale = 1.0f;
            g_comboOpacity = 1.0f;
            g_comboPosNormX = 0.80f;
            g_comboPosNormY = 0.50f;
            s_theme = 0;
            s_selectedCombatIndex = -1;
            CVarManager::SetFov(75);
            CVarManager::SetCameraMax(25);
            CVarManager::SetMaxFps(144);
            CVarManager::SetTripleBuffering(true);
            ResetCombatSession();
            BrConfig::Save();
            Repaint();
            return 0;
        }

        // Tab: Display
        if (s_activeTab == DrawerTab::Display) {
            auto cPr = [&](RECT& r, int w, int h) {
                if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                    ResizeDrawer(w, h);
                    return true;
                }
                return false;
            };
            if (cPr(s_presetDefaultRect, 760, 560)) return 0;
            if (cPr(s_presetWideRect, 880, 660)) return 0;
            if (cPr(s_presetCompactRect, 540, 500)) return 0;

            if (mx >= s_opacitySliderRect.left && mx <= s_opacitySliderRect.right && my >= s_opacitySliderRect.top - 6 && my <= s_opacitySliderRect.bottom + 6) {
                s_draggingOpacity = true;
                SetCapture(hwnd);
                return 0;
            }
            if (mx >= s_compactToggleRect.left && mx <= s_compactToggleRect.right && my >= s_compactToggleRect.top && my <= s_compactToggleRect.bottom) {
                g_compactView = !g_compactView.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (mx >= s_consoleToggleRect.left && mx <= s_consoleToggleRect.right && my >= s_consoleToggleRect.top && my <= s_consoleToggleRect.bottom) {
                g_hideConsoleSection = !g_hideConsoleSection.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (mx >= s_comboToggleRect.left && mx <= s_comboToggleRect.right && my >= s_comboToggleRect.top && my <= s_comboToggleRect.bottom) {
                bool nv = !g_comboVisible.load();
                g_comboVisible = nv;
                g_ComboUI.RequestLayoutRefresh();
                WebSocketClient::SendTextMessage(std::string("SET_COMBO_VISIBILITY:") + (nv ? "1" : "0"));
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (mx >= s_comboScaleSliderRect.left && mx <= s_comboScaleSliderRect.right && my >= s_comboScaleSliderRect.top - 6 && my <= s_comboScaleSliderRect.bottom + 6) {
                s_draggingComboScale = true;
                SetCapture(hwnd);
                return 0;
            }

            auto apP = [&](float tx, float ty) {
                SetComboOverlayLayout(tx, ty, g_comboScale.load());
                g_comboPosNormX = tx;
                g_comboPosNormY = ty;
                g_ComboUI.RequestLayoutRefresh();
                BrConfig::Save();
                Repaint();
            };
            if (mx >= s_comboPosTopRect.left && mx <= s_comboPosTopRect.right && my >= s_comboPosTopRect.top && my <= s_comboPosTopRect.bottom) { apP(0.5f, 0.12f); return 0; }
            if (mx >= s_comboPosMidRightRect.left && mx <= s_comboPosMidRightRect.right && my >= s_comboPosMidRightRect.top && my <= s_comboPosMidRightRect.bottom) { apP(0.8f, 0.5f); return 0; }
            if (mx >= s_comboPosCenterRect.left && mx <= s_comboPosCenterRect.right && my >= s_comboPosCenterRect.top && my <= s_comboPosCenterRect.bottom) { apP(0.5f, 0.5f); return 0; }
            if (mx >= s_comboPosLeftRect.left && mx <= s_comboPosLeftRect.right && my >= s_comboPosLeftRect.top && my <= s_comboPosLeftRect.bottom) { apP(0.2f, 0.5f); return 0; }

            if (mx >= s_saveSettingsBtnRect.left && mx <= s_saveSettingsBtnRect.right && my >= s_saveSettingsBtnRect.top && my <= s_saveSettingsBtnRect.bottom) {
                Close();
                return 0;
            }
            if (mx >= s_resetCombatBtnRect.left && mx <= s_resetCombatBtnRect.right && my >= s_resetCombatBtnRect.top && my <= s_resetCombatBtnRect.bottom) {
                ResetCombatSession();
                s_selectedCombatIndex = -1;
                Repaint();
                return 0;
            }
            if (mx >= s_targetCardCloseRect.left && mx <= s_targetCardCloseRect.right && my >= s_targetCardCloseRect.top && my <= s_targetCardCloseRect.bottom) {
                std::lock_guard<std::recursive_mutex> lk(g_combatMutex);
                g_currentTarget.hasTarget = false;
                Repaint();
                return 0;
            }
        }
        // Tab: DPS Meter
        else if (s_activeTab == DrawerTab::DpsMeter) {
            // Seletor de Sessão Ao Vivo
            if (mx >= s_combatLiveBtnRect.left && mx <= s_combatLiveBtnRect.right && my >= s_combatLiveBtnRect.top && my <= s_combatLiveBtnRect.bottom) {
                s_selectedCombatIndex = -1;
                Repaint();
                return 0;
            }
            // Seletor de Sessão Histórica
            for (int i = 0; i < 5; ++i) {
                if (s_combatHistBtnRects[i].right > s_combatHistBtnRects[i].left &&
                    mx >= s_combatHistBtnRects[i].left && mx <= s_combatHistBtnRects[i].right &&
                    my >= s_combatHistBtnRects[i].top && my <= s_combatHistBtnRects[i].bottom) {
                    s_selectedCombatIndex = i;
                    Repaint();
                    return 0;
                }
            }
            if (mx >= s_dpsResetRect.left && mx <= s_dpsResetRect.right && my >= s_dpsResetRect.top && my <= s_dpsResetRect.bottom) {
                ResetCombatSession();
                s_selectedCombatIndex = -1;
                Repaint();
                return 0;
            }
        }
        // Tab: Combo UI
        else if (s_activeTab == DrawerTab::ComboUi) {
            if (mx >= s_comboTabToggleRect.left && mx <= s_comboTabToggleRect.right && my >= s_comboTabToggleRect.top && my <= s_comboTabToggleRect.bottom) {
                bool nv = !g_comboVisible.load();
                g_comboVisible = nv;
                g_ComboUI.RequestLayoutRefresh();
                WebSocketClient::SendTextMessage(std::string("SET_COMBO_VISIBILITY:") + (nv ? "1" : "0"));
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (mx >= s_comboTabScaleSlider.left && mx <= s_comboTabScaleSlider.right && my >= s_comboTabScaleSlider.top - 6 && my <= s_comboTabScaleSlider.bottom + 6) {
                s_draggingComboScale = true;
                SetCapture(hwnd);
                return 0;
            }
            if (mx >= s_comboTabOpacitySlider.left && mx <= s_comboTabOpacitySlider.right && my >= s_comboTabOpacitySlider.top - 6 && my <= s_comboTabOpacitySlider.bottom + 6) {
                s_draggingComboOpacity = true;
                SetCapture(hwnd);
                return 0;
            }
            auto apP = [&](float tx, float ty) {
                SetComboOverlayLayout(tx, ty, g_comboScale.load());
                g_comboPosNormX = tx;
                g_comboPosNormY = ty;
                g_ComboUI.RequestLayoutRefresh();
                BrConfig::Save();
                Repaint();
            };
            if (mx >= s_comboTabPosTop.left && mx <= s_comboTabPosTop.right && my >= s_comboTabPosTop.top && my <= s_comboTabPosTop.bottom) { apP(0.5f, 0.12f); return 0; }
            if (mx >= s_comboTabPosMidRight.left && mx <= s_comboTabPosMidRight.right && my >= s_comboTabPosMidRight.top && my <= s_comboTabPosMidRight.bottom) { apP(0.8f, 0.5f); return 0; }
            if (mx >= s_comboTabPosCenter.left && mx <= s_comboTabPosCenter.right && my >= s_comboTabPosCenter.top && my <= s_comboTabPosCenter.bottom) { apP(0.5f, 0.5f); return 0; }
            if (mx >= s_comboTabPosLeft.left && mx <= s_comboTabPosLeft.right && my >= s_comboTabPosLeft.top && my <= s_comboTabPosLeft.bottom) { apP(0.2f, 0.5f); return 0; }
        }
        // Tab: Engine
        else if (s_activeTab == DrawerTab::Engine) {
            if (mx >= s_engFovSlider.left && mx <= s_engFovSlider.right && my >= s_engFovSlider.top - 6 && my <= s_engFovSlider.bottom + 6) {
                s_draggingFov = true;
                SetCapture(hwnd);
                return 0;
            }
            if (mx >= s_engCamSlider.left && mx <= s_engCamSlider.right && my >= s_engCamSlider.top - 6 && my <= s_engCamSlider.bottom + 6) {
                s_draggingCam = true;
                SetCapture(hwnd);
                return 0;
            }
            auto cFps = [&](RECT& r, int fps) {
                if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                    CVarManager::SetMaxFps(fps);
                    BrConfig::Save();
                    Repaint();
                    return true;
                }
                return false;
            };
            if (cFps(s_engFps60Rect, 60)) return 0;
            if (cFps(s_engFps144Rect, 144)) return 0;
            if (cFps(s_engFpsMaxRect, 0)) return 0;

            if (mx >= s_engTbToggleRect.left && mx <= s_engTbToggleRect.right && my >= s_engTbToggleRect.top && my <= s_engTbToggleRect.bottom) {
                CVarManager::SetTripleBuffering(!g_cvarTripleBuffering.load());
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (mx >= s_engConsoleRect.left && mx <= s_engConsoleRect.right && my >= s_engConsoleRect.top && my <= s_engConsoleRect.bottom) {
                g_hideConsoleSection = !g_hideConsoleSection.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }
        }
        // Tab: Advanced
        else if (s_activeTab == DrawerTab::Advanced) {
            auto cPr = [&](RECT& r, int w, int h) {
                if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                    ResizeDrawer(w, h);
                    return true;
                }
                return false;
            };
            if (cPr(s_advPresetDefault, 760, 560)) return 0;
            if (cPr(s_advPresetWide, 880, 660)) return 0;
            if (cPr(s_advPresetCompact, 540, 500)) return 0;

            if (mx >= s_advOpacitySlider.left && mx <= s_advOpacitySlider.right && my >= s_advOpacitySlider.top - 6 && my <= s_advOpacitySlider.bottom + 6) {
                s_draggingOpacity = true;
                SetCapture(hwnd);
                return 0;
            }

            auto cTh = [&](RECT& r, int id) {
                if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                    s_theme = id;
                    BrConfig::Save();
                    Repaint();
                    return true;
                }
                return false;
            };
            if (cTh(s_advThemeLight, 0)) return 0;
            if (cTh(s_advThemeDark, 1)) return 0;
            if (cTh(s_advThemeGray, 2)) return 0;
            if (cTh(s_advThemeNavy, 3)) return 0;

            if (mx >= s_advPinnedToggle.left && mx <= s_advPinnedToggle.right && my >= s_advPinnedToggle.top && my <= s_advPinnedToggle.bottom) {
                g_drawerPinned = !g_drawerPinned.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }

            auto cFt = [&](RECT& r, std::atomic<bool>& f) {
                if (mx >= r.left && mx <= r.right && my >= r.top && my <= r.bottom) {
                    f = !f.load();
                    BrConfig::Save();
                    Repaint();
                    return true;
                }
                return false;
            };
            if (cFt(s_advCompactToggle, g_compactView)) return 0;
            if (mx >= s_advConsoleToggle.left && mx <= s_advConsoleToggle.right && my >= s_advConsoleToggle.top && my <= s_advConsoleToggle.bottom) {
                g_hideConsoleSection = !g_hideConsoleSection.load();
                BrConfig::Save();
                Repaint();
                return 0;
            }
            if (cFt(s_advFovToggle, g_featFov)) return 0;
            if (cFt(s_advCamToggle, g_featCamMax)) return 0;
            if (cFt(s_advFpsToggle, g_featFpsUnlock)) return 0;
        }

        // Arrastar Janela através do Header
        if (mx >= s_headerDragRect.left && mx <= s_headerDragRect.right && my >= s_headerDragRect.top && my <= s_headerDragRect.bottom) {
            s_isDraggingWindow = true;
            GetCursorPos(&s_dragStartCursor);
            RECT wr = {};
            GetWindowRect(hwnd, &wr);
            s_dragStartPos.x = wr.left;
            s_dragStartPos.y = wr.top;
            SetCapture(hwnd);
        }
        return 0;
    }

    case WM_MOUSEMOVE: {
        int mx = LOWORD(lParam), my = HIWORD(lParam);
        s_mousePos.x = mx;
        s_mousePos.y = my;

        if (s_isDraggingWindow) {
            POINT c = {};
            GetCursorPos(&c);
            int nx = s_dragStartPos.x + (c.x - s_dragStartCursor.x);
            int ny = s_dragStartPos.y + (c.y - s_dragStartCursor.y);

            // Requisito 6: Bloqueio do arrasto dentro dos limites da tela do jogo se PINNED
            if (g_drawerPinned.load()) {
                HWND hG = g_gameHwnd.load();
                if (hG && IsWindow(hG)) {
                    RECT gr = {};
                    GetWindowRect(hG, &gr);
                    int minX = gr.left;
                    int maxX = gr.right - s_modalW;
                    int minY = gr.top;
                    int maxY = gr.bottom - s_modalH;
                    if (maxX >= minX) nx = std::clamp(nx, minX, maxX);
                    if (maxY >= minY) ny = std::clamp(ny, minY, maxY);
                }
            }

            g_drawerPosX = nx;
            g_drawerPosY = ny;
            SetWindowPos(hwnd, HWND_TOPMOST, nx, ny, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE);
            return 0;
        }

        if (s_draggingOpacity) {
            RECT& r = (s_activeTab == DrawerTab::Advanced) ? s_advOpacitySlider : s_opacitySliderRect;
            if (r.right > r.left) {
                float p = std::clamp((float)(mx - r.left) / (float)(r.right - r.left), 0.0f, 1.0f);
                g_drawerOpacity = (int)(120 + p * 135);
                Repaint();
            }
            return 0;
        }

        if (s_draggingComboScale) {
            RECT& r = (s_activeTab == DrawerTab::ComboUi) ? s_comboTabScaleSlider : s_comboScaleSliderRect;
            if (r.right > r.left) {
                float p = std::clamp((float)(mx - r.left) / (float)(r.right - r.left), 0.0f, 1.0f);
                float sc = 0.55f + p * 1.05f;
                SetComboOverlayLayout(g_comboPosNormX.load(), g_comboPosNormY.load(), sc);
                g_comboScale = sc;
                g_ComboUI.RequestLayoutRefresh();
                Repaint();
            }
            return 0;
        }

        if (s_draggingComboOpacity && s_comboTabOpacitySlider.right > s_comboTabOpacitySlider.left) {
            float p = std::clamp((float)(mx - s_comboTabOpacitySlider.left) / (float)(s_comboTabOpacitySlider.right - s_comboTabOpacitySlider.left), 0.0f, 1.0f);
            g_comboOpacity = 0.1f + p * 0.9f;
            Repaint();
            return 0;
        }

        if (s_draggingFov && s_engFovSlider.right > s_engFovSlider.left) {
            float p = std::clamp((float)(mx - s_engFovSlider.left) / (float)(s_engFovSlider.right - s_engFovSlider.left), 0.0f, 1.0f);
            CVarManager::SetFov(60.0f + p * 60.0f);
            Repaint();
            return 0;
        }

        if (s_draggingCam && s_engCamSlider.right > s_engCamSlider.left) {
            float p = std::clamp((float)(mx - s_engCamSlider.left) / (float)(s_engCamSlider.right - s_engCamSlider.left), 0.0f, 1.0f);
            CVarManager::SetCameraMax(5.0f + p * 40.0f);
            Repaint();
            return 0;
        }

        // Se mouse estiver sobre o card de target na aba Display, repintar para exibir tooltip
        if (s_activeTab == DrawerTab::Display && s_targetCardRect.right > s_targetCardRect.left) {
            if (PtInRect(&s_targetCardRect, s_mousePos)) {
                Repaint();
            }
        }
        return 0;
    }

    case WM_LBUTTONUP:
        if (s_isDraggingWindow) {
            s_isDraggingWindow = false;
            ReleaseCapture();
            BrConfig::Save();
            return 0;
        }
        if (s_draggingOpacity || s_draggingComboScale || s_draggingComboOpacity || s_draggingFov || s_draggingCam) {
            s_draggingOpacity = s_draggingComboScale = s_draggingComboOpacity = s_draggingFov = s_draggingCam = false;
            ReleaseCapture();
            BrConfig::Save();
        }
        return 0;

    case WM_DESTROY:
        return 0;

    default:
        return DefWindowProcW(hwnd, uMsg, wParam, lParam);
    }
}

} // namespace BrService
