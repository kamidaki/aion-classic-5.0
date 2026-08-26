//! Identificadores e Nomes Canônicos de IA (AIName / AiNames - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum AIName {
    Npc,
    Monster,
    Aggressive,
    Guard,
    Boss,
    Trap,
    Servant,
    Totem,
    Homing,
    Kisk,
    Chest,
    Artifact,
    SiegeWeapon,
    Portal,
    Postbox,
    Custom(String),
}

impl AIName {
    pub fn from_str(name: &str) -> Self {
        match name.to_ascii_lowercase().as_str() {
            "npc" => Self::Npc,
            "monster" => Self::Monster,
            "aggressive" | "aggressive_monster" => Self::Aggressive,
            "guard" | "abyss_guard" => Self::Guard,
            "boss" | "boss_monster" => Self::Boss,
            "trap" => Self::Trap,
            "servant" => Self::Servant,
            "totem" => Self::Totem,
            "homing" => Self::Homing,
            "kisk" => Self::Kisk,
            "chest" => Self::Chest,
            "artifact" => Self::Artifact,
            "siege_weapon" => Self::SiegeWeapon,
            "portal" => Self::Portal,
            "postbox" => Self::Postbox,
            other => Self::Custom(other.to_string()),
        }
    }

    pub fn as_str(&self) -> &str {
        match self {
            Self::Npc => "npc",
            Self::Monster => "monster",
            Self::Aggressive => "aggressive",
            Self::Guard => "guard",
            Self::Boss => "boss",
            Self::Trap => "trap",
            Self::Servant => "servant",
            Self::Totem => "totem",
            Self::Homing => "homing",
            Self::Kisk => "kisk",
            Self::Chest => "chest",
            Self::Artifact => "artifact",
            Self::SiegeWeapon => "siege_weapon",
            Self::Portal => "portal",
            Self::Postbox => "postbox",
            Self::Custom(s) => s.as_str(),
        }
    }
}
