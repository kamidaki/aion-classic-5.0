#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks = 0;
static void Check(bool condition, const char* msg) {
    ++checks;
    if (!condition) {
        fprintf(stderr, "FAIL check %u: %s\n", checks, msg);
        exit(1);
    }
}

// Signatures from multiserver_fix.h
static const BYTE selectSig[] = {
    0x8B, 0x42, 0x08, 0x48, 0x89, 0x9C, 0x24, 0x90, 0x02, 0x00, 0x00,
    0x33, 0xDB, 0x48, 0x89, 0xB4, 0x24, 0x98, 0x02, 0x00, 0x00,
    0x4C, 0x89, 0xB4, 0x24, 0xA0, 0x02, 0x00, 0x00
};
static const char selectMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx";

static const BYTE mapGroupSig[] = {
    0x48, 0x8B, 0x46, 0x40, 0x48, 0x85, 0xC0, 0x74, 0x0C,
    0x8B, 0x40, 0x04, 0x41, 0x89, 0x47, 0x08, 0x4C, 0x8B, 0x6C, 0x24, 0x40
};
static const char mapGroupMask[] = "xxxxxxxxxxxxxxxxxxxxx";

static BYTE* MockFindPattern(BYTE* buffer, size_t bufSize, const BYTE* pattern, const char* mask, size_t patSize) {
    if (bufSize < patSize) return nullptr;
    for (size_t i = 0; i <= bufSize - patSize; ++i) {
        bool match = true;
        for (size_t j = 0; j < patSize; ++j) {
            if (mask[j] == 'x' && buffer[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match) return buffer + i;
    }
    return nullptr;
}

int main() {
    printf("[*] Running multiserver_fix unit checks...\n");

    // Test 1: Verify signature lengths and masks match exactly
    Check(sizeof(selectSig) == 29, "selectSig length is 29");
    Check(strlen(selectMask) == sizeof(selectSig), "selectMask matches selectSig length");
    Check(sizeof(mapGroupSig) == 21, "mapGroupSig length is 21");
    Check(strlen(mapGroupMask) == sizeof(mapGroupSig), "mapGroupMask matches mapGroupSig length");

    // Test 2: Verify original opcode semantics
    // In selectSig: 8B 42 08 is 'mov eax, [rdx + 8]' -> offset is 8
    Check(selectSig[0] == 0x8B && selectSig[1] == 0x42 && selectSig[2] == 0x08, "selectSig starts with mov eax, [rdx + 8]");
    // In mapGroupSig: 74 0C is 'je +0x0C' -> conditional jump
    Check(mapGroupSig[7] == 0x74 && mapGroupSig[8] == 0x0C, "mapGroupSig has je +0x0C at offset 7");

    // Test 3: Simulate memory buffer with code stream containing both routines
    BYTE codeBuffer[256];
    memset(codeBuffer, 0x90, sizeof(codeBuffer)); // NOP sled

    // Embed selectSig at offset 32
    memcpy(codeBuffer + 32, selectSig, sizeof(selectSig));
    // Embed mapGroupSig at offset 128
    memcpy(codeBuffer + 128, mapGroupSig, sizeof(mapGroupSig));

    // Search for patterns
    BYTE* selectFound = MockFindPattern(codeBuffer, sizeof(codeBuffer), selectSig, selectMask, sizeof(selectSig));
    BYTE* mapGroupFound = MockFindPattern(codeBuffer, sizeof(codeBuffer), mapGroupSig, mapGroupMask, sizeof(mapGroupSig));
    Check(selectFound == codeBuffer + 32, "MockFindPattern found selectSig at expected offset 32");
    Check(mapGroupFound == codeBuffer + 128, "MockFindPattern found mapGroupSig at expected offset 128");

    // Apply Patch 1: replace [rdx + 8] with [rdx + 4] at offset 2
    BYTE newOffset = 0x04;
    selectFound[2] = newOffset;
    Check(selectFound[2] == 0x04, "Patch 1 applied: offset 2 is now 0x04 (mov eax, [rdx + 4])");
    Check(selectFound[0] == 0x8B && selectFound[1] == 0x42, "Patch 1 preserved opcode 8B 42");
    Check(selectFound[3] == 0x48 && selectFound[4] == 0x89, "Patch 1 preserved following instructions");

    // Apply Patch 2: replace 'je +0Ch' (74 0C) with 'jmp +0Ch' (EB 0C) at offset 7
    BYTE jmpOpcode = 0xEB;
    mapGroupFound[7] = jmpOpcode;
    Check(mapGroupFound[7] == 0xEB, "Patch 2 applied: offset 7 is now 0xEB (jmp +0x0C)");
    Check(mapGroupFound[8] == 0x0C, "Patch 2 preserved jump displacement +0x0C");
    Check(mapGroupFound[0] == 0x48 && mapGroupFound[1] == 0x8B, "Patch 2 preserved preceding instructions");

    // Test 4: Verify unpatched pattern is no longer found with original signatures
    BYTE* selectRetry = MockFindPattern(codeBuffer, sizeof(codeBuffer), selectSig, selectMask, sizeof(selectSig));
    BYTE* mapGroupRetry = MockFindPattern(codeBuffer, sizeof(codeBuffer), mapGroupSig, mapGroupMask, sizeof(mapGroupSig));
    Check(selectRetry == nullptr, "Original selectSig not found after patch (idempotent / already patched)");
    Check(mapGroupRetry == nullptr, "Original mapGroupSig not found after patch (idempotent / already patched)");

    // Test 5: Verify buffer integrity outside patch locations
    for (size_t i = 0; i < 32; ++i) {
        Check(codeBuffer[i] == 0x90, "Buffer before selectSig is untouched");
    }
    for (size_t i = 32 + sizeof(selectSig); i < 128; ++i) {
        Check(codeBuffer[i] == 0x90, "Buffer between routines is untouched");
    }
    for (size_t i = 128 + sizeof(mapGroupSig); i < sizeof(codeBuffer); ++i) {
        Check(codeBuffer[i] == 0x90, "Buffer after mapGroupSig is untouched");
    }

    printf("multiserver_fix_checks: ALL %u checks PASSED successfully!\n", checks);
    return 0;
}
