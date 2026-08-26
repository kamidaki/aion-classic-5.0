//! Animações de Teleporte (TeleportAnimation - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum TeleportAnimation {
    #[default]
    None,
    JumpAnimation,
    FlyAnimation,
    BeamAnimation,
    StatueAnimation,
}

impl TeleportAnimation {
    pub fn id(&self) -> u8 {
        match self {
            Self::None => 0,
            Self::JumpAnimation => 1,
            Self::FlyAnimation => 2,
            Self::BeamAnimation => 3,
            Self::StatueAnimation => 4,
        }
    }
}
