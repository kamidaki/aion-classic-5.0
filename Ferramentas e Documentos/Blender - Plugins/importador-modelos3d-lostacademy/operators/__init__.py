"""
Operators package for LostAcademy Aion Model Library.
"""

from . import library_ops
from . import viewer_ops
from . import animation_ops
from . import editing_ops
from . import save_ops
from . import creation_ops
from . import sound_ops
from . import effect_ops

MODULES = (
    library_ops,
    viewer_ops,
    animation_ops,
    editing_ops,
    save_ops,
    creation_ops,
    sound_ops,
    effect_ops,
)


def register() -> None:
    for mod in MODULES:
        mod.register()


def unregister() -> None:
    for mod in reversed(MODULES):
        mod.unregister()
