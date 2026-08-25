//! Camada Central de Carregamento de Dados e DataHolders (DataManager) - Padrão Java AION
//!
//! Realiza a leitura e indexação direta dos XMLs oficiais do cliente e XMLs de static_data.

pub mod item_data;
pub mod npc_data;
pub mod spawn_data;
pub mod skill_data;
pub mod world_data;
pub mod goods_data;
pub mod title_data;
pub mod gather_data;
pub mod pass_data;
pub mod housing_data;
pub mod flight_data;
pub mod tribe_data;
pub mod player_initial_data;

pub use item_data::{ItemDataHolder, ItemDef, Slot};
pub use npc_data::{NpcDataHolder, NpcDef};
pub use spawn_data::{SpawnsDataHolder, Spawn};
pub use skill_data::{SkillDataHolder, SkillLearn};
pub use world_data::{WorldMapsDataHolder, WorldMapTemplate};
pub use goods_data::{GoodsListDataHolder, GoodsListDef};
pub use title_data::{TitleDataHolder, TitleDef};
pub use gather_data::{GatherableDataHolder, GatherDef};
pub use pass_data::{PassDataHolder, BattlePassRewardDef, AttendanceRewardDef};
pub use housing_data::{HouseDataHolder, HouseTemplate};
pub use flight_data::{FlyPathDataHolder, FlightRoute};
pub use tribe_data::{TribeRelationsDataHolder, TribeRelation};
pub use player_initial_data::{PlayerInitialDataHolder, SpawnLocation};

use std::collections::HashMap;
use std::path::Path;

/// Skills universais concedidas no nascimento (coleta, coleta aérea, éter)
pub const SKILLS_UNIVERSAIS: [u32; 3] = [30002, 30003, 40009];

/// Fachada unificada de todos os DataHolders do jogo (equivalente ao DataManager do Java)
#[derive(Debug, Default)]
pub struct DataManager {
    pub items_data: ItemDataHolder,
    pub npcs_data: NpcDataHolder,
    pub spawns_data: SpawnsDataHolder,
    pub skills_data: SkillDataHolder,
    pub world_data: WorldMapsDataHolder,
    pub goods_data: GoodsListDataHolder,
    pub titles_data: TitleDataHolder,
    pub gather_data: GatherableDataHolder,
    pub pass_data: PassDataHolder,
    pub house_data: HouseDataHolder,
    pub flight_data: FlyPathDataHolder,
    pub player_initial_data: PlayerInitialDataHolder,
    pub initial_items: HashMap<String, Vec<(u32, u32)>>,
}

impl DataManager {
    pub fn new() -> Self {
        Self::default()
    }

    /// As skills que um personagem desta classe e deste nivel ja deveria ter
    pub fn skills_de(&self, classe: &str, base: &str, nivel: u16) -> Vec<u32> {
        let mut ids: Vec<u32> = self
            .skills_data
            .skill_learn_tree
            .iter()
            .filter(|a| a.nivel <= nivel && (a.classe == classe || a.classe == base
                || a.classe.eq_ignore_ascii_case("all")))
            .map(|a| a.skill_id)
            .collect();
        ids.extend_from_slice(&SKILLS_UNIVERSAIS);
        ids.sort_unstable();
        ids.dedup();
        ids
    }

