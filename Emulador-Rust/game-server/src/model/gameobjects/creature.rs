//! Criaturas com Atributos de Vida e Combate (Creature - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::visible_object::VisibleObject;
use crate::model::race::Race;
use crate::model::tribe_class::TribeClass;

#[derive(Debug, Clone)]
pub struct Creature {
    pub visible: VisibleObject,
    pub level: u16,
    pub race: Race,
    pub tribe: TribeClass,
    pub current_hp: i32,
    pub max_hp: i32,
    pub current_mp: i32,
    pub max_mp: i32,
    pub move_speed: f32,
    pub is_dead: bool,
}

impl Creature {
    pub fn new(object_id: u32, name: &str, pos: Coord, world_id: u32, instance_id: u32, level: u16, hp: i32, mp: i32) -> Self {
        Self {
            visible: VisibleObject::new(object_id, name, pos, world_id, instance_id),
            level,
            race: Race::None,
            tribe: TribeClass::General,
            current_hp: hp,
            max_hp: hp,
            current_mp: mp,
            max_mp: mp,
            move_speed: 6.0,
            is_dead: false,
        }
    }

    pub fn apply_damage(&mut self, damage: i32) -> i32 {
        self.current_hp = (self.current_hp - damage).max(0);
        if self.current_hp == 0 {
            self.is_dead = true;
        }
        damage
    }

    pub fn heal_hp(&mut self, amount: i32) {
        if !self.is_dead {
            self.current_hp = (self.current_hp + amount).min(self.max_hp);
        }
    }
}
