"""
User Interface Panels for LostAcademy Aion Model Library.
Provides an integrated 3D Viewport Sidebar (N-Panel) for asset browsing, staging,
editing, animation playback, and safe transactional saving.
"""

from __future__ import annotations
import bpy

PANEL_CATEGORY = "Modelos Aion"


class AION_UL_asset_list(bpy.types.UIList):
    """Custom UIList rendering of scanned Aion model library assets."""

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        icon: int,
        active_data: bpy.types.AnyType,
        active_propname: str,
        index: int = 0,
        flt_flag: int = 0,
    ) -> None:
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)

            # Modified status icon
            if item.is_modified:
                row.label(text="", icon="MODIFIER")

            # Icon based on category
            cat_icons = {
                "NPC": "COMMUNITY",
                "MONSTER": "GHOST_ENABLED",
                "CHARACTER": "USER",
                "WEAPON": "OUTLINER_OB_FORCE_FIELD",
                "ARMOR": "MOD_CLOTH",
                "WINGS": "PARTICLES",
                "PET_MOUNT": "OUTLINER_OB_ARMATURE",
                "BUILDING": "HOME",
                "PROP": "OBJECT_DATA",
                "VEGETATION": "OUTLINER_DATA_POINTCLOUD",
                "OBJECT": "MESH_CUBE",
                "EFFECT": "LIGHT_SUN",
            }
            ic = cat_icons.get(item.category, "MESH_DATA")

            row.label(text=item.name, icon=ic)

            # Details columns
            sub = row.row(align=True)
            sub.alignment = "RIGHT"
            if item.bone_count > 0:
                sub.label(text=f"{item.bone_count}b", icon="BONE_DATA")
            if item.anim_count > 0:
                sub.label(text=f"{item.anim_count}a", icon="ACTION")
            sub.label(text=f"{item.poly_count}p")

        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text=item.name, icon="MESH_DATA")


class AION_PT_client_header(bpy.types.Panel):
    """Client configuration and safety switch panel."""
    bl_label = "Configuração do Cliente Aion"
    bl_idname = "AION_PT_client_header"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Client Directory
        col = layout.column(align=True)
        col.prop(settings, "client_path")
        row = col.row(align=True)
        row.operator("aion_model.detect_client", icon="VIEWZOOM")
        row.label(text=f"Tipo: {settings.client_flavor}")

        # Scan / Cache Buttons
        box = layout.box()
        row = box.row(align=True)
        scan_label = "Escanear Arquivos do Cliente" if settings.scanned_total_count == 0 else f"Carregar Cache ({settings.scanned_total_count:,})"
        op = row.operator("aion_model.scan_assets", text=scan_label, icon="FILE_REFRESH")
        op.force_rescan = False
        if settings.scanned_total_count > 0:
            rescan_op = row.operator("aion_model.scan_assets", text="Forçar Reescaneamento", icon="FILE_CACHE")
            rescan_op.force_rescan = True

        # Safety Write Toggle
        safety_box = layout.box()
        safety_box.prop(settings, "allow_client_write", icon="ERROR" if settings.allow_client_write else "LOCKED")
        if settings.allow_client_write:
            w_box = safety_box.box()
            w_box.alert = True
            w_box.label(text="CUIDADO: Gravação Direta no Cliente ATIVADA!", icon="CANCEL")
            w_box.label(text="Edições irão modificar os arquivos/PAKs oficiais do jogo.")
            safety_box.prop(settings, "auto_backup")
        else:
            safety_box.label(text="Modo Seguro: Gravação direta desativada", icon="CHECKMARK")
            safety_box.prop(settings, "export_fallback_dir")


