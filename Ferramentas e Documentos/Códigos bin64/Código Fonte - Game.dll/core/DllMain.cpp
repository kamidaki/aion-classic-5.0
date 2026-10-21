#include <windows.h>
#include "GameGlobals.h"
#include "GameLog.h"

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        GameGlobals::s_hModule = hModule;
        GameLog_Init();
        GameLog_Info("Game.dll DLL_PROCESS_ATTACH disparado (Base: %p)", hModule);
        break;

    case DLL_PROCESS_DETACH:
        GameLog_Info("Game.dll DLL_PROCESS_DETACH disparado");
        if (GameGlobals::s_pGameInstance) {
            GameGlobals::s_pGameInstance->Shutdown();
            GameGlobals::s_pGameInstance->Release();
            GameGlobals::s_pGameInstance = nullptr;
        }
        break;
    }
    return TRUE;
}
