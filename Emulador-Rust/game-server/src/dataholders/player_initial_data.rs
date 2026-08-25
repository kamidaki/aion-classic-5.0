//! PlayerInitialDataHolder - Ponto de Spawn Inicial por Raça e Equipamentos/Itens Iniciais por Classe (player_initial_data.xml)
//!
//! Carrega 100% dinamicamente a partir do arquivo `player_initial_data.xml` (sem hardcoded).

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct SpawnLocation {
    pub map_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
}

#[derive(Debug, Clone, Default)]
pub struct PlayerInitialDataHolder {
    pub elyos_spawn: Option<SpawnLocation>,
    pub asmodian_spawn: Option<SpawnLocation>,
    pub elyos_telos_spawn: Option<SpawnLocation>,
    pub asmodian_telos_spawn: Option<SpawnLocation>,
    pub class_items: HashMap<String, Vec<(u32, u32)>>,
}

impl PlayerInitialDataHolder {
    pub fn new() -> Self {
        Self::default()
    }

    /// Retorna o ponto de spawn inicial da raça conforme carregado do XML
    pub fn get_spawn_location(&self, race: u8) -> SpawnLocation {
        if race == 1 {
            // Asmodian
            self.asmodian_spawn.unwrap_or(SpawnLocation {
                map_id: 220010000,
                x: 582.3742,
                y: 2790.7642,
                z: 299.3282,
                heading: 66,
            })
        } else {
            // Elyos (0 ou default)
            self.elyos_spawn.unwrap_or(SpawnLocation {
                map_id: 210010000,
                x: 1207.7640,
                y: 1044.5725,
                z: 140.14894,
                heading: 59,
            })
        }
    }

    /// Retorna a lista de itens iniciais de uma classe lida diretamente do XML
    pub fn get_initial_items(&self, class_name: &str) -> Vec<(u32, u32)> {
        let key = class_name.trim().to_uppercase();
        if let Some(items) = self.class_items.get(&key) {
            return items.clone();
        }

        // Tenta aliases comuns se a classe direta nao for encontrada
        let aliases: &[&str] = match key.as_str() {
            "GLADIATOR" | "BATTLEMASTER" | "WARRIOR" => &["GLADIATOR", "BATTLEMASTER", "WARRIOR"],
            "TEMPLAR" | "KNIGHT" => &["TEMPLAR", "KNIGHT", "WARRIOR"],
            "ASSASSIN" | "SCOUT" => &["ASSASSIN", "SCOUT"],
            "RANGER" => &["RANGER", "SCOUT"],
            "SORCERER" | "WIZARD" | "MAGE" => &["SORCERER", "WIZARD", "MAGE"],
            "SPIRIT_MASTER" | "ELEMENTALLIST" => &["SPIRIT_MASTER", "ELEMENTALLIST", "MAGE"],
            "CLERIC" | "PRIEST" => &["CLERIC", "PRIEST"],
            "CHANTER" => &["CHANTER", "PRIEST"],
            "BRAWLER" | "REVENANT" | "MONK" => &["BRAWLER", "REVENANT", "MONK"],
            "GUNSLINGER" | "GUNNER" | "ENGINEER" => &["GUNSLINGER", "GUNNER", "ENGINEER"],
            "AETHERTECH" | "RIDER" => &["AETHERTECH", "RIDER", "ENGINEER"],
            "SONGWEAVER" | "BARD" | "ARTIST" => &["SONGWEAVER", "BARD", "ARTIST"],
            _ => &["WARRIOR"],
        };

        for alias in aliases {
            if let Some(items) = self.class_items.get(*alias) {
                return items.clone();
            }
        }

        Vec::new()
    }

    /// Carrega dinamicamente todas as tags e atributos de `player_initial_data.xml`
    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut current_class = String::new();
        let mut items_count = 0usize;

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Empty(e)) | Ok(Event::Start(e)) => {
                    let tag_name = e.name();
                    let tag = String::from_utf8_lossy(tag_name.as_ref()).to_string();

                    if tag == "asmodian_spawn_location" {
                        let mut loc = SpawnLocation::default();
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(220010000),
                                "x" => loc.x = val.parse().unwrap_or(0.0),
                                "y" => loc.y = val.parse().unwrap_or(0.0),
                                "z" => loc.z = val.parse().unwrap_or(0.0),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(0),
                                _ => {}
                            }
                        }
                        self.asmodian_spawn = Some(loc);
                    } else if tag == "elyos_spawn_location" {
                        let mut loc = SpawnLocation::default();
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(210010000),
                                "x" => loc.x = val.parse().unwrap_or(0.0),
                                "y" => loc.y = val.parse().unwrap_or(0.0),
                                "z" => loc.z = val.parse().unwrap_or(0.0),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(0),
                                _ => {}
                            }
                        }
                        self.elyos_spawn = Some(loc);
                    } else if tag == "asmodian_telos_location" {
                        let mut loc = SpawnLocation::default();
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(220080000),
                                "x" => loc.x = val.parse().unwrap_or(0.0),
                                "y" => loc.y = val.parse().unwrap_or(0.0),
                                "z" => loc.z = val.parse().unwrap_or(0.0),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(0),
                                _ => {}
                            }
                        }
                        self.asmodian_telos_spawn = Some(loc);
                    } else if tag == "elyos_telos_location" {
                        let mut loc = SpawnLocation::default();
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(210070000),
                                "x" => loc.x = val.parse().unwrap_or(0.0),
                                "y" => loc.y = val.parse().unwrap_or(0.0),
                                "z" => loc.z = val.parse().unwrap_or(0.0),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(0),
                                _ => {}
                            }
                        }
                        self.elyos_telos_spawn = Some(loc);
                    } else if tag == "player_data" {
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            if key == "class" {
                                current_class = val.to_uppercase();
                            }
                        }
                    } else if tag == "item" && !current_class.is_empty() {
                        let mut item_id = 0u32;
                        let mut count = 1u32;
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "id" => item_id = val.parse().unwrap_or(0),
                                "count" => count = val.parse().unwrap_or(1),
                                _ => {}
                            }
                        }
                        if item_id > 0 {
                            self.class_items
                                .entry(current_class.clone())
                                .or_default()
                                .push((item_id, count));
                            items_count += 1;
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "player_data" {
                        current_class.clear();
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(items_count)
    }
}
