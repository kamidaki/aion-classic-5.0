import math
from array import array
from dataclasses import dataclass

from formats.level import TerrainBlendWeights


ATTRIBUTE_NAME_PREFIX = "AION_BlendWeights_"
MATERIALS_PER_ATTRIBUTE = 4


@dataclass(frozen=True)
class TerrainBlendAttributeResult:
    attribute_layers_created: int
    material_count: int
    layer_names: tuple[str, ...]


def _grid_subsamples(width: int, height: int, lod: int = 1):
    step = max(1, int(lod))
    if step <= 1:
        return list(range(height)), list(range(width))
    rows = list(range(0, height, step))
    if rows[-1] != height - 1:
        rows.append(height - 1)
    cols = list(range(0, width, step))
    if cols[-1] != width - 1:
        cols.append(width - 1)
    return rows, cols


def create_terrain_blend_attributes(
    mesh,
    blend_weights: TerrainBlendWeights,
    lod: int = 1,
    orig_width: int = 0,
    orig_height: int = 0,
) -> TerrainBlendAttributeResult:
    material_indices = blend_weights.used_material_indices
    layer_names = []
    num_verts = len(mesh.vertices)
    num_samples = len(blend_weights.samples)

    if orig_width <= 0:
        orig_width = int(math.isqrt(num_samples))
        orig_height = orig_width

    rows, cols = _grid_subsamples(orig_width, orig_height, lod)

    for layer_index, start in enumerate(
        range(0, len(material_indices), MATERIALS_PER_ATTRIBUTE)
    ):
        layer_material_indices = material_indices[start : start + MATERIALS_PER_ATTRIBUTE]
        layer_name = f"{ATTRIBUTE_NAME_PREFIX}{layer_index}"
        sample_colors = _pack_sample_colors_subsampled(
            blend_weights,
            layer_material_indices,
            rows,
            cols,
            orig_width,
        )

        used_point_domain = False
        try:
            attribute = mesh.color_attributes.new(
                name=layer_name,
                type="FLOAT_COLOR",
                domain="POINT",
            )
            attribute.data.foreach_set("color", sample_colors)
            used_point_domain = True
        except Exception:
            used_point_domain = False

        if not used_point_domain:
            attribute = mesh.color_attributes.new(
                name=layer_name,
                type="FLOAT_COLOR",
                domain="CORNER",
            )
            loop_colors = _pack_loop_colors_fast(mesh, sample_colors)
            attribute.data.foreach_set("color", loop_colors)

        layer_names.append(layer_name)

    mesh["aion_blend_material_indices"] = list(material_indices)
    mesh["aion_blend_attribute_layers"] = ",".join(layer_names)
    mesh["aion_blend_radius"] = blend_weights.radius

    return TerrainBlendAttributeResult(
        attribute_layers_created=len(layer_names),
        material_count=len(material_indices),
        layer_names=tuple(layer_names),
    )


