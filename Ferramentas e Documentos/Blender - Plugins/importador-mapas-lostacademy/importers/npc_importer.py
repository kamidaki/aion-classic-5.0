"""
Aion World NPC & Entity Spawner.
Extracts NPC spawns from level/world data, resolves templates & 3D models (CGF),
supports CryEngine skeleton rigs & idle animations (.caf/.cal),
and spawns entities into categorized Blender collections with ground terrain alignment.
"""

from __future__ import annotations

from array import array
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
import gzip
import io
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

from core.client_provider import AionClientProvider
from formats.cgf.caf_parser import parse_caf
from formats.cgf.parser import get_cgf
from formats.level.npc_spawns import (
    DEFAULT_HUMANOID_MODELS,
    KNOWN_MONSTER_MODELS,
    NpcSpawn,
    NpcTemplate,
    WalkerRoute,
    find_emulator_static_data_dir,
    parse_emulator_map_spawns,
    parse_npc_templates,
    parse_walker_routes,
    parse_world_npc_spawns,
)
from importers.armature_importer import (
    build_npc_armature,
    apply_skin_weights,
    apply_caf_animation,
    iter_apply_caf_animation,
    ArmatureCache,
)


@dataclass(frozen=True)
class NpcImportResult:
    spawns_found: int = 0
    spawns_placed: int = 0
    animated_rigs_created: int = 0
    models_loaded: int = 0
    missing_models: int = 0
    instances_created: int = 0
    walking_routes_applied: int = 0

    @property
    def spawned_count(self) -> int:
        return self.spawns_placed

    @property
    def models_loaded_count(self) -> int:
        return self.models_loaded


_NPC_TEMPLATE_CACHE: Dict[str, Dict[str, NpcTemplate]] = {}


def _get_npc_cache_file(client_path: Path) -> Path:
    cache_dir = client_path / ".aion_cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = cache_dir / ".perm_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return cache_dir / "npc_templates.json"
    except Exception:
        temp_cache = Path(tempfile.gettempdir()) / "aion_blender_cache" / "npcs"
        temp_cache.mkdir(parents=True, exist_ok=True)
        return temp_cache / "npc_templates.json"


def get_cached_npc_templates(client_path: Path) -> Dict[str, NpcTemplate]:
    """Caches NPC templates per client root with fast disk persistence (.json.gz)."""
    client_key = str(client_path.resolve())
    if client_key in _NPC_TEMPLATE_CACHE:
        return _NPC_TEMPLATE_CACHE[client_key]

    cache_file = _get_npc_cache_file(client_path)
    gz_file = cache_file.with_name(cache_file.name + ".gz")

    # Check npcs.pak mtime for cache invalidation
    provider = AionClientProvider(client_path)
    npc_paks = provider.get_npcs_pak_paths()
    latest_mtime = max((p.stat().st_mtime for p in npc_paks if p.is_file()), default=0.0)

    # 1. Try reading from disk cache (.json.gz or .json)
    raw_bytes: Optional[bytes] = None
    if gz_file.is_file():
        try:
            with gzip.open(gz_file, "rb") as f_gz:
                raw_bytes = f_gz.read()
        except Exception:
            raw_bytes = None

    if raw_bytes is None and cache_file.is_file():
        try:
            raw_bytes = cache_file.read_bytes()
        except Exception:
            raw_bytes = None

    if raw_bytes is not None:
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(payload, dict) and payload.get("version") == 2:
                cached_mtime = payload.get("pak_mtime", 0.0)
                if abs(cached_mtime - latest_mtime) < 1.0 or latest_mtime == 0.0:
                    loaded_templates: Dict[str, NpcTemplate] = {}
                    for item in payload.get("templates", []):
                        # [id, name, title, cgf_reference, scale, category, race, idle_animation, desc_key, title_key, walk_speed]
                        t = NpcTemplate(
                            id=item[0],
                            name=item[1],
                            title=item[2] if len(item) > 2 else "",
                            cgf_reference=item[3] if len(item) > 3 else "",
                            scale=item[4] if len(item) > 4 else 1.0,
                            category=item[5] if len(item) > 5 else "npc",
                            race=item[6] if len(item) > 6 else "",
                            idle_animation=item[7] if len(item) > 7 else "",
                            desc_key=item[8] if len(item) > 8 else "",
                            title_key=item[9] if len(item) > 9 else "",
                            walk_speed=float(item[10]) if len(item) > 10 else 1.5,
                        )
                        loaded_templates[t.id] = t
                    if loaded_templates:
                        _NPC_TEMPLATE_CACHE[client_key] = loaded_templates
                        return loaded_templates
        except Exception:
            pass

    # 2. Parse from XML tables if not in disk cache
    all_templates: Dict[str, NpcTemplate] = {}
    for t_name, t_bytes in provider.read_npc_templates_data():
        if t_bytes:
            try:
                parsed = parse_npc_templates(t_bytes)
                all_templates.update(parsed)
            except Exception as exc:
                print(f"[AION NPC] Warning parsing template table {t_name}: {exc}")

    _NPC_TEMPLATE_CACHE[client_key] = all_templates

    # 3. Save to disk cache for instantaneous subsequent loads
    if all_templates:
        try:
            tpl_list = [
                [
                    t.id,
                    t.name,
                    t.title,
                    t.cgf_reference,
                    t.scale,
                    t.category,
                    t.race,
                    t.idle_animation,
                    t.desc_key,
                    t.title_key,
                    t.walk_speed,
                ]
                for t in all_templates.values()
            ]
            payload = {
                "version": 2,
                "pak_mtime": latest_mtime,
                "templates": tpl_list,
            }
            raw_json = json.dumps(payload, separators=(",", ":"))
            json_bytes = raw_json.encode("utf-8")
            with gzip.open(gz_file, "wb") as f_gz:
                f_gz.write(json_bytes)
            if cache_file.is_file():
                cache_file.unlink(missing_ok=True)
        except Exception:
            pass

    return all_templates


