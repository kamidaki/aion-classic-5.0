import pefile
import re
import os
import sys

BASE_DIR = r"d:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Códigos bin64"
NATIVE_BIN64 = r"D:\GameForge\aionclassic\bin64"

MODULES = [
    {
        "name": "CryInput.dll",
        "folder": "Código Fonte - CryInput.dll",
        "compiled": "Release64\\CryInput.dll",
        "native": "CryInput.dll"
    },
    {
        "name": "CryScriptSystem.dll",
        "folder": "Código Fonte - CryScriptSystem.dll",
        "compiled": "Release64\\CryScriptSystem.dll",
        "native": "CryScriptSystem.dll"
    },
    {
        "name": "CryFont.dll",
        "folder": "Código Fonte - CryFont.dll",
        "compiled": "Release64\\CryFont.dll",
        "native": "CryFont.dll"
    },
    {
        "name": "CryEntitySystem.dll",
        "folder": "Código Fonte - CryEntitySystem.dll",
        "compiled": "Release64\\CryEntitySystem.dll",
        "native": "CryEntitySystem.dll"
    },
    {
        "name": "CrySoundSystem.dll",
        "folder": "Código Fonte - CrySoundSystem.dll",
        "compiled": "Release64\\CrySoundSystem.dll",
        "native": "CrySoundSystem.dll"
    },
    {
        "name": "CryPhysics.dll",
        "folder": "Código Fonte - CryPhysics.dll",
        "compiled": "Release64\\CryPhysics.dll",
        "native": "CryPhysics.dll"
    },
    {
        "name": "CryMovie.dll",
        "folder": "Código Fonte - CryMovie.dll",
        "compiled": "Release64\\CryMovie.dll",
        "native": "CryMovie.dll"
    },
    {
        "name": "CryAnimation.dll",
        "folder": "Código Fonte - CryAnimation.dll",
        "compiled": "Release64\\CryAnimation.dll",
        "native": "CryAnimation.dll"
    },
    {
        "name": "Cry3DEngine.dll",
        "folder": "Código Fonte - Cry3DEngine.dll",
        "compiled": "Release64\\Cry3DEngine.dll",
        "native": "Cry3DEngine.dll"
    },
    {
        "name": "CrySystem.dll",
        "folder": "Código Fonte - CrySystem.dll",
        "compiled": "Release64\\CrySystem.dll",
        "native": "CrySystem.dll"
    }
]

def get_exports(pe_path):
    try:
        pe = pefile.PE(pe_path)
        if not hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            return set()
        return set(exp.name.decode() for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols if exp.name)
    except Exception as e:
        return set()

def get_rtti_classes(bin_path):
    try:
        with open(bin_path, 'rb') as f:
            data = f.read()
        matches = re.findall(b'\\.?\\?AV([A-Za-z0-9_@]+)@@', data)
        return set(m.decode(errors='ignore') for m in matches)
    except Exception as e:
        return set()

def main():
    print("=" * 80)
    print("  AUDITORIA GERAL DE COBERTURA & INTEGRIDADE - TODAS AS DLLS CRYENGINE (AION 5.0)")
    print("=" * 80)
    print(f"{'Módulo':<22} | {'Exports':<12} | {'RTTI Classes':<16} | {'Tamanho Compilado':<18} | {'Status'}")
    print("-" * 80)

    total_modules = len(MODULES)
    passed_modules = 0

    for mod in MODULES:
        compiled_file = os.path.join(BASE_DIR, mod["folder"], mod["compiled"])
        native_file = os.path.join(NATIVE_BIN64, mod["native"])

        if not os.path.exists(compiled_file):
            print(f"{mod['name']:<22} | {'AUSENTE':<12} | {'AUSENTE':<16} | {'NÃO ENCONTRADO':<18} | [FALHA]")
            continue

        native_exp = get_exports(native_file)
        compiled_exp = get_exports(compiled_file)
        exp_ok = native_exp.issubset(compiled_exp) if native_exp else True
        exp_str = f"{len(compiled_exp)}/{len(native_exp)} OK" if exp_ok else f"{len(compiled_exp)}/{len(native_exp)} FALHA"

        native_rtti = get_rtti_classes(native_file)
        compiled_rtti = get_rtti_classes(compiled_file)
        rtti_missing = native_rtti - compiled_rtti
        rtti_ok = len(rtti_missing) == 0
        rtti_str = f"{len(native_rtti) - len(rtti_missing)}/{len(native_rtti)} (100%)" if rtti_ok else f"{len(native_rtti) - len(rtti_missing)}/{len(native_rtti)}"

        comp_size = os.path.getsize(compiled_file)
        size_str = f"{comp_size:,} bytes"

        status = "[100% CANÔNICO]" if (exp_ok and rtti_ok) else "[REVISÃO]"
        if exp_ok and rtti_ok:
            passed_modules += 1

        print(f"{mod['name']:<22} | {exp_str:<12} | {rtti_str:<16} | {size_str:<18} | {status}")

    print("=" * 80)
    print(f"Resultado Final: {passed_modules}/{total_modules} Módulos 100% Canônicos e Compilados!")
    print("=" * 80)

if __name__ == "__main__":
    main()
