#pragma once

// Classic 5.0 x64: the client has no harp. Its weapon type enum stops at 18 (1..14 are the combat
// weapons, 15..18 the gathering tools) and the slot the harp has in the Live client, 8, belongs to
// the chainblade here. This adds the harp as a new type, 19.
//
// Covered so far:
//  - the parser of the <weapon_type> field of client_items.xml, a loop over a {name, value} table
//    that returns 0 for an unknown name;
//  - the function that turns a weapon type into the animation name suffix ("_orb", "_2blade", ...),
//    a jump table over 0..18 that leaves the suffix empty for anything else;
//  - the function that names the bone a weapon mesh is attached to;
//  - the second mesh, the stick, in the in-world weapon refresh;
//  - the hit effect of the basic ranged attack.
// The other readers of the type (character preview windows, damage animation, skill requirement)
// still do not know 19.
#if defined(_M_AMD64)
static constexpr int kHarpWeaponType = 19;

using HarpParseWeaponType = int (__fastcall*)(const wchar_t*);
using HarpWeaponSuffix = void* (__fastcall*)(int, int, char*, size_t);
static HarpParseWeaponType s_harpParse = nullptr;
static HarpWeaponSuffix s_harpSuffix = nullptr;

static int __fastcall HarpParseWeaponTypeHook(const wchar_t* name) {
    if (name && _wcsicmp(name, L"2h_harp") == 0) return kHarpWeaponType;
    return s_harpParse(name);
}

// dual = an off-hand weapon is equipped; the harp is two-handed, so it does not apply.
static void* __fastcall HarpWeaponSuffixHook(int dual, int type, char* out, size_t size) {
    if (type != kHarpWeaponType) return s_harpSuffix(dual, type, out, size);
    if (out && size) strncpy_s(out, size, "_harp", _TRUNCATE);
    return out;
}

// Bone a weapon mesh is attached to: (item id, state, hand, flag, out, size). hand 0 is the main
// mesh and 1 the second one; state 1 and 5 are "drawn", anything else is sheathed. For an unknown
// type the client falls to the right hand when drawn and to no bone at all when sheathed, which
// hides the weapon. The harp rules are the ones of weapon type 8 in the Live 5.8 Game.dll:
//   drawn:    harp on Lhand_bone, stick on Rhand_bone
//   sheathed: harp on Lback_bone, stick hidden
//   bone named by the item itself: the side is mirrored the other way round (hand 0 R -> L,
//   hand 1 L -> R; every other type only turns R into L for hand 1)
using HarpAttachBone = void (__fastcall*)(int, int, int, int, char*, int);
using HarpGetTables = void* (__fastcall*)();
using HarpFindTable = void** (__fastcall*)(void*, int*);
using HarpFindItem = BYTE* (__fastcall*)(void*, int*);
static HarpAttachBone s_harpBone = nullptr;
static HarpGetTables s_harpGetTables = nullptr;
static HarpFindTable s_harpFindTable = nullptr;
static HarpFindItem s_harpFindItem = nullptr;
static constexpr int kHarpItemTable = 0xb;
static constexpr size_t kHarpItemWeaponTypeOffset = 0x1c7;

