"""
Aion World NPC & Monster Spawning System for Blender.

Instantiates authoritative NPCs, monsters, and critters from:
1. Data/world/world.pak -> client_world_<map>.xml
2. Data/npcs/npcs.pak -> client_npcs.xml
3. mission_mission0.xml placeables

Supports CryEngine skeleton rigs, bone hierarchies, vertex skin weighting,
looping idle animations (.cal / .caf), high-performance GPU hardware mesh instancing,
correct world positioning, terrain ground-snapping, and hierarchical collections.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import bpy
from mathutils import Euler, Matrix, Vector

from core.client_provider import AionClientProvider
from core.pak_engine import AionPakArchive, get_pak_resolver
from formats.cgf.parser import get_cgf
from formats.level.npc_spawns import (
    NpcSpawn,
    NpcTemplate,
    parse_client_npc_templates,
    parse_world_npc_spawns,
)
from importers.armature_importer import (
    apply_caf_animation,
    apply_skin_weights,
    build_npc_armature,
)


@dataclass(frozen=True)
class NpcImportResult:
    """Statistics and result summary for NPC spawning pass."""
    spawns_found: int = 0
    spawns_placed: int = 0
    templates_resolved: int = 0
    models_loaded: int = 0
    instances_created: int = 0
    animated_npcs_count: int = 0
    missing_models_count: int = 0
    collection_name: str = "NPCS"

    @property
    def spawned_count(self) -> int:
        return self.spawns_placed

    @property
    def models_loaded_count(self) -> int:
        return self.models_loaded


# Global memory cache for parsed NPC templates across map loads: client_path -> templates
_GLOBAL_NPC_TEMPLATES_CACHE: Dict[str, Dict[str, NpcTemplate]] = {}


def get_cached_npc_templates(client_root: Path | str) -> Dict[str, NpcTemplate]:
    """Retrieves or loads client_npcs.xml templates via AionClientProvider."""
    global _GLOBAL_NPC_TEMPLATES_CACHE
    c_key = str(Path(client_root).resolve()).lower()
    if c_key in _GLOBAL_NPC_TEMPLATES_CACHE:
        return _GLOBAL_NPC_TEMPLATES_CACHE[c_key]

    provider = AionClientProvider(client_root)
    merged: Dict[str, NpcTemplate] = {}

    for t_name, t_bytes in provider.read_npc_templates_data():
        try:
            tmpls = parse_client_npc_templates(t_bytes)
            merged.update(tmpls)
        except Exception as exc:
            print(f"[AION NPC] Warning parsing template {t_name}: {exc}")

    _GLOBAL_NPC_TEMPLATES_CACHE[c_key] = merged
    return merged


def clear_npc_template_cache() -> None:
    global _GLOBAL_NPC_TEMPLATES_CACHE
    _GLOBAL_NPC_TEMPLATES_CACHE.clear()


def _get_map_name_from_level_dir(level_dir: Path) -> str:
    """Infers the clean Aion map name (e.g. 'df1', 'dc1', 'ab1') from folder path."""
    p = Path(level_dir).resolve()
    if p.name.lower() == ".aion_cache":
        p = p.parent
    name = p.name.lower()
    if name.endswith(".pak"):
        name = p.stem.lower()
    return name


def _get_or_create_collection(
    parent: bpy.types.Collection,
    name: str,
) -> bpy.types.Collection:
    for child in parent.children:
        if child.name == name:
            return child
    col = bpy.data.collections.new(name)
    parent.children.link(col)
    return col


def _snap_z_to_terrain(
    x: float,
    y: float,
    terrain_obj: Optional[bpy.types.Object],
    default_z: float = 0.0,
) -> float:
    """Raycasts vertically onto terrain mesh to find the exact ground elevation."""
    if terrain_obj is None or terrain_obj.type != "MESH":
        return default_z

    try:
        high_pt = Vector((x, y, 2000.0))
        ray_dir = Vector((0.0, 0.0, -1.0))

        inv_mat = terrain_obj.matrix_world.inverted()
        local_origin = inv_mat @ high_pt
        local_dir = inv_mat.to_3x3() @ ray_dir

        success, hit_loc, _, _ = terrain_obj.ray_cast(local_origin, local_dir)
        if success:
            world_hit = terrain_obj.matrix_world @ hit_loc
            return float(world_hit.z)
    except Exception:
        pass

    return default_z


def create_world_npcs(
    context: bpy.types.Context,
    level_dir: Path | str,
    client_root: Path | str,
    root_collection: Optional[bpy.types.Collection] = None,
    *,
    parent_collection: Optional[bpy.types.Collection] = None,
    terrain_obj: Optional[bpy.types.Object] = None,
    load_models: bool = True,
    import_models: Optional[bool] = None,
    animate_npcs: bool = True,
    import_monsters: bool = True,
    import_friendly: bool = True,
    import_ambient: bool = True,
    max_npcs: int = 0,
) -> NpcImportResult:
    """
    Authoritatively loads and places world NPCs into the Blender scene.
    Supports animated CryEngine skeletons (.caf/.cal) and static fallbacks.
    """
    level_path = Path(level_dir).resolve()
    client_path = Path(client_root).resolve()
    map_name = _get_map_name_from_level_dir(level_path)

    if import_models is not None:
        load_models = import_models

    target_parent = parent_collection or root_collection
    if target_parent is None:
        target_parent = context.scene.collection

    provider = AionClientProvider(client_path)

    # 1. Load world spawns from World.pak
    spawns: List[NpcSpawn] = []
    wdata = provider.read_world_spawns_data(map_name)
    if wdata:
        try:
            spawns = parse_world_npc_spawns(wdata, map_name)
        except Exception as exc:
            print(f"[AION NPC] Error parsing world spawns: {exc}")

    # Also check local level directory for client_world_<map>.xml
    for local_cand in (level_path / f"client_world_{map_name}.xml", level_path / f"client_world_{map_name}.bxml"):
        if local_cand.is_file():
            try:
                local_spawns = parse_world_npc_spawns(local_cand, map_name)
                if local_spawns and not spawns:
                    spawns = local_spawns
            except Exception:
                pass

    if not spawns:
        return NpcImportResult(spawns_found=0, spawns_placed=0)

    # 2. Get NPC templates
    templates = get_cached_npc_templates(client_path)

    # 3. Create Hierarchical Collections
    if target_parent.name == "NPCS":
        npcs_root_col = target_parent
    else:
        npcs_root_col = _get_or_create_collection(target_parent, "NPCS")

    friendly_col = _get_or_create_collection(npcs_root_col, "NPCs - Friendly")
    monsters_col = _get_or_create_collection(npcs_root_col, "Monsters & Hostiles")
    ambient_col = _get_or_create_collection(npcs_root_col, "NPCs - Ambient Fauna")
    templates_col = _get_or_create_collection(npcs_root_col, ".NPC_Templates")
    templates_col.hide_viewport = True
    templates_col.hide_render = True

    # 4. Cache template datablocks
    # static_mesh_cache: norm_ref -> bpy.types.Mesh
    static_meshes: Dict[str, bpy.types.Mesh] = {}
    # rig_template_cache: norm_ref -> (template_rig_obj, template_mesh_obj, action)
    rig_templates: Dict[str, Tuple[bpy.types.Object, bpy.types.Object, Optional[bpy.types.Action], List[str], List[Any]]] = {}

    def get_or_import_npc_asset(cgf_ref: str, npc_name_clean: str):
        """
        Loads CGF mesh and skeleton.
        Returns: ('ANIMATED', rig_obj, mesh_obj, action, bone_names, skin_weights)
              or ('STATIC', mesh_datablock)
              or ('NONE', None)
        """
        if not cgf_ref or not load_models:
            return "NONE", None

        norm_ref = cgf_ref.replace("\\", "/").strip().lstrip("/").lower()

        # Check existing rig template
        if animate_npcs and norm_ref in rig_templates:
            tpl_rig, tpl_mesh, action, b_names, s_weights = rig_templates[norm_ref]
            return "ANIMATED", tpl_rig, tpl_mesh, action, b_names, s_weights

        # Check existing static mesh
        if norm_ref in static_meshes:
            return "STATIC", static_meshes[norm_ref]

        # Extract CGF bytes
        cgf_bytes = provider.resolve_cgf_bytes(norm_ref)

        if not cgf_bytes:
            return "NONE", None

        try:
            cgf = get_cgf(io.BytesIO(cgf_bytes))
        except Exception as exc:
            print(f"[AION NPC] Failed parsing CGF bytes for {norm_ref}: {exc}")
            return "NONE", None

        # Check if CGF contains skeleton chunks
        bone_names = cgf.get("bone_names", [])
        bone_anim = cgf.get("bone_anim", [])
        bone_initial_pos = cgf.get("bone_initial_pos", [])

        # Find first valid mesh node
        nodes = cgf.get("nodes", {})
        mesh_chunk = None
        for n_id, n_data in nodes.items():
            if isinstance(n_data, dict) and "mesh" in n_data and n_data["mesh"]:
                mesh_chunk = n_data["mesh"]
                break

        if not mesh_chunk:
            return "NONE", None

        verts_pos = mesh_chunk.get("vertices", {}).get("position", [])
        faces_v = mesh_chunk.get("faces", {}).get("v", [])
        if not verts_pos or not faces_v:
            return "NONE", None

        skin_weights = mesh_chunk.get("skin_weights", [])

        # If skeleton present and animation requested:
        if animate_npcs and bone_names and bone_initial_pos:
            try:
                # 1. Build template rig
                tpl_rig = build_npc_armature(npc_name_clean, bone_names, bone_initial_pos, bone_anim, templates_col)

                # 2. Build template mesh
                m_data = bpy.data.meshes.new(f"{npc_name_clean}_Mesh")
                m_data.from_pydata(verts_pos, [], faces_v)
                m_data.update()

                tpl_mesh = bpy.data.objects.new(f"{npc_name_clean}_Skin", m_data)
                templates_col.objects.link(tpl_mesh)
                tpl_mesh.parent = tpl_rig

                # Apply skinning weights & armature modifier
                apply_skin_weights(tpl_mesh, bone_names, skin_weights, tpl_rig)

                # 3. Resolve and apply idle animation
                cal_map, caf_bytes = provider.resolve_animation_asset(norm_ref)
                action = None
                if caf_bytes:
                    action_name = f"{npc_name_clean}_Idle"
                    action = apply_caf_animation(tpl_rig, caf_bytes, bone_names, bone_anim, action_name)

                rig_templates[norm_ref] = (tpl_rig, tpl_mesh, action, bone_names, skin_weights)
                return "ANIMATED", tpl_rig, tpl_mesh, action, bone_names, skin_weights
            except Exception as exc:
                print(f"[AION NPC] Skeleton import failed for {norm_ref}, falling back to static mesh: {exc}")

        # Static mesh fallback
        try:
            m_data = bpy.data.meshes.new(f"{npc_name_clean}_StaticMesh")
            m_data.from_pydata(verts_pos, [], faces_v)
            m_data.update()
            static_meshes[norm_ref] = m_data
            return "STATIC", m_data
        except Exception as exc:
            print(f"[AION NPC] Static mesh creation failed for {norm_ref}: {exc}")
            return "NONE", None

    # 5. Place NPCs
    placed_count = 0
    instances_created = 0
    animated_count = 0
    missing_models = 0
    resolved_templates_count = 0

    spawns_to_process = spawns[:max_npcs] if max_npcs > 0 else spawns

    for spawn in spawns_to_process:
        npc_id = spawn.npc_id
        template = templates.get(npc_id)
        if template:
            resolved_templates_count += 1
            name = template.name
            title = template.title
            cgf_ref = template.cgf_reference
            scale = template.scale
            category = template.category
        else:
            name = f"NPC_{npc_id}"
            title = ""
            cgf_ref = "objects/npc/human/cam/cam.cgf"
            scale = 1.0
            category = "npc"

        # Apply category filters
        if category == "monster" and not import_monsters:
            continue
        if category == "ambient" and not import_ambient:
            continue
        if category in ("npc", "shugo") and not import_friendly:
            continue

        # Target subcollection
        if category == "monster":
            target_col = monsters_col
        elif category == "ambient":
            target_col = ambient_col
        else:
            target_col = friendly_col

        x, y, z = spawn.position
        if not spawn.has_explicit_z or abs(z) < 0.001:
            z = _snap_z_to_terrain(x, y, terrain_obj, default_z=z)

        # Fallback to humanoid model if template mesh is empty
        is_object_prop = any(tok in name.lower() for tok in ("stone", "sack", "box", "pouch", "chest", "door", "gate", "tomb"))
        if not cgf_ref and category in ("npc", "friendly") and not is_object_prop:
            if "df" in map_name or "dc" in map_name:
                cgf_ref = "objects/npc/human/cam/cam.cgf"
            else:
                cgf_ref = "objects/npc/human/cem/cem.cgf"

        yaw_rad = math.radians(spawn.heading_degrees)
        obj_name = f"{name}_{npc_id}"

        # Resolve asset
        res_type, *res_data = get_or_import_npc_asset(cgf_ref, name)

        if res_type == "ANIMATED":
            tpl_rig, tpl_mesh, action, b_names, s_weights = res_data
            # Create instance rig
            rig_inst = bpy.data.objects.new(f"{obj_name}_Rig", tpl_rig.data)
            mesh_inst = bpy.data.objects.new(obj_name, tpl_mesh.data)

            target_col.objects.link(rig_inst)
            target_col.objects.link(mesh_inst)

            mesh_inst.parent = rig_inst
            apply_skin_weights(mesh_inst, b_names, s_weights, rig_inst)

            if action:
                rig_inst.animation_data_create()
                rig_inst.animation_data.action = action

            rig_inst.location = (x, y, z)
            rig_inst.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
            rig_inst.scale = (scale, scale, scale)

            rig_inst["aion_source_type"] = "npc_rig"
            rig_inst["aion_npc_id"] = npc_id
            rig_inst["aion_npc_name"] = name
            mesh_inst["aion_source_type"] = "npc"
            mesh_inst["aion_npc_id"] = npc_id
            mesh_inst["aion_npc_name"] = name

            placed_count += 1
            instances_created += 1
            animated_count += 1

        elif res_type == "STATIC":
            mesh_data = res_data[0]
            obj = bpy.data.objects.new(obj_name, mesh_data)
            obj.location = (x, y, z)
            obj.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
            obj.scale = (scale, scale, scale)

            obj["aion_source_type"] = "npc"
            obj["aion_npc_id"] = npc_id
            obj["aion_npc_name"] = name
            if title:
                obj["aion_npc_title"] = title
            if cgf_ref:
                obj["aion_cgf_reference"] = cgf_ref

            target_col.objects.link(obj)
            placed_count += 1
            instances_created += 1

        else:
            # Fallback marker empty
            obj = bpy.data.objects.new(obj_name, None)
            obj.empty_display_type = "SINGLE_ARROW" if category != "monster" else "SPHERE"
            obj.empty_display_size = 1.0
            obj.location = (x, y, z)
            obj.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
            obj.scale = (scale, scale, scale)

            obj["aion_source_type"] = "npc_empty"
            obj["aion_npc_id"] = npc_id
            obj["aion_npc_name"] = name

            target_col.objects.link(obj)
            placed_count += 1
            if load_models:
                missing_models += 1

    return NpcImportResult(
        spawns_found=len(spawns),
        spawns_placed=placed_count,
        templates_resolved=resolved_templates_count,
        models_loaded=len(static_meshes) + len(rig_templates),
        instances_created=instances_created,
        animated_npcs_count=animated_count,
        missing_models_count=missing_models,
        collection_name="NPCS",
    )
