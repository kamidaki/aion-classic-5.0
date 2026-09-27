"""
NPC Provider for Aion Assets.
Resolves NPC archetype names, mesh references, and world spawn locations.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.client_provider import AionClientProvider


class NPCProvider:
    """Provides NPC template lookups and world spawn coordinates."""

    def __init__(self, client_provider: AionClientProvider):
        self.client_prov = client_provider
        self._templates_cache: Dict[str, Dict[str, Any]] = {}

    def get_npc_template(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Looks up an NPC archetype template by its numeric string ID."""
        if not self._templates_cache:
            self._load_templates()
        return self._templates_cache.get(str(npc_id))

    def _load_templates(self) -> None:
        self._templates_cache = self.client_prov.get_npc_templates()
