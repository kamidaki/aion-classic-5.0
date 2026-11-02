"""
3D Viewport UI Panels for Aion Blender Toolkit.
Provides a comprehensive Sidebar (N-panel) workflow for importing, editing,
animating, and direct-saving Aion maps.
"""

from __future__ import annotations

from pathlib import Path
import bpy


class AION_PT_base:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Aion Map"


class AION_PT_main_panel(AION_PT_base, bpy.types.Panel):
    """Main Header Panel for Aion Map Toolkit."""

    bl_idname = "AION_PT_main_panel"
    bl_label = "Aion Map Toolkit"

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "aion_settings", None)
        if not settings:
            layout.label(text="Settings not initialized", icon="ERROR")
            return

        # Status box
        active_level = settings.loaded_level_dir
        box = layout.box()
        if active_level:
            map_name = str(active_level).replace("\\", "/").rstrip("/").split("/")[-1]
            box.label(text=f"Active Map: {map_name}", icon="WORLD")
        else:
            box.label(text="No Level Loaded", icon="INFO")

        if settings.status_message:
            box.label(text=settings.status_message, icon="CHECKMARK")


class AION_PT_level_io(AION_PT_base, bpy.types.Panel):
    """Import and Level Management."""

    bl_idname = "AION_PT_level_io"
    bl_label = "Level Management & Import"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "aion_settings", None)
        if not settings:
            return

        col = layout.column(align=True)
        col.prop(settings, "client_root", text="Client Root")
        col.separator()

        row = col.row(align=True)
        row.scale_y = 1.3
        row.operator("import_scene.aion_level_folder", text="Import Level", icon="IMPORT")
        row.operator("import_scene.aion_cgf", text="Import CGF", icon="OBJECT_DATA")

        # Import options & Granular Category Controls
        box_opt = layout.box()
        box_opt.label(text="LOD & Engine Performance:", icon="PREFERENCES")
        box_opt.prop(settings, "target_model_lod", text="Model LOD")
        row = box_opt.row(align=True)
        row.prop(settings, "import_lod0", text="LOD 0")
        row.prop(settings, "import_lod1", text="LOD 1")
        row.prop(settings, "import_lod2", text="LOD 2")
        row.prop(settings, "import_lod3", text="LOD 3")
        box_opt.prop(settings, "use_mesh_instancing")
        box_opt.prop(settings, "optimize_material_preview")
        row_clean = box_opt.row(align=True)
        row_clean.operator("aion.clean_wind_drivers", text="Fix Playback Freeze", icon="PLAY")
        row_clean.operator("aion.purge_unused_data", text="Purge RAM", icon="TRASH")

        # Category Switches
        box_cat = layout.box()
        box_cat.label(text="Import Categories:", icon="OUTLINER")
        col = box_cat.column(align=True)
        col.prop(settings, "import_terrain")
        if settings.import_terrain:
            row = col.row(align=True)
            row.prop(settings, "terrain_lod", text="LOD")
            row.prop(settings, "import_terrain_shadows", text="Shadows")
        col.prop(settings, "import_buildings")
        col.prop(settings, "import_props")
        col.prop(settings, "import_vegetation")
        col.prop(settings, "import_npcs")
        if settings.import_npcs:
            sub = col.box().column(align=True)
            sub.prop(settings, "import_nameplates", text="3D Billboard Names")
            sub.operator("aion.toggle_npc_names", text="Toggle Names Visibility", icon="HIDE_OFF")
            sub.prop(settings, "import_npc_models")
            sub.prop(settings, "animate_npcs")
            sub.prop(settings, "import_monsters")
            sub.prop(settings, "import_friendly_npcs")
            sub.prop(settings, "import_ambient_creatures")
        col.prop(settings, "import_water")
        col.prop(settings, "import_lighting")
        col.prop(settings, "import_skybox")
        col.prop(settings, "import_collision")


class AION_PT_direct_save(AION_PT_base, bpy.types.Panel):
    """Direct Save & Client Repack."""

    bl_idname = "AION_PT_direct_save"
    bl_label = "Direct Save & Export"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "aion_settings", None)

        box = layout.box()
        box.label(text="Client-Ready Export:", icon="FILE_TICK")

        row = box.row(align=True)
        row.scale_y = 1.6
        row.operator("aion.direct_save", text="Direct Save Map", icon="FILE_REFRESH")

        col = box.column(align=True)
        if settings:
            col.prop(settings, "create_backup", text="Create Backup (.pak.bak)")

        col.separator()
        col.operator("export_scene.aion_level", text="Export to Folder / Repack...", icon="EXPORT")


