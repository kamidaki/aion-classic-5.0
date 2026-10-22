#include <windows.h>
#include <cstdio>
#include "AionSystemCore.h"

HMODULE gDLLHandle = NULL;

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
{
    (void)lpReserved;
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        gDLLHandle = hModule;
        DisableThreadLibraryCalls(hModule);
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

extern "C"
{
    __declspec(dllexport) ISystem* __cdecl CreateSystemInterface(SSystemInitParams* pInitParams)
    {
        printf("  [CrySystem DLL] Entering CreateSystemInterface...\n"); fflush(stdout);
        if (!pInitParams) return nullptr;

        CSystem* pSystem = nullptr;
        if (!pInitParams->pSystem)
        {
            printf("  [CrySystem DLL] Instantiating new CSystem()...\n"); fflush(stdout);
            pSystem = new CSystem();
            printf("  [CrySystem DLL] Instantiated new CSystem() at %p\n", pSystem); fflush(stdout);
        }
        else
        {
            pSystem = reinterpret_cast<CSystem*>(pInitParams->pSystem);
        }

        printf("  [CrySystem DLL] Invoking pSystem->Init(*pInitParams)...\n"); fflush(stdout);
        if (!pSystem->Init(*pInitParams))
        {
            printf("  [CrySystem DLL] pSystem->Init failed!\n"); fflush(stdout);
            delete pSystem;
            return nullptr;
        }

        printf("  [CrySystem DLL] pSystem->Init succeeded!\n"); fflush(stdout);
        return pSystem;
    }
}