class AION_PT_asset_browser(bpy.types.Panel):
    """Asset library browser with search and filtering."""
    bl_label = "Biblioteca de Modelos"
    bl_idname = "AION_PT_asset_browser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Search & Filter
        col = layout.column(align=True)
        col.prop(settings, "category_filter", text="")
        col.prop(settings, "search_query", text="", icon="VIEWZOOM")

        # UI List
        row = layout.row()
        row.template_list(
            "AION_UL_asset_list",
            "aion_asset_list",
            settings,
            "asset_items",
            settings,
            "active_asset_index",
            rows=6,
        )

        # Action buttons
        btn_row = layout.row(align=True)
        btn_row.scale_y = 1.3
        btn_row.operator("aion_model.load_asset", text="Carregar no Visualizador", icon="RESTRICT_VIEW_OFF")
        btn_row.operator("aion_model.equip_asset", text="Equipar no Personagem", icon="USER")
        btn_row.operator("aion_model.clear_stage", text="Limpar Palco", icon="TRASH")


class AION_PT_character_preview(bpy.types.Panel):
    """Character Dressing Room & Class Preset Viewer."""
    bl_label = "Provador de Classes e Personagens"
    bl_idname = "AION_PT_character_preview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Mode Selection Box
        m_box = layout.box()
        m_box.label(text="Modo de Visualização", icon="RESTRICT_VIEW_OFF")
        m_box.prop(settings, "preview_mode", expand=True)
        m_box.prop(settings, "auto_complete_humanoid")

        # Class & Character Selection
        box = layout.box()
        box.label(text="Provador de Personagem", icon="COMMUNITY")
        col = box.column(align=True)
        col.prop(settings, "character_race")
        col.prop(settings, "character_class")

        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("aion_model.load_class_preset", text="Carregar Traje da Classe", icon="CHECKMARK")


class AION_PT_asset_details(bpy.types.Panel):
    """Metadata details of the loaded asset."""
    bl_label = "Detalhes do Modelo"
    bl_idname = "AION_PT_asset_details"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        if not settings.active_asset_id:
            layout.label(text="Nenhum modelo carregado no visualizador", icon="INFO")
            return

        box = layout.box()
        box.label(text=f"Modelo: {settings.active_asset_name}", icon="OBJECT_DATA")
        box.label(text=f"Categoria: {settings.active_category}")
        box.label(text=f"Polígonos: {settings.active_poly_count:,} | Vértices: {settings.active_vertex_count:,}")
        box.label(text=f"Ossos: {settings.active_bone_count}")

        p_box = box.box()
        p_box.scale_y = 0.8
        p_box.label(text=f"Caminho: {settings.active_model_path}")
        if settings.active_skeleton_path:
            p_box.label(text=f"Esqueleto: {settings.active_skeleton_path}")

        if settings.active_is_modified:
            m_box = layout.box()
            m_box.alert = True
            m_box.label(text="O modelo possui modificações não salvas!", icon="MODIFIER")


class AION_PT_viewport_controls(bpy.types.Panel):
    """Viewport staging, camera presets, and shading controls."""
    bl_label = "Câmera e Visualização"
    bl_idname = "AION_PT_viewport_controls"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Camera presets
        row = layout.row(align=True)
        row.operator("aion_model.set_camera_view", text="Frente").axis = "FRONT"
        row.operator("aion_model.set_camera_view", text="Lado").axis = "RIGHT"
        row.operator("aion_model.set_camera_view", text="Topo").axis = "TOP"

        row2 = layout.row(align=True)
        row2.operator("aion_model.focus_model", text="Focar", icon="VIEW_CAMERA")
        row2.operator("aion_model.set_camera_view", text="Persp/Orto").axis = "PERSP_ORTHO"
        row2.operator("aion_model.set_camera_view", text="Redefinir").axis = "RESET"

        # Shading buttons
        s_row = layout.row(align=True)
        s_row.operator("aion_model.set_shading", text="Aramado").mode = "WIREFRAME"
        s_row.operator("aion_model.set_shading", text="Sólido").mode = "SOLID"
        s_row.operator("aion_model.set_shading", text="Material").mode = "MATERIAL"
        s_row.operator("aion_model.set_shading", text="Renderizado").mode = "RENDERED"

        # Armature toggle
        layout.operator(
            "aion_model.toggle_bones",
            text="Ocultar Ossos" if settings.show_armature else "Exibir Ossos",
            icon="BONE_DATA",
        )


