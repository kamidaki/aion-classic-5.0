use std::collections::HashSet;
use std::sync::RwLock;

#[derive(Debug)]
pub struct Region {
    pub region_id: u32,
    pub x: u32,
    pub y: u32,
    pub players: RwLock<HashSet<u32>>,
    pub npcs: RwLock<HashSet<u32>>,
    pub objects: RwLock<HashSet<u32>>,
}

impl Region {
    pub fn new(region_id: u32, x: u32, y: u32) -> Self {
        Self {
            region_id,
            x,
            y,
            players: RwLock::new(HashSet::new()),
            npcs: RwLock::new(HashSet::new()),
            objects: RwLock::new(HashSet::new()),
        }
    }

    pub fn add_player(&self, player_id: u32) {
        let mut players = self.players.write().unwrap();
        players.insert(player_id);
    }

    pub fn remove_player(&self, player_id: u32) {
        let mut players = self.players.write().unwrap();
        players.remove(&player_id);
    }

    pub fn add_npc(&self, npc_id: u32) {
        let mut npcs = self.npcs.write().unwrap();
        npcs.insert(npc_id);
    }

    pub fn remove_npc(&self, npc_id: u32) {
        let mut npcs = self.npcs.write().unwrap();
        npcs.remove(&npc_id);
    }

    pub fn get_players(&self) -> Vec<u32> {
        let players = self.players.read().unwrap();
        players.iter().copied().collect()
    }

    pub fn get_npcs(&self) -> Vec<u32> {
        let npcs = self.npcs.read().unwrap();
        npcs.iter().copied().collect()
    }
}
