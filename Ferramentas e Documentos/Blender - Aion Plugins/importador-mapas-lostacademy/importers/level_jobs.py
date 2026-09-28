from dataclasses import dataclass

from aion_formats.level import BrushList, ObjectsList


SOURCE_OBJECT = "OBJECT"
SOURCE_BRUSH = "BRUSH"


@dataclass(frozen=True)
class LevelCgfJob:
    source_type: str
    source_index: int
    cgf_reference: str
    import_mode: str
    cache_key: tuple[str, str]
    position: tuple[float, float, float] | None = None
    scale: float | None = None
    heading_raw: int | None = None
    heading_degrees: float | None = None
    transform: tuple[float, ...] | None = None
    mesh_index: int | None = None
    category: str = "PROPS"


@dataclass(frozen=True)
class UnresolvedCgfReference:
    source_type: str
    source_index: int
    reason: str
    reference_index: int | None = None


@dataclass(frozen=True)
class LevelCgfJobs:
    jobs: tuple[LevelCgfJob, ...]
    unresolved: tuple[UnresolvedCgfReference, ...]

    @property
    def object_jobs(self) -> tuple[LevelCgfJob, ...]:
        return tuple(job for job in self.jobs if job.source_type == SOURCE_OBJECT)

    @property
    def brush_jobs(self) -> tuple[LevelCgfJob, ...]:
        return tuple(job for job in self.jobs if job.source_type == SOURCE_BRUSH)


def _cache_key(cgf_reference: str, import_mode: str) -> tuple[str, str]:
    return (cgf_reference.replace("\\", "/").lower(), import_mode)


def _is_invisible_collision_ref(ref: str) -> bool:
    clean = str(ref).lower().replace("\\", "/")
    return (
        "collision_wall" in clean
        or "/nodraw/" in clean
        or "nowalk_obstacle" in clean
        or "walk_obstacle" in clean
        or "/col_" in clean
        or "_col." in clean
        or "/collision/" in clean
    )


def classify_cgf_category(ref: str) -> str:
    """
    Classifies a CGF reference path into a logical scene collection category.
    Returns: 'COLLISION', 'VEGETATION', 'ROCKS', 'BUILDINGS', or 'PROPS'.
    """
    clean = str(ref).lower().replace("\\", "/")
    if _is_invisible_collision_ref(clean):
        return "COLLISION"

    # Rocks & Natural Formations
    if any(k in clean for k in ("rock", "stone", "boulder", "cliff", "stalagmite", "icicle", "crystal", "/cave/")):
        return "ROCKS"

    # Vegetation
    if any(k in clean for k in (
        "tree", "greens", "trunk", "branch", "pine", "oak", "palm", "birch",
        "grass", "reed", "weed", "lawn",
        "plant", "flower", "bush", "shrub", "vine", "leaf", "aquatic", "odella",
        "pumpkin", "crop", "lotus", "waterleaf", "mushgrass",
    )):
        return "VEGETATION"

    # Effects & Particles
    if any(k in clean for k in ("effect", "particle", "/fx/", "_fx.")):
        return "EFFECTS"

    # Buildings & Structures
    if any(k in clean for k in (
        "structure", "building", "house", "wall", "bridge", "tower", "temple",
        "castle", "ruin", "dungeon", "fortress", "stairs", "roof", "fence",
        "pillar", "arch", "door", "gate", "portal",
    )):
        return "BUILDINGS"

    # Default to PROPS (camp items, barrels, signs, milestones, etc.)
    return "PROPS"