    /// Carregamento unificado a partir da pasta raiz de dados do cliente (`data/client`) e `data/`
    pub fn load_all(client_dir: &Path, root_data_dir: &Path) -> Self {
        let mut dm = Self::new();

        // 1. Items (XML oficial do cliente - 180k+ itens)
        let items_path = client_dir.join("items").join("client_items.xml");
        if let Ok(count) = dm.items_data.load_from_file(&items_path) {
            println!("INFO: [ItemDataHolder] Carregados {count} itens oficiais de {}", items_path.display());
        }

        // 2. NPCs (XML oficial do cliente - 25k+ NPCs)
        let npcs_path = client_dir.join("npcs").join("client_npcs.xml");
        if let Ok(count) = dm.npcs_data.load_from_file(&npcs_path) {
            println!("INFO: [NpcDataHolder] Carregados {count} NPCs oficiais de {}", npcs_path.display());
        }

        // 3. Player Initial Data (XML de Spawns Iniciais de Raça e Equipamentos Iniciais de Classe)
        let player_init_path = root_data_dir.join("player_initial_data.xml");
        if let Ok(count) = dm.player_initial_data.load_from_file(&player_init_path) {
            println!("INFO: [PlayerInitialDataHolder] Carregadas {count} regras de itens/spawns iniciais de {}", player_init_path.display());
            dm.initial_items = dm.player_initial_data.class_items.clone();
        }

        // 4. Spawns (XMLs de todos os mapas em static_data/spawns)
        let spawns_dir = root_data_dir.join("static_data").join("spawns");
        if spawns_dir.exists() {
            if let Ok(count) = dm.spawns_data.load_from_directory(&spawns_dir) {
                println!("INFO: [SpawnsDataHolder] Carregados {count} spawns XML de {} mapas em {}", dm.spawns_data.spawns_by_map.len(), spawns_dir.display());
            }
        } else {
            // Fallback para spawns.csv se existir
            let spawns_csv = root_data_dir.join("spawns.csv");
            if let Ok(count) = dm.spawns_data.load_from_csv(&spawns_csv) {
                println!("INFO: [SpawnsDataHolder] Fallback CSV: Carregados {count} spawns de {} mapas", dm.spawns_data.spawns_by_map.len());
            }
        }

        // 5. Skills & Learn Tree (XMLs oficiais do cliente)
        let skills_path = client_dir.join("skills").join("client_skills.xml");
        let learns_path = client_dir.join("skills").join("client_skill_learns.xml");
        let _ = dm.skills_data.load_skills_catalog(&skills_path);
        let _ = dm.skills_data.load_learn_tree(&learns_path);

        // 6. World Maps & Zones (todos os 135 arquivos do cliente)
        let world_dir = client_dir.join("world");
        if let Ok(count) = dm.world_data.load_from_directory(&world_dir) {
            println!("INFO: [WorldMapsDataHolder] Catalogados {count} mapas e instâncias");
        }

        // 7. Goods Lists (Lojas de NPCs)
        let goods_path = client_dir.join("goods").join("client_npc_goodslist.xml");
        let _ = dm.goods_data.load_from_file(&goods_path);

        // 8. Titles (Títulos do cliente)
        let titles_path = client_dir.join("PC").join("client_titles.xml");
        let _ = dm.titles_data.load_from_file(&titles_path);

        // 9. Gatherable sources (Fontes de coleta do cliente)
        let gather_path = client_dir.join("Gather").join("client_gather_src.xml");
        let _ = dm.gather_data.load_from_file(&gather_path);

        // 10. BattlePass & Login Event
        let bp_path = client_dir.join("PC").join("client_battlepass_reward.xml");
        let login_path = client_dir.join("PC").join("client_login_event.xml");
        let _ = dm.pass_data.load_battlepass_rewards(&bp_path);
        let _ = dm.pass_data.load_attendance_rewards(&login_path);

        dm
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_player_initial_data_parsing() {
        let xml = r#"<?xml version="1.0" encoding="UTF-8"?>
<player_initial_data>
    <asmodian_spawn_location map_id="220010000" heading="32" x="571.0388" y="2787.3420" z="299.8750"/>
    <elyos_spawn_location map_id="210010000" heading="32" x="1212.9423" y="1044.8516" z="140.75568"/>
    <player_data class="WARRIOR">
        <items>
            <item id="182400001" count="1000"/>
            <item id="100000094" count="1"/>
            <item id="110500003" count="1"/>
        </items>
    </player_data>
</player_initial_data>"#;

        let mut holder = PlayerInitialDataHolder::new();
        let temp_dir = std::env::temp_dir();
        let temp_file = temp_dir.join("test_player_init.xml");
        std::fs::write(&temp_file, xml).unwrap();

        let count = holder.load_from_file(&temp_file).unwrap();
        assert_eq!(count, 3);
        assert_eq!(holder.elyos_spawn.map_id, 210010000);
        assert_eq!(holder.asmodian_spawn.map_id, 220010000);

        let items = holder.get_initial_items("WARRIOR");
        assert_eq!(items.len(), 3);
        assert_eq!(items[0], (182400001, 1000));
        assert_eq!(items[1], (100000094, 1));
    }

    #[test]
    fn test_spawn_data_xml_parsing() {
        let xml = r#"<?xml version="1.0" encoding="utf-8"?>
<spawns>
    <spawn_map map_id="210010000">
        <spawn npc_id="210119" respawn_time="28">
            <spot x="429.73" y="1796.03" z="125.125" h="25"/>
            <spot x="439.533" y="1776.26" z="122.381" h="40"/>
        </spawn>
        <spawn npc_id="203083" respawn_time="295">
            <spot x="425.428" y="1739.61" z="119.926" h="15"/>
        </spawn>
    </spawn_map>
</spawns>"#;

        let mut holder = SpawnsDataHolder::new();
        let temp_dir = std::env::temp_dir();
        let temp_file = temp_dir.join("test_spawns.xml");
        std::fs::write(&temp_file, xml).unwrap();

        let count = holder.load_from_xml(&temp_file).unwrap();
        assert_eq!(count, 3);
        let spawns = holder.get_spawns_for_map(210010000);
        assert!(spawns.is_some());
        assert_eq!(spawns.unwrap().len(), 3);
        assert_eq!(spawns.unwrap()[0].npc_id, 210119);
        assert_eq!(spawns.unwrap()[2].npc_id, 203083);
    }

    #[test]
    fn test_tribe_relations_hostility() {
        assert_eq!(
            TribeRelationsDataHolder::get_relation("PC_LIGHT", "PC_DARK"),
            TribeRelation::Hostile
        );
        assert_eq!(
            TribeRelationsDataHolder::get_relation("PC_LIGHT", "GUARD_LIGHT"),
            TribeRelation::Friendly
        );
        assert_eq!(
            TribeRelationsDataHolder::get_relation("PC_LIGHT", "MONSTER_AGGRESSIVE"),
            TribeRelation::Hostile
        );
    }
}
