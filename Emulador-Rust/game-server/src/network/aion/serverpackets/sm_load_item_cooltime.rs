//! Pacote SM_LOAD_ITEM_COOLTIME

#[derive(Debug, Clone)]
pub struct SmLoadItemCooltime {
    pub cooldowns: Vec<(u32, u32)>, // (item_id, remaining_ms)
}
