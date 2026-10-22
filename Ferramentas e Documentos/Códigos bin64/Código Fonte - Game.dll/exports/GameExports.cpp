#include "GameExports.h"
#include "../core/Game.h"
#include "../core/GameGlobals.h"
#include "../core/GameLog.h"

extern "C" {

__declspec(dllexport) IGame* CreateGameInstance(ISystem* pSystem) {
    GameLog_Info("CreateGameInstance chamado pela CrySystem Classic 5.0 (pSystem: %p)", pSystem);

    if (!GameGlobals::s_pGameInstance) {
        GameGlobals::s_pGameInstance = new CXGame();
    }

    return GameGlobals::s_pGameInstance;
}

__declspec(dllexport) void CryModuleGetMemoryInfo(CryModuleMemoryInfo* pMemInfo) {
    if (!pMemInfo) return;
    pMemInfo->AllocatedMemory = sizeof(CXGame);
    pMemInfo->StringAllocation = 0;
    pMemInfo->CryStringAllocation = 0;
}

}
