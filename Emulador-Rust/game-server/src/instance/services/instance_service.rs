//! Serviço de Instâncias e Teleportes de Masmorras (InstanceService - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::Instant;

use crate::character::Character;
use crate::engine::Coord;
use crate::instance::instance_engine::InstanceEngine;
use crate::instance::models::instance_cooldown::{InstanceCooldownTracker, InstanceCooltime};
use crate::instance::models::world_instance::InstanceManager;

pub struct InstanceService {
    pub instance_manager: InstanceManager,
    pub instance_engine: InstanceEngine,
    pub cooldown_tracker: InstanceCooldownTracker,
    pub cooldown_templates: HashMap<u32, InstanceCooltime>,
}

impl Default for InstanceService {
    fn default() -> Self {
        Self::new()
    }
}

impl InstanceService {
    pub fn new() -> Self {
        let mut templates = HashMap::new();
        // Templates de cooldown do Aion Classic
        templates.insert(300040000, InstanceCooltime::new(300040000, "Baranath Dredgion", 7200, 3, 46, 50, 6));
        templates.insert(300110000, InstanceCooltime::new(300110000, "Chantra Dredgion", 7200, 3, 51, 55, 6));
        templates.insert(300210000, InstanceCooltime::new(300210000, "Terath Dredgion", 7200, 3, 56, 65, 6));
        templates.insert(300550000, InstanceCooltime::new(300550000, "Tiak Research Center", 7200, 3, 50, 65, 6));
        templates.insert(300150000, InstanceCooltime::new(300150000, "Padmarashka's Cave", 86400, 1, 55, 65, 48));
        templates.insert(300280000, InstanceCooltime::new(300280000, "Dark Poeta", 14400, 2, 48, 65, 6));

        Self {
            instance_manager: InstanceManager::new(),
            instance_engine: InstanceEngine::new(),
            cooldown_tracker: InstanceCooldownTracker::new(),
            cooldown_templates: templates,
        }
    }

    /// Tenta entrar em uma instância com validações completas de nível e cooldown
    pub fn request_enter_instance(
        &mut self,
        player: &Character,
        map_id: u32,
        party_id: Option<u32>,
        now: Instant,
        current_tick: u64,
    ) -> Result<u32, &'static str> {
        if let Some(template) = self.cooldown_templates.get(&map_id) {
            if player.stats.level < template.min_level {
                return Err("Nível insuficiente para entrar nesta masmorra");
            }
            if player.stats.level > template.max_level {
                return Err("Nível máximo ultrapassado para esta masmorra");
            }
            self.cooldown_tracker.can_enter(player.id(), template, now)?;
        }

        let instance_id = self.instance_manager.create_instance(map_id, party_id, 7200, current_tick);
        if let Some(inst) = self.instance_manager.get_instance_mut(instance_id) {
            self.instance_engine.create_handler_for_map(inst);
            self.instance_engine.on_enter(inst, player);
        }

        self.cooldown_tracker.record_entry(player.id(), map_id, now);
        Ok(instance_id)
    }

    /// Retira um jogador de uma instância
    pub fn leave_instance(&mut self, instance_id: u32, player_id: u32) {
        if let Some(inst) = self.instance_manager.get_instance_mut(instance_id) {
            self.instance_engine.on_leave(inst, player_id);
        }
        self.instance_manager.remove_player(instance_id, player_id);
    }
}
