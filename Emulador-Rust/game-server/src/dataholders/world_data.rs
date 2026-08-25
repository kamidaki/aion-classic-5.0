//! WorldMapsDataHolder & ZoneDataHolder - Catálogo de Mapas, Zonas e Instâncias (world/client_world_*.xml e zonemap.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Copy, Default)]
pub struct MapPoint {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

#[derive(Debug, Clone, Default)]
pub struct SubzoneDef {
    pub name: String,
    pub string_id: String,
    pub priority: u32,
    pub bottom_z: f32,
    pub top_z: f32,
    pub map_points: Vec<MapPoint>,
    pub key_points: Vec<MapPoint>,
}

#[derive(Debug, Clone)]
pub struct WorldMapTemplate {
    pub map_id: u32,
    pub name: String,
    pub file_name: String,
    pub world_width: u32,
    pub world_height: u32,
    pub map_category: String,
    pub is_instance: bool,
    pub max_players: u32,
    pub subzones: Vec<SubzoneDef>,
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

    /// Carrega o catálogo completo direto dos XMLs originais do client (`data/client/world`)
    pub fn load_from_directory(&mut self, world_dir: &Path) -> Result<usize, String> {
        if !world_dir.exists() {
            return Err(format!("World directory {} does not exist", world_dir.display()));
        }

        // 1. Carrega zonemap.xml primeiro para mapear IDs oficiais, nomes e dimensoes
        let zonemap_path = world_dir.join("zonemap.xml");
        if zonemap_path.exists() {
            self.load_zonemap(&zonemap_path)?;
        }

        // 2. Carrega todos os client_world_*.xml para extrair subzonas, relevos e pontos de mapa
        let entries = fs::read_dir(world_dir).map_err(|e| e.to_string())?;
        for entry_res in entries {
            let entry = entry_res.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("xml") {
                let file_name = path.file_name().unwrap_or_default().to_string_lossy().to_string();
                if file_name.starts_with("client_world_") {
                    let _ = self.load_world_subzones(&path, &file_name);
                }
            }
        }

        Ok(self.world_maps.len())
    }

    fn load_zonemap(&mut self, zonemap_path: &Path) -> Result<(), String> {
        let mut reader = Reader::from_file(zonemap_path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_zonemap = false;
        let mut current_tag = String::new();
        let mut id = 0u32;
        let mut name = String::new();
        let mut world_width = 0u32;
        let mut world_height = 0u32;
        let mut map_category = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag_name = e.name();
                    let tag = String::from_utf8_lossy(tag_name.as_ref()).to_string();
                    if tag == "zonemap" {
                        in_zonemap = true;
                        id = 0;
                        name.clear();
                        world_width = 0;
                        world_height = 0;
                        map_category.clear();
                    } else if in_zonemap {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_zonemap {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => id = text.parse().unwrap_or(0),
                            "name" => name = text,
                            "world_width" => world_width = text.parse().unwrap_or(0),
                            "world_height" => world_height = text.parse().unwrap_or(0),
                            "map_category" => map_category = text,
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "zonemap" && in_zonemap {
                        if id > 0 {
                            let file_name = format!("client_world_{}.xml", name.to_lowercase());
                            let is_instance = id >= 300000000 && id < 400000000;
                            self.world_maps.insert(
                                id,
                                WorldMapTemplate {
                                    map_id: id,
                                    name: std::mem::take(&mut name),
                                    file_name,
                                    world_width,
                                    world_height,
                                    map_category: std::mem::take(&mut map_category),
                                    is_instance,
                                    max_players: if is_instance { 24 } else { 5000 },
                                    subzones: Vec::new(),
                                },
                            );
                        }
                        in_zonemap = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(())
    }

    fn load_world_subzones(&mut self, path: &Path, file_name: &str) -> Result<(), String> {
        let mut reader = match Reader::from_file(path) {
            Ok(r) => r,
            Err(_) => return Ok(()),
        };
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_subzone = false;
        let mut current_tag = String::new();
        let mut cur_subzone = SubzoneDef::default();
        let mut cur_point = MapPoint::default();
        let mut in_map_point = false;
        let mut in_key_point = false;

        let map_name_core = file_name
            .trim_start_matches("client_world_")
            .trim_end_matches(".xml")
            .to_lowercase();

        // Encontra o map_id correspondente
        let map_id = self
            .world_maps
            .iter()
            .find(|(_, tmpl)| tmpl.name.eq_ignore_ascii_case(&map_name_core))
            .map(|(id, _)| *id)
            .unwrap_or_else(|| map_name_to_id(&map_name_core));

        let mut subzones = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag_name = e.name();
                    let tag = String::from_utf8_lossy(tag_name.as_ref()).to_string();
                    if tag == "subzone" {
                        in_subzone = true;
                        cur_subzone = SubzoneDef::default();
                    } else if tag == "map_point" {
                        in_map_point = true;
                        cur_point = MapPoint::default();
                    } else if tag == "key_point" {
                        in_key_point = true;
                        cur_point = MapPoint::default();
                    } else if in_subzone {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_subzone {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        if in_map_point || in_key_point {
                            match current_tag.as_str() {
                                "x" => cur_point.x = text.parse().unwrap_or(0.0),
                                "y" => cur_point.y = text.parse().unwrap_or(0.0),
                                "z" => cur_point.z = text.parse().unwrap_or(0.0),
                                _ => {}
                            }
                        } else {
                            match current_tag.as_str() {
                                "name" => cur_subzone.name = text,
                                "string" => cur_subzone.string_id = text,
                                "priority" => cur_subzone.priority = text.parse().unwrap_or(0),
                                "bottom" => cur_subzone.bottom_z = text.parse().unwrap_or(0.0),
                                "top" => cur_subzone.top_z = text.parse().unwrap_or(0.0),
                                _ => {}
                            }
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "map_point" && in_map_point {
                        cur_subzone.map_points.push(cur_point);
                        in_map_point = false;
                    } else if tag == "key_point" && in_key_point {
                        cur_subzone.key_points.push(cur_point);
                        in_key_point = false;
                    } else if tag == "subzone" && in_subzone {
                        subzones.push(std::mem::take(&mut cur_subzone));
                        in_subzone = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(_) => break,
                _ => {}
            }
            buf.clear();
        }

        if let Some(tmpl) = self.world_maps.get_mut(&map_id) {
            tmpl.subzones = subzones;
        } else {
            let is_instance = map_name_core.starts_with("id");
            self.world_maps.insert(
                map_id,
                WorldMapTemplate {
                    map_id,
                    name: map_name_core,
                    file_name: file_name.to_string(),
                    world_width: 3072,
                    world_height: 3072,
                    map_category: if is_instance { "instance".to_string() } else { "world".to_string() },
                    is_instance,
                    max_players: if is_instance { 24 } else { 5000 },
                    subzones,
                },
            );
        }

        Ok(())
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
            let mut h = 300000000u32;
            for b in map_name.bytes() {
                h = h.wrapping_add(b as u32).wrapping_mul(31);
            }
            h
        }
    }
}
