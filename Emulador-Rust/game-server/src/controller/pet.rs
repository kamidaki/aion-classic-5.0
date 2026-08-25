//! PetController - Gerenciador de mascotes (bolsa, alimentação, emotes)

#[derive(Debug, Clone)]
pub struct PetController {
    pub pet_id: u32,
    pub owner_id: u32,
    pub hunger_level: u32,
    pub is_spawned: bool,
    pub bag_items: Vec<u32>,
}

impl PetController {
    pub fn new(pet_id: u32, owner_id: u32) -> Self {
        Self {
            pet_id,
            owner_id,
            hunger_level: 100,
            is_spawned: false,
            bag_items: Vec::new(),
        }
    }

    pub fn spawn(&mut self) {
        self.is_spawned = true;
    }

    pub fn despawn(&mut self) {
        self.is_spawned = false;
    }

    pub fn feed(&mut self, food_quality: u32) {
        self.hunger_level = (self.hunger_level + food_quality).min(100);
    }
}
