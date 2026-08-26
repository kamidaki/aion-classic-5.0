//! Listener de Início de Movimento de Entidades (StartMovingListener - Padrão Java Aion Classic 2.8 / 4.5)

pub trait StartMovingListener: Send + Sync {
    fn on_start_moving(&self, entity_id: u32);
}
