#include "ServiceWorker.h"
#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../combo/ComboUI.h"
#include <atomic>

namespace BrService {

static HANDLE s_hWatchdog = nullptr;
static std::atomic<bool> s_running(false);

// T14: Hotkey ID for Shift+F3 registered via RegisterHotKey
static const int kHotkeyShiftF3 = 0xB001;

struct WindowSearchContext {
    DWORD targetPid;
    HWND foundHwnd;
};

static BOOL CALLBACK EnumWindowsCallback(HWND hwnd, LPARAM lParam) {
    auto* ctx = reinterpret_cast<WindowSearchContext*>(lParam);
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (pid == ctx->targetPid) {
        HWND hPing = g_hPingHudWnd.load();
        HWND hDrw  = g_hDrawerModalWnd.load();
        HWND hCombo = g_hComboWnd.load();
        if (hwnd == hPing || hwnd == hDrw || hwnd == hCombo) return TRUE;

        wchar_t className[128] = { 0 };
        GetClassNameW(hwnd, className, 128);
        if (wcsstr(className, L"BrService") != nullptr ||
            wcscmp(className, L"AionComboUI") == 0 ||
            wcsstr(className, L"ComboUI") != nullptr ||
            wcsstr(className, L"Chrome_WidgetWin") != nullptr ||
            wcsstr(className, L"Intermediate D3D") != nullptr) {
            return TRUE;
        }

        // Aion Classic game window class (CrySystem / CryInput official class)
        if (wcscmp(className, L"AIONClientWndClass1.0") == 0 || wcscmp(className, L"AION Client") == 0) {
            RECT rc;
            if (GetClientRect(hwnd, &rc) && (rc.right - rc.left) >= 300 && (rc.bottom - rc.top) >= 300) {
                ctx->foundHwnd = hwnd;
                return FALSE;
            }
        }
    }
    return TRUE;
}

HWND ServiceWorker::FindGameWindow() {
    // 1. Fast direct lookup
    HWND fastHwnd = FindWindowW(L"AIONClientWndClass1.0", nullptr);
    if (!fastHwnd) fastHwnd = FindWindowW(L"AION Client", nullptr);
    if (fastHwnd) {
        DWORD pid = 0;
        GetWindowThreadProcessId(fastHwnd, &pid);
        if (pid == GetCurrentProcessId()) {
            return fastHwnd;
        }
    }

    // 2. Fallback process-wide window enumeration (no cross-thread message sending)
    WindowSearchContext ctx = { GetCurrentProcessId(), nullptr };
    EnumWindows(EnumWindowsCallback, reinterpret_cast<LPARAM>(&ctx));
    return ctx.foundHwnd;
}

bool ServiceWorker::CheckLoadingScreen(HWND /*hwnd*/) {
    // NEVER send synchronous WM_GETTEXT across threads to the game window.
    // In Aion, loading state is tracked via WebSocket PLAYER_STATE.isLoading.
    return g_isLoadingScreen.load();
}

static void SyncPositionsSafely(HWND hGame, bool force = false) {
    if (!hGame || !IsWindow(hGame) || IsIconic(hGame)) return;

    RECT cr = { 0 };
    if (!GetClientRect(hGame, &cr)) return;
    POINT pt = { cr.left, cr.top };
    if (!ClientToScreen(hGame, &pt)) return;

    int gx = pt.x;
    int gy = pt.y;
    int gw = cr.right - cr.left;
    int gh = cr.bottom - cr.top;

    if (gw <= 100 || gh <= 100) return;

    static int s_lastGx = -9999, s_lastGy = -9999, s_lastGw = -9999, s_lastGh = -9999;
    if (force || gx != s_lastGx || gy != s_lastGy || gw != s_lastGw || gh != s_lastGh) {
        s_lastGx = gx; s_lastGy = gy; s_lastGw = gw; s_lastGh = gh;
        PingHudUI::UpdatePosition(gx, gy, gw, gh);
        DrawerModalUI::UpdatePosition(gx, gy, gw, gh);
    }
}

// T04/T05: Safe cross-thread UI helpers using PostMessage (non-blocking, no deadlock risk).
// These replace direct Show/Hide/Repaint calls made from non-UI threads.
static void PostShowPingHud() {
    HWND h = g_hPingHudWnd.load();
    if (h) PostMessage(h, WM_BRSERVICE_SHOW, 0, 0);
}
static void PostHidePingHud() {
    HWND h = g_hPingHudWnd.load();
    if (h) PostMessage(h, WM_BRSERVICE_HIDE, 0, 0);
}
static void PostRepaintPingHud() {
    HWND h = g_hPingHudWnd.load();
    if (h) PostMessage(h, WM_BRSERVICE_REPAINT, 0, 0);
}
static void PostShowDrawer() {
    HWND h = g_hDrawerModalWnd.load();
    if (h) PostMessage(h, WM_BRSERVICE_SHOW, 0, 0);
}
static void PostHideDrawer() {
    HWND h = g_hDrawerModalWnd.load();
    if (h) PostMessage(h, WM_BRSERVICE_HIDE, 0, 0);
}

bool ServiceWorker::Start() {
    if (s_running.load()) return true;
    s_running = true;
    s_hWatchdog = CreateThread(nullptr, 0, WatchdogThread, nullptr, 0, nullptr);
    return s_hWatchdog != nullptr;
}

void ServiceWorker::Stop() {
    s_running = false;
    if (s_hWatchdog) {
        // Wake up MsgWaitForMultipleObjects if blocked
        PostThreadMessage(GetThreadId(s_hWatchdog), WM_QUIT, 0, 0);
        WaitForSingleObject(s_hWatchdog, 500);
        CloseHandle(s_hWatchdog);
        s_hWatchdog = nullptr;
    }
}

DWORD WINAPI ServiceWorker::WatchdogThread(LPVOID /*param*/) {
    LogInfo("ServiceWorker: Monitor de ciclo de vida e UI Host iniciado.");

    // Initialize UI Windows on THIS persistent thread so they possess a continuous message pump
    if (g_featPingUi.load() || g_featDpsMeterUI.load()) {
        PingHudUI::Initialize(g_hModule);
    }
    if (g_featDpsMeterUI.load()) {
        DrawerModalUI::Initialize(g_hModule);
    }

    // T14: Register Shift+F3 as a global hotkey owned by this thread (reliable, no polling).
    // This replaces the unsafe GetAsyncKeyState polling approach.
    bool hotkeyRegistered = (RegisterHotKey(nullptr, kHotkeyShiftF3, MOD_SHIFT | MOD_NOREPEAT, VK_F3) != FALSE);
    if (!hotkeyRegistered) {
        LogError("ServiceWorker: Falha ao registrar hotkey Shift+F3 (err=%lu). Tentando sem MOD_NOREPEAT.", GetLastError());
        hotkeyRegistered = (RegisterHotKey(nullptr, kHotkeyShiftF3, MOD_SHIFT, VK_F3) != FALSE);
    }
    if (hotkeyRegistered) {
        LogInfo("ServiceWorker: Hotkey Shift+F3 registrada com sucesso.");
    }

    HWND hGame = nullptr;
    bool s_gameEverFound = false;
    ULONGLONG s_gameLostTick = 0;
    bool lastLoading = false;
    bool lastActive = false;

    while (s_running.load()) {
        // 1. Process all pending window messages for our UI windows (PingHud & DrawerModal)
        MSG msg;
        while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                s_running = false;
                break;
            }

            // T04/T05: Handle cross-thread UI commands (Posted from WebSocket/PingEngine threads)
            if (msg.message == WM_BRSERVICE_SHOW && msg.hwnd == nullptr) {
                // Generic show-all (should not normally occur; real targeting is per-window PostMessage)
            } else if (msg.message == WM_BRSERVICE_PLAYER_STATE && msg.hwnd == nullptr) {
                bool inGame   = (msg.wParam != 0);
                bool isLoading = (msg.lParam != 0);
                if (!inGame || isLoading) {
                    PingHudUI::Hide();
                    DrawerModalUI::Hide();
                } else {
                    PingHudUI::Show();
                    PingHudUI::Repaint();
                }
            }

            // T14: Handle registered hotkey messages
            if (msg.message == WM_HOTKEY && msg.wParam == kHotkeyShiftF3) {
                if (!g_isLoadingScreen.load() && g_isGameActive.load()) {
                    DrawerModalUI::Toggle();
                }
            }

            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
        if (!s_running.load()) break;

        // 2. Periodic Safety Check: Check if game process is exiting
        DWORD exitCode = 0;
        if (GetExitCodeProcess(GetCurrentProcess(), &exitCode) && exitCode != STILL_ACTIVE) {
            LogInfo("ServiceWorker: Processo do jogo terminou (exitCode=%lu). Auto-encerrando...", exitCode);
            s_running = false;
            break;
        }

        // 3. Locate game window safely
        if (!hGame || !IsWindow(hGame)) {
            hGame = FindGameWindow();
            if (hGame) {
                g_gameHwnd = hGame;
                s_gameEverFound = true;
                s_gameLostTick = 0;
                LogInfo("ServiceWorker: Janela do Aion localizada: HWND=%p", hGame);
                SyncPositionsSafely(hGame, true);
            } else {
                if (s_gameEverFound) {
                    if (s_gameLostTick == 0) {
                        s_gameLostTick = GetTickCount64();
                    } else if (GetTickCount64() - s_gameLostTick > 2000) {
                        LogInfo("ServiceWorker: Janela do Aion fechada ha mais de 2s. Auto-encerrando processo para evitar orfaos em segundo plano...");
                        s_running = false;
                        ExitProcess(0);
                        return 0;
                    }
                }
                MsgWaitForMultipleObjects(0, nullptr, FALSE, 50, QS_ALLINPUT);
                continue;
            }
        }

        // 4. Active & Foreground Check (Non-intrusive cached calls, NO WM_GETTEXT)
        bool isMinimized = IsIconic(hGame);
        bool isVisible   = IsWindowVisible(hGame);
        HWND fg = GetForegroundWindow();
        DWORD fgPid = 0;
        GetWindowThreadProcessId(fg, &fgPid);
        DWORD myPid = GetCurrentProcessId();
        bool isForeground = (fgPid == myPid);
        bool active = (isVisible && !isMinimized && isForeground);
        g_isGameActive = active;

        // 5. Loading screen detection (state driven entirely by WebSocket PLAYER_STATE)
        bool isLoading = g_isLoadingScreen.load();
        if (isLoading != lastLoading) {
            lastLoading = isLoading;
            if (isLoading) {
                PingHudUI::Hide();
                DrawerModalUI::Hide();
            } else if (active) {
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
                SyncPositionsSafely(hGame, true);
            }
        }

        // 6. T08: g_isInWorld is set exclusively by WebSocket PLAYER_STATE event.
        // Removed redundant derivation from charId here (single source of truth = WebSocket).

        // 7. Active state transitions
        if (active != lastActive) {
            lastActive = active;
            if (active && !isLoading) {
                SyncPositionsSafely(hGame, true);
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
            } else {
                PingHudUI::Hide();
                if (g_drawerPinned.load()) {
                    DrawerModalUI::Hide();
                }
            }
        }

        // 8. Periodic position sync (UI windows follow the game window position)
        if (active && !isLoading) {
            static int syncCounter = 0;
            if (++syncCounter >= 6) { // ~180ms cadence
                syncCounter = 0;
                SyncPositionsSafely(hGame);
            }
        }

        // Wait up to 30ms or wake up immediately if a window message arrives
        MsgWaitForMultipleObjects(0, nullptr, FALSE, 30, QS_ALLINPUT);
    }

    // T14: Unregister hotkey before exiting
    if (hotkeyRegistered) {
        UnregisterHotKey(nullptr, kHotkeyShiftF3);
    }

    // T07: Clean up UI windows on the OWNING thread (WatchdogThread).
    // This is the ONLY place these are destroyed. BR_Shutdown does NOT call them again.
    DrawerModalUI::Shutdown();
    PingHudUI::Shutdown();

    LogInfo("ServiceWorker finalizado.");
    return 0;
}

} // namespace BrService
