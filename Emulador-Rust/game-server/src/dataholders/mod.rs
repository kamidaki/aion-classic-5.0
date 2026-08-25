//! Camada Central de Carregamento de Dados e DataHolders (DataManager) - Padrão Java AION
//!
//! Realiza a leitura e indexação direta dos XMLs oficiais do cliente (sem emuladores intermediários).

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
pub use world_data::{WorldMapsDataHolder, WorldMapTemplate, SubzoneDef, MapPoint};
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

        // 4. Spawns (de todos os mapas via spawns.csv)
        let spawns_csv = root_data_dir.join("spawns.csv");
        if let Ok(count) = dm.spawns_data.load_from_csv(&spawns_csv) {
            println!("INFO: [SpawnsDataHolder] Carregados {count} spawns de {} mapas em {}", dm.spawns_data.spawns_by_map.len(), spawns_csv.display());
        }

        // 5. Skills & Learn Tree (XMLs oficiais do cliente)
        let skills_path = client_dir.join("skills").join("client_skills.xml");
        let learns_path = client_dir.join("skills").join("client_skill_learns.xml");
        let _ = dm.skills_data.load_skills_catalog(&skills_path);
        let _ = dm.skills_data.load_learn_tree(&learns_path);

        // 6. World Maps & Zones (direto de zonemap.xml e todos os 135 arquivos client_world_*.xml)
        let world_dir = client_dir.join("world");
        if let Ok(count) = dm.world_data.load_from_directory(&world_dir) {
            println!("INFO: [WorldMapsDataHolder] Catalogados {count} mapas e instâncias do client em {}", world_dir.display());
        }

        // 7. Goods Lists (Lojas de NPCs do cliente)
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
    <asmodian_spawn_location map_id="220010000" x="582.3742" y="2790.7642" z="299.3282" heading="66"/>
    <elyos_spawn_location map_id="210010000" x="1207.7640" y="1044.5725" z="140.14894" heading="59"/>
    <player_data class="ASSASSIN">
        <items>
            <item id="182400001" count="0"/>
            <item id="100201355" count="1"/>
            <item id="110301463" count="1"/>
        </items>
    </player_data>
</player_initial_data>"#;

        let mut holder = PlayerInitialDataHolder::new();
        let temp_dir = std::env::temp_dir();
        let temp_file = temp_dir.join("test_player_init_classic.xml");
        std::fs::write(&temp_file, xml).unwrap();

        let count = holder.load_from_file(&temp_file).unwrap();
        assert_eq!(count, 3);
        assert_eq!(holder.elyos_spawn.unwrap().map_id, 210010000);
        assert_eq!(holder.elyos_spawn.unwrap().heading, 59);
        assert_eq!(holder.asmodian_spawn.unwrap().map_id, 220010000);
        assert_eq!(holder.asmodian_spawn.unwrap().heading, 66);

        let items = holder.get_initial_items("ASSASSIN");
        assert_eq!(items.len(), 3);
        assert_eq!(items[0], (182400001, 0));
        assert_eq!(items[1], (100201355, 1));
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