def clear_cache() -> None:
    """Clears in-memory NPC template cache."""
    global _NPC_TEMPLATE_CACHE
    _NPC_TEMPLATE_CACHE.clear()


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


def _sample_terrain_grid_z(x: float, y: float, grid: tuple) -> Optional[float]:
    """O(1) bilinear height interpolation over a regular axis-aligned terrain height grid."""
    row_xs, col_ys, z_vals, new_h, new_w = grid
    if new_h < 2 or new_w < 2 or not row_xs or not col_ys:
        return None
    if x < row_xs[0] or x > row_xs[-1] or y < col_ys[0] or y > col_ys[-1]:
        return None

    r0 = bisect_right(row_xs, x) - 1
    if r0 < 0:
        r0 = 0
    elif r0 > new_h - 2:
        r0 = new_h - 2
    r1 = r0 + 1

    c0 = bisect_right(col_ys, y) - 1
    if c0 < 0:
        c0 = 0
    elif c0 > new_w - 2:
        c0 = new_w - 2
    c1 = c0 + 1

    dx = row_xs[r1] - row_xs[r0]
    tx = (x - row_xs[r0]) / dx if dx > 0.0 else 0.0
    if tx < 0.0:
        tx = 0.0
    elif tx > 1.0:
        tx = 1.0

    dy = col_ys[c1] - col_ys[c0]
    ty = (y - col_ys[c0]) / dy if dy > 0.0 else 0.0
    if ty < 0.0:
        ty = 0.0
    elif ty > 1.0:
        ty = 1.0

    base0 = r0 * new_w
    base1 = r1 * new_w
    z00 = z_vals[base0 + c0]
    z01 = z_vals[base0 + c1]
    z10 = z_vals[base1 + c0]
    z11 = z_vals[base1 + c1]
    z0 = z00 + (z01 - z00) * ty
    z1 = z10 + (z11 - z10) * ty
    return float(z0 + (z1 - z0) * tx)


def _extract_terrain_height_grid(terrain_obj: Optional[bpy.types.Object]) -> Optional[tuple]:
    """Extracts a fast O(1) bilinear height grid from an imported Aion terrain object."""
    if terrain_obj is None or terrain_obj.type != "MESH" or terrain_obj.data is None:
        return None
    mesh = terrain_obj.data
    h = int(terrain_obj.get("aion_terrain_grid_h", 0) or 0)
    w = int(terrain_obj.get("aion_terrain_grid_w", 0) or 0)
    if h < 2 or w < 2 or h * w != len(mesh.vertices):
        return None
    try:
        flat_co = array("f", [0.0]) * (h * w * 3)
        mesh.vertices.foreach_get("co", flat_co)
        loc_x = float(terrain_obj.location.x)
        loc_y = float(terrain_obj.location.y)
        loc_z = float(terrain_obj.location.z)
        row_xs = [flat_co[(r * w) * 3] + loc_x for r in range(h)]
        col_ys = [flat_co[c * 3 + 1] + loc_y for c in range(w)]
        z_vals = flat_co[2::3]
        if abs(loc_z) > 1e-6:
            z_vals = array("f", (z + loc_z for z in z_vals))
        return (row_xs, col_ys, z_vals, h, w)
    except Exception:
        return None


def _snap_z_to_terrain(
    x: float,
    y: float,
    terrain_obj: Optional[bpy.types.Object],
    default_z: float = 0.0,
    terrain_bvh: Optional[BVHTree] = None,
    terrain_inv_mat: Optional[Matrix] = None,
    terrain_grid: Optional[tuple] = None,
) -> float:
    """Finds ground Z in O(1) from regular terrain grid, falling back to BVH/raycast if needed."""
    if terrain_grid is not None:
        sampled = _sample_terrain_grid_z(x, y, terrain_grid)
        if sampled is not None:
            return sampled
        return default_z

    if terrain_obj is None or terrain_obj.type != "MESH":
        return default_z

    try:
        high_pt = Vector((x, y, 2000.0))
        ray_dir = Vector((0.0, 0.0, -1.0))

        inv_mat = terrain_inv_mat if terrain_inv_mat is not None else terrain_obj.matrix_world.inverted()
        local_origin = inv_mat @ high_pt
        local_dir = inv_mat.to_3x3() @ ray_dir

        if terrain_bvh is not None:
            hit_loc, _, _, _ = terrain_bvh.ray_cast(local_origin, local_dir, 4500.0)
            if hit_loc is not None:
                world_hit = terrain_obj.matrix_world @ hit_loc
                return float(world_hit.z)
            return default_z

        success, hit_loc, _, _ = terrain_obj.ray_cast(local_origin, local_dir)
        if success:
            world_hit = terrain_obj.matrix_world @ hit_loc
            return float(world_hit.z)
    except Exception:
        pass

    return default_z


def _build_terrain_bvh(terrain_obj: Optional[bpy.types.Object]) -> tuple[Optional[BVHTree], Optional[Matrix]]:
    if terrain_obj is None or terrain_obj.type != "MESH" or terrain_obj.data is None:
        return None, None
    try:
        mesh = terrain_obj.data
        verts = [v.co for v in mesh.vertices]
        polys = [p.vertices for p in mesh.polygons]
        if not verts or not polys:
            return None, None
        return BVHTree.FromPolygons(verts, polys), terrain_obj.matrix_world.inverted()
    except Exception:
        return None, None


