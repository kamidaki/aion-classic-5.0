from dataclasses import dataclass

from formats.level import (
    LIQUID_KIND_LAVA,
    LIQUID_PRESET_LAVA_EMISSIVE,
    LIQUID_PRESET_NORMAL,
    LIQUID_PRESET_TRANSPARENT,
    LiquidSurfaceRecipe,
)


@dataclass(frozen=True)
class LiquidSurfaceMaterialResult:
    requested: bool
    applied: bool
    selected_kind: str
    inferred_kind: str
    selected_preset: str
    textures_loaded: int
    textures_used: int
    material_name: str
    skip_reason: str | None
    warnings: tuple[str, ...] = ()


def apply_liquid_surface_material(
    water_result,
    recipe: LiquidSurfaceRecipe,
    *,
    alpha: float = 0.72,
    tile_scale: float = 48.0,
    animate_liquid: bool = False,
    simple_shader: bool = False,
):
    if water_result is None or not water_result.created or water_result.object is None or water_result.mesh is None:
        return LiquidSurfaceMaterialResult(
            requested=True,
            applied=False,
            selected_kind=recipe.selected_kind,
            inferred_kind=recipe.inferred_kind,
            selected_preset=recipe.selected_preset,
            textures_loaded=0,
            textures_used=0,
            material_name="",
            skip_reason="liquid surface material requested but water/liquid plane was not created",
            warnings=recipe.warnings,
        )

    material, report = _create_liquid_material(
        recipe,
        alpha=alpha,
        tile_scale=tile_scale,
        animate_liquid=animate_liquid,
        simple_shader=simple_shader,
    )
    water_result.mesh.materials.clear()
    water_result.mesh.materials.append(material)
    water_result.object["aion_liquid_kind"] = recipe.selected_kind
    water_result.object["aion_liquid_inferred_kind"] = recipe.inferred_kind
    water_result.object["aion_liquid_preset"] = recipe.selected_preset
    water_result.object["aion_liquid_textures_loaded"] = report["textures_loaded"]
    water_result.object["aion_liquid_textures_used"] = report["textures_used"]
    water_result.object["aion_liquid_level"] = water_result.water_level
    water_result.object["aion_liquid_width"] = water_result.width
    water_result.object["aion_liquid_height"] = water_result.height
    material["aion_liquid_kind"] = recipe.selected_kind
    material["aion_liquid_inferred_kind"] = recipe.inferred_kind
    material["aion_liquid_preset"] = recipe.selected_preset
    material["aion_liquid_textures_loaded"] = report["textures_loaded"]
    material["aion_liquid_textures_used"] = report["textures_used"]
    return LiquidSurfaceMaterialResult(
        requested=True,
        applied=True,
        selected_kind=recipe.selected_kind,
        inferred_kind=recipe.inferred_kind,
        selected_preset=recipe.selected_preset,
        textures_loaded=report["textures_loaded"],
        textures_used=report["textures_used"],
        material_name=material.name,
        skip_reason=None,
        warnings=recipe.warnings,
    )


def skipped_liquid_surface_result(*, requested, selected_kind="", inferred_kind="", selected_preset="", reason=None):
    return LiquidSurfaceMaterialResult(
        requested=requested,
        applied=False,
        selected_kind=selected_kind,
        inferred_kind=inferred_kind,
        selected_preset=selected_preset,
        textures_loaded=0,
        textures_used=0,
        material_name="",
        skip_reason=reason,
    )


def _create_liquid_material(
    recipe: LiquidSurfaceRecipe,
    *,
    alpha: float,
    tile_scale: float,
    animate_liquid: bool = False,
    simple_shader: bool = False,
):
    import bpy

    material = bpy.data.materials.new(f"AION_Liquid_{recipe.selected_kind.lower()}_{recipe.selected_preset.lower()}")
    material.use_nodes = True
    try:
        # NEVER use CLIP on semi-transparent water (alpha < 0.5 vanishes completely!)
        material.blend_method = "BLEND"
    except (AttributeError, TypeError):
        pass
    try:
        material.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        pass
    try:
        material.show_transparent_back = False
        material.use_transparent_shadow = False
        material.use_backface_culling = False
    except (AttributeError, TypeError):
        pass
    tree = material.node_tree
    nodes = tree.nodes
    links = tree.links
    for node in tuple(nodes):
        nodes.remove(node)
    output = nodes.new("ShaderNodeOutputMaterial")
    mapping = nodes.new("ShaderNodeMapping")
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping.inputs["Scale"].default_value = (float(tile_scale), float(tile_scale), 1.0)
    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

    # Only attach Python drivers when explicitly requested (zero per-frame overhead at 60+ FPS)
    if animate_liquid and not simple_shader:
        try:
            flow_speed = 0.001 if recipe.selected_kind == LIQUID_KIND_LAVA else 0.003
            drv_x = mapping.inputs["Location"].driver_add("default_value", 0)
            drv_x.driver.expression = f"frame * {flow_speed}"
            drv_y = mapping.inputs["Location"].driver_add("default_value", 1)
            drv_y.driver.expression = f"frame * {flow_speed * 0.6}"
        except Exception:
            pass

    loaded = _load_candidates(recipe.candidates)
    used = []
    if recipe.selected_kind == LIQUID_KIND_LAVA or recipe.selected_preset == LIQUID_PRESET_LAVA_EMISSIVE:
        used.extend(_wire_lava(nodes, links, mapping, output, loaded, recipe.selected_preset))
    else:
        used.extend(
            _wire_water(
                nodes,
                links,
                mapping,
                output,
                loaded,
                recipe.selected_preset,
                alpha,
                tile_scale,
                animate_liquid=animate_liquid,
                simple_shader=simple_shader,
            )
        )
    return material, {
        "textures_loaded": len(loaded),
        "textures_used": len({item["candidate"].texture for item in used}),
    }


