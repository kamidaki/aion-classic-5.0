//! Carregamento de dados do jogo a partir dos XMLs oficiais do cliente Aion.
//!
//! Organização modular — cada arquivo cuida de um domínio:
//! - [`xml_reader`]       — parser XML genérico reutilizável
//! - [`npc_loader`]       — `client_npcs.xml`
//! - [`item_loader`]      — `client_items.xml` (slots, máscaras, tecido)
//! - [`skill_loader`]     — `client_skills.xml` + `client_skill_learns.xml`
//! - [`progression_loader`] — títulos, goodslists, battlepass, attendance, gather
//!
//! O ponto de entrada principal é [`GameData`] que une todos os dados numa única struct.

pub mod xml_reader;
pub mod npc_loader;
pub mod item_loader;
pub mod skill_loader;
pub mod progression_loader;

// Re-exportações públicas para compatibilidade retroativa com `crate::data_loader::*`
pub use npc_loader::{NpcDef, load_npcs};
pub use item_loader::{ItemDef, Slot, SLOTS_DE_CORPO, slot_do_catalogo, mascara_do_item, load_items};
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

/// Um NPC parado no mundo, com a posição que o servidor oficial usou.
#[derive(Debug, Clone)]
pub struct Spawn {
    pub mapa: u32,
    pub npc_id: u32,
    /// Id da string do nome — o pacote leva o número, não o texto.
    pub nome_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    /// O `S_PUT_NPC` que o servidor oficial mandou para este NPC, sem o prelude.
    ///
    /// Guardamos o pacote inteiro porque ele tem tamanho variável — de 107 a 267 bytes na captura
    /// — e o nosso `PutNpc` é implementação da 2.5, de tamanho fixo, que o cliente 4.5 ignora.
    /// Só o id de entidade é trocado no envio; ver [`OFFSET_ID_ENTIDADE`].
    pub payload: Vec<u8>,
}

/// Onde fica o id de entidade dentro do payload de [`Spawn`].
///
/// Tem o bit alto ligado (`0x80......`), que é o que o cliente 4.5 espera de id de entidade.
pub const OFFSET_ID_ENTIDADE: usize = 12;

/// Dados de jogo unificados, carregados dos XMLs oficiais do cliente na inicialização.
#[derive(Debug, Default)]
pub struct GameData {
    pub npcs: HashMap<u32, NpcDef>,
    pub items: HashMap<u32, ItemDef>,
    pub aprendizado: Vec<SkillLearn>,
    pub spawns: Vec<Spawn>,
    pub titles: HashMap<u16, TitleDef>,
    pub goods_lists: HashMap<u32, GoodsListDef>,
    pub battlepass_rewards: Vec<BattlePassRewardDef>,
    pub attendance_rewards: Vec<AttendanceRewardDef>,
    pub gather_sources: HashMap<u32, GatherDef>,
    /// Para cada skill, se ela age sobre um **inimigo**. Vem do `first_target` do XML do cliente.
    pub skill_no_alvo: HashMap<u32, bool>,
    /// O kit que cada grupo de classe recebe ao nascer: `(item_id, quantidade)`.
    ///
    /// A chave é a classe base — `FIGHTER`, `SCOUT`, `MAGE`, `PRIEST`.
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

