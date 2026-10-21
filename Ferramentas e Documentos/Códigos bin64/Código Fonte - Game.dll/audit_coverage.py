import os
import re
import sys
import pefile

src_root = os.path.dirname(os.path.abspath(__file__))
rtti_file = os.path.join(src_root, "rtti_classes.txt")
game_dll_path = r"D:\GameForge\aionclassic\bin64\Game.dll"
compiled_dll_path = os.path.join(src_root, "Release64", "Game.dll")

print("=======================================================================")
print("[AUDITORIA CANÔNICA DE COBERTURA & INTEGRIDADE - GAME.DLL CLASSIC 5.0]")
print("=======================================================================")

if not os.path.exists(rtti_file):
    print(f"[ERRO CRÍTICO] Arquivo de classes canônicas '{rtti_file}' não encontrado!")
    sys.exit(1)

with open(rtti_file, "r", encoding="utf-8") as f:
    expected_classes = [l.strip() for l in f if l.strip()]

total_expected = len(expected_classes)
print(f"[INFO] Total de classes canônicas RTTI esperadas: {total_expected}")

# Validação do Binário Oficial Canônico
if os.path.exists(game_dll_path):
    bin_size = os.path.getsize(game_dll_path)
    with open(game_dll_path, "rb") as f:
        bin_data = f.read()
    print(f"[INFO] Binário Oficial Canônico: {game_dll_path} ({bin_size:,} bytes | {bin_size/(1024*1024):.2f} MB)")
else:
    print(f"[AVISO] Binário oficial em {game_dll_path} não acessível!")
    bin_data = b""

# Validação da DLL Compilada
if os.path.exists(compiled_dll_path):
    compiled_size = os.path.getsize(compiled_dll_path)
    print(f"[INFO] DLL Compilada Atual:    {compiled_dll_path} ({compiled_size:,} bytes | {compiled_size/(1024*1024):.2f} MB)")
    if bin_size > 0:
        gap = bin_size - compiled_size
        pct_size = (compiled_size / bin_size) * 100.0
        print(f"[INFO] Paridade de Tamanho Físico: {pct_size:.2f}% (Faltando {gap:,} bytes)")
else:
    print(f"[AVISO] DLL compilada não encontrada em {compiled_dll_path}. Execute Build64.bat.")

# Escaneamento do Código Fonte
classes_in_code = set()
fictitious_classes = set()

for root, dirs, files in os.walk(src_root):
    if "Release64" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith((".h", ".cpp")):
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    m = re.match(r'^\s*(?:class|struct)\s+([A-Za-z0-9_]+)', line)
                    if m:
                        cls_name = m.group(1)
                        classes_in_code.add(cls_name)
                        if bin_data and cls_name.encode("latin1") not in bin_data:
                            fictitious_classes.add(cls_name)

# Cobertura de Classes Canônicas
found_classes = set()
for c in expected_classes:
    # simplificação para classes templated ou qualificadas com namespace
    simple = c.split("<")[0].split("@")[0].strip("?")
    if simple and simple in classes_in_code:
        found_classes.add(c)
    elif c in classes_in_code:
        found_classes.add(c)

missing = [c for c in expected_classes if c not in found_classes]
covered_count = len(found_classes)
coverage_pct = (covered_count / total_expected) * 100.0

print(f"\n=======================================================================")
print(f"[RESULTADOS DA AUDITORIA]")
print(f"=======================================================================")
print(f"Classes Canônicas Cobertas:     {covered_count} / {total_expected} ({coverage_pct:.2f}%)")
print(f"Classes Canônicas Pendentes:    {len(missing)}")
print(f"Classes Falsas / Inexistentes: {len(fictitious_classes)} (detectadas no código fonte)")

if fictitious_classes:
    print(f"\n[ALERTA DE PURGA] Foram encontradas {len(fictitious_classes)} classes falsas no código fonte que não existem na Game.dll oficial:")
    for f in sorted(list(fictitious_classes))[:15]:
        print(f"  - [REMOVER]: {f}")
    if len(fictitious_classes) > 15:
        print(f"  ... e mais {len(fictitious_classes) - 15} classes falsas.")

if missing:
    print(f"\n[AMOSTRA DE CLASSES REAIS AUSENTES ({len(missing)})]:")
    for m in missing[:20]:
        print(f"  + [DESENVOLVER]: {m}")

print("=======================================================================")
if len(fictitious_classes) > 0 or coverage_pct < 100.0:
    print("[STATUS DO ROADMAP]: Projeto em desenvolvimento ativo para paridade de 31.8 MB.")
    sys.exit(0)
else:
    print("[STATUS]: 100% de paridade canônica alcançada!")
    sys.exit(0)
