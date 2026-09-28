"""
Test Suite for LostAcademy Aion Model Library Indexer & Search.
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

for mod_name in list(sys.modules.keys()):
    if any(mod_name.startswith(p) or mod_name == p for p in ("config", "core", "formats", "indexer", "providers", "viewers", "editors")):
        del sys.modules[mod_name]

from indexer.asset_database import AssetDatabase
from indexer.thumbnail_generator import ensure_asset_thumbnail

CLIENT_PATH = Path("D:/GameForge/aionclassic")


def run_indexer_test():
    print("=" * 70)
    print("TESTING AION MODEL LIBRARY INDEXER")
    print(f"Client Root: {CLIENT_PATH}")
    print("=" * 70)

    if not CLIENT_PATH.is_dir():
        print("SKIP: Client path not found.")
        return

    db = AssetDatabase.get()
    t0 = time.time()
    count = db.scan_client(CLIENT_PATH, max_assets=500)
    duration = time.time() - t0
    print(f"Scanned {count} assets in {duration:.3f}s!")
    assert count > 50, f"Expected >50 assets, found {count}"

    # Test Categories
    cats = db.get_category_counts()
    print("Category breakdown:")
    for cat, c_count in cats.items():
        if c_count > 0:
            print(f"  [{cat}]: {c_count}")

    # Test Search
    print("\n--- Search Tests ---")
    res_shugo = db.search(query="shugo")
    print(f"Search 'shugo': {len(res_shugo)} results")
    assert len(res_shugo) > 0, "Expected at least 1 Shugo result!"
    first_shugo = res_shugo[0]
    print(f"Sample Result: ID={first_shugo.asset_id}, Name={first_shugo.name}, Model={first_shugo.model_path}, HasSkel={first_shugo.has_skeleton}, Anims={first_shugo.animation_count}")

    # Test Thumbnail Generation
    thumb_path = ensure_asset_thumbnail(CLIENT_PATH, first_shugo)
    assert Path(thumb_path).is_file(), f"Thumbnail not created at {thumb_path}"
    print(f"Thumbnail created: {thumb_path} ({Path(thumb_path).stat().st_size} bytes)")

    # Test Cache Saving & Reloading
    print("\n--- Cache Persistence Tests ---")
    assert db.save_cache(CLIENT_PATH) is True, "Failed to save index cache!"
    db.clear()
    assert db.total_count == 0
    assert db.load_cache(CLIENT_PATH) is True, "Failed to load index cache!"
    assert db.total_count == count, f"Cache reload mismatch: {db.total_count} vs {count}"
    print(f"PASS: Index cache successfully saved and reloaded ({db.total_count} assets).")

    print("\n" + "=" * 70)
    print("INDEXER UNIT TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_indexer_test()
