//! Qualidade dos itens no Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub enum ItemQuality {
    #[default]
    Junk = 0,
    Common = 1,
    Rare = 2,
    Unique = 3,
    Epic = 4,
    Mythic = 5,
}

impl ItemQuality {
    pub fn from_xml_str(s: &str) -> Self {
        match s.trim().to_lowercase().as_str() {
            "junk" => Self::Junk,
            "common" => Self::Common,
            "rare" => Self::Rare,
            "unique" | "legend" => Self::Unique,
            "epic" => Self::Epic,
            "mythic" => Self::Mythic,
            _ => Self::Common,
        }
    }
}
