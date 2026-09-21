#include "ServiceGlobals.h"
#include "ServiceLog.h"
#include "ServiceWorker.h"
#include "../config/BrConfig.h"
#include "../network/PingEngine.h"
#include "../network/WebSocketClient.h"
#include "../database/CombatDb.h"
#include "../cvar/CVarManager.h"
#include "../model3d/CryModelBridge.h"
#include "../ui/UICommon.h"
#include "../ui/PingHudUI.h"
#include "../ui/DrawerModalUI.h"
#include <string>

namespace BrService {

static std::string ParseParam(const char* cmdline, const char* key) {
    if (!cmdline || !key) return "";
    std::string s(cmdline);
    size_t pos = s.find(key);
    if (pos == std::string::npos) return "";
    pos += strlen(key);
    while (pos < s.length() && (s[pos] == ' ' || s[pos] == ':' || s[pos] == '=')) pos++;
    size_t end = s.find(' ', pos);
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

} // namespace BrService

extern "C" {

__declspec(dllexport) bool WINAPI BR_Initialize(const char* token, const char* cmdline) {
    using namespace BrService;

    try {
        // Validate token integrity
        if (!token || strcmp(token, g_securityToken.c_str()) != 0) {
            LogError("BR_Initialize: Token de seguranca incorreto ou violado.");
            return false;
        }

        LogInfo("=================================================================");
        LogInfo("   BrService.dll - Shugo Console, Ping & DPS Meter Ativado      ");
        LogInfo("=================================================================");

        // Extract IP and feature flags from cmdline
        if (cmdline) {
            std::string ip = ParseParam(cmdline, "-ip");
            if (!ip.empty()) {
                g_serverIp = ip;
                LogInfo("IP do Servidor extraido da linha de comando: %s", g_serverIp.c_str());
            }
            std::string port = ParseParam(cmdline, "-port");
            if (!port.empty()) {
                try { g_serverPort = std::stoi(port); } catch (...) {}
            }

            // Feature Control Flags (default: true / enable)
            g_featConsole = IsParamEnabled(cmdline, "console", true);
            g_featFreeFly = IsParamEnabled(cmdline, "freefly", true);
            g_featPingUi = IsParamEnabled(cmdline, "pingUi", true);
            g_featDpsMeterUI = IsParamEnabled(cmdline, "DpsMeterUI", true);
            g_featModel3D = IsParamEnabled(cmdline, "Model3D", true);
            g_featFov = IsParamEnabled(cmdline, "fov", true);
            g_featCamMax = IsParamEnabled(cmdline, "camMax", true);
            g_featFpsUnlock = IsParamEnabled(cmdline, "fpsUnlock", true);

            LogInfo("Configuracao de Recursos do BrService via Linha de Comando:");
            LogInfo("  [-console]    : %s", g_featConsole.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-freefly]    : %s", g_featFreeFly.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-pingUi]     : %s", g_featPingUi.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-DpsMeterUI] : %s", g_featDpsMeterUI.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-Model3D]    : %s", g_featModel3D.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-fov]        : %s", g_featFov.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-camMax]     : %s", g_featCamMax.load() ? "ENABLE" : "DISABLE");
            LogInfo("  [-fpsUnlock]  : %s", g_featFpsUnlock.load() ? "ENABLE" : "DISABLE");
        }

        // 1. Initialize Subsystems
        UICommon::InitializeGdiplus();
        BrConfig::Load();
        if (g_featDpsMeterUI.load()) {
            CombatDb::Initialize();
        }
        CVarManager::Initialize();
        if (g_featModel3D.load()) {
            CryModelBridge::Initialize();
        }

        // 2. Start Network Services
        if (g_featPingUi.load()) {
            PingEngine::Start(g_serverIp);
        }
        if (g_featDpsMeterUI.load()) {
            WebSocketClient::Start(g_serverIp, 2130);
        }

        // 3. Initialize UI Windows
        if (g_featConsole.load() || g_featPingUi.load()) {
            PingHudUI::Initialize(g_hModule);
        }
        if (g_featConsole.load()) {
            DrawerModalUI::Initialize(g_hModule);
        }

        // 4. Start Lifecycle Watchdog
        ServiceWorker::Start();

        LogInfo("BR_Initialize: Inicializacao concluida com 100%% de sucesso.");
        return true;
    } catch (const std::exception& e) {
        LogError("BR_Initialize: Excecao fatal durante inicializacao: %s", e.what());
        return false;
    } catch (...) {
        LogError("BR_Initialize: Excecao fatal desconhecida durante inicializacao.");
        return false;
    }
}

__declspec(dllexport) void WINAPI BR_Shutdown() {
    using namespace BrService;
    LogInfo("BR_Shutdown: Encerrando servicos...");

    ServiceWorker::Stop();
    DrawerModalUI::Shutdown();
    PingHudUI::Shutdown();
    WebSocketClient::Stop();
    PingEngine::Stop();
    CryModelBridge::Shutdown();
    CVarManager::Shutdown();
    CombatDb::Shutdown();
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

        // Pin DLL in memory
        HMODULE hSelf = nullptr;
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN, (LPCWSTR)hinstDLL, &hSelf);
    } else if (fdwReason == DLL_PROCESS_DETACH) {
        BR_Shutdown();
    }
    return TRUE;
}
