//! CreatureController - Gerenciador básico de criaturas vivas (jogadores, monstros, NPCs)

#[derive(Debug, Clone)]
pub struct CreatureController {
    pub object_id: u32,
    pub hp: i32,
    pub max_hp: i32,
    pub mp: u32,
    pub max_mp: u32,
    pub is_dead: bool,
    pub is_in_combat: bool,
    pub target_id: Option<u32>,
}

impl CreatureController {
    pub fn new(object_id: u32, max_hp: i32, max_mp: u32) -> Self {
        Self {
            object_id,
            hp: max_hp,
            max_hp,
            mp: max_mp,
            max_mp,
            is_dead: false,
            is_in_combat: false,
            target_id: None,
        }
    }

    pub fn take_damage(&mut self, amount: i32) -> bool {
        if self.is_dead {
            return false;
        }
        self.hp = (self.hp - amount).max(0);
        self.is_in_combat = true;
        if self.hp == 0 {
            self.is_dead = true;
            self.is_in_combat = false;
        }
        self.is_dead
    }

    pub fn heal(&mut self, amount: i32) {
        if !self.is_dead {
            self.hp = (self.hp + amount).min(self.max_hp);
        }
    }

    pub fn consume_mp(&mut self, amount: u32) -> bool {
        if self.mp >= amount {
            self.mp -= amount;
            true
        } else {
            false
        }
    }

    pub fn set_target(&mut self, target_id: Option<u32>) {
        self.target_id = target_id;
    }
}
