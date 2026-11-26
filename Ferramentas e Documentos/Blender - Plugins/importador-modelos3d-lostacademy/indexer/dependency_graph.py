"""
Asset Dependency Graph for Aion Assets.
Maintains bidirectional relationships between NPCs, Models, Skeletons, Animations, Materials, and Textures.
Identifies affected assets on modifications (Dependency-Aware Save).
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set


class DependencyGraph:
    """Directed dependency graph with bidirectional querying."""

    def __init__(self):
        # A depends on B: _forward[A] = set of B
        self._forward: Dict[str, Set[str]] = {}
        # B is depended on by A: _reverse[B] = set of A
        self._reverse: Dict[str, Set[str]] = {}

    def add_dependency(self, source_id: str, target_id: str) -> None:
        """Declares that source_id depends on target_id."""
        if source_id == target_id:
            return
        if source_id not in self._forward:
            self._forward[source_id] = set()
        self._forward[source_id].add(target_id)

        if target_id not in self._reverse:
            self._reverse[target_id] = set()
        self._reverse[target_id].add(source_id)

    def get_dependencies(self, asset_id: str) -> List[str]:
        """Returns all assets that asset_id directly depends upon."""
        return sorted(list(self._forward.get(asset_id, set())))

    def get_dependents(self, asset_id: str) -> List[str]:
        """Returns all assets that depend on asset_id (affected if asset_id is modified)."""
        return sorted(list(self._reverse.get(asset_id, set())))

    def get_deep_dependents(self, asset_id: str) -> List[str]:
        """Recursively resolves all assets affected if asset_id changes."""
        visited: Set[str] = set()
        queue = [asset_id]
        while queue:
            curr = queue.pop(0)
            for dep in self._reverse.get(curr, set()):
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
        return sorted(list(visited))

    def clear(self) -> None:
        self._forward.clear()
        self._reverse.clear()
