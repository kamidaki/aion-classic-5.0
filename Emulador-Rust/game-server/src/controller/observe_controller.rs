//! Gerenciador de Observadores de uma Entidade (ObserveController - Padrão Java Aion Classic 2.8 / 4.5)

use crate::controller::observer::{ActionObserver, AttackShieldObserver, ObserverType};
use crate::engine::Coord;
use std::sync::Arc;

#[derive(Default)]
pub struct ObserveController {
    observers: Vec<Arc<dyn ActionObserver>>,
    shield_observers: Vec<AttackShieldObserver>,
}

impl ObserveController {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn attach(&mut self, observer: Arc<dyn ActionObserver>) {
        self.observers.push(observer);
    }

    pub fn attach_shield(&mut self, shield: AttackShieldObserver) {
        self.shield_observers.push(shield);
    }

    pub fn notify_move(&self) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Move || obs.get_observer_type() == ObserverType::All {
                obs.on_move();
            }
        }
    }

    pub fn notify_attack(&self) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Attack || obs.get_observer_type() == ObserverType::All {
                obs.on_attack();
            }
        }
    }

    pub fn notify_attacked(&self) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Attacked || obs.get_observer_type() == ObserverType::All {
                obs.on_attacked();
            }
        }
    }

    pub fn notify_die(&self) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Die || obs.get_observer_type() == ObserverType::All {
                obs.on_die();
            }
        }
    }

    pub fn notify_item_use(&self, item_id: u32) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::ItemUse || obs.get_observer_type() == ObserverType::All {
                obs.on_item_use(item_id);
            }
        }
    }

    pub fn notify_dialog(&self, target_id: u32) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Dialog || obs.get_observer_type() == ObserverType::All {
                obs.on_dialog(target_id);
            }
        }
    }

    pub fn notify_collision(&self, pos: &Coord) {
        for obs in &self.observers {
            if obs.get_observer_type() == ObserverType::Collision || obs.get_observer_type() == ObserverType::All {
                obs.on_collision(pos);
            }
        }
    }

    pub fn absorb_damage_shields(&mut self, mut damage: i32) -> (i32, i32) {
        let mut total_absorbed = 0;
        for shield in &mut self.shield_observers {
            if damage <= 0 {
                break;
            }
            let (rem_dmg, abs) = shield.absorb_damage(damage);
            damage = rem_dmg;
            total_absorbed += abs;
        }
        self.shield_observers.retain(|s| !s.is_broken());
        (damage, total_absorbed)
    }

    pub fn clear(&mut self) {
        self.observers.clear();
        self.shield_observers.clear();
    }
}
