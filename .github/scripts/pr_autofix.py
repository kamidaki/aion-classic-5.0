#!/usr/bin/env python3
"""
Auto-correção segura e determinística para Pull Requests (/autofix).
Aplica somente normalizações mecânicas de higiene em arquivos modificados:
- Converte CRLF -> LF em workflows (.github/workflows/*.yml|*.yaml) e scripts .sh
- Remove espaços extras no fim das linhas em arquivos de código/config (.py, .yml, .yaml, .json, .xml, .java)
  (preserva espaços finais em Markdown para não quebrar quebras de linha intencionais)
- Garante exatamente uma quebra de linha final (EOF) em arquivos de texto não vazios
100% Python padrão.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TRAILING_WS_EXTS = {".py", ".yml", ".yaml", ".json", ".xml", ".java"}
EOF_NL_EXTS = {".md", ".markdown", ".py", ".yml", ".yaml", ".json", ".xml", ".java", ".sh"}
MAX_AUTOFIX_BYTES = 2 * 1024 * 1024


def fix_text_file(repo_root: Path, rel_path: str) -> list[str]:
    norm = rel_path.replace("\\", "/").lstrip("/")
    root_res = repo_root.resolve()
    try:
        target = (root_res / norm).resolve()
        target.relative_to(root_res)
    except Exception:
        return []

    if not target.is_file() or target.stat().st_size == 0 or target.stat().st_size > MAX_AUTOFIX_BYTES:
        return []

    raw = target.read_bytes()
    if b"\x00" in raw[:512]:
        return []

    ext = target.suffix.lower()
    low = norm.lower()
    if ext not in EOF_NL_EXTS:
        return []

    actions: list[str] = []
    force_lf = low.startswith(".github/workflows/") or ext == ".sh"
    had_crlf = b"\r\n" in raw
    newline = "\n" if (force_lf or not had_crlf) else "\r\n"

    text = raw.decode("utf-8", errors="strict")
    lines = text.splitlines()

    if force_lf and had_crlf:
        actions.append("CRLF->LF")

    if ext in TRAILING_WS_EXTS:
        stripped = [ln.rstrip(" \t") for ln in lines]
        if stripped != lines:
            lines = stripped
            actions.append("trim-trailing-spaces")

    rebuilt = newline.join(lines) + newline
    new_bytes = rebuilt.encode("utf-8")

    if not raw.endswith(b"\n"):
        actions.append("add-eof-newline")

    if new_bytes != raw:
        target.write_bytes(new_bytes)
        if not actions:
            actions.append("normalize-whitespace")
        return actions

    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-correção segura para arquivos do PR.")
    parser.add_argument("--repo-root", default=".", help="Diretório raiz do repositório.")
    parser.add_argument("--files", nargs="*", default=[], help="Arquivos relativos alterados pelo PR.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    modified: list[dict[str, object]] = []
    for rel in args.files:
        applied = fix_text_file(repo_root, rel)
        if applied:
            modified.append({"file": rel.replace("\\", "/"), "fixes": applied})

    print(json.dumps({"modified_count": len(modified), "modified": modified}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
