//! Pacote SM_GUILD_INFO

#[derive(Debug, Clone)]
pub struct SmGuildInfo {
    pub guild_id: u32,
    pub name: String,
    pub level: u32,
}
