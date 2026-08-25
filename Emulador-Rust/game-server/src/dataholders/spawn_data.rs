//! SpawnsDataHolder - Carregamento de todos os spawns de monstros e NPCs de todos os mapas

use std::collections::HashMap;
use std::fs::File;
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
