"""
Resource Resolver for Level CGF Jobs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from .pak_engine import AionClientPakResolver, get_pak_resolver


@dataclass(frozen=True)
class ResolvedLevelCgfJob:
    job: object
    resolved_path: Path
    normalized_reference: str = ""


@dataclass(frozen=True)
class LevelCgfResolutionResult:
    resolved: tuple[ResolvedLevelCgfJob, ...]
    missing: tuple[object, ...]


def resolve_level_cgf_jobs(
    jobs: Iterable[object],
    client_root: Path,
    target_lod: int = 0,
    max_workers: int = 1,
) -> LevelCgfResolutionResult:
    """
    Resolves each CGF job's file reference using the AionClientPakResolver.
    Deduplicates unique CGF paths and resolves sequentially (max_workers=1 default)
    to prevent disk thrashing on weak CPUs/HDDs.
    Supports target_lod (0..3) to resolve companion LOD meshes (<stem>_lod<N>.cgf).
    """
    resolver = get_pak_resolver(client_root)
    jobs_list = list(jobs)
    if not jobs_list:
        return LevelCgfResolutionResult(resolved=(), missing=())

    # 1. Deduplicate unique CGF references
    unique_refs: Dict[str, str] = {}  # normalized -> original
    job_refs: list[tuple[object, str]] = []
    for job in jobs_list:
        ref = getattr(job, "cgf_reference", "")
        if not ref:
            job_refs.append((job, ""))
            continue
        norm = str(ref).replace("\\", "/").strip().lstrip("/")
        if norm and norm not in unique_refs:
            unique_refs[norm] = str(ref)
        job_refs.append((job, norm))

    # 2. Resolve unique references (defaults to sequential single-worker extraction)
    resolved_paths: Dict[str, Optional[Path]] = {}
    if resolver and unique_refs:
        if max_workers <= 1:
            resolver.ensure_catalog()
            for norm, orig in unique_refs.items():
                p_res = resolver.resolve_resource(orig, target_lod=target_lod)
                if p_res and p_res.is_file():
                    resolved_paths[norm] = p_res
        else:
            batch_results = resolver.resolve_resources_batch(
                unique_refs.values(), max_workers=max_workers, target_lod=target_lod
            )
            for orig_ref, p_res in batch_results.items():
                norm = orig_ref.replace("\\", "/").strip().lstrip("/")
                if p_res and p_res.is_file():
                    resolved_paths[norm] = p_res

            # Fallback query for any unreturned reference
            for norm, orig in unique_refs.items():
                if norm not in resolved_paths:
                    p_res = resolver.resolve_resource(orig, target_lod=target_lod)
                    if p_res and p_res.is_file():
                        resolved_paths[norm] = p_res

    # 3. Fast O(1) in-memory mapping to original jobs
    resolved = []
    missing = []
    for job, norm in job_refs:
        if norm and norm in resolved_paths:
            resolved.append(
                ResolvedLevelCgfJob(
                    job=job,
                    resolved_path=resolved_paths[norm],
                    normalized_reference=norm,
                )
            )
        else:
            missing.append(job)

    return LevelCgfResolutionResult(
        resolved=tuple(resolved),
        missing=tuple(missing),
    )
