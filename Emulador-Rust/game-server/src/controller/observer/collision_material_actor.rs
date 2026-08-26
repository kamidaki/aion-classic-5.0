//! Ator de Efeito por Material de Terreno/Superfície (CollisionMaterialActor - Padrão Java Aion Classic 2.8 / 4.5)

use super::iactor::IActor;
use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct CollisionMaterialActor {
    pub material_id: u32,
    pub skill_effect_id: Option<u32>,
}

impl CollisionMaterialActor {
    pub fn new(material_id: u32, skill_effect_id: Option<u32>) -> Self {
        Self {
            material_id,
            skill_effect_id,
        }
    }
}

impl IActor for CollisionMaterialActor {
    fn act(&self, player_id: u32, _position: &Coord) {
        if let Some(skill_id) = self.skill_effect_id {
            println!("[COLLISION_MATERIAL] Aplicando efeito de material #{} (skill #{}) no jogador #{}", self.material_id, skill_id, player_id);
        }
    }
}
