#include "GameGlobals.h"

HMODULE GameGlobals::s_hModule = nullptr;
ISystem* GameGlobals::s_pSystem = nullptr;
IGame*   GameGlobals::s_pGameInstance = nullptr;
std::atomic<bool> GameGlobals::s_bInitialized{false};
std::atomic<bool> GameGlobals::s_bRunning{false};
char GameGlobals::s_szRootPath[MAX_PATH] = {0};
