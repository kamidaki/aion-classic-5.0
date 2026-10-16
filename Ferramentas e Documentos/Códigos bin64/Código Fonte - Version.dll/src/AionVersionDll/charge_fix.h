#pragma once

// Classic 5.0 x64: Charge skills of the Bard (Live 5.8). On the Live client the learned skill
// (stage 1, activation "Charge") charges through the stages of client_skill_charge.xml by itself;
// pressing it again fires the reached stage with C_FIRE_CHARGE_SKILL (opcode 234, no payload) and,
// without that press, the cast is cancelled at the end. The 5.0 Game.dll has none of it (no charge
// table, no 234 in its packet table), so the stage 1 skill is a plain Active skill there and the
// server runs the charge (activation CHARGE + skill_charge.xml). Three hooks give the second press:
// - 0x88FDE0 (connection, buffer, length) sends every client packet before encryption: a
//   C_USE_SKILL of a charge skill starts the charge here.
// - Decrypted server packets (observer of the Quna dispatch hook): S_SKILL_CANCELED or
//   S_SKILL_SUCCEDED of the caster ends it (a hit interrupts it, cancel_rate; so does the end of
//   the charge time).
// - 0x9A0E30 (player, action, id, ...) takes every action request. While a cast runs the client
//   queues a new request and sends its C_USE_SKILL only after the cast ends, so the second press
//   never left during the charge; it is answered here instead, with opcode 234.
//
// Plain body: [H length][H wire opcode][C 0x6F][H ~wire opcode][payload]; wire = (op + 0xC4) ^ 0x36.
// C_USE_SKILL (0x21, wire 0xD3) payload starts with [H skill id] (builder at 0x198180).
// The charge skills come from charge_skills.txt next to version.dll (bard_skills_58.py writes it):
// one "skill_id total_charge_ms" per line, total = sum of the stage times.
#if defined(_M_AMD64)
using ChargeSendPacket = INT_PTR (__fastcall*)(void*, BYTE*, int);
static ChargeSendPacket s_chargeSend = nullptr;

static constexpr WORD kChargeUseSkillWire = (0x21 + 0xC4) ^ 0x36;
static constexpr WORD kChargeFireWire = (234 + 0xC4) ^ 0x36;
static constexpr BYTE kChargeStaticByte = 0x6F;
static constexpr int kChargeMaxSkills = 64;
// The server may end the charge a little after the sum of the stages (cast speed only shortens it).
static constexpr ULONGLONG kChargeMarginMs = 500;

static WORD s_chargeSkillIds[kChargeMaxSkills] = {};
static DWORD s_chargeTotalMs[kChargeMaxSkills] = {};
static int s_chargeSkillCount = 0;
static bool s_chargeTableRead = false;
// Charge in progress, as the server reports it: set when C_USE_SKILL of a charge skill leaves,
// the caster is taken from the S_USE_SKILL that answers it, and S_SKILL_CANCELED or
// S_SKILL_SUCCEDED of that caster ends it. The time limit only covers a lost answer.
// Packets are sent and received on different threads.
static volatile LONG s_chargeActiveSkill = 0;
static volatile LONG s_chargeCaster = 0;
static ULONGLONG s_chargeActiveUntil = 0;
static void* s_chargeConnection = nullptr;

