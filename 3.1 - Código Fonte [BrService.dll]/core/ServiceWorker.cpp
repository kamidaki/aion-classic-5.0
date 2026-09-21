#include "ServiceWorker.h"
#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../cvar/CVarManager.h"
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
        // Skip our own overlay and drawer windows
        if (hwnd == g_hPingHudWnd || hwnd == g_hDrawerModalWnd) return TRUE;

        wchar_t className[128] = { 0 };
        GetClassNameW(hwnd, className, 128);
        if (wcsstr(className, L"BrService") != nullptr) return TRUE;

        wchar_t title[256] = { 0 };
        GetWindowTextW(hwnd, title, 256);
        if (wcscmp(title, L"Aion Ping HUD") == 0 || wcsstr(title, L"Combat Analysis") != nullptr) return TRUE;

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
    // While loading, Aion modifies title or state
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
    if (s_hWatchdog) {
        WaitForSingleObject(s_hWatchdog, 1500);
        CloseHandle(s_hWatchdog);
        s_hWatchdog = nullptr;
    }
}

DWORD WINAPI ServiceWorker::WatchdogThread(LPVOID /*param*/) {
    LogInfo("ServiceWorker iniciado. Monitorando ciclo de vida do Aion...");

    HWND hGame = nullptr;
    RECT lastRect = { 0, 0, 0, 0 };
    bool lastLoading = false;
    bool lastActive = false;

    while (s_running.load()) {
        if (!hGame || !IsWindow(hGame)) {
            hGame = FindGameWindow();
            if (hGame) {
                g_gameHwnd = hGame;
                LogInfo("Janela do Aion localizada: HWND=%p", hGame);
            } else {
                Sleep(500);
                continue;
            }
        }

        // 1. Check window visibility & active state
        bool isMinimized = IsIconic(hGame);
        bool isVisible = IsWindowVisible(hGame);
        g_isGameActive = (isVisible && !isMinimized);

        // 2. Check loading screen
        bool isLoading = CheckLoadingScreen(hGame);
        g_isLoadingScreen = isLoading;

        if (isLoading != lastLoading) {
            lastLoading = isLoading;
            if (isLoading) {
                // Instantly hide HUD and drawer during map transitions
                PingHudUI::Hide();
                DrawerModalUI::Close();
                LogInfo("Tela de carregamento detectada -> HUDs ocultados temporariamente.");
            } else {
                // Restore CVars and HUDs when loading finishes
                CVarManager::ResyncOnMapChange();
                PingHudUI::Show();
                LogInfo("Fim da tela de carregamento -> CVars sincronizados e HUD restaurado.");
            }
        }

        // 3. Track position and size of game window
        if (!isMinimized && !isLoading && g_isGameActive.load()) {
            RECT cr;
            GetClientRect(hGame, &cr);
            POINT pt = { 0, 0 };
            ClientToScreen(hGame, &pt);

            int gx = pt.x;
            int gy = pt.y;
            int gw = cr.right - cr.left;
            int gh = cr.bottom - cr.top;

            if (gx != lastRect.left || gy != lastRect.top ||
                gw != (lastRect.right - lastRect.left) || gh != (lastRect.bottom - lastRect.top) ||
                g_isGameActive.load() != lastActive || !IsWindowVisible(g_hPingHudWnd)) {

                lastRect = { gx, gy, gx + gw, gy + gh };
                lastActive = g_isGameActive.load();

                PingHudUI::UpdatePosition(gx, gy, gw, gh);
                DrawerModalUI::UpdatePosition(gx, gy, gw, gh);
            }
        } else {
            PingHudUI::Hide();
            if (g_isDrawerOpen.load()) {
                ShowWindow(g_hDrawerModalWnd, SW_HIDE);
            }
        }

        Sleep(60); // Low 16Hz polling -> 0% CPU consumption
    }

    LogInfo("ServiceWorker finalizado.");
    return 0;
}

} // namespace BrService
