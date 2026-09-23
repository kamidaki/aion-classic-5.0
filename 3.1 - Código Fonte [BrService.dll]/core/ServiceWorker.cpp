#include "ServiceWorker.h"
#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../cvar/CVarManager.h"
#include "../combo/ComboUI.h"
#include <atomic>
#include <commctrl.h>

#pragma comment(lib, "comctl32.lib")

namespace BrService {

static HANDLE s_hWatchdog = nullptr;
static std::atomic<bool> s_running(false);
static constexpr UINT_PTR GAME_SUBCLASS_ID = 0x2026;
static constexpr int HOTKEY_ID_CONSOLE = 0x53463; // Shift + F3
static bool s_subclassInstalled = false;

struct WindowSearchContext {
    DWORD targetPid;
    HWND foundHwnd;
};

static void SyncPositionsDirectly(HWND hGame) {
    if (!hGame || !IsWindow(hGame)) return;
    if (IsIconic(hGame)) return;

    RECT cr;
    GetClientRect(hGame, &cr);
    POINT pt = { 0, 0 };
    ClientToScreen(hGame, &pt);

    int gx = pt.x;
    int gy = pt.y;
    int gw = cr.right - cr.left;
    int gh = cr.bottom - cr.top;

    PingHudUI::UpdatePosition(gx, gy, gw, gh);
    DrawerModalUI::UpdatePosition(gx, gy, gw, gh);
}

static LRESULT CALLBACK GameWindowSubclassProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam,
                                              UINT_PTR uIdSubclass, DWORD_PTR /*dwRefData*/) {
    switch (uMsg) {
    case WM_HOTKEY:
        if (wParam == HOTKEY_ID_CONSOLE) {
            DrawerModalUI::Toggle();
            return 0;
        }
        break;

    case WM_KEYDOWN:
    case WM_SYSKEYDOWN: {
        bool shiftDown = (GetKeyState(VK_SHIFT) & 0x8000) != 0;
        if (wParam == VK_F3 && shiftDown) {
            DrawerModalUI::Toggle();
            return 0;
        }
        break;
    }

    case WM_WINDOWPOSCHANGED:
    case WM_MOVE:
    case WM_SIZE:
        SyncPositionsDirectly(hWnd);
        if (g_wakeEvent) SetEvent(g_wakeEvent);
        break;

    case WM_ACTIVATE:
        if (LOWORD(wParam) == WA_INACTIVE) {
            g_isGameActive = false;
            PingHudUI::Hide();
            if (g_drawerPinned.load()) DrawerModalUI::Hide(); // UNPINNED: manter visível
            if (g_wakeEvent) SetEvent(g_wakeEvent);
        } else {
            HWND fg = GetForegroundWindow();
            bool isMin = IsIconic(hWnd);
            bool isFore = (fg == hWnd || fg == g_hPingHudWnd || fg == g_hDrawerModalWnd || fg == g_overlayHwnd || IsForegroundInGameProcess(hWnd, fg));
            g_isGameActive = (!isMin && isFore);
            if (g_isGameActive.load()) {
                if (g_isInWorld.load() && !g_isLoadingScreen.load()) {
                    PingHudUI::Show();
                    DrawerModalUI::RestoreIfOpen();
                    SyncPositionsDirectly(hWnd);
                }
            } else {
                PingHudUI::Hide();
                if (g_drawerPinned.load()) DrawerModalUI::Hide();
            }
            if (g_wakeEvent) SetEvent(g_wakeEvent);
        }
        break;

    case WM_KILLFOCUS:
        g_isGameActive = false;
        PingHudUI::Hide();
        if (g_drawerPinned.load()) DrawerModalUI::Hide();
        if (g_wakeEvent) SetEvent(g_wakeEvent);
        break;

    case WM_SETFOCUS: {
        HWND fg = GetForegroundWindow();
        bool isMin = IsIconic(hWnd);
        bool isFore = (fg == hWnd || fg == g_hPingHudWnd || fg == g_hDrawerModalWnd || fg == g_overlayHwnd || IsForegroundInGameProcess(hWnd, fg));
        g_isGameActive = (!isMin && isFore);
        if (g_isGameActive.load()) {
            if (g_isInWorld.load() && !g_isLoadingScreen.load()) {
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
                SyncPositionsDirectly(hWnd);
            }
        } else {
            PingHudUI::Hide();
            if (g_drawerPinned.load()) DrawerModalUI::Hide();
        }
        if (g_wakeEvent) SetEvent(g_wakeEvent);
        break;
    }

    case WM_DESTROY:
        UnregisterHotKey(hWnd, HOTKEY_ID_CONSOLE);
        RemoveWindowSubclass(hWnd, GameWindowSubclassProc, uIdSubclass);
        s_subclassInstalled = false;
        break;
    }
    return DefSubclassProc(hWnd, uMsg, wParam, lParam);
}

