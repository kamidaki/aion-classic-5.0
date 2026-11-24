#include "CharacterLODManager.h"

CharacterLODManager::CharacterLODManager()
    : m_bEnabled(true),
      m_bSiegeMode(false),
      m_nMaxVisibleChars(100),
      m_fNearDist(15.0f),
      m_fMidDist(35.0f),
      m_fFarDist(70.0f),
      m_fUpdateTimer(0.0f)
{
}

CharacterLODManager::~CharacterLODManager()
{
}

bool CharacterLODManager::IsLODEnabled()
{
    return m_bEnabled;
}

void CharacterLODManager::SetMaxVisibleCharacters(int maxChars)
{
    if (maxChars < 10) maxChars = 10;
    if (maxChars > 500) maxChars = 500;
    m_nMaxVisibleChars = maxChars;
}

int CharacterLODManager::GetMaxVisibleCharacters() const
{
    return m_nMaxVisibleChars;
}

void CharacterLODManager::SetLODDistances(float nearDist, float midDist, float farDist)
{
    m_fNearDist = nearDist;
    m_fMidDist = midDist;
    m_fFarDist = farDist;
}

void CharacterLODManager::GetLODDistances(float& nearDist, float& midDist, float& farDist) const
{
    nearDist = m_fNearDist;
    midDist = m_fMidDist;
    farDist = m_fFarDist;
}

void CharacterLODManager::SetSiegeOptimization(bool bEnable)
{
    m_bSiegeMode = bEnable;
    if (bEnable)
    {
        // Aggressive LOD in large RvR battles
        m_nMaxVisibleChars = 50;
        m_fNearDist = 10.0f;
        m_fMidDist = 25.0f;
        m_fFarDist = 50.0f;
    }
    else
    {
        m_nMaxVisibleChars = 100;
        m_fNearDist = 15.0f;
        m_fMidDist = 35.0f;
        m_fFarDist = 70.0f;
    }
}

bool CharacterLODManager::IsSiegeOptimizationEnabled() const
{
    return m_bSiegeMode;
}

void CharacterLODManager::Update(float dt)
{
    m_fUpdateTimer += dt;
    if (m_fUpdateTimer >= 0.1f)
    {
        m_fUpdateTimer = 0.0f;
        // Periodic LOD calculation cycle
    }
}
