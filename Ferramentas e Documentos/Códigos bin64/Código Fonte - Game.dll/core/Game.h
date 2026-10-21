#pragma once
#include "../framework/IGame.h"
#include "../framework/IXGame.h"
#include "../framework/IConsoleSink.h"
#include "../framework/IInputEventListener.h"
#include <string>

// Objeto de jogo canônico mestre do Aion Classic (.?AVCXGame@@)
// Herança canônica validada via RTTI: CXGame -> IXGame, IGame, IConsoleSink, IInputEventListener
class CXGame : public IXGame, public IGame, public IConsoleSink, public IInputEventListener {
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

    // IXGame implementation
    virtual bool Init() override;

    // IConsoleSink implementation
    virtual void OnConsoleCommand(const char* szCommand) override;

    // IInputEventListener implementation
    virtual bool OnInputEvent(void* pEvent) override;

private:
    bool m_bEditor;
    bool m_bDedicated;
    std::string m_gameName;
};

using CGame = CXGame;
