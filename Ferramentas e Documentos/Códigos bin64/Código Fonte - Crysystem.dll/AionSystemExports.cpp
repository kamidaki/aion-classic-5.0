#include <windows.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>

// Forward declaration
struct ISystem;
struct SSystemInitParams;
ISystem* CreateSystem(const SSystemInitParams& params);

// Global memory statistics tracked for CryModuleGetMemoryInfo
static uint64_t g_nAllocatedBytes = 0;
static uint64_t g_nAllocatedPeak = 0;
static uint32_t g_nAllocatedCount = 0;
static uint32_t g_nPoolCRTCountBig = 0;
static uint32_t g_nAllocatedCRTSize = 0;
static uint32_t g_nAllocatedCacheSize = 0;
static uint32_t g_nAllocatedInScriptSize = 0;
static uint32_t g_nAllocatedPagesSize = 0;

struct CryModuleMemoryInfo
{
    uint64_t allocated;
    uint64_t peak;
    uint32_t count;
};

// C++ mangled memory exports (Ordinals 1-17)

// Ordinal 1: ?CheckMemory@@YAHH@Z
__declspec(dllexport) int __cdecl CheckMemory(int param)
{
    (void)param;
    return 0;
}

// Ordinal 2: ?CryMemoryGetAlloc16kCacheCounter@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetAlloc16kCacheCounter(int param)
{
    (void)param;
    return 0;
}

// Ordinal 3: ?CryMemoryGetAlloc16kCacheSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAlloc16kCacheSize()
{
    return 0x2f; // 47
}

// Ordinal 4: ?CryMemoryGetAlloc16kFreeCounter@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetAlloc16kFreeCounter(int param)
{
    if (param > 0x2e) return 0;
    return 0;
}

// Ordinal 5: ?CryMemoryGetAllocCount@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetAllocCount(int param)
{
    (void)param;
    return 0;
}

// Ordinal 6: ?CryMemoryGetAllocatedCRTSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAllocatedCRTSize()
{
    return static_cast<int>(g_nAllocatedCRTSize);
}

// Ordinal 7: ?CryMemoryGetAllocatedCacheSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAllocatedCacheSize()
{
    return static_cast<int>(g_nAllocatedCacheSize);
}

// Ordinal 8: ?CryMemoryGetAllocatedInScriptSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAllocatedInScriptSize()
{
    return static_cast<int>(g_nAllocatedInScriptSize);
}

// Ordinal 9: ?CryMemoryGetAllocatedPagesSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAllocatedPagesSize()
{
    return static_cast<int>(g_nAllocatedPagesSize);
}

// Ordinal 10: ?CryMemoryGetAllocatedSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetAllocatedSize()
{
    return static_cast<int>(g_nAllocatedBytes);
}

// Ordinal 11: ?CryMemoryGetFreePagesCount@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetFreePagesCount()
{
    return 64;
}

// Ordinal 12: ?CryMemoryGetPoolCRTCount32@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetPoolCRTCount32(int param)
{
    if (param > 0x2e) return 0;
    return param * 8;
}

// Ordinal 13: ?CryMemoryGetPoolCRTCount32Big@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetPoolCRTCount32Big(int param)
{
    if (param > 0xc8) return 0;
    return param * 16;
}

// Ordinal 14: ?CryMemoryGetPoolCRTCountBig@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetPoolCRTCountBig()
{
    return static_cast<int>(g_nPoolCRTCountBig);
}

// Ordinal 15: ?CryMemoryGetPoolCRTSize32@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetPoolCRTSize32(int param)
{
    if (param > 0x2e) return 0;
    return param * 32;
}

// Ordinal 16: ?CryMemoryGetPoolSize@@YAHXZ
__declspec(dllexport) int __cdecl CryMemoryGetPoolSize()
{
    return 0x20000; // 131072 (128 KB)
}

// Ordinal 17: ?CryMemoryGetReuseCount@@YAHH@Z
__declspec(dllexport) int __cdecl CryMemoryGetReuseCount(int param)
{
    (void)param;
    return 0;
}

