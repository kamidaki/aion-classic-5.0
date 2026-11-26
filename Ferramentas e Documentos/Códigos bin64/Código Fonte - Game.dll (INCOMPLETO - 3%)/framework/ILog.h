#pragma once
#include "CryModuleDefs.h"

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif

enum IMiniLogType {
    M_MESSAGE = 0,
    M_WARNING = 1,
    M_ERROR   = 2,
    M_COMMENT = 3
};

CRY_INTERFACE ILog {
    virtual void Log(const char* szCommand, ...) = 0;
    virtual void LogWarning(const char* szCommand, ...) = 0;
    virtual void LogError(const char* szCommand, ...) = 0;
    virtual void Release() = 0;
};
