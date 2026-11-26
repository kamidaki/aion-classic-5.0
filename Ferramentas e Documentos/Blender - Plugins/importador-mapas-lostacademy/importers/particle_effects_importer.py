from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path

from formats.cgf.texture_sequences import resolve_texture_sequence
from formats.level.particle_effects import (
    EntityContextParticleEffect,
    parse_entitycontext_particle_effects,
    resolve_particle_effect_definition,
)


PARTICLE_EFFECTS_COLLECTION_NAME = "Aion Particle Effects"
PARTICLE_EFFECTS_COORDINATE_VARIANT = "raw_xyz"
PARTICLE_EFFECTS_EXPERIMENTAL = True


@dataclass(frozen=True)
class ParticleEffectImportStatus:
    effect_name: str
    entity_name: str
    source_file: str
    record_index: int
    position: tuple[float, float, float] | None
    definition_found: bool
    effect_library: str
    texture_path: str
    texture_exists: bool
    emitter_name: str
    emitter_record_index: int
    visual_status: str
    object_name: str
    reason: str


@dataclass(frozen=True)
class ParticleEffectsImportResult:
    requested: bool
    files_scanned: int
    records_found: int
    definitions_found: int
    textures_resolved: int
    sprite_visuals_created: int
    marker_fallback_created: int
    skipped_invalid_placements: int
    unsupported_effects: int
    collection_name: str
    coordinate_variant: str
    statuses: tuple[ParticleEffectImportStatus, ...]
    skip_reasons: dict


@dataclass(frozen=True)
class PreparedParticleEffectsData:
    parsed: object
    entries: tuple[tuple[object, object, tuple[object, ...]], ...]


def prepare_particle_effects_stage_data(
    level_dir: str | Path,
    client_root: str | Path,
    *,
    level_data=None,
) -> PreparedParticleEffectsData:
    """Thread-safe worker preparation: parses entitycontexts and pre-extracts .prt/.dds assets."""
    level_path = Path(level_dir)
    client_root_path = Path(client_root)
    parsed = parse_entitycontext_particle_effects(level_path, level_data=level_data)
    prepared_entries = []
    for record in parsed.records:
        definition = resolve_particle_effect_definition(client_root_path, record.effect_name)
        texture_refs = _existing_textures(definition.texture_references)
        prepared_entries.append((record, definition, texture_refs))
    return PreparedParticleEffectsData(parsed=parsed, entries=tuple(prepared_entries))


def _get_or_create_particle_cross_mesh(bpy, sprite_size: float):
    """Creates one shared crossed-quad billboard mesh so hundreds of effects share 1 mesh datablock."""
    size_key = round(float(sprite_size), 3)
    mesh_name = f"AION_ParticleCrossQuad_{size_key:.3f}"
    existing = bpy.data.meshes.get(mesh_name)
    if existing is not None:
        return existing

    half = float(sprite_size) * 0.5
    verts = [
        # Quad 1 (X-Z plane)
        (-half, 0.0, -half),
        (half, 0.0, -half),
        (half, 0.0, half),
        (-half, 0.0, half),
        # Quad 2 (Y-Z plane)
        (0.0, -half, -half),
        (0.0, half, -half),
        (0.0, half, half),
        (0.0, -half, half),
    ]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7)]
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="AION_ParticleUV")
    quad_uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)) * 2
    for loop, uv in zip(uv_layer.data, quad_uvs):
        loop.uv = uv
    # Reserve 1 material slot so per-object slot linkage swaps textures on one shared mesh.
    mesh.materials.append(None)
    return mesh


