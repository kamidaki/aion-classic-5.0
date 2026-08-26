//! Instâncias do Mundo e Gerenciador de Instâncias (WorldMapInstance / InstanceManager - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::instance::models::dungeon_gate::DungeonGate;
use crate::instance::models::instance_reward::InstanceScore;
use crate::instance::models::stage_type::StageType;

#[derive(Debug, Clone)]
pub struct WorldMapInstance {
    pub instance_id: u32,
    pub map_id: u32,
    pub party_id: Option<u32>,
    pub players: Vec<u32>,
    pub created_at_tick: u64,
    pub expires_at_tick: u64,
    pub stage: StageType,
    pub score: InstanceScore,
    pub gates: HashMap<u32, DungeonGate>,
}

impl WorldMapInstance {
    pub fn new(instance_id: u32, map_id: u32, party_id: Option<u32>, duration_ticks: u64, current_tick: u64) -> Self {
        Self {
            instance_id,
            map_id,
            party_id,
            players: Vec::new(),
            created_at_tick: current_tick,
            expires_at_tick: current_tick + duration_ticks,
            stage: StageType::Starting,
            score: InstanceScore::new(),
            gates: HashMap::new(),
        }
    }

    pub fn is_expired(&self, current_tick: u64) -> bool {
        current_tick >= self.expires_at_tick
    }

    pub fn is_empty(&self) -> bool {
        self.players.is_empty()
    }

    pub fn add_player(&mut self, player_id: u32) {
        if !self.players.contains(&player_id) {
            self.players.push(player_id);
        }
    }

    pub fn remove_player(&mut self, player_id: u32) -> bool {
        if let Some(pos) = self.players.iter().position(|&id| id == player_id) {
            self.players.remove(pos);
            true
        } else {
            false
        }
    }
}

#[derive(Debug, Default)]
pub struct InstanceManager {
    next_instance_id: u32,
    pub instances: HashMap<u32, WorldMapInstance>,
}

impl InstanceManager {
    pub fn new() -> Self {
        Self {
            next_instance_id: 1,
            instances: HashMap::new(),
        }
    }

    pub fn create_instance(
        &mut self,
        map_id: u32,
        party_id: Option<u32>,
        duration_ticks: u64,
        current_tick: u64,
    ) -> u32 {
        let instance_id = self.next_instance_id;
        self.next_instance_id += 1;

        let instance = WorldMapInstance::new(instance_id, map_id, party_id, duration_ticks, current_tick);
        self.instances.insert(instance_id, instance);
        instance_id
    }

    pub fn get_instance(&self, instance_id: u32) -> Option<&WorldMapInstance> {
        self.instances.get(&instance_id)
    }

    pub fn get_instance_mut(&mut self, instance_id: u32) -> Option<&mut WorldMapInstance> {
        self.instances.get_mut(&instance_id)
    }

    pub fn add_player(&mut self, instance_id: u32, player_id: u32) -> bool {
        if let Some(inst) = self.instances.get_mut(&instance_id) {
            inst.add_player(player_id);
            true
        } else {
            false
        }
    }

    pub fn remove_player(&mut self, instance_id: u32, player_id: u32) -> bool {
        if let Some(inst) = self.instances.get_mut(&instance_id) {
            inst.remove_player(player_id)
        } else {
            false
        }
    }

    pub fn cleanup(&mut self, current_tick: u64) -> usize {
        let mut to_remove = Vec::new();
        for (&id, inst) in &self.instances {
            if inst.is_expired(current_tick) || (inst.is_empty() && current_tick > inst.created_at_tick + 300) {
                to_remove.push(id);
            }
        }

        let count = to_remove.len();
        for id in to_remove {
            self.instances.remove(&id);
        }
        count
    }

    pub fn instance_count(&self) -> usize {
        self.instances.len()
    }
}
