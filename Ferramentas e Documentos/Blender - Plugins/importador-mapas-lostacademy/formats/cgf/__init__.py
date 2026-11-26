"""
Aion CGF Format Parser and Shader Semantics Package.
"""

from .parser import get_cgf
from .diagnostics import CgfDiagnosticsCollector
from .shader_semantics import (
    ClientShaderSemantics,
    resolve_client_shader_semantics,
)
from .texture_sequences import (
    TextureSequencePattern,
    TextureSequenceResolution,
    resolve_texture_sequence,
    parse_texture_sequence_pattern,
)

__all__ = [
    "get_cgf",
    "CgfDiagnosticsCollector",
    "ClientShaderSemantics",
    "resolve_client_shader_semantics",
    "TextureSequencePattern",
    "TextureSequenceResolution",
    "resolve_texture_sequence",
    "parse_texture_sequence_pattern",
]
