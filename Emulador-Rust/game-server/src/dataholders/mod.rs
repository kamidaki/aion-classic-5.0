//! Camada Central de Carregamento de Dados e DataHolders (DataManager) - Padrão Java AION
//!
//! Realiza a leitura e indexação direta dos XMLs oficiais do cliente (sem conversões intermediárias).

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

    /// Carregamento unificado a partir da pasta raiz de dados do cliente (`data/client`)
    pub fn load_all(client_dir: &Path, root_data_dir: &Path) -> Self {
        let mut dm = Self::new();

        // 1. Items
        let items_path = client_dir.join("items").join("client_items.xml");
        if let Ok(count) = dm.items_data.load_from_file(&items_path) {
            println!("INFO: [ItemDataHolder] Carregados {count} itens oficiais de {}", items_path.display());
        }

        // 2. NPCs
        let npcs_path = client_dir.join("npcs").join("client_npcs.xml");
        if let Ok(count) = dm.npcs_data.load_from_file(&npcs_path) {
            println!("INFO: [NpcDataHolder] Carregados {count} NPCs oficiais de {}", npcs_path.display());
        }

        // 3. Spawns (de todos os mapas)
        let spawns_path = root_data_dir.join("spawns.csv");
        if let Ok(count) = dm.spawns_data.load_from_csv(&spawns_path) {
            println!("INFO: [SpawnsDataHolder] Carregados {count} spawns de {} mapas", dm.spawns_data.spawns_by_map.len());
        }

        // 4. Skills & Learn Tree
        let skills_path = client_dir.join("skills").join("client_skills.xml");
        let learns_path = client_dir.join("skills").join("client_skill_learns.xml");
        let _ = dm.skills_data.load_skills_catalog(&skills_path);
        let _ = dm.skills_data.load_learn_tree(&learns_path);

        // 5. World Maps & Zones (todos os 135 arquivos)
        let world_dir = client_dir.join("world");
        if let Ok(count) = dm.world_data.load_from_directory(&world_dir) {
            println!("INFO: [WorldMapsDataHolder] Catalogados {count} mapas e instâncias");
        }

        // 6. Goods Lists (Lojas)
        let goods_path = client_dir.join("goods").join("client_npc_goodslist.xml");
        let _ = dm.goods_data.load_from_file(&goods_path);

        // 7. Titles
        let titles_path = client_dir.join("PC").join("client_titles.xml");
        let _ = dm.titles_data.load_from_file(&titles_path);

        // 8. Gatherable sources
        let gather_path = client_dir.join("Gather").join("client_gather_src.xml");
        let _ = dm.gather_data.load_from_file(&gather_path);

        // 9. BattlePass & Login Event
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

    #[test]
    fn test_world_maps_data_holder_resolution() {
        let mut wdh = WorldMapsDataHolder::new();
        wdh.world_maps.insert(
            210010000,
            WorldMapTemplate {
                map_id: 210010000,
                name: "lf1".to_string(),
                file_name: "client_world_lf1.xml".to_string(),
                is_instance: false,
                max_players: 5000,
            },
        );

        let map = wdh.get_map(210010000);
        assert!(map.is_some());
        assert_eq!(map.unwrap().name, "lf1");
        assert!(!map.unwrap().is_instance);
    }
}
