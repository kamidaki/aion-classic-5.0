#include "ServiceWorker.h"
#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../cvar/CVarManager.h"
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
        if (hwnd == g_hPingHudWnd || hwnd == g_hDrawerModalWnd || hwnd == g_overlayHwnd) return TRUE;

        wchar_t className[128] = { 0 };
        GetClassNameW(hwnd, className, 128);
        if (wcsstr(className, L"BrService") != nullptr ||
            wcscmp(className, L"AionComboUI") == 0 ||
            wcsstr(className, L"ComboUI") != nullptr ||
            wcsstr(className, L"Chrome_WidgetWin") != nullptr ||
            wcsstr(className, L"Intermediate D3D") != nullptr) {
            return TRUE;
        }

        wchar_t title[256] = { 0 };
        GetWindowTextW(hwnd, title, 256);
        if (wcscmp(title, L"Aion Ping HUD") == 0 ||
            wcsstr(title, L"Analisador") != nullptr ||
            wcsstr(title, L"Painel Academy") != nullptr ||
            wcsstr(title, L"ComboUI") != nullptr) {
            return TRUE;
        }

        // Aion Classic game window class (CrySystem / CryInput official class)
        if (wcscmp(className, L"AIONClientWndClass1.0") == 0 || wcscmp(className, L"AION Client") == 0) {
            RECT rc;
            GetClientRect(hwnd, &rc);
            if ((rc.right - rc.left) >= 300 && (rc.bottom - rc.top) >= 300) {
                ctx->foundHwnd = hwnd;
                return FALSE;
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
    if (!hwnd || !IsWindow(hwnd)) return false;
    wchar_t title[256] = { 0 };
    GetWindowTextW(hwnd, title, 256);
    if (wcsstr(title, L"Loading") != nullptr || wcsstr(title, L"carregando") != nullptr) {
        return true;
    }
    return false;
}

static void SyncPositionsDirectly(HWND hGame, bool force = false) {
    if (!hGame || !IsWindow(hGame) || IsIconic(hGame)) return;

    RECT cr = { 0 };
    GetClientRect(hGame, &cr);
    POINT pt = { 0, 0 };
    ClientToScreen(hGame, &pt);

    int gx = pt.x;
    int gy = pt.y;
    int gw = cr.right - cr.left;
    int gh = cr.bottom - cr.top;

    if (gw <= 0 || gh <= 0) return;

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
        WaitForSingleObject(s_hWatchdog, 300);
        CloseHandle(s_hWatchdog);
        s_hWatchdog = nullptr;
    }
}

DWORD WINAPI ServiceWorker::WatchdogThread(LPVOID /*param*/) {
    LogInfo("ServiceWorker: Monitor de ciclo de vida do Aion iniciado.");

    HWND hGame = nullptr;
    bool s_gameEverFound = false;
    ULONGLONG s_gameLostTick = 0;
    bool lastLoading = false;
    bool lastActive = false;

    while (s_running.load()) {
        // 0. Periodic Safety Check: Check if game process is exiting
        DWORD exitCode = 0;
        if (GetExitCodeProcess(GetCurrentProcess(), &exitCode) && exitCode != STILL_ACTIVE) {
            LogInfo("ServiceWorker: Processo do jogo terminou (exitCode=%lu). Auto-encerrando...", exitCode);
            s_running = false;
            break;
        }

        // 1. Locate game window
        if (!hGame || !IsWindow(hGame)) {
            hGame = FindGameWindow();
            if (hGame) {
                g_gameHwnd = hGame;
                ::g_gameHwnd = hGame;
                s_gameEverFound = true;
                s_gameLostTick = 0;
                LogInfo("ServiceWorker: Janela do Aion localizada: HWND=%p", hGame);
                SyncPositionsDirectly(hGame, true);
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
                Sleep(100);
                continue;
            }
        }

        // 2. Active & Foreground Check
        bool isMinimized = IsIconic(hGame);
        bool isVisible   = IsWindowVisible(hGame);
        HWND fg = GetForegroundWindow();
        DWORD fgPid = 0;
        GetWindowThreadProcessId(fg, &fgPid);
        DWORD myPid = GetCurrentProcessId();
        bool isForeground = (fgPid == myPid);
        bool active = (isVisible && !isMinimized && isForeground);
        g_isGameActive = active;

        // 3. Loading screen detection
        bool isLoading = CheckLoadingScreen(hGame);
        g_isLoadingScreen = isLoading;
        if (isLoading != lastLoading) {
            lastLoading = isLoading;
            if (isLoading) {
                PingHudUI::Hide();
                DrawerModalUI::Hide();
            } else if (active) {
                CVarManager::ResyncOnMapChange();
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
                SyncPositionsDirectly(hGame, true);
            }
        }

        // 4. Update in-world memory flag dynamically from Game.dll
        uint32_t charId = GetLocalPlayerObjectId();
        g_isInWorld = (charId > 0);

        // 5. Active state change handling (clean, zero flickering)
        if (active != lastActive) {
            lastActive = active;
            if (active && !isLoading) {
                SyncPositionsDirectly(hGame, true);
                PingHudUI::Show();
                DrawerModalUI::RestoreIfOpen();
            } else {
                PingHudUI::Hide();
                if (g_drawerPinned.load()) {
                    DrawerModalUI::Hide();
                }
            }
        }

        // 6. Direct Hotkey (Shift + F3) with game active and not in loading
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
            if (++syncCounter >= 10) { // ~500ms
                syncCounter = 0;
                SyncPositionsDirectly(hGame);
            }
        }

        Sleep(50); // ~20Hz responsive loop (0% CPU)
    }

    LogInfo("ServiceWorker finalizado.");
    return 0;
}

} // namespace BrService
