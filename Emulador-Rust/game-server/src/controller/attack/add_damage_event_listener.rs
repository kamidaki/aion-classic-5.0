//! Listener de Evento de Dano (AddDamageEventListener - Padrão Java Aion Classic 2.8 / 4.5)

use super::add_damage_event::AddDamageEvent;

pub trait AddDamageEventListener: Send + Sync {
    fn on_add_damage(&self, event: &AddDamageEvent);
}
