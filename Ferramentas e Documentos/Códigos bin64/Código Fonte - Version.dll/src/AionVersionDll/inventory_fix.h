#pragma once

// Classic 5.0 x64: inventario numa lista unica, como no Reforg (cliente NA de 20/10).
//
// O DlgInventory do 5.0 tem 5 abas (button%d/inv%d/list%d), de 27 slots cada. O XML novo
// (teste_harpa_58.py --inventario) deixa so a list0 e a aba sem cabecalho; o codigo nativo ja
// acha a celula de cada slot subtraindo o tamanho real de cada lista (0x18056deb0), entao o que
// falta sao os limites de 27 escritos no codigo:
//
//   init   laco que cria as celulas da list0 (0x180af1320 acrescenta uma por volta) e grava o slot
//          de cada uma em +0x9c: 27 -> 135 (27 + 12 expansoes de 9, o maximo do servidor).
//   fx     dois lacos de efeito por celula: 27 -> 135 (so leem; o tamanho real e conferido).
//   lock   posiciona o botao "extend" (barra roxa) na primeira linha bloqueada: so fazia isso
//          com menos de 27 slots na aba e usava a linha (slots % 27) / 9. Passa a comparar com o
//          numero de celulas da lista e a usar slots / 9. Com abas de 27 o resultado e o mesmo.
//
// O Game.dll do Reforg (dump de 21/10) faz o mesmo: uma list0 numerada de 0 a 296 (0x129).
#if defined(_M_AMD64)
#ifndef INVENTORY_FIX_TEST
static SRWLOCK s_inventoryLock = SRWLOCK_INIT;
static bool s_inventoryChecked = false;

static const BYTE kInventorySlots = 135;

struct InventoryPatch {
    const char* name;
    const BYTE* signature;
    size_t signatureSize;
    size_t offset;          // onde o patch comeca dentro da assinatura
    const BYTE* expected;   // bytes originais nesse ponto
    const BYTE* replacement;
    size_t size;
};

// A grade so mostra as linhas liberadas e a linha do cadeado (o "extend"); cada expansao desce
// uma linha. Roda depois da funcao nativa do cadeado (0x180573160), que todo caminho de
// atualizacao chama antes do relayout (vtable +0x788): o relayout ja ve a altura nova.
using InventoryLockLayout = void (__fastcall*)(void* dialog, void* info);
using InventoryGetFrame = const double* (__fastcall*)(void* widget);   // {x, y, w, h}
using InventorySetFrame = void (__fastcall*)(void* widget, const double* frame);
static InventoryLockLayout s_inventoryLockLayout = nullptr;
static double s_inventoryListPad = -1, s_inventoryContainerPad = -1;

static void InventoryFitGrid(BYTE* dialog) {
    BYTE* list = *(BYTE**)(dialog + 0x5a0);      // list0
    BYTE* container = *(BYTE**)(dialog + 0x5c8); // inv0
    if (!list || !container) return;
    const long long cells = (*(BYTE**)(list + 0x380) - *(BYTE**)(list + 0x378)) / 8;
    if (cells <= 27) return; // layout de abas: nada a fazer
    const int totalRows = (int)((cells + 8) / 9);
    int capacity = *(int*)(dialog + 0x650);
    if (capacity < 0) capacity = 0;
    int rows = (capacity + 8) / 9 + (capacity < cells ? 1 : 0);
    if (rows < 1) rows = 1;
    if (rows > totalRows) rows = totalRows;
    const double pitch = *(double*)(list + 0x320) + *(double*)(list + 0x300);
    if (!(pitch > 0)) return;

    auto listVt = *(void***)list;
    auto containerVt = *(void***)container;
    double listFrame[4], containerFrame[4];
    memcpy(listFrame, ((InventoryGetFrame)listVt[0x198 / 8])(list), sizeof(listFrame));
    memcpy(containerFrame, ((InventoryGetFrame)containerVt[0x198 / 8])(container), sizeof(containerFrame));
    // Margens do XML, medidas na primeira vez (grade inteira, ainda sem corte).
    if (s_inventoryListPad < 0) {
        s_inventoryListPad = listFrame[3] - totalRows * pitch;
        s_inventoryContainerPad = containerFrame[3] - (listFrame[1] + listFrame[3]);
        if (s_inventoryListPad < 0) s_inventoryListPad = 0;
        if (s_inventoryContainerPad < 0) s_inventoryContainerPad = 0;
    }
    const double height = rows * pitch + s_inventoryListPad;
    if (listFrame[3] == height) return;
    listFrame[3] = height;
    ((InventorySetFrame)listVt[0x178 / 8])(list, listFrame);
    containerFrame[3] = listFrame[1] + height + s_inventoryContainerPad;
    ((InventorySetFrame)containerVt[0x178 / 8])(container, containerFrame);
}

