"""
Client Asset Coverage Audit Script for LostAcademy Aion Model Library.

Run headless::

    blender -b --python validation/audit_client_coverage.py

Generates a coverage report of all CGF/CGA/CAF/CAL assets in the Aion client
by sampling the first 20 PAK files inside ``objects/`` and parsing up to
5 CGF/CGA entries per archive.
"""
import os
import sys
import io
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrapping — makes the addon importable in headless mode
# ---------------------------------------------------------------------------
_PLUGIN_DIR = Path(__file__).resolve().parents[1]
_ADDONS_ROOT = _PLUGIN_DIR.parent
for _p in [str(_ADDONS_ROOT), str(_PLUGIN_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402 – available in headless Blender
import addon_utils  # noqa: E402

ADDON_NAME = "importador-modelos3d-lostacademy"
addon_utils.enable(ADDON_NAME)

import importlib  # noqa: E402

_pkg = ADDON_NAME
pe = importlib.import_module(f"{_pkg}.core.pak_engine")
parser = importlib.import_module(f"{_pkg}.formats.cgf.parser")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_env_client = os.environ.get("AION_CLIENT_ROOT", "").strip()
if not _env_client or not Path(_env_client).is_dir():
    print("SKIP: Set AION_CLIENT_ROOT to your Aion client directory before running this audit.")
    sys.exit(0)
CLIENT_ROOT = Path(_env_client)

# Limits — increase for a full audit (will be slower)
MAX_PAKS = 20        # number of PAK files to sample
MAX_PER_PAK = 5      # number of CGF/CGA entries to parse per PAK

# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
print("=" * 80)
print("AION ASSET COVERAGE AUDIT")
print(f"Client root : {CLIENT_ROOT}")
print(f"Sampling    : first {MAX_PAKS} PAKs × {MAX_PER_PAK} CGF entries")
print("=" * 80)

all_paks = list(CLIENT_ROOT.glob("objects/**/*.pak"))
print(f"\nFound {len(all_paks)} PAK file(s) in objects/")

total_cgf = 0
parsed_cgf = 0
skinned_cgf = 0
failed_cgf = 0
error_types: dict = {}

for pak_path in all_paks[:MAX_PAKS]:
    try:
        arc = pe.AionPakArchive(pak_path)
        cgf_names = [n for n in arc.entries if n.endswith((".cgf", ".cga"))]
        total_cgf += len(cgf_names)

        for name in cgf_names[:MAX_PER_PAK]:
            try:
                data = arc.read_file(name)
                if data:
                    parsed = parser.get_cgf(io.BytesIO(data))
                    if parsed and parsed.get("nodes"):
                        parsed_cgf += 1
                        if parsed.get("bone_names"):
                            skinned_cgf += 1
                    else:
                        failed_cgf += 1
                        error_types["empty_nodes"] = error_types.get("empty_nodes", 0) + 1
            except Exception as exc:
                failed_cgf += 1
                err_key = type(exc).__name__
                error_types[err_key] = error_types.get(err_key, 0) + 1
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print(f"\nCGF/CGA files found (sampled) : {total_cgf}")
print(f"Successfully parsed            : {parsed_cgf}")
print(f"  With skeleton/skin data      : {skinned_cgf}")
print(f"Parse failures                 : {failed_cgf}")

if error_types:
    print("\nError type breakdown:")
    for err, count in sorted(error_types.items(), key=lambda x: -x[1]):
        print(f"  {err:40s} : {count}")

total_attempted = parsed_cgf + failed_cgf
if total_attempted > 0:
    coverage_pct = 100.0 * parsed_cgf / total_attempted
    print(f"\nParse coverage : {coverage_pct:.1f}%")
else:
    print("\nNo CGF/CGA entries were attempted.")

print("=" * 80)
