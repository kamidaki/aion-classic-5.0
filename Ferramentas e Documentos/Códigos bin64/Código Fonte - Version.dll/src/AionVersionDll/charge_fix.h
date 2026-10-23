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
//   never left during the charge; it is answered here instead, with the fire packet (kChargeFireWire:
//   0x3E0, not the 234 of the Live client, which the 5.0 client uses for the hair slot expansion).
//
// Plain body: [H length][H wire opcode][C 0x6F][H ~wire opcode][payload]; wire = (op + 0xC4) ^ 0x36.
// C_USE_SKILL (0x21, wire 0xD3) payload starts with [H skill id] (builder at 0x198180).
// The charge skills come from charge_skills.txt next to version.dll (bard_skills_58.py writes it):
// one "skill_id motion n ms:skill ms:skill ..." per line (motion_name, charge_timeN and skill_nameN of the
// 5.8 data, the stage skills with their 5.0 ids; the motion is informative, n is how many charge
// animations it has: ccast_<weapon>_<motion>_001.._00n).
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
// Other fixes that rewrite outgoing packets (globaltrade_fix.h) set this filter: it returns true when it
// handled the packet itself, with the result of the send in *result.
static bool (*s_chargeSendFilter)(void*, BYTE*, int, INT_PTR*) = nullptr;

static constexpr WORD kChargeUseSkillWire = (0x21 + 0xC4) ^ 0x36;
// The Live 5.8 opcode of C_FIRE_CHARGE_SKILL (234, wire 0x198) is, in the 5.0 client, the hair slot
// expansion of the Wardrobe (serializer packet 0x11A). The fire goes out as 0x3E0 (wire 0x492), above
// every opcode the 5.0 client sends; CM_USE_CHARGE_SKILL is registered there.
static constexpr WORD kChargeFireWire = (0x3E0 + 0xC4) ^ 0x36;
static constexpr BYTE kChargeStaticByte = 0x6F;
static constexpr int kChargeMaxSkills = 64;
// The server may end the charge a little after the sum of the stages (cast speed only shortens it).
static constexpr ULONGLONG kChargeMarginMs = 500;

