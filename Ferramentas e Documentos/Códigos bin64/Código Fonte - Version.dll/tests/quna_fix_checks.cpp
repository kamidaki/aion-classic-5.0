#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define QUNA_FIX_TEST
#include "../src/AionVersionDll/quna_fix.h"

static LONG64 globals[2];
static unsigned dispatched, checks;
static void* lastConnection;
static int lastState, lastLength;
static BYTE* lastBody;

static void Check(bool condition) {
    ++checks;
    if (!condition) { fprintf(stderr, "FAIL check %u\n", checks); exit(1); }
}

static INT_PTR __fastcall Dispatch(void* connection, int state, BYTE* body, int length) {
    ++dispatched;
    lastConnection = connection;
    lastState = state;
    lastBody = body;
    lastLength = length;
    return 7;
}

static void Reset() {
    globals[0] = -1;
    globals[1] = -1;
}

static void Run(BYTE* body, int length) {
    const unsigned before = dispatched;
    Check(QunaDispatchPacket(&globals, 3, body, length) == 7);
    Check(dispatched == before + 1 && lastConnection == &globals && lastState == 3 &&
          lastBody == body && lastLength == length);
}

int main() {
    s_qunaDispatch = Dispatch;
    s_qunaPaid = &globals[0];
    s_qunaFree = &globals[1];

    // Official S 0x11B after the hair change (2026-09-21 14:56): code 0x149, balance 438.
    BYTE official[] = { 0x0b,0x01,0x65,0xf4,0xfe, 0x49,0x01, 0xb6,0x01,0,0,0,0,0,0 };
    BYTE copy[sizeof(official)];
    memcpy(copy, official, sizeof(official));
    Reset();
    Run(official, sizeof(official));
    Check(globals[0] == 438 && globals[1] == 0);
    Check(memcmp(copy, official, sizeof(official)) == 0); // The packet is not changed.

    // Emulator login packet: code 0, balance 93.
    BYTE login[] = { 0x0b,0x01,0x65,0xf4,0xfe, 0x00,0x00, 0x5d,0,0,0,0,0,0,0 };
    Reset();
    Run(login, sizeof(login));
    Check(globals[0] == 93 && globals[1] == 0);

    // Other packets, broken checksum, short body and negative balance leave the globals alone.
    BYTE other[] = { 0x0c,0x01,0x65,0xf3,0xfe, 0x00,0x00, 0x5d,0,0,0,0,0,0,0 };
    BYTE checksum[] = { 0x0b,0x01,0x65,0xf4,0xff, 0x00,0x00, 0x5d,0,0,0,0,0,0,0 };
    BYTE negative[] = { 0x0b,0x01,0x65,0xf4,0xfe, 0x00,0x00, 0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff };
    Reset();
    Run(other, sizeof(other));
    Run(checksum, sizeof(checksum));
    Run(login, sizeof(login) - 1);
    Run(negative, sizeof(negative));
    Run(nullptr, 0);
    Check(globals[0] == -1 && globals[1] == -1);

    // Without the globals (unsupported client) the packet still goes through.
    s_qunaPaid = nullptr;
    Run(login, sizeof(login));
    Check(globals[0] == -1);

    printf("quna_fix_checks: %u checks OK\n", checks);
    return 0;
}