def iter_create_particle_effects(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    level_data=None,
    sprite_size: float = 2.0,
    pre_prepared: PreparedParticleEffectsData | None = None,
    target_collection=None,
    disable_shadows: bool = True,
    batch_size: int = 24,
):
    """Time-sliced generator creating all particle effect visuals without freezing the UI thread."""
    level_path = Path(level_dir)
    client_root_path = Path(client_root)
    if sprite_size <= 0 or not math.isfinite(float(sprite_size)):
        raise ValueError("particle sprite size must be finite and positive")

    if pre_prepared is None:
        pre_prepared = prepare_particle_effects_stage_data(
            level_path,
            client_root_path,
            level_data=level_data,
        )
    parsed = pre_prepared.parsed

    import bpy

    if target_collection is not None:
        collection = target_collection
    else:
        collection = bpy.data.collections.new(PARTICLE_EFFECTS_COLLECTION_NAME)
        context.scene.collection.children.link(collection)

    shared_mesh = _get_or_create_particle_cross_mesh(bpy, sprite_size)
    material_cache = {}
    statuses = []
    skip_reasons = Counter()
    definitions_found = 0
    textures_resolved = 0
    sprite_count = 0
    marker_count = 0
    unsupported_count = 0

    total = len(pre_prepared.entries)
    step_yield = max(1, int(batch_size))

    for idx, (record, definition, texture_refs) in enumerate(pre_prepared.entries, start=1):
        if definition.definition_found:
            definitions_found += 1
        if texture_refs:
            textures_resolved += len(texture_refs)
            for layer_index, texture_ref in enumerate(texture_refs):
                obj, visual_status, reason = _create_sprite_object(
                    bpy,
                    record,
                    definition,
                    texture_ref,
                    material_cache,
                    client_root=client_root_path,
                    sprite_size=sprite_size,
                    layer_index=layer_index,
                    layer_count=len(texture_refs),
                    shared_mesh=shared_mesh,
                    disable_shadows=disable_shadows,
                )
                if obj is not None:
                    sprite_count += 1
                else:
                    obj = _create_marker_object(bpy, record, definition, texture_ref, visual_status, reason)
                    marker_count += 1
                    skip_reasons[reason or visual_status] += 1
                collection.objects.link(obj)
                statuses.append(
                    _status_from_object(
                        record,
                        definition,
                        texture_ref,
                        visual_status,
                        obj.name,
                        reason,
                    )
                )
        else:
            texture_ref = _first_texture(definition.texture_references)
            visual_status = "marker_no_texture"
            reason = "no_existing_particle_texture"
            obj = _create_marker_object(bpy, record, definition, texture_ref, visual_status, reason)
            marker_count += 1
            unsupported_count += 1
            skip_reasons[reason] += 1

            collection.objects.link(obj)
            statuses.append(
                _status_from_object(
                    record,
                    definition,
                    texture_ref,
                    visual_status,
                    obj.name,
                    reason,
                )
            )
        if idx % step_yield == 0 and idx < total:
            yield idx, total

    return ParticleEffectsImportResult(
        requested=True,
        files_scanned=parsed.files_scanned,
        records_found=parsed.records_found,
        definitions_found=definitions_found,
        textures_resolved=textures_resolved,
        sprite_visuals_created=sprite_count,
        marker_fallback_created=marker_count,
        skipped_invalid_placements=parsed.skipped_invalid_positions,
        unsupported_effects=unsupported_count,
        collection_name=collection.name,
        coordinate_variant=PARTICLE_EFFECTS_COORDINATE_VARIANT,
        statuses=tuple(statuses),
        skip_reasons=dict(skip_reasons),
    )


def create_particle_effects(
    context,
    level_dir: str | Path,
    client_root: str | Path,
    *,
    level_data=None,
    sprite_size: float = 2.0,
    target_collection=None,
    disable_shadows: bool = True,
) -> ParticleEffectsImportResult:
    gen = iter_create_particle_effects(
        context,
        level_dir,
        client_root,
        level_data=level_data,
        sprite_size=sprite_size,
        target_collection=target_collection,
        disable_shadows=disable_shadows,
        batch_size=999999,
    )
    try:
        while True:
            next(gen)
    except StopIteration as exc:
        return exc.value


