#pragma once
#include "CryModuleDefs.h"
#include "ISystem.h"

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

CRY_INTERFACE IGame {
    virtual ~IGame() {}
    virtual bool Init(ISystem* pSystem, bool bInEditor, bool bDedicated) = 0;
    virtual bool Update() = 0;
    virtual void Shutdown() = 0;
    virtual void Reset() = 0;
    virtual bool LoadLevel(const char* szLevel, const char* szMission) = 0;
    virtual const char* GetName() = 0;
    virtual void Release() = 0;
};
