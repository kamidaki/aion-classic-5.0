//! Tipos de acessórios e itens especiais do Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum AccessoryType {
    Helmet,
    Earring,
    Ring,
    Necklace,
    Belt,
    Wings,
    Plume,
    Bracelet,
}

impl AccessoryType {
    pub fn from_xml_str(s: &str) -> Option<Self> {
        match s.trim().to_lowercase().as_str() {
            "head" | "helmet" => Some(Self::Helmet),
            "right_or_left_ear" | "ear" | "earring" => Some(Self::Earring),
            "right_or_left_finger" | "finger" | "ring" => Some(Self::Ring),
            "neck" | "necklace" => Some(Self::Necklace),
            "waist" | "belt" => Some(Self::Belt),
            "wing" | "wings" => Some(Self::Wings),
            "plume" => Some(Self::Plume),
            "bracelet" => Some(Self::Bracelet),
            _ => None,
        }
    }
}
