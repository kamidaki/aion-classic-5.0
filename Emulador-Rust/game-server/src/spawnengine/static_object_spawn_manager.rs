//! StaticObjectSpawnManager - Gerenciador de Objetos Estáticos do Mundo (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::spawnengine::types::{StaticObject, StaticObjectTemplate};
use crate::spawnengine::visible_object_spawner::VisibleObjectSpawner;

#[derive(Debug, Default)]
pub struct StaticObjectSpawnManager {
    objects: HashMap<u32, StaticObject>,
    objects_by_world: HashMap<u32, Vec<u32>>,
}

impl StaticObjectSpawnManager {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registra e spawna um objeto estático
    pub fn register_template(&mut self, template: StaticObjectTemplate) {
        let obj = VisibleObjectSpawner::spawn_static_object(&template);
        let world_id = obj.world_id;
        let object_id = obj.object_id;
        self.objects.insert(object_id, obj);
        self.objects_by_world.entry(world_id).or_default().push(object_id);
    }

    /// Retorna todos os objetos estáticos de um mundo
    pub fn get_objects_for_world(&self, world_id: u32) -> Vec<&StaticObject> {
        if let Some(obj_ids) = self.objects_by_world.get(&world_id) {
            obj_ids.iter().filter_map(|id| self.objects.get(id)).collect()
        } else {
            Vec::new()
        }
    }

    /// Busca um objeto estático por ID
    pub fn get_object(&self, object_id: u32) -> Option<&StaticObject> {
        self.objects.get(&object_id)
    }

    /// Contagem total de objetos estáticos
    pub fn total_objects(&self) -> usize {
        self.objects.len()
    }
}