def prepare_subsampled_terrain_blend_data(
    land_map,
    lod: int = 1,
    radius: int = 1,
) -> dict:
    """
    Pure-Python subsampled blend weight computation safe to execute in a background worker thread.
    Returns packed float arrays and sample counts without touching any Blender (bpy) state.
    """
    orig_width = land_map.width
    orig_height = land_map.height
    samples = land_map.samples
    rows, cols = _grid_subsamples(orig_width, orig_height, lod)

    used_set = set()
    mat_counts: dict[int, int] = {}
    for r in rows:
        row_off = r * orig_width
        for c in cols:
            col_id = samples[row_off + c].color
            used_set.add(col_id)
            mat_counts[col_id] = mat_counts.get(col_id, 0) + 1

    used_material_indices = tuple(sorted(used_set))
    if not used_material_indices:
        return {
            "used_material_indices": (),
            "layer_arrays": [],
            "mat_counts": mat_counts,
            "boundary_count": 0,
            "radius": radius,
        }

    num_layers = (len(used_material_indices) + MATERIALS_PER_ATTRIBUTE - 1) // MATERIALS_PER_ATTRIBUTE
    mat_to_slot = {m: idx for idx, m in enumerate(used_material_indices)}

    vertex_count = len(rows) * len(cols)
    layer_arrays = [array("f", [0.0]) * (vertex_count * MATERIALS_PER_ATTRIBUTE) for _ in range(num_layers)]
    boundary_count = 0
    inv_9 = 1.0 / 9.0

    v_idx = 0
    for r in rows:
        r_top = r - 1 if r > 0 else 0
        r_bot = r + 1 if r < orig_height - 1 else orig_height - 1
        r_off = r * orig_width
        t_off = r_top * orig_width
        b_off = r_bot * orig_width
        internal_r = 0 < r < orig_height - 1

        for c in cols:
            center_id = samples[r_off + c].color
            if radius <= 0:
                slot = mat_to_slot[center_id]
                layer_arrays[slot >> 2][(v_idx << 2) + (slot & 3)] = 1.0
            elif radius == 1 and internal_r and 0 < c < orig_width - 1:
                c0 = samples[t_off + c - 1].color
                c1 = samples[t_off + c].color
                c2 = samples[t_off + c + 1].color
                c3 = samples[r_off + c - 1].color
                c5 = samples[r_off + c + 1].color
                c6 = samples[b_off + c - 1].color
                c7 = samples[b_off + c].color
                c8 = samples[b_off + c + 1].color
                if (
                    c0 == center_id and c1 == center_id and c2 == center_id
                    and c3 == center_id and c5 == center_id
                    and c6 == center_id and c7 == center_id and c8 == center_id
                ):
                    slot = mat_to_slot[center_id]
                    layer_arrays[slot >> 2][(v_idx << 2) + (slot & 3)] = 1.0
                else:
                    boundary_count += 1
                    local_counts: dict[int, int] = {}
                    for v in (c0, c1, c2, c3, center_id, c5, c6, c7, c8):
                        local_counts[v] = local_counts.get(v, 0) + 1
                    base = v_idx << 2
                    for m_id, cnt in local_counts.items():
                        slot = mat_to_slot.get(m_id)
                        if slot is not None:
                            layer_arrays[slot >> 2][base + (slot & 3)] = cnt * inv_9
            else:
                local_counts = {}
                pts = 0
                c_start = max(0, c - radius)
                c_end = min(orig_width, c + radius + 1)
                for nr in range(max(0, r - radius), min(orig_height, r + radius + 1)):
                    nr_off = nr * orig_width
                    for nc in range(c_start, c_end):
                        v = samples[nr_off + nc].color
                        local_counts[v] = local_counts.get(v, 0) + 1
                        pts += 1
                if len(local_counts) > 1:
                    boundary_count += 1
                inv_pts = 1.0 / pts if pts else 1.0
                base = v_idx << 2
                for m_id, cnt in local_counts.items():
                    slot = mat_to_slot.get(m_id)
                    if slot is not None:
                        layer_arrays[slot >> 2][base + (slot & 3)] = cnt * inv_pts
            v_idx += 1

    return {
        "used_material_indices": used_material_indices,
        "layer_arrays": layer_arrays,
        "mat_counts": mat_counts,
        "boundary_count": boundary_count,
        "radius": radius,
    }


def apply_precomputed_terrain_blend_attributes(
    mesh,
    blend_data: dict,
) -> tuple[TerrainBlendAttributeResult, dict[int, int], int]:
    """Applies precomputed subsampled blend arrays onto the Blender Mesh color attributes."""
    used_material_indices = blend_data["used_material_indices"]
    layer_arrays = blend_data["layer_arrays"]
    mat_counts = blend_data["mat_counts"]
    boundary_count = blend_data["boundary_count"]
    radius = blend_data["radius"]

    if not used_material_indices:
        mesh["aion_blend_material_indices"] = []
        mesh["aion_blend_attribute_layers"] = ""
        mesh["aion_blend_radius"] = radius
        return TerrainBlendAttributeResult(0, 0, ()), mat_counts, 0

    layer_names = []
    for layer_index, sample_colors in enumerate(layer_arrays):
        layer_name = f"{ATTRIBUTE_NAME_PREFIX}{layer_index}"
        used_point_domain = False
        try:
            attribute = mesh.color_attributes.new(
                name=layer_name,
                type="FLOAT_COLOR",
                domain="POINT",
            )
            attribute.data.foreach_set("color", sample_colors)
            used_point_domain = True
        except Exception:
            used_point_domain = False

        if not used_point_domain:
            attribute = mesh.color_attributes.new(
                name=layer_name,
                type="FLOAT_COLOR",
                domain="CORNER",
            )
            loop_colors = _pack_loop_colors_fast(mesh, sample_colors)
            attribute.data.foreach_set("color", loop_colors)

        layer_names.append(layer_name)

    mesh["aion_blend_material_indices"] = list(used_material_indices)
    mesh["aion_blend_attribute_layers"] = ",".join(layer_names)
    mesh["aion_blend_radius"] = radius

    return (
        TerrainBlendAttributeResult(
            attribute_layers_created=len(layer_names),
            material_count=len(used_material_indices),
            layer_names=tuple(layer_names),
        ),
        mat_counts,
        boundary_count,
    )


