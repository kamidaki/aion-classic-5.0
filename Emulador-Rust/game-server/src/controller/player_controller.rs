//! Controlador de Jogador (PlayerController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::attack::{KillList, PlayerAggroList};
use crate::controller::creature_controller::CreatureController;
use crate::controller::effect::PlayerEffectController;
use crate::controller::movement::PlayerMoveController;
use crate::engine::Coord;

pub struct PlayerController {
    pub creature: CreatureController,
    pub player_move: PlayerMoveController,
    pub player_effect: PlayerEffectController,
    pub player_aggro: PlayerAggroList,
    pub kill_list: KillList,
    pub dp: u32,
    pub max_dp: u32,
    pub fly_time: u32,
    pub max_fly_time: u32,
    pub is_in_pvp: bool,
}

impl PlayerController {
    pub fn new(
        player_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
        max_mp: i32,
        max_dp: u32,
        max_fly_time: u32,
    ) -> Self {
        Self {
            creature: CreatureController::new(
                player_id,
                map_id,
                position,
                heading,
                speed,
                max_hp,
                max_mp,
            ),
            player_move: PlayerMoveController::new(position, heading, speed),
            player_effect: PlayerEffectController::new(),
            player_aggro: PlayerAggroList::new(),
            kill_list: KillList::new(),
            dp: 0,
            max_dp,
            fly_time: max_fly_time,
            max_fly_time,
            is_in_pvp: false,
        }
    }

    pub fn on_enter_world(&mut self) {
        self.creature.visible.on_spawn();
    }

    pub fn on_leave_world(&mut self) {
        self.creature.visible.on_despawn();
        self.player_move.stop_moving();
    }

    pub fn add_dp(&mut self, amount: u32) {
        self.dp = (self.dp + amount).min(self.max_dp);
    }

    pub fn consume_dp(&mut self, amount: u32) -> bool {
        if self.dp >= amount {
            self.dp -= amount;
            true
        } else {
            false
        }
    }

    pub fn on_kill_player(&mut self, victim_id: u32) {
        self.kill_list.record_kill(victim_id);
    }

    pub fn drain_fly_time(&mut self, amount: u32) -> bool {
        if self.fly_time > amount {
            self.fly_time -= amount;
            true
        } else {
            self.fly_time = 0;
            self.player_move.stop_gliding();
            false
        }
    }

    pub fn restore_fly_time(&mut self, amount: u32) {
        self.fly_time = (self.fly_time + amount).min(self.max_fly_time);
    }
}
