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
static void HarpPatchEnchantTables();
static void HarpPatchClassIconsOnce();
static void HarpPatchAnimationSuffixOnce();

using HarpParseWeaponType = int (__fastcall*)(const wchar_t*);
using HarpWeaponSuffix = void* (__fastcall*)(int, int, char*, size_t);
static HarpParseWeaponType s_harpParse = nullptr;
static HarpWeaponSuffix s_harpSuffix = nullptr;

static int __fastcall HarpParseWeaponTypeHook(const wchar_t* name) {
    HarpPatchEnchantTables();
    HarpPatchClassIconsOnce();
    HarpPatchAnimationSuffixOnce();
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

// Weapon type name shown in tooltips: const wchar_t* f(type), a switch over 1..18 that looks
// each name up in the string table. The harp uses STR_TOOLTIP_HARP, which the 5.0 strings do
// not have: the client data gets it under kHarpTypeNameString (the 5.8 id, 904448, is taken).
using HarpWeaponTypeName = const wchar_t* (__fastcall*)(int);
using HarpRegistry = BYTE* (__fastcall*)();
using HarpFindManager = void** (__fastcall*)(BYTE*, const int*);
using HarpString = const wchar_t* (__fastcall*)(void*, int);
static HarpWeaponTypeName s_harpTypeName = nullptr;
static HarpRegistry s_harpRegistry = nullptr;
static HarpFindManager s_harpFindManager = nullptr;
static HarpString s_harpString = nullptr;
static constexpr int kHarpTypeNameString = 1990001;

static const wchar_t* __fastcall HarpWeaponTypeNameHook(int type) {
    HarpPatchEnchantTables();
    HarpPatchClassIconsOnce();
    if (type != kHarpWeaponType) return s_harpTypeName(type);
    const int key = 0; // string table manager
    void** manager = s_harpFindManager(s_harpRegistry() + 0x10, &key);
    return s_harpString(*manager, kHarpTypeNameString);
}

// ---- Bard class ------------------------------------------------------------------------------
// The 5.0 client knows classes 0..26; 14, 17, 20 and 23 are empty slots in every per-class table.
// The Bard of Live 5.8 takes 17 (base, "artist") and 20 (the playable class, "bard").
static constexpr int kBardBaseClass = 17;
static constexpr int kBardClass = 20;

// Class name: const wchar_t* f(string table, classId), a switch over 0..25 that leaves the empty
// slots blank. The names are strings of the client data: STR_CLASS_NAME_ARTIST / _BARD.
using HarpClassName = const wchar_t* (__fastcall*)(void*, int);
static HarpClassName s_harpClassName = nullptr;
static constexpr int kBardBaseClassNameString = 1990003;
static constexpr int kBardClassNameString = 1990004;

static const wchar_t* __fastcall HarpClassNameHook(void* table, int classId) {
    HarpPatchClassIconsOnce();
    if (classId == kBardBaseClass) return s_harpString(table, kBardBaseClassNameString);
    if (classId == kBardClass) return s_harpString(table, kBardClassNameString);
    return s_harpClassName(table, classId);
}

// Class icon: a table of Skin names (const char*), one per class id 0..26, read by the UI. The
// empty slots hold "", so the icon of a Bard kept whatever the widget showed before (Lumines).
// The Skins v4_class_artist / v4_class_bard come with the client data (version4.xml).
static constexpr int kHarpClassIconSlots = 27;
static const char kBardBaseClassIcon[] = "v4_class_artist";
static const char kBardClassIcon[] = "v4_class_bard";

// Patched on first use, like the enchant tables: writing into Game.dll while it is still being
// loaded makes its protector (WinLicense) fail the DLL initialization (error 1114).
static const char** s_harpClassIcons = nullptr;
static volatile LONG s_harpClassIconsDone = 0;
static bool HarpPatchClassIcons(const char** table);

static void HarpPatchEmblemsOnce();

static void HarpPatchClassIconsOnce() {
    HarpPatchEmblemsOnce();
    if (s_harpClassIconsDone || !s_harpClassIcons) return;
    if (InterlockedExchange(&s_harpClassIconsDone, 1)) return;
    __try {
        OutputDebugStringA(HarpPatchClassIcons(s_harpClassIcons) ? "[Harp] Class icons patched.\n" :
                           "[Harp] Class icon table not patched.\n");
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

// Class emblem (the big icon of the target window, Textures\UI\Emblem\icon_emblem_<name>): a
// table of {int classId; wchar_t name[260]} filled by an initializer, where each empty slot copies
// the name of the class before it -- slot 20 says "lumines". Patched on first use as well.
static constexpr size_t kHarpEmblemStride = 0x20c;
static wchar_t* s_harpEmblemNames = nullptr; // name of slot 0; slot i at + i * stride
static volatile LONG s_harpEmblemsDone = 0;

static bool HarpPatchEmblemName(int slot, const wchar_t* expected, const wchar_t* name) {
    wchar_t* text = (wchar_t*)((BYTE*)s_harpEmblemNames + slot * kHarpEmblemStride);
    if (*(int*)((BYTE*)text - 4) != slot || wcscmp(text, expected) != 0) return false;
    DWORD old;
    if (!VirtualProtect(text, 64, PAGE_EXECUTE_READWRITE, &old)) return false;
    wcscpy_s(text, 32, name);
    VirtualProtect(text, 64, old, &old);
    return true;
}

static void HarpPatchEmblemsOnce() {
    if (s_harpEmblemsDone || !s_harpEmblemNames) return;
    __try {
        // Not filled yet (first calls can come before the initializer): try again later.
        const wchar_t* lumines = (const wchar_t*)((BYTE*)s_harpEmblemNames + 19 * kHarpEmblemStride);
        if (wcscmp(lumines, L"lumines") != 0) return;
        if (InterlockedExchange(&s_harpEmblemsDone, 1)) return;
        const bool ok = HarpPatchEmblemName(kBardBaseClass, L"battlemaster", L"artist") &&
                        HarpPatchEmblemName(kBardClass, L"lumines", L"bard");
        OutputDebugStringA(ok ? "[Harp] Class emblems patched.\n" : "[Harp] Class emblems not patched.\n");
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

static bool HarpPatchClassIcons(const char** table) {
    // Sanity check: the slots around the Bard must be the ones of this build.
    if (strcmp(table[19], "v4_class_lumines") != 0 || strcmp(table[22], "v4_class_gunner") != 0 ||
        table[kBardBaseClass][0] || table[kBardClass][0]) return false;
    DWORD old;
    if (!VirtualProtect(&table[kBardBaseClass], (kBardClass - kBardBaseClass + 1) * sizeof(char*),
                        PAGE_EXECUTE_READWRITE, &old)) return false;
    table[kBardBaseClass] = kBardBaseClassIcon;
    table[kBardClass] = kBardClassIcon;
    VirtualProtect(&table[kBardBaseClass], (kBardClass - kBardBaseClass + 1) * sizeof(char*), old, &old);
    return true;
}

// Damage animation name: f(character, ?, char out[0x100]). With the weapon drawn it builds
// c + sdamage + <suffix> + _001 from a list of its own, without the harp; the 19 fell back to
// csdamage_noweapon_001. Same rule as the original: keep the name only when the model has it.
using HarpDamageAnimation = void* (__fastcall*)(BYTE*, void*, char*);
using HarpIsModel = int (__fastcall*)(BYTE*);
using HarpHasAnimation = int (__fastcall*)(void*, const char*);
static HarpDamageAnimation s_harpDamage = nullptr;
static HarpIsModel s_harpIsModel = nullptr;
static HarpHasAnimation s_harpHasAnimation = nullptr;
static constexpr size_t kHarpDamageNameSize = 0x100;

static void* __fastcall HarpDamageAnimationHook(BYTE* character, void* arg2, char* out) {
    void* result = s_harpDamage(character, arg2, out);
    __try {
        if (character && out) {
            const int state = *(const int*)(character + kHarpCharacterWeaponState);
            const int* types = (const int*)(character + kHarpCharacterMainWeaponType);
            static const char name[] = "csdamage_harp_001";
            if ((state == 1 || state == 5) && types[0] == kHarpWeaponType && types[1] == 0 &&
                (!s_harpIsModel(character) || s_harpHasAnimation(*(void**)(character + 8), name)))
                strncpy_s(out, kHarpDamageNameSize, name, _TRUNCATE);
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return result;
}

// Enchant bonus shown in tooltips: two static tables of {per level up to +10, per level above},
// indexed by weapon type, with 20 slots -- the 19th is left at zero. The server enchants HARP
// exactly like ORB (enchant_templates.xml), so the harp gets the orb entry.
static constexpr int kHarpOrbWeaponType = 9;

// The tables are filled by Game.dll's initializers, which may not have run yet when the hooks
// are installed (from a LoadLibrary made during Game.dll's own startup). So they are patched on
// first use: the parser runs when the client loads its items, and the tooltip asks for the
// weapon type name before reading the tables.
static int32_t* s_harpEnchantTables[2] = {};
static volatile LONG s_harpEnchantPatched = 0;

static bool HarpCopyOrbEnchant(int32_t* table) {
    int32_t* orb = table + kHarpOrbWeaponType * 2;
    int32_t* harp = table + kHarpWeaponType * 2;
    if (harp[0] == orb[0] && harp[1] == orb[1]) return orb[0] != 0;
    if (!orb[0] || !orb[1] || harp[0] || harp[1]) return false;
    DWORD old;
    // The packed image keeps code and data in one section: keep the page executable.
    if (!VirtualProtect(harp, 8, PAGE_EXECUTE_READWRITE, &old)) return false;
    harp[0] = orb[0];
    harp[1] = orb[1];
    VirtualProtect(harp, 8, old, &old);
    return true;
}

static void HarpPatchEnchantTables() {
    if (s_harpEnchantPatched) return;
    __try {
        bool done = true;
        for (int32_t* table : s_harpEnchantTables)
            done = table && HarpCopyOrbEnchant(table) && done;
        if (done && !InterlockedExchange(&s_harpEnchantPatched, 1))
            OutputDebugStringA("[Harp] Enchant tables patched.\n");
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

// Class key: the lowercase class name ("lumines", "runeblade"...), in char and in wchar_t. It fills
// "[%class]" in sound file names -- the login voice is vlogin2_<class>_<gender><race><voice>.ogg --
// and the class of scripts. The empty slots answer "none".
using HarpClassKey = const char* (__fastcall*)(int);
using HarpClassKeyW = const wchar_t* (__fastcall*)(int);
static HarpClassKey s_harpClassKey = nullptr;
static HarpClassKeyW s_harpClassKeyW = nullptr;

static const char* __fastcall HarpClassKeyHook(int classId) {
    if (classId == kBardBaseClass) return "artist";
    if (classId == kBardClass) return "bard";
    return s_harpClassKey(classId);
}

static const wchar_t* __fastcall HarpClassKeyWHook(int classId) {
    if (classId == kBardBaseClass) return L"artist";
    if (classId == kBardClass) return L"bard";
    return s_harpClassKeyW(classId);
}

// Class name -> id, the reverse: the data loader converts the class fields of the client XMLs with it
// (a table of wide strings "warrior" 0 ... "runeblade" 25, _wcsicmp; unknown -> 1Bh). The creation
// screen panel (client_character_class_info, class_name "Bard") is looked up by the class id, so
// "bard" must be 20. The converted tables are cached in data\dump\tables.dmp: while it is valid the
// XMLs are not read again and this hook is not called.
using HarpClassFromName = int (__fastcall*)(const wchar_t*);
static HarpClassFromName s_harpClassFromName = nullptr;

static int __fastcall HarpClassFromNameHook(const wchar_t* name) {
    if (name && _wcsicmp(name, L"artist") == 0) return kBardBaseClass;
    if (name && _wcsicmp(name, L"bard") == 0) return kBardClass;
    return s_harpClassFromName(name);
}

// Animation class suffix: the animation name builder has a switch on the class id that copies
// "_lumines", "_runeblade"... into the name (Nidle_<class>_lobby_001, nidle_<class>_001, ...).
// The empty slots jump to the default case, an empty suffix. Two new cases are added: a small
// stub, allocated right after Game.dll (jump table entries are unsigned offsets from its base),
// loads "_artist" / "_bard" and jumps back to the common copy, like the other cases.
static BYTE* s_harpSuffixSwitch = nullptr; // movsxd rax,[rbx+0C0h] of the switch
static BYTE* s_harpImageBase = nullptr;
static SIZE_T s_harpImageSize = 0;
static volatile LONG s_harpSuffixDone = 0;

static BYTE* HarpAllocateNear(BYTE* from, SIZE_T size) {
    SYSTEM_INFO info;
    GetSystemInfo(&info);
    const ULONG_PTR step = info.dwAllocationGranularity;
    ULONG_PTR at = ((ULONG_PTR)from + step - 1) & ~(step - 1);
    for (int i = 0; i < 4096; ++i, at += step) {
        void* p = VirtualAlloc((void*)at, size, MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE);
        if (p) return (BYTE*)p;
    }
    return nullptr;
}

static BYTE* HarpSuffixCase(BYTE* stub, BYTE* join, const char* suffix) {
    // lea rdx,[rip+5]; jmp join; "suffix"
    stub[0] = 0x48; stub[1] = 0x8d; stub[2] = 0x15;
    *(int32_t*)(stub + 3) = 5;
    stub[7] = 0xe9;
    *(int32_t*)(stub + 8) = (int32_t)(join - (stub + 12));
    strcpy_s((char*)stub + 12, 16, suffix);
    return stub + 32;
}

static void HarpPatchAnimationSuffixOnce() {
    if (s_harpSuffixDone || !s_harpSuffixSwitch) return;
    if (InterlockedExchange(&s_harpSuffixDone, 1)) return;
    __try {
        BYTE* s = s_harpSuffixSwitch;
        BYTE* fallback = s + 16 + *(int32_t*)(s + 12);  // ja target: empty suffix
        BYTE* base = s + 23 + *(int32_t*)(s + 19);      // lea rdx,[image base]
        uint32_t* table = (uint32_t*)(base + *(int32_t*)(s + 26));
        BYTE* join = s + 47 + *(int32_t*)(s + 43);      // jmp of case 0
        if (base != s_harpImageBase || base + table[kBardBaseClass] != fallback ||
            base + table[kBardClass] != fallback || base + table[19] == fallback) {
            OutputDebugStringA("[Harp] Animation suffix switch not as expected.\n");
            return;
        }
        BYTE* stub = HarpAllocateNear(s_harpImageBase + s_harpImageSize, 64);
        if (!stub || stub < base || stub + 64 - base > 0x7fffffff) {
            OutputDebugStringA("[Harp] No memory near Game.dll for the animation suffix.\n");
            return;
        }
        BYTE* bard = HarpSuffixCase(stub, join, "_artist");
        HarpSuffixCase(bard, join, "_bard");
        FlushInstructionCache(GetCurrentProcess(), stub, 64);
        DWORD old;
        if (!VirtualProtect(&table[kBardBaseClass], (kBardClass - kBardBaseClass + 1) * 4,
                            PAGE_EXECUTE_READWRITE, &old)) return;
        table[kBardBaseClass] = (uint32_t)(stub - base);
        table[kBardClass] = (uint32_t)(bard - base);
        VirtualProtect(&table[kBardBaseClass], (kBardClass - kBardBaseClass + 1) * 4, old, &old);
        OutputDebugStringA("[Harp] Animation suffixes _artist/_bard added.\n");
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

// ---- Creation screen ---------------------------------------------------------------------------
// The class buttons class_1..class_13 (UI_Create.xml) are kept in a fixed array of 13 in the window
// (+578h); a click finds the button's position (0..12) and selects it, and the position becomes the
// class id in a switch (0 -> 1 ... 10 -> 19 Lumines ... 12 -> 25). The Bard button (class_14, from
// the client data) is not in that array: clicking it turns "bard mode" on and selects position 10,
// the Orchestrator/Lumines line, and with the mode on that position means class 20. Every array of
// 13 stays within its bounds.
static constexpr int kBardButtonSlot = 10;     // position the Bard rides on
static constexpr int kBardRideClass = 19;      // class of that position (Lumines)
static constexpr size_t kCreateButtons = 0x578; // void* buttons[13]
static constexpr int kCreateButtonCount = 13;

using HarpCreateInit = void* (__fastcall*)(BYTE*, void*, void*, void*);
using HarpCreateClick = int (__fastcall*)(BYTE*, void**);
using HarpCreateSelect = void (__fastcall*)(BYTE*, int, int, char);
using HarpSlotToClass = int (__fastcall*)(int);
using HarpClassToSlot = int (__fastcall*)(int);
using HarpPreviewSlot = int (__fastcall*)(int, int, int, int);
using HarpDynamicCast = void* (__cdecl*)(void*, long, void*, void*, int);
static HarpCreateInit s_harpCreateInit = nullptr;
static HarpCreateClick s_harpCreateClick = nullptr;
static HarpCreateSelect s_harpCreateSelect = nullptr;
static HarpSlotToClass s_harpSlotToClass = nullptr;
static HarpClassToSlot s_harpClassToSlot = nullptr;
static HarpPreviewSlot s_harpPreviewSlot = nullptr;
static HarpDynamicCast s_harpDynamicCast = nullptr;
static void* s_harpButtonTypeFrom = nullptr;
static void* s_harpButtonTypeTo = nullptr;
static const int* s_harpCreateGender = nullptr; // global read by the original click
static BYTE* s_harpCreateWindow = nullptr;
static BYTE* s_harpBardButton = nullptr;
static volatile bool s_harpBardMode = false;

static void HarpSetButtonOn(void* button, bool on) {
    if (button) (*(void (__fastcall**)(void*, int))(*(BYTE**)button + 0x610))(button, on ? 1 : 0);
}

static void* __fastcall HarpCreateInitHook(BYTE* window, void* a2, void* a3, void* a4) {
    void* result = s_harpCreateInit(window, a2, a3, a4);
    s_harpBardMode = false;
    s_harpBardButton = nullptr;
    __try {
        // The same lookup the original does for class_1..class_13.
        char name[] = "class_14";
        void* widget = (*(void* (__fastcall**)(BYTE*, char*))(*(BYTE**)window + 0x370))(window, name);
        BYTE* button = widget ? (BYTE*)s_harpDynamicCast(widget, 0, s_harpButtonTypeFrom, s_harpButtonTypeTo, 0) : nullptr;
        if (button) {
            *(int*)(button + 0x378) = 0x5d;
            (*(void (__fastcall**)(void*, int))(*(BYTE**)button + 0x5d0))(button, 0);
            s_harpBardButton = button;
            s_harpCreateWindow = window;
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        s_harpBardButton = nullptr;
    }
    return result;
}

static void __fastcall HarpCreateSelectHook(BYTE* window, int slot, int gender, char flag);

static int __fastcall HarpCreateClickHook(BYTE* window, void** event) {
    void* sender = event ? *event : nullptr;
    if (sender && window == s_harpCreateWindow && sender == s_harpBardButton) {
        s_harpBardMode = true;
        // Through the hook: s_harpCreateSelect is the trampoline, and the original turns the button
        // of position 10 (Lumines) on -- the hook moves that to the Bard button.
        HarpCreateSelectHook(window, kBardButtonSlot, *s_harpCreateGender, 1);
        return 1;
    }
    if (sender && window == s_harpCreateWindow) {
        void** buttons = (void**)(window + kCreateButtons);
        for (int i = 0; i < kCreateButtonCount; ++i)
            if (buttons[i] == sender) s_harpBardMode = false;
    }
    return s_harpCreateClick(window, event);
}

static void __fastcall HarpCreateSelectHook(BYTE* window, int slot, int gender, char flag) {
    s_harpCreateSelect(window, slot, gender, flag);
    if (window != s_harpCreateWindow || !s_harpBardButton || slot < 0) return;
    __try {
        const bool bard = s_harpBardMode && slot == kBardButtonSlot;
        HarpSetButtonOn(s_harpBardButton, bard);
        if (bard) HarpSetButtonOn(((void**)(window + kCreateButtons))[kBardButtonSlot], false);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

static int __fastcall HarpSlotToClassHook(int slot) {
    if (s_harpBardMode && slot == kBardButtonSlot) return kBardClass;
    return s_harpSlotToClass(slot);
}

static int __fastcall HarpClassToSlotHook(int classId) {
    return s_harpClassToSlot(classId == kBardClass ? kBardRideClass : classId);
}

// Creation preview: a preloaded character per class/race/gender; the Bard has none yet and uses
// the Lumines one (its own preview is the next step).
static int __fastcall HarpPreviewSlotHook(int a1, int classId, int gender, int a4) {
    return s_harpPreviewSlot(a1, classId == kBardClass ? kBardRideClass : classId, gender, a4);
}

// Character list: builds each slot (class, emblem, level...) and reads the emblem table directly,
// often before any other hook here has run. The data patches go in right before it.
using HarpCharacterSlot = void* (__fastcall*)(void*, void*, void*, void*);
static HarpCharacterSlot s_harpCharacterSlot = nullptr;

static void* __fastcall HarpCharacterSlotHook(void* self, void* a2, void* a3, void* a4) {
    HarpPatchClassIconsOnce();
    HarpPatchAnimationSuffixOnce();
    return s_harpCharacterSlot(self, a2, a3, a4);
}

// Called when a LoadLibrary returns. When it is the one of Game.dll, its initialization (CRT
// initializers and protector included) is over: the data patches go in now, before the first
// screen is drawn -- the character list builds the class emblem before any of the hooks above runs.
static void HarpOnModuleLoaded(HMODULE module) {
    if (!module || module != GetModuleHandleW(L"game.dll")) return;
    HarpPatchEnchantTables();
    HarpPatchClassIconsOnce();
    HarpPatchAnimationSuffixOnce();
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
        // Weapon type name: push rbp; mov rbp,rsp; sub rsp,20h; dec ecx; cmp ecx,11h; ja default;
        // jump table; first case (sword): mov [rbp+10h],0; call registry; lea rdx,[rbp+10h];
        // lea rcx,[rax+10h]; call find; mov edx,STR_TOOLTIP_SWORD; mov rcx,[rax]; call string
        static const BYTE typeName[] = {
            0x40,0x55,0x48,0x8b,0xec,0x48,0x83,0xec,0x20,0xff,0xc9,0x83,0xf9,0x11,0x0f,0x87,
            0,0,0,0,0x48,0x63,0xc1,0x48,0x8d,0x15,0,0,0,0,0x8b,0x8c,0x82,0,0,0,0,0x48,0x03,
            0xca,0xff,0xe1,0xc7,0x45,0x10,0x00,0x00,0x00,0x00,0xe8,0,0,0,0,0x48,0x8d,0x55,0x10,
            0x48,0x8d,0x48,0x10,0xe8,0,0,0,0,0xba,0xdd,0xa9,0x03,0x00,0x48,0x8b,0x08,0xe8
        };
        static const char typeNameMask[] =
            "xxxxxxxxxxxxxxxx????xxxxxx????xxx????xxxxxxxxxxxxx????xxxxxxxxx????xxxxxxxxx";
        static const size_t typeNameCalls[] = { 0x31, 0x3e, 0x4b };
        // Damage animation: mov [rsp+8],rbx; mov [rsp+10h],rdi; push rbp; lea rbp,[rsp-160h];
        // sub rsp,260h; mov eax,[rcx+2D0h]; mov rdi,r8; dec eax; mov rbx,rcx; test eax,-5;
        // je drawn; lea r8,"n%s_001"
        static const BYTE damage[] = {
            0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x7c,0x24,0x10,0x55,0x48,0x8d,0xac,0x24,0xa0,
            0xfe,0xff,0xff,0x48,0x81,0xec,0x60,0x02,0x00,0x00,0x8b,0x81,0xd0,0x02,0x00,0x00,
            0x49,0x8b,0xf8,0xff,0xc8,0x48,0x8b,0xd9,0xa9,0xfb,0xff,0xff,0xff,0x74,0x0c,0x4c,
            0x8d,0x05
        };
        static const char damageMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        // Its fallback to the no-weapon name: mov rcx,rbx; call is-model; test eax,eax; je done;
        // mov rcx,[rbx+8]; mov rdx,rdi; call has-animation; test eax,eax; jne done; lea r8,...
        static const BYTE damageCheck[] = {
            0x48,0x8b,0xcb,0xe8,0,0,0,0,0x85,0xc0,0x74,0,0x48,0x8b,0x4b,0x08,0x48,0x8b,0xd7,
            0xe8,0,0,0,0,0x85,0xc0,0x75,0,0x4c,0x8d,0x05
        };
        static const char damageCheckMask[] = "xxxx????xxx?xxxxxxxx????xxx?xxx";
        // Enchant tables, from the tooltip code that loads them: movzx eax,word [rax+18Eh] (or
        // 19Eh); ...; lea r12/r13,[table]
        static const BYTE enchantAttack[] = {
            0x0f,0xb7,0x80,0x8e,0x01,0x00,0x00,0xeb,0x02,0x8b,0xc7,0x0f,0xb7,0xc0,0x4c,0x8d,
            0x25,0,0,0,0,0x41,0x89,0x46,0x08,0x41,0xbd,0x0a,0x00,0x00,0x00
        };
        static const char enchantAttackMask[] = "xxxxxxxxxxxxxxxxx????xxxxxxxxxx";
        static const BYTE enchantBoost[] = {
            0x0f,0xb7,0x80,0x9e,0x01,0x00,0x00,0xeb,0x02,0x8b,0xc6,0x0f,0xbf,0xe8,0x4c,0x8d,
            0x2d,0,0,0,0,0x8b,0x43,0x10,0x8b,0xfe
        };
        static const char enchantBoostMask[] = "xxxxxxxxxxxxxxxxx????xxxxx";
        static const size_t enchantLea = 14; // lea is 7 bytes, rel32 at +3
        // Class name: cmp edx,1Ah; ja blank; cmp edx,19h; ja blank; movsxd rax,edx;
        // lea r8,[image]; mov edx,[r8+rax*4+table]; add rdx,r8; jmp rdx
        static const BYTE className[] = {
            0x83,0xfa,0x1a,0x0f,0x87,0,0,0,0,0x83,0xfa,0x19,0x0f,0x87,0,0,0,0,0x48,0x63,0xc2,
            0x4c,0x8d,0x05,0,0,0,0,0x41,0x8b,0x94,0x80,0,0,0,0,0x49,0x03,0xd0,0xff,0xe2
        };
        static const char classNameMask[] = "xxxxx????xxxxx????xxxxxx????xxxx????xxxxx";
        static_assert(sizeof(classNameMask) - 1 == sizeof(className), "Class name signature mask length");
        // A reader of the class icon table: movsx rdx,byte [rsi+18h]; lea rax,[table];
        // lea rcx,[skins]; mov rdx,[rax+rdx*8]; call
        static const BYTE classIcon[] = {
            0x48,0x0f,0xbe,0x56,0x18,0x48,0x8d,0x05,0,0,0,0,0x48,0x8d,0x0d,0,0,0,0,0x48,0x8b,0x14,
            0xd0,0xe8
        };
        static const char classIconMask[] = "xxxxxxxx????xxx????xxxxx";
        static const size_t classIconLea = 5; // lea rax,[rip+rel32], 7 bytes
        static_assert(sizeof(classIconMask) - 1 == sizeof(classIcon), "Class icon signature mask length");
        // Class emblem name: cmp rbx,1Bh; jae other; imul rdx,rax,20Ch; lea rax,[names]
        static const BYTE emblem[] = {
            0x48,0x83,0xfb,0x1b,0x73,0,0x48,0x69,0xd0,0x0c,0x02,0x00,0x00,0x48,0x8d,0x05
        };
        static const char emblemMask[] = "xxxxx?xxxxxxxxxx";
        static const size_t emblemLea = 13;
        static_assert(sizeof(emblemMask) - 1 == sizeof(emblem), "Class emblem signature mask length");
        // Character list slot: mov [rsp+8],rcx; push rbp/r12/r13/r14; lea rbp,[rsp-488h];
        // sub rsp,588h; mov r14,-1; lea r8,[rsp+68h]; xor r12d,r12d
        static const BYTE characterSlot[] = {
            0x48,0x89,0x4c,0x24,0x08,0x55,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x8d,0xac,0x24,
            0x78,0xfb,0xff,0xff,0x48,0x81,0xec,0x88,0x05,0x00,0x00,0x49,0xc7,0xc6,0xff,0xff
        };
        static const char characterSlotMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(characterSlotMask) - 1 == sizeof(characterSlot), "Character slot mask length");
        // Animation class suffix switch: movsxd rax,[rbx+0C0h]; cmp eax,19h; ja none;
        // lea rdx,[base]; mov ecx,[rdx+rax*4+table]; add rcx,rdx; jmp rcx; lea rdx,"_warrior"; jmp
        static const BYTE suffixSwitch[] = {
            0x48,0x63,0x83,0xc0,0x00,0x00,0x00,0x83,0xf8,0x19,0x0f,0x87,0,0,0,0,0x48,0x8d,0x15,
            0,0,0,0,0x8b,0x8c,0x82,0,0,0,0,0x48,0x03,0xca,0xff,0xe1,0x48,0x8d,0x15,0,0,0,0,0xe9
        };
        static const char suffixSwitchMask[] = "xxxxxxxxxxxx????xxx????xxx????xxxxxxxx????x";
        static_assert(sizeof(suffixSwitchMask) - 1 == sizeof(suffixSwitch), "Suffix switch mask length");
        // Class key, char and wchar_t: push rbp; lea rbp,[rsp-57h]; sub rsp,0E0h; cmp ecx,1Bh;
        // jl table; lea rax,[empty]; add rsp,0E0h. The two differ only in that lea, kept whole.
        static const BYTE classKey[] = {
            0x40,0x55,0x48,0x8d,0x6c,0x24,0xa9,0x48,0x81,0xec,0xe0,0x00,0x00,0x00,0x83,0xf9,
            0x1b,0x7c,0x10,0x48,0x8d,0x05,0x4f,0xa9,0x8b,0x00,0x48,0x81,0xc4,0xe0,0x00,0x00
        };
        static const BYTE classKeyW[] = {
            0x40,0x55,0x48,0x8d,0x6c,0x24,0xa9,0x48,0x81,0xec,0xe0,0x00,0x00,0x00,0x83,0xf9,
            0x1b,0x7c,0x10,0x48,0x8d,0x05,0x66,0x62,0x9b,0x00,0x48,0x81,0xc4,0xe0,0x00,0x00
        };
        static const char classKeyMask[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(classKeyMask) - 1 == sizeof(classKey), "Class key mask length");
        // Class name -> id: save rbx/rbp/rsi/rdi; push r14; sub rsp,20h; lea r14,[table];
        // mov rsi,rcx; mov rbx,r14; lea rbp,[end]; xor edi,edi; loop of _stricmp; mov eax,1Bh
        static const BYTE classFromName[] = {
            0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,
            0x89,0x7c,0x24,0x20,0x41,0x56,0x48,0x83,0xec,0x20,0x4c,0x8d,0x35,0,0,0,0,0x48,
            0x8b,0xf1,0x49,0x8b,0xde,0x48,0x8d,0x2d,0,0,0,0,0x33,0xff,0x48,0x8b,0x0b,0x48,
            0x8b,0xd6,0xff,0x15,0,0,0,0,0x85,0xc0,0x74,0x12,0xff,0xc7,0x48,0x83,0xc3,0x10,
            0x48,0x3b,0xdd,0x7c,0xe5,0xb8,0x1b,0x00
        };
        static const char classFromNameMask[] =
            "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx????xxxxxxxxx????xxxxxxxxxx????xxxxxxxxxxxxxxxxxx";
        static_assert(sizeof(classFromNameMask) - 1 == sizeof(classFromName), "Class from name mask length");
        // Creation screen. Window init: mov rax,rsp; mov [rax+8],rbx; mov [rax+10h],rbp;
        // mov [rax+18h],rsi; push rdi/r14/r15; sub rsp,0E0h; movaps [rax-28h],xmm6
        static const BYTE createInit[] = {
            0x48,0x8b,0xc4,0x48,0x89,0x58,0x08,0x48,0x89,0x68,0x10,0x48,0x89,0x70,0x18,0x57,
            0x41,0x56,0x41,0x57,0x48,0x81,0xec,0xe0,0x00,0x00,0x00,0x0f
        };
        // Its lookup of each class_N button: find child (vtable+370h), then the RTTI dynamic cast
        // to the button type -- the cast and the two type descriptors are taken from here.
        static const BYTE createLookup[] = {
            0x48,0x8b,0x03,0x48,0x8d,0x54,0x24,0x30,0x48,0x8b,0xcb,0xff,0x90,0x70,0x03,0x00,0x00,
            0x4c,0x8d,0x0d,0,0,0,0,0x44,0x89,0x74,0x24,0x20,0x48,0x8b,0xc8,0x4c,0x8d,0x05,0,0,0,0,
            0x33,0xd2,0xe8,0,0,0,0,0x48,0x89,0x07,0x48,0x85,0xc0,0x74,0x18,0xc7,0x80,0x78,0x03,0x00,0x00
        };
        static const char createLookupMask[] = "xxxxxxxxxxxxxxxxxxxx????xxxxxxxxxxx????xxx????xxxxxxxxxxxxxx";
        // Window command handler (create_race_light, sel_class...), exact
        static const BYTE createClick[] = {
            0x48,0x89,0x5c,0x24,0x08,0x57,0x48,0x83,0xec,0x30,0x48,0x8b,0xf9,0x48,0x8b,0xda,
            0x48,0x8b,0x0a,0x48,0x8b,0x01,0xff,0x90,0xb0,0x00,0x00,0x00,0x48,0x8b,0xc8,0x48,
            0x8d,0x15,0xe2,0x41,0xb3,0x00,0xff,0x15,0x4c,0x60,0xa0,0x00,0x85,0xc0,0x0f,0x84
        };
        static const size_t createClickGender = 0x391; // mov r8d,[gender]; mov r9b,1; mov rcx,rdi; call select
        // Class select: mov [rsp+20h],r9b; push rbp/rsi/r12/r13/r14; lea rbp,[rsp-40h]
        static const BYTE createSelect[] = {
            0x44,0x88,0x4c,0x24,0x20,0x55,0x56,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x8d,0x6c
        };
        // Position -> class: cmp ecx,0Ch; ja; movsxd rax,ecx; lea rdx,[base]; mov ecx,[...]
        static const BYTE slotToClass[] = {
            0x83,0xf9,0x0c,0x77,0x5e,0x48,0x63,0xc1,0x48,0x8d,0x15,0,0,0,0,0x8b
        };
        // Class -> position: dec ecx; cmp ecx,18h; ja; movsxd rax,ecx; lea rdx,[base]
        static const BYTE classToSlot[] = {
            0xff,0xc9,0x83,0xf9,0x18,0x77,0x5e,0x48,0x63,0xc1,0x48,0x8d,0x15,0,0,0
        };
        static const char slotMask[] = "xxxxxxxxxxx????x";
        static const char classSlotMask[] = "xxxxxxxxxxxxx???";
        // Preview character slot: xor ecx,ecx; cmp r9d,1; jne other; lea eax,[rdx-1]; cmp eax,18h
        static const BYTE previewSlot[] = {
            0x33,0xc9,0x41,0x83,0xf9,0x01,0x0f,0x85,0,0,0,0,0x8d,0x42,0xff,0x83
        };
        static const char previewMask[] = "xxxxxxxx????xxxx";
        static_assert(sizeof(createLookupMask) - 1 == sizeof(createLookup), "Create lookup mask length");
        static_assert(sizeof(slotMask) - 1 == sizeof(slotToClass), "Slot mask length");
        static_assert(sizeof(classSlotMask) - 1 == sizeof(classToSlot), "Class slot mask length");
        static_assert(sizeof(previewMask) - 1 == sizeof(previewSlot), "Preview mask length");
        static_assert(sizeof(classKeyMask) - 1 == sizeof(classKeyW), "Class key mask length");
        static_assert(sizeof(typeNameMask) - 1 == sizeof(typeName), "Harp type name signature mask length");
        static_assert(sizeof(damageMask) - 1 == sizeof(damage), "Harp damage signature mask length");
        static_assert(sizeof(damageCheckMask) - 1 == sizeof(damageCheck), "Harp damage check mask length");
        static_assert(sizeof(enchantAttackMask) - 1 == sizeof(enchantAttack), "Harp enchant mask length");
        static_assert(sizeof(enchantBoostMask) - 1 == sizeof(enchantBoost), "Harp enchant mask length");
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
        auto target = [&](BYTE* call) -> BYTE* {
            BYTE* to = call[0] == 0xe8 ? call + 5 + *(int32_t*)(call + 1) : nullptr;
            return to && to >= base && to < base + image ? to : nullptr;
        };
        BYTE* typeNameStart = QunaFindUnique(base, nt, typeName, typeNameMask, sizeof(typeName));
        BYTE* typeNameTo[3] = {};
        for (size_t i = 0; typeNameStart && i < 3; ++i) typeNameTo[i] = target(typeNameStart + typeNameCalls[i]);
        BYTE* damageStart = QunaFindUnique(base, nt, damage, damageMask, sizeof(damage));
        BYTE* check = QunaFindUnique(base, nt, damageCheck, damageCheckMask, sizeof(damageCheck));
        BYTE* isModel = check ? target(check + 3) : nullptr;
        BYTE* hasAnimation = check ? target(check + 0x13) : nullptr;
        if (!typeNameTo[0] || !typeNameTo[1] || !typeNameTo[2] || !damageStart || !isModel ||
            !hasAnimation || check < damageStart || check > damageStart + 0x400) {
            OutputDebugStringA("[Harp] Unsupported client; tooltip/damage signatures not found.\n");
            __leave;
        }
        // The enchant tables are data, patched on first use (HarpPatchEnchantTables).
        const struct { const BYTE* pattern; const char* mask; size_t size; } enchantSigs[] = {
            { enchantAttack, enchantAttackMask, sizeof(enchantAttack) },
            { enchantBoost, enchantBoostMask, sizeof(enchantBoost) },
        };
        for (size_t i = 0; i < 2; ++i) {
            BYTE* found = QunaFindUnique(base, nt, enchantSigs[i].pattern, enchantSigs[i].mask,
                                         enchantSigs[i].size);
            BYTE* lea = found ? found + enchantLea : nullptr;
            BYTE* table = lea ? lea + 7 + *(int32_t*)(lea + 3) : nullptr;
            if (table && table >= base && table + 20 * 8 <= base + image)
                s_harpEnchantTables[i] = (int32_t*)table;
            else
                OutputDebugStringA("[Harp] Enchant table not found.\n");
        }
        BYTE* classNameStart = QunaFindUnique(base, nt, className, classNameMask, sizeof(className));
        if (!classNameStart) {
            OutputDebugStringA("[Harp] Unsupported client; class name signature not found.\n");
            __leave;
        }
        s_harpClassName = (HarpClassName)classNameStart;
        BYTE* characterSlotStart = QunaFindUnique(base, nt, characterSlot, characterSlotMask, sizeof(characterSlot));
        if (!characterSlotStart) {
            OutputDebugStringA("[Harp] Unsupported client; character slot signature not found.\n");
            __leave;
        }
        s_harpCharacterSlot = (HarpCharacterSlot)characterSlotStart;
        {
            static const char exact28[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx";
            static const char exact48[] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
            static const char exact16[] = "xxxxxxxxxxxxxxxx";
            BYTE* init = QunaFindUnique(base, nt, createInit, exact28, sizeof(createInit));
            BYTE* lookup = QunaFindUnique(base, nt, createLookup, createLookupMask, sizeof(createLookup));
            BYTE* click = QunaFindUnique(base, nt, createClick, exact48, sizeof(createClick));
            BYTE* sel = QunaFindUnique(base, nt, createSelect, exact16, sizeof(createSelect));
            BYTE* toClass = QunaFindUnique(base, nt, slotToClass, slotMask, sizeof(slotToClass));
            BYTE* toSlot = QunaFindUnique(base, nt, classToSlot, classSlotMask, sizeof(classToSlot));
            BYTE* preview = QunaFindUnique(base, nt, previewSlot, previewMask, sizeof(previewSlot));
            BYTE* g = click ? click + createClickGender : nullptr;
            // mov r8d,[rip+x]; mov r9b,1; mov rcx,rdi; call select -- the call must land on select.
            const bool clickOk = g && g[0] == 0x44 && g[1] == 0x8b && g[2] == 0x05 && g[7] == 0x41 &&
                                 g[8] == 0xb1 && g[9] == 0x01 && g[13] == 0xe8 &&
                                 g + 18 + *(int32_t*)(g + 14) == sel;
            if (!init || !lookup || !clickOk || !toClass || !toSlot || !preview) {
                OutputDebugStringA("[Harp] Unsupported client; creation screen signatures not found.\n");
                __leave;
            }
            s_harpCreateGender = (const int*)(g + 7 + *(int32_t*)(g + 3));
            s_harpButtonTypeTo = lookup + 24 + *(int32_t*)(lookup + 20);
            s_harpButtonTypeFrom = lookup + 39 + *(int32_t*)(lookup + 35);
            s_harpDynamicCast = (HarpDynamicCast)(lookup + 46 + *(int32_t*)(lookup + 42));
            s_harpCreateInit = (HarpCreateInit)init;
            s_harpCreateClick = (HarpCreateClick)click;
            s_harpCreateSelect = (HarpCreateSelect)sel;
            s_harpSlotToClass = (HarpSlotToClass)toClass;
            s_harpClassToSlot = (HarpClassToSlot)toSlot;
            s_harpPreviewSlot = (HarpPreviewSlot)preview;
        }
        s_harpClassKey = (HarpClassKey)QunaFindUnique(base, nt, classKey, classKeyMask, sizeof(classKey));
        s_harpClassKeyW = (HarpClassKeyW)QunaFindUnique(base, nt, classKeyW, classKeyMask, sizeof(classKeyW));
        s_harpClassFromName = (HarpClassFromName)QunaFindUnique(base, nt, classFromName, classFromNameMask,
                                                                sizeof(classFromName));
        if (!s_harpClassKey || !s_harpClassKeyW || !s_harpClassFromName) {
            OutputDebugStringA("[Harp] Unsupported client; class key signatures not found.\n");
            __leave;
        }
        s_harpImageBase = base;
        s_harpImageSize = image;
        s_harpSuffixSwitch = QunaFindUnique(base, nt, suffixSwitch, suffixSwitchMask, sizeof(suffixSwitch));
        if (!s_harpSuffixSwitch) OutputDebugStringA("[Harp] Animation suffix switch not found.\n");
        // The icon table is only located here; it is written on first use (HarpPatchClassIconsOnce).
        BYTE* iconReader = QunaFindUnique(base, nt, classIcon, classIconMask, sizeof(classIcon));
        BYTE* iconLea = iconReader ? iconReader + classIconLea : nullptr;
        const char** icons = iconLea ? (const char**)(iconLea + 7 + *(int32_t*)(iconLea + 3)) : nullptr;
        if (icons && (BYTE*)icons >= base && (BYTE*)(icons + kHarpClassIconSlots) <= base + image)
            s_harpClassIcons = icons;
        else
            OutputDebugStringA("[Harp] Class icon table not found.\n");
        BYTE* emblemCode = QunaFindUnique(base, nt, emblem, emblemMask, sizeof(emblem));
        BYTE* emblemLeaAt = emblemCode ? emblemCode + emblemLea : nullptr;
        BYTE* names = emblemLeaAt ? emblemLeaAt + 7 + *(int32_t*)(emblemLeaAt + 3) : nullptr;
        if (names && names - 4 >= base && names + 27 * kHarpEmblemStride <= base + image)
            s_harpEmblemNames = (wchar_t*)names;
        else
            OutputDebugStringA("[Harp] Class emblem table not found.\n");
        s_harpTypeName = (HarpWeaponTypeName)typeNameStart;
        s_harpRegistry = (HarpRegistry)typeNameTo[0];
        s_harpFindManager = (HarpFindManager)typeNameTo[1];
        s_harpString = (HarpString)typeNameTo[2];
        s_harpDamage = (HarpDamageAnimation)damageStart;
        s_harpIsModel = (HarpIsModel)isModel;
        s_harpHasAnimation = (HarpHasAnimation)hasAnimation;
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
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpTypeName, HarpWeaponTypeNameHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpDamage, HarpDamageAnimationHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpClassName, HarpClassNameHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpCharacterSlot, HarpCharacterSlotHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpClassKey, HarpClassKeyHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpClassKeyW, HarpClassKeyWHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpClassFromName, HarpClassFromNameHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpCreateInit, HarpCreateInitHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpCreateClick, HarpCreateClickHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpCreateSelect, HarpCreateSelectHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpSlotToClass, HarpSlotToClassHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpClassToSlot, HarpClassToSlotHook);
        if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_harpPreviewSlot, HarpPreviewSlotHook);
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
static void HarpOnModuleLoaded(HMODULE) {}
#endif