    /// Carrega todos os dados dos XMLs do cliente a partir de `data_dir`.
    pub fn load(data_dir: &Path) -> Self {
        let mut gd = Self::default();

        // NPCs
        let npcs_path = data_dir.join("npcs").join("client_npcs.xml");
        match load_npcs(&npcs_path) {
            Ok(npcs) => {
                println!("INFO: loaded {} NPCs from {}", npcs.len(), npcs_path.display());
                gd.npcs = npcs;
            }
            Err(e) => eprintln!("WARN: skipping NPCs ({}): {e}", npcs_path.display()),
        }

        // Items
        let items_path = data_dir.join("items").join("client_items.xml");
        match load_items(&items_path) {
            Ok(items) => {
                println!("INFO: loaded {} items from {}", items.len(), items_path.display());
                gd.items = items;
            }
            Err(e) => eprintln!("WARN: skipping items ({}): {e}", items_path.display()),
        }

        // Skills (targeting + learn tree)
        let skills_path = data_dir.join("skills").join("client_skills.xml");
        let arvore_path = data_dir.join("skills").join("client_skill_learns.xml");
        match load_skill_alvo(&skills_path) {
            Ok(m) => {
                println!("INFO: loaded targeting for {} skills", m.len());
                gd.skill_no_alvo = m;
            }
            Err(e) => eprintln!("WARN: skipping skill targeting ({}): {e}", skills_path.display()),
        }
        match load_aprendizado(&skills_path, &arvore_path) {
            Ok(a) => {
                println!("INFO: loaded {} skill learn rules from {}", a.len(), arvore_path.display());
                gd.aprendizado = a;
            }
            Err(e) => eprintln!("WARN: skipping skills ({}): {e}", arvore_path.display()),
        }

        // Titles
        let titles_path = data_dir.join("PC").join("client_titles.xml");
        match load_titles(&titles_path) {
            Ok(t) => {
                println!("INFO: loaded {} titles from {}", t.len(), titles_path.display());
                gd.titles = t;
            }
            Err(e) => eprintln!("WARN: skipping titles ({}): {e}", titles_path.display()),
        }

        // Goods lists
        let goods_path = data_dir.join("npcs").join("client_npc_goodslist.xml");
        match load_goods_lists(&goods_path) {
            Ok(g) => {
                println!("INFO: loaded {} goods lists from {}", g.len(), goods_path.display());
                gd.goods_lists = g;
            }
            Err(e) => eprintln!("WARN: skipping goods lists ({}): {e}", goods_path.display()),
        }

        // Daeva Pass (Battle Pass)
        let battlepass_path = data_dir.join("PC").join("client_battlepass_reward.xml");
        match load_battlepass_rewards(&battlepass_path) {
            Ok(bp) => {
                println!("INFO: loaded {} battlepass rewards from {}", bp.len(), battlepass_path.display());
                gd.battlepass_rewards = bp;
            }
            Err(e) => eprintln!("WARN: skipping battlepass rewards ({}): {e}", battlepass_path.display()),
        }

        // Attendance (Atreian Passport)
        let login_event_path = data_dir.join("PC").join("client_login_event.xml");
        match load_attendance_rewards(&login_event_path) {
            Ok(att) => {
                println!("INFO: loaded {} attendance login events from {}", att.len(), login_event_path.display());
                gd.attendance_rewards = att;
            }
            Err(e) => eprintln!("WARN: skipping attendance events ({}): {e}", login_event_path.display()),
        }

        // Gather sources
        let gather_path = data_dir.join("Gather").join("gather_src.xml");
        match load_gather_sources(&gather_path) {
            Ok(g) => {
                println!("INFO: loaded {} gather sources from {}", g.len(), gather_path.display());
                gd.gather_sources = g;
            }
            Err(e) => eprintln!("WARN: skipping gather sources ({}): {e}", gather_path.display()),
        }

        gd
    }

    /// Lê o kit inicial de `player_initial_data.xml` (ou fallback para `itens_iniciais.csv`).
    ///
    /// O XML oficial é preferido. O CSV é mantido apenas como fallback de retrocompatibilidade.
    pub fn carrega_itens_iniciais(&mut self, caminho: &Path) {
        // Tenta carregar do XML oficial se existir no diretório
        let xml_path = if let Some(parent) = caminho.parent() {
            parent.join("player_initial_data.xml")
        } else {
            PathBuf::from("data/player_initial_data.xml")
        };

        if xml_path.exists() {
            let mut init_holder = crate::dataholders::PlayerInitialDataHolder::new();
            if let Ok(count) = init_holder.load_from_file(&xml_path) {
                println!(
                    "INFO: [player_initial_data.xml] carregadas {count} definicoes de itens iniciais de {}",
                    xml_path.display()
                );
                self.itens_iniciais = init_holder.class_items;
                return;
            }
        }

        // Fallback CSV
        let texto = match std::fs::read_to_string(caminho) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("WARN: sem kit inicial ({}): {e}", caminho.display());
                return;
            }
        };
        for linha in texto.lines() {
            let linha = linha.trim();
            if linha.is_empty() || linha.starts_with('#') { continue; }
            let campos: Vec<&str> = linha.split(',').collect();
            if campos.len() != 3 { continue; }
            if let (Ok(item), Ok(quantidade)) =
                (campos[1].trim().parse::<u32>(), campos[2].trim().parse::<u32>())
            {
                self.itens_iniciais
                    .entry(campos[0].trim().to_ascii_uppercase())
                    .or_default()
                    .push((item, quantidade));
            }
        }
        println!(
            "INFO: kit inicial de {} classes lido de {}",
            self.itens_iniciais.len(),
            caminho.display()
        );
    }

    /// Lê spawns de todos os mapas via `SpawnsDataHolder` (XMLs do cliente).
    pub fn carrega_spawns(&mut self, caminho: &Path) {
        let mut holder = crate::dataholders::SpawnsDataHolder::new();
        if let Ok(total) = holder.load_from_csv(caminho) {
            println!(
                "INFO: [SpawnsDataHolder] Carregados {total} spawns de {} mapas de {}",
                holder.spawns_by_map.len(),
                caminho.display()
            );
            for (_mapa, lista) in holder.spawns_by_map {
                for s in lista {
                    self.spawns.push(Spawn {
                        mapa: s.mapa,
                        npc_id: s.npc_id,
                        nome_id: s.nome_id,
                        x: s.x,
                        y: s.y,
                        z: s.z,
                        payload: s.payload,
                    });
                }
            }
            return;
        }
        eprintln!("WARN: sem tabela de spawns ({}): arquivo não encontrado ou inválido", caminho.display());
    }
}
