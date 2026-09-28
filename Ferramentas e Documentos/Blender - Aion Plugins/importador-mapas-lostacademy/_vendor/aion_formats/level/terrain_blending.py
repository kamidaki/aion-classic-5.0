import math
from dataclasses import dataclass

from .terrain import LandMap


class TerrainSampleBlendWeights:
    __slots__ = ("sample_index", "material_index", "weights")

    def __init__(self, sample_index: int, material_index: int, weights: tuple[tuple[int, float], ...]):
        self.sample_index = sample_index
        self.material_index = material_index
        self.weights = weights

    @property
    def active_material_count(self) -> int:
        return len(self.weights)

    def __repr__(self) -> str:
        return (
            f"TerrainSampleBlendWeights(sample_index={self.sample_index}, "
            f"material_index={self.material_index}, weights={self.weights})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, TerrainSampleBlendWeights):
            return False
        return (
            self.sample_index == other.sample_index
            and self.material_index == other.material_index
            and self.weights == other.weights
        )


@dataclass(frozen=True)
class TerrainBlendWeights:
    radius: int
    used_material_indices: tuple[int, ...]
    samples: tuple[TerrainSampleBlendWeights, ...]
    boundary_sample_count: int
    max_active_material_count: int
    invalid_weight_count: int


def build_terrain_preview_blend_weights(
    land_map: LandMap,
    radius: int = 1,
) -> TerrainBlendWeights:
    if radius < 0:
        raise ValueError("terrain preview blend radius must be >= 0")
    if land_map.sample_count != len(land_map.samples):
        raise ValueError("LandMap sample count does not match parsed samples")
    if land_map.sample_count != land_map.width * land_map.height:
        raise ValueError("LandMap sample count does not match width * height")

    width = land_map.width
    height = land_map.height
    total_samples = land_map.sample_count
    colors = [s.color for s in land_map.samples]
    used_material_indices = tuple(sorted(set(colors)))
    uniform_weight_tuples = {m: ((m, 1.0),) for m in used_material_indices}

    sample_weights = [None] * total_samples
    boundary_sample_count = 0
    max_active_material_count = 1
    invalid_weight_count = 0

    if radius == 0:
        for idx in range(total_samples):
            c = colors[idx]
            sample_weights[idx] = TerrainSampleBlendWeights(idx, c, uniform_weight_tuples[c])
        return TerrainBlendWeights(
            radius=0,
            used_material_indices=used_material_indices,
            samples=tuple(sample_weights),
            boundary_sample_count=0,
            max_active_material_count=1,
            invalid_weight_count=0,
        )

    if radius == 1:
        inv_9 = 1.0 / 9.0
        for r in range(height):
            r_top = max(0, r - 1)
            r_bot = min(height - 1, r + 1)
            r_off = r * width
            top_off = r_top * width
            bot_off = r_bot * width
            is_internal_row = (0 < r < height - 1)

            for c in range(width):
                idx = r_off + c
                c4 = colors[idx]

                if is_internal_row and 0 < c < width - 1:
                    t = top_off + c
                    b = bot_off + c
                    # Fast-path: uniform 3x3 patch (all 9 neighbors identical)
                    if (
                        colors[t - 1] == c4
                        and colors[t] == c4
                        and colors[t + 1] == c4
                        and colors[idx - 1] == c4
                        and colors[idx + 1] == c4
                        and colors[b - 1] == c4
                        and colors[b] == c4
                        and colors[b + 1] == c4
                    ):
                        sample_weights[idx] = TerrainSampleBlendWeights(
                            idx, c4, uniform_weight_tuples[c4]
                        )
                        continue

                    # Boundary 3x3 patch: count frequencies directly without allocations
                    n_vals = (
                        colors[t - 1], colors[t], colors[t + 1],
                        colors[idx - 1], c4, colors[idx + 1],
                        colors[b - 1], colors[b], colors[b + 1],
                    )
                    counts = {}
                    for v in n_vals:
                        counts[v] = counts.get(v, 0) + 1
                    weights = tuple((k, v * inv_9) for k, v in sorted(counts.items()))
                else:
                    # Edge border pixels (r=0, r=height-1, c=0, c=width-1)
                    c_left = max(0, c - 1)
                    c_right = min(width - 1, c + 1)
                    counts = {}
                    total_pts = 0
                    for nr in (r_top, r, r_bot) if r_top != r_bot else (r,):
                        row_base = nr * width
                        for nc in range(c_left, c_right + 1):
                            v = colors[row_base + nc]
                            counts[v] = counts.get(v, 0) + 1
                            total_pts += 1
                    inv_pts = 1.0 / total_pts
                    weights = tuple((k, v * inv_pts) for k, v in sorted(counts.items()))

                active_count = len(weights)
                if active_count > 1:
                    boundary_sample_count += 1
                if active_count > max_active_material_count:
                    max_active_material_count = active_count

                sample_weights[idx] = TerrainSampleBlendWeights(idx, c4, weights)
    else:
        # General radius >= 2 fallback
        for sample_index in range(total_samples):
            row, column = divmod(sample_index, width)
            counts = {}
            total_pts = 0
            for nr in range(max(0, row - radius), min(height, row + radius + 1)):
                row_base = nr * width
                for nc in range(max(0, column - radius), min(width, column + radius + 1)):
                    v = colors[row_base + nc]
                    counts[v] = counts.get(v, 0) + 1
                    total_pts += 1
            inv_pts = 1.0 / total_pts
            weights = tuple((k, v * inv_pts) for k, v in sorted(counts.items()))
            active_count = len(weights)
            if active_count > 1:
                boundary_sample_count += 1
            if active_count > max_active_material_count:
                max_active_material_count = active_count
            sample_weights[sample_index] = TerrainSampleBlendWeights(
                sample_index, colors[sample_index], weights
            )

    return TerrainBlendWeights(
        radius=radius,
        used_material_indices=used_material_indices,
        samples=tuple(sample_weights),
        boundary_sample_count=boundary_sample_count,
        max_active_material_count=max_active_material_count,
        invalid_weight_count=invalid_weight_count,
    )


def _count_invalid_weights(weights: tuple[tuple[int, float], ...]) -> int:
    invalid_count = sum(
        not math.isfinite(weight) or not 0.0 <= weight <= 1.0
        for _, weight in weights
    )
    if not math.isclose(
        sum(weight for _, weight in weights),
        1.0,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        invalid_count += 1
    return invalid_count
