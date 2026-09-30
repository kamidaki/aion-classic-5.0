"""
CGF / CGA / CAF / CAL format parsers and writers.
"""

from .parser import get_cgf
from .caf_parser import parse_caf
from .caf_writer import write_caf
from .cal_parser import parse_cal, find_default_idle_animation
from .cal_writer import write_cal

__all__ = [
    "get_cgf",
    "parse_caf",
    "write_caf",
    "parse_cal",
    "find_default_idle_animation",
    "write_cal",
]