def _create_sprite_object(
    bpy,
    record,
    definition,
    texture_ref,
    material_cache,
    *,
    client_root,
    sprite_size,
    layer_index,
    layer_count,
    shared_mesh=None,
    disable_shadows: bool = True,
):
    try:
        material = _particle_material(bpy, texture_ref, material_cache, definition, client_root=client_root)
    except RuntimeError as exc:
        return None, "marker_texture_load_failed", f"texture_load_failed:{exc}"

    if shared_mesh is not None and len(shared_mesh.materials) > 0:
        mesh = shared_mesh
        obj = bpy.data.objects.new(_object_name(record, layer_index=layer_index, layer_count=layer_count), mesh)
        obj.material_slots[0].link = "OBJECT"
        obj.material_slots[0].material = material
    else:
        half = float(sprite_size) * 0.5
        mesh = bpy.data.meshes.new(f"AION_ParticleEffect_{record.record_index:04d}_Mesh")
        mesh.from_pydata(
            [(-half, 0.0, -half), (half, 0.0, -half), (half, 0.0, half), (-half, 0.0, half)],
            [],
            [(0, 1, 2, 3)],
        )
        mesh.update()
        uv_layer = mesh.uv_layers.new(name="AION_ParticleUV")
        for loop, uv in zip(uv_layer.data, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
            loop.uv = uv
        mesh.materials.append(material)
        obj = bpy.data.objects.new(_object_name(record, layer_index=layer_index, layer_count=layer_count), mesh)

    if disable_shadows and hasattr(obj, "visible_shadow"):
        try:
            obj.visible_shadow = False
        except (AttributeError, TypeError):
            pass
    base_pos = _raw_position(record.position)
    # Slight Z offset for upper layers prevents Z-fighting on overlapping emitter sprites
    obj.location = (base_pos[0], base_pos[1], base_pos[2] + float(layer_index) * 0.05)
    _assign_custom_properties(obj, record, definition, texture_ref, "sprite_texture", "")
    obj["aion_particle_layer_index"] = int(layer_index)
    obj["aion_particle_layer_count"] = int(layer_count)
    return obj, "sprite_texture", ""


def _create_marker_object(bpy, record, definition, texture_ref, visual_status, reason):
    obj = bpy.data.objects.new(_object_name(record), None)
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.05
    obj.location = _raw_position(record.position)
    _assign_custom_properties(obj, record, definition, texture_ref, visual_status, reason)
    return obj


def _particle_material(bpy, texture_ref, material_cache, definition, *, client_root):
    sequence = resolve_texture_sequence(
        {"name": texture_ref.texture_path, "long_name": texture_ref.texture_path},
        cgf_path=definition.library_path,
        client_root=client_root,
        fps=10,
    )
    key = (str(texture_ref.resolved_path), bool(sequence.is_sequence), sequence.frame_count)
    cached = material_cache.get(key)
    if cached is not None:
        return cached

    image = bpy.data.images.load(
        str(sequence.frame_paths[0] if sequence.is_sequence else texture_ref.resolved_path),
        check_existing=not sequence.is_sequence,
    )
    if sequence.is_sequence:
        image.source = "SEQUENCE"
        image.filepath = sequence.frame_paths[0]
        image.filepath_raw = sequence.frame_paths[0]
    material = bpy.data.materials.new(f"AION Particle {Path(texture_ref.texture_path).stem}")
    material.use_nodes = True
    if hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "BLENDED"
    if hasattr(material, "use_backface_culling"):
        material.use_backface_culling = False
    if hasattr(material, "show_transparent_back"):
        material.show_transparent_back = False
    if hasattr(material, "use_screen_refraction"):
        material.use_screen_refraction = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (420, 0)
    mix_shader = nodes.new(type="ShaderNodeMixShader")
    mix_shader.location = (220, 0)
    transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    transparent.location = (0, 80)
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, -80)
    if "Strength" in emission.inputs:
        emission.inputs["Strength"].default_value = 1.6
    texture = nodes.new(type="ShaderNodeTexImage")
    texture.name = "AION Particle Texture"
    texture.location = (-280, 0)
    texture.image = image
    image_user = getattr(texture, "image_user", None)
    if sequence.is_sequence and image_user is not None:
        image_user.frame_start = 1
        image_user.frame_duration = int(sequence.effective_frame_count)
        image_user.frame_offset = int(sequence.blender_frame_offset)
        image_user.use_cyclic = True
        image_user.use_auto_refresh = True
    links.new(texture.outputs["Color"], emission.inputs["Color"])
    if "Alpha" in texture.outputs:
        links.new(texture.outputs["Alpha"], mix_shader.inputs["Fac"])
    else:
        mix_shader.inputs["Fac"].default_value = 0.85
    links.new(transparent.outputs["BSDF"], mix_shader.inputs[1])
    links.new(emission.outputs["Emission"], mix_shader.inputs[2])
    links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])
    material["aion_particle_texture"] = texture_ref.texture_path
    material["aion_particle_texture_exists"] = bool(texture_ref.exists)
    material["aion_particle_emitter_name"] = texture_ref.emitter_name
    material["aion_particle_emitter_record_index"] = int(texture_ref.emitter_record_index)
    material["aion_particle_blend_semantics"] = "unknown_not_decoded"
    material["aion_particle_size_semantics"] = "unknown_not_decoded"
    material["aion_particle_orientation_semantics"] = "unknown_not_decoded"
    material["aion_particle_texture_sequence_enabled"] = bool(sequence.is_sequence)
    material["aion_particle_texture_sequence_frame_count"] = int(sequence.frame_count)
    material["aion_particle_texture_sequence_skip_reason"] = sequence.skip_reason
    material_cache[key] = material
    return material


