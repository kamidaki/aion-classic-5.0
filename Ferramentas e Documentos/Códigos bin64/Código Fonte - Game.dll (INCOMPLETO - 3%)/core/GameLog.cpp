#include "GameLog.h"
#include "GameGlobals.h"
#include "../framework/ILog.h"
#include <cstdarg>

static CRITICAL_SECTION s_logCs;
static bool s_csInit = false;

void GameLog_Init() {
    if (!s_csInit) {
        InitializeCriticalSection(&s_logCs);
        s_csInit = true;
    }
}

static void LogOutput(const char* prefix, const char* fmt, va_list args) {
    char buf[2048];
    vsnprintf(buf, sizeof(buf), fmt, args);

    if (s_csInit) EnterCriticalSection(&s_logCs);

    char fullMsg[2300];
    snprintf(fullMsg, sizeof(fullMsg), "[Game.dll] %s %s\n", prefix, buf);
    OutputDebugStringA(fullMsg);

    if (GameGlobals::s_pSystem && GameGlobals::s_pSystem->GetILog()) {
        GameGlobals::s_pSystem->GetILog()->Log("[Game.dll] %s %s", prefix, buf);
    }

    if (s_csInit) LeaveCriticalSection(&s_logCs);
}

void GameLog_Info(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    LogOutput("[INFO]", fmt, args);
    va_end(args);
}

void GameLog_Warn(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    LogOutput("[WARN]", fmt, args);
    va_end(args);
}

void GameLog_Error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    LogOutput("[ERROR]", fmt, args);
    va_end(args);
}
