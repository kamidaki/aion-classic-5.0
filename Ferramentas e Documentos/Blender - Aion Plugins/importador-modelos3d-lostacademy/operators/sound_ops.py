"""
Sound Operators for LostAcademy Aion Model Library.
Provides operators for playing, stopping, and browsing model audio clips.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import bpy
from bpy.props import IntProperty, StringProperty

from ..core.pak_engine import AionCatalogIndex
from ..indexer.asset_database import AssetDatabase
from ..providers.sound_provider import SoundProvider

logger = logging.getLogger("AionModelLibrary.SoundOps")


def get_sound_provider(client_path: str) -> Optional[SoundProvider]:
    """Returns or initializes the SoundProvider instance."""
    if not client_path:
        return None
    root = Path(client_path)
    if not root.is_dir():
        return None
    catalog = AionCatalogIndex(root)
    return SoundProvider.get(catalog, root)


class AION_OT_play_model_sound(bpy.types.Operator):
    """Plays the selected sound effect or voice clip for the loaded 3D model."""
    bl_idname = "aion_model.play_sound"
    bl_label = "Tocar Som"
    bl_description = "Reproduz o áudio selecionado através do motor de áudio nativo"
    bl_options = {"REGISTER"}

    sound_index: IntProperty(name="Índice do Som", default=-1)

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.client_path:
            self.report({"WARNING"}, "Configure a pasta do cliente Aion primeiro.")
            return {"CANCELLED"}

        sp = get_sound_provider(settings.client_path)
        if not sp:
            self.report({"ERROR"}, "Falha ao inicializar o motor de som.")
            return {"CANCELLED"}

        if not settings.model_sounds:
            self.report({"INFO"}, "Nenhum som carregado para este modelo.")
            return {"CANCELLED"}

        idx = self.sound_index
        if idx < 0 or idx >= len(settings.model_sounds):
            idx = settings.active_sound_index

        if idx < 0 or idx >= len(settings.model_sounds):
            return {"CANCELLED"}

        item = settings.model_sounds[idx]
        ok = sp.play_sound(
            sound_rel_or_file=item.file,
            volume=settings.sound_volume,
            pitch=settings.sound_pitch,
        )

        if ok:
            self.report({"INFO"}, f"Reproduzindo: {item.name}")
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, f"Não foi possível reproduzir: {item.name}")
            return {"CANCELLED"}


class AION_OT_stop_model_sound(bpy.types.Operator):
    """Stops all active audio playback immediately."""
    bl_idname = "aion_model.stop_sound"
    bl_label = "Parar Som"
    bl_description = "Interrompe qualquer reprodução de áudio ativa"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if settings.client_path:
            sp = get_sound_provider(settings.client_path)
            if sp:
                sp.stop_all_sounds()
        self.report({"INFO"}, "Áudio interrompido.")
        return {"FINISHED"}


class AION_OT_refresh_model_sounds(bpy.types.Operator):
    """Refreshes and populates the sound list for the currently inspected 3D model."""
    bl_idname = "aion_model.refresh_sounds"
    bl_label = "Atualizar Sons do Modelo"
    bl_description = "Descobre e lista todos os efeitos sonoros e vozes disponíveis para o modelo ativo"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.aion_model_lib
        if not settings.client_path or not settings.asset_items:
            return {"CANCELLED"}

        idx = settings.active_asset_index
        if idx < 0 or idx >= len(settings.asset_items):
            return {"CANCELLED"}

        active_asset = settings.asset_items[idx]
        db = AssetDatabase.get()
        entry = db.get_by_id(active_asset.asset_id)
        if not entry:
            return {"CANCELLED"}

        sp = get_sound_provider(settings.client_path)
        if not sp:
            return {"CANCELLED"}

        discovered = sp.get_sounds_for_model(entry)
        settings.model_sounds.clear()

        for s in discovered:
            item = settings.model_sounds.add()
            item.name = s.get("name", "")
            item.file = s.get("file", "")
            item.category = s.get("category", "EFEITO")
            item.anim_name = s.get("anim_name", "")
            item.when = float(s.get("when", 0.0))

        settings.active_sound_index = 0
        self.report({"INFO"}, f"{len(discovered)} sons encontrados para {entry.name}.")
        return {"FINISHED"}


CLASSES = (
    AION_OT_play_model_sound,
    AION_OT_stop_model_sound,
    AION_OT_refresh_model_sounds,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
