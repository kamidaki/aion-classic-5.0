//! Interface de Motores de Jogo (GameEngine - Padrão Java Aion Classic 2.8 / 4.5)

pub trait GameEngine: Send + Sync {
    fn load(&mut self) -> Result<(), &'static str>;
    fn shutdown(&mut self);
}
