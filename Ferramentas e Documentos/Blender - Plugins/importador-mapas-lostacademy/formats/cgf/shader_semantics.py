"""
Shader Semantics Parser for Aion CryEngine Shaders.

Reads shader techniques (.csl) and includes (.csi) both from loose disk folders
AND directly from the client's Shaders/shaders.pak archive.
"""

from __future__ import annotations

import re
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


UNKNOWN_NOT_DECODED = "unknown_not_decoded"


@dataclass(frozen=True)
class ClientShaderSemantics:
    shader_name: str
    resolved_shader_name: str
    definition_path: str
    include_paths: tuple[str, ...]
    blend_mode: str
    blend_equation: str
    alpha_mode: str
    sort_mode: str
    cull_mode: str
    two_sided: bool
    no_auto_depth_write: bool
    has_alpha_test: bool
    has_vertex_colors: bool
    no_shadows: bool
    uv_scroll_confirmed: bool
    uv_scroll_source: str
    uv_scroll_param: str
    uv_scroll_speed_x: float | None
    uv_scroll_speed_y: float | None
    uv_scroll_target_slot: str
    uv_scroll_target_layer: str
    uv_scroll_static_mask_slot: str
    alpha_source: str
    color_formula: str
    shader_layers: tuple[dict[str, str], ...]
    semantics_source: tuple[str, ...]

    def to_dict(self):
        return asdict(self)


# Thread-safe in-memory caches for shader texts and O(1) indexed blocks
_SHADER_LOCK = threading.RLock()
_SHADER_FILES_CACHE: Dict[str, Dict[str, str]] = {}  # client_root -> {rel_path_lower: text}
_SHADER_BLOCK_INDEX: Dict[str, Dict[str, Tuple[str, str, str]]] = {}  # client_root -> {key: (rel, name, block)}
_SEMANTICS_CACHE: Dict[Tuple[str, str], Optional[ClientShaderSemantics]] = {}
_ROOT_KEY_CACHE: Dict[str, str] = {}
_SHADER_DECL_RE = re.compile(r"Shader\s+['\"]([^'\"]+)['\"]\s*(?P<body>[{(])", re.IGNORECASE)


def _index_shader_blocks(shader_cache: Dict[str, str]) -> Dict[str, Tuple[str, str, str]]:
    block_index: Dict[str, Tuple[str, str, str]] = {}
    for rel_path, text in shader_cache.items():
        if not rel_path.endswith(".csl"):
            continue
        for match in _SHADER_DECL_RE.finditer(text):
            name = match.group(1).strip()
            opener = match.group("body")
            closer = "}" if opener == "{" else ")"
            start = match.start()
            end = _matching_block_end(text, match.end() - 1, opener, closer)
            entry = (rel_path, name, text[start:end])
            low = name.lower()
            norm = low.replace("_", "")
            block_index.setdefault(low, entry)
            block_index.setdefault(norm, entry)
    return block_index


def _ensure_shader_cache(client_root: Path) -> Dict[str, str]:
    root_key = str(client_root.resolve()).lower()
    with _SHADER_LOCK:
        if root_key in _SHADER_FILES_CACHE:
            return _SHADER_FILES_CACHE[root_key]

        cache: Dict[str, str] = {}
        shaders_dir = client_root / "Shaders"

        # 1. Read from Shaders/shaders.pak if available (always close archive handle!)
        shaders_pak = shaders_dir / "shaders.pak"
        if shaders_pak.is_file():
            try:
                from core.pak_engine import AionPakArchive
                with AionPakArchive(shaders_pak) as arc:
                    for lower_name, entry in arc.entries.items():
                        if lower_name.endswith((".csl", ".csi", ".ext")):
                            data = arc.read_entry(entry)
                            if data:
                                cache[lower_name] = data.decode("utf-8", errors="replace")
            except Exception:
                pass

        # 2. Read any loose files on disk (overrides pak if present)
        if shaders_dir.is_dir():
            for path in shaders_dir.rglob("*"):
                if path.is_file() and path.suffix.lower() in (".csl", ".csi", ".ext"):
                    try:
                        rel = path.relative_to(shaders_dir).as_posix().lower()
                        cache[rel] = path.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        pass

        # Keep bounded to avoid stale multi-client bloat
        if len(_SHADER_FILES_CACHE) >= 2:
            _SHADER_FILES_CACHE.clear()
            _SHADER_BLOCK_INDEX.clear()
            _SEMANTICS_CACHE.clear()
            _ROOT_KEY_CACHE.clear()

        _SHADER_FILES_CACHE[root_key] = cache
        _SHADER_BLOCK_INDEX[root_key] = _index_shader_blocks(cache)
        return cache


