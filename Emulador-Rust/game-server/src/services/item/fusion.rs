//! Serviço de Fusão de Armas de Duas Mãos (Armsfusion / Arms Combining).
//! Permite combinar uma arma secundária de 2 mãos em uma principal, herdando 10% do ataque e slots.

use crate::data::item::ItemTemplate;

#[derive(Debug, PartialEq, Eq)]
pub enum FusionError {
    NotTwoHandedWeapon,
    IncompatibleWeaponTypes,
    SecondaryLevelHigherThanPrimary,
    PrimaryAlreadyFused,
    NotComposable,
}

#[derive(Debug, Clone, Default)]
pub struct FusedWeaponData {
    pub secondary_item_id: u32,
    pub bonus_min_damage: u32,
    pub bonus_max_damage: u32,
    pub bonus_attack_speed_ratio: f32,
    pub secondary_manastones: Vec<u32>,
}

pub struct ItemFusionService;

impl ItemFusionService {
    /// Valida se duas armas podem ser combinadas via Armsfusion.
    pub fn can_fuse(primary: &ItemTemplate, secondary: &ItemTemplate) -> Result<(), FusionError> {
        if !primary.is_two_handed() || !secondary.is_two_handed() {
            return Err(FusionError::NotTwoHandedWeapon);
        }

        if primary.weapon_type != secondary.weapon_type {
            return Err(FusionError::IncompatibleWeaponTypes);
        }

        if secondary.level > primary.level {
            return Err(FusionError::SecondaryLevelHigherThanPrimary);
        }

        if !primary.modifiers.can_composite {
            return Err(FusionError::NotComposable);
        }

        Ok(())
    }

    /// Calcula os bônus concedidos pela arma secundária na fusão (10% do ataque base).
    pub fn calculate_fusion_bonus(secondary: &ItemTemplate) -> FusedWeaponData {
        FusedWeaponData {
            secondary_item_id: secondary.id,
            bonus_min_damage: (secondary.stats.min_damage as f32 * 0.10).round() as u32,
            bonus_max_damage: (secondary.stats.max_damage as f32 * 0.10).round() as u32,
            bonus_attack_speed_ratio: 0.0,
            secondary_manastones: Vec::new(),
        }
    }
}
