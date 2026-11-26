import math
from dataclasses import dataclass

from formats.level import LevelInfo


DEFAULT_WATER_NAME = "Aion Water"
DEFAULT_WATER_XY_SCALE = 2.0


@dataclass(frozen=True)
class WaterPlaneResult:
    created: bool
    object: object | None
    mesh: object | None
    water_level: float | None
    width: float
    height: float
    xy_scale: float
    skip_reason: str | None


def create_water_plane(
    context,
    level_info: LevelInfo,
    xy_scale: float = DEFAULT_WATER_XY_SCALE,
    name: str = DEFAULT_WATER_NAME,
    *,
    subdivide_water: bool = False,
    disable_shadows: bool = True,
    target_collection=None,
) -> WaterPlaneResult:
    if level_info.water_level is None:
        return _skipped_result(xy_scale, "LevelInfo WaterLevel is missing")
    if level_info.heightmap_x_size is None or level_info.heightmap_y_size is None:
        return _skipped_result(xy_scale, "LevelInfo heightmap dimensions are missing")
    if not math.isfinite(xy_scale) or xy_scale <= 0:
        raise ValueError("water XY scale must be finite and positive")
    if not math.isfinite(level_info.water_level):
        return _skipped_result(xy_scale, "LevelInfo WaterLevel is not finite")

    width = float(level_info.heightmap_x_size) * xy_scale
    height = float(level_info.heightmap_y_size) * xy_scale
    if width <= 0 or height <= 0:
        return _skipped_result(xy_scale, "LevelInfo heightmap dimensions must be positive")

    import bpy

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        (
            (0.0, 0.0, 0.0),
            (width, 0.0, 0.0),
            (width, height, 0.0),
            (0.0, height, 0.0),
        ),
        (),
        ((0, 1, 2, 3),),
    )
    mesh.update(calc_edges=False)

    # Assign UVMap coordinates
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_coords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for loop_idx, loop in enumerate(mesh.loops):
        uv_layer.data[loop_idx].uv = uv_coords[loop_idx % 4]

    water_object = bpy.data.objects.new(name, mesh)
    water_object.location.z = level_info.water_level
    if disable_shadows and hasattr(water_object, "visible_shadow"):
        try:
            water_object.visible_shadow = False
        except (AttributeError, TypeError):
            pass

    if subdivide_water:
        # Subdivide only when procedural vertex wave animation is explicitly enabled
        subdiv = water_object.modifiers.new("Aion_WaterSubdiv", type="SUBSURF")
        subdiv.subdivision_type = "SIMPLE"
        subdiv.levels = 1
        subdiv.render_levels = 1

    dest_col = target_collection if target_collection is not None else context.scene.collection
    dest_col.objects.link(water_object)

    return WaterPlaneResult(
        created=True,
        object=water_object,
        mesh=mesh,
        water_level=level_info.water_level,
        width=width,
        height=height,
        xy_scale=xy_scale,
        skip_reason=None,
    )


def _skipped_result(xy_scale: float, reason: str) -> WaterPlaneResult:
    return WaterPlaneResult(
        created=False,
        object=None,
        mesh=None,
        water_level=None,
        width=0.0,
        height=0.0,
        xy_scale=xy_scale,
        skip_reason=reason,
    )


def create_water_volumes(
    context,
    mission_xml_path,
    client_root,
    *,
    water_material=None,
    target_collection=None,
    disable_shadows: bool = True,
    simple_shaders: bool = True,
) -> int:
    """
    Imports `<Object Type="WaterVolume">` lakes, swamps, and rivers from `mission_mission0.xml`
    (via WaterGeometry CGF if available or fallback polygon mesh from Points) into `target_collection`.
    """
    from pathlib import Path
    import bpy
    from formats.level.liquid_surface import parse_water_volumes
    from core.pak_engine import get_pak_resolver
    from importers.cgf_importer import iter_load_cgf

    mission_xml_file = Path(mission_xml_path)
    if mission_xml_file.is_dir():
        mission_xml_file = mission_xml_file / "mission_mission0.xml"
    volumes = parse_water_volumes(mission_xml_file)
    if not volumes:
        return 0

    dest_col = target_collection if target_collection is not None else context.scene.collection
    resolver = get_pak_resolver(client_root)
    created = 0

    for idx, vol in enumerate(volumes):
        v_name = vol["name"]
        water_geom = vol.get("water_geometry") or ""
        points = vol.get("points") or []
        pos = vol.get("pos") or (0.0, 0.0, 0.0)
        obj_created = False

        if water_geom and resolver is not None:
            resolved = resolver.resolve_resource(water_geom)
            if resolved is not None and resolved.is_file():
                try:
                    tmp_col = bpy.data.collections.new(f"__wv_tmp_{idx}__")
                    gen = iter_load_cgf(
                        context,
                        str(resolved),
                        import_mode="VISUAL",
                        client_root=str(client_root),
                        simple_shaders=simple_shaders,
                        optimize_material_preview=True,
                        target_collection=tmp_col,
                        link_to_scene=False,
                        time_slice_s=9999.0,
                    )
                    try:
                        while True:
                            next(gen)
                    except StopIteration as exc_g:
                        res_status, _ = exc_g.value
                    if res_status == {"FINISHED"}:
                        for wobj in list(tmp_col.objects):
                            tmp_col.objects.unlink(wobj)
                            if wobj.type == "MESH" and wobj.data is not None and len(wobj.data.materials) == 0 and water_material is not None:
                                wobj.data.materials.append(water_material)
                            if disable_shadows and hasattr(wobj, "visible_shadow"):
                                try:
                                    wobj.visible_shadow = False
                                except (AttributeError, TypeError):
                                    pass
                            wobj["aion_source_type"] = "water_volume"
                            dest_col.objects.link(wobj)
                            created += 1
                            obj_created = True
                    bpy.data.collections.remove(tmp_col)
                except Exception:
                    try:
                        if tmp_col.name in bpy.data.collections:
                            bpy.data.collections.remove(tmp_col)
                    except Exception:
                        pass

        if not obj_created and len(points) >= 3:
            try:
                avg_z = sum(p[2] for p in points) / len(points)
                verts = [(p[0], p[1], avg_z) for p in points]
                face = tuple(range(len(verts)))
                wmesh = bpy.data.meshes.new(f"{v_name}_Mesh")
                wmesh.from_pydata(verts, (), (face,))
                wmesh.update(calc_edges=False)
                if len(wmesh.polygons) > 0:
                    uv_layer = wmesh.uv_layers.new(name="UVMap")
                    for poly in wmesh.polygons:
                        for lidx in poly.loop_indices:
                            co = wmesh.vertices[wmesh.loops[lidx].vertex_index].co
                            uv_layer.data[lidx].uv = (co.x * 0.05, co.y * 0.05)
                if water_material is not None:
                    wmesh.materials.append(water_material)
                wobj = bpy.data.objects.new(v_name, wmesh)
                if disable_shadows and hasattr(wobj, "visible_shadow"):
                    try:
                        wobj.visible_shadow = False
                    except (AttributeError, TypeError):
                        pass
                wobj["aion_source_type"] = "water_volume"
                dest_col.objects.link(wobj)
                created += 1
            except Exception:
                pass

    return created
