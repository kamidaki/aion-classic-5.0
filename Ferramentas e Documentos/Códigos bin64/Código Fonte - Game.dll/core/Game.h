#pragma once
#include "../framework/IGame.h"
#include <string>

// Objeto de jogo canônico do Aion Classic (.?AVCXGame@@)
class CXGame : public IGame {
public:
    CXGame();
    virtual ~CXGame();

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

using CGame = CXGame;
