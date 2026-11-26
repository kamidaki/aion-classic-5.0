"""
Animation Transport & Switching Operators for LostAcademy Aion Model Library.
Handles playback, stop, pause, and switching active animations from the CAL sequence list.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import bpy
from bpy.props import IntProperty, StringProperty

from ..viewers.animation_player import AnimationPlayer
from ..viewers.viewer_stage import ViewerStage
from .library_ops import get_client_provider, get_model_provider

logger = logging.getLogger(__name__)


class AION_OT_play_animation(bpy.types.Operator):
    """Starts or pauses playback of the active animation."""
    bl_idname = "aion_model.play_animation"
    bl_label = "Reproduzir / Pausar"
    bl_description = "Alternar reprodução da animação"
    bl_options = {"INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        if AnimationPlayer.is_playing():
            AnimationPlayer.pause()
        else:
            AnimationPlayer.play()
        return {"FINISHED"}


class AION_OT_stop_animation(bpy.types.Operator):
    """Stops playback and rewinds to the first frame."""
    bl_idname = "aion_model.stop_animation"
    bl_label = "Parar"
    bl_description = "Parar reprodução e voltar ao início"
    bl_options = {"INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        rig_obj = None
        if context.active_object and context.active_object.type == "ARMATURE":
            rig_obj = context.active_object
        else:
            stage_col = ViewerStage.get_or_create_stage_collection()
            for o in stage_col.objects:
                if o.type == "ARMATURE":
                    rig_obj = o
                    break
        AnimationPlayer.stop(rig_obj)
        return {"FINISHED"}


def _find_caf_bytes(client_prov, caf_rel_path: str, source_model_path: str = "") -> Optional[bytes]:
    """Resolve CAF bytes using client provider's find_caf_bytes with fallback."""
    if hasattr(client_prov, "find_caf_bytes"):
        return client_prov.find_caf_bytes(caf_rel_path, source_model_path=source_model_path)

    catalog = client_prov.catalog
    data = catalog.extract_file(caf_rel_path)
    if data:
        return data
    caf_name = Path(caf_rel_path).name
    data = catalog.extract_file(caf_name)
    if data:
        return data
    return None


class AION_OT_switch_animation(bpy.types.Operator):
    """Switches the active animation on the loaded model armature."""
    bl_idname = "aion_model.switch_animation"
    bl_label = "Trocar Animação"
    bl_description = "Carregar sequência de animação selecionada no esqueleto do modelo"
    bl_options = {"REGISTER", "UNDO"}

    anim_index: IntProperty(name="Índice da Animação", default=0)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.active_anims:
            self.report({"WARNING"}, "Nenhuma animação disponível para este modelo.")
            return {"CANCELLED"}

        idx = self.anim_index
        if idx < 0 or idx >= len(settings.active_anims):
            idx = settings.active_anim_index

        if idx < 0 or idx >= len(settings.active_anims):
            return {"CANCELLED"}

        selected_anim = settings.active_anims[idx]
        caf_rel = selected_anim.caf_path
        anim_name = selected_anim.name

        # Find loaded armature
        rig_obj = None
        if context.active_object and context.active_object.type == "ARMATURE":
            rig_obj = context.active_object
        else:
            stage_col = ViewerStage.get_or_create_stage_collection()
            for o in stage_col.objects:
                if o.type == "ARMATURE":
                    rig_obj = o
                    break

        if not rig_obj:
            self.report({"ERROR"}, "Nenhum esqueleto ativo encontrado no palco para aplicar a animação.")
            return {"CANCELLED"}

        client_prov = get_client_provider(settings.client_path)
        model_prov = get_model_provider(settings.client_path)
        if not client_prov or not model_prov:
            self.report({"ERROR"}, "Provedor do cliente não disponível.")
            return {"CANCELLED"}

        # Extract CAF bytes using robust multi-strategy resolver
        source_model = getattr(settings, "active_model_path", "") or getattr(settings, "active_asset_path", "")
        caf_bytes = _find_caf_bytes(client_prov, caf_rel, source_model_path=source_model)

        if not caf_bytes:
            self.report({"ERROR"}, f"Arquivo de animação CAF '{caf_rel}' não encontrado nos PAKs do cliente.")
            return {"CANCELLED"}

        # Extract bone info from armature
        b_names, b_pos, b_anim = model_prov.skel_prov.extract_armature(rig_obj)

        action = model_prov.anim_prov.load_animation(
            rig_obj=rig_obj,
            caf_bytes=caf_bytes,
            action_name=f"{settings.active_asset_name}_{anim_name}",
            bone_names=b_names,
            bone_anim=b_anim,
        )

        if not action:
            self.report({"ERROR"}, f"Falha ao carregar dados de animação para {anim_name}.")
            return {"CANCELLED"}

        # Adjust timeline
        start = int(action.frame_range[0])
        end = int(action.frame_range[1])
        AnimationPlayer.set_frame_range(start, end)
        settings.active_anim_index = idx

        # Start playback
        AnimationPlayer.play()
        self.report({"INFO"}, f"Reproduzindo animação '{anim_name}' ({end - start + 1} quadros)")
        return {"FINISHED"}


CLASSES = (
    AION_OT_play_animation,
    AION_OT_stop_animation,
    AION_OT_switch_animation,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
