//! Tipos de armas do Aion Classic (4.5 / 2.8).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum WeaponType {
    // Armas Clássicas de 1 Mão
    Dagger,
    Sword1H,
    Mace,
    // Armas Clássicas de 2 Mãos
    Sword2H,   // Greatsword
    Polearm,
    Bow,
    Staff,
    Orb,
    Book,      // Spellbook
    // Ferramenta de Coleta
    Tool,
}

impl WeaponType {
    pub fn is_two_handed(&self) -> bool {
        matches!(
            self,
            Self::Sword2H
                | Self::Polearm
                | Self::Bow
                | Self::Staff
                | Self::Orb
                | Self::Book
        )
    }

    pub fn from_xml_str(s: &str) -> Option<Self> {
        match s.trim().to_lowercase().as_str() {
            "1h_dagger" | "dagger" => Some(Self::Dagger),
            "1h_sword" | "sword_1h" | "sword" => Some(Self::Sword1H),
            "1h_mace" | "mace" | "mace_1h" => Some(Self::Mace),
            "2h_sword" | "greatsword" | "sword_2h" => Some(Self::Sword2H),
            "2h_polearm" | "polearm" => Some(Self::Polearm),
            "2h_bow" | "bow" => Some(Self::Bow),
            "2h_staff" | "staff" => Some(Self::Staff),
            "2h_orb" | "orb" => Some(Self::Orb),
            "2h_book" | "book" | "spellbook" => Some(Self::Book),
            "1h_tool" | "tool" => Some(Self::Tool),
            _ => None,
        }
    }
}
