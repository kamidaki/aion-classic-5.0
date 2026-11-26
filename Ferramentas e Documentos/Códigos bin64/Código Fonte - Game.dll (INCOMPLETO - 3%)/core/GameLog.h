#pragma once
#include <windows.h>
#include <cstdio>

void GameLog_Init();
void GameLog_Info(const char* fmt, ...);
void GameLog_Warn(const char* fmt, ...);
void GameLog_Error(const char* fmt, ...);