// Animacao de desbloqueio: o mesmo efeito que o guarda-roupa toca no slot que abre
// (sys_UIfx.wardrobe.extend, 0x6FD212). As celulas da lista nao sao widgets (0x180acec20 nao tem
// vtable), entao o efeito vai na barra do cadeado, antes de a funcao nativa descer a barra uma linha.
static void* s_inventoryDialog = nullptr;
static int s_inventoryCapacity = -1;

static void InventoryPlayUnlock(BYTE* dialog) {
    const int capacity = *(int*)(dialog + 0x650);
    const bool unlocked = dialog == s_inventoryDialog && s_inventoryCapacity >= 0 &&
                          capacity > s_inventoryCapacity;
    s_inventoryDialog = dialog;
    s_inventoryCapacity = capacity;
    if (unlocked) ChargePlayWidgetEffect(*(void**)(dialog + 0x560), "sys_UIfx.wardrobe.extend");
}

static void __fastcall InventoryLockLayoutHook(void* dialog, void* info) {
    __try {
        InventoryPlayUnlock((BYTE*)dialog);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        OutputDebugStringA("[Inventory] Unlock effect failed.\n");
    }
    s_inventoryLockLayout(dialog, info);
    __try {
        InventoryFitGrid((BYTE*)dialog);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        OutputDebugStringA("[Inventory] Grid fit failed.\n");
    }
}

static BYTE* InventoryFindUnique(BYTE* base, PIMAGE_NT_HEADERS nt, const BYTE* pattern, size_t size) {
    BYTE* found = nullptr;
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; ++i, ++section) {
        if (!(section->Characteristics & IMAGE_SCN_MEM_EXECUTE)) continue;
        const DWORD start = section->VirtualAddress;
        const DWORD length = section->Misc.VirtualSize;
        if (start >= nt->OptionalHeader.SizeOfImage ||
            length > nt->OptionalHeader.SizeOfImage - start || length < size) continue;
        BYTE* begin = base + start;
        for (size_t offset = 0; offset <= length - size; ++offset) {
            if (begin[offset] != pattern[0] || memcmp(begin + offset, pattern, size) != 0) continue;
            if (found) return nullptr; // Ambiguous builds are not patched.
            found = begin + offset;
        }
    }
    return found;
}

static void InventoryWriteCode(BYTE* at, const BYTE* data, size_t size) {
    DWORD old;
    if (!VirtualProtect(at, size, PAGE_EXECUTE_READWRITE, &old)) return;
    memcpy(at, data, size);
    VirtualProtect(at, size, old, &old);
    FlushInstructionCache(GetCurrentProcess(), at, size);
}

