"""
Blender Property Definitions for LostAcademy Aion Model Library.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Optional

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

from ..config.settings import (
    DEFAULT_CLIENT_PATHS,
    KNOWN_CATEGORIES,
    SAFETY_ALLOW_CLIENT_WRITE_DEFAULT,
)


class AionAnimItem(bpy.types.PropertyGroup):
    """Represents an animation entry belonging to a model's CAL list."""
    name: StringProperty(name="Anim Name", default="")
    caf_path: StringProperty(name="CAF Path", default="")


class AionAssetItem(bpy.types.PropertyGroup):
    """Represents a single model asset in the UI asset list."""
    asset_id: StringProperty(name="Asset ID", default="")
    name: StringProperty(name="Name", default="")
    category: StringProperty(name="Category", default="OTHER")
    model_path: StringProperty(name="Model Path", default="")
    skeleton_path: StringProperty(name="Skeleton Path", default="")
    cal_path: StringProperty(name="CAL Path", default="")
    poly_count: IntProperty(name="Polygons", default=0)
    vertex_count: IntProperty(name="Vertices", default=0)
    bone_count: IntProperty(name="Bones", default=0)
    anim_count: IntProperty(name="Animations", default=0)
    has_thumbnail: BoolProperty(name="Has Thumbnail", default=False)
    thumbnail_path: StringProperty(name="Thumbnail Path", default="")
    is_modified: BoolProperty(name="Modified", default=False)


def on_filter_updated(self: Any, context: bpy.types.Context) -> None:
    """Invoked when search text or category filter changes."""
    # Triggers operator to refresh filtered collection if database is loaded
    try:
        bpy.ops.aion_model.filter_assets()
    except Exception:
        pass


