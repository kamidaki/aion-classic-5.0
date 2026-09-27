"""
Viewer and Viewport Operators for LostAcademy Aion Model Library.
Handles camera framing, standard projection views, shading modes, and bone visibility.
"""

from __future__ import annotations
import bpy
from bpy.props import StringProperty

from ..viewers.viewport_controls import view_preset_axis, toggle_persp_ortho, reset_view
from ..viewers.display_modes import set_shading_mode, set_bones_display, toggle_wireframe_overlay
from ..viewers.viewer_stage import ViewerStage


class AION_OT_set_camera_view(bpy.types.Operator):
    """Sets the viewport camera to a standard axis or resets the view."""
    bl_idname = "aion_model.set_camera_view"
    bl_label = "Set Camera View"
    bl_description = "Switch 3D Viewport orientation"
    bl_options = {"INTERNAL"}

    axis: StringProperty(name="Axis", default="FRONT")

    def execute(self, context: bpy.types.Context) -> set[str]:
        ax = self.axis.upper()
        if ax in ("FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"):
            view_preset_axis(ax)
        elif ax == "PERSP_ORTHO":
            toggle_persp_ortho()
        elif ax == "RESET":
            reset_view()
        return {"FINISHED"}


class AION_OT_focus_model(bpy.types.Operator):
    """Focuses and frames the 3D viewport camera on the active model."""
    bl_idname = "aion_model.focus_model"
    bl_label = "Focus Model"
    bl_description = "Frame active model in 3D viewport"
    bl_options = {"INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        target = context.active_object
        if not target:
            # Fallback to any object in viewer stage
            stage_col = ViewerStage.get_or_create_stage_collection()
            non_lights = [o for o in stage_col.objects if o.type not in ("LIGHT", "CAMERA")]
            if non_lights:
                target = non_lights[0]

        if target:
            ViewerStage.frame_object(target)
            return {"FINISHED"}
        else:
            self.report({"INFO"}, "No model in viewer to focus.")
            return {"CANCELLED"}


class AION_OT_set_shading(bpy.types.Operator):
    """Switches 3D Viewport shading mode (Wireframe, Solid, Material, Rendered)."""
    bl_idname = "aion_model.set_shading"
    bl_label = "Set Shading Mode"
    bl_description = "Set viewport shading method"
    bl_options = {"INTERNAL"}

    mode: StringProperty(name="Mode", default="MATERIAL")

    def execute(self, context: bpy.types.Context) -> set[str]:
        set_shading_mode(self.mode)
        return {"FINISHED"}


class AION_OT_toggle_bones(bpy.types.Operator):
    """Toggles bone visibility in 3D viewport."""
    bl_idname = "aion_model.toggle_bones"
    bl_label = "Toggle Bones"
    bl_description = "Show or hide armature bones"
    bl_options = {"INTERNAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        settings.show_armature = not settings.show_armature

        # Find active or stage armature
        target_arm = None
        if context.active_object and context.active_object.type == "ARMATURE":
            target_arm = context.active_object
        else:
            stage_col = ViewerStage.get_or_create_stage_collection()
            for o in stage_col.objects:
                if o.type == "ARMATURE":
                    target_arm = o
                    break

        if target_arm:
            set_bones_display(
                target_arm,
                show_bones=settings.show_armature,
                in_front=True,
            )

        return {"FINISHED"}


CLASSES = (
    AION_OT_set_camera_view,
    AION_OT_focus_model,
    AION_OT_set_shading,
    AION_OT_toggle_bones,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
