//! Tipos de armas do Aion Classic.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum WeaponType {
    // Armas de 1 mão
    Dagger,
    Sword1H,
    Mace,
    Gun1H,
    // Armas de 2 mãos
    Sword2H,
    Polearm,
    Bow,
    Staff,
    Orb,
    Book,
    Cannon2H,
    Harp2H,
    Keyblade2H,
    // Outros
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
                | Self::Cannon2H
                | Self::Harp2H
                | Self::Keyblade2H
        )
    }

    pub fn from_xml_str(s: &str) -> Option<Self> {
        match s.trim().to_lowercase().as_str() {
            "1h_dagger" | "dagger" => Some(Self::Dagger),
            "1h_sword" | "sword_1h" | "sword" => Some(Self::Sword1H),
            "1h_mace" | "mace" | "mace_1h" => Some(Self::Mace),
            "1h_gun" | "gun" => Some(Self::Gun1H),
            "2h_sword" | "greatsword" | "sword_2h" => Some(Self::Sword2H),
            "2h_polearm" | "polearm" => Some(Self::Polearm),
            "2h_bow" | "bow" => Some(Self::Bow),
            "2h_staff" | "staff" => Some(Self::Staff),
            "2h_orb" | "orb" => Some(Self::Orb),
            "2h_book" | "book" | "spellbook" => Some(Self::Book),
            "2h_cannon" | "cannon" => Some(Self::Cannon2H),
            "2h_harp" | "harp" => Some(Self::Harp2H),
            "2h_keyblade" | "keyblade" => Some(Self::Keyblade2H),
            "1h_tool" | "tool" => Some(Self::Tool),
            _ => None,
        }
    }
}
