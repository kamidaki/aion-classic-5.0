//! Pacote SM_L2AUTH_LOGIN_CHECK

#[derive(Debug, Clone)]
pub struct SmL2AuthLoginCheck {
    pub success: bool,
    pub account_name: String,
}
