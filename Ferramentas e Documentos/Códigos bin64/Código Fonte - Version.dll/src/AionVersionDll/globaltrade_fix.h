#pragma once

// Classic 5.0 x64: split purchase ("buy each") in the Kinah tab of the Global Auction House.
// The 5.0 Game.dll still has the whole feature of the later clients, switched off:
// - every search result entry has a flag at +0xEA0; with it the list shows
//   STR_VENDOR_DIALOG_FLAG_BUY_EACH and the Kinah tab buy (KinaVendorTab, 0x2A3340) opens
//   DlgVendorBuyEach (vendor_buy_each_dialog: number pad, unit price, total, own kinah) instead of
//   the single/stack buy dialog, with the maximum count limited by the kinah the player has;
// - but S_GLOBAL_TRADE_LIST never sets the flag (0x8BC0A8 passes a byte that is always 0 to the
//   entry constructor 0x822A00), and the OK of DlgVendorBuyEach (0x6F4C10) hands the chosen
//   count (+0x528) to a callback (0x2A5ED0) that sends C_GLOBAL_TRADE_BUY with the listing only.
// Three hooks turn it on:
// - 0x822A00 (store, currency, ...) returns the new entry: kinah entries (currency 1) with more
//   than one unit (+0x18) get the flag;
// - 0x6F4C10 (closure, ...) remembers the count of the dialog (closure +8) while the OK runs;
// - the send filter of charge_fix.h adds [D count] to the C_GLOBAL_TRADE_BUY that this OK sends
//   (plain body [H length][H wire 0x1EC][C 0x6F][H ~wire][Q listing], 15 -> 19 bytes).
// The emulator reads the count (CM_GLOBAL_TRADE_BUY); without it the whole listing is bought.
#if defined(_M_AMD64)
using GlobalTradeAddEntry = BYTE* (__fastcall*)(void*, int, void*, void*, void*, void*, void*, void*,
                                                 void*, void*, void*, void*);
using GlobalTradeBuyEachOk = INT_PTR (__fastcall*)(BYTE*, void*);
static GlobalTradeAddEntry s_globalTradeAddEntry = nullptr;
static GlobalTradeBuyEachOk s_globalTradeBuyEachOk = nullptr;

static constexpr int kGlobalTradeKinah = 1;
static constexpr size_t kGlobalTradeEntryCount = 0x18;
static constexpr size_t kGlobalTradeEntrySplitFlag = 0xEA0;
static constexpr size_t kGlobalTradeBuyEachCount = 0x528;
static constexpr WORD kGlobalTradeBuyWire = (0x116 + 0xC4) ^ 0x36;
static constexpr int kGlobalTradeBuyLength = 15;

// Set only while the OK of DlgVendorBuyEach runs, on the UI thread that also sends the packet.
static volatile DWORD s_globalTradeBuyEachThread = 0;
static volatile LONG64 s_globalTradeBuyEachCount = 0;

