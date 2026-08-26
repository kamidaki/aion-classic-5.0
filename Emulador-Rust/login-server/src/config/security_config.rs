use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct SecurityConfig {
    #[serde(default = "default_true")]
    pub enable_rate_limit: bool,
    #[serde(default = "default_max_attempts")]
    pub max_attempts_per_minute: u32,
    #[serde(default = "default_ban_minutes")]
    pub temp_ban_minutes: u32,
}

fn default_true() -> bool {
    true
}
fn default_max_attempts() -> u32 {
    15
}
fn default_ban_minutes() -> u32 {
    15
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            enable_rate_limit: true,
            max_attempts_per_minute: default_max_attempts(),
            temp_ban_minutes: default_ban_minutes(),
        }
    }
}
