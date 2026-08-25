//! MonsterController - Gerenciador de combate, aggro, hate table e morte de monstros

use std::collections::HashMap;
use super::creature::CreatureController;

#[derive(Debug, Clone, Default)]
pub struct HateTable {
    pub entries: HashMap<u32, i32>,
}

impl HateTable {
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    pub fn add_hate(&mut self, player_id: u32, amount: i32) {
        let entry = self.entries.entry(player_id).or_insert(0);
        *entry += amount;
    }

    pub fn get_highest_target(&self) -> Option<u32> {
        self.entries
            .iter()
            .max_by_key(|(_, hate)| *hate)
            .map(|(id, _)| *id)
    }

    pub fn clear(&mut self) {
        self.entries.clear();
    }
}

#[derive(Debug, Clone)]
pub struct MonsterController {
    pub creature: CreatureController,
    pub template_id: u32,
    pub spawn_x: f32,
    pub spawn_y: f32,
    pub spawn_z: f32,
    pub leash_radius: f32,
    pub hate_table: HateTable,
    pub is_leashing: bool,
}

impl MonsterController {
    pub fn new(obj_id: u32, template_id: u32, max_hp: i32, x: f32, y: f32, z: f32) -> Self {
        Self {
            creature: CreatureController::new(obj_id, max_hp, 500),
            template_id,
            spawn_x: x,
            spawn_y: y,
            spawn_z: z,
            leash_radius: 35.0,
            hate_table: HateTable::new(),
            is_leashing: false,
        }
    }

    pub fn add_hate(&mut self, player_id: u32, hate: i32) {
        if !self.is_leashing && !self.creature.is_dead {
            self.hate_table.add_hate(player_id, hate);
            self.creature.set_target(self.hate_table.get_highest_target());
            self.creature.is_in_combat = true;
        }
    }

    pub fn check_leash(&mut self, cur_x: f32, cur_y: f32) -> bool {
        let dx = cur_x - self.spawn_x;
        let dy = cur_y - self.spawn_y;
        let dist = (dx * dx + dy * dy).sqrt();
        if dist > self.leash_radius {
            self.is_leashing = true;
            self.hate_table.clear();
            self.creature.set_target(None);
            self.creature.hp = self.creature.max_hp;
            self.creature.is_in_combat = false;
            true
        } else {
            false
        }
    }

    pub fn reset_at_spawn(&mut self) {
        self.is_leashing = false;
        self.creature.hp = self.creature.max_hp;
        self.creature.is_in_combat = false;
        self.creature.is_dead = false;
    }
}
