"""
Editing and Environment Operators for Aion Blender Toolkit.
"""

from __future__ import annotations

from pathlib import Path
import bpy
from bpy.props import BoolProperty, FloatProperty

from editing.object_editor import randomize_object_transforms, snap_objects_to_terrain
from editing.terrain_editor import find_terrain_object, sync_sculpted_terrain_to_land_map


class AION_OT_snap_to_terrain(bpy.types.Operator):
    """Snap selected objects down to the surface of the Aion terrain mesh."""

    bl_idname = "aion.snap_to_terrain"
    bl_label = "Snap to Terrain"
    bl_description = "Raycast selected objects down onto the underlying terrain heightfield"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        terrain_obj = find_terrain_object(context.scene)
        if not terrain_obj:
            self.report({"ERROR"}, "No terrain mesh found in scene.")
            return {"CANCELLED"}

        snapped = snap_objects_to_terrain(context.selected_objects, terrain_obj)
        self.report({"INFO"}, f"Snapped {snapped} objects onto terrain.")
        return {"FINISHED"}


class AION_OT_randomize_transforms(bpy.types.Operator):
    """Randomize rotation and scale of selected vegetation/decorations for natural scattering."""

    bl_idname = "aion.randomize_transforms"
    bl_label = "Randomize Jitter"
    bl_description = "Apply random yaw rotation and subtle scale variation to selected objects"
    bl_options = {"REGISTER", "UNDO"}

    min_scale: FloatProperty(
        name="Min Scale",
        description="Minimum scale multiplier",
        default=0.85,
        min=0.1,
        max=2.0,
    )

    max_scale: FloatProperty(
        name="Max Scale",
        description="Maximum scale multiplier",
        default=1.15,
        min=0.1,
        max=3.0,
    )

    random_yaw: BoolProperty(
        name="Random Yaw (Z-axis)",
        description="Apply full random 360-degree rotation around Z",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        count = randomize_object_transforms(
            context.selected_objects,
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            random_yaw=self.random_yaw,
        )
        self.report({"INFO"}, f"Randomized transforms for {count} objects.")
        return {"FINISHED"}


class AION_OT_sync_terrain(bpy.types.Operator):
    """Synchronize sculpted terrain mesh elevations into the active level's land_map.h32."""

    bl_idname = "aion.sync_terrain"
    bl_label = "Sync Sculpted Terrain"
    bl_description = "Write vertex elevations from the sculpted Blender terrain mesh back into land_map.h32"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        terrain_obj = find_terrain_object(context.scene)
        if not terrain_obj:
            self.report({"ERROR"}, "No terrain mesh found in scene.")
            return {"CANCELLED"}

        settings = getattr(context.scene, "aion_settings", None)
        loaded_dir = getattr(settings, "loaded_level_dir", "") if settings else ""
        if not loaded_dir or not Path(loaded_dir).is_dir():
            self.report({"ERROR"}, "No active level directory known. Please load a level first.")
            return {"CANCELLED"}

        level_path = Path(loaded_dir)
        h32_path = level_path / "terrain" / "land_map.h32"
        if not h32_path.is_file():
            cache_h32 = level_path / ".aion_cache" / "terrain" / "land_map.h32"
            if cache_h32.is_file():
                h32_path = cache_h32

        if not h32_path.is_file():
            self.report({"ERROR"}, f"land_map.h32 not found in {level_path}")
            return {"CANCELLED"}

        try:
            modified_count, total = sync_sculpted_terrain_to_land_map(
                terrain_obj,
                h32_path,
                h32_path,
            )
            msg = f"Synced terrain: {modified_count} samples updated in land_map.h32 (Total: {total})."
            self.report({"INFO"}, msg)
            if settings:
                settings.status_message = msg
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to sync terrain: {exc}")
            return {"CANCELLED"}


class AION_OT_toggle_animation(bpy.types.Operator):
    """Play or Pause live environmental animations (water ripples, wind sway, UV scrolling)."""

    bl_idname = "aion.toggle_animation"
    bl_label = "Play / Pause Live Environment"
    bl_description = "Toggle live playback of environmental animations in the viewport"
    bl_options = {"REGISTER"}

    def execute(self, context):
        wm = context.window_manager
        screen = context.screen
        if screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
            self.report({"INFO"}, "Animation paused.")
        else:
            bpy.ops.screen.animation_play()
            self.report({"INFO"}, "Animation playing (Space to pause).")
        return {"FINISHED"}


class AION_OT_toggle_npc_names(bpy.types.Operator):
    """Toggle visibility of 3D floating NPC Nameplates in the 3D Viewport."""

    bl_idname = "aion.toggle_npc_names"
    bl_label = "Toggle NPC Nameplates"
    bl_description = "Show or hide 3D billboard nameplates for all world NPCs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        names_col = bpy.data.collections.get("NPC_NAMES")
        if not names_col:
            npcs_col = bpy.data.collections.get("NPCS")
            if npcs_col:
                names_col = npcs_col.children.get("NPC_NAMES")

        if not names_col:
            self.report({"WARNING"}, "No NPC_NAMES collection found in scene.")
            return {"CANCELLED"}

        new_state = not names_col.hide_viewport
        names_col.hide_viewport = new_state
        state_str = "Hidden" if new_state else "Visible"
        self.report({"INFO"}, f"NPC Nameplates: {state_str}")
        return {"FINISHED"}


class AION_OT_open_asset_browser(bpy.types.Operator):
    """Open Blender's 3D Asset Browser inventory grid displaying model thumbnails."""

    bl_idname = "aion.open_asset_browser"
    bl_label = "Open 3D Asset Browser (Grid)"
    bl_description = "Switch an editor area to Blender's native 3D Asset Browser grid without blocking the viewport"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from importers.asset_catalog import catalog_scene_assets

        catalog_scene_assets(context, generate_previews=False)

        for area in context.screen.areas:
            if area.ui_type == "ASSETS":
                self.report({"INFO"}, "3D Asset Browser is already open.")
                return {"FINISHED"}

        candidate_area = None
        for area in context.screen.areas:
            if area.type not in ("VIEW_3D", "PROPERTIES", "OUTLINER"):
                candidate_area = area
                break

        if candidate_area:
            candidate_area.ui_type = "ASSETS"
            self.report({"INFO"}, f"Switched {candidate_area.type} area to 3D Asset Browser grid.")
            return {"FINISHED"}

        self.report({"INFO"}, "All models cataloged! Switch any editor area to Asset Browser to view 3D grid.")
        return {"FINISHED"}


class AION_OT_catalog_assets(bpy.types.Operator):
    """Catalog all models in scene (optionally render 3D thumbnail previews)."""

    bl_idname = "aion.catalog_assets"
    bl_label = "Catalogar Modelos da Cena"
    bl_description = "Marca os modelos importados como Assets do Blender (gera miniaturas 3D apenas se solicitado)"
    bl_options = {"REGISTER", "UNDO"}

    generate_previews: BoolProperty(
        name="Gerar Miniaturas 3D (Lento em GPU fraca)",
        description="Renderiza miniaturas 3D para cada modelo (desativado por padrão para evitar travamento)",
        default=False,
    )

    def execute(self, context):
        from importers.asset_catalog import catalog_scene_assets, invalidate_asset_catalog_cache

        count = catalog_scene_assets(context, generate_previews=self.generate_previews)
        invalidate_asset_catalog_cache()
        self.report({"INFO"}, f"Catalogados {count} assets na cena!")
        return {"FINISHED"}


class AION_OT_refresh_client_assets(bpy.types.Operator):
    """Scan client PAKs on demand to populate the Client Library Explorer cache."""

    bl_idname = "aion.refresh_client_assets"
    bl_label = "Escanear Biblioteca do Cliente"
    bl_description = "Indexa os modelos CGF/CGA disponíveis nos PAKs do cliente (executado apenas sob demanda)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = getattr(context.scene, "aion_settings", None)
        client_root = getattr(settings, "client_root", "") if settings else ""
        if not client_root or not Path(client_root).is_dir():
            self.report({"ERROR"}, "Defina um Client Root válido antes de escanear.")
            return {"CANCELLED"}

        from importers.asset_catalog import get_client_model_items, _CLIENT_MODEL_CACHE

        key = str(Path(client_root).resolve()).lower()
        _CLIENT_MODEL_CACHE.pop(key, None)
        items = get_client_model_items(client_root, category_filter="ALL", search_query="", limit=0, allow_scan=True)
        self.report({"INFO"}, f"Biblioteca escaneada: {len(items)} modelos encontrados em PAKs.")
        return {"FINISHED"}


class AION_OT_refresh_client_diagnostics(bpy.types.Operator):
    """Inspect client version and level count once on user demand (cached for zero UI redraw cost)."""

    bl_idname = "aion.refresh_client_diagnostics"
    bl_label = "Verificar Cliente Aion"
    bl_description = "Detecta a versão e quantidade de mapas do Client Root (armazenado em cache para 60+ FPS na interface)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = getattr(context.scene, "aion_settings", None)
        client_root = getattr(settings, "client_root", "") if settings else ""
        if not client_root or not Path(client_root).is_dir():
            self.report({"ERROR"}, "Defina um Client Root válido primeiro.")
            return {"CANCELLED"}

        from ui.panels import refresh_client_diagnostics_cache

        flavor_name, maps_count = refresh_client_diagnostics_cache(client_root)
        self.report({"INFO"}, f"Cliente detectado: {flavor_name} ({maps_count} mapas).")
        return {"FINISHED"}


class AION_OT_spawn_asset(bpy.types.Operator):
    """Spawn an instance of the selected map asset into the active scene."""

    bl_idname = "aion.spawn_asset"
    bl_label = "Spawn Asset"
    bl_description = "Spawn a new instance of this model at the 3D cursor"
    bl_options = {"REGISTER", "UNDO"}

    reference: bpy.props.StringProperty(name="Reference", default="")

    def execute(self, context):
        from importers.asset_catalog import spawn_asset_at_location

        settings = getattr(context.scene, "aion_settings", None)
        snap = getattr(settings, "asset_snap_terrain", True) if settings else True

        target = None
        ref_norm = self.reference.replace("\\", "/").strip().lower()

        templates_col = bpy.data.collections.get(".TEMPLATES")
        if templates_col:
            for child in templates_col.children:
                for o in child.objects:
                    cand_ref = str(o.get("aion_reference") or o.name).replace("\\", "/").strip().lower()
                    if cand_ref == ref_norm or o.name.lower() == ref_norm:
                        target = o
                        break
                if target:
                    break

        if not target:
            for o in context.scene.objects:
                cand_ref = str(o.get("aion_reference") or o.name).replace("\\", "/").strip().lower()
                if cand_ref == ref_norm or o.name.lower() == ref_norm:
                    target = o
                    break

        if not target:
            self.report({"ERROR"}, f"Could not find model template for: {self.reference}")
            return {"CANCELLED"}

        loc = context.scene.cursor.location
        new_inst = spawn_asset_at_location(context, target, loc, snap_terrain=snap)
        if new_inst:
            self.report({"INFO"}, f"Spawned '{new_inst.name}' at {loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}")
            return {"FINISHED"}
        return {"CANCELLED"}


class AION_OT_spawn_client_model(bpy.types.Operator):
    """Import and spawn a 3D model from the client library."""

    bl_idname = "aion.spawn_client_model"
    bl_label = "Import & Spawn Model"
    bl_description = "Extract and import this 3D model from client PAKs, create template asset, and place at 3D cursor"
    bl_options = {"REGISTER", "UNDO"}

    model_path: bpy.props.StringProperty(name="Model Path", default="")

    def execute(self, context):
        from importers.asset_catalog import import_and_spawn_client_model

        settings = getattr(context.scene, "aion_settings", None)
        client_root = getattr(settings, "client_root", "") if settings else ""
        if not client_root:
            self.report({"ERROR"}, "Client Root is not set in Aion settings.")
            return {"CANCELLED"}

        snap = getattr(settings, "asset_snap_terrain", True) if settings else True
        loc = context.scene.cursor.location

        inst = import_and_spawn_client_model(
            context,
            client_root,
            self.model_path,
            location=loc,
            snap_terrain=snap,
        )
        if inst:
            self.report({"INFO"}, f"Imported & spawned '{inst.name}' into scene.")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, f"Failed to import client model: {self.model_path}")
            return {"CANCELLED"}


class AION_OT_select_asset_in_scene(bpy.types.Operator):
    """Select this asset template or instance in the 3D viewport."""

    bl_idname = "aion.select_asset_in_scene"
    bl_label = "Select in Scene"
    bl_description = "Select and focus on this model in the 3D viewport"
    bl_options = {"REGISTER", "UNDO"}

    reference: bpy.props.StringProperty(name="Reference", default="")

    def execute(self, context):
        ref_norm = self.reference.replace("\\", "/").strip().lower()
        target = None
        for o in context.scene.objects:
            cand_ref = str(o.get("aion_reference") or o.name).replace("\\", "/").strip().lower()
            if cand_ref == ref_norm or o.name.lower() == ref_norm:
                target = o
                break

        if target:
            for o in context.selected_objects:
                o.select_set(False)
            target.select_set(True)
            context.view_layer.objects.active = target
            self.report({"INFO"}, f"Selected '{target.name}'")
            return {"FINISHED"}
        self.report({"WARNING"}, f"No instance found in scene for: {self.reference}")
        return {"CANCELLED"}
