#pragma once

// Classic 5.0 x64: the Quna balance shown by the client (inventory, Quna Market "Funds owned",
// Auction House, wardrobe expansion) is the sum of two Game.dll globals, paid and free Quna.
// Both start at -1 (the field shows "-") and only the reply parser of the NCSoft STS service
// (port 6600) writes them. The emulator has no STS (-noweb/-nowebshop): it sends the account
// balance in S 0x11B [H code][Q balance], at login and after every change. This hook sees every
// decrypted server packet before the client dispatches it and copies that balance into the
// globals. The packet itself is not changed.
#if defined(_M_AMD64)
using QunaPacketDispatch = INT_PTR (__fastcall*)(void*, int, BYTE*, int);
static QunaPacketDispatch s_qunaDispatch = nullptr;
static volatile LONG64* s_qunaPaid = nullptr;
static volatile LONG64* s_qunaFree = nullptr;

// Decrypted body: [H opcode][C][H checksum = ~opcode][payload]. S 0x11B travels as
// ((0x11B + 0xC4) ^ 0xD4) = 0x10B; the payload is [H code][Q balance].
static constexpr WORD kQunaBalanceOpcode = 0x10B;
static constexpr int kQunaBalanceLength = 5 + 2 + 8;

static void QunaApplyBalance(const BYTE* body, int length) {
    if (!body || length < kQunaBalanceLength || !s_qunaPaid || !s_qunaFree) return;
    const WORD opcode = *(const WORD*)body;
    if (opcode != kQunaBalanceOpcode || *(const WORD*)(body + 3) != (WORD)~opcode) return;
    const LONG64 balance = *(const LONG64*)(body + 7);
    if (balance < 0) return;
    // The emulator keeps a single balance, so all of it is shown as paid Quna.
    InterlockedExchange64(s_qunaPaid, balance);
    InterlockedExchange64(s_qunaFree, 0);
}

// Other fixes that need to see decrypted server packets (charge_fix.h) set this observer.
static void (*s_qunaServerPacketObserver)(const BYTE*, int) = nullptr;

static INT_PTR __fastcall QunaDispatchPacket(void* connection, int state, BYTE* body, int length) {
    __try {
        QunaApplyBalance(body, length);
        if (s_qunaServerPacketObserver) s_qunaServerPacketObserver(body, length);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return s_qunaDispatch(connection, state, body, length);
}

#ifndef QUNA_FIX_TEST
static SRWLOCK s_qunaLock = SRWLOCK_INIT;
static bool s_qunaChecked = false;

static BYTE* QunaFindUnique(BYTE* base, PIMAGE_NT_HEADERS nt,
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

static void InstallQunaFix(HMODULE module) {
    // LoadLibrary hooks can reenter while Detours allocates its trampoline.
    if (!TryAcquireSRWLockExclusive(&s_qunaLock)) return;
    __try {
        if (s_qunaChecked) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Receive loop, after decrypting the body in place:
        // mov edx,[rbx+70h]; lea rdi,[rbx+104C0h]; mov r9d,ecx; mov r8,rdi; mov rcx,rbx; call dispatch
        static const BYTE receive[] = {
            0x8b,0x53,0x70,0x48,0x8d,0xbb,0xc0,0x04,0x01,0x00,0x44,0x8b,0xc9,0x4c,0x8b,0xc7,
            0x48,0x8b,0xcb,0xe8,0,0,0,0
        };
        static const char receiveMask[] = "xxxxxxxxxxxxxxxxxxxx????";
        // Balance text of the Quna Market header:
        // push rbx; sub rsp,0C0h; cmp qword ptr [rcx+568h],0; mov rbx,rcx; je;
        // mov r8,[rip+paid]; lea rcx,[rsp+20h]; add r8,[rip+free]
        static const BYTE money[] = {
            0x40,0x53,0x48,0x81,0xec,0xc0,0x00,0x00,0x00,0x48,0x83,0xb9,0x68,0x05,0x00,0x00,
            0x00,0x48,0x8b,0xd9,0x74,0x32,0x4c,0x8b,0x05,0,0,0,0,0x48,0x8d,0x4c,0x24,0x20,
            0x4c,0x03,0x05,0,0,0,0
        };
        static const char moneyMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxx????xxxxxxxx????";
        static_assert(sizeof(receiveMask) - 1 == sizeof(receive), "Quna receive signature mask length");
        static_assert(sizeof(moneyMask) - 1 == sizeof(money), "Quna money signature mask length");

        BYTE* receiveCall = QunaFindUnique(base, nt, receive, receiveMask, sizeof(receive));
        BYTE* moneyText = QunaFindUnique(base, nt, money, moneyMask, sizeof(money));
        s_qunaChecked = true;
        if (!receiveCall || !moneyText) {
            OutputDebugStringA("[Quna] Unsupported client; signatures not unique.\n");
            __leave;
        }
        BYTE* dispatch = receiveCall + 24 + *(int32_t*)(receiveCall + 20);
        BYTE* paid = moneyText + 0x1d + *(int32_t*)(moneyText + 0x19);
        BYTE* freeQuna = moneyText + 0x29 + *(int32_t*)(moneyText + 0x25);
        const SIZE_T image = nt->OptionalHeader.SizeOfImage;
        if (dispatch < base || dispatch >= base + image || paid < base || paid + 16 > base + image ||
            freeQuna != paid + 8) {
            OutputDebugStringA("[Quna] Unsupported client; unexpected addresses.\n");
            __leave;
        }

        s_qunaPaid = (volatile LONG64*)paid;
        s_qunaFree = (volatile LONG64*)freeQuna;
        s_qunaDispatch = (QunaPacketDispatch)dispatch;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_qunaChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_qunaDispatch, QunaDispatchPacket);
        if (error == NO_ERROR) error = DetourTransactionCommit();
        else DetourTransactionAbort();
        OutputDebugStringA(error == NO_ERROR ? "[Quna] Balance hook installed.\n" :
            "[Quna] Balance hook installation failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_qunaLock);
    }
}
#endif
#else
static void InstallQunaFix(HMODULE) {}
#endif
