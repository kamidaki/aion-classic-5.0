#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "ServiceWorker.h"
#include "../config/BrConfig.h"
#include "../network/PingEngine.h"
#include "../network/WebSocketClient.h"
#include "../database/CombatDb.h"
#include "../ui/UICommon.h"
#include "../ui/IconManager.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include "../combo/ComboUI.h"
#include <string>
#include <atomic>

namespace BrService {

static HANDLE s_hInitThread = nullptr;
static std::atomic<bool> s_initDone(false);
// T07: Prevent double-shutdown from DLL_PROCESS_DETACH + explicit BR_Shutdown call
static std::atomic<bool> s_alreadyShutdown(false);

static std::string ParseParam(const char* cmdline, const char* key) {
    if (!cmdline || !key) return "";
    std::string s(cmdline);
    std::string sLower = s;
    for (char& c : sLower) c = (char)::tolower((unsigned char)c);
    std::string keyLower(key);
    for (char& c : keyLower) c = (char)::tolower((unsigned char)c);

    size_t pos = sLower.find(keyLower);
    if (pos == std::string::npos) return "";
    pos += keyLower.length();
    while (pos < s.length() && (s[pos] == ' ' || s[pos] == ':' || s[pos] == '=')) pos++;
    size_t end = s.find_first_of(" \t\r\n", pos);
    if (end == std::string::npos) end = s.length();
    return s.substr(pos, end - pos);
}

static bool IsParamEnabled(const char* cmdline, const char* paramName, bool defaultValue = true) {
    if (!cmdline || !paramName) return defaultValue;
    std::string s(cmdline);
    for (char& c : s) c = (char)::tolower((unsigned char)c);

    std::string pName(paramName);
    for (char& c : pName) c = (char)::tolower((unsigned char)c);

    std::string keyColon = "-" + pName + ":";
    std::string keyEqual = "-" + pName + "=";

    size_t pos = s.find(keyColon);
    size_t keyLen = keyColon.length();
    if (pos == std::string::npos) {
        pos = s.find(keyEqual);
        keyLen = keyEqual.length();
    }
    if (pos == std::string::npos) {
        return defaultValue;
    }

    pos += keyLen;
    while (pos < s.length() && (s[pos] == ' ' || s[pos] == '\t')) pos++;
    size_t end = s.find_first_of(" \t\r\n", pos);
    if (end == std::string::npos) end = s.length();
    std::string val = s.substr(pos, end - pos);

    if (val == "disable" || val == "disabled" || val == "0" || val == "false" || val == "no" || val == "off") {
        return false;
    }
    if (val == "enable" || val == "enabled" || val == "1" || val == "true" || val == "yes" || val == "on") {
        return true;
    }
    return defaultValue;
}

static DWORD WINAPI BackgroundInitThread(LPVOID /*param*/) {
    LogInfo("BackgroundInitThread: Inicializando subsistemas em thread separada...");

    // 1. Initialize core subsystems
    UICommon::InitializeGdiplus();
    BrConfig::Load();

    // T16: Initialize IconManager during startup (filesystem scan) — NEVER lazy from render thread.
    // This prevents first-render latency and render-thread I/O blocking.
    IconManager::Initialize();

    if (g_featDpsMeterUI.load()) {
        CombatDb::Initialize();
    }

    // 2. Start Network Services
    if (g_featPingUi.load()) {
        PingEngine::Start(g_serverIp);
    }
    if (g_featDpsMeterUI.load()) {
        WebSocketClient::Start(g_serverIp, 2130);
    }

    // 3. Start Combo UI (has its own render thread)
    if (g_featComboUi.load()) {
        g_ComboUI.Start();
    }

    // 4. Start Lifecycle Watchdog & UI Host
    ServiceWorker::Start();

    s_initDone = true;
    LogInfo("BackgroundInitThread: Inicializacao concluida com 100%% de sucesso.");
    return 0;
}

} // namespace BrService

