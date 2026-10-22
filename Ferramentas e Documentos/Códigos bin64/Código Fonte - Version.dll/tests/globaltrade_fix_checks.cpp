#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// globaltrade_fix.h sends through the trampoline of the charge_fix.h send hook.
using ChargeSendPacket = INT_PTR (__fastcall*)(void*, BYTE*, int);
static ChargeSendPacket s_chargeSend = nullptr;
#define GLOBAL_TRADE_FIX_TEST
#include "../src/AionVersionDll/globaltrade_fix.h"

static unsigned checks, sent;
static BYTE lastPacket[64];
static int lastLength;

static void Check(bool condition) {
    ++checks;
    if (!condition) { fprintf(stderr, "FAIL check %u\n", checks); exit(1); }
}

static INT_PTR __fastcall Send(void*, BYTE* body, int length) {
    ++sent;
    lastLength = length;
    memcpy(lastPacket, body, length);
    return 9;
}

// Plain C_GLOBAL_TRADE_BUY of listing 0x127DF8: [H 15][H 0x1EC][C 6F][H ~0x1EC][Q listing].
static void Buy(BYTE* body) {
    const BYTE plain[] = { 0x0f,0x00,0xec,0x01,0x6f,0x13,0xfe,0xf8,0x7d,0x12,0,0,0,0,0 };
    memcpy(body, plain, sizeof(plain));
}

static bool Filter(BYTE* body, int length, INT_PTR* result) {
    return GlobalTradeSendFilter(nullptr, body, length, result);
}

int main() {
    s_chargeSend = Send;
    BYTE body[15];
    INT_PTR result = 0;

    // Outside the OK of DlgVendorBuyEach the packet goes out untouched (whole listing).
    Buy(body);
    Check(!Filter(body, sizeof(body), &result) && sent == 0);

    // Inside it, the count is appended: 15 -> 19 bytes, listing kept.
    s_globalTradeBuyEachThread = GetCurrentThreadId();
    s_globalTradeBuyEachCount = 5;
    Check(Filter(body, sizeof(body), &result) && result == 9 && sent == 1 && lastLength == 19);
    Check(*(WORD*)lastPacket == 19 && memcmp(lastPacket + 2, body + 2, 13) == 0 && *(DWORD*)(lastPacket + 15) == 5);
    // One packet per OK.
    Check(!Filter(body, sizeof(body), &result) && sent == 1);

    // Another packet during the OK is not touched.
    s_globalTradeBuyEachThread = GetCurrentThreadId();
    s_globalTradeBuyEachCount = 5;
    BYTE other[15];
    Buy(other);
    other[2] = 0xed; // C_GLOBAL_TRADE_COMMIT wire
    Check(!Filter(other, sizeof(other), &result) && sent == 1);
    Check(!Filter(body, 14, &result) && sent == 1);

    // Another thread is not touched.
    s_globalTradeBuyEachThread = GetCurrentThreadId() + 1;
    Check(!Filter(body, sizeof(body), &result) && sent == 1);

    // A count of 0 sends nothing (the server would sell the whole listing).
    s_globalTradeBuyEachThread = GetCurrentThreadId();
    s_globalTradeBuyEachCount = 0;
    Check(Filter(body, sizeof(body), &result) && result == 0 && sent == 1);

    // Unit minimum of the sale entry: the 200000 of the listing spread over the stack, rounded up.
    Check(GlobalTradeUnitMinimum(200000, 84) == 2381 && 2381LL * 84 >= 200000 && 2380LL * 84 < 200000);
    Check(GlobalTradeUnitMinimum(200000, 1) == 200000 && GlobalTradeUnitMinimum(200000, 0) == 200000);
    Check(GlobalTradeUnitMinimum(200000, 200000) == 1 && GlobalTradeUnitMinimum(200000, 300000) == 1);
    Check(GlobalTradeUnitMinimum(0, 5) == 0);

    printf("globaltrade_fix_checks: %u checks passed\n", checks);
    return 0;
}
