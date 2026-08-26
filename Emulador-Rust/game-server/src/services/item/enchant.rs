//! Serviço de Encantamento de Equipamentos (+1 a +15).

use crate::data::item::ItemTemplate;

#[derive(Debug, PartialEq, Eq)]
pub enum EnchantError {
    NotEnchantable,
    MaxEnchantReached,
    InvalidEnchantStone,
}

pub struct ItemEnchantService;

impl ItemEnchantService {
    /// Valida se o item pode receber encantamento.
    pub fn can_enchant(item: &ItemTemplate, current_level: u8) -> Result<(), EnchantError> {
        if item.modifiers.no_enchant {
            return Err(EnchantError::NotEnchantable);
        }
        if current_level >= item.modifiers.max_enchant_level {
            return Err(EnchantError::MaxEnchantReached);
        }
        Ok(())
    }

    /// Calcula a taxa de sucesso de encantamento baseada no nível do item, nível da pedra e nível atual de enchant.
    pub fn calculate_enchant_chance(item_level: u8, stone_level: u8, current_enchant: u8) -> f32 {
        let diff = stone_level as i32 - item_level as i32;
        let mut base_prob = match diff {
            d if d >= 30 => 0.90,
            d if d >= 20 => 0.80,
            d if d >= 10 => 0.70,
            d if d >= 0  => 0.55,
            d if d >= -10 => 0.35,
            _ => 0.15,
        };

        // Penalidade para níveis altos (+10 a +15)
        if current_enchant >= 10 {
            base_prob -= (current_enchant - 9) as f32 * 0.08;
        }

        base_prob.clamp(0.05, 0.95)
    }

    /// Calcula os atributos extras concedidos pelo nível de encantamento.
    /// Armas ganham dano físico/mágico por nível; Armaduras ganham defesa, HP e redução de dano crítico.
    pub fn get_enchant_stats(item: &ItemTemplate, enchant_level: u8) -> (i32, i32) {
        if item.is_weapon() {
            let bonus_per_level = if item.is_two_handed() { 4 } else { 2 };
            (bonus_per_level * enchant_level as i32, 0)
        } else if item.is_armor() {
            let hp_bonus = 20 * enchant_level as i32;
            let def_bonus = 3 * enchant_level as i32;
            (hp_bonus, def_bonus)
        } else {
            (0, 0)
        }
    }
}
