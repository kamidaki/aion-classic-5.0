//! Controlador Base de Criaturas (CreatureController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::attack::{AggroList, AttackResult, AttackStatus, AttackUtil};
use crate::controller::effect::EffectController;
use crate::controller::movement::CreatureMoveController;
use crate::controller::observe_controller::ObserveController;
use crate::controller::visible_object_controller::VisibleObjectController;
use crate::engine::Coord;

pub struct CreatureController {
    pub visible: VisibleObjectController,
    pub movement: CreatureMoveController,
    pub effect: EffectController,
    pub aggro_list: AggroList,
    pub observers: ObserveController,
    pub is_dead: bool,
    pub hp: i32,
    pub max_hp: i32,
    pub mp: i32,
    pub max_mp: i32,
}

impl CreatureController {
    pub fn new(
        object_id: u32,
        map_id: u32,
        position: Coord,
        heading: u8,
        speed: f32,
        max_hp: i32,
        max_mp: i32,
    ) -> Self {
        Self {
            visible: VisibleObjectController::new(object_id, map_id, position, heading),
            movement: CreatureMoveController::new(position, heading, speed),
            effect: EffectController::new(),
            aggro_list: AggroList::new(),
            observers: ObserveController::new(),
            is_dead: false,
            hp: max_hp,
            max_hp,
            mp: max_mp,
            max_mp,
        }
    }

    pub fn on_attack(&mut self, target_id: u32, base_damage: i32) -> AttackResult {
        self.observers.notify_attack();
        self.aggro_list.add_damage(target_id, base_damage);
        AttackResult::new(base_damage, AttackStatus::NormalHit)
    }

    pub fn on_attacked(&mut self, attacker_id: u32, damage: i32) -> AttackResult {
        self.observers.notify_attacked();
        let (dmg_after_shield, absorbed) = self.observers.absorb_damage_shields(damage);
        self.aggro_list.add_hate(attacker_id, dmg_after_shield);

        self.hp = self.hp.saturating_sub(dmg_after_shield);
        if self.hp <= 0 && !self.is_dead {
            self.on_die(attacker_id);
        }

        AttackResult::new(dmg_after_shield, AttackStatus::NormalHit).with_shield(absorbed)
    }

    pub fn on_die(&mut self, _killer_id: u32) {
        self.is_dead = true;
        self.hp = 0;
        self.movement.stop_moving();
        self.observers.notify_die();
    }

    pub fn on_respawn(&mut self, spawn_pos: Coord) {
        self.is_dead = false;
        self.hp = self.max_hp;
        self.mp = self.max_mp;
        self.movement.position = spawn_pos;
        self.aggro_list.clear();
    }

    pub fn on_restore(&mut self, hp_amount: i32, mp_amount: i32) {
        if !self.is_dead {
            self.hp = (self.hp + hp_amount).min(self.max_hp);
            self.mp = (self.mp + mp_amount).min(self.max_mp);
        }
    }
}
