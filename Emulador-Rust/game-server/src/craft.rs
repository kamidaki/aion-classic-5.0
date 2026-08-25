//! Motor de Coleta (Gathering), Extração de Éter e Artesanato (Crafting)

use std::collections::HashMap;
use super::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CraftProfession {
    Essencetapping = 1001,
    Aethertapping = 1002,
    Cooking = 40001,
    Weaponsmithing = 40002,
    Armorsmithing = 40003,
    Tailoring = 40004,
    Handicrafting = 40005,
    Alchemy = 40006,
    Construction = 40007,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GatherResult {
    Success { item_id: u32, count: u32 },
    Failure,
    InProgress { success_pct: u8, fail_pct: u8 },
}

#[derive(Debug, Clone)]
pub struct Gatherable {
    pub id: u32,
    pub template_id: u32,
    pub location: Coord,
    pub skill_level_req: u16,
    pub remaining_harvests: u8,
    pub material_item_id: u32,
    pub is_aerial: bool,
}

impl Gatherable {
    pub fn new(
        id: u32,
        template_id: u32,
        location: Coord,
        skill_level_req: u16,
        harvest_count: u8,
        material_item_id: u32,
        is_aerial: bool,
    ) -> Self {
        Self {
            id,
            template_id,
            location,
            skill_level_req,
            remaining_harvests: harvest_count,
            material_item_id,
            is_aerial,
        }
    }

    pub fn can_gather(&self, player_skill: u16, player_pos: &Coord, is_flying: bool) -> bool {
        if self.remaining_harvests == 0 || player_skill < self.skill_level_req {
            return false;
        }

        if self.is_aerial && !is_flying {
            return false;
        }

        self.location.distance(player_pos) <= 6.0
    }

    pub fn harvest(&mut self) -> Option<(u32, u32)> {
        if self.remaining_harvests > 0 {
            self.remaining_harvests -= 1;
            Some((self.material_item_id, 1))
        } else {
            None
        }
    }
}

#[derive(Debug, Clone)]
pub struct CraftRecipe {
    pub id: u32,
    pub profession: CraftProfession,
    pub required_level: u16,
    pub ingredients: Vec<(u32, u32)>,
    pub normal_product_id: u32,
    pub normal_product_count: u32,
    pub combo_product_id: Option<u32>,
    pub combo_chance_percent: f32,
}

impl CraftRecipe {
    pub fn new(
        id: u32,
        profession: CraftProfession,
        required_level: u16,
        ingredients: Vec<(u32, u32)>,
        normal_product_id: u32,
        normal_product_count: u32,
        combo_product_id: Option<u32>,
        combo_chance_percent: f32,
    ) -> Self {
        Self {
            id,
            profession,
            required_level,
            ingredients,
            normal_product_id,
            normal_product_count,
            combo_product_id,
            combo_chance_percent,
        }
    }

    pub fn can_craft(&self, player_skill: u16, inventory: &HashMap<u32, u64>) -> bool {
        if player_skill < self.required_level {
            return false;
        }

        for (item_id, req_count) in &self.ingredients {
            let available = inventory.get(item_id).copied().unwrap_or(0);
            if available < *req_count as u64 {
                return false;
            }
        }

        true
    }

    pub fn execute_craft(&self, roll_proc: f32) -> (u32, u32) {
        if let Some(combo_id) = self.combo_product_id {
            if roll_proc <= self.combo_chance_percent {
                return (combo_id, self.normal_product_count);
            }
        }
        (self.normal_product_id, self.normal_product_count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gatherable_distance_skill_and_aerial_check() {
        let mut herb = Gatherable::new(
            1,
            1001,
            Coord::new(100.0, 100.0, 0.0),
            15,
            3,
            152000001,
            false,
        );

        // Player too far (10m away)
        assert!(!herb.can_gather(20, &Coord::new(110.0, 100.0, 0.0), false));

        // Player too low level (skill 10 < 15)
        assert!(!herb.can_gather(10, &Coord::new(102.0, 100.0, 0.0), false));

        // Valid gather
        assert!(herb.can_gather(20, &Coord::new(102.0, 100.0, 0.0), false));
        assert_eq!(herb.harvest(), Some((152000001, 1)));
        assert_eq!(herb.remaining_harvests, 2);

        // Aerial Aether vortex requires flying
        let aether = Gatherable::new(
            2,
            1002,
            Coord::new(100.0, 100.0, 50.0),
            1,
            3,
            152200001,
            true,
        );
        assert!(!aether.can_gather(10, &Coord::new(100.0, 100.0, 50.0), false));
        assert!(aether.can_gather(10, &Coord::new(100.0, 100.0, 50.0), true));
    }

    #[test]
    fn craft_recipe_validation_and_combo_proc() {
        let recipe = CraftRecipe::new(
            101,
            CraftProfession::Alchemy,
            10,
            vec![(152000001, 2), (182400001, 100)], // 2 Herbs + 100 Kinah
            160000001, // Normal Potion
            1,
            Some(160000002), // Greater Potion (Proc)
            25.0, // 25% chance
        );

        let mut inventory = HashMap::new();
        inventory.insert(152000001, 1); // Not enough herbs

        assert!(!recipe.can_craft(15, &inventory), "Deve falhar por falta de ingredientes");

        inventory.insert(152000001, 5);
        inventory.insert(182400001, 500);
        assert!(recipe.can_craft(15, &inventory), "Deve aprovar craft com ingredientes suficientes");

        // Normal roll
        let (item, count) = recipe.execute_craft(50.0);
        assert_eq!(item, 160000001);
        assert_eq!(count, 1);

        // Lucky roll (proc triggered <= 25%)
        let (proc_item, count) = recipe.execute_craft(15.0);
        assert_eq!(proc_item, 160000002, "Deve gerar produto combo crítico (Proc)");
        assert_eq!(count, 1);
    }
}
