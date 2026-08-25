//! Handler Geral Padrão de Masmorras (GeneralInstanceHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

#[derive(Debug, Clone, Default)]
pub struct GeneralInstanceHandler {
    pub map_id: u32,
    pub instance_id: u32,
    pub stage: StageType,
}

impl GeneralInstanceHandler {
    pub fn new(map_id: u32) -> Self {
        Self {
            map_id,
            instance_id: 0,
            stage: StageType::Starting,
        }
    }
}

impl InstanceHandler for GeneralInstanceHandler {
    fn on_instance_create(&mut self, instance: &mut WorldMapInstance) {
        self.instance_id = instance.instance_id;
        self.map_id = instance.map_id;
        instance.stage = StageType::Starting;
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

    fn on_die_player(&mut self, _player: &Character, instance: &mut WorldMapInstance) -> bool {
        instance.score.record_death();
        false
    }

    fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance) {
        let is_boss = npc.max_hp > 50_000;
        let points = if is_boss { 5_000 } else { 200 };
        instance.score.add_kill(is_boss, points);
    }

    fn on_dialog(&mut self, _player_id: u32, _npc_id: u32, _dialog_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        self.stage = stage;
        instance.stage = stage;
    }

    fn do_reward(&self, _player: &Character) -> InstanceReward {
        let mut reward = InstanceReward::new();
        reward.abyss_points = 1500;
        reward.kinah = 50_000;
        reward
    }

    fn check_distance(&self, player: &Character, npc: &Entity) -> bool {
        player.location().distance(npc.location()) <= 50.0
    }
}
