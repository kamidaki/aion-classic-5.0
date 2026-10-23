#include "LITELauncherManager.h"
#include <cstring>

LITELauncherManager::LITELauncherManager()
    : m_bLaunchedFromLauncher(false)
{
    m_szToken[0] = '\0';
}

LITELauncherManager::~LITELauncherManager()
{
}

bool LITELauncherManager::Init()
{
    return true;
}

void LITELauncherManager::Shutdown()
{
    m_bLaunchedFromLauncher = false;
    m_szToken[0] = '\0';
}

bool LITELauncherManager::IsLaunchedFromLauncher() const
{
    return m_bLaunchedFromLauncher;
}

const char* LITELauncherManager::GetLauncherToken() const
{
    return m_szToken;
}

void LITELauncherManager::SetLauncherToken(const char* token)
{
    if (token)
    {
        strncpy_s(m_szToken, sizeof(m_szToken), token, _TRUNCATE);
        m_bLaunchedFromLauncher = true;
    }
}
