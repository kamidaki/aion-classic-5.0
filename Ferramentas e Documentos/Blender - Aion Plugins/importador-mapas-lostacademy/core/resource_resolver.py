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
) -> LevelCgfResolutionResult:
    """
    Resolves each CGF job's file reference using the AionClientPakResolver.
    """
    resolver = get_pak_resolver(client_root)
    resolved = []
    missing = []

    for job in jobs:
        ref = getattr(job, "cgf_reference", "")
        if not ref:
            missing.append(job)
            continue

        normalized_ref = str(ref).replace("\\", "/").strip().lstrip("/")
        resolved_path = resolver.resolve_resource(ref) if resolver else None
        if resolved_path and resolved_path.is_file():
            resolved.append(
                ResolvedLevelCgfJob(
                    job=job,
                    resolved_path=resolved_path,
                    normalized_reference=normalized_ref,
                )
            )
        else:
            missing.append(job)

    return LevelCgfResolutionResult(
        resolved=tuple(resolved),
        missing=tuple(missing),
    )
