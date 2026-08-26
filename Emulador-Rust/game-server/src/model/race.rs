//! Raças e Facções (Race - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum Race {
    #[default]
    Elyos,
    Asmodians,
    Lycan,
    Krall,
    Dragon,
    Naga,
    Undead,
    Beast,
    Demihuman,
    Construct,
    Elemental,
    None,
}

impl Race {
    pub fn is_player_race(&self) -> bool {
        matches!(self, Self::Elyos | Self::Asmodians)
    }

    pub fn is_enemy(&self, other: &Race) -> bool {
        match (self, other) {
            (Self::Elyos, Self::Asmodians) | (Self::Asmodians, Self::Elyos) => true,
            (Self::Elyos, Self::Dragon) | (Self::Asmodians, Self::Dragon) => true,
            (Self::Dragon, Self::Elyos) | (Self::Dragon, Self::Asmodians) => true,
            _ => false,
        }
    }

    pub fn id(&self) -> u8 {
        match self {
            Self::Elyos => 0,
            Self::Asmodians => 1,
            Self::Lycan => 2,
            Self::Krall => 3,
            Self::Dragon => 4,
            Self::Naga => 5,
            _ => 15,
        }
    }

    pub fn from_id(id: u8) -> Self {
        match id {
            0 => Self::Elyos,
            1 => Self::Asmodians,
            2 => Self::Lycan,
            3 => Self::Krall,
            4 => Self::Dragon,
            5 => Self::Naga,
            _ => Self::None,
        }
    }
}
