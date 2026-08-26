//! Orquestrador Central do Motor de Instâncias (InstanceEngine - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::arena_handler::ArenaInstanceHandler;
use crate::instance::handlers::boss_rush_handler::BossRushInstanceHandler;
use crate::instance::handlers::dredgion_handler::DredgionInstanceHandler;
use crate::instance::handlers::general_handler::GeneralInstanceHandler;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::handlers::tiak_handler::TiakResearchCenterHandler;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

pub enum DynamicHandler {
    General(GeneralInstanceHandler),
    Dredgion(DredgionInstanceHandler),
    Tiak(TiakResearchCenterHandler),
    Arena(ArenaInstanceHandler),
    BossRush(BossRushInstanceHandler),
}

impl DynamicHandler {
    pub fn on_instance_create(&mut self, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_instance_create(instance),
            Self::Dredgion(h) => h.on_instance_create(instance),
            Self::Tiak(h) => h.on_instance_create(instance),
            Self::Arena(h) => h.on_instance_create(instance),
            Self::BossRush(h) => h.on_instance_create(instance),
        }
    }

    pub fn on_instance_destroy(&mut self, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_instance_destroy(instance),
            Self::Dredgion(h) => h.on_instance_destroy(instance),
            Self::Tiak(h) => h.on_instance_destroy(instance),
            Self::Arena(h) => h.on_instance_destroy(instance),
            Self::BossRush(h) => h.on_instance_destroy(instance),
        }
    }

    pub fn on_enter_instance(&mut self, player: &Character, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_enter_instance(player, instance),
            Self::Dredgion(h) => h.on_enter_instance(player, instance),
            Self::Tiak(h) => h.on_enter_instance(player, instance),
            Self::Arena(h) => h.on_enter_instance(player, instance),
            Self::BossRush(h) => h.on_enter_instance(player, instance),
        }
    }

    pub fn on_leave_instance(&mut self, player_id: u32, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_leave_instance(player_id, instance),
            Self::Dredgion(h) => h.on_leave_instance(player_id, instance),
            Self::Tiak(h) => h.on_leave_instance(player_id, instance),
            Self::Arena(h) => h.on_leave_instance(player_id, instance),
            Self::BossRush(h) => h.on_leave_instance(player_id, instance),
        }
    }

    pub fn on_open_door(&mut self, player_id: u32, door_id: u32, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_open_door(player_id, door_id, instance),
            Self::Dredgion(h) => h.on_open_door(player_id, door_id, instance),
            Self::Tiak(h) => h.on_open_door(player_id, door_id, instance),
            Self::Arena(h) => h.on_open_door(player_id, door_id, instance),
            Self::BossRush(h) => h.on_open_door(player_id, door_id, instance),
        }
    }

    pub fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_die_npc(npc, instance),
            Self::Dredgion(h) => h.on_die_npc(npc, instance),
            Self::Tiak(h) => h.on_die_npc(npc, instance),
            Self::Arena(h) => h.on_die_npc(npc, instance),
            Self::BossRush(h) => h.on_die_npc(npc, instance),
        }
    }

    pub fn on_die_player(&mut self, player: &Character, instance: &mut WorldMapInstance) -> bool {
        match self {
            Self::General(h) => h.on_die_player(player, instance),
            Self::Dredgion(h) => h.on_die_player(player, instance),
            Self::Tiak(h) => h.on_die_player(player, instance),
            Self::Arena(h) => h.on_die_player(player, instance),
            Self::BossRush(h) => h.on_die_player(player, instance),
        }
    }

    pub fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        match self {
            Self::General(h) => h.on_change_stage(stage, instance),
            Self::Dredgion(h) => h.on_change_stage(stage, instance),
            Self::Tiak(h) => h.on_change_stage(stage, instance),
            Self::Arena(h) => h.on_change_stage(stage, instance),
            Self::BossRush(h) => h.on_change_stage(stage, instance),
        }
    }
}

pub struct InstanceEngine {
    // instance_id -> DynamicHandler
    pub active_handlers: HashMap<u32, DynamicHandler>,
}

impl Default for InstanceEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl InstanceEngine {
    pub fn new() -> Self {
        Self {
            active_handlers: HashMap::new(),
        }
    }

    /// Cria e associa o handler correto com base no ID do mapa / Masmorra
    pub fn create_handler_for_map(&mut self, instance: &mut WorldMapInstance) {
        let mut handler = match instance.map_id {
            300040000 | 300110000 | 300210000 => DynamicHandler::Dredgion(DredgionInstanceHandler::new()), // Dredgions
            300350000 | 300360000 => DynamicHandler::Arena(ArenaInstanceHandler::new(3)),                  // Arenas
            300550000 => DynamicHandler::Tiak(TiakResearchCenterHandler::new()),                            // Tiak Research Center
            300150000 | 300280000 => DynamicHandler::BossRush(BossRushInstanceHandler::new()),             // Padmarashka / Tahabata
            _ => DynamicHandler::General(GeneralInstanceHandler::new(instance.map_id)),
        };

        handler.on_instance_create(instance);
        self.active_handlers.insert(instance.instance_id, handler);
    }

    pub fn on_enter(&mut self, instance: &mut WorldMapInstance, player: &Character) {
        if let Some(h) = self.active_handlers.get_mut(&instance.instance_id) {
            h.on_enter_instance(player, instance);
        }
    }

    pub fn on_leave(&mut self, instance: &mut WorldMapInstance, player_id: u32) {
        if let Some(h) = self.active_handlers.get_mut(&instance.instance_id) {
            h.on_leave_instance(player_id, instance);
        }
    }

    pub fn on_die_npc(&mut self, instance: &mut WorldMapInstance, npc: &Entity) {
        if let Some(h) = self.active_handlers.get_mut(&instance.instance_id) {
            h.on_die_npc(npc, instance);
        }
    }

    pub fn on_die_player(&mut self, instance: &mut WorldMapInstance, player: &Character) -> bool {
        if let Some(h) = self.active_handlers.get_mut(&instance.instance_id) {
            h.on_die_player(player, instance)
        } else {
            false
        }
    }

    pub fn on_open_door(&mut self, instance: &mut WorldMapInstance, player_id: u32, door_id: u32) {
        if let Some(h) = self.active_handlers.get_mut(&instance.instance_id) {
            h.on_open_door(player_id, door_id, instance);
        }
    }

    pub fn on_instance_destroy(&mut self, instance: &mut WorldMapInstance) {
        if let Some(mut h) = self.active_handlers.remove(&instance.instance_id) {
            h.on_instance_destroy(instance);
        }
    }
}
