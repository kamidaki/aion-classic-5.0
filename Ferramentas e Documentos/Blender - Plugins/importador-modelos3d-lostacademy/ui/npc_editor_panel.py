"""
NPC Editor Panel for LostAcademy Aion Model Library.
Provides a sidebar panel for creating and editing Aion NPC data,
writing transactionally to both the active Aion client (data/npcs/npcs.pak and
data/Strings/Strings.pak) and the emulator static data (npc_templates.xml).
"""
from __future__ import annotations

from pathlib import Path
import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

PANEL_CATEGORY = "Modelos Aion"


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class AionNPCCreatorSettings(bpy.types.PropertyGroup):
    """Settings for the NPC Creator/Editor panel."""

    # --- Identification ---
    npc_id: IntProperty(
        name="ID do NPC",
        description="ID numérico único do NPC no cliente e emulador",
        default=900001,
        min=200000,
        max=9999999,
    )
    npc_name: StringProperty(
        name="Nome",
        description="Nome de exibição do NPC no jogo",
        default="Novo NPC",
    )
    npc_name_id: IntProperty(
        name="ID da String",
        description="ID numérico na tabela de strings (client_strings_npc.xml)",
        default=799999,
    )
    npc_string_key: StringProperty(
        name="Chave de String",
        description="Identificador STR_ na tabela de strings",
        default="STR_NPC_NOVO_NPC",
    )

    # --- Mesh & Visual Representation ---
    npc_dir: StringProperty(
        name="Diretório da Malha",
        description="Caminho relativo da pasta da malha (ex: NPC/ShugoMale, Monster/Brax)",
        default="NPC/ShugoMale",
    )
    npc_mesh: StringProperty(
        name="Nome da Malha",
        description="Nome base do arquivo CGF (sem extensão)",
        default="ShugoMale",
    )
    npc_material: StringProperty(
        name="Material",
        description="Identificador do material CryEngine do cliente",
        default="mat_mob_reptile",
    )
    npc_foot_mat: StringProperty(
        name="Material dos Pés",
        description="Tipo de material de passos para efeitos sonoros",
        default="foot_etc",
    )
    npc_scale: FloatProperty(
        name="Escala (%)",
        description="Escala percentual da malha no mundo (100 = 1.0x)",
        default=100.0,
        min=1.0,
        max=1000.0,
    )
    npc_weapon_scale: FloatProperty(
        name="Escala da Arma (%)",
        description="Escala percentual de armas acopladas",
        default=100.0,
        min=1.0,
        max=1000.0,
    )

    # --- Combat attributes ---
    npc_level: IntProperty(name="Nível", default=1, min=1, max=100)
    npc_height: FloatProperty(name="Altura", default=1.0, min=0.1, max=10.0)
    npc_max_hp: IntProperty(name="HP Máximo", default=10000, min=1)
    npc_rank: EnumProperty(
        name="Rank",
        items=[
            ("NOVICE", "NOVICE", ""),
            ("DISCIPLINED", "DISCIPLINED", ""),
            ("SEASONED", "SEASONED", ""),
            ("EXPERT", "EXPERT", ""),
            ("VETERAN", "VETERAN", ""),
            ("MASTER", "MASTER", ""),
        ],
        default="NOVICE",
    )
    npc_rating: EnumProperty(
        name="Rating",
        items=[
            ("JUNK", "JUNK", ""),
            ("NORMAL", "NORMAL", ""),
            ("ELITE", "ELITE", ""),
            ("HERO", "HERO", ""),
            ("LEGENDARY", "LEGENDARY", ""),
        ],
        default="NORMAL",
    )

    # --- Classification ---
    npc_race: StringProperty(name="Raça", default="")
    npc_tribe: StringProperty(name="Tribo", default="GENERAL")
    npc_type: StringProperty(name="Tipo", default="GENERAL")

    # --- Behaviour ---
    npc_ai: EnumProperty(
        name="IA",
        items=[
            ("general", "General", "Comportamento geral passivo"),
            ("homing", "Homing / Agressivo", "Persegue o jogador"),
            ("skillarea", "SkillArea", "Usa habilidades em área"),
            ("merchant", "Merchant", "NPC de loja"),
            ("npc", "Quest NPC", "NPC de missão"),
            ("stand", "Static / Stand", "NPC estático"),
        ],
        default="general",
    )
    npc_srange: IntProperty(name="Alcance de Visão", default=10, min=0)
    npc_sangle: IntProperty(name="Ângulo de Visão", default=240, min=0, max=360)

    # --- Movement ---
    npc_walk_speed: FloatProperty(name="Velocidade de Caminhada", default=2.0, min=0.0)
    npc_run_speed: FloatProperty(name="Velocidade de Corrida", default=6.0, min=0.0)

    # --- Collision ---
    npc_bound_front: FloatProperty(name="Raio Frontal", default=0.5, min=0.0)
    npc_bound_side: FloatProperty(name="Raio Lateral", default=0.5, min=0.0)
    npc_bound_upper: FloatProperty(name="Raio Superior", default=2.0, min=0.0)

    # --- Export options ---
    export_to_client: BoolProperty(
        name="Exportar para Cliente (npcs.pak / Strings.pak)",
        description="Injeta registros em data/npcs/npcs.pak e data/Strings/Strings.pak",
        default=True,
    )
    export_to_emulator: BoolProperty(
        name="Exportar para Emulador (npc_templates.xml)",
        description="Cria registro correspondente no npc_templates.xml do emulador",
        default=True,
    )


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class AION_OT_fill_from_active_stage(bpy.types.Operator):
    """Auto-populates NPC creator fields from the active stage model."""

    bl_idname = "aion_model.fill_from_active_stage"
    bl_label = "Preencher com Modelo Ativo"
    bl_description = "Preenche automaticamente os campos de malha e nome com o modelo ativo no palco"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        settings = context.scene.aion_model_lib
        npc_s = context.scene.aion_npc_creator

        if not settings.active_model_path:
            self.report({"WARNING"}, "Nenhum modelo carregado no palco.")
            return {"CANCELLED"}

        model_path = Path(settings.active_model_path.replace("\\", "/"))
        npc_s.npc_mesh = model_path.stem
        # Dir relative to objects/ (e.g. NPC/ShugoMale or Monster/Brax)
        parent_parts = model_path.parent.parts
        if "objects" in [p.lower() for p in parent_parts]:
            obj_idx = [p.lower() for p in parent_parts].index("objects")
            npc_s.npc_dir = "/".join(parent_parts[obj_idx + 1:])
        else:
            npc_s.npc_dir = str(model_path.parent).replace("\\", "/")

        if settings.active_asset_name:
            npc_s.npc_name = settings.active_asset_name
            clean_tag = "".join(c if c.isalnum() else "_" for c in settings.active_asset_name).upper()
            npc_s.npc_string_key = f"STR_NPC_{clean_tag}"

        self.report({"INFO"}, f"Campos preenchidos a partir de {model_path.stem}")
        return {"FINISHED"}


