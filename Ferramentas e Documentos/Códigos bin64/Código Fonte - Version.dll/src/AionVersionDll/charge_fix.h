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
// one "skill_id stage1_ms stage2_ms ..." per line (charge_time1.. of the 5.8 table).
//
// Charge bar: the 5.8 skill_delay_dialog has a charge bar coloured by stage (preset
// v5_gauge_charge) and one light per stage (v5_gauge_charge_step, state 0 = off, 1-4 = colours).
// The 5.0 preload already has both presets and the texture; teste_harpa_58.py adds the widgets
// charge_gauge and charge_step1..3 to the 5.0 dialog, and the frame hook of the dialog (DlgSkillDelay,
// 0x65F0E0) drives them while a charge runs. Widget calls of the 5.0 UI: find child = dialog
// vtable+0x368 (name, type: 0x2010 gauge, 0x2025 static); flags at +0x28, bit 1 = visible,
// vtable+0xD8 (bits, 0) sets and +0xE0 clears; vtable+0x110 (state) as UIActionSetState does;
// gauge maximum/value = 0xAAD660/0xAAD6A0, called by the frame function itself.
#if defined(_M_AMD64)
using ChargeSendPacket = INT_PTR (__fastcall*)(void*, BYTE*, int);
static ChargeSendPacket s_chargeSend = nullptr;

static constexpr WORD kChargeUseSkillWire = (0x21 + 0xC4) ^ 0x36;
static constexpr WORD kChargeFireWire = (234 + 0xC4) ^ 0x36;
static constexpr BYTE kChargeStaticByte = 0x6F;
static constexpr int kChargeMaxSkills = 64;
// The server may end the charge a little after the sum of the stages (cast speed only shortens it).
static constexpr ULONGLONG kChargeMarginMs = 500;

