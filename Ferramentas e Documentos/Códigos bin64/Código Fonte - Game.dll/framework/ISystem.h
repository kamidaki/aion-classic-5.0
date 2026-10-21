#pragma once
#include "CryModuleDefs.h"
#include "ILog.h"
#include "IConsole.h"

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

struct IEntitySystem;
struct IScriptSystem;
struct I3DEngine;
struct IPhysicalWorld;
struct IRenderer;
struct IAnimationSystem;
struct ISoundSystem;

CRY_INTERFACE ISystem {
    virtual void Release() = 0;
    virtual bool Update(int updateFlags = 0, int nPauseMode = 0) = 0;
    virtual ILog* GetILog() = 0;
    virtual IConsole* GetIConsole() = 0;
    virtual IEntitySystem* GetIEntitySystem() = 0;
    virtual IScriptSystem* GetIScriptSystem() = 0;
    virtual I3DEngine* GetI3DEngine() = 0;
    virtual IPhysicalWorld* GetIPhysicalWorld() = 0;
    virtual IRenderer* GetIRenderer() = 0;
    virtual IAnimationSystem* GetIAnimationSystem() = 0;
    virtual ISoundSystem* GetISoundSystem() = 0;
    virtual const char* GetRootFolder() = 0;
    virtual void Quit() = 0;
};
