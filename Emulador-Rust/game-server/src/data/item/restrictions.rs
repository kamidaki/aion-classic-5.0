//! Restrições de uso de itens (Classes, Raça, Gênero, Nível).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct PlayerClassMask(pub u32);

impl PlayerClassMask {
    pub const WARRIOR: Self = Self(1 << 0);
    pub const GLADIATOR: Self = Self(1 << 1);
    pub const TEMPLAR: Self = Self(1 << 2);
    pub const SCOUT: Self = Self(1 << 3);
    pub const ASSASSIN: Self = Self(1 << 4);
    pub const RANGER: Self = Self(1 << 5);
    pub const MAGE: Self = Self(1 << 6);
    pub const SORCERER: Self = Self(1 << 7);
    pub const SPIRITMASTER: Self = Self(1 << 8);
    pub const PRIEST: Self = Self(1 << 9);
    pub const CLERIC: Self = Self(1 << 10);
    pub const CHANTER: Self = Self(1 << 11);
    pub const GUNNER: Self = Self(1 << 12);
    pub const AETHERTECH: Self = Self(1 << 13);
    pub const SONGWEAVER: Self = Self(1 << 14);

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
            12 => self.0 & Self::GUNNER.0 != 0,
            13 => self.0 & Self::AETHERTECH.0 != 0,
            14 => self.0 & Self::SONGWEAVER.0 != 0,
            _ => true,
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