class AION_PT_live_environment(AION_PT_base, bpy.types.Panel):
    """Live Environment & Animation Controls."""

    bl_idname = "AION_PT_live_environment"
    bl_label = "Live Environment & Animation"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "aion_settings", None)
        screen = context.screen

        is_playing = screen.is_animation_playing if screen else False
        row = layout.row(align=True)
        row.scale_y = 1.4
        if is_playing:
            row.operator("aion.toggle_animation", text="Pause Live Environment", icon="PAUSE")
        else:
            row.operator("aion.toggle_animation", text="Play Live Environment", icon="PLAY")

        if settings:
            box = layout.box()
            box.label(text="Environment Simulation:", icon="FORCE_WIND")
            col = box.column(align=True)
            col.prop(settings, "live_wind", text="Vegetation Wind Sway")
            col.prop(settings, "wind_strength", text="Wind Strength")
            col.prop(settings, "wind_speed", text="Wind Speed")
            col.prop(settings, "water_flow_speed", text="Water Wave Speed")


class AION_PT_map_editing(AION_PT_base, bpy.types.Panel):
    """Map Authoring & Placement Tools."""

    bl_idname = "AION_PT_map_editing"
    bl_label = "Map Editing Tools"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Placement & Transforms:", icon="SNAP_ON")
        col = box.column(align=True)
        col.operator("aion.snap_to_terrain", text="Snap Selected to Terrain", icon="SNAP_FACE")
        col.operator("aion.randomize_transforms", text="Randomize Jitter (Scatter)", icon="RNDCURVE")

        box2 = layout.box()
        box2.label(text="Terrain Sculpting:", icon="BRUSH_DATA")
        col2 = box2.column(align=True)
        col2.operator("aion.sync_terrain", text="Sync Sculpted Heights to LandMap", icon="MOD_OCEAN")


class AION_PT_inspector(AION_PT_base, bpy.types.Panel):
    """Selected Object & Asset Inspector."""

    bl_idname = "AION_PT_inspector"
    bl_label = "Aion Asset Inspector"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj:
            layout.label(text="Select an object to inspect", icon="RESTRICT_SELECT_ON")
            return

        box = layout.box()
        box.label(text=f"Object: {obj.name}", icon="OBJECT_DATA")

        src_type = obj.get("aion_source_type", None)
        src_ref = obj.get("aion_reference", None)
        src_idx = obj.get("aion_source_index", None)

        if src_type:
            col = box.column(align=True)
            col.label(text=f"Source Type: {src_type}")
            if src_ref:
                ref_name = str(src_ref).replace("\\", "/").split("/")[-1]
                col.label(text=f"Ref: {ref_name}")
            if src_idx is not None:
                col.label(text=f"Index: {src_idx}")
        else:
            box.label(text="Standard Blender Object (Unsaved)", icon="INFO")

        # Material list
        if obj.type == "MESH" and obj.data.materials:
            mat_box = layout.box()
            mat_box.label(text="Materials:", icon="MATERIAL")
            for mat in obj.data.materials:
                if not mat:
                    continue
                row = mat_box.row()
                row.label(text=mat.name)
                # Show blend method
                blend = getattr(mat, "blend_method", "OPAQUE")
                row.label(text=blend)




class AION_PT_performance_monitor(AION_PT_base, bpy.types.Panel):
    """Real-time Scene & Performance Monitor."""

    bl_idname = "AION_PT_performance_monitor"
    bl_label = "Performance & Client Monitor"
    bl_parent_id = "AION_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "aion_settings", None)

        box = layout.box()
        box.label(text="Scene Resources:", icon="INFO")
        col = box.column(align=True)
        col.label(text=f"Total Objects: {len(bpy.data.objects)}")
        col.label(text=f"Unique Meshes: {len(bpy.data.meshes)}")
        col.label(text=f"Materials: {len(bpy.data.materials)}")
        col.label(text=f"Textures / Images: {len(bpy.data.images)}")

        if settings and settings.client_root:
            from core.client_provider import AionClientProvider
            client_path = Path(settings.client_root)
            if client_path.is_dir():
                box_client = layout.box()
                box_client.label(text="Client Diagnostics:", icon="GHOST_ENABLED")
                try:
                    prov = AionClientProvider(client_path)
                    box_client.label(text=f"Version: {prov.flavor.name}")
                    box_client.label(text=f"Levels Available: {len(prov.get_available_maps())}")
                except Exception as exc:
                    box_client.label(text=f"Audit: {exc}")


PANEL_CLASSES = (
    AION_PT_main_panel,
    AION_PT_level_io,
    AION_PT_direct_save,
    AION_PT_map_editing,
    AION_PT_live_environment,
    AION_PT_inspector,
    AION_PT_performance_monitor,
)


def register():
    for cls in PANEL_CLASSES:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(PANEL_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