def should_import_cgf_ref(
    ref: str,
    *,
    import_mode: str = "VISUAL",
    import_buildings: bool = True,
    import_structures: bool = True,
    import_doors_portals: bool = True,
    import_props: bool = True,
    import_rocks: bool = True,
    import_interactive_objects: bool = True,
    import_vegetation: bool = True,
    import_trees: bool = True,
    import_grass: bool = True,
    import_bushes_flowers: bool = True,
    import_collision: bool = True,
    import_lod0: bool = True,
    import_lod1: bool = True,
    import_lod2: bool = True,
    import_lod3: bool = True,
) -> bool:
    """Checks whether a CGF reference should be imported according to granular options."""
    clean = str(ref).lower().replace("\\", "/")

    # 1. LOD Filter
    if "_lod3." in clean:
        if not import_lod3:
            return False
    elif "_lod2." in clean:
        if not import_lod2:
            return False
    elif "_lod1." in clean:
        if not import_lod1:
            return False
    else:
        if not import_lod0:
            return False

    # 2. Collision Filter
    is_col = _is_invisible_collision_ref(clean)
    if import_mode == "COLLISION":
        return is_col

    if is_col and not import_collision:
        return False

    # 3. Category Filter
    # Vegetation sub-categories
    if any(k in clean for k in ("tree", "greens", "trunk", "branch", "pine", "oak", "palm", "birch")):
        return import_vegetation and import_trees
    if any(k in clean for k in ("grass", "reed", "weed", "lawn", "mushgrass")):
        return import_vegetation and import_grass
    if any(k in clean for k in ("plant", "flower", "bush", "shrub", "vine", "leaf", "aquatic", "odella", "pumpkin", "crop", "lotus", "waterleaf")):
        return import_vegetation and import_bushes_flowers

    # Rocks & Natural
    if any(k in clean for k in ("rock", "stone", "boulder", "cliff", "stalagmite", "icicle", "crystal", "/cave/")):
        return import_props and import_rocks

    # Doors / Portals
    if any(k in clean for k in ("door", "gate", "portal")):
        return import_buildings and import_doors_portals

    # Structures / Buildings
    if any(k in clean for k in ("structure", "building", "house", "wall", "bridge", "tower", "temple", "castle", "ruin", "dungeon", "fortress", "stairs", "roof", "fence", "pillar", "arch")):
        return import_buildings and import_structures

    # Interactive objects / Signs
    if any(k in clean for k in ("milestone", "sign", "board", "altar", "burner", "pedestal", "obelisk", "items/")):
        return import_props and import_interactive_objects

    # Other props
    return import_props


def collect_level_cgf_jobs(
    objects: ObjectsList | None,
    brush: BrushList | None,
    import_mode: str = "VISUAL",
    *,
    import_buildings: bool = True,
    import_structures: bool = True,
    import_doors_portals: bool = True,
    import_props: bool = True,
    import_rocks: bool = True,
    import_interactive_objects: bool = True,
    import_vegetation: bool = True,
    import_trees: bool = True,
    import_grass: bool = True,
    import_bushes_flowers: bool = True,
    import_collision: bool = True,
    import_lod0: bool = True,
    import_lod1: bool = True,
    import_lod2: bool = True,
    import_lod3: bool = True,
) -> LevelCgfJobs:
    jobs = []
    unresolved = []

    filter_kwargs = {
        "import_mode": import_mode,
        "import_buildings": import_buildings,
        "import_structures": import_structures,
        "import_doors_portals": import_doors_portals,
        "import_props": import_props,
        "import_rocks": import_rocks,
        "import_interactive_objects": import_interactive_objects,
        "import_vegetation": import_vegetation,
        "import_trees": import_trees,
        "import_grass": import_grass,
        "import_bushes_flowers": import_bushes_flowers,
        "import_collision": import_collision,
        "import_lod0": import_lod0,
        "import_lod1": import_lod1,
        "import_lod2": import_lod2,
        "import_lod3": import_lod3,
    }

    if objects is not None:
        for index, placement in enumerate(objects.placements):
            if not placement.vegetation_file:
                unresolved.append(
                    UnresolvedCgfReference(
                        source_type=SOURCE_OBJECT,
                        source_index=index,
                        reason="missing vegetation file reference",
                        reference_index=placement.vegetation_index,
                    )
                )
                continue

            if not should_import_cgf_ref(placement.vegetation_file, **filter_kwargs):
                continue

            category = classify_cgf_category(placement.vegetation_file)
            jobs.append(
                LevelCgfJob(
                    source_type=SOURCE_OBJECT,
                    source_index=index,
                    cgf_reference=placement.vegetation_file,
                    import_mode=import_mode,
                    cache_key=_cache_key(placement.vegetation_file, import_mode),
                    position=placement.position,
                    scale=placement.scale,
                    heading_raw=placement.heading_raw,
                    heading_degrees=placement.heading_degrees,
                    category=category,
                )
            )

    if brush is not None:
        for node in brush.nodes:
            if not node.mesh_file_name:
                unresolved.append(
                    UnresolvedCgfReference(
                        source_type=SOURCE_BRUSH,
                        source_index=node.index,
                        reason="missing brush mesh reference",
                        reference_index=node.mesh_index,
                    )
                )
                continue

            if not should_import_cgf_ref(node.mesh_file_name, **filter_kwargs):
                continue

            category = classify_cgf_category(node.mesh_file_name)
            jobs.append(
                LevelCgfJob(
                    source_type=SOURCE_BRUSH,
                    source_index=node.index,
                    cgf_reference=node.mesh_file_name,
                    import_mode=import_mode,
                    cache_key=_cache_key(node.mesh_file_name, import_mode),
                    transform=node.transform,
                    mesh_index=node.mesh_index,
                    category=category,
                )
            )

    return LevelCgfJobs(jobs=tuple(jobs), unresolved=tuple(unresolved))
