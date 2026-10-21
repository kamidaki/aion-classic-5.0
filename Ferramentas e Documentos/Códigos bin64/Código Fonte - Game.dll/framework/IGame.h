#pragma once
#include "CryModuleDefs.h"
#include "ISystem.h"

// Interface CryEngine de processo (.?AUIProcess@@)
struct IProcess {
    virtual ~IProcess() {}
    virtual void Process() = 0;
};

// Interface CryEngine de motor de jogo (.?AUIGame@@)
struct IGame : public IProcess {
    virtual ~IGame() {}
    virtual bool Init(ISystem* pSystem, bool bInEditor, bool bDedicated) = 0;
    virtual bool Update() = 0;
    virtual void Shutdown() = 0;
    virtual void Reset() = 0;
    virtual bool LoadLevel(const char* szLevel, const char* szMission) = 0;
    virtual const char* GetName() = 0;
    virtual void Release() = 0;
    virtual void Process() override {}
};