def _get_nameplate_material(category: str) -> bpy.types.Material:
    """Shares 1 lightweight Emission material per NPC disposition so nameplates read crisp at 60+ FPS."""
    if category == "monster":
        mat_name = "AION_Nameplate_Monster"
        color = (1.0, 0.25, 0.22, 1.0)
    elif category == "ambient":
        mat_name = "AION_Nameplate_Ambient"
        color = (0.65, 0.96, 0.48, 1.0)
    else:
        mat_name = "AION_Nameplate_Friendly"
        color = (0.35, 0.92, 1.0, 1.0)

    existing = bpy.data.materials.get(mat_name)
    if existing is not None:
        return existing

    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = color
    if "Strength" in emit.inputs:
        emit.inputs["Strength"].default_value = 1.15
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def _create_npc_nameplate(
    target_col: bpy.types.Collection,
    parent_obj: bpy.types.Object,
    npc_id: str,
    localized_name: str,
    title: str = "",
    scale: float = 1.0,
    category: str = "npc",
    *,
    yaw_rad: float = 0.0,
    has_walker_anim: bool = False,
    bbox_height: float = 1.85,
    disable_shadows: bool = True,
) -> bpy.types.Object:
    """Creates an upright, lightweight PT-BR 3D Font Nameplate positioned above the NPC's head."""
    curve_data = bpy.data.curves.new(type="FONT", name=f"NPCLabel_{npc_id}")
    if title and not title.startswith("STR_"):
        label_text = f"<{title}>\n{localized_name}"
    else:
        label_text = localized_name
    curve_data.body = label_text
    curve_data.align_x = "CENTER"
    curve_data.align_y = "BOTTOM"
    curve_data.fill_mode = "FRONT"
    curve_data.size = 0.42 * max(0.7, min(float(scale), 2.0))
    curve_data.resolution_u = 1
    curve_data.extrude = 0.0
    curve_data.bevel_depth = 0.0
    curve_data.materials.append(_get_nameplate_material(category))

    label_obj = bpy.data.objects.new(f"NPCLabel_{npc_id}", curve_data)
    head_z = max(2.15, float(bbox_height) + 0.35)
    label_obj.location = (0.0, 0.0, head_z)
    # Stand text upright in world Z; stationary NPCs compensate parent yaw so text faces South (-Y) cleanly.
    comp_yaw = 0.0 if has_walker_anim else -float(yaw_rad)
    label_obj.rotation_euler = Euler((math.pi * 0.5, 0.0, comp_yaw), "XYZ")
    label_obj.parent = parent_obj
    if disable_shadows and hasattr(label_obj, "visible_shadow"):
        try:
            label_obj.visible_shadow = False
        except (AttributeError, TypeError):
            pass
    label_obj["aion_source_type"] = "npc_nameplate"
    label_obj["aion_npc_id"] = npc_id
    label_obj["aion_npc_name"] = localized_name
    if title:
        label_obj["aion_npc_title"] = title
    target_col.objects.link(label_obj)
    return label_obj


def _apply_npc_walk_route(
    target_obj: bpy.types.Object,
    route: WalkerRoute,
    walk_speed: float,
    spawn_id: str,
    spawn_pos: Tuple[float, float, float],
    terrain_obj,
    terrain_bvh,
    terrain_inv_mat,
    terrain_grid,
    fps: float = 24.0,
) -> int:
    """Builds a smooth cyclic walk patrol F-Curve action along the emulator's walker_template route."""
    steps = list(route.steps)
    if len(steps) < 2:
        return 0

    def _resolve_pt(sx: float, sy: float, sz: float) -> Tuple[float, float, float]:
        if abs(sz) < 0.001:
            sz = _snap_z_to_terrain(
                sx,
                sy,
                terrain_obj,
                default_z=spawn_pos[2],
                terrain_bvh=terrain_bvh,
                terrain_inv_mat=terrain_inv_mat,
                terrain_grid=terrain_grid,
            )
        return (float(sx), float(sy), float(sz))

    pts: List[Tuple[Tuple[float, float, float], int]] = [
        (_resolve_pt(st.x, st.y, st.z), int(st.rest_time)) for st in steps
    ]
    # Close loop or mirror path cleanly so Cyclic animation has zero teleportation jump
    first_xyz, last_xyz = pts[0][0], pts[-1][0]
    close_dist = math.dist(first_xyz[:2], last_xyz[:2])
    if route.loop and close_dist > 1.5:
        pts.append((first_xyz, pts[0][1]))
    elif not route.loop and len(pts) >= 2:
        for rev_pt in reversed(pts[:-1]):
            pts.append(rev_pt)

    speed = float(walk_speed) if walk_speed and walk_speed > 0.2 else 1.5
    act_name = f"Walk_{route.route_id}_{spawn_id}"
    action = bpy.data.actions.new(act_name)
    if target_obj.animation_data is None:
        target_obj.animation_data_create()
    target_obj.animation_data.action = action

    cur_frame = 1
    prev_xyz = pts[0][0]
    n_pts = len(pts)

    for idx_pt, (xyz, rest_sec) in enumerate(pts):
        if idx_pt > 0:
            dist = math.dist(prev_xyz, xyz)
            move_sec = dist / speed if dist > 0.01 else 0.35
            cur_frame += max(4, int(round(move_sec * fps)))

        # Face next waypoint heading (cryengine forward +Y)
        next_xyz = pts[(idx_pt + 1) % n_pts][0]
        dx = next_xyz[0] - xyz[0]
        dy = next_xyz[1] - xyz[1]
        if (dx * dx + dy * dy) > 1e-4:
            heading_rad = math.atan2(dy, dx) - math.pi * 0.5
        else:
            heading_rad = float(target_obj.rotation_euler[2])

        target_obj.location = xyz
        target_obj.rotation_euler = Euler((0.0, 0.0, heading_rad), "XYZ")
        target_obj.keyframe_insert(data_path="location", frame=cur_frame)
        target_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=cur_frame)

        if rest_sec > 0 and idx_pt < n_pts - 1:
            cur_frame += max(2, int(round(rest_sec * fps)))
            target_obj.keyframe_insert(data_path="location", frame=cur_frame)
            target_obj.keyframe_insert(data_path="rotation_euler", index=2, frame=cur_frame)

        prev_xyz = xyz

    # Ensure linear interpolation & endless Cycles modifier on patrol F-Curves
    fcurves: List[Any] = []
    if hasattr(action, "fcurves"):
        fcurves.extend(action.fcurves)
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                fcurves.extend(getattr(bag, "fcurves", ()))

    for fc in fcurves:
        for kp in getattr(fc, "keyframe_points", ()):
            kp.interpolation = "LINEAR"
        if not any(m.type == "CYCLES" for m in fc.modifiers):
            fc.modifiers.new(type="CYCLES")

    target_obj["aion_walker_route_id"] = route.route_id
    target_obj["aion_walker_step_count"] = len(steps)
    target_obj["aion_walker_end_frame"] = cur_frame
    return cur_frame


