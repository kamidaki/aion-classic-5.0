//! StaticDoorSpawnManager - Gerenciador de Portas Estáticas do Mundo (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::spawnengine::types::{StaticDoor, StaticDoorTemplate};
use crate::spawnengine::visible_object_spawner::VisibleObjectSpawner;

#[derive(Debug, Default)]
pub struct StaticDoorSpawnManager {
    doors: HashMap<u32, StaticDoor>,
    doors_by_world: HashMap<u32, Vec<u32>>,
}

impl StaticDoorSpawnManager {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registra e spawna um template de porta estática
    pub fn register_template(&mut self, template: StaticDoorTemplate) {
        let door = VisibleObjectSpawner::spawn_static_door(&template);
        let world_id = door.world_id;
        let door_id = door.door_id;
        self.doors.insert(door_id, door);
        self.doors_by_world.entry(world_id).or_default().push(door_id);
    }

    /// Retorna todas as portas de um mundo específico
    pub fn get_doors_for_world(&self, world_id: u32) -> Vec<&StaticDoor> {
        if let Some(door_ids) = self.doors_by_world.get(&world_id) {
            door_ids.iter().filter_map(|id| self.doors.get(id)).collect()
        } else {
            Vec::new()
        }
    }

    /// Obtém uma porta estática por ID
    pub fn get_door(&self, door_id: u32) -> Option<&StaticDoor> {
        self.doors.get(&door_id)
    }

    /// Altera o estado aberto/fechado de uma porta
    pub fn set_door_state(&mut self, door_id: u32, is_open: bool) -> bool {
        if let Some(door) = self.doors.get_mut(&door_id) {
            door.is_open = is_open;
            true
        } else {
            false
        }
    }

    /// Retorna contagem total de portas estáticas carregadas
    pub fn total_doors(&self) -> usize {
        self.doors.len()
    }
}
