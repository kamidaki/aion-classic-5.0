//! Pacotes do Cliente para Loja Quna e BattlePass (CM_SHOP / CM_BATTLEPASS - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmInGameShopInfo {
    pub category_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmQunaShopInfo {
    pub subcategory_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmBattlePassReward {
    pub pass_id: u32,
    pub level: u32,
    pub is_premium: bool,
}

#[derive(Debug, Clone)]
pub struct CmBlackCloudMail {
    pub mail_id: u32,
}
