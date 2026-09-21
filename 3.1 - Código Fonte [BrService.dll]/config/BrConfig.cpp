#include "BrConfig.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"

namespace BrService {

std::wstring BrConfig::GetIniPath() {
    wchar_t path[MAX_PATH] = { 0 };
    GetModuleFileNameW(nullptr, path, MAX_PATH);
    wchar_t* lastSlash = wcsrchr(path, L'\\');
    if (lastSlash) {
        wcscpy_s(lastSlash + 1, MAX_PATH - (lastSlash - path + 1), L"br_settings.ini");
    } else {
        wcscpy_s(path, MAX_PATH, L"br_settings.ini");
    }
    return std::wstring(path);
}

void BrConfig::Load() {
    std::wstring ini = GetIniPath();

    wchar_t buf[64] = { 0 };
    GetPrivateProfileStringW(L"ShugoConsole", L"FOV", L"75.0", buf, 64, ini.c_str());
    g_cvarFov = static_cast<float>(_wtof(buf));

    GetPrivateProfileStringW(L"ShugoConsole", L"CamMax", L"25.0", buf, 64, ini.c_str());
    g_cvarCamMax = static_cast<float>(_wtof(buf));

    g_cvarMaxFps = GetPrivateProfileIntW(L"ShugoConsole", L"MaxFPS", 144, ini.c_str());
    g_cvarTripleBuffering = (GetPrivateProfileIntW(L"ShugoConsole", L"TripleBuffering", 1, ini.c_str()) != 0);
    g_cvarAnisotropic = (GetPrivateProfileIntW(L"ShugoConsole", L"Anisotropic", 1, ini.c_str()) != 0);

    LogInfo("Configuracoes carregadas de %ls: FOV=%.1f, CamMax=%.1f, MaxFPS=%d",
            ini.c_str(), g_cvarFov.load(), g_cvarCamMax.load(), g_cvarMaxFps.load());
}

void BrConfig::Save() {
    std::wstring ini = GetIniPath();

    wchar_t buf[64] = { 0 };
    swprintf_s(buf, L"%.1f", g_cvarFov.load());
    WritePrivateProfileStringW(L"ShugoConsole", L"FOV", buf, ini.c_str());

    swprintf_s(buf, L"%.1f", g_cvarCamMax.load());
    WritePrivateProfileStringW(L"ShugoConsole", L"CamMax", buf, ini.c_str());

    swprintf_s(buf, L"%d", g_cvarMaxFps.load());
    WritePrivateProfileStringW(L"ShugoConsole", L"MaxFPS", buf, ini.c_str());

    WritePrivateProfileStringW(L"ShugoConsole", L"TripleBuffering", g_cvarTripleBuffering.load() ? L"1" : L"0", ini.c_str());
    WritePrivateProfileStringW(L"ShugoConsole", L"Anisotropic", g_cvarAnisotropic.load() ? L"1" : L"0", ini.c_str());
}

} // namespace BrService
