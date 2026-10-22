#include "GameOptions.h"
#include <cstdio>
#include <windows.h>

GameOptions::GameOptions()
    : m_nPreset(3),
      m_nWidth(1920),
      m_nHeight(1080),
      m_nBPP(32),
      m_nRefresh(60),
      m_bFullscreen(true),
      m_bNCPing(true),
      m_bMRT(true)
{
    // Populate default graphics options matching Aion Classic
    m_intOptions["g_cfg_edit_option"] = 1;
    m_intOptions["g_cfg_change_gameoption"] = 1;
    m_intOptions["r_mrt_depthrender"] = 1;
    m_intOptions["g_cfg_video_BACKGROUND"] = 3;
    m_intOptions["g_cfg_video_EFFECT"] = 3;
    m_intOptions["g_cfg_video_ENTITY_DIST"] = 3;
    m_intOptions["g_cfg_video_ENV_TEX"] = 3;
    m_intOptions["g_cfg_video_FSAA"] = 2;
    m_intOptions["g_cfg_video_GENERAL"] = 3;
    m_intOptions["g_cfg_video_GLARE"] = 1;
    m_intOptions["g_cfg_video_GLOW"] = 1;
    m_intOptions["g_cfg_video_MODEL_CACHE"] = 3;
    m_intOptions["g_cfg_video_MRT_BACKGROUND"] = 3;
    m_intOptions["g_cfg_video_MRT_BUMP"] = 1;
    m_intOptions["g_cfg_video_MRT_CAMERA"] = 1;
    m_intOptions["g_cfg_video_MRT_DOF"] = 1;
    m_intOptions["g_cfg_video_MRT_EFFECT"] = 3;
    m_intOptions["g_cfg_video_MRT_ENTITY_DIST"] = 3;
    m_intOptions["g_cfg_video_MRT_ENV_TEX"] = 3;
    m_intOptions["g_cfg_video_MRT_FSAA"] = 2;
    m_intOptions["g_cfg_video_MRT_GENERAL"] = 3;
    m_intOptions["g_cfg_video_MRT_GLARE"] = 1;
    m_intOptions["g_cfg_video_MRT_GLOW"] = 1;
    m_intOptions["g_cfg_video_MRT_LOWEST"] = 0;
    m_intOptions["g_cfg_video_MRT_MODEL_CACHE"] = 3;
    m_intOptions["g_cfg_video_MRT_SHADER"] = 3;
    m_intOptions["g_cfg_video_MRT_SHADOW"] = 3;
    m_intOptions["g_cfg_video_MRT_SKILLFX"] = 3;
}

GameOptions::~GameOptions()
{
}

bool GameOptions::Init()
{
    LoadOptions();
    return true;
}

void GameOptions::Shutdown()
{
    SaveOptions();
}

void GameOptions::SetPreset(int presetLevel)
{
    if (presetLevel < 0) presetLevel = 0;
    if (presetLevel > 4) presetLevel = 4;
    m_nPreset = presetLevel;

    // Adjust settings according to preset
    for (auto& kv : m_intOptions)
    {
        if (kv.first.find("video") != std::string::npos)
        {
            kv.second = presetLevel;
        }
    }
}

int GameOptions::GetPreset() const
{
    return m_nPreset;
}

void GameOptions::ApplyOptions()
{
    // Apply options to console / engine CVars
}

void GameOptions::SaveOptions()
{
    // Write options to system.cfg
}

void GameOptions::LoadOptions()
{
    // Load from system.cfg
}

void GameOptions::ResetToDefaults()
{
    SetPreset(3);
    m_bNCPing = true;
    m_bMRT = true;
}

void GameOptions::SetGraphicOption(const char* name, int value)
{
    if (name && name[0])
    {
        m_intOptions[name] = value;
    }
}

int GameOptions::GetGraphicOption(const char* name) const
{
    if (name)
    {
        auto it = m_intOptions.find(name);
        if (it != m_intOptions.end())
            return it->second;
    }
    return 0;
}

