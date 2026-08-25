use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct NetworkConfig {
    #[serde(default = "default_bind")]
    pub bind_address: String,
    #[serde(default = "default_client_port")]
    pub client_port: u16,
    #[serde(default = "default_hq_port")]
    pub hq_port: u16,
    #[serde(default = "default_sts_port")]
    pub sts_port: u16,
    #[serde(default = "default_gameserver_port")]
    pub gameserver_port: u16,
    #[serde(default = "default_announce_ip")]
    pub announce_game_server_ip: String,
    #[serde(default = "default_announce_port")]
    pub announce_game_server_port: u16,
}

fn default_bind() -> String {
    "0.0.0.0".to_string()
}
fn default_client_port() -> u16 {
    2106
}
fn default_hq_port() -> u16 {
    13001
}
fn default_sts_port() -> u16 {
    6600
}
fn default_gameserver_port() -> u16 {
    9014
}
fn default_announce_ip() -> String {
    "127.0.0.1".to_string()
}
fn default_announce_port() -> u16 {
    7777
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            bind_address: default_bind(),
            client_port: default_client_port(),
            hq_port: default_hq_port(),
            sts_port: default_sts_port(),
            gameserver_port: default_gameserver_port(),
            announce_game_server_ip: default_announce_ip(),
            announce_game_server_port: default_announce_port(),
        }
    }
}
