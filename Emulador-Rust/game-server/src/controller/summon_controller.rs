//! Controlador de Invocações de Combate / Summons (SummonController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::creature_controller::CreatureController;
use crate::controller::movement::SummonMoveController;
use crate::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SummonMode {
    #[default]
    Guard,
    Attack,
    Follow,
    Rest,
}

pub struct SummonController {
    pub creature: CreatureController,
    pub summon_move: SummonMoveController,
    pub master_id: u32,
    pub mode: SummonMode,
    pub target_id: Option<u32>,
}

impl SummonController {
    pub fn new(
        object_id: u32,
        master_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
    ) -> Self {
        Self {
            creature: CreatureController::new(
                object_id,
                map_id,
                position,
                heading,
                speed,
                max_hp,
                2000,
            ),
            summon_move: SummonMoveController::new(position, heading, speed),
            master_id,
            mode: SummonMode::Guard,
            target_id: None,
        }
    }

    pub fn set_mode(&mut self, mode: SummonMode) {
        self.mode = mode;
        if mode == SummonMode::Rest {
            self.summon_move.stop_moving();
        }
    }

    pub fn order_attack(&mut self, target_id: u32) {
        self.mode = SummonMode::Attack;
        self.target_id = Some(target_id);
    }
}
