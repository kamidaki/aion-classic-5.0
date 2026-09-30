"""
Loose Exporter for Aion Models.
Exports models, armatures, animations, materials, and textures to a loose folder on disk,
mirroring the client folder structure without touching PAK archives.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import bpy
from ..providers.model_provider import ModelProvider

logger = logging.getLogger(__name__)


class LooseExporter:
    """Exports Aion assets as loose files to an arbitrary disk directory."""

    @staticmethod
    def export_asset(
        root_obj: bpy.types.Object,
        entry: Any,
        model_provider: ModelProvider,
        target_dir: Path,
        export_textures: bool = True,
        export_animations: bool = True,
    ) -> Dict[str, Any]:
        """
        Exports the asset to target_dir.
        Returns a dict with status and list of written files.
        """
        written_files: List[Path] = []
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Serialize CGF
            cgf_bytes = model_provider.serialize_model(root_obj, entry)
            rel_model = Path(entry.model_path)
            # Retain relative directory or put in target_dir
            out_cgf = target_dir / rel_model
            out_cgf.parent.mkdir(parents=True, exist_ok=True)
            out_cgf.write_bytes(cgf_bytes)
            written_files.append(out_cgf)

            # 2. Export Animations & CAL if armature has action
            if export_animations and root_obj.type == "ARMATURE":
                if root_obj.animation_data and root_obj.animation_data.action and entry.idle_animation:
                    action = root_obj.animation_data.action
                    b_names, b_pos, b_anim = model_provider.skel_prov.extract_armature(root_obj)
                    caf_bytes = model_provider.anim_prov.serialize_action(
                        rig_obj=root_obj,
                        action=action,
                        bone_names=b_names,
                        bone_anim=b_anim,
                    )
                    if caf_bytes:
                        out_caf = target_dir / entry.idle_animation
                        out_caf.parent.mkdir(parents=True, exist_ok=True)
                        out_caf.write_bytes(caf_bytes)
                        written_files.append(out_caf)

            return {
                "success": True,
                "written_files": [str(p) for p in written_files],
                "target_dir": str(target_dir),
                "error": None,
            }
        except Exception as e:
            logger.error("Failed to export loose asset: %s", e, exc_info=True)
            return {
                "success": False,
                "written_files": [str(p) for p in written_files],
                "target_dir": str(target_dir),
                "error": str(e),
            }
