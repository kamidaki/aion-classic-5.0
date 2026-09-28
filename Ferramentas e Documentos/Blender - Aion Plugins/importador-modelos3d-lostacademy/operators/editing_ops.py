"""
Editing Operators for LostAcademy Aion Model Library.
Handles switching to Mesh Edit Mode, Sculpt Mode, Bone Edit Mode, adding bones, UV unwrapping, and normals.
"""

from __future__ import annotations
import bpy
from bpy.props import StringProperty, FloatVectorProperty

from ..core.change_tracker import ChangeTracker
from ..editors.mesh_editor import MeshEditor
from ..editors.skeleton_editor import SkeletonEditor
from ..editors.uv_editor import UVEditor


def get_active_mesh(context: bpy.types.Context) -> bpy.types.Object | None:
    """Finds the active mesh or the first mesh child of the active armature."""
    obj = context.active_object
    if not obj:
        return None
    if obj.type == "MESH":
        return obj
    if obj.type == "ARMATURE":
        for child in obj.children:
            if child.type == "MESH":
                return child
    return None


def get_active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Finds the active armature or the parent armature of the active mesh."""
    obj = context.active_object
    if not obj:
        return None
    if obj.type == "ARMATURE":
        return obj
    if obj.type == "MESH" and obj.parent and obj.parent.type == "ARMATURE":
        return obj.parent
    return None


class AION_OT_edit_mesh(bpy.types.Operator):
    """Enters Blender Edit Mode for the active model mesh."""
    bl_idname = "aion_model.edit_mesh"
    bl_label = "Editar Malha"
    bl_description = "Alternar para Modo de Edição para modificar vértices, arestas e faces"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        mesh_obj = get_active_mesh(context)
        if not mesh_obj:
            self.report({"WARNING"}, "Nenhum objeto de malha selecionado.")
            return {"CANCELLED"}

        MeshEditor.enter_edit_mode(mesh_obj)
        context.scene.aion_model_lib.active_is_modified = True
        return {"FINISHED"}


class AION_OT_sculpt_mesh(bpy.types.Operator):
    """Enters Sculpt Mode for high-resolution organic mesh deformation."""
    bl_idname = "aion_model.sculpt_mesh"
    bl_label = "Esculpir Malha"
    bl_description = "Alternar para Modo de Escultura para modelagem orgânica"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        mesh_obj = get_active_mesh(context)
        if not mesh_obj:
            self.report({"WARNING"}, "Nenhum objeto de malha selecionado.")
            return {"CANCELLED"}

        MeshEditor.enter_sculpt_mode(mesh_obj)
        context.scene.aion_model_lib.active_is_modified = True
        return {"FINISHED"}


class AION_OT_recalc_normals(bpy.types.Operator):
    """Recalculates outside face and vertex normals."""
    bl_idname = "aion_model.recalc_normals"
    bl_label = "Recalcular Normais"
    bl_description = "Garantir que todas as normais das faces apontem consistentemente para fora"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        mesh_obj = get_active_mesh(context)
        if not mesh_obj:
            self.report({"WARNING"}, "Nenhum objeto de malha selecionado.")
            return {"CANCELLED"}

        MeshEditor.recalculate_normals(mesh_obj)
        context.scene.aion_model_lib.active_is_modified = True
        self.report({"INFO"}, "Normais das faces recalculadas para fora.")
        return {"FINISHED"}


class AION_OT_edit_bones(bpy.types.Operator):
    """Enters Armature Edit Mode to reposition or reparent bones."""
    bl_idname = "aion_model.edit_bones"
    bl_label = "Editar Esqueleto"
    bl_description = "Entrar no Modo de Edição de ossos no esqueleto do modelo"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        arm_obj = get_active_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "Nenhum esqueleto encontrado no modelo selecionado.")
            return {"CANCELLED"}

        SkeletonEditor.enter_bone_edit_mode(arm_obj)
        context.scene.aion_model_lib.active_is_modified = True
        return {"FINISHED"}


class AION_OT_add_bone(bpy.types.Operator):
    """Adds a new bone to the model armature."""
    bl_idname = "aion_model.add_bone"
    bl_label = "Adicionar Osso"
    bl_description = "Criar e anexar um novo osso à hierarquia do esqueleto"
    bl_options = {"REGISTER", "UNDO"}

    bone_name: StringProperty(name="Nome do Osso", default="Bip01 Custom")
    parent_bone: StringProperty(name="Osso Pai", default="")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        arm_obj = get_active_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "Nenhum esqueleto encontrado para adicionar o osso.")
            return {"CANCELLED"}

        actual_name = SkeletonEditor.add_bone(
            arm_obj=arm_obj,
            bone_name=self.bone_name.strip(),
            head_pos=(0.0, 0.0, 1.5),
            tail_pos=(0.0, 0.0, 1.8),
            parent_name=self.parent_bone.strip() if self.parent_bone else None,
        )

        if actual_name:
            context.scene.aion_model_lib.active_is_modified = True
            context.scene.aion_model_lib.active_bone_count = len(arm_obj.data.bones)
            self.report({"INFO"}, f"Osso '{actual_name}' adicionado com sucesso.")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Falha ao adicionar osso.")
            return {"CANCELLED"}


class AION_OT_unwrap_uv(bpy.types.Operator):
    """Unwraps UVs of the active mesh."""
    bl_idname = "aion_model.unwrap_uv"
    bl_label = "Desembrulhar UV"
    bl_description = "Desembrulhar mapeamento UV com projeção baseada em ângulos"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        mesh_obj = get_active_mesh(context)
        if not mesh_obj:
            self.report({"WARNING"}, "Nenhum objeto de malha selecionado.")
            return {"CANCELLED"}

        UVEditor.unwrap_mesh(mesh_obj)
        context.scene.aion_model_lib.active_is_modified = True
        self.report({"INFO"}, "UVs da malha desembrulhadas.")
        return {"FINISHED"}


class AION_OT_pack_uv(bpy.types.Operator):
    """Packs UV islands within the 0..1 coordinate boundary."""
    bl_idname = "aion_model.pack_uv"
    bl_label = "Organizar Ilhas UV"
    bl_description = "Organizar e empacotar ilhas UV dentro do espaço UV 0..1"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        mesh_obj = get_active_mesh(context)
        if not mesh_obj:
            self.report({"WARNING"}, "Nenhum objeto de malha selecionado.")
            return {"CANCELLED"}

        UVEditor.pack_islands(mesh_obj)
        context.scene.aion_model_lib.active_is_modified = True
        self.report({"INFO"}, "Ilhas UV organizadas.")
        return {"FINISHED"}


CLASSES = (
    AION_OT_edit_mesh,
    AION_OT_sculpt_mesh,
    AION_OT_recalc_normals,
    AION_OT_edit_bones,
    AION_OT_add_bone,
    AION_OT_unwrap_uv,
    AION_OT_pack_uv,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