def _prepare_npc_stage_data(
    level_path: Path,
    client_path: Path,
    map_name: str,
    *,
    import_monsters: bool,
    import_friendly: bool,
    import_ambient: bool,
    max_npcs: int,
    emulator_data_dir: Optional[Path] = None,
) -> dict:
    """Pure-Python I/O & XML/BXML parsing stage safe for background worker execution."""
    provider = AionClientProvider(client_path)

    spawns: List[NpcSpawn] = []
    client_spawns: List[NpcSpawn] = []
    wdata = provider.read_world_spawns_data(map_name)
    if wdata:
        try:
            client_spawns = parse_world_npc_spawns(wdata, map_name)
        except Exception as exc:
            print(f"[AION NPC] Error parsing world spawns: {exc}")

    for local_cand in (level_path / f"client_world_{map_name}.xml", level_path / f"client_world_{map_name}.bxml"):
        if local_cand.is_file():
            try:
                local_spawns = parse_world_npc_spawns(local_cand, map_name)
                if local_spawns and not client_spawns:
                    client_spawns = local_spawns
            except Exception:
                pass

    walker_routes: Dict[str, WalkerRoute] = {}
    static_data_dir = find_emulator_static_data_dir(emulator_data_dir, client_path)
    if static_data_dir is not None:
        emu_spawns = parse_emulator_map_spawns(static_data_dir, map_name)
        if emu_spawns:
            spawns.extend(emu_spawns)
            seen_coords = {
                (sp.npc_id, round(sp.position[0] / 3.0), round(sp.position[1] / 3.0))
                for sp in emu_spawns
            }
            for csp in client_spawns:
                ckey = (csp.npc_id, round(csp.position[0] / 3.0), round(csp.position[1] / 3.0))
                if ckey not in seen_coords:
                    spawns.append(csp)
        else:
            spawns = list(client_spawns)
    else:
        spawns = list(client_spawns)

    if not spawns:
        return {
            "spawns_found": 0,
            "entries": [],
            "unique_cgfs": [],
            "walker_cgfs": set(),
            "walker_routes": {},
            "provider": provider,
        }

    needed_routes = {sp.walker_id for sp in spawns if getattr(sp, "walker_id", "")}
    if static_data_dir is not None and needed_routes:
        walker_routes = parse_walker_routes(static_data_dir, needed_routes)

    templates = get_cached_npc_templates(client_path)
    provider.load_string_tables("BRA")
    provider.ensure_catalog()

    spawns_to_process = spawns[:max_npcs] if max_npcs > 0 else spawns
    entries = []
    unique_cgfs = []
    seen_cgfs = set()
    walker_cgfs = set()

    for spawn in spawns_to_process:
        npc_id = spawn.npc_id
        template = templates.get(npc_id)
        loc_name = ""
        loc_title = ""
        walk_speed = 1.5
        if template:
            name = template.name
            title = template.title
            cgf_ref = template.cgf_reference
            scale = template.scale
            category = template.category
            walk_speed = template.walk_speed if template.walk_speed > 0.2 else 1.5
            for name_cand in (template.desc_key, template.name):
                if name_cand:
                    resolved = provider.resolve_localized_string(name_cand)
                    if resolved and resolved != name_cand and not resolved.startswith("STR_"):
                        loc_name = resolved
                        break
            for title_cand in (template.title_key, template.title):
                if title_cand:
                    resolved_t = provider.resolve_localized_string(title_cand)
                    if resolved_t and resolved_t != title_cand and not resolved_t.startswith("STR_"):
                        loc_title = resolved_t
                        break
        else:
            name = f"NPC_{npc_id}"
            title = ""
            cgf_ref = DEFAULT_HUMANOID_MODELS["DM"] if ("df" in map_name or "dc" in map_name) else DEFAULT_HUMANOID_MODELS["LM"]
            scale = 1.0
            category = "npc"

        display_name = loc_name if loc_name else (name if not name.startswith("STR_") else f"NPC_{npc_id}")
        display_title = loc_title if loc_title else (title if not title.startswith("STR_") else "")

        if category == "monster" and not import_monsters:
            continue
        if category == "ambient" and not import_ambient:
            continue
        if category in ("npc", "shugo") and not import_friendly:
            continue

        is_object_prop = any(
            tok in name.lower()
            for tok in ("stone", "sack", "box", "pouch", "chest", "door", "gate", "tomb")
        )
        if not cgf_ref and category in ("npc", "friendly") and not is_object_prop:
            if "df" in map_name or "dc" in map_name:
                cgf_ref = DEFAULT_HUMANOID_MODELS["DM"]
            else:
                cgf_ref = DEFAULT_HUMANOID_MODELS["LM"]
        elif not cgf_ref and template and template.name:
            name_low = template.name.lower()
            for known_tok, known_cgf in KNOWN_MONSTER_MODELS.items():
                if known_tok in name_low:
                    cgf_ref = known_cgf
                    break
            if not cgf_ref:
                clean_tok = name_low.replace("str_npc_", "").strip("_")
                for prefix_dir in ("objects/npc/monster/", "objects/monster/", "objects/npc/"):
                    for ext in (".cgf", ".cga"):
                        cand_ref = f"{prefix_dir}{clean_tok}/{clean_tok}{ext}"
                        if provider.catalog.find_entry(cand_ref) is not None:
                            cgf_ref = cand_ref
                            break
                    if cgf_ref:
                        break

        norm_ref = cgf_ref.replace("\\", "/").strip().lstrip("/").lower() if cgf_ref else ""
        if norm_ref and norm_ref not in seen_cgfs:
            seen_cgfs.add(norm_ref)
            unique_cgfs.append(norm_ref)
        if norm_ref and getattr(spawn, "walker_id", ""):
            walker_cgfs.add(norm_ref)

        entries.append((spawn, name, display_name, display_title, scale, category, cgf_ref, norm_ref, walk_speed))

    return {
        "spawns_found": len(spawns),
        "entries": entries,
        "unique_cgfs": unique_cgfs,
        "walker_cgfs": walker_cgfs,
        "walker_routes": walker_routes,
        "provider": provider,
    }


