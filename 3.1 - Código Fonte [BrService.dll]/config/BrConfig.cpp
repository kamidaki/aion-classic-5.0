#include "BrConfig.h"
#include "../core/ServiceGlobals.h"
#include "../core/ServiceLog.h"
#include "../combo/ComboTypes.h"
#include <algorithm>

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

    g_drawerW = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Width", 460, ini.c_str()), 400, 640);
    g_drawerH = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Height", 580, ini.c_str()), 480, 780);
    g_drawerOpacity = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Opacity", 255, ini.c_str()), 120, 255);
    g_compactView = (GetPrivateProfileIntW(L"DrawerUI", L"CompactView", 0, ini.c_str()) != 0);
    g_hideConsoleSection = (GetPrivateProfileIntW(L"DrawerUI", L"HideConsole", 0, ini.c_str()) != 0);

    g_comboVisible = (GetPrivateProfileIntW(L"ComboUI", L"Visible", 1, ini.c_str()) != 0);

    GetPrivateProfileStringW(L"ComboUI", L"Opacity", L"1.0", buf, 64, ini.c_str());
    g_comboOpacity = std::clamp(static_cast<float>(_wtof(buf)), 0.10f, 1.0f);
    SetComboOverlayOpacity(g_comboOpacity.load());

    GetPrivateProfileStringW(L"ComboUI", L"Scale", L"1.0", buf, 64, ini.c_str());
    g_comboScale = std::clamp(static_cast<float>(_wtof(buf)), 0.55f, 1.60f);

    GetPrivateProfileStringW(L"ComboUI", L"PosNormX", L"0.80", buf, 64, ini.c_str());
    g_comboPosNormX = std::clamp(static_cast<float>(_wtof(buf)), 0.05f, 0.95f);

    GetPrivateProfileStringW(L"ComboUI", L"PosNormY", L"0.50", buf, 64, ini.c_str());
    g_comboPosNormY = std::clamp(static_cast<float>(_wtof(buf)), 0.05f, 0.95f);

    SetComboOverlayLayout(g_comboPosNormX.load(), g_comboPosNormY.load(), g_comboScale.load());

    g_secureAreaVisible = (GetPrivateProfileIntW(L"SecureArea", L"Visible", 1, ini.c_str()) != 0);

    LogInfo("Configuracoes carregadas de %ls: FOV=%.1f, CamMax=%.1f, MaxFPS=%d, W=%d, H=%d, Opacity=%d, ComboVis=%d, ComboScale=%.2f, ComboPos=(%.2f, %.2f), SecureArea=%d",
            ini.c_str(), g_cvarFov.load(), g_cvarCamMax.load(), g_cvarMaxFps.load(),
            g_drawerW.load(), g_drawerH.load(), g_drawerOpacity.load(),
            g_comboVisible.load() ? 1 : 0, g_comboScale.load(),
            g_comboPosNormX.load(), g_comboPosNormY.load(), g_secureAreaVisible.load() ? 1 : 0);
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

    WritePrivateProfileStringW(L"DrawerUI", L"Width", std::to_wstring(g_drawerW.load()).c_str(), ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"Height", std::to_wstring(g_drawerH.load()).c_str(), ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"Opacity", std::to_wstring(g_drawerOpacity.load()).c_str(), ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"CompactView", g_compactView.load() ? L"1" : L"0", ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"HideConsole", g_hideConsoleSection.load() ? L"1" : L"0", ini.c_str());

    WritePrivateProfileStringW(L"ComboUI", L"Visible", g_comboVisible.load() ? L"1" : L"0", ini.c_str());
    swprintf_s(buf, L"%.2f", g_comboOpacity.load());
    WritePrivateProfileStringW(L"ComboUI", L"Opacity", buf, ini.c_str());
    swprintf_s(buf, L"%.2f", g_comboScale.load());
    WritePrivateProfileStringW(L"ComboUI", L"Scale", buf, ini.c_str());
    swprintf_s(buf, L"%.3f", g_comboPosNormX.load());
    WritePrivateProfileStringW(L"ComboUI", L"PosNormX", buf, ini.c_str());
    swprintf_s(buf, L"%.3f", g_comboPosNormY.load());
    WritePrivateProfileStringW(L"ComboUI", L"PosNormY", buf, ini.c_str());

    WritePrivateProfileStringW(L"SecureArea", L"Visible", g_secureAreaVisible.load() ? L"1" : L"0", ini.c_str());
}

} // namespace BrService
