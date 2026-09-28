"""
UI package for LostAcademy Aion Model Library.
"""

from . import panels
from . import menus


def register() -> None:
    panels.register()
    menus.register()


def unregister() -> None:
    menus.unregister()
    panels.unregister()