static constexpr int kChargeMaxStages = 4;
static WORD s_chargeSkillIds[kChargeMaxSkills] = {};
static DWORD s_chargeStageMs[kChargeMaxSkills][kChargeMaxStages] = {};
static WORD s_chargeStageSkill[kChargeMaxSkills][kChargeMaxStages] = {};
static int s_chargeStageCount[kChargeMaxSkills] = {};
// Charge animations of the motion, one digit per ccast_<weapon>_<motion>_00N of the 5.8 .cal, the
// same digit for the same .caf ("123", "122": the _003 repeats the _002_loop).
static char s_chargeAnimations[kChargeMaxSkills][kChargeMaxStages + 1] = {};
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
        unsigned skill = 0, ms[kChargeMaxStages] = {}, ids[kChargeMaxStages] = {};
        if (line[0] == '#') continue;
        char motion[48] = {};
        char animations[kChargeMaxStages + 1] = {};
        const int read = sscanf_s(line, "%u %47s %4s %u:%u %u:%u %u:%u %u:%u", &skill, motion, (unsigned)sizeof(motion),
                                  animations, (unsigned)sizeof(animations), &ms[0], &ids[0], &ms[1], &ids[1],
                                  &ms[2], &ids[2], &ms[3], &ids[3]);
        if (read < 5 || (read - 3) % 2 != 0 || skill == 0 || skill > 0xFFFF) continue;
        const int index = s_chargeSkillCount++;
        s_chargeSkillIds[index] = (WORD)skill;
        if (strspn(animations, "123456789") == strlen(animations)) strcpy_s(s_chargeAnimations[index], animations);
        s_chargeStageCount[index] = (read - 3) / 2;
        for (int i = 0; i < s_chargeStageCount[index]; ++i) {
            s_chargeStageMs[index][i] = ms[i];
            s_chargeStageSkill[index][i] = (WORD)ids[i];
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
    if (s_chargeSendFilter) {
        INT_PTR result = 0;
        if (s_chargeSendFilter(connection, body, length, &result)) return result;
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
// Start of the charge the bar shows. A cancel closes the dialog and its frame function stops, so the
// end of that charge is never seen there: a new start is what tells the bar to begin again.
static LONG64 s_chargeBarStart = 0;

// Name of the cast ("Fiery Descant 1Stage" on 5.8): the name the dialog writes (+0x518) plus the stage
// and STR_CHARGE_STEP, as the 5.8 dialog does. The 5.0 has no such string: teste_harpa_58.py adds it
// with this id. Strings by id: manager() + 0x10 -> table 0 -> 0xA34F00 (table, id), the same calls
// the dialog makes for its own texts (0x65F9DC). UIStatic::SetText (vtable +0x288, 0xB1E380) is
// where the dialog writes the name, so the name it writes is kept as the base of the stage text.
static constexpr int kChargeStepStringId = 1990006;
using ChargeManager = BYTE* (__fastcall*)();
using ChargeContainerFind = void** (__fastcall*)(void*, const int*);
using ChargeGetString = const wchar_t* (__fastcall*)(void*, int);
using ChargeSetText = void (__fastcall*)(void*, const wchar_t*);
static ChargeManager s_chargeManager = nullptr;
static ChargeContainerFind s_chargeContainerFind = nullptr;
static ChargeGetString s_chargeGetString = nullptr;
static ChargeSetText s_chargeSetText = nullptr;
static void* s_chargeNameWidget = nullptr;
static wchar_t s_chargeBaseName[128] = {};

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

// Body animation of each stage, as on 5.8: ccast_<weapon>_<motion>_00N, the last one a loop
// (LM_ccast_harp_SongBattle01_003_loop.caf). How the 5.0 plays the cast animation:
// - the cast start (0x923420) calls SetAction (0x960880: character, 1, 0x1C = cast, parameters),
//   which keeps the action in character+0xBA0/+0xBA4, its parameters in +0xBB0..+0xBDB and raises
//   +0xBA8, the signal CharacterObject::StartAnimation (0x9373A0) answers on the next frame;
// - StartAnimation builds the name (ccast_harp_SongBattle01 + "_%01d%02d", 0x936270) with the
//   variant forced by character+0xB5D, the field the skill result (0x923BA0) fills from the
//   packet for the fire animation; without it the variant is drawn by weight.
// The 5.0 has no stages: the _001 (1.6 s) ended and the character stood still for the rest of
// the charge. On each new stage the cast action is set again, as the cast start does, with the
// stage in +0xB5D and the skill of the stage in the parameters (+0x08, kept at +0xBB8): its
// cast_fx (FC_Ba_SongofBattle.G1.cast_lv2/lv3) is played as on 5.8, with the same motion. This is
// done for every character casting a charge (ChargeUpdateCharacter).
// The cast_fx is not played by SetAction: an event of the body animation reaches 0x948790
// (character, event), which reads the skill at +0xBB8 and its level at +0xBBE, takes the cast_fx
// (0xA13B40, kind 0 = skill+0x330) and plays it in slot 0x38 (0x948C80); the event is only tested
// for null. A stage whose animation is the one already playing (SongPowerShock01 has only _001, the
// last stage of a loop) must not set the action again, which restarts the animation from its first
// frame: the stage skill goes to +0xBB8 and its cast_fx is played directly.
static constexpr size_t kChargeVariant = 0xB5D;
static constexpr size_t kChargeActionType = 0xBA0;
static constexpr size_t kChargeActionId = 0xBA4;
static constexpr size_t kChargeActionParameters = 0xBB0;
static constexpr int kChargeActionCastType = 1;
static constexpr int kChargeActionCast = 0x1C;

using ChargeSetAction = void (__fastcall*)(BYTE*, int, int, void*);
static ChargeSetAction s_chargeSetAction = nullptr;
using ChargePlayCastFx = void (__fastcall*)(BYTE*, void*);
static ChargePlayCastFx s_chargePlayCastFx = nullptr;

static void ChargePlayStageAnimation(BYTE* character, int index, int stage) {
    if (!s_chargeSetAction) return;
    // Stage N plays ccast_<weapon>_<motion>_00N (the last one for later stages); the .cal may point two
    // of them to the same .caf (SongGravity01 _002 and _003 = _002_loop, SongPowerShock01 too), and then
    // the animation already playing goes on. Without the column the variant is not forced (0).
    const char* animations = s_chargeAnimations[index];
    const int count = (int)strlen(animations);
    const int variant = count <= 0 ? 0 : stage < count ? stage : count;
    const int previous = count <= 0 ? 0 : stage - 1 < count ? stage - 1 : count;
    const WORD stageSkill = s_chargeStageSkill[index][stage - 1];
    if (count > 0 && animations[variant - 1] == animations[previous - 1] && stageSkill && s_chargePlayCastFx) {
        *(DWORD*)(character + kChargeActionParameters + 0x08) = stageSkill;
        s_chargePlayCastFx(character, character);
        return;
    }
    // The parameters as SetAction keeps them: 0x20 bytes, a double and an int (0x2C).
    alignas(16) BYTE parameters[0x30] = {};
    memcpy(parameters, character + kChargeActionParameters, 0x2C);
    if (stageSkill) *(DWORD*)(parameters + 0x08) = stageSkill;
    character[kChargeVariant] = (BYTE)variant;
    s_chargeSetAction(character, kChargeActionCastType, kChargeActionCast, parameters);
}

// Stages of every character, not only the local player: on 5.8 the cast bars of the target, of the
// target's target and of the spectated group (target_delay_dialog, target_assist_delay_dialog,
// spectator_group_delay_dialog) have the charge widgets too, and the protocol has no stage packet
// (only the cast start and the fire), so each client follows a charge by the time since its start.
// CharacterObject's frame (0x939020, called by the scene for every character) runs during the cast
// too (it calls StartAnimation, 0x9373A0, only out of it: a hook there never saw a cast). The cast
// start keeps the duration the server sent at +0xBC0 and the start at +0xBC4, in milliseconds since
// boot. The client reads that clock through a WinLicense stub (0x1CEEAE5) that faults when called from
// this DLL; GetTickCount and timeGetTime, logged at a cast start, were within 16 ms of +0xBC4 (stages
// are 1.5 s or more). The stage the character is in is the one of
// the skill at +0xBB8 (stage 1 is the charge skill itself; every new stage puts its skill there).
static constexpr size_t kChargeActionDuration = 0xBC0;
static constexpr size_t kChargeActionStart = 0xBC4;
using ChargeCharacterFrame = INT_PTR (__fastcall*)(BYTE*, INT_PTR);
static ChargeCharacterFrame s_chargeCharacterFrame = nullptr;

static void ChargeUpdateCharacter(BYTE* character) {
    if (*(const int*)(character + kChargeActionType) != kChargeActionCastType ||
        *(const int*)(character + kChargeActionId) != kChargeActionCast) return;
    const DWORD skill = *(const DWORD*)(character + kChargeActionParameters + 0x08);
    int index = -1, current = 0;
    for (int i = 0; i < s_chargeSkillCount && index < 0; ++i)
        for (int k = 0; k < s_chargeStageCount[i]; ++k)
            if (s_chargeStageSkill[i][k] == skill) {
                index = i;
                current = k + 1;
                break;
            }
    if (index < 0 || !s_chargeTotalMs[index]) return;
    const DWORD duration = *(const DWORD*)(character + kChargeActionDuration);
    if (!duration) return;
    const double scale = (double)duration / s_chargeTotalMs[index];
    // GetTickCount moves in ~16 ms steps and may still be behind the start.
    const LONG since = (LONG)(GetTickCount() - *(const DWORD*)(character + kChargeActionStart));
    const double elapsed = since > 0 ? (double)since : 0.0;
    int stage = 1;
    double next = 0;
    for (int i = 0; i + 1 < s_chargeStageCount[index]; ++i) {
        next += s_chargeStageMs[index][i] * scale;
        if (elapsed <= next) break;
        stage = i + 2;
    }
    if (stage > current) ChargePlayStageAnimation(character, index, stage);
}

static INT_PTR __fastcall ChargeCharacterFrameHook(BYTE* character, INT_PTR a2) {
    __try {
        if (character) ChargeUpdateCharacter(character);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return s_chargeCharacterFrame(character, a2);
}

// The cast bar the dialog selected (DlgSkillDelay keeps two at +0x508/+0x510, the index at +0x520).
// While charging it is hidden, as the 5.8 dialog hides its "general" group for the "charge" one:
// otherwise it is drawn over the charge bar.
static void* ChargeNativeBar(BYTE* dialog) {
    const int index = *(const int*)(dialog + 0x520);
    return index >= 0 && index < 2 ? *(void**)(dialog + 0x508 + 8 * index) : nullptr;
}

static const wchar_t* ChargeStepText() {
    if (!s_chargeManager || !s_chargeContainerFind || !s_chargeGetString) return nullptr;
    const int table = 0;
    void** strings = s_chargeContainerFind(s_chargeManager() + 0x10, &table);
    const wchar_t* text = strings && *strings ? s_chargeGetString(*strings, kChargeStepStringId) : nullptr;
    return text && *text ? text : nullptr; // Client data without the string: the name stays as it is.
}

// Name with the stage, or the plain name for stage 0.
static void ChargeComposeName(int stage, wchar_t* name, size_t size) {
    const wchar_t* step = stage > 0 ? ChargeStepText() : nullptr;
    if (step) swprintf_s(name, size, L"%s %d%s", s_chargeBaseName, stage, step);
    else wcscpy_s(name, size, s_chargeBaseName);
}

static void ChargeShowStageName(int stage) {
    if (!s_chargeNameWidget || !s_chargeSetText || !s_chargeBaseName[0]) return;
    wchar_t name[192];
    ChargeComposeName(stage, name, _countof(name));
    s_chargeSetText(s_chargeNameWidget, name);
}

// The dialog writes the name before its first frame (first cast after login): the dialogs are taken
// from their constructor (0x65EF10, sets the DlgSkillDelay vtable and clears +0x4F8..+0x520), so the
// name widget (+0x518) is known on that first write.
using ChargeDialogConstructor = BYTE* (__fastcall*)(BYTE*);
static ChargeDialogConstructor s_chargeDialogConstructor = nullptr;
static constexpr int kChargeMaxDialogs = 4;
static BYTE* s_chargeDialogs[kChargeMaxDialogs] = {};
static void* s_chargeDialogVtable = nullptr;

static BYTE* __fastcall ChargeDialogConstructorHook(BYTE* dialog) {
    BYTE* result = s_chargeDialogConstructor(dialog);
    __try {
        s_chargeDialogVtable = *(void**)dialog;
        for (BYTE*& slot : s_chargeDialogs) {
            if (slot == dialog) break;
            if (!slot || *(void**)slot != s_chargeDialogVtable) { slot = dialog; break; } // empty or destroyed
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return result;
}

static bool ChargeHasWidgets(BYTE* dialog);

static bool ChargeIsDialogName(void* widget) {
    for (BYTE* dialog : s_chargeDialogs)
        if (dialog && *(void**)dialog == s_chargeDialogVtable && *(void**)(dialog + 0x518) == widget &&
            ChargeHasWidgets(dialog))
            return true;
    return false;
}

static void ChargeHideBar();
static void ChargeHideWidgets();

static void __fastcall ChargeSetTextHook(void* widget, const wchar_t* text) {
    __try {
        // The cast name written while a charge is pending is the charge's own.
        if (s_chargeActiveSkill && widget && text && widget != s_chargeNameWidget && ChargeIsDialogName(widget))
            s_chargeNameWidget = widget;
        if (widget && widget == s_chargeNameWidget && text) {
            wcsncpy_s(s_chargeBaseName, text, _TRUNCATE);
            // A charge sent (C_USE_SKILL of a charge skill) and not ended: the dialog shows the cast before
            // the server answers, so a new charge starts on stage 1, as on 5.8; the charge on the bar keeps
            // its stage.
            const bool barCharge = s_chargeBarShown && s_chargeBarStart == s_chargeStartTick && s_chargeBarStage > 0;
            const int stage = !s_chargeActiveSkill ? 0 : barCharge ? s_chargeBarStage : 1;
            if (stage > 0) {
                wchar_t name[192];
                ChargeComposeName(stage, name, _countof(name));
                s_chargeSetText(widget, name);
                return;
            }
            if (s_chargeBarShown) ChargeHideBar();
            else ChargeHideWidgets();
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    s_chargeSetText(widget, text);
}

// UI effect on a widget (0xB62D90, as the wardrobe plays sys_UIfx.wardrobe.extend at 0x6FD212):
// (widget, effect, 1, 1, offset xyz, slot it writes, empty callback; +0x38 = its target).
// The 5.8 dialog plays sys_UIfx.Charge.basic on the bubble of the stage reached (Game.dll 5.8
// 0x442470). Its sys_UIfx.Charge.last on the bar is left out: on 5.0 it piles up on every cast.
// The effects stay on the widget until removed: the manager of widget effects (0xB618F0) keeps them
// per widget; its vtable +0x08 (widget, 0, 1) clears them before a new one, as the client does before
// playing (0x1F90E5), and +0x20 (widget) removes them all, as the dialogs do when they close.
using ChargePlayEffect = bool (__fastcall*)(void*, const char*, int, int, const float*, INT_PTR, void*);
using ChargeEffectManager = void* (__fastcall*)();
using ChargeClearEffects = void (__fastcall*)(void*, void*, int, bool);
using ChargeRemoveEffects = void (__fastcall*)(void*, void*);
static ChargePlayEffect s_chargePlayEffect = nullptr;
static ChargeEffectManager s_chargeEffectManager = nullptr;

static void ChargePlayWidgetEffect(void* widget, const char* effect) {
    if (!widget || !s_chargePlayEffect || !s_chargeEffectManager) return;
    if (void* manager = s_chargeEffectManager())
        ChargeVirtual<ChargeClearEffects>(manager, 0x08)(manager, widget, 0, true);
    const float offset[3] = {};
    alignas(16) BYTE callback[0x40] = {};
    s_chargePlayEffect(widget, effect, 1, 1, offset, 0, callback);
}

static void ChargeRemoveWidgetEffects(void* widget) {
    if (!widget || !s_chargeEffectManager) return;
    if (void* manager = s_chargeEffectManager()) ChargeVirtual<ChargeRemoveEffects>(manager, 0x20)(manager, widget);
}

// The dialog also shows our widgets when it opens for a cast (proven on video: the first cast after
// login showed the empty charge bar, its light at the start, and the three bubbles), so without a
// charge they are kept hidden on every frame and at every cast start, not only after a charge.
static bool ChargeWidgetVisible(void* widget) {
    return widget && (*(const ULONGLONG*)((BYTE*)widget + 0x28) & kChargeWidgetVisible);
}

static void ChargeHideWidgets() {
    if (ChargeWidgetVisible(s_chargeGauge)) ChargeShowWidget(s_chargeGauge, false);
    for (void* step : s_chargeSteps) {
        if (!ChargeWidgetVisible(step)) continue;
        ChargeShowWidget(step, false);
        ChargeRemoveWidgetEffects(step);
    }
}

static void ChargeHideBar() {
    ChargeHideWidgets();
    for (void* step : s_chargeSteps) ChargeRemoveWidgetEffects(step);
    if (s_chargeDialog) ChargeShowWidget(ChargeNativeBar(s_chargeDialog), true);
    s_chargeBarShown = false;
    s_chargeBarStage = 0;
    ChargeShowStageName(0);
}

// The frame function runs for every DlgSkillDelay: the own cast bar (skill_delay_dialog, the one with
// the charge widgets) and the cast bar of the target (target_delay_dialog) when an enemy has one. Taking
// each as "the dialog" restarted the bar on every frame while a target was casting: the stage went back
// to 0 and the bubble effect was played again each frame (the endless flash), and the name widget became
// the target's. Only the dialog with the charge widgets is used; the others are remembered and skipped.
static constexpr int kChargeOtherDialogs = 8;
static BYTE* s_chargeOtherDialogs[kChargeOtherDialogs] = {};
static int s_chargeOtherNext = 0;

static bool ChargeHasWidgets(BYTE* dialog) {
    return ChargeVirtual<ChargeFindChild>(dialog, 0x368)(dialog, "charge_gauge", kChargeWidgetGauge) != nullptr;
}

static bool ChargeIsOtherDialog(BYTE* dialog) {
    for (BYTE* other : s_chargeOtherDialogs)
        if (other == dialog) return true;
    if (ChargeHasWidgets(dialog)) return false;
    s_chargeOtherDialogs[s_chargeOtherNext] = dialog;
    s_chargeOtherNext = (s_chargeOtherNext + 1) % kChargeOtherDialogs;
    return true;
}

static void ChargeUpdateDialog(BYTE* dialog) {
    if (dialog != s_chargeDialog) {
        if (ChargeIsOtherDialog(dialog)) return;
        s_chargeDialog = dialog;
        s_chargeBarShown = false;
        s_chargeBarStage = 0;
        const ChargeFindChild find = ChargeVirtual<ChargeFindChild>(dialog, 0x368);
        s_chargeGauge = find(dialog, "charge_gauge", kChargeWidgetGauge);
        // The light at the end of the fill ("skilldelay", drawn by the gauge when +0x898 is set): the
        // dialog sets it on its own bars when it loads (0x65F074); the charge bar is ours.
        if (s_chargeGauge) *(DWORD*)((BYTE*)s_chargeGauge + 0x898) = 1;
        s_chargeNameWidget = *(void**)(dialog + 0x518);
        for (int i = 0; i < kChargeStepWidgets; ++i) {
            char name[16];
            sprintf_s(name, "charge_step%d", i + 1);
            s_chargeSteps[i] = find(dialog, name, kChargeWidgetStatic);
        }
    }
    if (!s_chargeGauge) return; // Client data without the charge widgets.
    const LONG index = s_chargeIndex;
    const bool charging = s_chargeActiveSkill && s_chargeCaster && index >= 0 && index < s_chargeSkillCount &&
                          dialog[0x500] != 0 && GetTickCount64() < s_chargeActiveUntil;
    if (!charging) {
        if (s_chargeBarShown) ChargeHideBar();
        else ChargeHideWidgets();
        return;
    }
    const int stages = s_chargeStageCount[index] < kChargeStepWidgets ? s_chargeStageCount[index] : kChargeStepWidgets;
    // The server shortens the stages with the cast speed; the dialog has the duration it sent.
    const DWORD dialogTotal = *(const DWORD*)(dialog + 0x4F8);
    const double total = dialogTotal ? (double)dialogTotal : (double)s_chargeTotalMs[index];
    const double scale = s_chargeTotalMs[index] ? total / s_chargeTotalMs[index] : 1.0;
    const double elapsed = (double)(GetTickCount64() - (ULONGLONG)s_chargeStartTick);
    if (s_chargeBarStart != s_chargeStartTick) {
        s_chargeBarStart = s_chargeStartTick;
        s_chargeBarShown = false;
        s_chargeBarStage = 0;
    }
    // The client shows its own bar again on every cast start (the stage animations restart the cast too).
    void* nativeBar = ChargeNativeBar(dialog);
    if (nativeBar && (*(const ULONGLONG*)((BYTE*)nativeBar + 0x28) & kChargeWidgetVisible)) ChargeShowWidget(nativeBar, false);
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
        ChargeShowStageName(stage);
        ChargeSetWidgetState(s_chargeGauge, ChargeColour(stage, stages));
        for (int i = 0; i < stages; ++i)
            ChargeSetWidgetState(s_chargeSteps[i], i < stage ? ChargeColour(i + 1, stages) : 0);
        ChargePlayWidgetEffect(s_chargeSteps[stage - 1], "sys_UIfx.Charge.basic");
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
        // SetAction: mov [rsp+8],rbx; mov [rsp+10h],rsi; push rdi; sub rsp,50h;
        // movups xmm3,[rcx+0BB0h]; mov r10d,[rcx+0BA4h]
        static const BYTE setAction[] = {
            0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x50,0x0f,
            0x10,0x99,0xb0,0x0b,0x00,0x00,0x44,0x8b,0x91,0xa4,0x0b,0x00,0x00
        };
        static const char setActionMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(setActionMask) - 1 == sizeof(setAction), "Charge SetAction signature mask length");
        s_chargeSetAction = (ChargeSetAction)QunaFindUnique(base, nt, setAction, setActionMask, sizeof(setAction));
        // Cast_fx of the action (0x948790): push rbp; push r14; lea rbp,[rsp-3C8h]; sub rsp,4C8h;
        // cmp qword [rcx+8],0; mov r14,rcx; je; test rdx,rdx; je; cmp qword [rcx+12C8h],0
        static const BYTE castFx[] = {
            0x40,0x55,0x41,0x56,0x48,0x8d,0xac,0x24,0x38,0xfc,0xff,0xff,0x48,0x81,0xec,0xc8,0x04,0x00,0x00,
            0x48,0x83,0x79,0x08,0x00,0x4c,0x8b,0xf1,0x0f,0x84,0,0,0,0,0x48,0x85,0xd2,0x0f,0x84,0,0,0,0,
            0x48,0x83,0xb9,0xc8,0x12,0x00,0x00,0x00
        };
        static const char castFxMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx????xxxxx????xxxxxxxx";
        static_assert(sizeof(castFxMask) - 1 == sizeof(castFx), "Charge cast_fx signature mask length");
        s_chargePlayCastFx = (ChargePlayCastFx)QunaFindUnique(base, nt, castFx, castFxMask, sizeof(castFx));
        // CharacterObject's frame (0x939020): mov rax,rsp; sub rsp,0D8h; mov r8d,[rip+x]; mov [rax+8],rbx;
        // mov rbx,rdx; mov [rax+10h],rsi; lea rsi,[rip+x]
        static const BYTE characterFrame[] = {
            0x48,0x8b,0xc4,0x48,0x81,0xec,0xd8,0x00,0x00,0x00,0x44,0x8b,0x05,0,0,0,0,0x48,0x89,0x58,0x08,
            0x48,0x8b,0xda,0x48,0x89,0x70,0x10,0x48,0x8d,0x35
        };
        static const char characterFrameMask[] = "xxxxxxxxxxxxx????xxxxxxxxxxxxxx";
        static_assert(sizeof(characterFrameMask) - 1 == sizeof(characterFrame), "Charge character frame mask length");
        s_chargeCharacterFrame = (ChargeCharacterFrame)QunaFindUnique(base, nt, characterFrame, characterFrameMask,
                                                                      sizeof(characterFrame));
        // Text of the dialog by id (0x65F9D7): mov [rsp+70h],r12d; call manager; lea rdx,[rsp+70h];
        // lea rcx,[rax+10h]; call find; mov edx,902803; mov rcx,[rax]; mov rax,[rdi+518h];
        // mov rbx,[rax]; call string; mov rcx,[rdi+518h]; mov rdx,rax; call [rbx+288h]
        static const BYTE text[] = {
            0x44,0x89,0x64,0x24,0x70,0xe8,0,0,0,0,0x48,0x8d,0x54,0x24,0x70,0x48,0x8d,0x48,0x10,0xe8,0,0,0,0,
            0xba,0x93,0xc6,0x0d,0x00,0x48,0x8b,0x08,0x48,0x8b,0x87,0x18,0x05,0x00,0x00,0x48,0x8b,0x18,0xe8,0,0,0,0,
            0x48,0x8b,0x8f,0x18,0x05,0x00,0x00,0x48,0x8b,0xd0,0xff,0x93,0x88,0x02,0x00,0x00
        };
        static const char textMask[] = "xxxxxx????xxxxxxxxxx????xxxxxxxxxxxxxxxxxxx????xxxxxxxxxxxxxxxx";
        static_assert(sizeof(textMask) - 1 == sizeof(text), "Charge text signature mask length");
        // UIStatic::SetText: sub rsp,38h; mov r10,[rcx]; lea rax,[rcx+384h]; movzx r9d,byte [rcx+380h];
        // lea r8,[rcx+160h]
        static const BYTE setText[] = {
            0x48,0x83,0xec,0x38,0x4c,0x8b,0x11,0x48,0x8d,0x81,0x84,0x03,0x00,0x00,0x44,0x0f,0xb6,0x89,
            0x80,0x03,0x00,0x00,0x4c,0x8d,0x81,0x60,0x01,0x00,0x00
        };
        static const char setTextMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(setTextMask) - 1 == sizeof(setText), "Charge SetText signature mask length");
        if (BYTE* t = QunaFindUnique(base, nt, text, textMask, sizeof(text))) {
            s_chargeManager = (ChargeManager)(t + 10 + *(int32_t*)(t + 6));
            s_chargeContainerFind = (ChargeContainerFind)(t + 24 + *(int32_t*)(t + 20));
            s_chargeGetString = (ChargeGetString)(t + 47 + *(int32_t*)(t + 43));
        }
        s_chargeSetText = (ChargeSetText)QunaFindUnique(base, nt, setText, setTextMask, sizeof(setText));
        // Constructor: push rbx; sub rsp,20h; mov rbx,rcx; call base; lea rax,[vtable]; mov [rbx],rax;
        // xor eax,eax; mov [rbx+508h],rax; mov [rbx+510h],rax; mov [rbx+518h],rax; mov [rbx+500h],al
        static const BYTE constructor[] = {
            0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0xe8,0,0,0,0,0x48,0x8d,0x05,0,0,0,0,0x48,0x89,0x03,
            0x33,0xc0,0x48,0x89,0x83,0x08,0x05,0x00,0x00,0x48,0x89,0x83,0x10,0x05,0x00,0x00,0x48,0x89,0x83,
            0x18,0x05,0x00,0x00,0x88
        };
        static const char constructorMask[] = "xxxxxxxxxx????xxx????xxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(constructorMask) - 1 == sizeof(constructor), "Charge dialog constructor signature mask length");
        s_chargeDialogConstructor = (ChargeDialogConstructor)QunaFindUnique(base, nt, constructor, constructorMask, sizeof(constructor));
        // Widget effect: mov rax,rsp; mov [rax+8],rbx; mov [rax+10h],rbp; mov [rax+18h],rsi;
        // mov [rax+20h],rdi; push r14; sub rsp,80h; mov rbx,[rsp+0C0h]; mov r14,rcx; mov edi,r9d
        static const BYTE effect[] = {
            0x48,0x8b,0xc4,0x48,0x89,0x58,0x08,0x48,0x89,0x68,0x10,0x48,0x89,0x70,0x18,0x48,0x89,0x78,0x20,
            0x41,0x56,0x48,0x81,0xec,0x80,0x00,0x00,0x00,0x48,0x8b,0x9c,0x24,0xc0,0x00,0x00,0x00,0x4c,0x8b,
            0xf1,0x41,0x8b,0xf9
        };
        static const char effectMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(effectMask) - 1 == sizeof(effect), "Charge widget effect signature mask length");
        s_chargePlayEffect = (ChargePlayEffect)QunaFindUnique(base, nt, effect, effectMask, sizeof(effect));
        // Effect manager: sub rsp,28h; mov rax,[instance]; test rax,rax; jnz ...; add qword [count],4B0h
        static const BYTE effectManager[] = {
            0x48,0x83,0xec,0x28,0x48,0x8b,0x05,0,0,0,0,0x48,0x85,0xc0,0x0f,0x85,0,0,0,0,0x48,0x81,0x05
        };
        static const char effectManagerMask[] = "xxxxxxx????xxxxx????xxx";
        static_assert(sizeof(effectManagerMask) - 1 == sizeof(effectManager), "Charge effect manager mask length");
        s_chargeEffectManager = (ChargeEffectManager)QunaFindUnique(base, nt, effectManager, effectManagerMask,
                                                                    sizeof(effectManager));
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
        // Every client follows the charges it sees, also one that never cast a charge itself.
        if (!s_chargeTableRead) ChargeReadTable();
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
        if (error == NO_ERROR && s_chargeCharacterFrame && s_chargeSetAction)
            error = DetourAttach(&(PVOID&)s_chargeCharacterFrame, ChargeCharacterFrameHook);
        if (error == NO_ERROR && s_chargeSetText) error = DetourAttach(&(PVOID&)s_chargeSetText, ChargeSetTextHook);
        if (error == NO_ERROR && s_chargeSetText && s_chargeDialogConstructor)
            error = DetourAttach(&(PVOID&)s_chargeDialogConstructor, ChargeDialogConstructorHook);
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