static BOOL CALLBACK EnumWindowsCallback(HWND hwnd, LPARAM lParam) {
    auto* ctx = reinterpret_cast<WindowSearchContext*>(lParam);
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (pid == ctx->targetPid) {
        // Skip our own overlay and drawer windows
        if (hwnd == g_hPingHudWnd || hwnd == g_hDrawerModalWnd) return TRUE;

        wchar_t className[128] = { 0 };
        GetClassNameW(hwnd, className, 128);
        if (wcsstr(className, L"BrService") != nullptr) return TRUE;

        wchar_t title[256] = { 0 };
        GetWindowTextW(hwnd, title, 256);
        if (wcscmp(title, L"Aion Ping HUD") == 0 || wcsstr(title, L"Analisador") != nullptr || wcsstr(title, L"Painel Academy") != nullptr) return TRUE;

        // Aion Classic game window class or title
        if (wcscmp(className, L"AION Client") == 0) {
            ctx->foundHwnd = hwnd;
            return FALSE; // Exact class match
        }
        if (wcsstr(title, L"AION Client") != nullptr) {
            ctx->foundHwnd = hwnd;
            return FALSE;
        }

        // Secondary match: visible window with real game client dimensions
        if (!ctx->foundHwnd && IsWindowVisible(hwnd)) {
            RECT rc;
            GetClientRect(hwnd, &rc);
            if ((rc.right - rc.left) >= 300 && (rc.bottom - rc.top) >= 300) {
                ctx->foundHwnd = hwnd;
            }
        }
    }
    return TRUE;
}

HWND ServiceWorker::FindGameWindow() {
    WindowSearchContext ctx = { GetCurrentProcessId(), nullptr };
    EnumWindows(EnumWindowsCallback, reinterpret_cast<LPARAM>(&ctx));
    return ctx.foundHwnd;
}

bool ServiceWorker::CheckLoadingScreen(HWND hwnd) {
    if (!hwnd) return false;
    wchar_t title[256] = { 0 };
    GetWindowTextW(hwnd, title, 256);
    if (wcsstr(title, L"Loading") != nullptr || wcsstr(title, L"carregando") != nullptr) {
        return true;
    }
    return false;
}

bool ServiceWorker::Start() {
    if (s_running.load()) return true;
    s_running = true;
    s_hWatchdog = CreateThread(nullptr, 0, WatchdogThread, nullptr, 0, nullptr);
    return s_hWatchdog != nullptr;
}

void ServiceWorker::Stop() {
    s_running = false;
    HWND hGame = g_gameHwnd.load();
    if (s_subclassInstalled && hGame && IsWindow(hGame)) {
        UnregisterHotKey(hGame, HOTKEY_ID_CONSOLE);
        RemoveWindowSubclass(hGame, GameWindowSubclassProc, GAME_SUBCLASS_ID);
        s_subclassInstalled = false;
    }
    if (s_hWatchdog) {
        WaitForSingleObject(s_hWatchdog, 1500);
        CloseHandle(s_hWatchdog);
        s_hWatchdog = nullptr;
    }
}

DWORD WINAPI ServiceWorker::WatchdogThread(LPVOID /*param*/) {
    LogInfo("ServiceWorker iniciado. Monitorando ciclo de vida do Aion...");

    HWND hGame = nullptr;
    bool lastLoading = false;

    while (s_running.load()) {
        if (!hGame || !IsWindow(hGame)) {
            hGame = FindGameWindow();
            if (hGame) {
                g_gameHwnd = hGame;
                ::g_gameHwnd = hGame;
                LogInfo("Janela do Aion localizada: HWND=%p", hGame);

                // Install high-performance zero-delay subclass for instant window synchronization
                if (!s_subclassInstalled) {
                    if (SetWindowSubclass(hGame, GameWindowSubclassProc, GAME_SUBCLASS_ID, 0)) {
                        s_subclassInstalled = true;
                        RegisterHotKey(hGame, HOTKEY_ID_CONSOLE, MOD_SHIFT, VK_F3);
                        LogInfo("Subclasse de alta performance e Hotkey (Shift+F3) vinculadas a janela do jogo.");
                    }
                }
                SyncPositionsDirectly(hGame);
            } else {
                Sleep(250);
                continue;
            }
        }

        // 1. Check window visibility & active state & foreground focus
        bool isMinimized = IsIconic(hGame);
        bool isVisible = IsWindowVisible(hGame);
        HWND fg = GetForegroundWindow();
        bool isForeground = (fg == hGame || fg == g_hPingHudWnd || fg == g_hDrawerModalWnd || fg == g_overlayHwnd || IsForegroundInGameProcess(hGame, fg));
        bool active = (isVisible && !isMinimized && isForeground);
        g_isGameActive = active;

        // 2. Fallback check for loading screen title
        bool isLoading = CheckLoadingScreen(hGame);
        if (isLoading != lastLoading) {
            lastLoading = isLoading;
            if (isLoading) {
                PingHudUI::Hide();
                DrawerModalUI::Hide();
            } else if (g_isInWorld.load() && active) {
                CVarManager::ResyncOnMapChange();
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
            }
        }

        // 3. Periodic synchronization checkpoint
        if (active && g_isInWorld.load() && !isLoading) {
            static int syncCounter = 0;
            if (++syncCounter >= 10) { // ~300ms sync check
                syncCounter = 0;
                SyncPositionsDirectly(hGame);
            }
            PingHudUI::Show();
            DrawerModalUI::RestoreIfOpen();

            // 4. Reliable Direct Hotkey (Shift + F3) with game in focus
            static bool s_lastShiftF3 = false;
            bool isF3 = (GetAsyncKeyState(VK_F3) & 0x8000) != 0;
            bool isShift = (GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0;
            bool shiftF3 = isF3 && isShift;
            if (shiftF3 && !s_lastShiftF3) {
                DrawerModalUI::Toggle();
            }
            s_lastShiftF3 = shiftF3;
        } else {
            PingHudUI::Hide();
            if (g_drawerPinned.load()) DrawerModalUI::Hide();
        }

        Sleep(30); // ~33Hz responsive input & window loop (0% CPU)
    }

    LogInfo("ServiceWorker finalizado.");
    return 0;
}

} // namespace BrService
