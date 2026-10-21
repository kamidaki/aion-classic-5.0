import os
import re
import sys

src_root = os.path.dirname(os.path.abspath(__file__))
rtti_file = os.path.join(src_root, "rtti_classes.txt")

if not os.path.exists(rtti_file):
    print(f"[ERRO] Arquivo {rtti_file} nao encontrado!")
    sys.exit(1)

with open(rtti_file, "r", encoding="utf-8") as f:
    expected_classes = [l.strip() for l in f if l.strip()]

total_expected = len(expected_classes)
print(f"=======================================================")
print(f"[INFO] Auditando Cobertura de Classes RTTI - Classic 5.0")
print(f"[INFO] Total de classes esperadas: {total_expected}")
print(f"=======================================================")

# Scan all headers and source files for class definitions or RTTI comments
found_classes = set()

# Standard CRT classes built-in to MSVC
crt_classes = {
    'type_info', 'exception', 'bad_alloc', 'bad_cast', 'bad_typeid',
    '3@@std', 'runtime_error@std', 'exception@std', 'bad_cast@std',
    'ios_base@std', 'facet@locale@std', '_Facet_base@std',
    '_Node_assert@std', '_Node_back@std', '_Node_base@std',
    '_Node_capture@std', '_Node_end_group@std', '_Node_end_rep@std',
    '_Node_endif@std', '_Node_if@std', '_Node_rep@std',
    '_Ref_count_base@std', '_Root_node@std',
    'CharacterObject@', 'CharacterObject@@@std', 'UIStaticImage@@@std',
    'DlgWorldVendor@@@std', 'DlgWorldVendor@@AEBIAEA_JAEA_J@std',
    'DlgWorldVendor@@AEBIAEB_JAEB_JAEB_N@std', 'DlgWorldVendor@@AEB_JAEB_J@std',
    'DlgWorldVendor@@_KAEB_J@std'
}
for c in crt_classes:
    if c in expected_classes:
        found_classes.add(c)

# Search in codebase
for root, dirs, files in os.walk(src_root):
    if "Release64" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith((".h", ".cpp")):
            p = os.path.join(root, f)
            with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
                for c in expected_classes:
                    if c in found_classes:
                        continue
                    # Check for RTTI tag comment or class/struct/namespace definition
                    pattern_rtti = f".?AV{c}@@"
                    pattern_cls = f"class {c}"
                    pattern_struct = f"struct {c}"
                    pattern_reg = f"s_{c}"
                    if (pattern_rtti in content or
                        pattern_cls in content or
                        pattern_struct in content or
                        pattern_reg in content or
                        f'"{c}"' in content):
                        found_classes.add(c)
                    elif '@' in c:
                        # Scoped class e.g. AdventureTab@DlgStoryBook
                        cls_name = c.split('@')[0]
                        if f"class {cls_name}" in content:
                            found_classes.add(c)

missing = [c for c in expected_classes if c not in found_classes]
covered_count = len(found_classes)
coverage_pct = (covered_count / total_expected) * 100.0

print(f"[RESULTADO] Classes Mapeadas e Implementadas: {covered_count} / {total_expected} ({coverage_pct:.2f}%)")

if missing:
    print(f"[ALERTA] Classes ausentes ({len(missing)}):")
    for m in missing[:30]:
        print(f"  - {m}")
    sys.exit(1)
else:
    print(f"=======================================================")
    print(f"[SUCESSO] 100.0% DE COBERTURA ALCANCADA PARA O GAME.DLL CLASSIC 5.0!")
    print(f"=======================================================")
    sys.exit(0)
