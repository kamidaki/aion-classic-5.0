"""
Visual Effect (VFX) Operators for LostAcademy Aion Model Library.
Provides operators to apply, adjust, and remove magical auras, socket lights, and particle effects.
"""

from __future__ import annotations
import logging
from typing import Optional

import bpy

from ..providers.effect_provider import EffectProvider
from ..viewers.viewer_stage import ViewerStage

logger = logging.getLogger("AionModelLibrary.EffectOps")


def get_active_stage_model() -> Optional[bpy.types.Object]:
    """Returns the primary armature or mesh object in the viewer stage."""
    col = ViewerStage.get_or_create_stage_collection()
    # Check active object first
    act = bpy.context.active_object
    if act and act.name in col.objects:
        if act.type == "ARMATURE":
            return act
        if act.parent and act.parent.type == "ARMATURE":
            return act.parent
        return act

    # Otherwise return the first armature in stage
    for obj in col.objects:
        if obj.type == "ARMATURE":
            return obj
    for obj in col.objects:
        if obj.type == "MESH" and not obj.get("is_aion_vfx"):
            return obj
    return None


class AION_OT_apply_vfx(bpy.types.Operator):
    """Applies elemental visual effects (shader glow, socket lights, particle emitters) to the model."""
    bl_idname = "aion_model.apply_vfx"
    bl_label = "Aplicar Efeitos Visuais"
    bl_description = "Aplica auras mágicas elementais, emissão de brilho e luzes nos sockets do modelo ativo"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        root_obj = get_active_stage_model()
        if not root_obj:
            self.report({"WARNING"}, "Nenhum modelo carregado no palco para aplicar efeitos.")
            return {"CANCELLED"}

        ep = EffectProvider.get()
        ok = ep.apply_vfx(
            root_obj=root_obj,
            element=settings.vfx_element,
            intensity=settings.vfx_intensity,
            show_glow=settings.vfx_show_glow,
            show_lights=settings.vfx_show_lights,
            show_particles=settings.vfx_show_particles,
        )

        if ok:
            settings.enable_vfx = True
            self.report({"INFO"}, f"Efeito visual ({settings.vfx_element}) aplicado com sucesso.")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Falha ao aplicar efeitos visuais no modelo.")
            return {"CANCELLED"}


class AION_OT_remove_vfx(bpy.types.Operator):
    """Removes all visual effect lights, emitters, and shader glow from the model."""
    bl_idname = "aion_model.remove_vfx"
    bl_label = "Remover Efeitos Visuais"
    bl_description = "Remove todas as auras, luzes e partículas de efeito do modelo ativo"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        root_obj = get_active_stage_model()
        ep = EffectProvider.get()
        ep.remove_vfx(root_obj)
        settings.enable_vfx = False
        self.report({"INFO"}, "Efeitos visuais removidos.")
        return {"FINISHED"}


class AION_OT_toggle_vfx(bpy.types.Operator):
    """Toggles visual effects on or off for the loaded 3D model."""
    bl_idname = "aion_model.toggle_vfx"
    bl_label = "Alternar Efeitos Visuais"
    bl_description = "Ativa ou desativa a exibição de efeitos visuais mágicos"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if settings.enable_vfx:
            return bpy.ops.aion_model.apply_vfx()
        else:
            return bpy.ops.aion_model.remove_vfx()


CLASSES = (
    AION_OT_apply_vfx,
    AION_OT_remove_vfx,
    AION_OT_toggle_vfx,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
