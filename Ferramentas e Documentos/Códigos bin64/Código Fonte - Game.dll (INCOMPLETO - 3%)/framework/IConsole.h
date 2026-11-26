#pragma once
#include "CryModuleDefs.h"

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

CRY_INTERFACE IConsole {
    virtual void PrintLine(const char* s) = 0;
    virtual void ShowConsole(bool show) = 0;
    virtual int  GetNumVars() = 0;
    virtual void ExecuteString(const char* command, bool bSilentMode = false, bool bDeferExecution = false) = 0;
};
