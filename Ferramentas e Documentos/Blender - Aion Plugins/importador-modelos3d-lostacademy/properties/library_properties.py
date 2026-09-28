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


class AionSoundItem(bpy.types.PropertyGroup):
    """Represents a discovered sound effect or voice track for the loaded model."""
    name: StringProperty(name="Nome do Som", default="")
    file: StringProperty(name="Arquivo", default="")
    category: StringProperty(name="Categoria", default="EFEITO")
    anim_name: StringProperty(name="Animação", default="")
    when: FloatProperty(name="Momento (s)", default=0.0)



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


# ---------------------------------------------------------------------------
# Cache global para o EnumProperty de classes — NUNCA fazer I/O no callback!
# ---------------------------------------------------------------------------
_CACHED_CLASSES = None

_CLASSES_FALLBACK = [
    ("GLADIATOR", "Gladiador", "Gladiador (Placas, Espadão / Lança)"),
    ("TEMPLAR", "Templário", "Templário (Placas, Espada + Escudo)"),
    ("RANGER", "Arqueiro", "Arqueiro (Couro, Arco)"),
    ("ASSASSIN", "Assassino", "Assassino (Couro, Duplas Adagas)"),
    ("SORCERER", "Feiticeiro", "Feiticeiro (Tecido, Orbe / Livro)"),
    ("SPIRITMASTER", "Espiritualista", "Espiritualista (Tecido, Orbe / Livro)"),
    ("CLERIC", "Clérigo", "Clérigo (Malha, Maça + Escudo)"),
    ("CHANTER", "Cantor", "Cantor (Malha, Cajado)"),
]


def get_character_classes_callback(self: Any, context: Optional[bpy.types.Context]) -> List[Tuple[str, str, str]]:
    """Retorna classes de personagem a partir do cache global — SEM I/O de disco.

    O cache é populado de forma assíncrona por :func:`populate_classes_cache`.
    Enquanto não populado, retorna o FALLBACK estático imediatamente para que
    a UI não congele.
    """
    global _CACHED_CLASSES
    if _CACHED_CLASSES is not None:
        return _CACHED_CLASSES
    return _CLASSES_FALLBACK


def invalidate_classes_cache() -> None:
    """Zera o cache de classes, forçando recarga na próxima chamada a populate_classes_cache."""
    global _CACHED_CLASSES
    _CACHED_CLASSES = None


def populate_classes_cache(client_path: str) -> None:
    """Popula o cache de classes fazendo I/O em uma thread de background.

    Deve ser chamada após o usuário definir/alterar o caminho do cliente,
    NUNCA dentro de um callback de propriedade ou redesenho de UI.

    Args:
        client_path: Caminho raiz do cliente Aion.
    """
    import threading

    def _worker():
        global _CACHED_CLASSES
        try:
            if not client_path or not Path(client_path).is_dir():
                return
            from ..core.client_provider import AionClientProvider
            cp = AionClientProvider(client_path)
            result = cp.get_available_classes()
            if result:
                _CACHED_CLASSES = result
        except Exception:
            pass  # Mantém o FALLBACK em caso de erro

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


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
    filter_omitted_count: IntProperty(
        name="Resultados Omitidos",
        description="Número de modelos ocultados pelo limite de exibição de 200 itens",
        default=0,
    )

    # Active loaded asset metadata
    active_asset_id: StringProperty(name="ID do Modelo", default="")
    active_asset_name: StringProperty(name="Nome do Modelo", default="")
    active_category: StringProperty(name="Categoria", default="")
    active_model_path: StringProperty(name="Caminho do Modelo", default="")
    active_asset_path: StringProperty(name="Caminho do Asset (Alias)", default="")
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
        items=get_character_classes_callback,
    )
    auto_complete_humanoid: BoolProperty(
        name="Auto-Completar Corpo Humanoide",
        description="Anexa automaticamente cabeça, cabelo, mãos e pés correspondentes em roupas modulares ou NPCs",
        default=True,
    )

    # Multi-Model Viewport
    multi_model_mode: BoolProperty(
        name="Modo Multi-Modelo (Fileira)",
        description="Quando ativo, cada novo modelo é posicionado ao lado dos já carregados em vez de substituir. Cria uma fileira comparativa.",
        default=False,
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

    # Audio & Sound System
    enable_sound: BoolProperty(
        name="Ativar Áudio dos Modelos",
        description="Permite reproduzir efeitos sonoros, vozes de monstros/NPCs e impactos de combate",
        default=True,
    )
    sound_volume: FloatProperty(
        name="Volume do Áudio",
        description="Controle de volume para reprodução dos sons dos modelos 3D",
        default=1.0,
        min=0.0,
        max=2.0,
    )
    sound_pitch: FloatProperty(
        name="Pitch / Velocidade",
        description="Ajuste de afinação e velocidade do som",
        default=1.0,
        min=0.5,
        max=2.0,
    )
    model_sounds: CollectionProperty(type=AionSoundItem)
    active_sound_index: IntProperty(name="Som Selecionado", default=0)

    # Visual Effects (VFX) System
    enable_vfx: BoolProperty(
        name="Ativar Efeitos Visuais (VFX)",
        description="Aplica auras mágicas elementais, emissão de brilho e luzes nos sockets do modelo",
        default=False,
    )
    vfx_element: EnumProperty(
        name="Elemento VFX",
        description="Selecione o elemento ou tema visual do efeito",
        items=[
            ("FIRE", "Fogo / Chamas", "Chamas rubras e brasas ardentes"),
            ("FROST", "Gelo / Geada", "Gelo ciano e névoa ártica cintilante"),
            ("LIGHTNING", "Eletricidade / Raios", "Faíscas elétricas e relâmpagos"),
            ("SHADOW", "Sombra / Trevas", "Vórtice sombrio e aura de trevas"),
            ("POISON", "Veneno / Ácido", "Glow cáustico esmeralda tóxico"),
            ("DIVINE", "Sagrado / Celestial", "Luz celestial dourada e radiante"),
            ("AION_AETHER", "Aether Clássico (Aion)", "Energia aethérica azul e ciano"),
        ],
        default="FIRE",
    )
    vfx_intensity: FloatProperty(
        name="Intensidade VFX",
        description="Multiplicador de intensidade para brilho emissivo, luzes e partículas",
        default=1.0,
        min=0.1,
        max=5.0,
    )
    vfx_show_glow: BoolProperty(
        name="Brilho Emissivo (Shader)",
        description="Ativa brilho emissivo com pulsação suave nos materiais da malha",
        default=True,
    )
    vfx_show_lights: BoolProperty(
        name="Luzes nos Sockets",
        description="Cria fontes de luz pontuais nos sockets (olhos, mãos, cabeça)",
        default=True,
    )
    vfx_show_particles: BoolProperty(
        name="Emissores de Partículas",
        description="Cria emissores de partículas mágicas anexados aos sockets",
        default=True,
    )


CLASSES = (
    AionAnimItem,
    AionSoundItem,
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

