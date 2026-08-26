use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StigmaType {
    Regular,
    Advanced,
}

#[derive(Debug, Clone)]
pub struct StigmaTemplate {
    pub item_id: u32,
    pub skill_id: u16,
    pub skill_level: u8,
    pub shard_cost: u32,
    pub required_level: u8,
    pub stigma_type: StigmaType,
}

#[derive(Debug, Clone, Default)]
pub struct StigmaService {
    pub stigmas: HashMap<u32, StigmaTemplate>,
}

impl StigmaService {
    pub fn new() -> Self {
        let mut stigmas = HashMap::new();

        // 1. Gladiator: Severe Precision Cut
        stigmas.insert(
            140000001,
            StigmaTemplate {
                item_id: 140000001,
                skill_id: 1001,
                skill_level: 1,
                shard_cost: 60,
                required_level: 20,
                stigma_type: StigmaType::Regular,
            },
        );

        // 2. Sorcerer: Big Magma Eruption (Advanced)
        stigmas.insert(
            140000050,
            StigmaTemplate {
                item_id: 140000050,
                skill_id: 1401,
                skill_level: 1,
                shard_cost: 250,
                required_level: 50,
                stigma_type: StigmaType::Advanced,
            },
        );

        Self { stigmas }
    }

    /// Retorna quantos slots de Stigma regular o jogador tem liberados para seu nivel
    pub fn get_max_regular_slots(level: u8) -> usize {
        if level >= 58 {
            6
        } else if level >= 55 {
            5
        } else if level >= 50 {
            4
        } else if level >= 40 {
            3
        } else if level >= 30 {
            2
        } else if level >= 20 {
            1
        } else {
            0
        }
    }

    /// Retorna quantos slots de Stigma avancada o jogador tem liberados para seu nivel
    pub fn get_max_advanced_slots(level: u8) -> usize {
        if level >= 60 {
            6
        } else if level >= 58 {
            5
        } else if level >= 55 {
            4
        } else if level >= 52 {
            3
        } else if level >= 50 {
            2
        } else if level >= 45 {
            1
        } else {
            0
        }
    }

    pub fn can_equip(
        &self,
        item_id: u32,
        player_level: u8,
        player_shards: u32,
        current_equipped_regular: usize,
        current_equipped_advanced: usize,
    ) -> Result<(&StigmaTemplate, u32), &'static str> {
        let stigma = self.stigmas.get(&item_id).ok_or("Stigma nao encontrada")?;

        if player_level < stigma.required_level {
            return Err("Nivel insuficiente para equipar esta Stigma");
        }

        if player_shards < stigma.shard_cost {
            return Err("Stigma Shards insuficientes");
        }

        match stigma.stigma_type {
            StigmaType::Regular => {
                if current_equipped_regular >= Self::get_max_regular_slots(player_level) {
                    return Err("Limite de slots de Stigma Regular atingido");
                }
            }
            StigmaType::Advanced => {
                if current_equipped_advanced >= Self::get_max_advanced_slots(player_level) {
                    return Err("Limite de slots de Stigma Avancada atingido");
                }
            }
        }

        let remaining_shards = player_shards - stigma.shard_cost;
        Ok((stigma, remaining_shards))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stigma_slots_progression() {
        assert_eq!(StigmaService::get_max_regular_slots(19), 0);
        assert_eq!(StigmaService::get_max_regular_slots(20), 1);
        assert_eq!(StigmaService::get_max_regular_slots(50), 4);
        assert_eq!(StigmaService::get_max_regular_slots(65), 6);

        assert_eq!(StigmaService::get_max_advanced_slots(40), 0);
        assert_eq!(StigmaService::get_max_advanced_slots(45), 1);
        assert_eq!(StigmaService::get_max_advanced_slots(65), 6);
    }

    #[test]
    fn test_stigma_equip() {
        let service = StigmaService::new();
        let (stigma, remaining) = service
            .can_equip(140000001, 25, 100, 0, 0)
            .expect("deve equipar regular");
        assert_eq!(stigma.skill_id, 1001);
        assert_eq!(remaining, 40); // 100 - 60
    }
}
