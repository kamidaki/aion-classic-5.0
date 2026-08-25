//! Pacotes do Servidor para Guarda-Roupa Classic (SM_USER_CLASSIC_WARDROBE_LOAD - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct SmUserClassicWardrobeLoad {
    pub player_id: u32,
    pub unlocked_slots: u32,
    pub active_skin_id: Option<u32>,
}
