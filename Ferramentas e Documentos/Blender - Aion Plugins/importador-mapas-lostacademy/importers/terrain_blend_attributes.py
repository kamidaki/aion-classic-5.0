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

    for r in rows:
        row_offset = r * orig_width
        for c in cols:
            sample = all_samples[row_offset + c]
            weights = sample.weights
            if not weights:
                sample_colors.extend((0.0, 0.0, 0.0, 0.0))
                continue
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
