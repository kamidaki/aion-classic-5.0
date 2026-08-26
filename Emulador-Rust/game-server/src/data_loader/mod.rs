//! Carregamento de dados do jogo a partir dos XMLs oficiais do cliente Aion.
//!
//! Organização modular — cada arquivo cuida de um domínio:
//! - [`xml_reader`]        — parser XML genérico reutilizável
//! - [`npc_loader`]        — `client_npcs.xml`
//! - [`item_loader`]       — `client_items.xml` (templates completos, slots, máscaras, tecido)
//! - [`string_loader`]     — `client_strings_item*.xml` (tabela de nomes de itens UTF-16LE/UTF-8)
//! - [`auxiliary_loader`]  — `client_setitem.xml`, `client_dye_color.xml`, `client_item_compose.xml`, `client_item_upgrade.xml`
//! - [`cache_watcher`]     — monitoramento e hot-reload automático de XMLs e .properties
//! - [`skill_loader`]      — `client_skills.xml` + `client_skill_learns.xml`
//! - [`progression_loader`] — títulos, goodslists, battlepass, attendance, gather
//!
//! O ponto de entrada principal é [`GameData`] que une todos os dados numa única struct.

pub mod xml_reader;
pub mod npc_loader;
pub mod item_loader;
pub mod string_loader;
pub mod auxiliary_loader;
pub mod cache_watcher;
pub mod skill_loader;
pub mod progression_loader;

// Re-exportações públicas para compatibilidade retroativa com `crate::data_loader::*`
pub use npc_loader::{NpcDef, load_npcs};
pub use item_loader::{ItemDef, Slot, SLOTS_DE_CORPO, slot_do_catalogo, mascara_do_item, load_items, load_items_full};
pub use string_loader::{StringTable, load_item_strings};
pub use auxiliary_loader::{load_set_items, load_dye_colors, load_item_upgrades, load_item_composes, AuxiliaryItemData};
pub use cache_watcher::CacheWatcher;
pub use skill_loader::{SkillLearn, SKILLS_UNIVERSAIS, load_skill_alvo, load_aprendizado};
pub use progression_loader::{
    TitleDef, load_titles,
    GoodsListDef, load_goods_lists,
    BattlePassRewardDef, load_battlepass_rewards,
    AttendanceRewardDef, load_attendance_rewards,
    GatherDef, load_gather_sources,
};

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use crate::data::item::{DyeColorTemplate, ItemComposeTemplate, ItemTemplate, ItemUpgradeTemplate, SetItemTemplate};

/// Um NPC parado no mundo, com a posição que o servidor oficial usou.
#[derive(Debug, Clone)]
pub struct Spawn {
    pub mapa: u32,
    pub npc_id: u32,
    pub nome_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub payload: Vec<u8>,
}

pub const OFFSET_ID_ENTIDADE: usize = 12;

/// Dados de jogo unificados, carregados dos XMLs oficiais do cliente na inicialização.
#[derive(Default)]
pub struct GameData {
    pub npcs: HashMap<u32, NpcDef>,
    pub items: HashMap<u32, ItemDef>,
    pub item_templates: HashMap<u32, ItemTemplate>,
    pub set_items: HashMap<u32, SetItemTemplate>,
    pub dye_colors: HashMap<u32, DyeColorTemplate>,
    pub item_upgrades: HashMap<u32, ItemUpgradeTemplate>,
    pub item_composes: HashMap<u32, ItemComposeTemplate>,
    pub aprendizado: Vec<SkillLearn>,
    pub spawns: Vec<Spawn>,
    pub titles: HashMap<u16, TitleDef>,
    pub goods_lists: HashMap<u32, GoodsListDef>,
    pub battlepass_rewards: Vec<BattlePassRewardDef>,
    pub attendance_rewards: Vec<AttendanceRewardDef>,
    pub gather_sources: HashMap<u32, GatherDef>,
    pub skill_no_alvo: HashMap<u32, bool>,
    pub itens_iniciais: HashMap<String, Vec<(u32, u32)>>,
}

impl GameData {
    /// As skills que um personagem desta classe e deste nível já deveria ter.
    pub fn skills_de(&self, classe: &str, base: &str, nivel: u16) -> Vec<u32> {
        let mut ids: Vec<u32> = self
            .aprendizado
            .iter()
            .filter(|a| {
                a.nivel <= nivel
                    && (a.classe == classe
                        || a.classe == base
                        || a.classe.eq_ignore_ascii_case("all"))
            })
            .map(|a| a.skill_id)
            .collect();
        ids.extend_from_slice(&SKILLS_UNIVERSAIS);
        ids.sort_unstable();
        ids.dedup();
        ids
    }

