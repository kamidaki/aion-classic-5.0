#pragma once

// Classic 5.0 x64: successful disassembly closes DlgItemCrush while its
// progress flag is still set. ResetProgress then emits the local Stop message.
// Keep the automatic C_CANCEL_ITEM_CRUSH handshake; clear the flag only when
// ResetProgress runs inside the successful result dialog helper.
#if defined(_M_AMD64)
using HammerShowResult = void (__fastcall*)(void*, void*, bool);
using HammerResetProgress = void (__fastcall*)(void*);
static HammerShowResult s_hammerShowResult = nullptr;
static HammerResetProgress s_hammerResetProgress = nullptr;
static thread_local unsigned s_hammerSuccessDepth = 0;

static void __fastcall HammerShowSuccessfulResult(void* context, void* items, bool bonus) {
    const unsigned previous = s_hammerSuccessDepth;
    s_hammerSuccessDepth = previous + 1;
    __try {
        s_hammerShowResult(context, items, bonus);
    }
    __finally {
        s_hammerSuccessDepth = previous;
    }
}

static void __fastcall HammerResetAfterResult(void* dialog) {
    if (s_hammerSuccessDepth && dialog)
        *((BYTE*)dialog + 0x524) = 0;
    s_hammerResetProgress(dialog);
}

#ifndef SIEL_HAMMER_FIX_TEST
static SRWLOCK s_hammerLock = SRWLOCK_INIT;
static bool s_hammerChecked = false;

static BYTE* HammerFindUnique(BYTE* base, PIMAGE_NT_HEADERS nt,
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

static void InstallSielHammerFix(HMODULE module) {
    // LoadLibrary hooks can reenter while Detours allocates its trampoline.
    if (!TryAcquireSRWLockExclusive(&s_hammerLock)) return;
    __try {
        if (s_hammerChecked) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        static const BYTE show[] = {
            0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x4c,0x24,0x08,0x57,
            0x48,0x83,0xec,0x30,0x48,0x8b,0x0d,0,0,0,0,0x4c,0x8d,0x0d,0,0,0,0,
            0x41,0x0f,0xb6,0xf0,0xc7,0x44,0x24,0x20,0,0,0,0
        };
        static const char showMask[] = "xxxxxxxxxxxxxxxxxxxxxxx????xxx????xxxxxxxxxxxx";
        static const BYTE reset[] = {
            0x40,0x53,0x48,0x83,0xec,0x30,0x80,0xb9,0x24,0x05,0,0,0,0x48,0x8b,0xd9,
            0x74,0x10,0x45,0x33,0xc9,0x45,0x33,0xc0,0xba,0x24,0x6e,0x15,0
        };
        static_assert(sizeof(showMask) - 1 == sizeof(show), "Hammer signature mask length");
        BYTE* showAddress = HammerFindUnique(base, nt, show, showMask, sizeof(show));
        BYTE* resetAddress = HammerFindUnique(base, nt, reset,
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx", sizeof(reset));
        s_hammerChecked = true;
        if (!showAddress || !resetAddress) {
            OutputDebugStringA("[Siel Hammer] Unsupported client; signatures not unique.\n");
            __leave;
        }
        // Confirm that the result helper refers to the expected C++ UI type.
        const intptr_t typeOffset = (showAddress - base) + 34 + *(int32_t*)(showAddress + 30);
        static const char typeName[] = ".?AVDlgItemCrushResult@@";
        if (typeOffset < 0 || (size_t)typeOffset + 16 + sizeof(typeName) > nt->OptionalHeader.SizeOfImage ||
            memcmp(base + typeOffset + 16, typeName, sizeof(typeName)) != 0) __leave;

        s_hammerShowResult = (HammerShowResult)showAddress;
        s_hammerResetProgress = (HammerResetProgress)resetAddress;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_hammerChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_hammerShowResult, HammerShowSuccessfulResult);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_hammerResetProgress, HammerResetAfterResult);
        if (error == NO_ERROR) error = DetourTransactionCommit();
        else DetourTransactionAbort();
        OutputDebugStringA(error == NO_ERROR ? "[Siel Hammer] Success/Stop UI fix installed.\n" :
            "[Siel Hammer] UI hook installation failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_hammerLock);
    }
}
#endif
#else
static void InstallSielHammerFix(HMODULE) {}
#endif