def _load_candidates(candidates):
    import bpy

    loaded = []
    for candidate in candidates:
        if not candidate.exists:
            continue
        try:
            image = bpy.data.images.load(candidate.resolved_path, check_existing=True)
        except RuntimeError:
            continue
        loaded.append({"candidate": candidate, "image": image})
    return loaded


def _wire_water(
    nodes,
    links,
    mapping,
    output,
    loaded,
    preset,
    alpha,
    tile_scale=48.0,
    *,
    animate_liquid: bool = False,
    simple_shader: bool = False,
):
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    effective_alpha = 0.55 if preset == LIQUID_PRESET_TRANSPARENT else max(0.55, min(0.92, float(alpha)))
    bsdf.inputs["Alpha"].default_value = effective_alpha
    water_tint = (0.04, 0.30, 0.48, 1.0)
    bsdf.inputs["Base Color"].default_value = water_tint
    bsdf.inputs["Roughness"].default_value = 0.10 if simple_shader else 0.06
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.65
    try:
        bsdf.inputs["IOR"].default_value = 1.333
    except Exception:
        pass
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    used = []
    texture = _first_loaded(loaded, roles=("diffuse_base", "caustics", "reflection"), kinds=("WATER", "SWAMP", "MAGIC", "UNKNOWN"))
    if texture:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = texture["image"]
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        try:
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MIX"
            fac_in = mix.inputs.get("Factor_Float") or mix.inputs[0]
            a_in = mix.inputs.get("A_Color") or mix.inputs[6]
            b_in = mix.inputs.get("B_Color") or mix.inputs[7]
            res_out = mix.outputs.get("Result_Color") or mix.outputs[2]
            fac_in.default_value = 0.5
            a_in.default_value = water_tint
            links.new(tex.outputs["Color"], b_in)
            links.new(res_out, bsdf.inputs["Base Color"])
        except Exception:
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        used.append(texture)

    normal_connected = False
    if not simple_shader and preset == LIQUID_PRESET_NORMAL:
        normal_texture = _first_loaded(loaded, roles=("normal_bump",), kinds=("WATER", "SWAMP", "MAGIC", "UNKNOWN"))
        if normal_texture:
            normal_texture["image"].colorspace_settings.name = "Non-Color"
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = normal_texture["image"]
            normal = nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = 0.35
            links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
            links.new(tex.outputs["Color"], normal.inputs["Color"])
            links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
            normal_connected = True
            used.append(normal_texture)

    if not normal_connected and texture:
        try:
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.14
            bump.inputs["Distance"].default_value = 0.08
            links.new(tex.outputs["Color"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception:
            pass

    # 4D animated noise + bump is very heavy on weak GPUs; enable ONLY when explicitly requested
    if animate_liquid and not simple_shader and not normal_connected and not texture:
        try:
            noise = nodes.new("ShaderNodeTexNoise")
            noise.noise_dimensions = "4D"
            noise.inputs["Scale"].default_value = float(tile_scale) * 1.2
            noise.inputs["Detail"].default_value = 3.0
            noise.inputs["Roughness"].default_value = 0.45
            drv_w = noise.inputs["W"].driver_add("default_value")
            drv_w.driver.expression = "frame * 0.018"

            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.18
            bump.inputs["Distance"].default_value = 0.08

            links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception:
            pass

    if preset == LIQUID_PRESET_TRANSPARENT:
        bsdf.inputs["Alpha"].default_value = 0.55
    return used


def _wire_lava(nodes, links, mapping, output, loaded, preset):
    texture = _first_loaded(loaded, roles=("emission_glow", "diffuse_base", "caustics"), kinds=("LAVA", "UNKNOWN"))
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (1.0, 0.22, 0.02, 1.0)
    emission.inputs["Strength"].default_value = 4.0 if preset == LIQUID_PRESET_LAVA_EMISSIVE else 2.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    if not texture:
        return []
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = texture["image"]
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], emission.inputs["Color"])
    return [texture]


def _first_loaded(loaded, *, roles, kinds):
    for kind in kinds:
        for role in roles:
            for item in loaded:
                candidate = item["candidate"]
                if candidate.role == role and candidate.liquid_kind == kind:
                    return item
    for role in roles:
        for item in loaded:
            if item["candidate"].role == role:
                return item
    return None
