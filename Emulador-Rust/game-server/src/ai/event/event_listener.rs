//! Listener de Eventos de IA (AIEventListener - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::event::event_type::AIEventType;

pub trait AIEventListener: Send + Sync {
    fn on_ai_event(&mut self, event: AIEventType);
}
