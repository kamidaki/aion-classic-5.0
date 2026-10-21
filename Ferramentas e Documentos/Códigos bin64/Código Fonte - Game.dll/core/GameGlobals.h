#pragma once
#include <windows.h>
#include <atomic>
#include <typeinfo>
#include <new>
#include "../framework/ISystem.h"
#include "../framework/IGame.h"

// Referencia e ancoragem aos tipos CRT nativos presentes no RTTI original: bad_alloc, type_info
using std::bad_alloc;
using ::type_info;

struct GameGlobals {
    static HMODULE s_hModule;
    static ISystem* s_pSystem;
    static IGame*   s_pGameInstance;
    static std::atomic<bool> s_bInitialized;
    static std::atomic<bool> s_bRunning;
    static char s_szRootPath[MAX_PATH];
};

