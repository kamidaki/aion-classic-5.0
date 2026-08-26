//! Trait Canônica do Manipulador de Missão (QuestHandler - Padrão Java Aion Classic 2.8 / 4.5)

use super::handler_result::HandlerResult;
use crate::questengine::model::{QuestEnv, QuestState};

pub trait QuestHandler: Send + Sync {
    fn get_quest_id(&self) -> u32;

    fn on_dialog(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_kill(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_kill_in_world(&self, _env: &mut QuestEnv, _state: &mut QuestState, _world_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_gather(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_movie_end(&self, _env: &mut QuestEnv, _state: &mut QuestState, _movie_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_enter_zone(&self, _env: &mut QuestEnv, _state: &mut QuestState, _zone_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_leave_zone(&self, _env: &mut QuestEnv, _state: &mut QuestState, _zone_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_loot_item(&self, _env: &mut QuestEnv, _state: &mut QuestState, _item_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_item_use(&self, _env: &mut QuestEnv, _state: &mut QuestState, _item_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_attack(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_enter_world(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_level_up(&self, _env: &mut QuestEnv, _state: &mut QuestState, _new_level: u8) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_die(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_can_act(&self, _env: &QuestEnv, _state: &QuestState) -> bool {
        true
    }

    fn on_pass_flying_ring(&self, _env: &mut QuestEnv, _state: &mut QuestState, _ring_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_invisible_timer_end(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_atreian_passport(&self, _env: &mut QuestEnv, _state: &mut QuestState) -> HandlerResult {
        HandlerResult::Unknown
    }

    fn on_equip_item(&self, _env: &mut QuestEnv, _state: &mut QuestState, _item_id: u32) -> HandlerResult {
        HandlerResult::Unknown
    }
}