def _parse_npc_cgf_chunk(
    provider: AionClientProvider,
    cgf_refs: List[str],
    animate_npcs: bool,
    cancel_event=None,
    walker_cgfs: Optional[set] = None,
) -> Dict[str, dict]:
    """Extracts & parses a small chunk of NPC CGFs (plus optional idle/walk CAF) off the main thread."""
    parsed_map: Dict[str, dict] = {}
    walker_set = walker_cgfs or set()
    for norm_ref in cgf_refs:
        if cancel_event is not None and cancel_event.is_set():
            break
        cgf_bytes = provider.resolve_cgf_bytes(norm_ref)
        if not cgf_bytes:
            continue
        try:
            cgf = get_cgf(io.BytesIO(cgf_bytes))
        except Exception as exc:
            print(f"[AION NPC] Failed parsing CGF bytes for {norm_ref}: {exc}")
            continue

        caf_parsed = None
        walk_caf_parsed = None
        if animate_npcs and cgf.get("bone_names") and cgf.get("bone_initial_pos"):
            try:
                _, resolved_caf = provider.resolve_animation_asset(norm_ref, preferred_kind="idle")
                if resolved_caf:
                    parsed_idle = parse_caf(resolved_caf)
                    if parsed_idle and parsed_idle.get("controllers"):
                        caf_parsed = parsed_idle
            except Exception:
                pass
            if norm_ref in walker_set:
                try:
                    _, resolved_walk = provider.resolve_animation_asset(norm_ref, preferred_kind="walk")
                    if resolved_walk:
                        parsed_walk = parse_caf(resolved_walk)
                        if parsed_walk and parsed_walk.get("controllers"):
                            walk_caf_parsed = parsed_walk
                except Exception:
                    pass
        parsed_map[norm_ref] = {
            "cgf": cgf,
            "caf_parsed": caf_parsed,
            "walk_caf_parsed": walk_caf_parsed,
        }
    return parsed_map


def _build_merged_static_npc_mesh(cgf: dict, mesh_name: str) -> Optional[bpy.types.Mesh]:
    """Combines all valid mesh chunks inside an NPC CGF into one lightweight static Mesh datablock."""
    nodes = cgf.get("nodes", {}) or {}
    combined_verts: List[Tuple[float, float, float]] = []
    combined_faces: List[Tuple[int, ...]] = []

    for n_data in nodes.values():
        if not isinstance(n_data, dict):
            continue
        mesh_chunk = n_data.get("mesh")
        if not mesh_chunk:
            continue
        verts_pos = mesh_chunk.get("vertices", {}).get("position", [])
        faces_v = mesh_chunk.get("faces", {}).get("v", [])
        if not verts_pos or not faces_v:
            continue
        v_offset = len(combined_verts)
        combined_verts.extend(verts_pos)
        if v_offset == 0:
            combined_faces.extend(faces_v)
        else:
            combined_faces.extend(tuple(idx + v_offset for idx in face) for face in faces_v)

    if not combined_verts or not combined_faces:
        return None

    m_data = bpy.data.meshes.new(mesh_name)
    m_data.from_pydata(combined_verts, [], combined_faces)
    m_data.update(calc_edges=False)
    return m_data


