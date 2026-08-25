//! Portões e Portas Interativas de Masmorras (DungeonGate - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct DungeonGate {
    pub gate_id: u32,
    pub name: String,
    pub is_open: bool,
    pub key_item_id: Option<u32>,
}

impl DungeonGate {
    pub fn new(gate_id: u32, name: &str, key_item_id: Option<u32>) -> Self {
        Self {
            gate_id,
            name: name.to_string(),
            is_open: false,
            key_item_id,
        }
    }

    pub fn try_unlock(&mut self, player_items: &[u32]) -> bool {
        if let Some(key) = self.key_item_id {
            if player_items.contains(&key) {
                self.is_open = true;
                true
            } else {
                false
            }
        } else {
            self.is_open = true;
            true
        }
    }
}
