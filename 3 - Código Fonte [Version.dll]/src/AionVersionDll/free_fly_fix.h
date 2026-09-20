#pragma once

#include <windows.h>
#include <stdint.h>
#include <stdio.h>

#if defined(_M_AMD64)

static SRWLOCK s_freeFlyLock = SRWLOCK_INIT;
static bool s_freeFlyPatched = false;

static BYTE* FreeFlyFindUnique(BYTE* base, PIMAGE_NT_HEADERS nt,
                               const BYTE* pattern, const char* mask, size_t size) {
    BYTE* found = nullptr;
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section) {
        if (!(section->Characteristics & IMAGE_SCN_MEM_EXECUTE)) continue;
        const DWORD start = section->VirtualAddress;
        const DWORD length = section->Misc.VirtualSize;
        if (start >= nt->OptionalHeader.SizeOfImage ||
            length > nt->OptionalHeader.SizeOfImage - start || length < size) continue;
        for (size_t offset = 0; offset <= length - size; ++offset) {
            BYTE* candidate = base + start + offset;
            if (candidate[0] != pattern[0]) continue;
            size_t j = 1;
            for (; j < size; ++j)
                if (mask[j] != '?' && candidate[j] != pattern[j]) break;
            if (j == size) {
                if (found) return nullptr; // Ambiguous builds are not patched.
                found = candidate;
            }
        }
    }
    return found;
}

static void InstallFreeFlyFix(HMODULE module) {
    if (!TryAcquireSRWLockExclusive(&s_freeFlyLock)) return;
    __try {
        if (s_freeFlyPatched) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Pattern 1: UIFlyGauge flight gauge button enable check (RVA 0x96a22f)
        // 48 8B 01 FF 50 08 85 C0 74 4B 48 8B CF E8 4F C6 FE FF
        static const BYTE pat1[] = {
            0x48, 0x8b, 0x01, 0xff, 0x50, 0x08, 0x85, 0xc0, 0x74, 0x4b, 0x48, 0x8b, 0xcf, 0xe8, 0x4f, 0xc6, 0xfe, 0xff
        };
        static const char mask1[] = "xxxxxxxxxxxxxxxxxx";

        // Pattern 2: UIFlyGauge wing click / takeoff permission check (RVA 0x9564b5)
        // 48 8B 01 FF 50 08 85 C0 0F 84 64 FF FF FF 48 8B 4F 08
        static const BYTE pat2[] = {
            0x48, 0x8b, 0x01, 0xff, 0x50, 0x08, 0x85, 0xc0, 0x0f, 0x84, 0x64, 0xff, 0xff, 0xff, 0x48, 0x8b, 0x4f, 0x08
        };
        static const char mask2[] = "xxxxxxxxxxxxxxxxxx";

        // Pattern 3: Player in-flight movement / no-fly zone bypass (RVA 0x161d4b)
        // 8D 5F 01 48 8B 01 FF 50 08 4C 8B 6D D0 85 C0 75 4E 8B D3
        static const BYTE pat3[] = {
            0x8d, 0x5f, 0x01, 0x48, 0x8b, 0x01, 0xff, 0x50, 0x08, 0x4c, 0x8b, 0x6d, 0xd0, 0x85, 0xc0, 0x75, 0x4e, 0x8b, 0xd3
        };
        static const char mask3[] = "xxxxxxxxxxxxxxxxxxx";

        BYTE* addr1 = FreeFlyFindUnique(base, nt, pat1, mask1, sizeof(pat1));
        BYTE* addr2 = FreeFlyFindUnique(base, nt, pat2, mask2, sizeof(pat2));
        BYTE* addr3 = FreeFlyFindUnique(base, nt, pat3, mask3, sizeof(pat3));

        if (!addr1 || !addr2 || !addr3) {
            char buf[128];
            sprintf_s(buf, "[FreeFly] Signatures not matched: addr1=%p, addr2=%p, addr3=%p\n", addr1, addr2, addr3);
            OutputDebugStringA(buf);
            __leave;
        }

        // Patch 1: NOP the conditional jump `je` (74 4B -> 90 90) at offset +8
        DWORD oldProtect1 = 0;
        if (VirtualProtect(addr1 + 8, 2, PAGE_EXECUTE_READWRITE, &oldProtect1)) {
            addr1[8] = 0x90;
            addr1[9] = 0x90;
            VirtualProtect(addr1 + 8, 2, oldProtect1, &oldProtect1);
        }

        // Patch 2: NOP the conditional jump `je` (0F 84 64 FF FF FF -> 6x 90) at offset +8
        DWORD oldProtect2 = 0;
        if (VirtualProtect(addr2 + 8, 6, PAGE_EXECUTE_READWRITE, &oldProtect2)) {
            memset(addr2 + 8, 0x90, 6);
            VirtualProtect(addr2 + 8, 6, oldProtect2, &oldProtect2);
        }

        // Patch 3: Invert conditional jump `jne` (75 4E) to unconditional `jmp` (EB 4E) at offset +15
        DWORD oldProtect3 = 0;
        if (VirtualProtect(addr3 + 15, 2, PAGE_EXECUTE_READWRITE, &oldProtect3)) {
            addr3[15] = 0xEB; // jmp
            VirtualProtect(addr3 + 15, 2, oldProtect3, &oldProtect3);
        }

        s_freeFlyPatched = true;
        OutputDebugStringA("[FreeFly] Global free flight successfully enabled on all maps!\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_freeFlyLock);
    }
}

#else

static void InstallFreeFlyFix(HMODULE /*module*/) {
    // 32-bit stub
}

#endif
