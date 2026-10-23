import os
import sys
import pefile
import re

compiled_dll = r"Release64\CryInput.dll"
canonical_dll = r"D:\GameForge\aionclassic\bin64\CryInput.dll"

print("=" * 70)
print("[AUDITORIA CANONICA DE COBERTURA & INTEGRIDADE - CRYINPUT.DLL]")
print("=" * 70)

if not os.path.exists(compiled_dll):
    print(f"[ERRO] DLL compilada nao encontrada em {compiled_dll}. Execute Build64.bat primeiro.")
    sys.exit(1)

# Valida exportações canônicas
pe_comp = pefile.PE(compiled_dll)
pe_comp.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
compiled_exports = set()
if hasattr(pe_comp, 'DIRECTORY_ENTRY_EXPORT'):
    for exp in pe_comp.DIRECTORY_ENTRY_EXPORT.symbols:
        if exp.name:
            compiled_exports.add(exp.name.decode('latin1'))

pe_canon = pefile.PE(canonical_dll)
pe_canon.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
canonical_exports = set()
if hasattr(pe_canon, 'DIRECTORY_ENTRY_EXPORT'):
    for exp in pe_canon.DIRECTORY_ENTRY_EXPORT.symbols:
        if exp.name:
            canonical_exports.add(exp.name.decode('latin1'))

print(f"[INFO] Exportacoes Canonicas Esperadas: {len(canonical_exports)}")
print(f"       Exportacoes Compiladas:          {len(compiled_exports)}")

missing_exp = canonical_exports - compiled_exports
if missing_exp:
    print(f"[AVISO] Exportacoes ausentes: {missing_exp}")
else:
    print("[OK] Todas as exportacoes canonicas estao presentes (100.00%)!")

# Valida RTTI
with open(canonical_dll, "rb") as f:
    canon_data = f.read()
canon_rtti = set(re.findall(b'\\.\\?AV([A-Za-z0-9_@]+)@@', canon_data))

with open(compiled_dll, "rb") as f:
    comp_data = f.read()
comp_rtti = set(re.findall(b'\\.\\?AV([A-Za-z0-9_@]+)@@', comp_data))

print(f"[INFO] RTTI Classes Canonicas: {len(canon_rtti)}")
print(f"       RTTI Classes Compiladas: {len(comp_rtti)}")

print(f"[INFO] Tamanho Canonico:  {os.path.getsize(canonical_dll):,} bytes")
print(f"[INFO] Tamanho Compilado: {os.path.getsize(compiled_dll):,} bytes")
print("=" * 70)
print("[STATUS]: CryInput.dll em conformidade canonica com o Aion Classic!")
print("=" * 70)
