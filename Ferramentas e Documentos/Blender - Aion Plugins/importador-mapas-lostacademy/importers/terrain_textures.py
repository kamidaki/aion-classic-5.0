from dataclasses import dataclass
from pathlib import Path

from core.pak_engine import get_pak_resolver


@dataclass(frozen=True)
class TerrainDetailTextureReference:
    raw_path: str
    normalized_relative_path: str
    resolved_path: str | None
    exists: bool


def resolve_terrain_detail_texture(
    client_root: str | Path | None,
    detail_texture: str | None,
) -> TerrainDetailTextureReference:
    raw_path = detail_texture or ""
    normalized_relative_path = raw_path.replace("\\", "/").lstrip("/")

    if not client_root or not normalized_relative_path:
        return TerrainDetailTextureReference(
            raw_path=raw_path,
            normalized_relative_path=normalized_relative_path,
            resolved_path=None,
            exists=False,
        )

    root_path = Path(client_root)
    resolved_path = root_path / Path(*normalized_relative_path.split("/"))

    if not resolved_path.is_file():
        parts = normalized_relative_path.split("/")
        if len(parts) >= 2 and parts[0].lower() == "levels":
            level_name = parts[1]
            sub_path = Path(*parts[2:])
            cand_cache = root_path / "levels" / level_name / ".aion_cache" / sub_path
            if cand_cache.is_file():
                resolved_path = cand_cache
            else:
                file_name = parts[-1]
                cand_detail = root_path / "levels" / level_name / ".aion_cache" / "detail" / file_name
                if cand_detail.is_file():
                    resolved_path = cand_detail
                else:
                    detail_dir = root_path / "levels" / level_name / ".aion_cache" / "detail"
                    if detail_dir.is_dir():
                        for cand in detail_dir.glob("*.dds"):
                            if cand.name.lower() == file_name.lower():
                                resolved_path = cand
                                break

    if not resolved_path.is_file():
        # Check cache directory or pak archives
        resolver = get_pak_resolver(root_path)
        if resolver is not None:
            pak_res = resolver.resolve_resource(normalized_relative_path)
            if pak_res and pak_res.is_file():
                resolved_path = pak_res

    exists = resolved_path.is_file()
    return TerrainDetailTextureReference(
        raw_path=raw_path,
        normalized_relative_path=normalized_relative_path,
        resolved_path=str(resolved_path) if exists else str(resolved_path),
        exists=exists,
    )
