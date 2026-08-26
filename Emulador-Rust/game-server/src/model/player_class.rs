//! Classes de Jogadores (PlayerClass - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum PlayerClass {
    #[default]
    Warrior,
    Gladiator,
    Templar,
    Scout,
    Assassin,
    Ranger,
    Mage,
    Sorcerer,
    SpiritMaster,
    Priest,
    Cleric,
    Chanter,
    // Classes do Aion Classic 4.5
    Luminess,
    Phoenix,
    Brawler,
    Monk,
}

impl PlayerClass {
    pub fn is_starting_class(&self) -> bool {
        matches!(
            self,
            Self::Warrior | Self::Scout | Self::Mage | Self::Priest
        )
    }

    pub fn get_starting_class(&self) -> Self {
        match self {
            Self::Warrior | Self::Gladiator | Self::Templar => Self::Warrior,
            Self::Scout | Self::Assassin | Self::Ranger => Self::Scout,
            Self::Mage | Self::Sorcerer | Self::SpiritMaster => Self::Mage,
            Self::Priest | Self::Cleric | Self::Chanter => Self::Priest,
            Self::Luminess | Self::Phoenix => Self::Mage,
            Self::Brawler | Self::Monk => Self::Warrior,
        }
    }

    pub fn id(&self) -> u8 {
        match self {
            Self::Warrior => 0,
            Self::Gladiator => 1,
            Self::Templar => 2,
            Self::Scout => 3,
            Self::Assassin => 4,
            Self::Ranger => 5,
            Self::Mage => 6,
            Self::Sorcerer => 7,
            Self::SpiritMaster => 8,
            Self::Priest => 9,
            Self::Cleric => 10,
            Self::Chanter => 11,
            Self::Luminess => 16,
            Self::Phoenix => 17,
            Self::Brawler => 18,
            Self::Monk => 19,
        }
    }

    pub fn from_id(id: u8) -> Self {
        match id {
            0 => Self::Warrior,
            1 => Self::Gladiator,
            2 => Self::Templar,
            3 => Self::Scout,
            4 => Self::Assassin,
            5 => Self::Ranger,
            6 => Self::Mage,
            7 => Self::Sorcerer,
            8 => Self::SpiritMaster,
            9 => Self::Priest,
            10 => Self::Cleric,
            11 => Self::Chanter,
            16 => Self::Luminess,
            17 => Self::Phoenix,
            18 => Self::Brawler,
            19 => Self::Monk,
            _ => Self::Warrior,
        }
    }
}
