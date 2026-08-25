//! Slots de Equipamentos (ItemSlot - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum ItemSlot {
    #[default]
    MainHand,
    SubHand,
    Helmet,
    Torso,
    Glove,
    Boots,
    EarringLeft,
    EarringRight,
    RingLeft,
    RingRight,
    Necklace,
    Shoulders,
    Pants,
    Belt,
    Wings,
    Plume,
    Bracelet,
}

impl ItemSlot {
    pub fn id(&self) -> u32 {
        match self {
            Self::MainHand => 1,
            Self::SubHand => 2,
            Self::Helmet => 4,
            Self::Torso => 8,
            Self::Glove => 16,
            Self::Boots => 32,
            Self::EarringLeft => 64,
            Self::EarringRight => 128,
            Self::RingLeft => 256,
            Self::RingRight => 512,
            Self::Necklace => 1024,
            Self::Shoulders => 2048,
            Self::Pants => 4096,
            Self::Belt => 8192,
            Self::Wings => 16384,
            Self::Plume => 32768,
            Self::Bracelet => 65536,
        }
    }
}