// Ordinal 18: CreateSystemInterface is implemented in DllMain.cpp

extern "C" {

// Ordinal 19: CryCalloc
__declspec(dllexport) void* __cdecl CryCalloc(size_t num, size_t size)
{
    size_t total = num * size;
    if (total == 0) return nullptr;
    void* ptr = calloc(num, size);
    if (ptr)
    {
        g_nAllocatedBytes += total;
        if (g_nAllocatedBytes > g_nAllocatedPeak)
            g_nAllocatedPeak = g_nAllocatedBytes;
        g_nAllocatedCount++;
    }
    return ptr;
}

// Ordinal 20: CryFlushAll
__declspec(dllexport) void __cdecl CryFlushAll()
{
    // Flushes intermediate caches
}

// Ordinal 21: CryFree
__declspec(dllexport) void __cdecl CryFree(void* ptr)
{
    if (ptr)
    {
        if (g_nAllocatedCount > 0)
            g_nAllocatedCount--;
        free(ptr);
    }
}

// Ordinal 22: CryFreeSize
__declspec(dllexport) void __cdecl CryFreeSize(void* ptr, size_t size)
{
    if (g_nAllocatedBytes >= size)
        g_nAllocatedBytes -= size;
    CryFree(ptr);
}

// Ordinal 23: CryMalloc
__declspec(dllexport) void* __cdecl CryMalloc(size_t size)
{
    if (size == 0) return nullptr;
    void* ptr = malloc(size);
    if (ptr)
    {
        g_nAllocatedBytes += size;
        if (g_nAllocatedBytes > g_nAllocatedPeak)
            g_nAllocatedPeak = g_nAllocatedBytes;
        g_nAllocatedCount++;
    }
    return ptr;
}

// Ordinal 24: CryModuleGetMemoryInfo
__declspec(dllexport) void __cdecl CryModuleGetMemoryInfo(CryModuleMemoryInfo* pMemInfo)
{
    if (pMemInfo)
    {
        pMemInfo->allocated = g_nAllocatedBytes;
        pMemInfo->peak = g_nAllocatedPeak;
        pMemInfo->count = g_nAllocatedCount;
    }
}

// Ordinal 25: CryRealloc
__declspec(dllexport) void* __cdecl CryRealloc(void* ptr, size_t size)
{
    if (!ptr) return CryMalloc(size);
    if (size == 0) { CryFree(ptr); return nullptr; }
    return realloc(ptr, size);
}

// Ordinal 26: CryReallocSize
__declspec(dllexport) void* __cdecl CryReallocSize(void* ptr, size_t oldSize, size_t newSize)
{
    if (g_nAllocatedBytes >= oldSize)
        g_nAllocatedBytes -= oldSize;
    g_nAllocatedBytes += newSize;
    if (g_nAllocatedBytes > g_nAllocatedPeak)
        g_nAllocatedPeak = g_nAllocatedBytes;
    return realloc(ptr, newSize);
}

// Ordinal 27: CryStats
__declspec(dllexport) void __cdecl CryStats(char* buffer)
{
    if (buffer)
    {
        sprintf_s(buffer, 256, "CryMemory: Allocated = %llu KB, Peak = %llu KB, Blocks = %u",
                  g_nAllocatedBytes / 1024, g_nAllocatedPeak / 1024, g_nAllocatedCount);
    }
}

// CryModule internal memory functions
void* CryModuleMalloc(size_t size) throw() { return CryMalloc(size); }
void* CryModuleRealloc(void* ptr, size_t size) throw() { return CryRealloc(ptr, size); }
void  CryModuleFree(void* ptr) throw() { CryFree(ptr); }
void* CryModuleReallocSize(void* ptr, size_t oldsize, size_t size) { return CryReallocSize(ptr, oldsize, size); }
void  CryModuleFreeSize(void* ptr, size_t size) { CryFreeSize(ptr, size); }

} // extern "C"