static constexpr int kChargeMaxStages = 4;
static WORD s_chargeSkillIds[kChargeMaxSkills] = {};
static DWORD s_chargeStageMs[kChargeMaxSkills][kChargeMaxStages] = {};
static int s_chargeStageCount[kChargeMaxSkills] = {};
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
// Table row of the charge and the moment the server started it (S_USE_SKILL), for the stages.
static volatile LONG s_chargeIndex = -1;
static volatile LONG64 s_chargeStartTick = 0;

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
        unsigned skill = 0, ms[kChargeMaxStages] = {};
        if (line[0] == '#') continue;
        const int read = sscanf_s(line, "%u %u %u %u %u", &skill, &ms[0], &ms[1], &ms[2], &ms[3]);
        if (read < 2 || skill == 0 || skill > 0xFFFF) continue;
        const int index = s_chargeSkillCount++;
        s_chargeSkillIds[index] = (WORD)skill;
        s_chargeStageCount[index] = read - 1;
        for (int i = 0; i < read - 1; ++i) {
            s_chargeStageMs[index][i] = ms[i];
            s_chargeTotalMs[index] += ms[i];
        }
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
        if (!s_chargeCaster && *(const WORD*)(body + 9) == (WORD)skill) {
            InterlockedExchange64(&s_chargeStartTick, (LONG64)GetTickCount64());
            InterlockedExchange(&s_chargeCaster, caster);
        }
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
        if (action == kChargeActionUseSkill && id > 0 && s_chargeActiveSkill == id && s_chargeCaster &&
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
                InterlockedExchange(&s_chargeIndex, index);
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

// Charge bar in skill_delay_dialog. The frame function (dialog) updates the cast bar from the
// duration (+0x4F8) and the end (+0x4FC) of the cast, while +0x500 says a cast is shown.
using ChargeDialogFrame = INT_PTR (__fastcall*)(BYTE*);
using ChargeGaugeMaximum = void (__fastcall*)(void*, double);
using ChargeGaugeValue = void (__fastcall*)(void*, double, int);
using ChargeFindChild = void* (__fastcall*)(void*, const char*, int);
using ChargeWidgetBits = void (__fastcall*)(void*, INT_PTR, int);
using ChargeWidgetState = void (__fastcall*)(void*, int);
static ChargeDialogFrame s_chargeDialogFrame = nullptr;
static ChargeGaugeMaximum s_chargeGaugeMaximum = nullptr;
static ChargeGaugeValue s_chargeGaugeValue = nullptr;

static constexpr int kChargeStepWidgets = 3;
static constexpr int kChargeWidgetGauge = 0x2010;
static constexpr int kChargeWidgetStatic = 0x2025;
static constexpr INT_PTR kChargeWidgetVisible = 1;
static BYTE* s_chargeDialog = nullptr;
static void* s_chargeGauge = nullptr;
static void* s_chargeSteps[kChargeStepWidgets] = {};
static bool s_chargeBarShown = false;
static int s_chargeBarStage = 0;

template <class Function>
static Function ChargeVirtual(void* object, size_t offset) {
    return *(Function*)(*(BYTE**)object + offset);
}

static void ChargeShowWidget(void* widget, bool show) {
    if (widget) ChargeVirtual<ChargeWidgetBits>(widget, show ? 0xD8 : 0xE0)(widget, kChargeWidgetVisible, 0);
}

static void ChargeSetWidgetState(void* widget, int state) {
    if (widget) ChargeVirtual<ChargeWidgetState>(widget, 0x110)(widget, state);
}

// Colour (preset state) of stage `stage` of `stages`: 1, 2... and the last one always blue (4), as on 5.8.
static int ChargeColour(int stage, int stages) {
    return stage >= stages ? 4 : stage;
}

static void ChargeHideBar() {
    ChargeShowWidget(s_chargeGauge, false);
    for (void* step : s_chargeSteps) ChargeShowWidget(step, false);
    s_chargeBarShown = false;
    s_chargeBarStage = 0;
}

static void ChargeUpdateDialog(BYTE* dialog) {
    if (dialog != s_chargeDialog) {
        s_chargeDialog = dialog;
        s_chargeBarShown = false;
        s_chargeBarStage = 0;
        const ChargeFindChild find = ChargeVirtual<ChargeFindChild>(dialog, 0x368);
        s_chargeGauge = find(dialog, "charge_gauge", kChargeWidgetGauge);
        for (int i = 0; i < kChargeStepWidgets; ++i) {
            char name[16];
            sprintf_s(name, "charge_step%d", i + 1);
            s_chargeSteps[i] = find(dialog, name, kChargeWidgetStatic);
        }
    }
    if (!s_chargeGauge) return; // Client data without the charge widgets.
    const LONG index = s_chargeIndex;
    const bool charging = s_chargeActiveSkill && s_chargeCaster && index >= 0 && index < s_chargeSkillCount &&
                          dialog[0x500] != 0;
    if (!charging) {
        if (s_chargeBarShown) ChargeHideBar();
        return;
    }
    const int stages = s_chargeStageCount[index] < kChargeStepWidgets ? s_chargeStageCount[index] : kChargeStepWidgets;
    // The server shortens the stages with the cast speed; the dialog has the duration it sent.
    const DWORD dialogTotal = *(const DWORD*)(dialog + 0x4F8);
    const double total = dialogTotal ? (double)dialogTotal : (double)s_chargeTotalMs[index];
    const double scale = s_chargeTotalMs[index] ? total / s_chargeTotalMs[index] : 1.0;
    const double elapsed = (double)(GetTickCount64() - (ULONGLONG)s_chargeStartTick);
    if (!s_chargeBarShown) {
        ChargeShowWidget(s_chargeGauge, true);
        for (int i = 0; i < kChargeStepWidgets; ++i) ChargeShowWidget(s_chargeSteps[i], i < stages);
        s_chargeBarShown = true;
    }
    // The bar fills again on every stage, as on 5.8: maximum = length of the current stage.
    int stage = 1;
    double stageStart = 0;
    for (int i = 0; i + 1 < stages; ++i) {
        const double next = stageStart + s_chargeStageMs[index][i] * scale;
        if (elapsed <= next) break;
        stage = i + 2;
        stageStart = next;
    }
    const double stageLength = stage == stages ? total - stageStart : s_chargeStageMs[index][stage - 1] * scale;
    const double inStage = elapsed - stageStart;
    s_chargeGaugeMaximum(s_chargeGauge, stageLength);
    s_chargeGaugeValue(s_chargeGauge, inStage < stageLength ? inStage : stageLength, 1);
    if (stage != s_chargeBarStage) {
        s_chargeBarStage = stage;
        ChargeSetWidgetState(s_chargeGauge, ChargeColour(stage, stages));
        for (int i = 0; i < stages; ++i)
            ChargeSetWidgetState(s_chargeSteps[i], i < stage ? ChargeColour(i + 1, stages) : 0);
    }
}

static INT_PTR __fastcall ChargeDialogFrameHook(BYTE* dialog) {
    const INT_PTR result = s_chargeDialogFrame(dialog);
    __try {
        ChargeUpdateDialog(dialog);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return result;
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

        // Frame of DlgSkillDelay: push rbx; sub rsp,20h; cmp dword [rcx+4F8h],0; mov rbx,rcx; je;
        // cmp byte [rcx+500h],0; je. Gauge maximum and value are the calls at +5Ah and +91h.
        static const BYTE frame[] = {
            0x40,0x53,0x48,0x83,0xec,0x20,0x83,0xb9,0xf8,0x04,0x00,0x00,0x00,0x48,0x8b,0xd9,
            0x0f,0x84,0,0,0,0,0x80,0xb9,0x00,0x05,0x00,0x00,0x00,0x0f,0x84,0,0,0,0
        };
        static const char frameMask[] = "xxxxxxxxxxxxxxxxxx????xxxxxxxxx????";
        static_assert(sizeof(frameMask) - 1 == sizeof(frame), "Charge frame signature mask length");

        BYTE* sendPacket = QunaFindUnique(base, nt, send, sendMask, sizeof(send));
        BYTE* requestAction = QunaFindUnique(base, nt, request, requestMask, sizeof(request));
        BYTE* dialogFrame = QunaFindUnique(base, nt, frame, frameMask, sizeof(frame));
        s_chargeChecked = true;
        if (!sendPacket || !requestAction || !dialogFrame || dialogFrame[0x5a] != 0xe8 || dialogFrame[0x91] != 0xe8) {
            OutputDebugStringA("[Charge] Unsupported client; signatures not unique.\n");
            __leave;
        }
        s_chargeSend = (ChargeSendPacket)sendPacket;
        s_chargeRequest = (ChargeRequestAction)requestAction;
        s_chargeDialogFrame = (ChargeDialogFrame)dialogFrame;
        s_chargeGaugeMaximum = (ChargeGaugeMaximum)(dialogFrame + 0x5f + *(int32_t*)(dialogFrame + 0x5b));
        s_chargeGaugeValue = (ChargeGaugeValue)(dialogFrame + 0x96 + *(int32_t*)(dialogFrame + 0x92));
        s_qunaServerPacketObserver = ChargeOnServerPacket;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_chargeChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_chargeSend, ChargeSendPacketHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_chargeRequest, ChargeRequestActionHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_chargeDialogFrame, ChargeDialogFrameHook);
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
