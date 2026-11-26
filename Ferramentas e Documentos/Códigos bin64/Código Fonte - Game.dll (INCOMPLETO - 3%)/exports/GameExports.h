#pragma once
#include <windows.h>
#include "../framework/IGame.h"
#include "../framework/CryModuleDefs.h"

extern "C" {
    __declspec(dllexport) IGame* CreateGameInstance(ISystem* pSystem);
    __declspec(dllexport) void CryModuleGetMemoryInfo(CryModuleMemoryInfo* pMemInfo);
}
