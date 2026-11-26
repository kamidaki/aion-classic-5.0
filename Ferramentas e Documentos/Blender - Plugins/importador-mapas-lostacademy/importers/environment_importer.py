from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree

from aion_formats.level.environment import lighting_preview_settings, resolve_level_environment


@dataclass(frozen=True)
class SkyboxImportResult:
    applied: bool
    profile: str
    reason: str = ""
    world_name: str = ""
    warnings: tuple[str, ...] = ()


def create_environment_lighting_preview(
    scene,
    level_dir,
    client_root,
    *,
    time_option="Daylight",
    sun_energy=2.0,
    ambient_strength=0.3,
    use_shadow: bool = True,
    pre_resolved_report=None,
    target_collection=None,
):
    import bpy
    from mathutils import Vector

    try:
        if any(not math.isfinite(value) or value < 0 for value in (sun_energy, ambient_strength)):
            raise ValueError("Lighting preview strengths must be finite and non-negative")
        report = (
            pre_resolved_report
            if pre_resolved_report is not None
            else resolve_level_environment(
                Path(level_dir) / "mission_mission0.xml", client_root, time_option=time_option,
            )
        )
        settings = lighting_preview_settings(report)
    except (OSError, ElementTree.ParseError, ValueError) as error:
        return SkyboxImportResult(False, time_option, f"lighting_read_error: {error}")
    source_key = str((Path(level_dir) / "mission_mission0.xml").resolve())
    warnings = (
        "static_reference_sun; active TimeEnv sun angles are not converted",
        "preview_strength_and_color_mapping; not calibrated game illumination",
        "World ambient needs indirect lighting/probes in Eevee; Sun works directly",
        settings.sun_status,
    )
    previous_world = scene.world
    base_world = previous_world
    if base_world and base_world.get("aion_environment_lighting"):
        base_world = base_world.get("aion_lighting_original_world_ref")
    world = base_world.copy() if base_world else bpy.data.worlds.new("AION Environment Lighting")
    world.name = "AION Environment Lighting"
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    outputs = [node for node in nodes if node.type == "OUTPUT_WORLD" and node.is_active_output]
    if len(outputs) != 1:
        bpy.data.worlds.remove(world)
        return SkyboxImportResult(False, time_option, "lighting_preview_requires_one_world_output")
    surface = outputs[0].inputs["Surface"]
    original = surface.links[0].from_socket if base_world and surface.is_linked else None
    if base_world and not base_world.use_nodes:
        constant = nodes.new("ShaderNodeBackground")
        constant.inputs["Color"].default_value = (*base_world.color, 1)
        original = constant.outputs[0]
    ambient = nodes.new("ShaderNodeBackground")
    ambient.name = "AION Environment Ambient"
    ambient.inputs["Color"].default_value = (*settings.ambient_color, 1)
    ambient.inputs["Strength"].default_value = ambient_strength
    rays = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    mix.name = "AION Lighting Preserve Camera Background"
    links.new(rays.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(ambient.outputs[0], mix.inputs[1])
    if original:
        links.new(original, mix.inputs[2])
    links.new(mix.outputs[0], surface)
    world["aion_environment_lighting"] = True
    if base_world:
        world["aion_lighting_original_world_ref"] = base_world
    world["aion_lighting_source"] = source_key
    world["aion_lighting_settings"] = json.dumps(asdict(settings))
    world["aion_lighting_time_option"] = json.dumps(report.selected_time_option)
    world["aion_lighting_warnings"] = json.dumps(warnings)
    matches = [obj for obj in scene.objects if obj.get("aion_environment_sun") == source_key]
    if len(matches) > 1 or any(obj.type != "LIGHT" or obj.data.type != "SUN" for obj in matches):
        bpy.data.worlds.remove(world)
        return SkyboxImportResult(False, time_option, "ambiguous_environment_sun")
    if matches and len(matches[0].users_scene) > 1:
        bpy.data.worlds.remove(world)
        return SkyboxImportResult(False, time_option, "environment_sun_shared_between_scenes")
    if settings.ray_direction is not None:
        if matches:
            sun = matches[0]
            if sun.data.users > 1:
                sun.data = sun.data.copy()
        else:
            sun = bpy.data.objects.new("AION Environment Sun", bpy.data.lights.new("AION Environment Sun", "SUN"))
            dest_col = target_collection if target_collection is not None else scene.collection
            dest_col.objects.link(sun)
        sun.rotation_mode = "QUATERNION"
        sun.rotation_quaternion = Vector(settings.ray_direction).to_track_quat("-Z", "Y")
        sun.data.color = settings.sun_color
        sun.data.energy = sun_energy
        sun.data.use_shadow = bool(use_shadow)
        sun["aion_environment_sun"] = source_key
        sun["aion_sun_ray_direction"] = settings.ray_direction
        sun["aion_sun_source"] = settings.source
        sun["aion_sun_direction_mapping"] = settings.direction_mapping
        sun["aion_sun_color_source"] = settings.color_source
        sun["aion_sun_status"] = settings.sun_status
    elif matches:
        if matches[0].data.users > 1:
            matches[0].data = matches[0].data.copy()
        matches[0].data.energy = 0
    scene.world = world
    if previous_world and previous_world.get("aion_environment_lighting") and previous_world.users == 0:
        bpy.data.worlds.remove(previous_world)
    return SkyboxImportResult(True, time_option, reason=settings.sun_status, world_name=world.name, warnings=warnings)


def skybox_coordinates(directions):
    import numpy as np

    axis_x, axis_y, axis_z = np.moveaxis(np.asarray(directions), -1, 0)
    distance = np.maximum(np.maximum(abs(axis_x), abs(axis_y)), np.maximum(axis_z, 1e-8))
    axis_x, axis_y, axis_z = axis_x / distance, axis_y / distance, axis_z / distance
    cap = axis_z >= 1
    north_south = abs(axis_y) >= abs(axis_x)
    north = north_south & (axis_y >= 0)
    south = north_south & (axis_y < 0)
    east = ~north_south & (axis_x < 0)
    field = np.where(cap, 2, np.where(south | east, 1, 0))
    coord_u = np.where(cap | north, (1 + axis_x) / 2,
                       np.where(south, (1 - axis_x) / 2,
                                np.where(east, (1 + axis_y) / 2, (1 - axis_y) / 2)))
    coord_v = np.where(cap, (1 - axis_y) / 2,
                       np.where(north_south, (1 + axis_z) / 2, (1 - axis_z) / 2))
    return field, coord_u, coord_v


def _panorama(images, width=2048):
    import numpy as np

    height = width // 2
    longitude = (0.5 - (np.arange(width, dtype=np.float32) + 0.5) / width) * (2 * np.pi)
    latitude = ((np.arange(height, dtype=np.float32) + 0.5) / height - 0.5) * np.pi
    longitude, latitude = np.meshgrid(longitude, latitude)
    directions = np.stack((
        np.cos(latitude) * np.cos(longitude),
        np.cos(latitude) * np.sin(longitude),
        np.sin(latitude),
    ), axis=-1)
    field, coord_u, coord_v = skybox_coordinates(directions)
    output = np.zeros((height, width, 4), dtype=np.float32)
    for index, image in enumerate(images):
        image_width, image_height = image.size
        pixels = np.empty(image_width * image_height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(image_height, image_width, 4)
        if not image.is_float and image.colorspace_settings.name == "sRGB":
            color = pixels[:, :, :3]
            pixels[:, :, :3] = np.where(color <= 0.04045, color / 12.92, ((color + 0.055) / 1.055) ** 2.4)
        mask = (field == index) & (latitude >= 0)
        sample_x = np.clip(coord_u[mask] * image_width - 0.5, 0, image_width - 1)
        sample_y = np.clip(coord_v[mask] * image_height - 0.5, 0, image_height - 1)
        if index != 2:
            half = image_height // 2
            sample_y = np.where(coord_v[mask] >= 0.5,
                                np.clip(sample_y, half, image_height - 1),
                                np.clip(sample_y, 0, half - 1))
        low_x, low_y = sample_x.astype(int), sample_y.astype(int)
        high_x, high_y = np.minimum(low_x + 1, image_width - 1), np.minimum(low_y + 1, image_height - 1)
        weight_x, weight_y = (sample_x - low_x)[:, None], (sample_y - low_y)[:, None]
        bottom = pixels[low_y, low_x] * (1 - weight_x) + pixels[low_y, high_x] * weight_x
        top = pixels[high_y, low_x] * (1 - weight_x) + pixels[high_y, high_x] * weight_x
        output[mask] = bottom * (1 - weight_y) + top * weight_y
    output[:, :, 3] = (latitude >= 0).astype(np.float32)
    if not np.isfinite(output).all():
        raise ValueError("Skybox contains non-finite pixels")
    return output


def create_skybox_preview(scene, level_dir, client_root, *, time_option="Daylight", pre_resolved_report=None):
    import bpy

    try:
        report = (
            pre_resolved_report
            if pre_resolved_report is not None
            else resolve_level_environment(
                Path(level_dir) / "mission_mission0.xml", client_root, time_option=time_option,
            )
        )
    except (OSError, ElementTree.ParseError, ValueError) as error:
        return SkyboxImportResult(False, "", f"environment_read_error: {error}")
    if report.status != "resolved":
        return SkyboxImportResult(False, report.skybox_reference, report.status)
    if report.profile_parameters.get("use_skybox") != "1":
        return SkyboxImportResult(False, report.skybox_reference, "skybox_disabled_in_profile")
    textures = report.textures[:3]
    if any(texture.status != "resolved" for texture in textures):
        return SkyboxImportResult(False, report.skybox_reference, "missing_required_skybox_texture")
    signature = hashlib.sha256(json.dumps([
        "cryengine_upper_hemisphere_v1", report.source_file, report.skybox_reference,
        [(item.resolved_path, Path(item.resolved_path).stat().st_mtime_ns) for item in textures],
    ]).encode()).hexdigest()
    warnings = (
        "camera_background_only; existing illumination preserved",
        "reference_orientation; Aion angle/stretch not applied",
        "lower_hemisphere, clouds, atmosphere, sun and fog not transferred",
    )
    if scene.world and scene.world.get("aion_skybox_signature") == signature:
        return SkyboxImportResult(True, report.skybox_reference, world_name=scene.world.name, warnings=warnings)
    images = []
    loaded_images = []
    panorama = None
    world = None
    try:
        for texture in textures:
            image = bpy.data.images.load(texture.resolved_path, check_existing=False)
            loaded_images.append(image)
            image.alpha_mode = "NONE"
            if min(image.size) < 2 or image.size[0] != image.size[1]:
                return SkyboxImportResult(False, report.skybox_reference, "unsupported_skybox_dimensions")
            images.append(image)
        pixels = _panorama(images)
        panorama = bpy.data.images.new("AION_Skybox_Preview", width=pixels.shape[1], height=pixels.shape[0], float_buffer=True)
        panorama.colorspace_settings.name = "Non-Color"
        panorama.pixels.foreach_set(pixels.ravel())
        panorama.pack()
        previous_world = scene.world
        base_world = previous_world
        if base_world and base_world.get("aion_skybox_signature"):
            base_world = base_world.get("aion_skybox_original_world_ref")
        world = base_world.copy() if base_world else bpy.data.worlds.new("AION_Skybox_Preview")
        world.name = "AION_Skybox_Preview"
        world.use_nodes = True
        nodes, links = world.node_tree.nodes, world.node_tree.links
        outputs = [node for node in nodes if node.type == "OUTPUT_WORLD" and node.is_active_output]
        if len(outputs) != 1:
            raise ValueError("Expected one active World Output for skybox preview")
        surface = outputs[0].inputs["Surface"]
        original = surface.links[0].from_socket if base_world and surface.is_linked else None
        if base_world and not base_world.use_nodes:
            constant = nodes.new("ShaderNodeBackground")
            constant.inputs["Color"].default_value = (*base_world.color, 1)
            original = constant.outputs[0]
        texture_node = nodes.new("ShaderNodeTexEnvironment")
        texture_node.name = "AION Skybox Texture"
        texture_node.image = panorama
        geometry = nodes.new("ShaderNodeNewGeometry")
        direction = nodes.new("ShaderNodeVectorMath")
        direction.operation = "SCALE"
        direction.inputs[3].default_value = -1
        links.new(geometry.outputs["Incoming"], direction.inputs[0])
        links.new(direction.outputs["Vector"], texture_node.inputs["Vector"])
        components = nodes.new("ShaderNodeSeparateXYZ")
        links.new(direction.outputs["Vector"], components.inputs[0])
        upper_hemisphere = nodes.new("ShaderNodeMath")
        upper_hemisphere.operation = "GREATER_THAN"
        upper_hemisphere.inputs[1].default_value = 0
        links.new(components.outputs["Z"], upper_hemisphere.inputs[0])
        background = nodes.new("ShaderNodeBackground")
        links.new(texture_node.outputs["Color"], background.inputs["Color"])
        rays = nodes.new("ShaderNodeLightPath")
        camera_mask = nodes.new("ShaderNodeMath")
        camera_mask.operation = "MULTIPLY"
        links.new(rays.outputs["Is Camera Ray"], camera_mask.inputs[0])
        links.new(upper_hemisphere.outputs[0], camera_mask.inputs[1])
        mix = nodes.new("ShaderNodeMixShader")
        mix.name = "AION Camera Skybox"
        links.new(camera_mask.outputs[0], mix.inputs[0])
        if original:
            links.new(original, mix.inputs[1])
        links.new(background.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], surface)
        world["aion_skybox_signature"] = signature
        world["aion_skybox_original_world"] = base_world.name if base_world else ""
        if base_world:
            world["aion_skybox_original_world_ref"] = base_world
        world["aion_skybox_profile"] = report.skybox_reference
        world["aion_skybox_textures"] = json.dumps([item.resolved_path for item in textures])
        world["aion_skybox_warnings"] = json.dumps(warnings)
        world["aion_environment_source"] = json.dumps(report.sections)
        world["aion_time_option"] = json.dumps(report.selected_time_option)
        scene.world = world
        if previous_world and previous_world.get("aion_skybox_signature") and previous_world.users == 0:
            old_texture = previous_world.node_tree.nodes.get("AION Skybox Texture")
            old_image = old_texture.image if old_texture else None
            bpy.data.worlds.remove(previous_world)
            if old_image and old_image.users == 0:
                bpy.data.images.remove(old_image)
    except (RuntimeError, OSError, ValueError) as error:
        if world is not None and world.users == 0:
            bpy.data.worlds.remove(world)
        if panorama is not None and panorama.users == 0:
            bpy.data.images.remove(panorama)
        return SkyboxImportResult(False, report.skybox_reference, f"skybox_preview_error: {error}")
    finally:
        for image in loaded_images:
            if image.users == 0:
                bpy.data.images.remove(image)
    return SkyboxImportResult(True, report.skybox_reference, world_name=world.name, warnings=warnings)


def create_physical_skydome(
    context,
    client_root: str | Path,
    *,
    center: tuple[float, float, float] = (1536.0, 1536.0, 100.0),
    radius: float = 3500.0,
    animate_clouds: bool = False,
    override_viewport_shading: bool = False,
):
    """
    Creates or imports an authentic Aion physical SkyDome mesh centered over the map
    with an unlit celestial sky and cloud gradient shader.
    """
    import bpy
    from core.pak_engine import get_pak_resolver

    resolver = get_pak_resolver(client_root)
    skydome_cgf = resolver.resolve_resource("skydome.cgf") if resolver else None

    col_name = "Aion Sky & Environment"
    sky_col = bpy.data.collections.get(col_name)
    if not sky_col:
        sky_col = bpy.data.collections.new(col_name)
        context.scene.collection.children.link(sky_col)

    existing = bpy.data.objects.get("AION_SkyDome")
    if existing:
        return existing

    sky_obj = None
    if skydome_cgf and skydome_cgf.is_file():
        try:
            from importers.cgf_importer import load
            load(context, skydome_cgf, client_root=str(client_root))
            sky_obj = bpy.data.objects.get("SkyDome")
            if sky_obj:
                sky_obj.name = "AION_SkyDome"
                for c in bpy.data.collections:
                    if sky_obj.name in c.objects and c != sky_col:
                        try:
                            c.objects.unlink(sky_obj)
                        except Exception:
                            pass
                if sky_obj.name not in sky_col.objects:
                    sky_col.objects.link(sky_obj)
        except Exception:
            sky_obj = None

    if not sky_obj:
        # Procedural hemisphere dome fallback
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(
            bm,
            u_segments=32,
            v_segments=16,
            radius=radius,
        )
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new("AION_SkyDome_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        sky_obj = bpy.data.objects.new("AION_SkyDome", mesh)
        sky_col.objects.link(sky_obj)

    sky_obj.location = center
    sky_obj.scale = (1.5, 1.5, 1.2)

    # Assign beautiful sky shader (unlit gradient + clouds)
    mat = bpy.data.materials.new("AION_SkyDome_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)
    emission = nodes.new("ShaderNodeEmission")
    emission.location = (350, 0)
    emission.inputs["Strength"].default_value = 1.0

    # Sky gradient coordinates
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

    # Gradient texture
    grad = nodes.new("ShaderNodeTexGradient")
    grad.location = (-400, 0)
    grad.gradient_type = "LINEAR"
    links.new(mapping.outputs["Vector"], grad.inputs["Vector"])

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-150, 0)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[0].color = (0.65, 0.78, 0.90, 1.0)
    color_ramp.color_ramp.elements[1].position = 0.9
    color_ramp.color_ramp.elements[1].color = (0.15, 0.42, 0.82, 1.0)
    links.new(grad.outputs["Fac"], color_ramp.inputs["Fac"])

    # Resolve cloud texture
    cloud_tex_path = resolver.resolve_resource("sky_cloudmask01.dds") or resolver.resolve_resource("clouds_rgba_daylight.dds")
    if cloud_tex_path and cloud_tex_path.is_file():
        from materials.texture_loader import load_texture_image
        cloud_img = load_texture_image(cloud_tex_path, colorspace="sRGB")
        if cloud_img:
            cloud_node = nodes.new("ShaderNodeTexImage")
            cloud_node.location = (-150, 250)
            cloud_node.image = cloud_img
            cloud_map = nodes.new("ShaderNodeMapping")
            cloud_map.location = (-400, 250)
            links.new(tex_coord.outputs["UV"], cloud_map.inputs["Vector"])
            if animate_clouds:
                try:
                    drv = cloud_map.inputs["Location"].driver_add("default_value", 0)
                    drv.driver.expression = "frame * 0.0008"
                except Exception:
                    pass
            links.new(cloud_map.outputs["Vector"], cloud_node.inputs["Vector"])

            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MIX"
            mix.location = (120, 100)

            fac_in = mix.inputs.get("Factor_Float") or mix.inputs[0]
            a_in = mix.inputs.get("A_Color") or mix.inputs[6]
            b_in = mix.inputs.get("B_Color") or mix.inputs[7]
            res_out = mix.outputs.get("Result_Color") or mix.outputs[2]

            links.new(cloud_node.outputs.get("Alpha", cloud_node.outputs[0]), fac_in)
            links.new(color_ramp.outputs["Color"], a_in)
            links.new(cloud_node.outputs["Color"], b_in)
            links.new(res_out, emission.inputs["Color"])
        else:
            links.new(color_ramp.outputs["Color"], emission.inputs["Color"])
    else:
        links.new(color_ramp.outputs["Color"], emission.inputs["Color"])

    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    try:
        mat.use_backface_culling = False
    except Exception:
        pass
    sky_obj.data.materials.clear()
    sky_obj.data.materials.append(mat)

    if override_viewport_shading:
        # Optionally enable scene world in 3D viewports when high-quality mode wants it
        try:
            if hasattr(context, "screen") and context.screen:
                for area in context.screen.areas:
                    if area.type == "VIEW_3D":
                        for space in area.spaces:
                            if space.type == "VIEW_3D":
                                space.shading.use_scene_world = True
                                space.shading.use_scene_lights = True
        except Exception:
            pass

    return sky_obj
