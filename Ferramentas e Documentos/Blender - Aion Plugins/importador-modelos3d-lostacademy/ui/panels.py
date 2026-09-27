"""
User Interface Panels for LostAcademy Aion Model Library.
Provides an integrated 3D Viewport Sidebar (N-Panel) for asset browsing, staging,
editing, animation playback, and safe transactional saving.
"""

from __future__ import annotations
import bpy

PANEL_CATEGORY = "Aion Models"


class AION_UL_asset_list(bpy.types.UIList):
    """Custom UIList rendering of scanned Aion model library assets."""

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        icon: int,
        active_data: bpy.types.AnyType,
        active_propname: str,
        index: int = 0,
        flt_flag: int = 0,
    ) -> None:
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)

            # Modified status icon
            if item.is_modified:
                row.label(text="", icon="MODIFIER")

            # Icon based on category
            cat_icons = {
                "NPC": "COMMUNITY",
                "MONSTER": "GHOST_ENABLED",
                "CHARACTER": "USER",
                "WEAPON": "OUTLINER_OB_FORCE_FIELD",
                "ARMOR": "MOD_CLOTH",
                "WINGS": "PARTICLES",
                "PET_MOUNT": "OUTLINER_OB_ARMATURE",
                "BUILDING": "HOME",
                "PROP": "OBJECT_DATA",
                "VEGETATION": "OUTLINER_DATA_POINTCLOUD",
                "OBJECT": "MESH_CUBE",
                "EFFECT": "LIGHT_SUN",
            }
            ic = cat_icons.get(item.category, "MESH_DATA")

            row.label(text=item.name, icon=ic)

            # Details columns
            sub = row.row(align=True)
            sub.alignment = "RIGHT"
            if item.bone_count > 0:
                sub.label(text=f"{item.bone_count}b", icon="BONE_DATA")
            if item.anim_count > 0:
                sub.label(text=f"{item.anim_count}a", icon="ACTION")
            sub.label(text=f"{item.poly_count}p")

        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text=item.name, icon="MESH_DATA")


class AION_PT_client_header(bpy.types.Panel):
    """Client configuration and safety switch panel."""
    bl_label = "Aion Client Setup"
    bl_idname = "AION_PT_client_header"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Client Directory
        col = layout.column(align=True)
        col.prop(settings, "client_path")
        row = col.row(align=True)
        row.operator("aion_model.detect_client", icon="VIEWZOOM")
        row.label(text=f"Flavor: {settings.client_flavor}")

        # Scan Button
        box = layout.box()
        row = box.row(align=True)
        scan_label = "Scan Client Assets" if settings.scanned_total_count == 0 else f"Rescan ({settings.scanned_total_count})"
        row.operator("aion_model.scan_assets", text=scan_label, icon="FILE_REFRESH")

        # Safety Write Toggle
        safety_box = layout.box()
        safety_box.prop(settings, "allow_client_write", icon="ERROR" if settings.allow_client_write else "LOCKED")
        if settings.allow_client_write:
            w_box = safety_box.box()
            w_box.alert = True
            w_box.label(text="CAUTION: Live Client Write ENABLED!", icon="CANCEL")
            w_box.label(text="Edits will modify official game files/PAKs.")
            safety_box.prop(settings, "auto_backup")
        else:
            safety_box.label(text="Safe Mode: Direct client writing disabled", icon="CHECKMARK")
            safety_box.prop(settings, "export_fallback_dir")


class AION_PT_asset_browser(bpy.types.Panel):
    """Asset library browser with search and filtering."""
    bl_label = "Model Library"
    bl_idname = "AION_PT_asset_browser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Search & Filter
        col = layout.column(align=True)
        col.prop(settings, "category_filter", text="")
        col.prop(settings, "search_query", text="", icon="VIEWZOOM")

        # UI List
        row = layout.row()
        row.template_list(
            "AION_UL_asset_list",
            "aion_asset_list",
            settings,
            "asset_items",
            settings,
            "active_asset_index",
            rows=6,
        )

        # Action buttons
        btn_row = layout.row(align=True)
        btn_row.scale_y = 1.3
        btn_row.operator("aion_model.load_asset", text="Load in Viewer", icon="RESTRICT_VIEW_OFF")
        btn_row.operator("aion_model.clear_stage", text="Clear", icon="TRASH")


class AION_PT_asset_details(bpy.types.Panel):
    """Metadata details of the loaded asset."""
    bl_label = "Asset Details"
    bl_idname = "AION_PT_asset_details"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        if not settings.active_asset_id:
            layout.label(text="No asset loaded in viewer", icon="INFO")
            return

        box = layout.box()
        box.label(text=f"Asset: {settings.active_asset_name}", icon="OBJECT_DATA")
        box.label(text=f"Category: {settings.active_category}")
        box.label(text=f"Polys: {settings.active_poly_count:,} | Verts: {settings.active_vertex_count:,}")
        box.label(text=f"Bones: {settings.active_bone_count}")

        p_box = box.box()
        p_box.scale_y = 0.8
        p_box.label(text=f"Path: {settings.active_model_path}")
        if settings.active_skeleton_path:
            p_box.label(text=f"Skel: {settings.active_skeleton_path}")

        if settings.active_is_modified:
            m_box = layout.box()
            m_box.alert = True
            m_box.label(text="Asset has unsaved modifications!", icon="MODIFIER")


