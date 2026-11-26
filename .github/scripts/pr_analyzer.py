#!/usr/bin/env python3
"""
Analisador proporcional de Pull Requests do repositório Aion Classic 5.0.
Classifica o escopo do PR (ex.: docs-only vs backend Java), gera labels automáticas,
valida integridade sintática/segurança e identifica melhorias aplicáveis via /autofix.
100% Python padrão (zero dependências externas).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

DOC_EXTENSIONS = {".md", ".markdown", ".txt", ".rst"}
DOC_ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
DOC_ASSET_MARKERS = (
    "/docs/",
    "/banner/",
    "auditorias e relatórios/",
    "blender - plugins/",
    "geo and nav builder",
    "patch final",
)

TEXT_CHECK_MAX_BYTES = 2 * 1024 * 1024
XML_CHECK_MAX_BYTES = 15 * 1024 * 1024

CC_TITLE_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|security|l10n)"
    r"(\([^)]+\))?!?: .+",
    re.IGNORECASE,
)
WIP_PREFIX_RE = re.compile(r"^(?:WIP\s*:|\[WIP\])\s*", re.IGNORECASE)

# Padrões restritos a segredos reais e caminhos pessoais vazados do computador local
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Chave privada exposta detectada", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("Token clássico do GitHub exposto", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b")),
    ("Token fine-grained do GitHub exposto", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Chave AWS Access Key ID exposta", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "Webhook privado de Discord/Slack exposto",
        re.compile(r"https://(?:discord(?:app)?\.com/api/webhooks|hooks\.slack\.com/services)/[^\s\"')>]+"),
    ),
    (
        "Caminho absoluto pessoal do Windows vazado (Users)",
        re.compile(r"(?i)[A-Za-z]:\\Users\\(?!<|\.\.\.|your|user|example|usuario|nome|seu_)([A-Za-z0-9._-]+)\\"),
    ),
    ("Caminho local privado detectado (D:\\GameForge)", re.compile(r"(?i)D:\\GameForge\\")),
    ("Caminho local privado detectado (I:\\Aion)", re.compile(r"(?i)I:\\Aion")),
    ("Caminho local privado detectado (E:\\Programas instalados)", re.compile(r"(?i)E:\\Programas instalados")),
)

SKIP_SCAN_PATHS = {
    ".github/scripts/pr_analyzer.py",
}

TRAILING_WS_EXTS = {".py", ".yml", ".yaml", ".json", ".xml", ".java"}
EOF_NL_EXTS = {".md", ".markdown", ".py", ".yml", ".yaml", ".json", ".xml", ".java", ".sh"}
LF_ONLY_MARKERS = (".github/workflows/",)

MD_LINK_RE = re.compile(r"(?<!\\)!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _norm_path(raw: str) -> str:
    return unicodedata.normalize("NFC", raw).replace("\\", "/").lstrip("/")


def _is_doc_or_doc_asset(path_str: str) -> bool:
    norm = _norm_path(path_str)
    low = norm.lower()
    p = Path(norm)
    ext = p.suffix.lower()
    if ext in DOC_EXTENSIONS or p.name.lower() in {"license", "license.md", "license.txt", "copying"}:
        return True
    if ext in DOC_ASSET_EXTENSIONS:
        if low.startswith(("docs/", ".github/")) or any(m in low for m in DOC_ASSET_MARKERS):
            return True
    return False


def _infer_area_labels(filenames: list[str]) -> set[str]:
    areas: set[str] = set()
    for f in filenames:
        low = _norm_path(f).lower()
        if "game-server-gameforge/" in low:
            areas.add("area/gameforge")
        elif "login-server/" in low:
            areas.add("area/login-server")
        elif "chat-server/" in low:
            areas.add("area/chat-server")
        elif "código fonte - emulador/commons/" in low or "codigo fonte - emulador/commons/" in low:
            areas.add("area/commons")
        elif "código fonte - version.dll/" in low or "códigos bin64/" in low:
            areas.add("area/version-dll")
        elif "blender - plugins/" in low:
            areas.add("area/blender-plugins")
        elif "geo and nav builder" in low:
            areas.add("area/geo-nav")
        elif low.startswith(".github/"):
            areas.add("area/ci")
        elif low.startswith(("ferramentas e documentos/", "emulador - produto final/")):
            if "/docs/" not in low and not low.startswith("ferramentas e documentos/docs/"):
                areas.add("area/tools")
    return areas


def _infer_size_label(total_changes: int) -> str:
    if total_changes <= 20:
        return "size/XS"
    if total_changes <= 100:
        return "size/S"
    if total_changes <= 400:
        return "size/M"
    if total_changes <= 1000:
        return "size/L"
    return "size/XL"


def _infer_kind_labels(title: str, author: str, is_docs_only: bool) -> set[str]:
    kinds: set[str] = set()
    low_author = author.lower()
    low_title = title.strip().lower()
    if low_author in {"dependabot[bot]", "renovate[bot]"} or low_title.startswith(("build(deps", "chore(deps")):
        kinds.add("kind/deps")
        return kinds

    cleaned = WIP_PREFIX_RE.sub("", title.strip())
    m = re.match(r"^([a-z0-9]+)(?:\([^)]+\))?!?:", cleaned, re.IGNORECASE)
    cc_type = m.group(1).lower() if m else ""
    if cc_type in {"fix", "revert"}:
        kinds.add("kind/bug")
    elif cc_type in {"feat", "l10n"}:
        kinds.add("kind/feature")
    elif cc_type == "perf":
        kinds.add("kind/perf")
    elif cc_type == "security":
        kinds.add("kind/security")
    elif cc_type in {"refactor", "style"}:
        kinds.add("kind/refactor")
    elif not is_docs_only and cc_type == "docs":
        kinds.add("documentation")
    return kinds


def _suggest_docs_title(title: str, filenames: list[str]) -> str:
    stripped = title.strip()
    if not stripped or WIP_PREFIX_RE.match(stripped) or CC_TITLE_RE.match(stripped):
        return ""

    low = stripped.lower()
    m_upd = re.match(r"^(update|edit|fix|modify)\s+(.+)$", stripped, re.IGNORECASE)
    m_add = re.match(r"^(create|add)\s+(.+)$", stripped, re.IGNORECASE)
    m_del = re.match(r"^(delete|remove)\s+(.+)$", stripped, re.IGNORECASE)

    if m_upd:
        candidate = f"docs: atualizar {m_upd.group(2).strip()}"
    elif m_add:
        candidate = f"docs: adicionar {m_add.group(2).strip()}"
    elif m_del:
        candidate = f"docs: remover {m_del.group(2).strip()}"
    elif low in {"update", "docs", "readme", "atualizacao", "atualização"} and len(filenames) == 1:
        candidate = f"docs: atualizar {Path(filenames[0]).name}"
    else:
        first_lower = stripped[0].lower() + stripped[1:] if len(stripped) > 1 else stripped.lower()
        candidate = f"docs: {first_lower}"

    if len(candidate) > 96:
        candidate = candidate[:93].rstrip() + "..."
    return candidate


def _extract_added_lines(patch: str) -> list[tuple[int, str]]:
    """Extrai `(linha_no_arquivo, conteudo)` apenas para linhas adicionadas (`+`) do patch unificado."""
    results: list[tuple[int, str]] = []
    cur_line = 0
    for raw_line in patch.splitlines():
        if raw_line.startswith("@@"):
            m = re.search(r"\+(\d+)(?:,\d+)?", raw_line)
            if m:
                cur_line = int(m.group(1))
            continue
        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue
        if raw_line.startswith("+"):
            results.append((max(1, cur_line), raw_line[1:]))
            cur_line += 1
        elif not raw_line.startswith("-"):
            cur_line += 1
    return results


def _resolve_safe_path(repo_root: Path, rel_path: str) -> Path | None:
    try:
        candidate = (repo_root / rel_path).resolve()
        root_res = repo_root.resolve()
        candidate.relative_to(root_res)
        return candidate
    except Exception:
        return None


def _validate_yaml(path_obj: Path, text: str) -> str | None:
    try:
        import yaml  # type: ignore

        try:
            yaml.safe_load(text)
            return None
        except Exception as exc:
            return f"YAML inválido: {exc}"
    except ImportError:
        pass

    ruby = shutil.which("ruby")
    if ruby:
        proc = subprocess.run(
            [ruby, "-ryaml", "-e", "YAML.load_file(ARGV[0])", str(path_obj)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "Erro de sintaxe YAML").strip().splitlines()[0]
            return f"YAML inválido: {err}"
        return None
    return "skipped_no_yaml_parser"


def _check_relative_markdown_links(repo_root: Path, md_path: Path, rel_path: str, text: str) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        s = line.lstrip()
        if s.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in MD_LINK_RE.finditer(line):
            raw_target = match.group(1).strip()
            if not raw_target or "{{" in raw_target or "}}" in raw_target:
                continue
            low_t = raw_target.lower()
            if low_t.startswith(("http://", "https://", "mailto:", "file://", "#", "tel:")):
                continue
            clean_target = urllib.parse.unquote(raw_target.split("#", 1)[0].split("?", 1)[0]).strip()
            if not clean_target:
                continue
            target_path = (
                (repo_root / clean_target.lstrip("/"))
                if clean_target.startswith("/")
                else (md_path.parent / clean_target)
            )
            try:
                resolved = target_path.resolve()
                resolved.relative_to(repo_root.resolve())
            except Exception:
                continue
            if not resolved.exists():
                warnings.append(
                    {
                        "file": rel_path,
                        "line": line_no,
                        "rule": "markdown-link",
                        "message": f"Link relativo possivelmente quebrado: `{raw_target}`",
                    }
                )
    return warnings


def analyze_pr(
    *,
    files_data: list[dict[str, Any]],
    event_data: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    title = str(event_data.get("title") or "").strip()
    author = str(event_data.get("author") or "unknown").strip()
    repo_owner = str(event_data.get("repo_owner") or "").strip()
    head_sha = str(event_data.get("head_sha") or "").strip()
    pr_number = int(event_data.get("pr_number") or 0)
    is_fork = bool(event_data.get("is_fork"))
    draft = bool(event_data.get("draft"))
    is_owner = bool(repo_owner and author.lower() == repo_owner.lower())
    is_bot = author.lower() in {"dependabot[bot]", "renovate[bot]", "github-actions[bot]"}

    filenames = [_norm_path(str(item.get("filename") or "")) for item in files_data if item.get("filename")]
    doc_files = [f for f in filenames if _is_doc_or_doc_asset(f)]
    is_docs_only = bool(filenames) and len(doc_files) == len(filenames)
    needs_java_build = any(
        f.startswith("Código Fonte - Emulador/") or f == ".github/workflows/ci-backend.yml"
        for f in filenames
    )

    additions = sum(int(item.get("additions") or 0) for item in files_data)
    deletions = sum(int(item.get("deletions") or 0) for item in files_data)
    total_changes = sum(int(item.get("changes") or 0) for item in files_data) or (additions + deletions)

    labels: set[str] = set()
    if doc_files:
        labels.add("documentation")
    if is_docs_only:
        labels.add("docs-only")
    labels.update(_infer_area_labels(filenames))
    labels.add(_infer_size_label(total_changes))
    labels.update(_infer_kind_labels(title, author, is_docs_only))

    blocking_issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    autofix_candidates: set[str] = set()
    checks_run: list[str] = ["leak_scan", "syntax_check", "policy_check"]

    if is_docs_only:
        checks_run.append("docs_fast_track")
        checks_run.append("markdown_link_hints")
    elif needs_java_build:
        checks_run.append("requires_java_ci")

    yaml_parser_noted = False

    for item in files_data:
        rel_path = _norm_path(str(item.get("filename") or ""))
        if not rel_path:
            continue
        status = str(item.get("status") or "modified").lower()
        low_path = rel_path.lower()

        # Política proporcional de GSID 2 / GSID 3: só bloqueia alterações em código de servidores auxiliares por terceiros
        if not is_owner and (
            low_path.startswith("código fonte - emulador/game-server-battleroyale/")
            or low_path.startswith("código fonte - emulador/game-server-remake/")
        ):
            blocking_issues.append(
                {
                    "file": rel_path,
                    "line": 1,
                    "rule": "gsid-scope",
                    "message": (
                        "Contribuições externas devem manter o escopo exclusivo no GameServer 1 "
                        "(GameForge GSID 1) — não modificar game-server-remake ou game-server-battleroyale."
                    ),
                }
            )

        if status == "removed":
            continue

        disk_path = _resolve_safe_path(repo_root, rel_path)
        if disk_path is None or not disk_path.is_file():
            continue

        raw_bytes: bytes | None = None
        file_size = disk_path.stat().st_size

        # 1. Varredura de segredos / caminhos pessoais vazados (nas linhas adicionadas ou arquivo novo)
        if rel_path not in SKIP_SCAN_PATHS:
            patch = item.get("patch")
            lines_to_scan: list[tuple[int, str]] = []
            if isinstance(patch, str) and patch.strip():
                lines_to_scan = _extract_added_lines(patch)
            elif file_size <= TEXT_CHECK_MAX_BYTES:
                raw_bytes = disk_path.read_bytes()
                if b"\x00" not in raw_bytes[:1024]:
                    text_tmp = raw_bytes.decode("utf-8", errors="ignore")
                    lines_to_scan = list(enumerate(text_tmp.splitlines(), start=1))

            for line_no, content in lines_to_scan:
                for label_msg, pat in SECRET_PATTERNS:
                    if pat.search(content):
                        blocking_issues.append(
                            {
                                "file": rel_path,
                                "line": line_no,
                                "rule": "security-leak",
                                "message": label_msg,
                            }
                        )

        # 2. Leitura segura para validação sintática / higiene textual
        ext = disk_path.suffix.lower()
        need_text = ext in {".py", ".json", ".yml", ".yaml", ".xml", ".md", ".markdown", ".java", ".sh"}
        if not need_text:
            continue

        if raw_bytes is None:
            limit = XML_CHECK_MAX_BYTES if ext == ".xml" else TEXT_CHECK_MAX_BYTES
            if file_size > limit:
                continue
            raw_bytes = disk_path.read_bytes()

        if b"\x00" in raw_bytes[:512]:
            # Binário (ex.: BXML do cliente Aion) — ignorar checagem de XML/texto
            continue

        text = raw_bytes.decode("utf-8", errors="replace")

        if ext == ".py":
            try:
                ast.parse(text, filename=rel_path)
            except SyntaxError as exc:
                blocking_issues.append(
                    {
                        "file": rel_path,
                        "line": exc.lineno or 1,
                        "rule": "python-syntax",
                        "message": f"Erro de sintaxe Python: {exc.msg}",
                    }
                )
        elif ext == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                blocking_issues.append(
                    {
                        "file": rel_path,
                        "line": exc.lineno or 1,
                        "rule": "json-syntax",
                        "message": f"JSON inválido: {exc.msg}",
                    }
                )
        elif ext == ".xml":
            try:
                ET.fromstring(text)
            except ET.ParseError as exc:
                lineno = exc.position[0] if getattr(exc, "position", None) else 1
                blocking_issues.append(
                    {
                        "file": rel_path,
                        "line": lineno,
                        "rule": "xml-syntax",
                        "message": f"XML malformado: {exc}",
                    }
                )
        elif ext in {".yml", ".yaml"}:
            yml_res = _validate_yaml(disk_path, text)
            if yml_res == "skipped_no_yaml_parser":
                if not yaml_parser_noted:
                    yaml_parser_noted = True
                    checks_run.append("yaml_parser_unavailable")
            elif yml_res is not None:
                blocking_issues.append(
                    {
                        "file": rel_path,
                        "line": 1,
                        "rule": "yaml-syntax",
                        "message": yml_res,
                    }
                )

        if ext in {".md", ".markdown"}:
            warnings.extend(_check_relative_markdown_links(repo_root, disk_path, rel_path, text))

        # 3. Candidatos seguros para /autofix (nunca bloqueia o PR)
        needs_fix = False
        if (any(low_path.startswith(m) for m in LF_ONLY_MARKERS) or ext == ".sh") and b"\r\n" in raw_bytes:
            needs_fix = True
        if ext in EOF_NL_EXTS and len(raw_bytes) > 0 and not raw_bytes.endswith(b"\n"):
            needs_fix = True
        if ext in TRAILING_WS_EXTS and any(ln != ln.rstrip(" \t") for ln in text.splitlines()):
            needs_fix = True
        if needs_fix:
            autofix_candidates.add(rel_path)

    suggested_title = _suggest_docs_title(title, filenames) if is_docs_only else ""

    return {
        "schema_version": "1.0",
        "pr_number": pr_number,
        "head_sha": head_sha,
        "author": author,
        "is_owner": is_owner,
        "is_bot": is_bot,
        "is_fork": is_fork,
        "draft": draft,
        "title": title,
        "suggested_title": suggested_title,
        "is_docs_only": is_docs_only,
        "needs_java_build": needs_java_build,
        "stats": {
            "files_changed": len(filenames),
            "doc_files": len(doc_files),
            "additions": additions,
            "deletions": deletions,
            "total_changes": total_changes,
        },
        "labels": sorted(labels),
        "checks_run": checks_run,
        "blocking_issues": blocking_issues,
        "warnings": warnings[:25],
        "autofix_candidates": sorted(autofix_candidates),
        "passed": len(blocking_issues) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisador proporcional de PRs.")
    parser.add_argument("--files-json", required=True, help="Caminho do JSON de arquivos alterados.")
    parser.add_argument("--event-json", required=True, help="Caminho do JSON de metadados do PR.")
    parser.add_argument("--repo-root", default=".", help="Diretório raiz do repositório.")
    parser.add_argument("--output", required=True, help="Arquivo de saída pr-review-report.json.")
    args = parser.parse_args()

    files_data = json.loads(Path(args.files_json).read_text(encoding="utf-8"))
    event_data = json.loads(Path(args.event_json).read_text(encoding="utf-8"))
    report = analyze_pr(
        files_data=files_data if isinstance(files_data, list) else [],
        event_data=event_data if isinstance(event_data, dict) else {},
        repo_root=Path(args.repo_root),
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
