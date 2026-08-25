//! Handler de Arenas PvP (Arena of Chaos e Arena of Discipline - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

#[derive(Debug, Clone, Default)]
pub struct ArenaInstanceHandler {
    // player_id -> score
    pub player_scores: HashMap<u32, i32>,
    pub current_round: u32,
    pub max_rounds: u32,
    pub stage: StageType,
}

impl ArenaInstanceHandler {
    pub fn new(max_rounds: u32) -> Self {
        Self {
            player_scores: HashMap::new(),
            current_round: 1,
            max_rounds,
            stage: StageType::Phase1,
        }
    }

    pub fn record_pvp_kill(&mut self, killer_id: u32, victim_id: u32) {
        *self.player_scores.entry(killer_id).or_insert(0) += 1000;
        let victim_score = self.player_scores.entry(victim_id).or_insert(0);
        *victim_score = victim_score.saturating_sub(300);
    }
}

impl InstanceHandler for ArenaInstanceHandler {
    fn on_instance_create(&mut self, instance: &mut WorldMapInstance) {
        self.stage = StageType::Phase1;
        instance.stage = StageType::Phase1;
    }

    fn on_instance_destroy(&mut self, _instance: &mut WorldMapInstance) {
        self.stage = StageType::Complete;
    }

    fn on_player_login(&mut self, _player: &Character, _instance: &mut WorldMapInstance) {}
    fn on_player_logout(&mut self, _player_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_enter_instance(&mut self, player: &Character, instance: &mut WorldMapInstance) {
        instance.add_player(player.id());
        self.player_scores.entry(player.id()).or_insert(0);
    }

    fn on_leave_instance(&mut self, player_id: u32, instance: &mut WorldMapInstance) {
        instance.remove_player(player_id);
    }

    fn on_open_door(&mut self, _player_id: u32, _door_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_die_player(&mut self, _player: &Character, _instance: &mut WorldMapInstance) -> bool {
        false
    }

    fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance) {
        let pts = if npc.max_hp > 50_000 { 500 } else { 100 };
        instance.score.add_kill(npc.max_hp > 50_000, pts);
    }

    fn on_dialog(&mut self, _player_id: u32, _npc_id: u32, _dialog_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        self.stage = stage;
        instance.stage = stage;
    }

    fn do_reward(&self, player: &Character) -> InstanceReward {
        let mut reward = InstanceReward::new();
        let score = self.player_scores.get(&player.id()).copied().unwrap_or(0);
        reward.abyss_points = (score / 2).max(500) as u32;
        reward.add_item(186000130, 3); // Courage Insignia
        reward
    }

    fn check_distance(&self, player: &Character, npc: &Entity) -> bool {
        player.location().distance(npc.location()) <= 50.0
    }
}