static int HarpItemWeaponType(int itemId) {
    __try {
        int table = kHarpItemTable;
        BYTE* tables = (BYTE*)s_harpGetTables();
        if (!tables) return 0;
        void** slot = s_harpFindTable(tables + 0x10, &table);
        if (!slot || !*slot) return 0;
        const BYTE* item = s_harpFindItem(*slot, &itemId);
        return item ? item[kHarpItemWeaponTypeOffset] : 0;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

static void __fastcall HarpAttachBoneHook(int itemId, int state, int hand, int flag, char* out, int size) {
    s_harpBone(itemId, state, hand, flag, out, size);
    if (!out || size <= 0 || (hand != 0 && hand != 1)) return;
    if (HarpItemWeaponType(itemId) != kHarpWeaponType) return;

    const bool drawn = state == 1 || state == 5;
    // What the client answers for a type it does not know.
    const char* unknown = !drawn ? "" : hand == 0 ? "Rhand_bone" : "Lhand_bone";
    if (strcmp(out, unknown) == 0) {
        const char* bone = drawn ? (hand == 0 ? "Lhand_bone" : "Rhand_bone")
                                 : (hand == 0 ? "Lback_bone" : "");
        strncpy_s(out, size, bone, _TRUNCATE);
    } else if (hand == 0 && out[0] == 'R') {
        out[0] = 'L';
    } else if (hand == 1 && out[0] == 'L') {
        out[0] = 'R';
    }
}

// Second mesh: the stick. The function that refreshes the weapons of a character attaches the
// main hand item and then the off hand one, one call each: (character, mode, ?, item id, right).
// A chainblade (type 8) has no off hand item, so that function reuses the main item for the
// second call and the mesh path function answers "<mesh>_r.cgf" / "<mesh>_l.cgf". In the Live 5.8
// client type 8 is the harp and the second path is "<mesh>_stick.cgf", with
// objects/items/ha_test_stick.cgf when the harp has no stick of its own. Both are redone here
// for 19: the second attach call gets the harp id while the weapon is drawn (the stick is hidden
// when sheathed), and the path of that call becomes the stick.
using HarpAttachWeapon = void (__fastcall*)(BYTE*, int, int, int, char);
using HarpWeaponMeshPath = void (__fastcall*)(int, char, int, int, const char*, char*);
using HarpFileExists = int (__fastcall*)(const char*);
static HarpAttachWeapon s_harpAttach = nullptr;
static HarpWeaponMeshPath s_harpMeshPath = nullptr;
static HarpFileExists s_harpFileExists = nullptr;
static constexpr size_t kHarpCharacterWeaponState = 0x2d0; // 1 and 5 = weapon drawn
static constexpr size_t kHarpMeshPathSize = 0x104;
static BYTE* volatile s_harpMainOwner = nullptr; // character whose main hand was just attached
static volatile LONG s_harpMainItem = 0;         // its item id when that item is a harp

static void __fastcall HarpAttachWeaponHook(BYTE* character, int mode, int arg3, int itemId, char right) {
    if (right) {
        s_harpMainOwner = character;
        s_harpMainItem = HarpItemWeaponType(itemId) == kHarpWeaponType ? itemId : 0;
    } else {
        const int harp = s_harpMainOwner == character ? s_harpMainItem : 0;
        s_harpMainOwner = nullptr;
        if (harp && itemId == 0 && character) {
            const int state = *(const int*)(character + kHarpCharacterWeaponState);
            if (state == 1 || state == 5) itemId = harp;
        }
    }
    s_harpAttach(character, mode, arg3, itemId, right);
}

static void __fastcall HarpWeaponMeshPathHook(int itemId, char right, int arg3, int arg4,
                                              const char* suffix, char* out) {
    s_harpMeshPath(itemId, right, arg3, arg4, suffix, out);
    if (right || !out || !out[0] || HarpItemWeaponType(itemId) != kHarpWeaponType) return;
    const size_t length = strlen(out);
    static const char extension[] = ".cgf";
    static const char stick[] = "_stick.cgf";
    static const char fallback[] = "Objects/Items/Ha_test_stick.cgf";
    if (length >= 4 && _stricmp(out + length - 4, extension) == 0 &&
        length - 4 + sizeof(stick) <= kHarpMeshPathSize) {
        memcpy(out + length - 4, stick, sizeof(stick));
        __try {
            if (!s_harpFileExists(out)) strncpy_s(out, kHarpMeshPathSize, fallback, _TRUNCATE);
        }
        __except (EXCEPTION_EXECUTE_HANDLER) {
            strncpy_s(out, kHarpMeshPathSize, fallback, _TRUNCATE);
        }
    }
}

// Basic ranged attack: (hand, ?, ?, character, <unused>, shot) -- the shot is the SIXTH argument;
// the only caller leaves the fifth slot unset. The projectile itself comes from the item
// (ammo_fx, ammo_bone, ammo_speed) for any weapon type, but the effect played where it lands is
// picked from the weapon type of that hand -- orb, book, gun and bow only. The harp gets the one
// its particles were made for, sys_hit.hit.harp (brought from the 5.8 sys_hit.prt).
using HarpRangedAttack = void* (__fastcall*)(int, int, int, BYTE*, void*, BYTE*);
static HarpRangedAttack s_harpRanged = nullptr;
static constexpr size_t kHarpCharacterMainWeaponType = 0x384; // +4 = off hand
static constexpr size_t kHarpShotHitEffect = 0x20;            // char[0x40]
static constexpr size_t kHarpShotHitEffectSize = 0x40;

static void* __fastcall HarpRangedAttackHook(int hand, int arg2, int arg3, BYTE* character,
                                             void* unused, BYTE* shot) {
    void* result = s_harpRanged(hand, arg2, arg3, character, unused, shot);
    __try {
        if (character && shot) {
            const int type = *(const int*)(character + kHarpCharacterMainWeaponType + (hand == 2 ? 4 : 0));
            char* effect = (char*)(shot + kHarpShotHitEffect);
            if (type == kHarpWeaponType && !effect[0])
                strncpy_s(effect, kHarpShotHitEffectSize, "sys_hit.hit.harp", _TRUNCATE);
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return result;
}

static SRWLOCK s_harpLock = SRWLOCK_INIT;
static bool s_harpChecked = false;

static void InstallHarpFix(HMODULE module) {
    // LoadLibrary hooks can reenter while Detours allocates its trampoline.
    if (!TryAcquireSRWLockExclusive(&s_harpLock)) return;
    __try {
        if (s_harpChecked) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;

        // Loop of the weapon_type parser, 0x23 bytes into the function:
        // mov rcx,[rdi]; mov rdx,rsi; call [wcsicmp]; test eax,eax; je found; inc ebx;
        // add rdi,10h; cmp ebx,12h; jb loop
        // The armor_type parser is the same code with cmp ebx,5.
        static const BYTE parse[] = {
            0x48,0x8b,0x0f,0x48,0x8b,0xd6,0xff,0x15,0,0,0,0,0x85,0xc0,0x74,0x0f,
            0xff,0xc3,0x48,0x83,0xc7,0x10,0x83,0xfb,0x12,0x72,0xe5
        };
        static const char parseMask[] = "xxxxxxxx????xxxxxxxxxxxxxxx";
        static const size_t parseLoopOffset = 0x23;
        // mov [rsp+8],rbx; mov [rsp+10h],rbp; mov [rsp+18h],rsi; push rdi; sub rsp,20h
        static const BYTE parseStart[] = {
            0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,
            0x48,0x83,0xec,0x20
        };
        // Start of the suffix function:
        // mov r10,r8; test ecx,ecx; je single; cmp edx,4; je gauntlet; mov r8,r9; mov rcx,r10;
        // cmp edx,0Ch
        static const BYTE suffix[] = {
            0x4d,0x8b,0xd0,0x85,0xc9,0x74,0x30,0x83,0xfa,0x04,0x0f,0x84,0,0,0,0,
            0x4d,0x8b,0xc1,0x49,0x8b,0xca,0x83,0xfa,0x0c
        };
        static const char suffixMask[] = "xxxxxxxxxxxx????xxxxxxxxx";
        // Start of the attach bone function, up to its first call:
        // mov [rsp+20h],rbx; push rbp/rsi/r12/r14/r15; sub rsp,20h; mov r12d,r9d;
        // mov dword ptr [rsp+50h],0Bh; mov r15d,r8d; mov ebp,edx; mov r14d,ecx; call tables
        // It looks the item up with three calls, at +24h, +32h and +44h.
        static const BYTE bone[] = {
            0x48,0x89,0x5c,0x24,0x20,0x55,0x56,0x41,0x54,0x41,0x56,0x41,0x57,0x48,0x83,0xec,
            0x20,0x45,0x8b,0xe1,0xc7,0x44,0x24,0x50,0x0b,0x00,0x00,0x00,0x45,0x8b,0xf8,0x8b,
            0xea,0x44,0x8b,0xf1,0xe8
        };
        static const char boneMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static const size_t boneCalls[] = { 0x24, 0x32, 0x44 };
        // Start of the per-hand attach function:
        // mov rax,rsp; mov [rax+18h],r8d; push rbp/rbx/rsi/r13/r14; lea rbp,[rax-1F8h];
        // sub rsp,2D0h; mov rbx,[rcx+12C8h]
        // Its call at +DCh is the "does this file exist" check of the mesh path it just built.
        static const BYTE attach[] = {
            0x48,0x8b,0xc4,0x44,0x89,0x40,0x18,0x55,0x53,0x56,0x41,0x55,0x41,0x56,0x48,0x8d,
            0xa8,0x08,0xfe,0xff,0xff,0x48,0x81,0xec,0xd0,0x02,0x00,0x00,0x48,0x8b,0x99,0xc8,
            0x12,0x00,0x00
        };
        static const char attachMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static const size_t attachExistsCall = 0xdc;
        // Start of the weapon mesh path function:
        // mov [rsp+10h],rbx; mov [rsp+18h],rbp; push rsi/rdi/r14; sub rsp,40h;
        // mov rbx,[rsp+88h]; mov edi,r8d; movzx r14d,dl; mov ebp,ecx
        static const BYTE meshPath[] = {
            0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x6c,0x24,0x18,0x56,0x57,0x41,0x56,0x48,0x83,
            0xec,0x40,0x48,0x8b,0x9c,0x24,0x88,0x00,0x00,0x00,0x41,0x8b,0xf8,0x44,0x0f,0xb6,
            0xf2,0x8b,0xe9
        };
        static const char meshPathMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        // Start of the basic ranged attack setup:
        // mov rax,rsp; mov [rax+18h],r8d; mov [rax+10h],edx; push rbx; sub rsp,60h;
        // mov [rax+8],rbp; mov [rax-10h],rsi; mov [rax-18h],rdi; mov rdi,r9; mov [rax-30h],r14;
        // mov r14d,ecx
        static const BYTE ranged[] = {
            0x48,0x8b,0xc4,0x44,0x89,0x40,0x18,0x89,0x50,0x10,0x53,0x48,0x83,0xec,0x60,0x48,
            0x89,0x68,0x08,0x48,0x89,0x70,0xf0,0x48,0x89,0x78,0xe8,0x49,0x8b,0xf9,0x4c,0x89,
            0x70,0xd0,0x44,0x8b,0xf1
        };
        static const char rangedMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(rangedMask) - 1 == sizeof(ranged), "Harp ranged signature mask length");
        static_assert(sizeof(attachMask) - 1 == sizeof(attach), "Harp attach signature mask length");
        static_assert(sizeof(meshPathMask) - 1 == sizeof(meshPath), "Harp mesh path signature mask length");
        static_assert(sizeof(boneMask) - 1 == sizeof(bone), "Harp bone signature mask length");
        static_assert(sizeof(parseMask) - 1 == sizeof(parse), "Harp parse signature mask length");
        static_assert(sizeof(suffixMask) - 1 == sizeof(suffix), "Harp suffix signature mask length");

        BYTE* parseLoop = QunaFindUnique(base, nt, parse, parseMask, sizeof(parse));
        BYTE* suffixStart = QunaFindUnique(base, nt, suffix, suffixMask, sizeof(suffix));
        BYTE* boneStart = QunaFindUnique(base, nt, bone, boneMask, sizeof(bone));
        s_harpChecked = true;
        if (!parseLoop || !suffixStart || !boneStart) {
            OutputDebugStringA("[Harp] Unsupported client; signatures not unique.\n");
            __leave;
        }
        const SIZE_T image = nt->OptionalHeader.SizeOfImage;
        BYTE* lookup[3];
        for (size_t i = 0; i < 3; ++i) {
            BYTE* call = boneStart + boneCalls[i];
            lookup[i] = call[0] == 0xe8 ? call + 5 + *(int32_t*)(call + 1) : nullptr;
            if (!lookup[i] || lookup[i] < base || lookup[i] >= base + image) {
                OutputDebugStringA("[Harp] Unsupported client; unexpected item lookup calls.\n");
                __leave;
            }
        }
        BYTE* attachStart = QunaFindUnique(base, nt, attach, attachMask, sizeof(attach));
        BYTE* meshPathStart = QunaFindUnique(base, nt, meshPath, meshPathMask, sizeof(meshPath));
        BYTE* existsCall = attachStart ? attachStart + attachExistsCall : nullptr;
        BYTE* exists = existsCall && existsCall[0] == 0xe8 ?
            existsCall + 5 + *(int32_t*)(existsCall + 1) : nullptr;
        if (!attachStart || !meshPathStart || !exists || exists < base || exists >= base + image) {
            OutputDebugStringA("[Harp] Unsupported client; stick signatures not found.\n");
            __leave;
        }
        BYTE* rangedStart = QunaFindUnique(base, nt, ranged, rangedMask, sizeof(ranged));
        if (!rangedStart) {
            OutputDebugStringA("[Harp] Unsupported client; ranged attack signature not found.\n");
            __leave;
        }
        s_harpRanged = (HarpRangedAttack)rangedStart;
        s_harpFileExists = (HarpFileExists)exists;
        s_harpAttach = (HarpAttachWeapon)attachStart;
        s_harpMeshPath = (HarpWeaponMeshPath)meshPathStart;
        s_harpGetTables = (HarpGetTables)lookup[0];
        s_harpFindTable = (HarpFindTable)lookup[1];
        s_harpFindItem = (HarpFindItem)lookup[2];
        BYTE* parseFunction = parseLoop - parseLoopOffset;
        if (parseFunction < base || memcmp(parseFunction, parseStart, sizeof(parseStart)) != 0) {
            OutputDebugStringA("[Harp] Unsupported client; unexpected parser prologue.\n");
            __leave;
        }

        s_harpParse = (HarpParseWeaponType)parseFunction;
        s_harpSuffix = (HarpWeaponSuffix)suffixStart;
        s_harpBone = (HarpAttachBone)boneStart;
        LONG error = DetourTransactionBegin();
        if (error != NO_ERROR) {
            s_harpChecked = false; // Another initialization transaction may still be active.
            __leave;
        }
        error = DetourUpdateThread(GetCurrentThread());
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpParse, HarpParseWeaponTypeHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpSuffix, HarpWeaponSuffixHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpBone, HarpAttachBoneHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpAttach, HarpAttachWeaponHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpMeshPath, HarpWeaponMeshPathHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpRanged, HarpRangedAttackHook);
        if (error == NO_ERROR) error = DetourTransactionCommit();
        else DetourTransactionAbort();
        OutputDebugStringA(error == NO_ERROR ? "[Harp] Weapon type hooks installed.\n" :
            "[Harp] Weapon type hook installation failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_harpLock);
    }
}
#else
static void InstallHarpFix(HMODULE) {}
#endif
