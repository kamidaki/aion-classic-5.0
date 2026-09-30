"""
UI package for LostAcademy Aion Model Library.
"""

from . import panels
from . import menus
from . import npc_editor_panel


def register() -> None:
    panels.register()
    menus.register()
    npc_editor_panel.register()


def unregister() -> None:
    npc_editor_panel.unregister()
    menus.unregister()
    panels.unregister()
