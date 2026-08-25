//! Serviço de Pedras de Mana (Manastones) e Godstones (ItemSocketService).

use crate::data::item::ItemTemplate;

#[derive(Debug, PartialEq, Eq)]
pub enum SocketError {
    NoAvailableSlots,
    InvalidManastone,
    SocketFailed,
    ItemNotSocketable,
}

#[derive(Debug, Clone, Default)]
pub struct SocketedManastone {
    pub item_id: u32,
    pub stat_bonus: i32,
}

pub struct ItemSocketService;

impl ItemSocketService {
    /// Calcula o número total de slots de pedras de mana (base + bônus).
    pub fn get_total_manastone_slots(item: &ItemTemplate) -> u8 {
        let base = match item.quality {
            crate::data::item::ItemQuality::Junk => 0,
            crate::data::item::ItemQuality::Common => 1,
            crate::data::item::ItemQuality::Rare => 2,
            crate::data::item::ItemQuality::Unique => 3,
            crate::data::item::ItemQuality::Epic => 4,
            crate::data::item::ItemQuality::Mythic => 5,
        };
        base + item.modifiers.option_slot_bonus
    }

    /// Valida se uma nova pedra de mana pode ser engastada.
    pub fn can_socket_manastone(item: &ItemTemplate, current_socketed_count: u8) -> Result<(), SocketError> {
        let max_slots = Self::get_total_manastone_slots(item);
        if max_slots == 0 {
            return Err(SocketError::ItemNotSocketable);
        }
        if current_socketed_count >= max_slots {
            return Err(SocketError::NoAvailableSlots);
        }
        Ok(())
    }

    /// Calcula a probabilidade de sucesso ao engastar uma pedra de mana.
    pub fn calculate_socket_success_rate(item_level: u8, manastone_level: u8, current_sockets: u8) -> f32 {
        let base_rate = if manastone_level <= item_level {
            0.75f32
        } else {
            0.50f32
        };
        // Cada pedra já engastada reduz ligeiramente a chance
        (base_rate - (current_sockets as f32 * 0.05)).clamp(0.20, 0.95)
    }
}