static void ChargeReadTable() {
    s_chargeTableRead = true;
    HMODULE self = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            (LPCWSTR)&ChargeReadTable, &self)) return;
    wchar_t path[MAX_PATH];
    const DWORD size = GetModuleFileNameW(self, path, MAX_PATH);
    if (size == 0 || size >= MAX_PATH) return;
    wchar_t* slash = wcsrchr(path, L'\\');
    if (!slash || wcscpy_s(slash + 1, MAX_PATH - (slash + 1 - path), L"charge_skills.txt") != 0) return;
    FILE* file = nullptr;
    if (_wfopen_s(&file, path, L"r") != 0 || !file) {
        OutputDebugStringA("[Charge] charge_skills.txt not found.\n");
        return;
    }
    char line[128];
    while (s_chargeSkillCount < kChargeMaxSkills && fgets(line, sizeof(line), file)) {
        unsigned skill = 0, total = 0;
        if (line[0] == '#' || sscanf_s(line, "%u %u", &skill, &total) != 2 || skill == 0 || skill > 0xFFFF) continue;
        s_chargeSkillIds[s_chargeSkillCount] = (WORD)skill;
        s_chargeTotalMs[s_chargeSkillCount] = total;
        ++s_chargeSkillCount;
    }
    fclose(file);
}

static int ChargeFind(WORD skill) {
    for (int i = 0; i < s_chargeSkillCount; ++i)
        if (s_chargeSkillIds[i] == skill) return i;
    return -1;
}

// Server packets (decrypted, [H wire][C][H ~wire][payload]; wire = (op + 0xC4) ^ 0xD4):
// S_USE_SKILL 0x21 (wire 0x31), S_SKILL_CANCELED 0x2A (0x3A), S_SKILL_SUCCEDED 0x2B (0x3B).
// The payload of the three starts with [D caster]; S_USE_SKILL and S_SKILL_CANCELED follow with
// [H skill]. S_SKILL_SUCCEDED ends whatever the caster was casting, so only the caster is compared.
static constexpr WORD kChargeServerUseSkill = 0x31;
static constexpr WORD kChargeServerCanceled = 0x3A;
static constexpr WORD kChargeServerSucceeded = 0x3B;

static void ChargeOnServerPacket(const BYTE* body, int length) {
    if (!body || length < 11) return;
    const WORD wire = *(const WORD*)body;
    if (wire != kChargeServerUseSkill && wire != kChargeServerCanceled && wire != kChargeServerSucceeded) return;
    const LONG skill = s_chargeActiveSkill;
    if (!skill) return;
    const LONG caster = *(const LONG*)(body + 5);
    if (wire == kChargeServerUseSkill) {
        if (!s_chargeCaster && *(const WORD*)(body + 9) == (WORD)skill) InterlockedExchange(&s_chargeCaster, caster);
        return;
    }
    if (s_chargeCaster && caster == s_chargeCaster) InterlockedExchange(&s_chargeActiveSkill, 0);
}

static INT_PTR ChargeSendFire(void* connection) {
    BYTE fire[7];
    *(WORD*)(fire + 0) = sizeof(fire);
    *(WORD*)(fire + 2) = kChargeFireWire;
    fire[4] = kChargeStaticByte;
    *(WORD*)(fire + 5) = (WORD)~kChargeFireWire;
    return s_chargeSend(connection, fire, sizeof(fire));
}

// 0x9A0E30 (player, action, id, ...): compares with the request in player+0x1900/+0x1908 and keeps
// it queued while a cast runs. Action 2 is "use skill" (id = skill id), proven in game.
using ChargeRequestAction = void (__fastcall*)(void*, int, int, WORD, INT_PTR, INT_PTR, INT_PTR, INT_PTR);
static ChargeRequestAction s_chargeRequest = nullptr;
static constexpr int kChargeActionUseSkill = 2;

