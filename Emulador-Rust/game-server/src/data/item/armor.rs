//! Tipos de armadura do Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ArmorType {
    Robe,
    Leather,
    Chain,
    Plate,
    Shield,
}

impl ArmorType {
    pub fn from_xml_str(s: &str) -> Option<Self> {
        match s.trim().to_lowercase().as_str() {
            "robe" | "clothes" => Some(Self::Robe),
            "leather" => Some(Self::Leather),
            "chain" => Some(Self::Chain),
            "plate" => Some(Self::Plate),
            "shield" => Some(Self::Shield),
            _ => None,
        }
    }
}
