//! Handler de Dredgion PvPvE (Baranath, Chantra e Terath Dredgion - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

#[derive(Debug, Clone, Default)]
pub struct DredgionInstanceHandler {
    pub elyos_score: i32,
    pub asmodian_score: i32,
    pub surkanas_destroyed: u32,
    pub captain_killed: bool,
    pub stage: StageType,
}

impl DredgionInstanceHandler {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn add_surkana_points(&mut self, is_elyos: bool, points: i32) {
        self.surkanas_destroyed += 1;
        if is_elyos {
            self.elyos_score += points;
        } else {
            self.asmodian_score += points;
        }
    }

    pub fn add_pvp_kill(&mut self, killer_is_elyos: bool) {
        if killer_is_elyos {
            self.elyos_score += 60;
            self.asmodian_score = self.asmodian_score.saturating_sub(60);
        } else {
            self.asmodian_score += 60;
            self.elyos_score = self.elyos_score.saturating_sub(60);
        }
    }
}

impl InstanceHandler for DredgionInstanceHandler {
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
    }

    fn on_leave_instance(&mut self, player_id: u32, instance: &mut WorldMapInstance) {
        instance.remove_player(player_id);
    }

    fn on_open_door(&mut self, _player_id: u32, door_id: u32, instance: &mut WorldMapInstance) {
        if let Some(gate) = instance.gates.get_mut(&door_id) {
            gate.is_open = true;
        }
    }

    fn on_die_player(&mut self, _player: &Character, _instance: &mut WorldMapInstance) -> bool {
        // Redução e transferência de pontuação em morte PvP
        false
    }

    fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance) {
        // Checa se é o Capitão Dredgion
        if npc.max_hp >= 500_000 {
            self.captain_killed = true;
            self.stage = StageType::Boss;
            instance.stage = StageType::Boss;
        }
    }

    fn on_dialog(&mut self, _player_id: u32, _npc_id: u32, _dialog_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        self.stage = stage;
        instance.stage = stage;
    }

    fn do_reward(&self, _player: &Character) -> InstanceReward {
        let mut reward = InstanceReward::new();
        let is_winner = self.elyos_score > self.asmodian_score;
        if is_winner {
            reward.abyss_points = 5_000;
            reward.glory_points = 100;
            reward.add_item(186000030, 2); // Medalhas
        } else {
            reward.abyss_points = 2_500;
            reward.glory_points = 30;
            reward.add_item(186000030, 1);
        }
        reward
    }

    fn check_distance(&self, player: &Character, npc: &Entity) -> bool {
        player.location().distance(npc.location()) <= 60.0
    }
}
