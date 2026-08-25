//! WorldMapsDataHolder & ZoneDataHolder - Catálogo de Mapas, Zonas e Instâncias (world/client_world_*.xml)

use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct WorldMapTemplate {
    pub map_id: u32,
    pub name: String,
    pub file_name: String,
    pub is_instance: bool,
    pub max_players: u32,
}

#[derive(Debug, Clone, Default)]
pub struct WorldMapsDataHolder {
    pub world_maps: HashMap<u32, WorldMapTemplate>,
}

impl WorldMapsDataHolder {
    pub fn new() -> Self {
        Self {
            world_maps: HashMap::new(),
        }
    }

    pub fn get_map(&self, map_id: u32) -> Option<&WorldMapTemplate> {
        self.world_maps.get(&map_id)
    }

    pub fn load_from_directory(&mut self, world_dir: &Path) -> Result<usize, String> {
        if !world_dir.exists() {
            return Err(format!("World directory {} does not exist", world_dir.display()));
        }

        let entries = fs::read_dir(world_dir).map_err(|e| e.to_string())?;

        for entry_res in entries {
            let entry = entry_res.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("xml") {
                let file_name = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                if file_name.starts_with("client_world_") {
                    let map_name = file_name
                        .trim_start_matches("client_world_")
                        .trim_end_matches(".xml")
                        .to_string();

                    let map_id = map_name_to_id(&map_name);
                    let is_instance = map_name.starts_with("id");

                    self.world_maps.insert(
                        map_id,
                        WorldMapTemplate {
                            map_id,
                            name: map_name,
                            file_name,
                            is_instance,
                            max_players: if is_instance { 24 } else { 5000 },
                        },
                    );
                }
            }
        }

        Ok(self.world_maps.len())
    }
}

fn map_name_to_id(map_name: &str) -> u32 {
    match map_name {
        "lf1" | "lf1a" => 210010000, // Poeta / Sanctum
        "lf2" => 210030000,          // Verteron
        "lf3" => 210020000,          // Eltnen
        "lf4" => 210040000,          // Heiron
        "df1" => 220010000,          // Ishalgen
        "df2" | "df2a" => 220020000, // Morheim
        "df3" => 220040000,          // Beluslan
        "df4" => 220050000,          // Brusthonin
        "ab1" => 400010000,          // Reshanta (Abyss)
        "ldf1" => 600010000,         // Silentera Canyon
        "ldf4a" => 600020000,        // Katalam
        "ldf3_01" => 600030000,      // Danaria
        "ldf10" => 600040000,        // Kaldor
        _ => {
            // Hash determinístico se for ID desconhecido
            let mut h = 300000000u32;
            for b in map_name.bytes() {
                h = h.wrapping_add(b as u32).wrapping_mul(31);
            }
            h
        }
    }
}
