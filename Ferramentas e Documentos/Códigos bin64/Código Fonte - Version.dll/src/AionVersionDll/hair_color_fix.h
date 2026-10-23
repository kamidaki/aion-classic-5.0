#pragma once

// Classic 5.0 x64: the customization screen (character creation, Aion Look, plastic surgery) greys out
// the hair color with the "Inactive_hair_color" cover (STR_DLG_CUSTOM_HAIR_COLOR_SPECIAL_DIMMED) and
// disables the color buttons and the picker while the chosen hair is a special one (20000..29999, the
// special dye hairstyles df20001_hair...). Game.dll 0x32b882:
//   movzx ebx, word [rip+hair]; mov eax, 4E20h; mov rcx, [rsi+1490h]; sub bx, ax; mov r14d, 270Fh
// then three "cmp bx, r14w" pick show/hide. Changing the 4E20h (20000) to 9C40h (40000) makes
// hair - 40000 (16 bits) land in 25536..58303 for every hair 0..32767, never in 0..9999: the screen
// treats every hairstyle as an ordinary one. Only this screen; the mesh choice at 0x397910 is untouched.
//
// Hair dye item (Game.dll 0x81266c): with a hair dye on a hair of 20000..29999 (0x366c70) the client
// refuses with STR_UI_EDIT_CHAR_HAIR_SPECIAL_ITEM_USE_CONFIRM_INVEN (909413) and sends nothing:
//   movzx ecx, word [rax+11h]; mov eax, 4E20h; mov [rbp+10F8h], cx; cmp cx, ax; jb ordinary
// The jb becomes a jmp, so the dye goes on as on any other hairstyle.
#if defined(_M_AMD64)
#ifndef HAIR_COLOR_FIX_TEST
// Where the installation stopped, next to the "HCDIAG1" marker: 1 started, 2 signatures not found yet,
// 3 patched; tries = attempts; dye = 1 when the hair dye check was patched too.
static volatile struct { char marker[8]; LONG step; LONG tries; LONG dye; } s_hairColorDiag = { "HCDIAG1", 0, 0, 0 };
static SRWLOCK s_hairColorLock = SRWLOCK_INIT;
static bool s_hairColorChecked = false;
// Game.dll is unpacked by WinLicense while it loads, and writing into it during the load fails the DLL
// initialization (error 1114): only a thread of its own patches it, a moment later, retrying for two
// minutes like the Global Trade fix.
static volatile LONG s_hairColorRetrying = 0;
static constexpr int kHairColorRetries = 240;
static constexpr DWORD kHairColorRetryMs = 500;
static constexpr int kHairColorImmediate = 8; // offset of the 4E20h inside the signature
static constexpr int kHairDyeJump = 19;        // offset of the jb inside the dye signature

static bool HairColorWrite(BYTE* at, const void* data, SIZE_T size) {
    DWORD old;
    if (!VirtualProtect(at, size, PAGE_EXECUTE_READWRITE, &old)) return false;
    memcpy(at, data, size);
    VirtualProtect(at, size, old, &old);
    FlushInstructionCache(GetCurrentProcess(), at, size);
    return true;
}
static void PatchHairColorDim(HMODULE module);

static DWORD WINAPI HairColorRetryThread(LPVOID module) {
    for (int i = 0; i < kHairColorRetries && !s_hairColorChecked; ++i) {
        Sleep(kHairColorRetryMs);
        PatchHairColorDim((HMODULE)module);
    }
    return 0;
}

static void InstallHairColorFix(HMODULE module) {
    if (InterlockedCompareExchange(&s_hairColorRetrying, 1, 0) != 0) return;
    HANDLE thread = CreateThread(nullptr, 0, HairColorRetryThread, module, 0, nullptr);
    if (thread) CloseHandle(thread);
}

static void PatchHairColorDim(HMODULE module) {
    if (!TryAcquireSRWLockExclusive(&s_hairColorLock)) return;
    __try {
        if (s_hairColorChecked) __leave;
        s_hairColorDiag.step = 1;
        InterlockedIncrement(&s_hairColorDiag.tries);
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // movzx ebx, word [rip+x]; mov eax, 4E20h; mov rcx, [rsi+1490h]; sub bx, ax; mov r14d, 270Fh;
        // mov r15d, 1; test rcx, rcx
        static const BYTE dim[] = {
            0x0f,0xb7,0x1d,0,0,0,0,0xb8,0x20,0x4e,0x00,0x00,0x48,0x8b,0x8e,0x90,0x14,0x00,0x00,
            0x66,0x2b,0xd8,0x41,0xbe,0x0f,0x27,0x00,0x00,0x41,0xbf,0x01,0x00,0x00,0x00,0x48,0x85,0xc9
        };
        static const char dimMask[] = "xxx????xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(dimMask) - 1 == sizeof(dim), "Hair color signature mask length");
        // movzx ecx, word [rax+11h]; mov eax, 4E20h; mov [rbp+10F8h], cx; cmp cx, ax; jb +95h
        static const BYTE dye[] = {
            0x0f,0xb7,0x48,0x11,0xb8,0x20,0x4e,0x00,0x00,0x66,0x89,0x8d,0xf8,0x10,0x00,0x00,
            0x66,0x3b,0xc8,0x0f,0x82,0x95,0x00,0x00,0x00
        };
        static const char dyeMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(dyeMask) - 1 == sizeof(dye), "Hair dye signature mask length");
        BYTE* at = QunaFindUnique(base, nt, dim, dimMask, sizeof(dim));
        BYTE* dyeAt = QunaFindUnique(base, nt, dye, dyeMask, sizeof(dye));
        if (!at || !dyeAt) { s_hairColorDiag.step = 2; __leave; }

        static const DWORD notSpecial = 40000;
        if (!HairColorWrite(at + kHairColorImmediate, &notSpecial, sizeof(notSpecial))) __leave;
        // jb rel32 (6 bytes) -> jmp rel32 (5 bytes) + nop, to the same target
        static const BYTE always[] = { 0xe9, 0x96, 0x00, 0x00, 0x00, 0x90 };
        if (HairColorWrite(dyeAt + kHairDyeJump, always, sizeof(always))) s_hairColorDiag.dye = 1;
        s_hairColorChecked = true;
        s_hairColorDiag.step = 3;
        OutputDebugStringA("[Hair color] Special hairstyles can be colored.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_hairColorLock);
    }
}
#endif
#else
static void InstallHairColorFix(HMODULE) {}
#endif
