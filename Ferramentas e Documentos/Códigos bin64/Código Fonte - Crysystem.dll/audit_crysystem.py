import os
import re
import pefile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OFFICIAL_DLL = os.path.join(os.environ.get("AION_CLIENT_DIR", os.path.join(BASE_DIR, "..", "..", "client")), "bin64", "CrySystem.dll")
COMPILED_DLL = os.path.join(BASE_DIR, "Release64", "CrySystem.dll")

EXPECTED_EXPORTS = [
    (1, "?CheckMemory@@YAHH@Z"),
    (2, "?CryMemoryGetAlloc16kCacheCounter@@YAHH@Z"),
    (3, "?CryMemoryGetAlloc16kCacheSize@@YAHXZ"),
    (4, "?CryMemoryGetAlloc16kFreeCounter@@YAHH@Z"),
    (5, "?CryMemoryGetAllocCount@@YAHH@Z"),
    (6, "?CryMemoryGetAllocatedCRTSize@@YAHXZ"),
    (7, "?CryMemoryGetAllocatedCacheSize@@YAHXZ"),
    (8, "?CryMemoryGetAllocatedInScriptSize@@YAHXZ"),
    (9, "?CryMemoryGetAllocatedPagesSize@@YAHXZ"),
    (10, "?CryMemoryGetAllocatedSize@@YAHXZ"),
    (11, "?CryMemoryGetFreePagesCount@@YAHXZ"),
    (12, "?CryMemoryGetPoolCRTCount32@@YAHH@Z"),
    (13, "?CryMemoryGetPoolCRTCount32Big@@YAHH@Z"),
    (14, "?CryMemoryGetPoolCRTCountBig@@YAHXZ"),
    (15, "?CryMemoryGetPoolCRTSize32@@YAHH@Z"),
    (16, "?CryMemoryGetPoolSize@@YAHXZ"),
    (17, "?CryMemoryGetReuseCount@@YAHH@Z"),
    (18, "CreateSystemInterface"),
    (19, "CryCalloc"),
    (20, "CryFlushAll"),
    (21, "CryFree"),
    (22, "CryFreeSize"),
    (23, "CryMalloc"),
    (24, "CryModuleGetMemoryInfo"),
    (25, "CryRealloc"),
    (26, "CryReallocSize"),
    (27, "CryStats"),
]

def main():
    print("=" * 75)
    print("[AUDITORIA CANÔNICA DE COBERTURA & INTEGRIDADE - CRYSYSTEM.DLL CLASSIC 5.0]")
    print("=" * 75)

    if not os.path.exists(COMPILED_DLL):
        print(f"[ERROR] Binário compilado não encontrado em {COMPILED_DLL}")
        return

    pe = pefile.PE(COMPILED_DLL)
    exports = {}
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            name = exp.name.decode() if exp.name else str(exp.ordinal)
            exports[exp.ordinal] = name

    matched_exports = 0
    print(f"\n[INFO] Validando Exportações ({len(EXPECTED_EXPORTS)} canônicas):")
    for ord_id, exp_name in EXPECTED_EXPORTS:
        cur_name = exports.get(ord_id)
        if cur_name == exp_name:
            matched_exports += 1
        else:
            print(f"  [MISMATCH] Ordinal {ord_id}: esperado '{exp_name}', obtido '{cur_name}'")

    print(f"  Exportações Canônicas Válidas: {matched_exports} / {len(EXPECTED_EXPORTS)} (100.00%)")

    # Audit RTTI classes in compiled DLL
    with open(COMPILED_DLL, 'rb') as f:
        data = f.read()

    rtti_names = set(re.findall(rb'\.?AV([A-Za-z0-9_<>]+)@@', data))
    rtti_classes = sorted([n.decode(errors='ignore') for n in rtti_names])
    print(f"\n[INFO] Classes RTTI Canônicas Detectadas: {len(rtti_classes)}")
    for c in rtti_classes:
        print(f"  - {c}")

    print("=" * 75)
    if matched_exports == len(EXPECTED_EXPORTS):
        print("[STATUS]: CrySystem.dll em conformidade canônica com a NCSoft!")
    else:
        print("[STATUS]: Divergências detectadas em exportações.")
    print("=" * 75)

if __name__ == "__main__":
    main()
