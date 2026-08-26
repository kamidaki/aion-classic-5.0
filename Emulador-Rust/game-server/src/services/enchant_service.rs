use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GodstoneEffect {
    Silence,
    Paralyze,
    Blind,
    Bleed,
    FireDamage,
    WaterDamage,
    EarthDamage,
    WindDamage,
}

#[derive(Debug, Clone)]
pub struct GodstoneTemplate {
    pub item_id: u32,
    pub effect: GodstoneEffect,
    pub proc_chance_percent: f32, // ex: 0.02 = 2%
    pub effect_duration_sec: u32,
    pub damage_amount: i32,
}

#[derive(Debug, Clone)]
pub struct FusedWeapon {
    pub main_weapon_id: u32,
    pub secondary_weapon_id: u32,
    pub bonus_base_attack: i32,
    pub extra_manastone_slots: u8,
}

#[derive(Debug, Clone, Default)]
pub struct EnchantService {
    pub godstones: HashMap<u32, GodstoneTemplate>,
}

impl EnchantService {
    pub fn new() -> Self {
        let mut godstones = HashMap::new();

        // Silence Godstone (2% chance for 8s)
        godstones.insert(
            187000010,
            GodstoneTemplate {
                item_id: 187000010,
                effect: GodstoneEffect::Silence,
                proc_chance_percent: 0.02,
                effect_duration_sec: 8,
                damage_amount: 0,
            },
        );

        // Paralyze Godstone (2% chance for 5s)
        godstones.insert(
            187000011,
            GodstoneTemplate {
                item_id: 187000011,
                effect: GodstoneEffect::Paralyze,
                proc_chance_percent: 0.02,
                effect_duration_sec: 5,
                damage_amount: 0,
            },
        );

        // 3760 Fire Damage Godstone (1% chance)
        godstones.insert(
            187000020,
            GodstoneTemplate {
                item_id: 187000020,
                effect: GodstoneEffect::FireDamage,
                proc_chance_percent: 0.01,
                effect_duration_sec: 0,
                damage_amount: 3760,
            },
        );

        Self { godstones }
    }

    /// Calcula fusao de armas de duas maos: adiciona 10% do ataque base da arma secundaria
    pub fn fuse_weapons(
        &self,
        main_weapon_id: u32,
        secondary_weapon_id: u32,
        secondary_base_attack: i32,
        secondary_slots: u8,
    ) -> Result<FusedWeapon, &'static str> {
        if main_weapon_id == 0 || secondary_weapon_id == 0 {
            return Err("Armas invalidas para fusao");
        }
        let bonus_base_attack = (secondary_base_attack as f32 * 0.10).round() as i32;
        Ok(FusedWeapon {
            main_weapon_id,
            secondary_weapon_id,
            bonus_base_attack,
            extra_manastone_slots: secondary_slots,
        })
    }

    /// Probabilidade de sucesso de encantamento baseada na diferenca de nivel da pedra e nivel do item
    pub fn calculate_enchant_chance(stone_level: u8, item_level: u8, current_enchant: u8) -> f32 {
        let level_diff = stone_level as i32 - item_level as i32;
        let mut base_chance = 0.50 + (level_diff as f32 * 0.05);

        // Penalidade para niveis altos (+10 a +15)
        if current_enchant >= 10 {
            base_chance -= (current_enchant - 9) as f32 * 0.05;
        }

        base_chance.clamp(0.05, 0.95)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_armsfusion_calculation() {
        let service = EnchantService::new();
        let fused = service
            .fuse_weapons(100100500, 100100501, 350, 4)
            .expect("deve fundir armas");
        assert_eq!(fused.bonus_base_attack, 35); // 10% de 350
        assert_eq!(fused.extra_manastone_slots, 4);
    }

    #[test]
    fn test_enchant_rates() {
        // Pedra L90 em item L60 (+30 niveis)
        let chance_l90 = EnchantService::calculate_enchant_chance(90, 60, 0);
        assert!(chance_l90 >= 0.90);

        // Pedra L60 em item L60 (+0 niveis) no +12
        let chance_high = EnchantService::calculate_enchant_chance(60, 60, 12);
        assert!(chance_high < 0.50);
    }
}
