//! Pacote CM_GUILD

#[derive(Debug, Clone)]
pub struct CmGuild {
    pub action_type: u8,
    pub guild_name: Option<String>,
}