    /// Carrega todos os dados dos XMLs do cliente a partir dos caminhos configurados.
    pub fn load_configured(data_dir: &Path, items_dir: &Path, strings_dir: &Path) -> Self {
        let mut gd = Self::default();

        // 1. Carrega strings de itens (UTF-16LE / UTF-8)
        let strings_table = load_item_strings(strings_dir);

        // 2. Carrega templates de itens completos com nomes associados
        let items_candidates = [
            items_dir.join("client_items.xml"),
            data_dir.join("data").join("items").join("client_items.xml"),
            data_dir.join("items").join("client_items.xml"),
        ];

        for path in &items_candidates {
            if path.exists() {
                let (templates, defs) = load_items_full(path, &strings_table);
                gd.item_templates = templates;
                gd.items = defs;
                break;
            }
        }

        // 3. Carrega tabelas auxiliares de itens
        let set_path = items_dir.join("client_setitem.xml");
        gd.set_items = load_set_items(&set_path);

        let dye_path = items_dir.join("client_dye_color.xml");
        gd.dye_colors = load_dye_colors(&dye_path);

        let up_path = items_dir.join("client_item_upgrade.xml");
        gd.item_upgrades = load_item_upgrades(&up_path);

        let comp_path = items_dir.join("client_item_compose.xml");
        gd.item_composes = load_item_composes(&comp_path);

        // 4. NPCs
        let npcs_candidates = [
            data_dir.join("data").join("npcs").join("client_npcs.xml"),
            data_dir.join("npcs").join("client_npcs.xml"),
        ];
        for npcs_path in &npcs_candidates {
            if npcs_path.exists() {
                if let Ok(npcs) = load_npcs(npcs_path) {
                    println!("INFO: loaded {} NPCs from {}", npcs.len(), npcs_path.display());
                    gd.npcs = npcs;
                    break;
                }
            }
        }

        // 5. Skills
        let skills_candidates = [
            (data_dir.join("data").join("skills").join("client_skills.xml"), data_dir.join("data").join("skills").join("client_skill_learns.xml")),
            (data_dir.join("skills").join("client_skills.xml"), data_dir.join("skills").join("client_skill_learns.xml")),
        ];
        for (skills_path, arvore_path) in &skills_candidates {
            if skills_path.exists() {
                if let Ok(m) = load_skill_alvo(skills_path) {
                    gd.skill_no_alvo = m;
                }
                if arvore_path.exists() {
                    if let Ok(a) = load_aprendizado(skills_path, arvore_path) {
                        gd.aprendizado = a;
                        break;
                    }
                }
            }
        }

        // 6. Titles
        let titles_candidates = [
            data_dir.join("data").join("PC").join("client_titles.xml"),
            data_dir.join("PC").join("client_titles.xml"),
        ];
        for titles_path in &titles_candidates {
            if titles_path.exists() {
                if let Ok(t) = load_titles(titles_path) {
                    gd.titles = t;
                    break;
                }
            }
        }

        // 7. Goods lists
        let goods_candidates = [
            data_dir.join("data").join("npcs").join("client_npc_goodslist.xml"),
            data_dir.join("npcs").join("client_npc_goodslist.xml"),
        ];
        for goods_path in &goods_candidates {
            if goods_path.exists() {
                if let Ok(g) = load_goods_lists(goods_path) {
                    gd.goods_lists = g;
                    break;
                }
            }
        }

        // 8. Daeva Pass
        let bp_candidates = [
            data_dir.join("data").join("PC").join("client_battlepass_reward.xml"),
            data_dir.join("PC").join("client_battlepass_reward.xml"),
        ];
        for bp_path in &bp_candidates {
            if bp_path.exists() {
                if let Ok(bp) = load_battlepass_rewards(bp_path) {
                    gd.battlepass_rewards = bp;
                    break;
                }
            }
        }

        // 9. Attendance
        let att_candidates = [
            data_dir.join("data").join("PC").join("client_login_event.xml"),
            data_dir.join("PC").join("client_login_event.xml"),
        ];
        for att_path in &att_candidates {
            if att_path.exists() {
                if let Ok(att) = load_attendance_rewards(att_path) {
                    gd.attendance_rewards = att;
                    break;
                }
            }
        }

        // 10. Gather
        let gather_candidates = [
            data_dir.join("data").join("Gather").join("gather_src.xml"),
            data_dir.join("Gather").join("gather_src.xml"),
        ];
        for gather_path in &gather_candidates {
            if gather_path.exists() {
                if let Ok(g) = load_gather_sources(gather_path) {
                    gd.gather_sources = g;
                    break;
                }
            }
        }

        gd
    }

    /// Carrega todos os dados dos XMLs do cliente a partir de `data_dir`.
    pub fn load(data_dir: &Path) -> Self {
        let items_dir = data_dir.join("data").join("items");
        let strings_dir = data_dir.join("Strings").join("strings");
        Self::load_configured(data_dir, &items_dir, &strings_dir)
    }

    /// Lê o kit inicial de `player_initial_data.xml`.
    pub fn carrega_itens_iniciais(&mut self, caminho: &Path) {
        let xml_path = if let Some(parent) = caminho.parent() {
            parent.join("player_initial_data.xml")
        } else {
            PathBuf::from("data/player_initial_data.xml")
        };

        if xml_path.exists() {
            if let Ok(m) = crate::data_loader::xml_reader::carrega_itens_iniciais_xml(&xml_path) {
                if !m.is_empty() {
                    self.itens_iniciais = m;
                    return;
                }
            }
        }

        if caminho.exists() {
            if let Ok(m) = crate::data_loader::xml_reader::carrega_itens_iniciais_xml(caminho) {
                if !m.is_empty() {
                    self.itens_iniciais = m;
                    return;
                }
            }
        }
    }

    /// Lê os spawns de monstros e NPCs de `spawns.xml`.
    pub fn carrega_spawns(&mut self, caminho: &Path) {
        let xml_path = if let Some(parent) = caminho.parent() {
            parent.join("spawns.xml")
        } else {
            PathBuf::from("data/client/spawns.xml")
        };

        if xml_path.exists() {
            if let Ok(s) = crate::data_loader::xml_reader::carrega_spawns_xml(&xml_path) {
                if !s.is_empty() {
                    self.spawns = s;
                    return;
                }
            }
        }

        if caminho.exists() {
            if let Ok(s) = crate::data_loader::xml_reader::carrega_spawns_xml(caminho) {
                if !s.is_empty() {
                    self.spawns = s;
                }
            }
        }
    }
}