def resolve_client_shader_semantics(
    arg1: str | Path | None = None,
    arg2: str | Path | None = None,
    *,
    client_root: str | Path | None = None,
    shader_name: str | None = None,
) -> Optional[ClientShaderSemantics]:
    actual_root = client_root
    actual_shader = shader_name

    # Determine whether arg1 is client_root or shader_name (avoid filesystem stat when separators present)
    if arg1 is not None:
        s_arg1 = str(arg1).strip()
        if (
            actual_root is None
            and (
                "/" in s_arg1
                or "\\" in s_arg1
                or (":" in s_arg1)
                or Path(s_arg1).is_dir()
            )
        ):
            actual_root = s_arg1
            if arg2 is not None and actual_shader is None:
                actual_shader = str(arg2).strip()
        else:
            if actual_shader is None:
                actual_shader = s_arg1
            if arg2 is not None and actual_root is None:
                actual_root = arg2

    actual_shader = str(actual_shader or "").strip()
    if not actual_shader or not actual_root:
        return None

    raw_root_str = str(actual_root).strip()
    with _SHADER_LOCK:
        root_key = _ROOT_KEY_CACHE.get(raw_root_str)
    if root_key is None:
        root_path = Path(raw_root_str)
        root_key = str(root_path.resolve()).lower()
        with _SHADER_LOCK:
            _ROOT_KEY_CACHE[raw_root_str] = root_key
    else:
        root_path = Path(raw_root_str)

    sem_key = (root_key, actual_shader.lower())
    with _SHADER_LOCK:
        if sem_key in _SEMANTICS_CACHE:
            return _SEMANTICS_CACHE[sem_key]

    shader_cache = _ensure_shader_cache(root_path)
    if not shader_cache:
        with _SHADER_LOCK:
            _SEMANTICS_CACHE[sem_key] = None
        return None

    with _SHADER_LOCK:
        block_index = _SHADER_BLOCK_INDEX.get(root_key)
    shader_block = None
    if block_index is not None:
        shader_block = block_index.get(actual_shader.lower()) or block_index.get(actual_shader.lower().replace("_", ""))
    if shader_block is None:
        shader_block = _find_shader_block_cached(shader_cache, actual_shader)
    if shader_block is None:
        with _SHADER_LOCK:
            _SEMANTICS_CACHE[sem_key] = None
        return None

    definition_rel, resolved_name, block = shader_block
    include_paths, include_text = _resolve_includes_cached(shader_cache, definition_rel, block)
    combined_text = f"{block}\n{include_text}"

    blend_equation = _first_blend_equation(combined_text)
    sort_mode = _first_param_value(block, "Sort")
    cull_mode = _first_param_value(combined_text, "Cull")
    no_auto_depth_write = bool(re.search(r"\bNoAutoDepthWrite\b", combined_text, re.IGNORECASE))
    has_alpha_test = bool(re.search(r"\bHasAlphaTest\b", combined_text, re.IGNORECASE))
    has_vcolors = bool(re.search(r"\bHasVColors\b", combined_text, re.IGNORECASE))
    no_shadows = bool(re.search(r"\bNoCastShadows\b", combined_text, re.IGNORECASE))

    two_sided = (
        _two_sided_from_cull(cull_mode)
        or bool(re.search(r"\bCull\s*=\s*(?:None|TwoSided)\b", combined_text, re.IGNORECASE))
        or "leaf" in actual_shader.lower()
        or "plant" in actual_shader.lower()
    )

    shader_layers = _shader_layers(combined_text)
    uv_scroll = _texshift_uv_scroll(combined_text, shader_layers)

    sources = ["client_shader.definition"]
    if include_paths:
        sources.append("client_shader.include")
    if blend_equation:
        sources.append("client_shader.blend")
    if cull_mode or two_sided:
        sources.append("client_shader.cull")
    if has_alpha_test:
        sources.append("client_shader.alpha_test")
    if uv_scroll["confirmed"]:
        sources.append("client_shader.uv_scroll")

    semantics_obj = ClientShaderSemantics(
        shader_name=actual_shader,
        resolved_shader_name=resolved_name,
        definition_path=definition_rel,
        include_paths=tuple(include_paths),
        blend_mode=_blend_mode_from_equation(blend_equation),
        blend_equation=blend_equation,
        alpha_mode="alpha_test" if has_alpha_test else UNKNOWN_NOT_DECODED,
        sort_mode=sort_mode,
        cull_mode=cull_mode,
        two_sided=two_sided,
        no_auto_depth_write=no_auto_depth_write,
        has_alpha_test=has_alpha_test,
        has_vertex_colors=has_vcolors,
        no_shadows=no_shadows,
        uv_scroll_confirmed=uv_scroll["confirmed"],
        uv_scroll_source=uv_scroll["source"],
        uv_scroll_param=uv_scroll["param"],
        uv_scroll_speed_x=uv_scroll["speed_x"],
        uv_scroll_speed_y=uv_scroll["speed_y"],
        uv_scroll_target_slot=uv_scroll["target_slot"],
        uv_scroll_target_layer=uv_scroll["target_layer"],
        uv_scroll_static_mask_slot=uv_scroll["static_mask_slot"],
        alpha_source=uv_scroll["alpha_source"],
        color_formula=uv_scroll["color_formula"],
        shader_layers=shader_layers,
        semantics_source=tuple(sources),
    )
    with _SHADER_LOCK:
        _SEMANTICS_CACHE[sem_key] = semantics_obj
    return semantics_obj


