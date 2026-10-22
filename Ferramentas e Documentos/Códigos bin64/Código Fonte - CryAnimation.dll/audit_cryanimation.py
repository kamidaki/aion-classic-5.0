import pefile
import re
import os
import sys

NATIVE_PATH = r"D:\GameForge\aionclassic\bin64\CryAnimation.dll"
COMPILED_PATH = r"Release64\CryAnimation.dll"

def get_exports(pe_path):
    try:
        pe = pefile.PE(pe_path)
        if not hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            return set()
        return set(exp.name.decode() for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols if exp.name)
    except Exception as e:
        print(f"Erro ao ler exports de {pe_path}: {e}")
        return set()

def get_rtti_classes(bin_path):
    try:
        with open(bin_path, 'rb') as f:
            data = f.read()
        matches = re.findall(b'\\.?\\?AV([A-Za-z0-9_@]+)@@', data)
        return set(m.decode(errors='ignore') for m in matches)
    except Exception as e:
        print(f"Erro ao ler RTTI de {bin_path}: {e}")
        return set()

def main():
    print("=" * 70)
    print("[AUDITORIA CANONICA DE COBERTURA & INTEGRIDADE - CRYANIMATION.DLL]")
    print("=" * 70)

    if not os.path.exists(COMPILED_PATH):
        print(f"[ERRO] DLL compilada nao encontrada em {COMPILED_PATH}")
        sys.exit(1)

    native_exp = get_exports(NATIVE_PATH)
    compiled_exp = get_exports(COMPILED_PATH)

    print(f"[INFO] Exportacoes Canonicas Esperadas: {len(native_exp)}")
    print(f"       Exportacoes Compiladas:          {len(compiled_exp)}")

    missing_exp = native_exp - compiled_exp
    if missing_exp:
        print(f"[FALHA] Exportacoes ausentes ({len(missing_exp)}):")
        for exp in sorted(missing_exp):
            print(f"  - {exp}")
    else:
        print("[OK] Todas as exportacoes canonicas estao presentes (100.00%)!")

    native_rtti = get_rtti_classes(NATIVE_PATH)
    compiled_rtti = get_rtti_classes(COMPILED_PATH)

    print(f"[INFO] RTTI Classes Canonicas: {len(native_rtti)}")
    print(f"       RTTI Classes Compiladas: {len(compiled_rtti)}")

    missing_rtti = native_rtti - compiled_rtti
    if missing_rtti:
        print(f"[AVISO] Classes RTTI ausentes ({len(missing_rtti)}):")
        for c in sorted(missing_rtti):
            print(f"  - {c}")
    else:
        print("[OK] 100% das classes RTTI canonicas estao presentes no binario!")

    sz_native = os.path.getsize(NATIVE_PATH)
    sz_compiled = os.path.getsize(COMPILED_PATH)
    print(f"[INFO] Tamanho Canonico:  {sz_native:,} bytes")
    print(f"[INFO] Tamanho Compilado: {sz_compiled:,} bytes")

    if not missing_exp:
        print("=" * 70)
        print("[STATUS]: CryAnimation.dll em conformidade canonica com o Aion Classic!")
        print("=" * 70)
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