extern "C" {

__declspec(dllexport) bool WINAPI BR_Initialize(const char* token, const char* cmdline) {
    using namespace BrService;

    try {
        if (!token || strcmp(token, g_securityToken.c_str()) != 0) {
            LogError("BR_Initialize: Token de seguranca incorreto ou violado.");
            return false;
        }

        LogInfo("=================================================================");
        LogInfo("   BrService.dll - Ping, DPS Meter & Combo UI Ativado           ");
        LogInfo("=================================================================");

        const char* actualCmd = (cmdline && cmdline[0] != '\0') ? cmdline : GetCommandLineA();
        if (actualCmd) {
            std::string ip = ParseParam(actualCmd, "-ip");
            if (!ip.empty()) {
                g_serverIp = ip;
            }
            std::string port = ParseParam(actualCmd, "-port");
            if (!port.empty()) {
                try { g_serverPort = std::stoi(port); } catch (...) {}
            }

            // T08/T09: Parse language from cmdline and set BOTH g_clientLang (for INI save)
            // AND g_isEnglish atomic (for thread-safe I18n queries from any thread).
            std::string lang = ParseParam(actualCmd, "-lang");
            if (lang.empty()) lang = ParseParam(actualCmd, "/lang");
            if (!lang.empty()) {
                for (char& c : lang) c = (char)::toupper((unsigned char)c);
                g_clientLang = lang;
            }
            // Set atomic flag from parsed language (cmdline takes priority over INI default)
            g_isEnglish.store(g_clientLang == "ENG" || g_clientLang == "ENU",
                              std::memory_order_relaxed);

            g_featPingUi     = IsParamEnabled(actualCmd, "pingUi",     true);
            g_featDpsMeterUI = IsParamEnabled(actualCmd, "DpsMeterUI", true);
            g_featComboUi    = IsParamEnabled(actualCmd, "comboUi",    true);
        }

        // T01/T02: Run heavy initialization asynchronously. BR_Shutdown will wait for
        // s_initDone before proceeding to stop subsystems, preventing shutdown-before-init races.
        s_alreadyShutdown = false;
        s_hInitThread = CreateThread(nullptr, 0, BackgroundInitThread, nullptr, 0, nullptr);
        return true;
    } catch (...) {
        return false;
    }
}

__declspec(dllexport) void WINAPI BR_Shutdown() {
    using namespace BrService;

    // T07: Prevent double-shutdown (e.g., DLL_PROCESS_DETACH + explicit call from Version.dll)
    if (s_alreadyShutdown.exchange(true)) {
        LogInfo("BR_Shutdown: ja foi executado, ignorando chamada duplicada.");
        return;
    }

    LogInfo("BR_Shutdown: Encerrando servicos de forma segura...");

    // T02: Wait for background init to complete before shutting down subsystems.
    // This prevents Stop() being called before Start() on any subsystem.
    if (s_hInitThread) {
        // Wait up to 5s for init to finish; if it doesn't, proceed anyway (defensive).
        DWORD waitResult = WaitForSingleObject(s_hInitThread, 5000);
        if (waitResult == WAIT_TIMEOUT) {
            LogError("BR_Shutdown: Timeout aguardando BackgroundInitThread. Continuando shutdown defensivo.");
        }
        CloseHandle(s_hInitThread);
        s_hInitThread = nullptr;
    }

    ServiceWorker::Stop();
    if (g_featComboUi.load()) {
        g_ComboUI.Stop();
    }
    // T07: DrawerModalUI::Shutdown and PingHudUI::Shutdown are called by ServiceWorker's
    // WatchdogThread cleanup. We do NOT call them again here to prevent double-destroy.
    // ServiceWorker::Stop() ensures WatchdogThread has exited before returning.
    WebSocketClient::Stop();
    PingEngine::Stop();
    CombatDb::Shutdown();
    IconManager::Shutdown();
    UICommon::ShutdownGdiplus();

    LogInfo("BR_Shutdown: Finalizacao concluida.");
}

__declspec(dllexport) bool WINAPI BR_GetStatus() {
    return true;
}

} // extern "C"

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID /*lpvReserved*/) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinstDLL);
        BrService::g_hModule = hinstDLL;
    }
    // T01: Do NOT call BR_Shutdown in DLL_PROCESS_DETACH.
    // Calling WaitForSingleObject while the loader lock is held causes deadlock.
    // BR_Shutdown must be called EXPLICITLY by the host (Version.dll) before FreeLibrary.
    // else if (fdwReason == DLL_PROCESS_DETACH) { BR_Shutdown(); } // REMOVED — deadlock risk
    return TRUE;
}
