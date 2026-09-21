#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>

namespace BrService {

void LogInfo(const char* fmt, ...);
void LogError(const char* fmt, ...);

} // namespace BrService