static BYTE* __fastcall GlobalTradeAddEntryHook(void* store, int currency, void* a3, void* a4, void* a5,
                                               void* a6, void* a7, void* a8, void* a9, void* a10,
                                               void* a11, void* a12) {
    BYTE* entry = s_globalTradeAddEntry(store, currency, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12);
    __try {
        if (entry && currency == kGlobalTradeKinah && *(const LONG64*)(entry + kGlobalTradeEntryCount) > 1)
            entry[kGlobalTradeEntrySplitFlag] = 1;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return entry;
}

static INT_PTR __fastcall GlobalTradeBuyEachOkHook(BYTE* closure, void* argument) {
    LONG64 count = 0;
    __try {
        if (closure) {
            BYTE* dialog = *(BYTE**)(closure + 8);
            if (dialog) count = *(const LONG64*)(dialog + kGlobalTradeBuyEachCount);
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    s_globalTradeBuyEachCount = count;
    s_globalTradeBuyEachThread = GetCurrentThreadId();
    const INT_PTR result = s_globalTradeBuyEachOk(closure, argument);
    s_globalTradeBuyEachThread = 0;
    s_globalTradeBuyEachCount = 0;
    return result;
}

// Send filter (charge_fix.h): true when the packet was handled here and *result is the answer.
static bool GlobalTradeSendFilter(void* connection, BYTE* body, int length, INT_PTR* result) {
    if (s_globalTradeBuyEachThread != GetCurrentThreadId()) return false;
    if (!body || length != kGlobalTradeBuyLength || *(const WORD*)(body + 2) != kGlobalTradeBuyWire ||
        *(const WORD*)(body + 5) != (WORD)~kGlobalTradeBuyWire) return false;
    const LONG64 count = s_globalTradeBuyEachCount;
    s_globalTradeBuyEachThread = 0; // One packet per OK.
    if (count <= 0 || count > MAXLONG) {
        // Without a count the server sells the whole listing: an empty choice buys nothing.
        *result = 0;
        return true;
    }
    BYTE packet[kGlobalTradeBuyLength + 4];
    memcpy(packet, body, kGlobalTradeBuyLength);
    *(WORD*)packet = (WORD)sizeof(packet);
    *(DWORD*)(packet + kGlobalTradeBuyLength) = (DWORD)count;
    *result = s_chargeSend(connection, packet, (int)sizeof(packet));
    return true;
}

#ifndef GLOBAL_TRADE_FIX_TEST
// Where the installation stopped, readable in the client's memory next to the "GTDIAG1" marker:
// 1 started, 2 no send hook, 31/32 entry/OK signature not found yet, 33 unexpected fields,
// 4 Detours, 5 installed; tries = installation attempts.
static volatile struct { char marker[8]; LONG step; LONG tries; } s_globalTradeDiag = { "GTDIAG1", 0, 0 };
static SRWLOCK s_globalTradeLock = SRWLOCK_INIT;
static bool s_globalTradeChecked = false;
// Game.dll is unpacked by WinLicense while it loads: the first attempts can run before these two
// functions are in their final form (step 3 at load, unique a moment later). A thread of its own
// retries for two minutes, since the loader monitor stops once every module was seen.
static volatile LONG s_globalTradeRetrying = 0;
static constexpr int kGlobalTradeRetries = 240;
static constexpr DWORD kGlobalTradeRetryMs = 500;
static void InstallGlobalTradeFix(HMODULE module);

static DWORD WINAPI GlobalTradeRetryThread(LPVOID module) {
    for (int i = 0; i < kGlobalTradeRetries && !s_globalTradeChecked; ++i) {
        Sleep(kGlobalTradeRetryMs);
        InstallGlobalTradeFix((HMODULE)module);
    }
    return 0;
}

static void GlobalTradeRetryLater(HMODULE module) {
    if (InterlockedCompareExchange(&s_globalTradeRetrying, 1, 0) != 0) return;
    HANDLE thread = CreateThread(nullptr, 0, GlobalTradeRetryThread, module, 0, nullptr);
    if (thread) CloseHandle(thread);
}

static void InstallGlobalTradeFix(HMODULE module) {
    // LoadLibrary hooks can reenter while Detours allocates its trampoline.
    if (!TryAcquireSRWLockExclusive(&s_globalTradeLock)) return;
    __try {
        if (s_globalTradeChecked) __leave;
        s_globalTradeDiag.step = 1;
        InterlockedIncrement(&s_globalTradeDiag.tries);
        // The count goes out through the send hook of charge_fix.h. The installers run on the loader
        // monitor thread and in the LoadLibrary hooks at the same time and give up on a busy lock, so
        // the charge hook may be half way on the other thread: wait for it, or install it here. Leaving
        // without it lost the hook for good (the other thread then found this lock busy).
        if (!s_chargeSend) {
            AcquireSRWLockShared(&s_chargeLock);
            ReleaseSRWLockShared(&s_chargeLock);
        }
        if (!s_chargeSend) InstallChargeFix(module);
        if (!s_chargeSend) { s_globalTradeDiag.step = 2; __leave; }
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Entry constructor: mov [rsp+18h],rbp; mov [rsp+20h],rsi; push rdi/r14/r15; sub rsp,70h;
        // mov rbp,[rip+store]; mov ecx,0EB8h; add [rip+x],0EB8h; mov r15,r9; inc [rip+y];
        // mov r14,r8; mov esi,edx
        static const BYTE addEntry[] = {
            0x48,0x89,0x6c,0x24,0x18,0x48,0x89,0x74,0x24,0x20,0x57,0x41,0x56,0x41,0x57,0x48,
            0x83,0xec,0x70,0x48,0x8b,0x2d,0,0,0,0,0xb9,0xb8,0x0e,0x00,0x00,0x48,0x81,0x05,
            0,0,0,0,0xb8,0x0e,0x00,0x00,0x4d,0x8b,0xf9,0xff,0x05,0,0,0,0,0x4d,0x8b,0xf0,
            0x8b,0xf2
        };
        static const char addEntryMask[] = "xxxxxxxxxxxxxxxxxxxxxx????xxxxxxxx????xxxxxxxxx????xxxxx";
        // OK of DlgVendorBuyEach: mov [rsp+10h],rdx; push rbx; sub rsp,20h; mov rbx,[rcx+8];
        // cmp qword [rbx+590h],0; je; mov eax,[rbx+540h]; mov rcx,rbx; mov [rsp+38h],rax;
        // mov rax,[rbx]; call [rax+5B8h]; mov rcx,[rbx+590h]
        static const BYTE buyEachOk[] = {
            0x48,0x89,0x54,0x24,0x10,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0x59,0x08,0x48,0x83,
            0xbb,0x90,0x05,0x00,0x00,0x00,0x74,0,0x8b,0x83,0x40,0x05,0x00,0x00,0x48,0x8b,
            0xcb,0x48,0x89,0x44,0x24,0x38,0x48,0x8b,0x03,0xff,0x90,0xb8,0x05,0x00,0x00,0x48,
            0x8b,0x8b,0x90,0x05,0x00,0x00
        };
        static const char buyEachOkMask[] = "xxxxxxxxxxxxxxxxxxxxxxx?xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(addEntryMask) - 1 == sizeof(addEntry), "Global trade entry signature mask length");
        static_assert(sizeof(buyEachOkMask) - 1 == sizeof(buyEachOk), "Global trade buy each signature mask length");

        BYTE* entry = QunaFindUnique(base, nt, addEntry, addEntryMask, sizeof(addEntry));
        BYTE* ok = QunaFindUnique(base, nt, buyEachOk, buyEachOkMask, sizeof(buyEachOk));
        if (!entry || !ok) {
            s_globalTradeDiag.step = !entry ? 31 : 32;
            GlobalTradeRetryLater(module);
            __leave;
        }
        s_globalTradeChecked = true;
        // Fields the hooks rely on: the entry stores the count at +18h and the flag at +0EA0h, and the
        // OK hands the count at +528h to the callback.
        static const BYTE storeCount[] = { 0x48,0x89,0x4f,0x18 };              // mov [rdi+18h],rcx
        static const BYTE storeFlag[] = { 0x88,0x8f,0xa0,0x0e,0x00,0x00 };     // mov [rdi+0EA0h],cl
        static const BYTE passCount[] = { 0x4c,0x8d,0x8b,0x28,0x05,0x00,0x00 }; // lea r9,[rbx+528h]
        if (memcmp(entry + 0xbb, storeCount, sizeof(storeCount)) != 0 ||
            memcmp(entry + 0xf5, storeFlag, sizeof(storeFlag)) != 0 ||
            memcmp(ok + 0x4a, passCount, sizeof(passCount)) != 0) {
            OutputDebugStringA("[GlobalTrade] Unsupported client; signatures not unique.\n");
            s_globalTradeDiag.step = 33;
            __leave;
        }

        s_globalTradeAddEntry = (GlobalTradeAddEntry)entry;
        s_globalTradeBuyEachOk = (GlobalTradeBuyEachOk)ok;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_globalTradeChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_globalTradeAddEntry, GlobalTradeAddEntryHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_globalTradeBuyEachOk, GlobalTradeBuyEachOkHook);
        if (error == NO_ERROR) error = DetourTransactionCommit();
        else DetourTransactionAbort();
        if (error == NO_ERROR) s_chargeSendFilter = GlobalTradeSendFilter;
        s_globalTradeDiag.step = error == NO_ERROR ? 5 : 4;
        OutputDebugStringA(error == NO_ERROR ? "[GlobalTrade] Split purchase hooks installed.\n" :
            "[GlobalTrade] Split purchase hook installation failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_globalTradeLock);
    }
}
#endif
#else
static void InstallGlobalTradeFix(HMODULE) {}
#endif
