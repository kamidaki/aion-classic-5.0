#pragma once
#include "../framework/IGame.h"
#include <string>

class CGame : public IGame {
public:
    CGame();
    virtual ~CGame();

    // IGame implementation
    virtual bool Init(ISystem* pSystem, bool bInEditor, bool bDedicated) override;
    virtual bool Update() override;
    virtual void Shutdown() override;
    virtual void Reset() override;
    virtual bool LoadLevel(const char* szLevel, const char* szMission) override;
    virtual const char* GetName() override;
    virtual void Release() override;

private:
    bool m_bEditor;
    bool m_bDedicated;
    std::string m_gameName;
};
