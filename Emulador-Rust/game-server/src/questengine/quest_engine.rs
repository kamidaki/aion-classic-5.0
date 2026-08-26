//! Motor Central de Missões do Aion (QuestEngine - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::sync::Arc;
use crate::questengine::handlers::{HandlerResult, QuestHandler};
use crate::questengine::model::{QuestEnv, QuestState};

#[derive(Default)]
pub struct QuestEngine {
    handlers: HashMap<u32, Arc<dyn QuestHandler>>,
}

impl QuestEngine {
    pub fn new() -> Self {
        Self {
            handlers: HashMap::new(),
        }
    }

    pub fn register_handler(&mut self, handler: Arc<dyn QuestHandler>) {
        self.handlers.insert(handler.get_quest_id(), handler);
    }

    pub fn get_handler(&self, quest_id: u32) -> Option<&Arc<dyn QuestHandler>> {
        self.handlers.get(&quest_id)
    }

    pub fn on_dialog(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_dialog(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_kill(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_kill(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_kill_in_world(&self, env: &mut QuestEnv, state: &mut QuestState, world_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_kill_in_world(env, state, world_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_gather(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_gather(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_movie_end(&self, env: &mut QuestEnv, state: &mut QuestState, movie_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_movie_end(env, state, movie_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_enter_zone(&self, env: &mut QuestEnv, state: &mut QuestState, zone_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_enter_zone(env, state, zone_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_leave_zone(&self, env: &mut QuestEnv, state: &mut QuestState, zone_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_leave_zone(env, state, zone_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_loot_item(&self, env: &mut QuestEnv, state: &mut QuestState, item_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_loot_item(env, state, item_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_item_use(&self, env: &mut QuestEnv, state: &mut QuestState, item_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_item_use(env, state, item_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_attack(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_attack(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_enter_world(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_enter_world(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_level_up(&self, env: &mut QuestEnv, state: &mut QuestState, new_level: u8) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_level_up(env, state, new_level)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_die(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_die(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_can_act(&self, env: &QuestEnv, state: &QuestState) -> bool {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_can_act(env, state)
        } else {
            true
        }
    }

    pub fn on_pass_flying_ring(&self, env: &mut QuestEnv, state: &mut QuestState, ring_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_pass_flying_ring(env, state, ring_id)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_invisible_timer_end(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_invisible_timer_end(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_atreian_passport(&self, env: &mut QuestEnv, state: &mut QuestState) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_atreian_passport(env, state)
        } else {
            HandlerResult::Unknown
        }
    }

    pub fn on_equip_item(&self, env: &mut QuestEnv, state: &mut QuestState, item_id: u32) -> HandlerResult {
        if let Some(handler) = self.handlers.get(&env.quest_id) {
            handler.on_equip_item(env, state, item_id)
        } else {
            HandlerResult::Unknown
        }
    }
}
