//! Interface Canônica de Comportamento de Instâncias (InstanceHandler - Padrão Java Aion Classic 2.8 / 4.5)

use crate::character::Character;
use crate::entity::Entity;
use crate::instance::models::instance_reward::InstanceReward;
use crate::instance::models::stage_type::StageType;
use crate::instance::models::world_instance::WorldMapInstance;

pub trait InstanceHandler: Send + Sync {
    fn on_instance_create(&mut self, instance: &mut WorldMapInstance);
    fn on_instance_destroy(&mut self, instance: &mut WorldMapInstance);
    fn on_player_login(&mut self, player: &Character, instance: &mut WorldMapInstance);
    fn on_player_logout(&mut self, player_id: u32, instance: &mut WorldMapInstance);
    fn on_enter_instance(&mut self, player: &Character, instance: &mut WorldMapInstance);
    fn on_leave_instance(&mut self, player_id: u32, instance: &mut WorldMapInstance);
    fn on_open_door(&mut self, player_id: u32, door_id: u32, instance: &mut WorldMapInstance);
    fn on_die_player(&mut self, player: &Character, instance: &mut WorldMapInstance) -> bool;
    fn on_die_npc(&mut self, npc: &Entity, instance: &mut WorldMapInstance);
    fn on_dialog(&mut self, player_id: u32, npc_id: u32, dialog_id: u32, instance: &mut WorldMapInstance);
    fn on_change_stage(&mut self, stage: StageType, instance: &mut WorldMapInstance);
    fn do_reward(&self, player: &Character) -> InstanceReward;
    fn check_distance(&self, player: &Character, npc: &Entity) -> bool;
}
