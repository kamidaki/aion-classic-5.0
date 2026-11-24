#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#define SIEL_HAMMER_FIX_TEST
#include "../src/AionVersionDll/siel_hammer_fix.h"

static BYTE dialog[0x525];
static unsigned warnings, resets, checks;
static bool nested, fail;
static void Check(bool condition) {
    ++checks;
    if (!condition) { fprintf(stderr, "FAIL check %u\n", checks); exit(1); }
}
static void __fastcall Reset(void* instance) {
    Check(instance == dialog);
    if (((BYTE*)instance)[0x524]) ++warnings;
    ((BYTE*)instance)[0x524] = 0;
    ++resets;
}
static DWORD WINAPI OtherThread(void*) {
    return s_hammerSuccessDepth;
}
static void __fastcall Show(void* context, void* items, bool bonus) {
    Check(context == dialog && items == &warnings && bonus);
    Check(s_hammerSuccessDepth > 0);
    if (fail) RaiseException(0xE0425000, 0, 0, nullptr);
    if (nested) {
        nested = false;
        HammerShowSuccessfulResult(context, items, bonus);
        Check(s_hammerSuccessDepth == 1);
    }
    HANDLE thread = CreateThread(nullptr, 0, OtherThread, nullptr, 0, nullptr);
    Check(thread != nullptr);
    WaitForSingleObject(thread, INFINITE);
    DWORD depth = 1;
    GetExitCodeThread(thread, &depth);
    CloseHandle(thread);
    Check(depth == 0);
    dialog[0x524] = 1;
    HammerResetAfterResult(dialog);
}
int main() {
    s_hammerResetProgress = Reset;
    s_hammerShowResult = Show;
    // Real Stop keeps its message.
    dialog[0x524] = 1;
    HammerResetAfterResult(dialog);
    Check(warnings == 1 && resets == 1);
    // Successful result suppresses only the local cancellation warning.
    HammerShowSuccessfulResult(dialog, &warnings, true);
    Check(warnings == 1 && resets == 2 && s_hammerSuccessDepth == 0);
    // Nested result processing restores the caller's scope.
    nested = true;
    HammerShowSuccessfulResult(dialog, &warnings, true);
    Check(warnings == 1 && resets == 4 && s_hammerSuccessDepth == 0);
    // An exceptional UI exit cannot suppress future real Stop messages.
    fail = true;
    __try { HammerShowSuccessfulResult(dialog, &warnings, true); }
    __except (GetExceptionCode() == 0xE0425000 ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) {}
    Check(s_hammerSuccessDepth == 0);
    dialog[0x524] = 1;
    HammerResetAfterResult(dialog);
    Check(warnings == 2 && resets == 5);
    HammerResetAfterResult(dialog);
    Check(warnings == 2 && resets == 6);
    printf("PASS: %u Siel Hammer client checks\n", checks);
}
