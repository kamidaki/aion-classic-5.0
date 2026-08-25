//! PlayerInitialDataHolder - Ponto de Spawn Inicial por Raça e Equipamentos/Itens Iniciais por Classe (player_initial_data.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SpawnLocation {
    pub map_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
}

impl Default for SpawnLocation {
    fn default() -> Self {
        Self {
            map_id: 210010000,
            x: 1207.7640,
            y: 1044.5725,
            z: 140.14894,
            heading: 59,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct PlayerInitialDataHolder {
    pub elyos_spawn: SpawnLocation,
    pub asmodian_spawn: SpawnLocation,
    pub class_items: HashMap<String, Vec<(u32, u32)>>,
}

impl PlayerInitialDataHolder {
    pub fn new() -> Self {
        Self {
            elyos_spawn: SpawnLocation {
                map_id: 210010000,
                x: 1207.7640,
                y: 1044.5725,
                z: 140.14894,
                heading: 59,
            },
            asmodian_spawn: SpawnLocation {
                map_id: 220010000,
                x: 582.3742,
                y: 2790.7642,
                z: 299.3282,
                heading: 66,
            },
            class_items: HashMap::new(),
        }
    }

    pub fn get_spawn_location(&self, race: u8) -> SpawnLocation {
        if race == 1 {
            // Asmodian
            self.asmodian_spawn
        } else {
            // Elyos (0 ou default)
            self.elyos_spawn
        }
    }

    pub fn get_initial_items(&self, class_name: &str) -> Vec<(u32, u32)> {
        let key = class_name.to_uppercase();
        if let Some(items) = self.class_items.get(&key) {
            items.clone()
        } else {
            // Mapeamentos de aliases e classes derivadas
            let base = match key.as_str() {
                "GLADIATOR" | "BATTLEMASTER" | "TEMPLAR" | "KNIGHT" => "WARRIOR",
                "ASSASSIN" | "RANGER" => "SCOUT",
                "SORCERER" | "WIZARD" | "SPIRIT_MASTER" | "ELEMENTALLIST" => "MAGE",
                "CLERIC" | "CHANTER" => "PRIEST",
                "GUNSLINGER" | "GUNNER" | "AETHERTECH" | "RIDER" => "ENGINEER",
                "SONGWEAVER" | "BARD" => "ARTIST",
                "BRAWLER" | "REVENANT" => "MONK",
                _ => "WARRIOR",
            };
            self.class_items.get(base).cloned().unwrap_or_default()
        }
    }

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
                        let mut loc = SpawnLocation {
                            map_id: 220010000,
                            x: 582.3742,
                            y: 2790.7642,
                            z: 299.3282,
                            heading: 66,
                        };
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(220010000),
                                "x" => loc.x = val.parse().unwrap_or(582.3742),
                                "y" => loc.y = val.parse().unwrap_or(2790.7642),
                                "z" => loc.z = val.parse().unwrap_or(299.3282),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(66),
                                _ => {}
                            }
                        }
                        self.asmodian_spawn = loc;
                    } else if tag == "elyos_spawn_location" {
                        let mut loc = SpawnLocation {
                            map_id: 210010000,
                            x: 1207.7640,
                            y: 1044.5725,
                            z: 140.14894,
                            heading: 59,
                        };
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "map_id" => loc.map_id = val.parse().unwrap_or(210010000),
                                "x" => loc.x = val.parse().unwrap_or(1207.7640),
                                "y" => loc.y = val.parse().unwrap_or(1044.5725),
                                "z" => loc.z = val.parse().unwrap_or(140.14894),
                                "h" | "heading" => loc.heading = val.parse().unwrap_or(59),
                                _ => {}
                            }
                        }
                        self.elyos_spawn = loc;
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