class AION_OT_create_npc(bpy.types.Operator):
    """Creates a new NPC in both the Aion Client and the Emulator static data."""

    bl_idname = "aion_model.create_npc"
    bl_label = "Criar NPC no Cliente e Emulador"
    bl_description = "Executa a gravação transacional do NPC nos arquivos do cliente e emulador"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        settings = context.scene.aion_model_lib
        npc_s = context.scene.aion_npc_creator

        if not settings.client_path:
            self.report({"ERROR"}, "Configure a pasta do cliente Aion primeiro.")
            return {"CANCELLED"}

        from ..exporters.npc_metadata import AionNPCMetadata

        metadata = AionNPCMetadata(
            npc_id=npc_s.npc_id,
            name=npc_s.npc_name,
            desc=npc_s.npc_string_key,
            string_id=npc_s.npc_name_id,
            string_body=npc_s.npc_name,
            dir=npc_s.npc_dir,
            mesh=npc_s.npc_mesh,
            material=npc_s.npc_material,
            foot_mat=npc_s.npc_foot_mat,
            bound_front=npc_s.npc_bound_front,
            bound_side=npc_s.npc_bound_side,
            bound_upper=npc_s.npc_bound_upper,
            scale=npc_s.npc_scale,
            weapon_scale=npc_s.npc_weapon_scale,
            level=npc_s.npc_level,
            max_hp=npc_s.npc_max_hp,
            rank=npc_s.npc_rank,
            rating=npc_s.npc_rating,
            race=npc_s.npc_race,
            tribe=npc_s.npc_tribe,
            npc_type=npc_s.npc_type,
            ai_name=npc_s.npc_ai,
            sensory_range=float(npc_s.npc_srange),
            sangle=npc_s.npc_sangle,
            move_speed_normal_walk=npc_s.npc_walk_speed,
            move_speed_normal_run=npc_s.npc_run_speed,
        )

        messages = []

        # 1. Export to Client
        if npc_s.export_to_client:
            from ..exporters.client_exporter import ClientNPCExporter
            try:
                tx_res = ClientNPCExporter.export_npc_to_client(
                    client_root=settings.client_path,
                    metadata=metadata,
                    allow_client_write=settings.allow_client_write,
                )
                if not tx_res.success:
                    self.report({"ERROR"}, f"Falha na exportação para cliente: {tx_res.message}")
                    return {"CANCELLED"}
                messages.append("Cliente atualizado com sucesso")
            except Exception as exc:
                self.report({"ERROR"}, f"Erro ao exportar para cliente: {exc}")
                return {"CANCELLED"}

        # 2. Export to Emulator
        if npc_s.export_to_emulator:
            from ..exporters.emulator_exporter import EmulatorExporter
            try:
                exp = EmulatorExporter()
                if exp.npc_id_exists(npc_s.npc_id):
                    self.report(
                        {"WARNING"},
                        f"NPC ID {npc_s.npc_id} já existe no emulador!",
                    )
                else:
                    exp.export_npc(**metadata.to_emulator_dict())
                    messages.append("Emulador atualizado (npc_templates.xml)")
            except Exception as exc:
                self.report({"ERROR"}, f"Erro ao exportar para emulador: {exc}")
                return {"CANCELLED"}

        summary = " e ".join(messages) if messages else "Nenhuma exportação selecionada"
        self.report({"INFO"}, f"NPC {npc_s.npc_id} ({npc_s.npc_name}): {summary}!")
        return {"FINISHED"}


