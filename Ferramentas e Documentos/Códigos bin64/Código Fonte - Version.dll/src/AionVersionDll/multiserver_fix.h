#pragma once

// =========================================================================
// Multi-GameServer Routing Fix for Aion Classic 5.0 (x64)
// =========================================================================
// Problem:
// In the official NCSoft client (Game.dll), when multiple GameServers share
// the same IP address (e.g. 127.0.0.1 on localhost or multi-instance servers
// on the same machine/VPS with distinct ports like 7778 and 7779), Game.dll
// builds an internal std::map<std::string, ServerEntry*> keyed by the server's
// IP string (0x18088dc10 - 0x18088dd5e).
//
// In that loop, if two servers have the same IP address, Game.dll skips
// inserting the second server (comparing serverId with jle at 0x18088dcb4),
// keeping the lowest serverId (e.g. GS ID 2) for that IP in the map.
//
// In the subsequent loop (0x18088ddb0 - 0x18088de19), Game.dll looks up the
// IP of each server entry in that map (0x18088ddd4), extracts the mapped
// serverId (0x18088de12: mov eax, [rax + 4]), and writes it into [entry + 8]
// (0x18088de15: mov [r15 + 8], eax). Consequently, GS ID 3 has its offset +8
// overwritten with GS ID 2!
//
// Then, when the user clicks on GS ID 3 in the UI server list (0x180647470),
// Game.dll executes at 0x1806474a7:
//   mov eax, dword ptr [rdx + 8]   <-- reads offset +8 instead of +4!
//   mov dword ptr [0x1815dc4a0], eax <-- writes to selected_server_to_play!
//
// The client then sends CM_PLAY with servId = 2 instead of 3, causing the
// player to be routed to GS ID 2 regardless of their visual selection.
//
// Structural Solution:
// 1. Patch 1 (UI Server Selection):
//    At 0x1806474a7: change '8B 42 08' (mov eax, [rdx + 8]) to '8B 42 04'
//    (mov eax, [rdx + 4]). Offset +4 ALWAYS contains the genuine serverId
//    received directly from the LoginServer's SM_SERVER_LIST packet.
//
// 2. Patch 2 (IP Map Group Overwrite Bypass):
//    At 0x18088de10: change '74 0C' (je +0x0C) to 'EB 0C' (jmp +0x0C).
//    This unconditionally skips the write to [r15 + 8], preventing the
//    IP grouping map from overwriting offset +8 with the lowest server ID.
// =========================================================================

#if defined(_M_AMD64)
#ifndef MULTISERVER_FIX_TEST

static volatile struct {
    char marker[16];
    LONG step;
    LONG tries;
    LONG patchedSelect;
    LONG patchedMapGroup;
    LONG patchedShardCopy;
} s_multiServerDiag = { "MSVDIAG2", 0, 0, 0, 0, 0 };

static SRWLOCK s_multiServerLock = SRWLOCK_INIT;
static bool s_multiServerChecked = false;
static volatile LONG s_multiServerRetrying = 0;
static constexpr int kMultiServerRetries = 240;
static constexpr DWORD kMultiServerRetryMs = 500;

static bool MultiServerWrite(BYTE* at, const void* data, SIZE_T size) {
    DWORD oldProtect;
    if (!VirtualProtect(at, size, PAGE_EXECUTE_READWRITE, &oldProtect)) return false;
    memcpy(at, data, size);
    VirtualProtect(at, size, oldProtect, &oldProtect);
    FlushInstructionCache(GetCurrentProcess(), at, size);
    return true;
}

static void PatchMultiServerRouting(HMODULE module);

static DWORD WINAPI MultiServerRetryThread(LPVOID module) {
    for (int i = 0; i < kMultiServerRetries && !s_multiServerChecked; ++i) {
        Sleep(kMultiServerRetryMs);
        PatchMultiServerRouting((HMODULE)module);
    }
    return 0;
}

static void InstallMultiServerFix(HMODULE module) {
    if (!module) return;
    if (InterlockedCompareExchange(&s_multiServerRetrying, 1, 0) != 0) return;
    HANDLE thread = CreateThread(nullptr, 0, MultiServerRetryThread, module, 0, nullptr);
    if (thread) CloseHandle(thread);
}