def _find_shader_block_cached(
    shader_cache: Dict[str, str],
    shader_name: str,
) -> Optional[Tuple[str, str, str]]:
    wanted = shader_name.lower().replace("_", "")
    pattern = re.compile(r"Shader\s+['\"]([^'\"]+)['\"]\s*(?P<body>[{(])", re.IGNORECASE)

    for rel_path, text in shader_cache.items():
        if not rel_path.endswith(".csl"):
            continue
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            norm_name = name.lower().replace("_", "")
            if norm_name == wanted or name.lower() == shader_name.lower():
                opener = match.group("body")
                closer = "}" if opener == "{" else ")"
                start = match.start()
                end = _matching_block_end(text, match.end() - 1, opener, closer)
                return rel_path, name, text[start:end]

    return None


def _resolve_includes_cached(
    shader_cache: Dict[str, str],
    definition_rel: str,
    block: str,
) -> Tuple[List[str], str]:
    include_paths = []
    include_texts = []
    def_parent = str(Path(definition_rel).parent).replace("\\", "/")

    for match in re.finditer(r'#include\s+["<]([^">]+)[">]', block, re.IGNORECASE):
        inc_rel = match.group(1).replace("\\", "/")
        # Try relative to parent
        cand = f"{def_parent}/{inc_rel}".replace("//", "/")
        norm_cand = Path(cand).as_posix().lower()
        if norm_cand in shader_cache:
            include_paths.append(norm_cand)
            include_texts.append(shader_cache[norm_cand])
            continue

        # Try base name
        inc_base = inc_rel.split("/")[-1].lower()
        for k, v in shader_cache.items():
            if k.endswith(inc_base):
                include_paths.append(k)
                include_texts.append(v)
                break

    return include_paths, "\n".join(include_texts)


def _matching_block_end(text: str, opener_index: int, opener: str, closer: str) -> int:
    depth = 0
    for index in range(opener_index, len(text)):
        char = text[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index + 1
    return len(text)


def _first_param_value(text: str, key: str) -> str:
    pattern = rf"(?i)\b{re.escape(key)}\b\s*=\s*([A-Za-z0-9_]+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _two_sided_from_cull(cull_mode: str) -> bool:
    mode = str(cull_mode or "").lower()
    return mode in ("none", "twosided")


def _first_blend_equation(text: str) -> str:
    match = re.search(
        r"(?i)\b(?:Blend|SrcBlend|DestBlend|BlendEquation)\b\s*=?\s*([A-Za-z0-9_\s+*/,]+?)(?=[;\n\r}]|$)",
        text,
    )
    if not match:
        return ""
    return " ".join(match.group(1).split())


def _blend_mode_from_equation(blend_equation: str) -> str:
    eq = str(blend_equation or "").lower()
    if not eq:
        return UNKNOWN_NOT_DECODED
    if "one" in eq and ("add" in eq or "plus" in eq or eq.endswith("one")):
        return "additive"
    if "srcalpha" in eq:
        return "alpha_blend"
    return UNKNOWN_NOT_DECODED


def _shader_layers(text: str) -> tuple[dict[str, str], ...]:
    layers = []
    layer_pattern = re.compile(r"Layer\s*(?P<body>[{(])", re.IGNORECASE)
    for match in layer_pattern.finditer(text):
        opener = match.group("body")
        closer = "}" if opener == "{" else ")"
        end = _matching_block_end(text, match.end() - 1, opener, closer)
        layer_block = text[match.start():end]
        layer_info = {}
        for line in layer_block.splitlines():
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                layer_info[k.strip().lower()] = v.strip().rstrip(";")
        if layer_info:
            layers.append(layer_info)
    return tuple(layers)


def _texshift_uv_scroll(text: str, shader_layers: tuple[dict[str, str], ...]) -> dict:
    result = {
        "confirmed": False,
        "source": "",
        "param": "",
        "speed_x": None,
        "speed_y": None,
        "target_slot": "",
        "target_layer": "",
        "static_mask_slot": "",
        "alpha_source": "",
        "color_formula": "",
    }
    match = re.search(r"(?i)\bTexShift\s*=\s*\(([^)]+)\)", text)
    if match:
        parts = [p.strip() for p in match.group(1).split(",")]
        try:
            result["speed_x"] = float(parts[0]) if len(parts) > 0 else 0.0
            result["speed_y"] = float(parts[1]) if len(parts) > 1 else 0.0
            result["confirmed"] = True
            result["source"] = "TexShift"
            result["param"] = match.group(0)
        except ValueError:
            pass
    elif "shiftspeed" in text.lower() or "opacityshift" in text.lower():
        result["confirmed"] = True
        result["source"] = "shiftspeedY"
        result["param"] = "shiftspeedY"
        result["speed_x"] = 0.0
        result["speed_y"] = -0.015
    return result
