//! SpawnsDataHolder - Carregamento e indexação de todos os spawns de monstros e NPCs de todos os mapas

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufRead, BufReader};
use std::path::Path;

#[derive(Debug, Clone)]
pub struct Spawn {
    pub mapa: u32,
    pub npc_id: u32,
    pub nome_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub respawn_time: u32,
    pub payload: Vec<u8>,
}

#[derive(Debug, Clone, Default)]
pub struct SpawnsDataHolder {
    pub spawns_by_map: HashMap<u32, Vec<Spawn>>,
    pub total_spawns: usize,
}

impl SpawnsDataHolder {
    pub fn new() -> Self {
        Self {
            spawns_by_map: HashMap::new(),
            total_spawns: 0,
        }
    }

    pub fn get_spawns_for_map(&self, map_id: u32) -> Option<&Vec<Spawn>> {
        self.spawns_by_map.get(&map_id)
    }

    pub fn get_all_maps(&self) -> Vec<u32> {
        self.spawns_by_map.keys().copied().collect()
    }

    /// Carrega recursivamente todos os arquivos XML de spawns de uma pasta (ex: data/static_data/spawns)
    pub fn load_from_directory(&mut self, dir_path: &Path) -> Result<usize, String> {
        if !dir_path.exists() {
            return Err(format!("Spawns directory {} does not exist", dir_path.display()));
        }

        self.load_directory_recursive(dir_path);
        Ok(self.total_spawns)
    }

    fn load_directory_recursive(&mut self, dir_path: &Path) {
        if let Ok(entries) = fs::read_dir(dir_path) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    self.load_directory_recursive(&path);
                } else if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("xml") {
                    let _ = self.load_from_xml(&path);
                }
            }
        }
    }

    /// Carrega um arquivo XML de spawns com streaming SAX ultra-rápido
    pub fn load_from_xml(&mut self, file_path: &Path) -> Result<usize, String> {
        let mut reader = match Reader::from_file(file_path) {
            Ok(r) => r,
            Err(e) => return Err(e.to_string()),
        };
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut current_map_id = 0u32;
        let mut current_npc_id = 0u32;
        let mut current_respawn_time = 295u32;
        let mut spawns_added = 0usize;

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag_name = e.name();
                    let tag = String::from_utf8_lossy(tag_name.as_ref()).to_string();

                    if tag == "spawn_map" {
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            if key == "map_id" {
                                current_map_id = val.parse().unwrap_or(0);
                            }
                        }
                    } else if tag == "spawn" {
                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            if key == "npc_id" {
                                current_npc_id = val.parse().unwrap_or(0);
                            } else if key == "respawn_time" {
                                current_respawn_time = val.parse().unwrap_or(295);
                            }
                        }
                    }
                }
                Ok(Event::Empty(e)) => {
                    let tag_name = e.name();
                    let tag = String::from_utf8_lossy(tag_name.as_ref()).to_string();

                    if tag == "spot" && current_map_id > 0 && current_npc_id > 0 {
                        let mut x = 0.0f32;
                        let mut y = 0.0f32;
                        let mut z = 0.0f32;
                        let mut heading = 0u8;

                        for attr in e.attributes().flatten() {
                            let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                            let val = String::from_utf8_lossy(&attr.value).to_string();
                            match key.as_str() {
                                "x" => x = val.parse().unwrap_or(0.0),
                                "y" => y = val.parse().unwrap_or(0.0),
                                "z" => z = val.parse().unwrap_or(0.0),
                                "h" | "heading" => heading = val.parse().unwrap_or(0),
                                _ => {}
                            }
                        }

                        let spawn = Spawn {
                            mapa: current_map_id,
                            npc_id: current_npc_id,
                            nome_id: 0,
                            x,
                            y,
                            z,
                            heading,
                            respawn_time: current_respawn_time,
                            payload: Vec::new(),
                        };

                        self.spawns_by_map.entry(current_map_id).or_default().push(spawn);
                        self.total_spawns += 1;
                        spawns_added += 1;
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "spawn" {
                        current_npc_id = 0;
                    } else if tag == "spawn_map" {
                        current_map_id = 0;
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(spawns_added)
    }

    /// Suporte complementar para leitura de CSV caso necessário
    pub fn load_from_csv(&mut self, path: &Path) -> Result<usize, String> {
        let file = File::open(path).map_err(|e| e.to_string())?;
        let reader = BufReader::new(file);

        for (line_num, line_res) in reader.lines().enumerate() {
            let line = line_res.map_err(|e| e.to_string())?;
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') || line.starts_with("mapa") {
                continue;
            }

            let parts: Vec<&str> = line.split(',').collect();
            if parts.len() >= 6 {
                let mapa = parts[0].trim().parse().unwrap_or(0);
                let npc_id = parts[1].trim().parse().unwrap_or(0);
                let nome_id = parts[2].trim().parse().unwrap_or(0);
                let x = parts[3].trim().parse().unwrap_or(0.0);
                let y = parts[4].trim().parse().unwrap_or(0.0);
                let z = parts[5].trim().parse().unwrap_or(0.0);
                let heading = if parts.len() > 6 {
                    parts[6].trim().parse().unwrap_or(0)
                } else {
                    0
                };

                let payload = if parts.len() > 7 {
                    hex_para_bytes(parts[7]).unwrap_or_default()
                } else {
                    Vec::new()
                };

                let spawn = Spawn {
                    mapa,
                    npc_id,
                    nome_id,
                    x,
                    y,
                    z,
                    heading,
                    respawn_time: 295,
                    payload,
                };

                self.spawns_by_map.entry(mapa).or_default().push(spawn);
                self.total_spawns += 1;
            } else {
                eprintln!("WARN: invalid spawn line {line_num}: {line}");
            }
        }

        Ok(self.total_spawns)
    }
}

fn hex_para_bytes(texto: &str) -> Option<Vec<u8>> {
    let texto = texto.trim();
    if texto.len() % 2 != 0 {
        return None;
    }
    (0..texto.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&texto[i..i + 2], 16).ok())
        .collect()
}
