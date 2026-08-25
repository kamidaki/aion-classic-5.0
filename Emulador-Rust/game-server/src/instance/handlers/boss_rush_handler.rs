//! Handler de Masmorras Boss Rush / Raid (Padmarashka, Tahabata, Dark Poeta - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

#[derive(Debug, Clone, Default)]
pub struct BossRushInstanceHandler {
    pub main_boss_killed: bool,
    pub stage: StageType,
}

impl BossRushInstanceHandler {
    pub fn new() -> Self {
        Self::default()
    }
}

impl InstanceHandler for BossRushInstanceHandler {
    fn on_instance_create(&mut self, instance: &mut WorldMapInstance) {
        self.stage = StageType::Starting;
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
        if npc.max_hp > 1_000_000 {
            self.main_boss_killed = true;
            self.stage = StageType::Complete;
            instance.stage = StageType::Complete;
            instance.score.add_kill(true, 50_000);
        } else {
            instance.score.add_kill(false, 500);
        }
    }

    fn on_dialog(&mut self, _player_id: u32, _npc_id: u32, _dialog_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        self.stage = stage;
        instance.stage = stage;
    }

    fn do_reward(&self, _player: &Character) -> InstanceReward {
        let mut reward = InstanceReward::new();
        reward.abyss_points = 10_000;
        reward.kinah = 200_000;
        reward.add_item(186000030, 5); // Medalhas de Ouro/Platina
        reward
    }

    fn check_distance(&self, player: &Character, npc: &Entity) -> bool {
        player.location().distance(npc.location()) <= 80.0
    }
}
