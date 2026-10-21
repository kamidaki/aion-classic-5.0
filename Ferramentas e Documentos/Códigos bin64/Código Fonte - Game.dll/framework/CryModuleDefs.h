#pragma once
#include <windows.h>
#include <cstdint>

// Estrutura padrão de alocação de memória reportada à CrySystem
struct CryModuleMemoryInfo {
    uint64_t AllocatedMemory;
    uint64_t StringAllocation;
    uint64_t CryStringAllocation;
    uint64_t Reserved[5];
};

#ifndef CRY_INTERFACE
#define CRY_INTERFACE struct
#endif
