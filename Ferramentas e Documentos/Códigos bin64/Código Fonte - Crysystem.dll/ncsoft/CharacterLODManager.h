#pragma once

#ifndef _CHARACTERLODMANAGER_H_
#define _CHARACTERLODMANAGER_H_

class CharacterLODManager
{
public:
    CharacterLODManager();
    virtual ~CharacterLODManager();

    virtual bool IsLODEnabled();

    void  SetMaxVisibleCharacters(int maxChars);
    int   GetMaxVisibleCharacters() const;
    void  SetLODDistances(float nearDist, float midDist, float farDist);
    void  GetLODDistances(float& nearDist, float& midDist, float& farDist) const;
    void  SetSiegeOptimization(bool bEnable);
    bool  IsSiegeOptimizationEnabled() const;
    void  Update(float dt);

private:
    bool  m_bEnabled;
    bool  m_bSiegeMode;
    int   m_nMaxVisibleChars;
    float m_fNearDist;
    float m_fMidDist;
    float m_fFarDist;
    float m_fUpdateTimer;
};

#endif // _CHARACTERLODMANAGER_H_
