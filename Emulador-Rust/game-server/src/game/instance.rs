//! Motor de Instâncias Dinâmicas, Sieges de Fortalezas e Rifts

use std::collections::HashMap;
use super::engine::Coord;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorldMapInstance {
    pub instance_id: u32,
    pub map_id: u32,
    pub party_id: Option<u32>,
    pub players: Vec<u32>,
    pub created_at_tick: u64,
    pub expires_at_tick: u64,
}

impl WorldMapInstance {
    pub fn is_expired(&self, current_tick: u64) -> bool {
        current_tick >= self.expires_at_tick
    }

    pub fn is_empty(&self) -> bool {
        self.players.is_empty()
    }
}

#[derive(Debug, Default)]
pub struct InstanceManager {
    next_instance_id: u32,
    instances: HashMap<u32, WorldMapInstance>,
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

        let instance = WorldMapInstance {
            instance_id,
            map_id,
            party_id,
            players: Vec::new(),
            created_at_tick: current_tick,
            expires_at_tick: current_tick + duration_ticks,
        };

        self.instances.insert(instance_id, instance);
        instance_id
    }

    pub fn add_player(&mut self, instance_id: u32, player_id: u32) -> bool {
        if let Some(inst) = self.instances.get_mut(&instance_id) {
            if !inst.players.contains(&player_id) {
                inst.players.push(player_id);
            }
            true
        } else {
            false
        }
    }

    pub fn remove_player(&mut self, instance_id: u32, player_id: u32) -> bool {
        if let Some(inst) = self.instances.get_mut(&instance_id) {
            if let Some(pos) = inst.players.iter().position(|&id| id == player_id) {
                inst.players.remove(pos);
                true
            } else {
                false
            }
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

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SiegeState {
    Peaceful,
    Vulnerable,
}

#[derive(Debug, Clone)]
pub struct SiegeLocation {
    pub id: u32,
    pub name: String,
    pub state: SiegeState,
    pub occupying_legion_id: Option<u32>,
    pub deity_hp: i32,
}

impl SiegeLocation {
    pub fn new(id: u32, name: &str) -> Self {
        Self {
            id,
            name: name.to_string(),
            state: SiegeState::Peaceful,
            occupying_legion_id: None,
            deity_hp: 1_000_000,
        }
    }

    pub fn start_siege(&mut self) {
        self.state = SiegeState::Vulnerable;
        self.deity_hp = 1_000_000;
    }

    pub fn resolve_siege(&mut self, winning_legion_id: Option<u32>) {
        self.occupying_legion_id = winning_legion_id;
        self.state = SiegeState::Peaceful;
    }
}

#[derive(Debug, Clone)]
pub struct Rift {
    pub id: u32,
    pub origin_map: u32,
    pub dest_map: u32,
    pub origin_pos: Coord,
    pub dest_pos: Coord,
    pub min_level: u16,
    pub max_level: u16,
    pub max_uses: u32,
    pub current_uses: u32,
    pub is_active: bool,
}

impl Rift {
    pub fn new(
        id: u32,
        origin_map: u32,
        dest_map: u32,
        origin_pos: Coord,
        dest_pos: Coord,
        min_level: u16,
        max_level: u16,
        max_uses: u32,
    ) -> Self {
        Self {
            id,
            origin_map,
            dest_map,
            origin_pos,
            dest_pos,
            min_level,
            max_level,
            max_uses,
            current_uses: 0,
            is_active: true,
        }
    }

    pub fn try_teleport(&mut self, player_level: u16) -> Option<Coord> {
        if !self.is_active || self.current_uses >= self.max_uses {
            return None;
        }

        if player_level >= self.min_level && player_level <= self.max_level {
            self.current_uses += 1;
            if self.current_uses >= self.max_uses {
                self.is_active = false;
            }
            Some(self.dest_pos)
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn instance_lifecycle_and_cleanup() {
        let mut mgr = InstanceManager::new();
        let inst_id = mgr.create_instance(300040000, Some(101), 1000, 100);

        assert_eq!(mgr.instance_count(), 1);
        assert!(mgr.add_player(inst_id, 1));
        assert!(mgr.add_player(inst_id, 2));

        // Player leaves
        assert!(mgr.remove_player(inst_id, 1));
        assert!(mgr.remove_player(inst_id, 2));

        // Cleanup before expiration should retain instance until grace period expires
        assert_eq!(mgr.cleanup(200), 0);

        // Cleanup after grace period
        assert_eq!(mgr.cleanup(500), 1);
        assert_eq!(mgr.instance_count(), 0);
    }

    #[test]
    fn siege_state_transitions_and_conquest() {
        let mut fort = SiegeLocation::new(1011, "Divine Fortress");
        assert_eq!(fort.state, SiegeState::Peaceful);

        fort.start_siege();
        assert_eq!(fort.state, SiegeState::Vulnerable);

        // Legion 55 captures the fort
        fort.resolve_siege(Some(55));
        assert_eq!(fort.state, SiegeState::Peaceful);
        assert_eq!(fort.occupying_legion_id, Some(55));
    }

    #[test]
    fn rift_level_and_usage_limits() {
        let mut rift = Rift::new(
            1,
            210020000,
            220020000,
            Coord::new(100.0, 100.0, 0.0),
            Coord::new(500.0, 500.0, 10.0),
            20,
            32,
            2,
        );

        // Player level 15 (too low)
        assert_eq!(rift.try_teleport(15), None);

        // Player level 25 (valid)
        assert!(rift.try_teleport(25).is_some());
        assert_eq!(rift.current_uses, 1);

        // Player level 30 (valid, reaches max_uses)
        assert!(rift.try_teleport(30).is_some());
        assert_eq!(rift.current_uses, 2);
        assert!(!rift.is_active);

        // Player level 28 (rift closed)
        assert_eq!(rift.try_teleport(28), None);
    }
}
