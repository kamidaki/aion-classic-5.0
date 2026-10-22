#include <windows.h>
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
        if (!pInitParams) return nullptr;

        CSystem* pSystem = nullptr;
        if (!pInitParams->pSystem)
        {
            pSystem = new CSystem();
        }
        else
        {
            pSystem = reinterpret_cast<CSystem*>(pInitParams->pSystem);
        }

        if (!pSystem->Init(*pInitParams))
        {
            delete pSystem;
            return nullptr;
        }

        return pSystem;
    }
}