//! Restrições de uso de itens no Aion Classic (4.5 / 2.8).
//! Contém todas as 16 classes oficiais do Aion Classic (0..15).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct PlayerClassMask(pub u32);

impl PlayerClassMask {
    // Classes Base Tradicionais
    pub const WARRIOR: Self = Self(1 << 0);
    pub const SCOUT: Self = Self(1 << 3);
    pub const MAGE: Self = Self(1 << 6);
    pub const PRIEST: Self = Self(1 << 9);

    // Classes Especializadas Tradicionais
    pub const GLADIATOR: Self = Self(1 << 1);
    pub const TEMPLAR: Self = Self(1 << 2);
    pub const ASSASSIN: Self = Self(1 << 4);
    pub const RANGER: Self = Self(1 << 5);
    pub const SORCERER: Self = Self(1 << 7);
    pub const SPIRITMASTER: Self = Self(1 << 8);
    pub const CLERIC: Self = Self(1 << 10);
    pub const CHANTER: Self = Self(1 << 11);

    // Novas Classes Clássicas (Telos / Classic 2.5 / 2.8 / 4.5)
    pub const MONK: Self = Self(1 << 12);           // Soldier / Monk (Base de Telos)
    pub const THUNDERER: Self = Self(1 << 13);      // Revenant / Executor (Chainblade)
    pub const MARTIAL_ARTIST: Self = Self(1 << 14); // Lumines / Luminess / Painter (Base)
    pub const BATTLE_MASTER: Self = Self(1 << 15);  // Brawler / Phoenix / Vanguard (Especializada)

    // Máscara total de classes (0..15)
    pub const ALL: Self = Self(0xFFFF);

    #[inline]
    pub fn allows(&self, class_id: u8) -> bool {
        if self.0 == 0 || self.0 == Self::ALL.0 {
            return true;
        }
        match class_id {
            0 => self.0 & (Self::WARRIOR.0 | Self::GLADIATOR.0 | Self::TEMPLAR.0) != 0,
            1 => self.0 & Self::GLADIATOR.0 != 0,
            2 => self.0 & Self::TEMPLAR.0 != 0,
            3 => self.0 & (Self::SCOUT.0 | Self::ASSASSIN.0 | Self::RANGER.0) != 0,
            4 => self.0 & Self::ASSASSIN.0 != 0,
            5 => self.0 & Self::RANGER.0 != 0,
            6 => self.0 & (Self::MAGE.0 | Self::SORCERER.0 | Self::SPIRITMASTER.0) != 0,
            7 => self.0 & Self::SORCERER.0 != 0,
            8 => self.0 & Self::SPIRITMASTER.0 != 0,
            9 => self.0 & (Self::PRIEST.0 | Self::CLERIC.0 | Self::CHANTER.0) != 0,
            10 => self.0 & Self::CLERIC.0 != 0,
            11 => self.0 & Self::CHANTER.0 != 0,
            12 => self.0 & (Self::MONK.0 | Self::THUNDERER.0) != 0,
            13 => self.0 & Self::THUNDERER.0 != 0,
            14 => self.0 & (Self::MARTIAL_ARTIST.0 | Self::BATTLE_MASTER.0) != 0,
            15 => self.0 & Self::BATTLE_MASTER.0 != 0,
            _ => false,
        }
    }

    pub fn is_starting_class(class_id: u8) -> bool {
        matches!(class_id, 0 | 3 | 6 | 9 | 12 | 14)
    }

    pub fn get_starting_class_for(class_id: u8) -> u8 {
        match class_id {
            1 | 2 => 0,   // Gladiator / Templar -> Warrior
            4 | 5 => 3,   // Assassin / Ranger -> Scout
            7 | 8 => 6,   // Sorcerer / Spiritmaster -> Mage
            10 | 11 => 9, // Cleric / Chanter -> Priest
            13 => 12,     // Thunderer (Revenant) -> Monk
            15 => 14,     // Battle Master (Brawler / Phoenix) -> Martial Artist (Lumines)
            _ => class_id,
        }
    }

    pub fn class_code_name(class_id: u8) -> &'static str {
        match class_id {
            0 => "WARRIOR",
            1 => "GLADIATOR",
            2 => "TEMPLAR",
            3 => "SCOUT",
            4 => "ASSASSIN",
            5 => "RANGER",
            6 => "MAGE",
            7 => "SORCERER",
            8 => "SPIRIT_MASTER",
            9 => "PRIEST",
            10 => "CLERIC",
            11 => "CHANTER",
            12 => "MONK",
            13 => "THUNDERER",
            14 => "MARTIAL_ARTIST",
            15 => "BATTLE_MASTER",
            _ => "WARRIOR",
        }
    }

    pub fn class_display_name(class_id: u8) -> &'static str {
        match class_id {
            0 => "Warrior",
            1 => "Gladiator",
            2 => "Templar",
            3 => "Scout",
            4 => "Assassin",
            5 => "Ranger",
            6 => "Mage",
            7 => "Sorcerer",
            8 => "Spiritmaster",
            9 => "Priest",
            10 => "Cleric",
            11 => "Chanter",
            12 => "Monk (Soldier)",
            13 => "Revenant (Thunderer / Executor)",
            14 => "Lumines (Martial Artist / Painter)",
            15 => "Brawler (Battle Master / Phoenix)",
            _ => "Warrior",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum RacePermitted {
    #[default]
    All = 0,
    Elyos = 1,
    Asmodian = 2,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum GenderPermitted {
    #[default]
    All = 0,
    Male = 1,
    Female = 2,
}

#[derive(Debug, Clone, Default)]
pub struct ItemRestrictions {
    pub min_level: u8,
    pub max_level: u8,
    pub class_mask: PlayerClassMask,
    pub race: RacePermitted,
    pub gender: GenderPermitted,
    pub soul_bind: bool,
    pub can_exchange: bool,
    pub can_sell_to_npc: bool,
    pub can_deposit_character_warehouse: bool,
    pub can_deposit_account_warehouse: bool,
    pub can_deposit_guild_warehouse: bool,
    pub breakable: bool,
}
