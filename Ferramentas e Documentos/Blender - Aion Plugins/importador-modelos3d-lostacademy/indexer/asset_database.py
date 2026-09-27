"""
High-Performance In-Memory and Disk-Cached Asset Database.
Provides fast O(1) lookups, sub-millisecond full-text search, and category filtering across tens of thousands of assets.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from config.settings import INDEX_CACHE_FILENAME
except ImportError:
    from ..config.settings import INDEX_CACHE_FILENAME

from .asset_entry import AssetEntry
from .dependency_graph import DependencyGraph
from .scanner import ClientScanner


class AssetDatabase:
    """Singleton in-memory asset database."""

    _instance: Optional["AssetDatabase"] = None

    def __init__(self):
        self._entries: Dict[str, AssetEntry] = {}  # asset_id -> AssetEntry
        self._path_to_id: Dict[str, str] = {}  # model_path_lower -> asset_id
        self._category_index: Dict[str, List[str]] = {}  # category -> [asset_ids]
        self._dep_graph = DependencyGraph()
        self.client_root: Optional[Path] = None
        self.is_loaded: bool = False
        self.last_scan_time: float = 0.0

    @classmethod
    def get(cls) -> "AssetDatabase":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def total_count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._path_to_id.clear()
        self._category_index.clear()
        self._dep_graph.clear()
        self.is_loaded = False

    def add_entry(self, entry: AssetEntry) -> None:
        self._entries[entry.asset_id] = entry
        clean_path = entry.model_path.lower().replace("\\", "/")
        self._path_to_id[clean_path] = entry.asset_id
        stem = Path(clean_path).stem
        self._path_to_id[stem] = entry.asset_id

        cat = entry.category
        if cat not in self._category_index:
            self._category_index[cat] = []
        self._category_index[cat].append(entry.asset_id)

    @property
    def all_assets(self) -> List[AssetEntry]:
        return list(self._entries.values())

    def load_from_entries(self, entries: List[AssetEntry]) -> None:
        self.clear()
        for e in entries:
            self.add_entry(e)
        self.is_loaded = True

    def get_categories(self) -> List[str]:
        return list(self._category_index.keys())

    def get_by_id(self, asset_id: str) -> Optional[AssetEntry]:
        return self._entries.get(asset_id)

    def get_by_path(self, model_path: str) -> Optional[AssetEntry]:
        clean = model_path.lower().replace("\\", "/").strip().lstrip("/")
        aid = self._path_to_id.get(clean) or self._path_to_id.get(Path(clean).stem)
        return self._entries.get(aid) if aid else None

    def search(
        self,
        query: str = "",
        category: str = "ALL",
        has_skeleton: Optional[bool] = None,
        min_animations: int = 0,
        limit: int = 200,
    ) -> List[AssetEntry]:
        """
        Fast multi-predicate search across all indexed assets.
        Query matches name, ID, model path, and animation state tags.
        """
        clean_q = (query or "").strip().lower()
        tokens = clean_q.split() if clean_q else []

        # Candidate pool based on category
        if category and category != "ALL":
            candidate_ids = self._category_index.get(category, [])
            candidates = [self._entries[cid] for cid in candidate_ids if cid in self._entries]
        else:
            candidates = list(self._entries.values())

        results: List[AssetEntry] = []

        for entry in candidates:
            # Filter 1: Skeleton
            if has_skeleton is not None and entry.has_skeleton != has_skeleton:
                continue

            # Filter 2: Animation count
            if min_animations > 0 and entry.animation_count < min_animations:
                continue

            # Filter 3: Query tokens
            if tokens:
                search_str = entry.search_string
                if not all(t in search_str for t in tokens):
                    continue

            results.append(entry)
            if len(results) >= limit:
                break

        return results

    def get_category_counts(self) -> Dict[str, int]:
        """Returns the distribution of assets across categories."""
        counts = {"ALL": len(self._entries)}
        for cat, ids in self._category_index.items():
            counts[cat] = len(ids)
        return counts

    def get_cache_file(self, client_root: Path) -> Path:
        return client_root / INDEX_CACHE_FILENAME

    def save_cache(self, client_root: Path) -> bool:
        """Serializes current index to disk cache for fast reloading."""
        try:
            cache_file = self.get_cache_file(client_root)
            data = {
                "version": 1,
                "timestamp": time.time(),
                "client_root": str(client_root),
                "total_entries": len(self._entries),
                "entries": [e.to_dict() for e in self._entries.values()],
            }
            cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def load_cache(self, client_root: Path) -> bool:
        """Loads index from disk cache if valid."""
        cache_file = self.get_cache_file(client_root)
        if not cache_file.is_file():
            return False

        try:
            content = json.loads(cache_file.read_text(encoding="utf-8"))
            entries = content.get("entries", [])
            self.clear()
            self.client_root = client_root

            for ed in entries:
                entry = AssetEntry.from_dict(ed)
                self.add_entry(entry)

            self.is_loaded = True
            self.last_scan_time = content.get("timestamp", time.time())
            return True
        except Exception:
            return False

    def scan_client(self, client_root: Path, max_assets: Optional[int] = None) -> int:
        """Scans the client and populates the database."""
        self.clear()
        self.client_root = client_root
        scanner = ClientScanner(client_root)
        assets, dep_graph = scanner.scan(max_assets=max_assets)

        for a in assets:
            self.add_entry(a)

        self._dep_graph = dep_graph
        self.is_loaded = True
        self.last_scan_time = time.time()
        self.save_cache(client_root)
        return len(self._entries)