static void __fastcall ChargeRequestActionHook(void* player, int action, int id, WORD extra, INT_PTR a5,
                                                INT_PTR a6, INT_PTR a7, INT_PTR a8) {
    __try {
        if (action == kChargeActionUseSkill && id > 0 && s_chargeActiveSkill == id &&
            GetTickCount64() < s_chargeActiveUntil && s_chargeConnection) {
            // Second press while charging: fire the reached stage.
            InterlockedExchange(&s_chargeActiveSkill, 0);
            ChargeSendFire(s_chargeConnection);
            return;
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    s_chargeRequest(player, action, id, extra, a5, a6, a7, a8);
}

static INT_PTR __fastcall ChargeSendPacketHook(void* connection, BYTE* body, int length) {
    __try {
        if (body && length >= 9 && *(const WORD*)(body + 2) == kChargeUseSkillWire) {
            if (!s_chargeTableRead) ChargeReadTable();
            s_chargeConnection = connection;
            const int index = ChargeFind(*(const WORD*)(body + 7));
            InterlockedExchange(&s_chargeCaster, 0);
            if (index >= 0) {
                s_chargeActiveUntil = GetTickCount64() + s_chargeTotalMs[index] + kChargeMarginMs;
                InterlockedExchange(&s_chargeActiveSkill, s_chargeSkillIds[index]);
            } else {
                InterlockedExchange(&s_chargeActiveSkill, 0); // Any other skill ends the charge on the server.
            }
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return s_chargeSend(connection, body, length);
}

static SRWLOCK s_chargeLock = SRWLOCK_INIT;
static bool s_chargeChecked = false;

static void InstallChargeFix(HMODULE module) {
    // LoadLibrary hooks can reenter while Detours allocates its trampoline.
    if (!TryAcquireSRWLockExclusive(&s_chargeLock)) return;
    __try {
        if (s_chargeChecked) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Send: mov [rsp+18h],rbx; push rbp; push rsi; push rdi; sub rsp,20h; mov rbx,rcx;
        // mov edi,r8d; add rcx,90h; mov rsi,rdx; call [rip+x] (lock); mov rcx,[rbx+78h] (key)
        static const BYTE send[] = {
            0x48,0x89,0x5c,0x24,0x18,0x55,0x56,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x41,
            0x8b,0xf8,0x48,0x81,0xc1,0x90,0x00,0x00,0x00,0x48,0x8b,0xf2,0xff,0x15,0,0,0,0,
            0x48,0x8b,0x4b,0x78
        };
        static const char sendMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx????xxxx";
        static_assert(sizeof(sendMask) - 1 == sizeof(send), "Charge send signature mask length");

        // Request: mov [rsp+20h],r9w; mov [rsp+18h],r8d; push rbp/rbx/rsi/rdi/r13;
        // lea rbp,[rsp-610h]; sub rsp,710h; movsxd rsi,edx; mov r13d,r8d
        static const BYTE request[] = {
            0x66,0x44,0x89,0x4c,0x24,0x20,0x44,0x89,0x44,0x24,0x18,0x55,0x53,0x56,0x57,0x41,
            0x55,0x48,0x8d,0xac,0x24,0xf0,0xf9,0xff,0xff,0x48,0x81,0xec,0x10,0x07,0x00,0x00,
            0x48,0x63,0xf2,0x45,0x8b,0xe8
        };
        static const char requestMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(requestMask) - 1 == sizeof(request), "Charge request signature mask length");

        BYTE* sendPacket = QunaFindUnique(base, nt, send, sendMask, sizeof(send));
        BYTE* requestAction = QunaFindUnique(base, nt, request, requestMask, sizeof(request));
        s_chargeChecked = true;
        if (!sendPacket || !requestAction) {
            OutputDebugStringA("[Charge] Unsupported client; signatures not unique.\n");
            __leave;
        }
        s_chargeSend = (ChargeSendPacket)sendPacket;
        s_chargeRequest = (ChargeRequestAction)requestAction;
        s_qunaServerPacketObserver = ChargeOnServerPacket;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_chargeChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_chargeSend, ChargeSendPacketHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_chargeRequest, ChargeRequestActionHook);
        if (error == NO_ERROR) error = DetourTransactionCommit();
        else DetourTransactionAbort();
        OutputDebugStringA(error == NO_ERROR ? "[Charge] Send hook installed.\n" :
            "[Charge] Send hook installation failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_chargeLock);
    }
}
#else
static void InstallChargeFix(HMODULE) {}
#endif