class AION_PT_animation_player(bpy.types.Panel):
    """Animation list and timeline transport controls."""
    bl_label = "Animações"
    bl_idname = "AION_PT_animation_player"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        if not settings.active_anims:
            layout.label(text="Nenhuma animação disponível", icon="INFO")
            return

        layout.template_list(
            "UI_UL_list",
            "aion_anim_list",
            settings,
            "active_anims",
            settings,
            "active_anim_index",
            rows=3,
        )

        row = layout.row(align=True)
        row.operator("aion_model.switch_animation", text="Aplicar Animação", icon="PLAY")

        t_row = layout.row(align=True)
        t_row.scale_y = 1.2
        t_row.operator("aion_model.play_animation", text="Reproduzir / Pausar", icon="PLAY")
        t_row.operator("aion_model.stop_animation", text="Parar", icon="REW")


class AION_PT_editors(bpy.types.Panel):
    """Mesh, skeleton, UV, and normal editing operations."""
    bl_label = "Editar Modelo"
    bl_idname = "AION_PT_editors"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        col = layout.column(align=True)
        row1 = col.row(align=True)
        row1.operator("aion_model.edit_mesh", text="Editar Malha", icon="EDITMODE_HLT")
        row1.operator("aion_model.sculpt_mesh", text="Esculpir", icon="SCULPTMODE_HLT")

        row2 = col.row(align=True)
        row2.operator("aion_model.edit_bones", text="Editar Esqueleto", icon="ARMATURE_DATA")
        row2.operator("aion_model.add_bone", text="Adicionar Osso", icon="PLUS")

        col.operator("aion_model.recalc_normals", text="Recalcular Normais", icon="NORMALS_FACE")

        uv_row = col.row(align=True)
        uv_row.operator("aion_model.unwrap_uv", text="Desembrulhar UV", icon="UV")
        uv_row.operator("aion_model.pack_uv", text="Organizar UVs", icon="ALIGN_CENTER")


class AION_PT_save_export(bpy.types.Panel):
    """Transactional saving back to client or safe loose export."""
    bl_label = "Salvar e Exportar"
    bl_idname = "AION_PT_save_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.aion_model_lib

        # Save Button
        save_col = layout.column(align=True)
        save_col.scale_y = 1.4
        btn_text = "SALVAR DIRETAMENTE NO CLIENTE" if settings.allow_client_write else "SALVAR NA PASTA DE EXPORTAÇÃO"
        btn_icon = "CHECKMARK" if not settings.allow_client_write else "ERROR"
        save_col.operator("aion_model.save_asset", text=btn_text, icon=btn_icon)

        sub_row = layout.row(align=True)
        sub_row.operator("aion_model.export_loose", text="Exportar Avulso", icon="EXPORT")
        sub_row.operator("aion_model.rollback_asset", text="Restaurar Backup (.bak)", icon="LOOP_BACK")


class AION_PT_creation(bpy.types.Panel):
    """Create new Aion assets from scratch or clone existing assets."""
    bl_label = "Criar / Clonar"
    bl_idname = "AION_PT_creation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PANEL_CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("aion_model.create_from_mesh", text="Criar Modelo da Malha", icon="MESH_DATA")
        layout.operator("aion_model.clone_asset", text="Clonar Modelo Ativo", icon="DUPLICATE")


CLASSES = (
    AION_UL_asset_list,
    AION_PT_client_header,
    AION_PT_asset_browser,
    AION_PT_character_preview,
    AION_PT_asset_details,
    AION_PT_viewport_controls,
    AION_PT_animation_player,
    AION_PT_editors,
    AION_PT_save_export,
    AION_PT_creation,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
