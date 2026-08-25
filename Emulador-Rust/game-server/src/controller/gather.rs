//! GatherableController - Gerenciador de coleta de materiais (Herb, Ore, Aether)

#[derive(Debug, Clone)]
pub struct GatherableController {
    pub object_id: u32,
    pub template_id: u32,
    pub required_skill_level: u32,
    pub remaining_gathers: u32,
    pub max_gathers: u32,
    pub is_gathering: bool,
    pub current_gatherer: Option<u32>,
}

impl GatherableController {
    pub fn new(object_id: u32, template_id: u32, required_skill_level: u32, max_gathers: u32) -> Self {
        Self {
            object_id,
            template_id,
            required_skill_level,
            remaining_gathers: max_gathers,
            max_gathers,
            is_gathering: false,
            current_gatherer: None,
        }
    }

    pub fn can_gather(&self, player_skill_level: u32) -> bool {
        self.remaining_gathers > 0 && !self.is_gathering && player_skill_level >= self.required_skill_level
    }

    pub fn start_gathering(&mut self, player_id: u32) -> bool {
        if !self.is_gathering && self.remaining_gathers > 0 {
            self.is_gathering = true;
            self.current_gatherer = Some(player_id);
            true
        } else {
            false
        }
    }

    pub fn calculate_success_chance(&self, player_skill_level: u32) -> f32 {
        if player_skill_level < self.required_skill_level {
            return 0.0;
        }
        let diff = player_skill_level - self.required_skill_level;
        let base = 50.0 + (diff as f32 * 2.0);
        base.clamp(10.0, 95.0)
    }

    pub fn finish_gathering(&mut self, success: bool) -> bool {
        self.is_gathering = false;
        self.current_gatherer = None;
        if success {
            self.remaining_gathers = self.remaining_gathers.saturating_sub(1);
        }
        self.remaining_gathers == 0 // Retorna true se o nó se esgotou
    }
}
