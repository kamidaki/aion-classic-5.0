//! Modelo de NPC e Monstro (NpcModel - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::creature::Creature;
use crate::model::npc_type::NpcType;
use crate::model::tribe_class::TribeClass;

#[derive(Debug, Clone)]
pub struct NpcModel {
    pub creature: Creature,
    pub npc_template_id: u32,
    pub npc_type: NpcType,
    pub ai_name: String,
    pub spawn_pos: Coord,
    pub respawn_time_seconds: u32,
}

impl NpcModel {
    pub fn new(
        object_id: u32,
        npc_template_id: u32,
        name: &str,
        pos: Coord,
        world_id: u32,
        instance_id: u32,
        level: u16,
        hp: i32,
    ) -> Self {
        let mut creature = Creature::new(object_id, name, pos, world_id, instance_id, level, hp, 1000);
        creature.tribe = TribeClass::Monster;

        Self {
            creature,
            npc_template_id,
            npc_type: NpcType::Attackable,
            ai_name: "monster".to_string(),
            spawn_pos: pos,
            respawn_time_seconds: 60,
        }
    }
}
