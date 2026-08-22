//! Mascotes (ToyPets), Invocadores (Summons) e Armadilhas (Traps)

use std::collections::HashMap;
use super::engine::Coord;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PetFunction {
    Loot,
    Bag,
    Alarm,
    Buff,
    Feed,
}

#[derive(Debug, Clone)]
pub struct Pet {
    pub pet_id: u32,
    pub owner_id: u32,
    pub name: String,
    pub functions: Vec<PetFunction>,
    pub bag_slots: u8,
    pub bag_items: HashMap<u8, u32>,
    pub fullness: u8,
    pub mood: u16,
}

impl Pet {
    pub fn new(pet_id: u32, owner_id: u32, name: &str, bag_slots: u8, functions: Vec<PetFunction>) -> Self {
        Self {
            pet_id,
            owner_id,
            name: name.to_string(),
            functions,
            bag_slots,
            bag_items: HashMap::new(),
            fullness: 50,
            mood: 100,
        }
    }

    pub fn store_in_bag(&mut self, slot: u8, item_id: u32) -> bool {
        if slot < self.bag_slots && !self.bag_items.contains_key(&slot) {
            self.bag_items.insert(slot, item_id);
            true
        } else {
            false
        }
    }

    pub fn take_from_bag(&mut self, slot: u8) -> Option<u32> {
        self.bag_items.remove(&slot)
    }

    pub fn feed(&mut self, food_quality: u8) -> bool {
        if self.fullness < 100 {
            self.fullness = (self.fullness + food_quality).min(100);
            self.mood = (self.mood + 10).min(1000);
            true
        } else {
            false
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SummonType {
    FireSpirit,
    EarthSpirit,
    WaterSpirit,
    WindSpirit,
    MagmaSpirit,
    TempestSpirit,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SummonMode {
    Follow,
    Attack,
    Stay,
    Rest,
}

#[derive(Debug, Clone)]
pub struct Summon {
    pub summon_id: u32,
    pub master_id: u32,
    pub spirit_type: SummonType,
    pub hp: i32,
    pub max_hp: i32,
    pub location: Coord,
    pub mode: SummonMode,
    pub target_id: Option<u32>,
}

impl Summon {
    pub fn new(summon_id: u32, master_id: u32, spirit_type: SummonType, location: Coord) -> Self {
        let max_hp = match spirit_type {
            SummonType::EarthSpirit => 3500,
            SummonType::FireSpirit => 2200,
            SummonType::WaterSpirit => 1800,
            SummonType::WindSpirit => 2000,
            _ => 5000,
        };

        Self {
            summon_id,
            master_id,
            spirit_type,
            hp: max_hp,
            max_hp,
            location,
            mode: SummonMode::Follow,
            target_id: None,
        }
    }

    pub fn order_attack(&mut self, target_id: u32) {
        self.mode = SummonMode::Attack;
        self.target_id = Some(target_id);
    }

    pub fn order_follow(&mut self) {
        self.mode = SummonMode::Follow;
        self.target_id = None;
    }

    pub fn order_stay(&mut self) {
        self.mode = SummonMode::Stay;
        self.target_id = None;
    }
}

#[derive(Debug, Clone)]
pub struct Trap {
    pub trap_id: u32,
    pub owner_id: u32,
    pub location: Coord,
    pub trigger_radius: f32,
    pub damage: i32,
    pub effect_id: u32,
    pub is_triggered: bool,
}

impl Trap {
    pub fn new(trap_id: u32, owner_id: u32, location: Coord, damage: i32, effect_id: u32) -> Self {
        Self {
            trap_id,
            owner_id,
            location,
            trigger_radius: 3.0,
            damage,
            effect_id,
            is_triggered: false,
        }
    }

    pub fn check_trigger(&mut self, enemy_pos: &Coord) -> Option<(i32, u32)> {
        if !self.is_triggered && self.location.distance(enemy_pos) <= self.trigger_radius {
            self.is_triggered = true;
            Some((self.damage, self.effect_id))
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pet_bag_and_feeding() {
        let mut pet = Pet::new(
            1,
            100,
            "Shugo Pouch",
            6,
            vec![PetFunction::Bag, PetFunction::Feed],
        );

        assert!(pet.store_in_bag(0, 182400001));
        assert!(pet.store_in_bag(1, 160000001));
        assert!(!pet.store_in_bag(0, 999), "Slot 0 ja esta ocupado");
        assert!(!pet.store_in_bag(10, 999), "Slot fora do limite");

        assert_eq!(pet.take_from_bag(0), Some(182400001));
        assert_eq!(pet.take_from_bag(0), None);

        assert!(pet.feed(20));
        assert_eq!(pet.fullness, 70);
    }

    #[test]
    fn spiritmaster_summon_commands() {
        let mut fire_spirit = Summon::new(
            1,
            100,
            SummonType::FireSpirit,
            Coord::new(100.0, 100.0, 0.0),
        );
        assert_eq!(fire_spirit.mode, SummonMode::Follow);

        fire_spirit.order_attack(505);
        assert_eq!(fire_spirit.mode, SummonMode::Attack);
        assert_eq!(fire_spirit.target_id, Some(505));

        fire_spirit.order_stay();
        assert_eq!(fire_spirit.mode, SummonMode::Stay);
        assert_eq!(fire_spirit.target_id, None);
    }

    #[test]
    fn trap_trigger_detection() {
        let mut trap = Trap::new(
            1,
            100,
            Coord::new(100.0, 100.0, 0.0),
            450,
            8201, // Snare effect
        );

        // Enemy outside trigger radius (10m away)
        assert_eq!(trap.check_trigger(&Coord::new(110.0, 100.0, 0.0)), None);
        assert!(!trap.is_triggered);

        // Enemy enters trigger radius (2m away)
        let detonation = trap.check_trigger(&Coord::new(102.0, 100.0, 0.0));
        assert_eq!(detonation, Some((450, 8201)));
        assert!(trap.is_triggered);

        // Cannot trigger again
        assert_eq!(trap.check_trigger(&Coord::new(100.0, 100.0, 0.0)), None);
    }
}
