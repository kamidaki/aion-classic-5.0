//! Anúncios Globais do Servidor (Announcement - Padrão Java Aion Classic 2.8 / 4.5)

use crate::model::race::Race;

#[derive(Debug, Clone)]
pub struct Announcement {
    pub id: u32,
    pub message: String,
    pub target_race: Option<Race>,
    pub interval_seconds: u32,
    pub is_active: bool,
}

impl Announcement {
    pub fn new(id: u32, message: &str, target_race: Option<Race>, interval: u32) -> Self {
        Self {
            id,
            message: message.to_string(),
            target_race,
            interval_seconds: interval,
            is_active: true,
        }
    }
}
