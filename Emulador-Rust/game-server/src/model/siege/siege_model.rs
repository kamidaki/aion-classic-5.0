//! Modelos de Fortalezas e Sieges (SiegeRace / SiegeLocation - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::race::Race;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum SiegeRace {
    #[default]
    Elyos,
    Asmodians,
    Balaur,
}

impl From<Race> for SiegeRace {
    fn from(r: Race) -> Self {
        match r {
            Race::Elyos => Self::Elyos,
            Race::Asmodians => Self::Asmodians,
            _ => Self::Balaur,
        }
    }
}

#[derive(Debug, Clone)]
pub struct FortressLocationModel {
    pub location_id: u32,
    pub name: String,
    pub occupying_race: SiegeRace,
    pub occupying_legion_id: Option<u32>,
    pub is_vulnerable: bool,
}