static void InstallInventoryFix(HMODULE module) {
    if (!TryAcquireSRWLockExclusive(&s_inventoryLock)) return;
    __try {
        if (s_inventoryChecked) __leave;
        BYTE* base = (BYTE*)module;
        auto dos = (PIMAGE_DOS_HEADER)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE || dos->e_lfanew <= 0 ||
            dos->e_lfanew > 0x10000000) __leave;
        auto nt = (PIMAGE_NT_HEADERS)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE ||
            nt->FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64) __leave;
        s_inventoryChecked = true;

        // inc ebx; inc ebp; inc rdi; cmp rdi,1Bh; jl -5Bh; jmp +58h (fim do laco da list0)
        static const BYTE initSig[] = { 0xff,0xc3,0xff,0xc5,0x48,0xff,0xc7,0x48,0x83,0xff,0x1b,0x7c,0xa5,0xeb,0x58 };
        static const BYTE initOld[] = { 0x48,0x83,0xff,0x1b,0x7c,0xa5 };
        // cmp dil,135; jb -5Bh (sem sinal: rdi vai de 0 a 134)
        static const BYTE initNew[] = { 0x40,0x80,0xff,kInventorySlots,0x72,0xa5 };

        // inc esi; inc rbx; cmp rbx,1Bh; jl rel32; add r14,8
        static const BYTE fx0Sig[] = { 0xff,0xc6,0x48,0xff,0xc3,0x48,0x83,0xfb,0x1b,0x0f,0x8c,0x54,0xff,0xff,0xff,0x49,0x83,0xc6,0x08 };
        // inc edi; inc rbx; cmp rbx,1Bh; jl rel32; inc rbp
        static const BYTE fx1Sig[] = { 0xff,0xc7,0x48,0xff,0xc3,0x48,0x83,0xfb,0x1b,0x0f,0x8c,0x66,0xff,0xff,0xff,0x48,0xff,0xc5 };
        static const BYTE fxOld[] = { 0x48,0x83,0xfb,0x1b,0x0f,0x8c };
        // cmp bl,135; nop; jb rel32 (o mesmo deslocamento)
        static const BYTE fxNew[] = { 0x80,0xfb,kInventorySlots,0x90,0x0f,0x82 };

        // cmp esi,1Bh; jge +258h; mov ecx,esi; mov eax,4BDA12F7h; imul esi
        static const BYTE lockCmpSig[] = { 0x83,0xfe,0x1b,0x0f,0x8d,0x58,0x02,0x00,0x00,0x8b,0xce,0xb8,0xf7,0x12,0xda,0x4b,0xf7,0xee };
        static const BYTE lockCmpOld[] = { 0x83,0xfe,0x1b };
        static const BYTE lockCmpNew[] = { 0x44,0x39,0xfe }; // cmp esi,r15d (r15 = celulas da lista)

        // imul eax,edx,1Bh; sub ecx,eax; mov eax,38E38E39h; imul ecx
        static const BYTE lockModSig[] = { 0x6b,0xc2,0x1b,0x2b,0xc8,0xb8,0x39,0x8e,0xe3,0x38,0xf7,0xe9 };
        static const BYTE lockModOld[] = { 0x2b,0xc8 };
        static const BYTE lockModNew[] = { 0x90,0x90 };    // ecx = slots, nao slots % 27

        const InventoryPatch patches[] = {
            { "init", initSig, sizeof(initSig), 7, initOld, initNew, sizeof(initNew) },
            { "fx0", fx0Sig, sizeof(fx0Sig), 5, fxOld, fxNew, sizeof(fxNew) },
            { "fx1", fx1Sig, sizeof(fx1Sig), 5, fxOld, fxNew, sizeof(fxNew) },
            { "lock cmp", lockCmpSig, sizeof(lockCmpSig), 0, lockCmpOld, lockCmpNew, sizeof(lockCmpNew) },
            { "lock mod", lockModSig, sizeof(lockModSig), 3, lockModOld, lockModNew, sizeof(lockModNew) },
        };
        static_assert(sizeof(initOld) == sizeof(initNew) && sizeof(fxOld) == sizeof(fxNew) &&
                      sizeof(lockCmpOld) == sizeof(lockCmpNew) && sizeof(lockModOld) == sizeof(lockModNew),
                      "Inventory patch sizes");

        // Tudo ou nada: com um ponto faltando, a lista unica ficaria pela metade.
        BYTE* sites[_countof(patches)] = {};
        for (size_t i = 0; i < _countof(patches); ++i) {
            const InventoryPatch& p = patches[i];
            BYTE* at = InventoryFindUnique(base, nt, p.signature, p.signatureSize);
            if (!at || memcmp(at + p.offset, p.expected, p.size) != 0) {
                char message[160];
                sprintf_s(message, "[Inventory] Unsupported client; signature '%s' not unique.\n", p.name);
                OutputDebugStringA(message);
                __leave;
            }
            sites[i] = at + p.offset;
        }
        // Inicio da funcao do cadeado: 0x123 bytes antes do "cmp esi,1Bh".
        // mov [rsp+18h],rbx; mov [rsp+20h],rbp; push rsi/rdi/r12/r13/r14; sub rsp,50h; mov r13,rcx
        static const BYTE lockStart[] = {
            0x48,0x89,0x5c,0x24,0x18,0x48,0x89,0x6c,0x24,0x20,0x56,0x57,0x41,0x54,0x41,0x55,
            0x41,0x56,0x48,0x83,0xec,0x50,0x4c,0x8b,0xe9
        };
        BYTE* lockFunction = sites[3] - 0x123;
        if (memcmp(lockFunction, lockStart, sizeof(lockStart)) != 0) {
            OutputDebugStringA("[Inventory] Unsupported client; lock layout start not found.\n");
            __leave;
        }

        for (size_t i = 0; i < _countof(patches); ++i)
            InventoryWriteCode(sites[i], patches[i].replacement, patches[i].size);

        s_inventoryLockLayout = (InventoryLockLayout)lockFunction;
        LONG error = DetourTransactionBegin();
        if (error == NO_ERROR) {
            error = DetourUpdateThread(GetCurrentThread());
            if (error == NO_ERROR) error = DetourAttach(&(PVOID&)s_inventoryLockLayout, InventoryLockLayoutHook);
            if (error == NO_ERROR) error = DetourTransactionCommit();
            else DetourTransactionAbort();
        }
        OutputDebugStringA(error == NO_ERROR ?
            "[Inventory] Single-list inventory installed (135 slots, grid follows the cube size).\n" :
            "[Inventory] Single-list inventory installed; grid fit hook failed.\n");
    }
    __finally {
        ReleaseSRWLockExclusive(&s_inventoryLock);
    }
}
#endif
#else
static void InstallInventoryFix(HMODULE) {}
#endif
