//! Handler de Tiak Research Center (Masmorra PvPvE do Classic 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::instance::handlers::instance_handler::InstanceHandler;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

#[derive(Debug, Clone, Default)]
pub struct TiakResearchCenterHandler {
    pub elyos_points: i32,
    pub asmodian_points: i32,
    pub generators_captured: u32,
    pub stage: StageType,
}

impl TiakResearchCenterHandler {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn capture_generator(&mut self, is_elyos: bool) {
        self.generators_captured += 1;
        if is_elyos {
            self.elyos_points += 500;
        } else {
            self.asmodian_points += 500;
        }
    }
}

impl InstanceHandler for TiakResearchCenterHandler {
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

    fn on_die_player(&mut self, _player: &Character, _instance: &mut WorldMapInstance) -> bool {
        false
    }

    fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance) {
        let pts = if npc.max_hp > 100_000 { 1000 } else { 150 };
        instance.score.add_kill(npc.max_hp > 100_000, pts);
    }

    fn on_dialog(&mut self, _player_id: u32, _npc_id: u32, _dialog_id: u32, _instance: &mut WorldMapInstance) {}

    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance) {
        self.stage = stage;
        instance.stage = stage;
    }

    fn do_reward(&self, _player: &Character) -> InstanceReward {
        let mut reward = InstanceReward::new();
        reward.abyss_points = 4_000;
        reward.glory_points = 50;
        reward.add_item(186000040, 1); // Medalha de Mithril/Ceramium
        reward
    }

    fn check_distance(&self, player: &Character, npc: &Entity) -> bool {
        player.location().distance(npc.location()) <= 50.0
    }
}