class AION_PT_viewport_controls(bpy.types.Panel):
    """Viewport staging, camera presets, and shading controls."""
    bl_label = "Viewer & Camera"
    bl_idname = "AION_PT_viewport_controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Camera presets
        row = layout.row(align=True)
        row.operator("aion_model.set_camera_view", text="Front").axis = "FRONT"
        row.operator("aion_model.set_camera_view", text="Side").axis = "RIGHT"
        row.operator("aion_model.set_camera_view", text="Top").axis = "TOP"

        row2 = layout.row(align=True)
        row2.operator("aion_model.focus_model", text="Focus", icon="VIEW_CAMERA")
        row2.operator("aion_model.set_camera_view", text="Persp/Ortho").axis = "PERSP_ORTHO"
        row2.operator("aion_model.set_camera_view", text="Reset").axis = "RESET"

        # Shading buttons
        s_row = layout.row(align=True)
        s_row.operator("aion_model.set_shading", text="Wire").mode = "WIREFRAME"
        s_row.operator("aion_model.set_shading", text="Solid").mode = "SOLID"
        s_row.operator("aion_model.set_shading", text="Material").mode = "MATERIAL"
        s_row.operator("aion_model.set_shading", text="Rendered").mode = "RENDERED"

        # Armature toggle
        layout.operator(
            "aion_model.toggle_bones",
            text="Hide Bones" if settings.show_armature else "Show Bones",
            icon="BONE_DATA",
        )


class AION_PT_animation_player(bpy.types.Panel):
    """Animation list and timeline transport controls."""
    bl_label = "Animations"
    bl_idname = "AION_PT_animation_player"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        if not settings.active_anims:
            layout.label(text="No animations available", icon="INFO")
            return

        layout.template_list(
            "UI_UL_list",
            "aion_anim_list",
            settings,
            "active_anims",
            settings,
            "active_anim_index",
            rows=3,
        )

        row = layout.row(align=True)
        row.operator("aion_model.switch_animation", text="Apply Animation", icon="PLAY")

        t_row = layout.row(align=True)
        t_row.scale_y = 1.2
        t_row.operator("aion_model.play_animation", text="Play / Pause", icon="PLAY")
        t_row.operator("aion_model.stop_animation", text="Stop", icon="REW")


class AION_PT_editors(bpy.types.Panel):
    """Mesh, skeleton, UV, and normal editing operations."""
    bl_label = "Edit Model"
    bl_idname = "AION_PT_editors"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        col = layout.column(align=True)
        row1 = col.row(align=True)
        row1.operator("aion_model.edit_mesh", text="Edit Mesh", icon="EDITMODE_HLT")
        row1.operator("aion_model.sculpt_mesh", text="Sculpt", icon="SCULPTMODE_HLT")

        row2 = col.row(align=True)
        row2.operator("aion_model.edit_bones", text="Edit Rig", icon="ARMATURE_DATA")
        row2.operator("aion_model.add_bone", text="Add Bone", icon="PLUS")

        col.operator("aion_model.recalc_normals", text="Recalculate Normals", icon="NORMALS_FACE")

        uv_row = col.row(align=True)
        uv_row.operator("aion_model.unwrap_uv", text="Unwrap UV", icon="UV")
        uv_row.operator("aion_model.pack_uv", text="Pack UVs", icon="ALIGN_CENTER")


class AION_PT_save_export(bpy.types.Panel):
    """Transactional saving back to client or safe loose export."""
    bl_label = "Save & Export"
    bl_idname = "AION_PT_save_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Save Button
        save_col = layout.column(align=True)
        save_col.scale_y = 1.4
        btn_text = "SAVE DIRECTLY TO CLIENT" if settings.allow_client_write else "SAVE TO SAFE EXPORT FOLDER"
        btn_icon = "CHECKMARK" if not settings.allow_client_write else "ERROR"
        save_col.operator("aion_model.save_asset", text=btn_text, icon=btn_icon)

        sub_row = layout.row(align=True)
        sub_row.operator("aion_model.export_loose", text="Export Loose", icon="EXPORT")
        sub_row.operator("aion_model.rollback_asset", text="Rollback .bak", icon="LOOP_BACK")


class AION_PT_creation(bpy.types.Panel):
    """Create new Aion assets from scratch or clone existing assets."""
    bl_label = "Create / Clone"
    bl_idname = "AION_PT_creation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("aion_model.create_from_mesh", text="Create Model from Mesh", icon="MESH_DATA")
        layout.operator("aion_model.clone_asset", text="Clone Active Asset", icon="DUPLICATE")


CLASSES = (
    AION_UL_asset_list,
    AION_PT_client_header,
    AION_PT_asset_browser,
    AION_PT_asset_details,
    AION_PT_viewport_controls,
    AION_PT_animation_player,
    AION_PT_editors,
    AION_PT_save_export,
    AION_PT_creation,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