def iter_create_world_npcs(
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
    import_nameplates: bool = True,
    max_npcs: int = 0,
    disable_shadows: bool = True,
    batch_size: int = 8,
    executor: Optional[ThreadPoolExecutor] = None,
    cancel_event=None,
    terrain_grid: Optional[tuple] = None,
    emulator_data_dir: Optional[Path | str] = None,
):
    """
    Strictly linear, non-blocking generator for authoritative NPC loading:
      Stage A (async worker): read & parse spawns + templates + walker routes + PT-BR string tables
      Stage B (async worker chunks): extract & parse unique NPC CGF/CAF bytes (idle & walk)
      Stage C (main thread): build mesh/rig templates cleanly (1 by 1)
      Stage D (main thread): place NPC instances, cyclic walk paths, and upright PT-BR nameplates
    Yields `(local_frac, status_message)` in `[0.0, 1.0]` and returns `NpcImportResult`.
    """
    level_path = Path(level_dir).resolve()
    client_path = Path(client_root).resolve()
    emu_path = Path(emulator_data_dir).resolve() if emulator_data_dir else None
    map_name = _get_map_name_from_level_dir(level_path)

    if import_models is not None:
        load_models = import_models

    target_parent = parent_collection or root_collection
    if target_parent is None:
        target_parent = context.scene.collection

    own_executor = executor is None
    worker = ThreadPoolExecutor(max_workers=1) if own_executor else executor
    provider = None

    try:
        # Stage A: Offload World.pak / emulator XML / npcs.pak / L10N BRA parsing off main thread
        fut_meta = worker.submit(
            _prepare_npc_stage_data,
            level_path,
            client_path,
            map_name,
            import_monsters=import_monsters,
            import_friendly=import_friendly,
            import_ambient=import_ambient,
            max_npcs=max_npcs,
            emulator_data_dir=emu_path,
        )
        while not fut_meta.done():
            if cancel_event is not None and cancel_event.is_set():
                return NpcImportResult()
            yield (0.05, "Lendo spawns, rotas e nomes PT-BR de NPCs em segundo plano...")
        stage_data = fut_meta.result()

        spawns_found = stage_data["spawns_found"]
        entries = stage_data["entries"]
        unique_cgfs = stage_data["unique_cgfs"]
        walker_cgfs = stage_data.get("walker_cgfs", set())
        walker_routes = stage_data.get("walker_routes", {})
        provider = stage_data["provider"]

        if not spawns_found or not entries:
            return NpcImportResult(spawns_found=spawns_found, spawns_placed=0)

        # Stage B: Extract & parse unique NPC models linearly in small worker chunks
        parsed_cgf_map: Dict[str, dict] = {}
        if load_models and unique_cgfs:
            chunk_n = 6
            total_u = len(unique_cgfs)
            for start in range(0, total_u, chunk_n):
                if cancel_event is not None and cancel_event.is_set():
                    return NpcImportResult(spawns_found=spawns_found, spawns_placed=0)
                chunk_refs = unique_cgfs[start : start + chunk_n]
                pct_msg = f"Extraindo modelos de NPCs ({min(start + len(chunk_refs), total_u)}/{total_u})..."
                frac = 0.15 + 0.30 * (start / max(1, total_u))
                fut_chunk = worker.submit(
                    _parse_npc_cgf_chunk,
                    provider,
                    chunk_refs,
                    animate_npcs,
                    cancel_event,
                    walker_cgfs,
                )
                while not fut_chunk.done():
                    if cancel_event is not None and cancel_event.is_set():
                        return NpcImportResult(spawns_found=spawns_found, spawns_placed=0)
                    yield (frac, pct_msg)
                parsed_cgf_map.update(fut_chunk.result())

        # Free PAK archive handles before Blender mesh phase
        if provider is not None:
            provider.close()

        # Stage C: Prepare collections & terrain inverse matrix on main thread
        if target_parent.name == "NPCS":
            npcs_root_col = target_parent
        else:
            npcs_root_col = _get_or_create_collection(target_parent, "NPCS")

        friendly_col = _get_or_create_collection(npcs_root_col, "NPCs - Friendly")
        monsters_col = _get_or_create_collection(npcs_root_col, "Monsters & Hostiles")
        ambient_col = _get_or_create_collection(npcs_root_col, "NPCs - Ambient Fauna")
        nameplates_col = _get_or_create_collection(npcs_root_col, "NPC_NAMES")

        yield (0.44, "Preparando referências do terreno para NPCs...")
        needs_snap = bool(walker_routes) or any(
            (not sp.has_explicit_z or abs(sp.position[2]) < 0.001)
            for sp, *_ in entries
        )
        active_grid = (
            terrain_grid
            if (needs_snap and terrain_grid is not None)
            else (_extract_terrain_height_grid(terrain_obj) if needs_snap else None)
        )
        terrain_bvh, terrain_inv_mat = (None, None)
        if needs_snap and active_grid is None and terrain_obj is not None and terrain_obj.type == "MESH":
            terrain_bvh, terrain_inv_mat = _build_terrain_bvh(terrain_obj)

        static_meshes: Dict[str, bpy.types.Mesh] = {}
        animated_data: Dict[str, Tuple[bpy.types.Armature, bpy.types.Object, Optional[dict], Optional[dict], List[str], List[Dict[str, Any]]]] = {}
        model_heights: Dict[str, float] = {}
        action_cache: Dict[Tuple[str, str], Optional[bpy.types.Action]] = {}

        # Build unique Blender mesh/rig templates 1 at a time (yielding between models)
        if load_models and parsed_cgf_map:
            ref_to_sample_name = {}
            for _, name, _, _, _, _, _, norm_ref, _ in entries:
                if norm_ref and norm_ref not in ref_to_sample_name:
                    ref_to_sample_name[norm_ref] = name

            parsed_items = list(parsed_cgf_map.items())
            for idx_m, (norm_ref, bundle) in enumerate(parsed_items, start=1):
                cgf = bundle["cgf"]
                caf_parsed = bundle.get("caf_parsed")
                walk_caf_parsed = bundle.get("walk_caf_parsed")
                npc_name_clean = ref_to_sample_name.get(norm_ref, Path(norm_ref).stem)

                bone_names = cgf.get("bone_names", [])
                bone_anim = cgf.get("bone_anim", [])
                bone_initial_pos = cgf.get("bone_initial_pos", [])

                mesh_chunk = None
                for n_data in (cgf.get("nodes") or {}).values():
                    if isinstance(n_data, dict) and n_data.get("mesh"):
                        mesh_chunk = n_data["mesh"]
                        break

                if mesh_chunk:
                    verts_pos = mesh_chunk.get("vertices", {}).get("position", [])
                    faces_v = mesh_chunk.get("faces", {}).get("v", [])
                    skin_weights = mesh_chunk.get("skin_weights", [])

                    if verts_pos:
                        zs = [v[2] for v in verts_pos]
                        model_heights[norm_ref] = max(0.8, max(zs) - min(zs))

                    if verts_pos and faces_v:
                        if animate_npcs and bone_names and bone_initial_pos:
                            try:
                                arm_data = build_npc_armature(
                                    npc_name_clean, bone_names, bone_initial_pos, bone_anim, collection=None
                                )
                                if isinstance(arm_data, bpy.types.Object):
                                    arm_data = arm_data.data
                                if arm_data is not None:
                                    m_data = bpy.data.meshes.new(f"{npc_name_clean}_Mesh")
                                    m_data.from_pydata(verts_pos, [], faces_v)
                                    m_data.update(calc_edges=False)
                                    tpl_mesh_obj = bpy.data.objects.new(
                                        f"__aion_npc_tpl_{npc_name_clean}_{idx_m}__", m_data
                                    )
                                    apply_skin_weights(tpl_mesh_obj, bone_names, skin_weights, rig_obj=None)
                                    arm_mod = tpl_mesh_obj.modifiers.new(name="Aion_Armature", type="ARMATURE")
                                    arm_mod.use_vertex_groups = True
                                    if disable_shadows and hasattr(tpl_mesh_obj, "visible_shadow"):
                                        try:
                                            tpl_mesh_obj.visible_shadow = False
                                        except (AttributeError, TypeError):
                                            pass
                                    animated_data[norm_ref] = (
                                        arm_data,
                                        tpl_mesh_obj,
                                        caf_parsed,
                                        walk_caf_parsed,
                                        bone_names,
                                        bone_anim,
                                    )
                            except Exception as exc:
                                print(f"[AION NPC] Skeleton build failed for {norm_ref}, using static mesh: {exc}")

                        if norm_ref not in animated_data:
                            static_m = _build_merged_static_npc_mesh(cgf, f"{npc_name_clean}_StaticMesh")
                            if static_m is not None:
                                static_meshes[norm_ref] = static_m

                yield (
                    0.45 + 0.15 * (idx_m / max(1, len(parsed_items))),
                    f"Construindo malha de NPC {idx_m}/{len(parsed_items)}...",
                )

        # Stage D: Place NPC instances in small batches
        placed_count = 0
        instances_created = 0
        animated_count = 0
        walking_routes_applied = 0
        missing_models = 0
        max_walk_end_frame = 0
        scene_fps = float(getattr(context.scene.render, "fps", 24) or 24)
        total_entries = len(entries)
        step_batch = max(1, int(batch_size))

        for idx_e, (spawn, name, display_name, title, scale, category, cgf_ref, norm_ref, walk_speed) in enumerate(entries, start=1):
            if cancel_event is not None and cancel_event.is_set():
                break
            if category == "monster":
                target_col = monsters_col
            elif category == "ambient":
                target_col = ambient_col
            else:
                target_col = friendly_col

            x, y, z = spawn.position
            if not spawn.has_explicit_z or abs(z) < 0.001:
                z = _snap_z_to_terrain(
                    x,
                    y,
                    terrain_obj,
                    default_z=z,
                    terrain_bvh=terrain_bvh,
                    terrain_inv_mat=terrain_inv_mat,
                    terrain_grid=active_grid,
                )

            yaw_rad = math.radians(spawn.heading_degrees)
            obj_name = f"{name}_{spawn.npc_id}_{idx_e:04d}"
            route = walker_routes.get(getattr(spawn, "walker_id", ""))
            has_walk_route = bool(animate_npcs and route is not None and len(route.steps) >= 2)
            bbox_h = model_heights.get(norm_ref, 1.85) * float(scale)

            target_root_obj = None

            if load_models and animate_npcs and norm_ref in animated_data:
                arm_data, tpl_mesh_obj, caf_parsed, walk_caf_parsed, b_names, b_anim = animated_data[norm_ref]
                rig_inst = bpy.data.objects.new(f"{obj_name}_Rig", arm_data)
                mesh_inst = tpl_mesh_obj.copy()
                mesh_inst.name = obj_name
                for mod in mesh_inst.modifiers:
                    if mod.type == "ARMATURE":
                        mod.object = rig_inst
                        break

                target_col.objects.link(rig_inst)
                target_col.objects.link(mesh_inst)

                mesh_inst.parent = rig_inst

                pose_kind = "walk" if (has_walk_route and walk_caf_parsed) else "idle"
                use_caf = walk_caf_parsed if pose_kind == "walk" else caf_parsed
                act_key = (norm_ref, pose_kind)
                if act_key not in action_cache:
                    act = None
                    if use_caf:
                        act_name = f"{name}_{'WalkPose' if pose_kind == 'walk' else 'Idle'}"
                        caf_gen = iter_apply_caf_animation(
                            rig_inst,
                            use_caf,
                            b_names,
                            b_anim,
                            act_name,
                            bones_per_yield=6,
                        )
                        try:
                            while True:
                                if cancel_event is not None and cancel_event.is_set():
                                    return NpcImportResult(
                                        spawns_found=spawns_found,
                                        spawns_placed=placed_count,
                                        animated_rigs_created=animated_count,
                                        models_loaded=len(static_meshes) + len(animated_data),
                                        missing_models=missing_models,
                                        instances_created=instances_created,
                                        walking_routes_applied=walking_routes_applied,
                                    )
                                b_done, b_tot = next(caf_gen)
                                yield (
                                    0.60 + 0.39 * (idx_e / max(1, total_entries)),
                                    f"Animação CAF {name} ({b_done}/{b_tot})...",
                                )
                        except StopIteration as exc_caf:
                            act = exc_caf.value
                    action_cache[act_key] = act
                else:
                    act = action_cache[act_key]

                if act:
                    rig_inst.animation_data_create()
                    rig_inst.animation_data.action = act
                    if has_walk_route and hasattr(rig_inst.animation_data, "nla_tracks"):
                        try:
                            nla_t = rig_inst.animation_data.nla_tracks.new()
                            nla_t.name = "AION_SkeletalCycle"
                            strip = nla_t.strips.new(act.name, 1, act)
                            strip.repeat = 500.0
                        except Exception:
                            pass

                rig_inst.location = (x, y, z)
                rig_inst.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
                rig_inst.scale = (scale, scale, scale)

                rig_inst["aion_source_type"] = "npc_rig"
                rig_inst["aion_npc_id"] = spawn.npc_id
                rig_inst["aion_npc_name"] = display_name
                rig_inst["aion_orig_pos"] = [x, y, z]
                mesh_inst["aion_source_type"] = "npc"
                mesh_inst["aion_npc_id"] = spawn.npc_id
                mesh_inst["aion_npc_name"] = display_name
                mesh_inst["aion_orig_pos"] = [x, y, z]

                target_root_obj = rig_inst
                placed_count += 1
                instances_created += 1
                animated_count += 1

            elif load_models and norm_ref in static_meshes:
                mesh_data = static_meshes[norm_ref]
                obj = bpy.data.objects.new(obj_name, mesh_data)
                obj.location = (x, y, z)
                obj.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
                obj.scale = (scale, scale, scale)
                if disable_shadows and hasattr(obj, "visible_shadow"):
                    try:
                        obj.visible_shadow = False
                    except (AttributeError, TypeError):
                        pass

                obj["aion_source_type"] = "npc"
                obj["aion_npc_id"] = spawn.npc_id
                obj["aion_npc_name"] = display_name
                obj["aion_orig_pos"] = [x, y, z]
                if title:
                    obj["aion_npc_title"] = title
                if cgf_ref:
                    obj["aion_cgf_reference"] = cgf_ref

                target_col.objects.link(obj)
                target_root_obj = obj
                placed_count += 1
                instances_created += 1

            else:
                obj = bpy.data.objects.new(obj_name, None)
                obj.empty_display_type = "SINGLE_ARROW" if category != "monster" else "SPHERE"
                obj.location = (x, y, z)
                obj.rotation_euler = Euler((0.0, 0.0, yaw_rad), "XYZ")
                obj.scale = (scale, scale, scale)

                obj["aion_source_type"] = "npc_marker"
                obj["aion_npc_id"] = spawn.npc_id
                obj["aion_npc_name"] = display_name
                obj["aion_orig_pos"] = [x, y, z]
                if title:
                    obj["aion_npc_title"] = title
                if cgf_ref:
                    obj["aion_cgf_reference"] = cgf_ref

                target_col.objects.link(obj)
                target_root_obj = obj
                placed_count += 1
                instances_created += 1
                missing_models += 1

            if has_walk_route and target_root_obj is not None:
                try:
                    end_f = _apply_npc_walk_route(
                        target_root_obj,
                        route,
                        walk_speed,
                        f"{spawn.npc_id}_{idx_e:04d}",
                        (x, y, z),
                        terrain_obj,
                        terrain_bvh,
                        terrain_inv_mat,
                        active_grid,
                        fps=scene_fps,
                    )
                    if end_f > 0:
                        walking_routes_applied += 1
                        max_walk_end_frame = max(max_walk_end_frame, end_f)
                except Exception as exc_w:
                    print(f"[AION NPC] Walker route failed for {spawn.npc_id}: {exc_w}")

            if import_nameplates and target_root_obj is not None:
                _create_npc_nameplate(
                    nameplates_col,
                    target_root_obj,
                    spawn.npc_id,
                    display_name,
                    title,
                    scale,
                    category,
                    yaw_rad=yaw_rad,
                    has_walker_anim=has_walk_route,
                    bbox_height=bbox_h,
                    disable_shadows=disable_shadows,
                )

            if idx_e % step_batch == 0 and idx_e < total_entries:
                yield (
                    0.60 + 0.39 * (idx_e / max(1, total_entries)),
                    f"Posicionando NPCs {idx_e}/{total_entries}...",
                )

        if max_walk_end_frame > 0:
            try:
                context.scene.frame_end = max(int(context.scene.frame_end), int(max_walk_end_frame), 1200)
            except Exception:
                pass

        # Prune empty subcollections in NPCS
        for sub in (friendly_col, monsters_col, ambient_col, nameplates_col):
            if len(sub.objects) == 0 and len(sub.children) == 0:
                if sub.name in npcs_root_col.children.keys():
                    npcs_root_col.children.unlink(sub)
                bpy.data.collections.remove(sub)

        return NpcImportResult(
            spawns_found=spawns_found,
            spawns_placed=placed_count,
            animated_rigs_created=animated_count,
            models_loaded=len(static_meshes) + len(animated_data),
            missing_models=missing_models,
            instances_created=instances_created,
            walking_routes_applied=walking_routes_applied,
        )
    finally:
        for obj in list(bpy.data.objects):
            if obj.name.startswith("__aion_npc_tpl_"):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
        if provider is not None:
            try:
                provider.close()
            except Exception:
                pass
        if own_executor:
            worker.shutdown(wait=False, cancel_futures=True)


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
    import_nameplates: bool = True,
    max_npcs: int = 0,
    disable_shadows: bool = True,
    emulator_data_dir: Optional[Path | str] = None,
) -> NpcImportResult:
    """Synchronous wrapper around iter_create_world_npcs for headless scripts and tests."""
    import time

    gen = iter_create_world_npcs(
        context,
        level_dir,
        client_root,
        root_collection=root_collection,
        parent_collection=parent_collection,
        terrain_obj=terrain_obj,
        load_models=load_models,
        import_models=import_models,
        animate_npcs=animate_npcs,
        import_monsters=import_monsters,
        import_friendly=import_friendly,
        import_ambient=import_ambient,
        import_nameplates=import_nameplates,
        max_npcs=max_npcs,
        disable_shadows=disable_shadows,
        batch_size=100000,
        emulator_data_dir=emulator_data_dir,
    )
    last_state = None
    try:
        while True:
            state = next(gen)
            if state == last_state:
                time.sleep(0.002)
            last_state = state
    except StopIteration as exc:
        return exc.value
