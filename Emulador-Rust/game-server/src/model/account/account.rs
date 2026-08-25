//! Modelos de Conta e Armazém de Conta (Account - Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum MembershipType {
    #[default]
    Normal,
    Premium,
    Vip,
    SielAura,
}

#[derive(Debug, Clone)]
pub struct AccountModel {
    pub id: u32,
    pub name: String,
    pub access_level: u8,
    pub membership: MembershipType,
    pub creation_time: Instant,
    pub last_login: Instant,
    pub characters_count: u8,
}

impl AccountModel {
    pub fn new(id: u32, name: &str, access_level: u8) -> Self {
        Self {
            id,
            name: name.to_string(),
            access_level,
            membership: MembershipType::SielAura,
            creation_time: Instant::now(),
            last_login: Instant::now(),
            characters_count: 0,
        }
    }
}