void GameOptions::SetGraphicOptionFloat(const char* name, float value)
{
    if (name && name[0])
    {
        m_floatOptions[name] = value;
    }
}

float GameOptions::GetGraphicOptionFloat(const char* name) const
{
    if (name)
    {
        auto it = m_floatOptions.find(name);
        if (it != m_floatOptions.end())
            return it->second;
    }
    return 0.0f;
}

void GameOptions::SetResolution(int width, int height, int bpp, int refresh)
{
    if (width > 640 && height > 480)
    {
        m_nWidth = width;
        m_nHeight = height;
        m_nBPP = bpp;
        m_nRefresh = refresh;
    }
}

void GameOptions::GetResolution(int& width, int& height, int& bpp, int& refresh) const
{
    width = m_nWidth;
    height = m_nHeight;
    bpp = m_nBPP;
    refresh = m_nRefresh;
}

void GameOptions::SetFullscreen(bool bFullscreen)
{
    m_bFullscreen = bFullscreen;
}

bool GameOptions::IsFullscreen() const
{
    return m_bFullscreen;
}

void GameOptions::SetNCPingEnabled(bool bEnable)
{
    m_bNCPing = bEnable;
    if (bEnable)
    {
        OutputDebugStringA("[GameOptions] Success to set NC Ping\n");
    }
    else
    {
        OutputDebugStringA("[GameOptions] Success to canceling NC Ping\n");
    }
}

bool GameOptions::IsNCPingEnabled() const
{
    return m_bNCPing;
}

void GameOptions::SetMRTEnabled(bool bEnable)
{
    m_bMRT = bEnable;
    SetGraphicOption("r_mrt_depthrender", bEnable ? 1 : 0);
}

bool GameOptions::IsMRTEnabled() const
{
    return m_bMRT;
}

// Stubs for slots 20-77
void GameOptions::Slot20() {}
void GameOptions::Slot21() {}
void GameOptions::Slot22() {}
void GameOptions::Slot23() {}
void GameOptions::Slot24() {}
void GameOptions::Slot25() {}
void GameOptions::Slot26() {}
void GameOptions::Slot27() {}
void GameOptions::Slot28() {}
void GameOptions::Slot29() {}
void GameOptions::Slot30() {}
void GameOptions::Slot31() {}
void GameOptions::Slot32() {}
void GameOptions::Slot33() { SetNCPingEnabled(!m_bNCPing); }
void GameOptions::Slot34() {}
void GameOptions::Slot35() {}
void GameOptions::Slot36() {}
void GameOptions::Slot37() {}
void GameOptions::Slot38() {}
void GameOptions::Slot39() {}
void GameOptions::Slot40() {}
void GameOptions::Slot41() {}
void GameOptions::Slot42() {}
void GameOptions::Slot43() {}
void GameOptions::Slot44() {}
void GameOptions::Slot45() {}
void GameOptions::Slot46() {}
void GameOptions::Slot47() {}
void GameOptions::Slot48() {}
void GameOptions::Slot49() {}
void GameOptions::Slot50() {}
void GameOptions::Slot51() {}
void GameOptions::Slot52() {}
void GameOptions::Slot53() {}
void GameOptions::Slot54() {}
void GameOptions::Slot55() {}
void GameOptions::Slot56() {}
void GameOptions::Slot57() {}
void GameOptions::Slot58() {}
void GameOptions::Slot59() {}
void GameOptions::Slot60() {}
void GameOptions::Slot61() {}
void GameOptions::Slot62() {}
void GameOptions::Slot63() {}
void GameOptions::Slot64() {}
void GameOptions::Slot65() {}
void GameOptions::Slot66() {}
void GameOptions::Slot67() {}
void GameOptions::Slot68() {}
void GameOptions::Slot69() {}
void GameOptions::Slot70() {}
void GameOptions::Slot71() {}
void GameOptions::Slot72() {}
void GameOptions::Slot73() {}
void GameOptions::Slot74() {}
void GameOptions::Slot75() {}
void GameOptions::Slot76() {}
void GameOptions::Slot77() {}
