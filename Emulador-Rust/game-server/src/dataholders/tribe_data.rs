//! TribeRelationsDataHolder - Relações de Hostilidade entre Facções e Tribos

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TribeRelation {
    Friendly,
    Neutral,
    Hostile,
}

#[derive(Debug, Clone, Default)]
pub struct TribeRelationsDataHolder;

impl TribeRelationsDataHolder {
    pub fn get_relation(tribe_a: &str, tribe_b: &str) -> TribeRelation {
        if tribe_a.eq_ignore_ascii_case(tribe_b) {
            return TribeRelation::Friendly;
        }

        let is_light_a = tribe_a.contains("LIGHT") || tribe_a.contains("ELYOS");
        let is_dark_a = tribe_a.contains("DARK") || tribe_a.contains("ASMODIAN");
        let is_balaur_a = tribe_a.contains("DRAGON") || tribe_a.contains("BALAUR");

        let is_light_b = tribe_b.contains("LIGHT") || tribe_b.contains("ELYOS");
        let is_dark_b = tribe_b.contains("DARK") || tribe_b.contains("ASMODIAN");
        let is_balaur_b = tribe_b.contains("DRAGON") || tribe_b.contains("BALAUR");

        if (is_light_a && is_light_b) || (is_dark_a && is_dark_b) {
            TribeRelation::Friendly
        } else if (is_light_a && is_dark_b) || (is_dark_a && is_light_b) || is_balaur_a || is_balaur_b {
            TribeRelation::Hostile
        } else if tribe_a.contains("MONSTER") || tribe_b.contains("MONSTER") {
            TribeRelation::Hostile
        } else {
            TribeRelation::Neutral
        }
    }
}