class AionModelLibrarySettings(bpy.types.PropertyGroup):
    """Main settings and state for the Aion Model Library addon."""

    # Client Selection
    client_path: StringProperty(
        name="Pasta do Cliente",
        description="Caminho raiz do cliente Aion (contendo as pastas Data, Objects, etc.)",
        subtype='DIR_PATH',
        default=DEFAULT_CLIENT_PATHS[0] if DEFAULT_CLIENT_PATHS else "",
    )
    client_flavor: StringProperty(
        name="Versão do Cliente",
        description="Geração ou versão detectada do cliente Aion",
        default="Não Detectado",
    )

    # Safety
    allow_client_write: BoolProperty(
        name="Permitir Gravação no Cliente",
        description="CHAVE DE SEGURANÇA: Habilita modificar e gravar diretamente dentro dos arquivos/PAKs oficiais do jogo. Quando desativado, alterações são salvas na Pasta Segura de Exportação.",
        default=SAFETY_ALLOW_CLIENT_WRITE_DEFAULT,
    )
    auto_backup: BoolProperty(
        name="Backups Automáticos",
        description="Sempre cria cópias de segurança (.bak ou .pak.bak) antes de alterar qualquer arquivo do cliente",
        default=True,
    )
    export_fallback_dir: StringProperty(
        name="Pasta Segura de Exportação",
        description="Diretório de destino para exportação de arquivos quando a gravação direta estiver desativada",
        subtype='DIR_PATH',
        default="",
    )

    # Search & Filtering
    search_query: StringProperty(
        name="Buscar",
        description="Pesquisar modelos por nome, ID ou caminho de arquivo",
        default="",
        update=on_filter_updated,
    )
    category_filter: EnumProperty(
        name="Categoria",
        description="Filtrar modelos por categoria",
        items=KNOWN_CATEGORIES,
        default="ALL",
        update=on_filter_updated,
    )

    # Scanned asset list
    asset_items: CollectionProperty(type=AionAssetItem)
    active_asset_index: IntProperty(
        name="Índice do Modelo Ativo",
        default=0,
    )
    scanned_total_count: IntProperty(
        name="Total de Modelos Escaneados",
        default=0,
    )

    # Active loaded asset metadata
    active_asset_id: StringProperty(name="ID do Modelo", default="")
    active_asset_name: StringProperty(name="Nome do Modelo", default="")
    active_category: StringProperty(name="Categoria", default="")
    active_model_path: StringProperty(name="Caminho do Modelo", default="")
    active_skeleton_path: StringProperty(name="Caminho do Esqueleto", default="")
    active_cal_path: StringProperty(name="Caminho do CAL", default="")
    active_is_modified: BoolProperty(name="Modificado", default=False)
    active_poly_count: IntProperty(name="Polígonos", default=0)
    active_vertex_count: IntProperty(name="Vértices", default=0)
    active_bone_count: IntProperty(name="Ossos", default=0)

    # Animations of active loaded asset
    active_anims: CollectionProperty(type=AionAnimItem)
    active_anim_index: IntProperty(name="Índice da Animação", default=0)

    # Viewport & Display
    studio_lighting: BoolProperty(
        name="Iluminação de Estúdio",
        description="Adiciona sistema de 3 pontos de luz ao palco de visualização",
        default=True,
    )
    camera_auto_frame: BoolProperty(
        name="Enquadramento Automático da Câmera",
        description="Enquadra automaticamente a câmera no modelo carregado",
        default=True,
    )
    show_armature: BoolProperty(
        name="Exibir Ossos",
        description="Alterna visibilidade dos ossos do esqueleto na viewport 3D",
        default=True,
    )
    bone_display_type: EnumProperty(
        name="Exibição de Ossos",
        items=[
            ('OCTAHEDRAL', 'Octaédrico', 'Exibição padrão octaédrica'),
            ('STICK', 'Haste', 'Exibição simples em hastes'),
            ('BBONE', 'B-Bone', 'Exibição curvada / Bendy Bone'),
            ('WIRE', 'Aramado', 'Exibição em linhas aramadas'),
        ],
        default='OCTAHEDRAL',
    )

    # Character Dressing Room & Class Preview
    preview_mode: EnumProperty(
        name="Modo de Visualização",
        description="Alterna entre visualizar o item isolado ou no corpo de um personagem",
        items=[
            ('ISOLATED', 'Item Isolado', 'Renderiza apenas o modelo 3D selecionado'),
            ('ON_BODY', 'No Corpo do Personagem', 'Equipa e renderiza o item diretamente no corpo do personagem'),
        ],
        default='ISOLATED',
    )
    character_race: EnumProperty(
        name="Raça e Gênero",
        description="Selecione a raça e gênero do personagem para o provador",
        items=[
            ('LF', 'Elyos Mulher (LF)', 'Elyos Feminino'),
            ('LM', 'Elyos Homem (LM)', 'Elyos Masculino'),
            ('DF', 'Asmodian Mulher (DF)', 'Asmodian Feminino'),
            ('DM', 'Asmodian Homem (DM)', 'Asmodian Masculino'),
        ],
        default='LF',
    )
    character_class: EnumProperty(
        name="Classe",
        description="Selecione a classe Aion para visualizar conjunto completo de armadura e armas",
        items=[
            ('GLADIATOR', 'Gladiador', 'Gladiador (Placas, Espadão / Lança)'),
            ('TEMPLAR', 'Templário', 'Templário (Placas, Espada + Escudo)'),
            ('RANGER', 'Arqueiro', 'Arqueiro (Couro, Arco)'),
            ('ASSASSIN', 'Assassino', 'Assassino (Couro, Duplas Adagas)'),
            ('SORCERER', 'Feiticeiro', 'Feiticeiro (Tecido, Orbe / Livro)'),
            ('SPIRITMASTER', 'Espiritualista', 'Espiritualista (Tecido, Orbe / Livro)'),
            ('CLERIC', 'Clérigo', 'Clérigo (Malha, Maça + Escudo)'),
            ('CHANTER', 'Cantor', 'Cantor (Malha, Cajado)'),
            ('GUNSLINGER', 'Atirador', 'Atirador (Couro, Pistolas Mágicas)'),
            ('SONGWEAVER', 'Bardo', 'Bardo (Tecido, Harpa)'),
            ('AETHERTECH', 'Cavaleiro Mecânico', 'Cavaleiro Mecânico (Malha, Chave Espada / Robô)'),
        ],
        default='GLADIATOR',
    )
    auto_complete_humanoid: BoolProperty(
        name="Auto-Completar Corpo Humanoide",
        description="Anexa automaticamente cabeça, cabelo, mãos e pés correspondentes em roupas modulares ou NPCs",
        default=True,
    )

    # Creation & Cloning
    new_asset_id: StringProperty(name="ID do Novo Modelo", default="custom_mesh_01")
    new_category: EnumProperty(
        name="Nova Categoria",
        items=[c for c in KNOWN_CATEGORIES if c[0] != "ALL"],
        default="PROP",
    )
    new_model_path: StringProperty(
        name="Caminho do Novo Modelo",
        default="objects/custom/custom_mesh_01.cgf",
    )
    clone_new_id: StringProperty(name="ID do Modelo Clonado", default="cloned_asset_01")
    clone_new_path: StringProperty(
        name="Caminho do Modelo Clonado",
        default="objects/custom/cloned_asset_01.cgf",
    )


CLASSES = (
    AionAnimItem,
    AionAssetItem,
    AionModelLibrarySettings,
)


def register_properties() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.aion_model_lib = PointerProperty(type=AionModelLibrarySettings)


def unregister_properties() -> None:
    if hasattr(bpy.types.Scene, "aion_model_lib"):
        del bpy.types.Scene.aion_model_lib
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
