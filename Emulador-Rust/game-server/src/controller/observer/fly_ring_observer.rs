//! Observer de Anéis de Voo (FlyRingObserver - Padrão Java Aion Classic 2.8 / 4.5)

use super::action_observer::ActionObserver;
use super::observer_type::ObserverType;

#[derive(Debug, Clone)]
pub struct FlyRingObserver {
    pub ring_id: u32,
    pub boost_speed: f32,
}

impl FlyRingObserver {
    pub fn new(ring_id: u32, boost_speed: f32) -> Self {
        Self {
            ring_id,
            boost_speed,
        }
    }
}

impl ActionObserver for FlyRingObserver {
    fn get_observer_type(&self) -> ObserverType {
        ObserverType::FlyRing
    }

    fn on_pass_ring(&self, ring_id: u32) {
        if ring_id == self.ring_id {
            println!("[FLY_RING] Passou pelo anel de voo #{} com boost {:.1}x", ring_id, self.boost_speed);
        }
    }
}
