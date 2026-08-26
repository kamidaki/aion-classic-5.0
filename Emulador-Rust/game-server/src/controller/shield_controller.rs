//! Controlador de Escudos de Fortalezas e Artefatos (ShieldController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct ShieldController {
    pub visible: VisibleObjectController,
    pub fortress_id: u32,
    pub radius: f32,
    pub is_shield_active: bool,
    pub shield_hp: i32,
    pub max_shield_hp: i32,
}

impl ShieldController {
    pub fn new(
        object_id: u32,
        fortress_id: u32,
        map_id: u32,
        position: Coord,
        radius: f32,
        max_shield_hp: i32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, 0),
            fortress_id,
            radius,
            is_shield_active: true,
            shield_hp: max_shield_hp,
            max_shield_hp,
        }
    }

    pub fn absorb_damage(&mut self, damage: i32) -> i32 {
        if !self.is_shield_active || self.shield_hp <= 0 {
            return damage;
        }

        let absorbed = damage.min(self.shield_hp);
        self.shield_hp -= absorbed;
        if self.shield_hp <= 0 {
            self.is_shield_active = false;
        }
        damage - absorbed
    }
}