def create_fast_subsampled_terrain_blend_attributes(
    mesh,
    land_map,
    lod: int = 1,
    radius: int = 1,
) -> tuple[TerrainBlendAttributeResult, dict[int, int], int]:
    """
    Fast subsampled blend weight builder.
    Computes 3x3 neighborhood weights ONLY for the (rows x cols) vertices that actually exist
    at the chosen terrain LOD (e.g. 66k points at LOD 4 instead of 1,048,576 points),
    avoiding ~1M Python TerrainSampleBlendWeights allocations.
    Returns (TerrainBlendAttributeResult, subsampled_material_counts, boundary_sample_count).
    """
    blend_data = prepare_subsampled_terrain_blend_data(land_map, lod=lod, radius=radius)
    return apply_precomputed_terrain_blend_attributes(mesh, blend_data)


def _pack_sample_colors_subsampled(
    blend_weights: TerrainBlendWeights,
    layer_material_indices: tuple[int, ...],
    rows: list[int],
    cols: list[int],
    orig_width: int,
) -> array:
    indices = layer_material_indices
    pad = MATERIALS_PER_ATTRIBUTE - len(indices)
    sample_colors = array("f")
    all_samples = blend_weights.samples
    all_materials = blend_weights.used_material_indices

    # Precompute uniform 4-float vectors for all materials (eliminates 250,000+ dict creations)
    uniform_vectors = {}
    for m in all_materials:
        vec = []
        for mat_id in indices:
            vec.append(1.0 if m == mat_id else 0.0)
        if pad > 0:
            vec.extend([0.0] * pad)
        uniform_vectors[m] = tuple(vec)

    zero_vector = (0.0,) * MATERIALS_PER_ATTRIBUTE

    for r in rows:
        row_offset = r * orig_width
        for c in cols:
            sample = all_samples[row_offset + c]
            weights = sample.weights
            if not weights:
                sample_colors.extend(zero_vector)
                continue
            if len(weights) == 1:
                # Fast path: uniform point (over 90% of terrain samples)
                sample_colors.extend(uniform_vectors.get(sample.material_index, zero_vector))
                continue

            # Boundary point with mixed materials
            w_dict = dict(weights)
            for mat_id in indices:
                sample_colors.append(float(w_dict.get(mat_id, 0.0)))
            if pad > 0:
                sample_colors.extend((0.0,) * pad)

    return sample_colors


def _pack_loop_colors_fast(mesh, sample_colors: array) -> array:
    num_loops = len(mesh.loops)
    loop_vertex_indices = [0] * num_loops
    mesh.loops.foreach_get("vertex_index", loop_vertex_indices)

    loop_colors = array("f", [0.0]) * (num_loops * MATERIALS_PER_ATTRIBUTE)
    for loop_idx, v_idx in enumerate(loop_vertex_indices):
        s_off = v_idx * MATERIALS_PER_ATTRIBUTE
        d_off = loop_idx * MATERIALS_PER_ATTRIBUTE
        loop_colors[d_off] = sample_colors[s_off]
        loop_colors[d_off + 1] = sample_colors[s_off + 1]
        loop_colors[d_off + 2] = sample_colors[s_off + 2]
        loop_colors[d_off + 3] = sample_colors[s_off + 3]
    return loop_colors
