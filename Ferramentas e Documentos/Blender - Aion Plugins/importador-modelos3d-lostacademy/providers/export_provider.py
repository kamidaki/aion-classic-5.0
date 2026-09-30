"""
Export Provider for Aion Assets.
Orchestrates saving modified models, armatures, animations, materials, and textures
back to the client files safely through the TransactionManager.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from ..core.transaction_manager import TransactionManager, TransactionResult
from ..core.change_tracker import ChangeTracker, TrackedAsset
from .model_provider import ModelProvider


class ExportProvider:
    """Manages transactional export of scene edits back into Aion client files."""

    def __init__(self, model_provider: ModelProvider, client_root: Path):
        self.model_prov = model_provider
        self.client_root = client_root
        self.change_tracker = ChangeTracker.get()

    def save_current_asset(
        self,
        root_obj: bpy.types.Object,
        entry: Any,
        allow_client_write: bool = False,
        export_fallback_dir: Optional[str | Path] = None,
    ) -> TransactionResult:
        """
        Serializes root_obj and commits changes transactionally to the client or export directory.
        """
        # 1. Serialize modified model
        new_cgf_bytes = self.model_prov.serialize_model(root_obj, entry)

        # 2. Package updates dictionary
        updates: Dict[str, bytes] = {
            entry.model_path: new_cgf_bytes,
        }

        # 3. Check for modified action (if rig has active action)
        if root_obj.type == "ARMATURE" and root_obj.animation_data and root_obj.animation_data.action:
            action = root_obj.animation_data.action
            if entry.idle_animation:
                b_names, b_pos, b_anim = self.model_prov.skel_prov.extract_armature(root_obj)
                new_caf_bytes = self.model_prov.anim_prov.serialize_action(
                    rig_obj=root_obj,
                    action=action,
                    bone_names=b_names,
                    bone_anim=b_anim,
                )
                if new_caf_bytes:
                    updates[entry.idle_animation] = new_caf_bytes

        # 4. Execute safe transaction
        result = TransactionManager.save_assets(
            client_root=self.client_root,
            asset_updates=updates,
            allow_client_write=allow_client_write,
            export_fallback_dir=export_fallback_dir,
            create_backups=True,
        )

        if result.success:
            # Commit change in change tracker
            tracked = self.change_tracker.get_tracked(entry.asset_id)
            if tracked:
                tracked.commit()
            entry.is_modified = False

        return result
