//! Controlador de Armas de Cerco e Tanques (SiegeWeaponController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::creature_controller::CreatureController;
use crate::controller::movement::SiegeWeaponMoveController;
use crate::engine::Coord;

pub struct SiegeWeaponController {
    pub creature: CreatureController,
    pub siege_move: SiegeWeaponMoveController,
    pub pilot_id: Option<u32>,
    pub siege_power: i32,
}

impl SiegeWeaponController {
    pub fn new(
        object_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
        siege_power: i32,
    ) -> Self {
        Self {
            creature: CreatureController::new(
                object_id,
                map_id,
                position,
                heading,
                speed,
                max_hp,
                0,
            ),
            siege_move: SiegeWeaponMoveController::new(position, heading, speed),
            pilot_id: None,
            siege_power,
        }
    }

    pub fn board_pilot(&mut self, pilot_id: u32) -> bool {
        if self.pilot_id.is_none() {
            self.pilot_id = Some(pilot_id);
            true
        } else {
            false
        }
    }

    pub fn unboard_pilot(&mut self) -> Option<u32> {
        self.pilot_id.take()
    }
}