static void PatchMultiServerRouting(HMODULE module) {
    if (!module) return;
    if (!TryAcquireSRWLockExclusive(&s_multiServerLock)) return;
    __try {
        if (s_multiServerChecked) __leave;
        s_multiServerDiag.step = 1;
        InterlockedIncrement(&s_multiServerDiag.tries);

        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Signature 1: UI Server Selection
        // mov eax, [rdx + 8]; mov [rsp+290h], rbx; xor ebx, ebx; mov [rsp+298h], rsi; mov [rsp+2a0h], r14
        // 8B 42 08 48 89 9C 24 90 02 00 00 33 DB 48 89 B4 24 98 02 00 00 4C 89 B4 24 A0 02 00 00
        static const BYTE selectSig[] = {
            0x8B, 0x42, 0x08, 0x48, 0x89, 0x9C, 0x24, 0x90, 0x02, 0x00, 0x00,
            0x33, 0xDB, 0x48, 0x89, 0xB4, 0x24, 0x98, 0x02, 0x00, 0x00,
            0x4C, 0x89, 0xB4, 0x24, 0xA0, 0x02, 0x00, 0x00
        };
        static const char selectMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(selectMask) - 1 == sizeof(selectSig), "UI select signature mask length");

        // Signature 2: Server List IP Map Grouping Assignment
        // mov rax, [rsi + 40h]; test rax, rax; je +0Ch; mov eax, [rax + 4]; mov [r15 + 8], eax; mov r13, [rsp + 40h]
        // 48 8B 46 40 48 85 C0 74 0C 8B 40 04 41 89 47 08 4C 8B 6C 24 40
        static const BYTE mapGroupSig[] = {
            0x48, 0x8B, 0x46, 0x40, 0x48, 0x85, 0xC0, 0x74, 0x0C,
            0x8B, 0x40, 0x04, 0x41, 0x89, 0x47, 0x08, 0x4C, 0x8B, 0x6C, 0x24, 0x40
        };
        static const char mapGroupMask[] = "xxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(mapGroupMask) - 1 == sizeof(mapGroupSig), "Map group signature mask length");

        // Signature 3: Shard Copy Loop (0x18088df08)
        // mov eax, [r14 + 8]; cmp [r14 + 4], eax; je +0x5D; mov rdi, [r13 + 8]
        // 41 8B 46 08 41 39 46 04 74 5D 49 8B 7D 08
        static const BYTE shardCopySig[] = {
            0x41, 0x8B, 0x46, 0x08, 0x41, 0x39, 0x46, 0x04, 0x74, 0x5D, 0x49, 0x8B, 0x7D, 0x08
        };
        static const char shardCopyMask[] = "xxxxxxxxxxxxxx";
        static_assert(sizeof(shardCopyMask) - 1 == sizeof(shardCopySig), "Shard copy signature mask length");

        BYTE* selectAt = QunaFindUnique(base, nt, selectSig, selectMask, sizeof(selectSig));
        BYTE* mapGroupAt = QunaFindUnique(base, nt, mapGroupSig, mapGroupMask, sizeof(mapGroupSig));
        BYTE* shardCopyAt = QunaFindUnique(base, nt, shardCopySig, shardCopyMask, sizeof(shardCopySig));

        if (!selectAt || !mapGroupAt || !shardCopyAt) {
            s_multiServerDiag.step = 2;
            __leave;
        }

        // Patch 1: change [rdx + 8] to [rdx + 4] at offset 2 (8B 42 08 -> 8B 42 04)
        static const BYTE newOffset = 0x04;
        if (MultiServerWrite(selectAt + 2, &newOffset, sizeof(newOffset))) {
            s_multiServerDiag.patchedSelect = 1;
        }

        // Patch 2: replace the lowest-serverId map overwrite with direct self-identity assignment:
        // mov eax, [r15 + 4] (real serverId)
        // mov [r15 + 8], eax
        // 8x nop
        static const BYTE selfIdAssignCode[16] = {
            0x41, 0x8B, 0x47, 0x04,                         // mov eax, dword ptr [r15 + 4]
            0x41, 0x89, 0x47, 0x08,                         // mov dword ptr [r15 + 8], eax
            0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90  // nop nop nop nop nop nop nop nop
        };
        if (MultiServerWrite(mapGroupAt, selfIdAssignCode, sizeof(selfIdAssignCode))) {
            s_multiServerDiag.patchedMapGroup = 1;
        }

        // Patch 3: change 'je +0x5D' (74 5D) to 'jmp +0x5D' (EB 5D) at offset 8 in shardCopySig.
        // This unconditionally skips 0x18089c550, preventing Game.dll from ever overwriting
        // secondary GameServers' ports (e.g. port 7779 -> 7778), character counts, or properties.
        static const BYTE jmpOpcode = 0xEB;
        if (MultiServerWrite(shardCopyAt + 8, &jmpOpcode, sizeof(jmpOpcode))) {
            s_multiServerDiag.patchedShardCopy = 1;
        }

        if (s_multiServerDiag.patchedSelect && s_multiServerDiag.patchedMapGroup && s_multiServerDiag.patchedShardCopy) {
            s_multiServerChecked = true;
            s_multiServerDiag.step = 3;
            OutputDebugStringA("[Multi-Server] Multi-GameServer routing fix applied successfully (UI selection, self-identity GS ID, and shard copy bypass).\n");
        }
    }
    __finally {
        ReleaseSRWLockExclusive(&s_multiServerLock);
    }
}
#endif // MULTISERVER_FIX_TEST
#else
static void InstallMultiServerFix(HMODULE) {}
#endif // _M_AMD64