def _existing_textures(texture_references):
    return tuple(texture for texture in texture_references if texture.exists)


def _first_texture(texture_references):
    return texture_references[0] if texture_references else None


def _first_existing_texture(texture_references):
    for texture in texture_references:
        if texture.exists:
            return texture
    return None


def _assign_custom_properties(obj, record, definition, texture_ref, visual_status, reason):
    obj["aion_entity_type"] = "ParticleEffect"
    obj["aion_effect_name"] = record.effect_name
    obj["aion_effect_library"] = str(definition.library_path) if definition.library_path else ""
    obj["aion_effect_definition_found"] = bool(definition.definition_found)
    obj["aion_particle_texture"] = texture_ref.texture_path if texture_ref else ""
    obj["aion_particle_texture_exists"] = bool(texture_ref and texture_ref.exists)
    obj["aion_particle_emitter_name"] = texture_ref.emitter_name if texture_ref else ""
    obj["aion_particle_emitter_record_index"] = int(texture_ref.emitter_record_index) if texture_ref else -1
    obj["aion_particle_emitter_record_offset"] = int(texture_ref.emitter_record_offset) if texture_ref else -1
    obj["aion_particle_prt_record_layout"] = definition.record_layout
    obj["aion_particle_selected_record_count"] = int(definition.selected_record_count)
    obj["aion_particle_blend_semantics"] = "unknown_not_decoded"
    obj["aion_particle_size_semantics"] = "unknown_not_decoded"
    obj["aion_particle_orientation_semantics"] = "billboard_preview_no_prt_orientation_decoded"
    obj["aion_particle_visual_status"] = visual_status
    obj["aion_particle_import_experimental"] = PARTICLE_EFFECTS_EXPERIMENTAL
    obj["aion_entitycontext_source"] = record.source_file
    obj["aion_entitycontext_record_index"] = int(record.record_index)
    obj["aion_entity_name"] = record.entity_name
    obj["aion_raw_position"] = tuple(float(value) for value in record.position)
    obj["aion_coordinate_variant"] = PARTICLE_EFFECTS_COORDINATE_VARIANT
    obj["aion_particle_reason"] = reason
    obj["aion_raw_position_candidates"] = ";".join(
        ",".join(f"{float(value):.6g}" for value in candidate)
        for candidate in record.raw_position_candidates[:4]
    )
    obj["aion_particle_warnings"] = ";".join(record.warnings)


def _status_from_object(record, definition, texture_ref, visual_status, object_name, reason):
    return ParticleEffectImportStatus(
        effect_name=record.effect_name,
        entity_name=record.entity_name,
        source_file=record.source_file,
        record_index=record.record_index,
        position=tuple(record.position) if record.position else None,
        definition_found=definition.definition_found,
        effect_library=str(definition.library_path) if definition.library_path else "",
        texture_path=texture_ref.texture_path if texture_ref else "",
        texture_exists=bool(texture_ref and texture_ref.exists),
        emitter_name=texture_ref.emitter_name if texture_ref else "",
        emitter_record_index=int(texture_ref.emitter_record_index) if texture_ref else -1,
        visual_status=visual_status,
        object_name=object_name,
        reason=reason,
    )


def _raw_position(position):
    values = tuple(float(value) for value in position)
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError(f"invalid particle effect position: {position}")
    return values


def _object_name(record: EntityContextParticleEffect, *, layer_index=0, layer_count=1) -> str:
    base = record.entity_name or record.effect_name.split(".")[-1] or "ParticleEffect"
    suffix = f"_L{layer_index:02d}" if layer_count > 1 else ""
    return f"AION_ParticleEffect_{record.record_index:04d}_{base}{suffix}"
