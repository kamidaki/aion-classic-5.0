//! Modelo de Jogador (PlayerModel - Padrão Java Aion Classic 2.8 / 4.5)

use crate::engine::Coord;
use crate::model::gameobjects::creature::Creature;
use crate::model::gender::Gender;
use crate::model::player_class::PlayerClass;
use crate::model::race::Race;

#[derive(Debug, Clone)]
pub struct PlayerModel {
    pub creature: Creature,
    pub account_id: u32,
    pub player_class: PlayerClass,
    pub gender: Gender,
    pub exp: u64,
    pub kinah: u64,
    pub abyss_points: u32,
    pub title_id: u16,
    pub legion_id: Option<u32>,
    pub is_flying: bool,
}

impl PlayerModel {
    pub fn new(
        player_id: u32,
        account_id: u32,
        name: &str,
        player_class: PlayerClass,
        gender: Gender,
        race: Race,
        pos: Coord,
        world_id: u32,
    ) -> Self {
        let mut creature = Creature::new(player_id, name, pos, world_id, 1, 1, 1000, 1000);
        creature.race = race;

        Self {
            creature,
            account_id,
            player_class,
            gender,
            exp: 0,
            kinah: 0,
            abyss_points: 0,
            title_id: 0,
            legion_id: None,
            is_flying: false,
        }
    }
}
