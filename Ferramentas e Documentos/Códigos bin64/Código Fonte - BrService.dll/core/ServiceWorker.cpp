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

struct WindowSearchContext {
    DWORD targetPid;
    HWND foundHwnd;
};

static BOOL CALLBACK EnumWindowsCallback(HWND hwnd, LPARAM lParam) {
    auto* ctx = reinterpret_cast<WindowSearchContext*>(lParam);
    DWORD pid = 0;
    GetWindowThreadProcessId(hwnd, &pid);
    if (pid == ctx->targetPid) {
        if (hwnd == g_hPingHudWnd || hwnd == g_hDrawerModalWnd || hwnd == g_hComboWnd.load()) return TRUE;

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
    // In Aion, loading state is tracked via WebSocket and in-world status.
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

        // 5. Loading screen detection
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

        // 6. In-world flag from WebSocket player state
        uint32_t charId = g_localPlayerId.load();
        g_isInWorld = (charId > 0);

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

        // 8. Direct Hotkey (Shift + F3) with game active and not loading
        if (active && !isLoading) {
            static bool s_lastShiftF3 = false;
            bool isF3 = (GetAsyncKeyState(VK_F3) & 0x8000) != 0;
            bool isShift = (GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0;
            bool shiftF3 = isF3 && isShift;
            if (shiftF3 && !s_lastShiftF3) {
                DrawerModalUI::Toggle();
            }
            s_lastShiftF3 = shiftF3;

            // Periodic position sync check
            static int syncCounter = 0;
            if (++syncCounter >= 6) { // ~180ms cadence
                syncCounter = 0;
                SyncPositionsSafely(hGame);
            }
        }

        // Wait up to 30ms or wake up immediately if a window message arrives
        MsgWaitForMultipleObjects(0, nullptr, FALSE, 30, QS_ALLINPUT);
    }

    // Clean up UI windows on the owning thread
    DrawerModalUI::Shutdown();
    PingHudUI::Shutdown();

    LogInfo("ServiceWorker finalizado.");
    return 0;
}

} // namespace BrService
