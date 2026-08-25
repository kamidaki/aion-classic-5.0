//! Facções de Monstros e Tribos (TribeClass - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum TribeClass {
    #[default]
    General,
    Guard,
    GuardDark,
    GuardDragon,
    Monster,
    Dragon,
    AbyssGuard,
    Protector,
    Undead,
    Lycan,
    Krall,
    AggressiveMonster,
    Friendly,
    Pet,
    Servant,
    Kisk,
    Neutral,
}

impl TribeClass {
    pub fn is_guard(&self) -> bool {
        matches!(self, Self::Guard | Self::GuardDark | Self::GuardDragon | Self::AbyssGuard)
    }

    pub fn is_hostile_to(&self, other: &TribeClass) -> bool {
        match (self, other) {
            (Self::Guard, Self::GuardDark) | (Self::GuardDark, Self::Guard) => true,
            (Self::Guard, Self::Dragon) | (Self::Dragon, Self::Guard) => true,
            (Self::GuardDark, Self::Dragon) | (Self::Dragon, Self::GuardDark) => true,
            (Self::AggressiveMonster, _) => true,
            _ => false,
        }
    }
}
