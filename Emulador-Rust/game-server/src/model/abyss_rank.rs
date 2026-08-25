//! Ranks e Resultados do Abyss (AbyssRankingResult / AbyssRankType - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::player_class::PlayerClass;
use crate::model::race::Race;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AbyssRankType {
    #[default]
    SoldierRank9,
    SoldierRank8,
    SoldierRank7,
    SoldierRank6,
    SoldierRank5,
    SoldierRank4,
    SoldierRank3,
    SoldierRank2,
    SoldierRank1,
    Officer1Star,
    Officer2Star,
    Officer3Star,
    Officer4Star,
    Officer5Star,
    General,
    GreatGeneral,
    Commander,
    SupremeCommander,
}

impl AbyssRankType {
    pub fn id(&self) -> u8 {
        match self {
            Self::SoldierRank9 => 1,
            Self::SoldierRank8 => 2,
            Self::SoldierRank7 => 3,
            Self::SoldierRank6 => 4,
            Self::SoldierRank5 => 5,
            Self::SoldierRank4 => 6,
            Self::SoldierRank3 => 7,
            Self::SoldierRank2 => 8,
            Self::SoldierRank1 => 9,
            Self::Officer1Star => 10,
            Self::Officer2Star => 11,
            Self::Officer3Star => 12,
            Self::Officer4Star => 13,
            Self::Officer5Star => 14,
            Self::General => 15,
            Self::GreatGeneral => 16,
            Self::Commander => 17,
            Self::SupremeCommander => 18,
        }
    }
}

#[derive(Debug, Clone)]
pub struct AbyssRankingResult {
    pub player_id: u32,
    pub player_name: String,
    pub player_class: PlayerClass,
    pub race: Race,
    pub rank: AbyssRankType,
    pub ap: u32,
    pub gp: u32,
    pub standing: u32,
}