class AION_OT_suggest_npc_id(bpy.types.Operator):
    """Reads npc_templates.xml and suggests the next free NPC ID."""

    bl_idname = "aion_model.suggest_npc_id"
    bl_label = "Sugerir Próximo ID"
    bl_description = "Lê o emulador e sugere automaticamente o próximo ID de NPC disponível"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        try:
            from ..exporters.emulator_exporter import EmulatorExporter
            next_id = EmulatorExporter.get_max_npc_id() + 1
            context.scene.aion_npc_creator.npc_id = next_id
            self.report({"INFO"}, f"Próximo ID sugerido: {next_id}")
        except Exception as e:
            self.report({"WARNING"}, f"Não foi possível ler o emulador: {e}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class AION_PT_npc_creator(bpy.types.Panel):
    """NPC Creator and Editor panel (N-Panel sidebar)."""

    bl_label = "Criador de NPCs"
    bl_idname = "AION_PT_npc_creator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        npc_s = context.scene.aion_npc_creator

        # ---- Identification ----
        box = layout.box()
        box.label(text="Identificação", icon="COMMUNITY")
        col = box.column(align=True)
        id_row = col.row(align=True)
        id_row.prop(npc_s, "npc_id")
        id_row.operator("aion_model.suggest_npc_id", text="", icon="EYEDROPPER")
        col.prop(npc_s, "npc_name")
        col.prop(npc_s, "npc_name_id")
        col.prop(npc_s, "npc_string_key")

        # Auto-detect from stage button
        col.separator()
        col.operator("aion_model.fill_from_active_stage", icon="SHADING_BBOX")

        # ---- Mesh & Appearance ----
        box_mesh = layout.box()
        box_mesh.label(text="Malha e Aparência", icon="MESH_DATA")
        col_m = box_mesh.column(align=True)
        col_m.prop(npc_s, "npc_dir")
        col_m.prop(npc_s, "npc_mesh")
        col_m.prop(npc_s, "npc_material")
        col_m.prop(npc_s, "npc_foot_mat")
        row_scale = col_m.row(align=True)
        row_scale.prop(npc_s, "npc_scale")
        row_scale.prop(npc_s, "npc_weapon_scale")

        # ---- Combat attributes ----
        box2 = layout.box()
        box2.label(text="Atributos de Combate", icon="ARMATURE_DATA")
        col2 = box2.column(align=True)
        col2.prop(npc_s, "npc_level")
        col2.prop(npc_s, "npc_max_hp")
        col2.prop(npc_s, "npc_height")
        col2.prop(npc_s, "npc_rank")
        col2.prop(npc_s, "npc_rating")

        # ---- Behaviour ----
        box3 = layout.box()
        box3.label(text="Comportamento", icon="LOGIC")
        col3 = box3.column(align=True)
        col3.prop(npc_s, "npc_ai")
        col3.prop(npc_s, "npc_race")
        col3.prop(npc_s, "npc_tribe")
        col3.prop(npc_s, "npc_type")
        col3.prop(npc_s, "npc_srange")
        col3.prop(npc_s, "npc_sangle")

        # ---- Movement & Collision ----
        box4 = layout.box()
        box4.label(text="Movimento e Colisão", icon="MOD_PHYSICS")
        col4 = box4.column(align=True)
        col4.prop(npc_s, "npc_walk_speed")
        col4.prop(npc_s, "npc_run_speed")
        col4.prop(npc_s, "npc_bound_front")
        col4.prop(npc_s, "npc_bound_side")
        col4.prop(npc_s, "npc_bound_upper")

        # ---- Export options & action button ----
        layout.separator()
        box_exp = layout.box()
        box_exp.label(text="Destinos de Exportação", icon="EXPORT")
        col_exp = box_exp.column(align=True)
        col_exp.prop(npc_s, "export_to_client")
        col_exp.prop(npc_s, "export_to_emulator")

        row = layout.row()
        row.scale_y = 1.4
        row.operator("aion_model.create_npc", text="Salvar NPC no Cliente e Emulador", icon="FILE_TICK")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES = (
    AionNPCCreatorSettings,
    AION_OT_fill_from_active_stage,
    AION_OT_create_npc,
    AION_OT_suggest_npc_id,
    AION_PT_npc_creator,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.aion_npc_creator = bpy.props.PointerProperty(
        type=AionNPCCreatorSettings
    )


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "aion_npc_creator"):
        del bpy.types.Scene.aion_npc_creator
