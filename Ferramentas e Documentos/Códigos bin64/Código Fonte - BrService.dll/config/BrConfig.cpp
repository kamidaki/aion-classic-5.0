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

    g_drawerW       = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Width",       760, ini.c_str()), 420, 960);
    g_drawerH       = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Height",      560, ini.c_str()), 480, 800);
    g_drawerOpacity = std::clamp((int)GetPrivateProfileIntW(L"DrawerUI", L"Opacity",     255, ini.c_str()), 120, 255);
    g_compactView   = (GetPrivateProfileIntW(L"DrawerUI", L"CompactView",  0, ini.c_str()) != 0);
    g_drawerPinned  = (GetPrivateProfileIntW(L"DrawerUI", L"Pinned",       1, ini.c_str()) != 0);

    g_comboVisible = (GetPrivateProfileIntW(L"ComboUI", L"Visible", 1, ini.c_str()) != 0);

    wchar_t buf[64] = { 0 };
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

    g_drawerPosX = GetPrivateProfileIntW(L"DrawerUI", L"PosX", -1, ini.c_str());
    g_drawerPosY = GetPrivateProfileIntW(L"DrawerUI", L"PosY", -1, ini.c_str());

    LogInfo("Configuracoes carregadas de %ls: W=%d, H=%d, Pos=(%d, %d), Opacity=%d, ComboVis=%d, ComboScale=%.2f, ComboPos=(%.2f, %.2f)",
            ini.c_str(),
            g_drawerW.load(), g_drawerH.load(), g_drawerPosX.load(), g_drawerPosY.load(), g_drawerOpacity.load(),
            g_comboVisible.load() ? 1 : 0, g_comboScale.load(),
            g_comboPosNormX.load(), g_comboPosNormY.load());
}

void BrConfig::Save() {
    std::wstring ini = GetIniPath();

    WritePrivateProfileStringW(L"DrawerUI", L"Width",       std::to_wstring(g_drawerW.load()).c_str(),        ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"Height",      std::to_wstring(g_drawerH.load()).c_str(),        ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"PosX",        std::to_wstring(g_drawerPosX.load()).c_str(),     ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"PosY",        std::to_wstring(g_drawerPosY.load()).c_str(),     ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"Opacity",     std::to_wstring(g_drawerOpacity.load()).c_str(),  ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"CompactView", g_compactView.load()       ? L"1" : L"0", ini.c_str());
    WritePrivateProfileStringW(L"DrawerUI", L"Pinned",      g_drawerPinned.load()       ? L"1" : L"0", ini.c_str());

    WritePrivateProfileStringW(L"ComboUI", L"Visible", g_comboVisible.load() ? L"1" : L"0", ini.c_str());
    wchar_t buf[64] = { 0 };
    swprintf_s(buf, L"%.2f", g_comboOpacity.load());
    WritePrivateProfileStringW(L"ComboUI", L"Opacity", buf, ini.c_str());
    swprintf_s(buf, L"%.2f", g_comboScale.load());
    WritePrivateProfileStringW(L"ComboUI", L"Scale", buf, ini.c_str());
    swprintf_s(buf, L"%.3f", g_comboPosNormX.load());
    WritePrivateProfileStringW(L"ComboUI", L"PosNormX", buf, ini.c_str());
    swprintf_s(buf, L"%.3f", g_comboPosNormY.load());
    WritePrivateProfileStringW(L"ComboUI", L"PosNormY", buf, ini.c_str());
}

} // namespace BrService
