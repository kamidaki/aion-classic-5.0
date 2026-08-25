//! TemporarySpawnEngine - Motor de Spawns Temporários e Ciclo Horário (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use crate::entity::Entity;
use crate::spawnengine::types::SpawnTemplate;
use crate::spawnengine::visible_object_spawner::VisibleObjectSpawner;

#[derive(Debug, Default)]
pub struct TemporarySpawnEngine {
    templates: Vec<SpawnTemplate>,
    /// Mapeamento de template_id -> entity_id ativo
    active_spawns: HashMap<u32, u32>,
}

impl TemporarySpawnEngine {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registra um template com restrição horária de spawn
    pub fn register_temporary_template(&mut self, template: SpawnTemplate) {
        self.templates.push(template);
    }

    /// Processa mudança de hora do jogo (Day/Night cycle)
    /// Retorna: (IDs de entidades que devem ser despawnadas, novas Entidades criadas)
    pub fn on_hour_change(
        &mut self,
        current_hour: u8,
        mut next_entity_id: impl FnMut() -> u32,
    ) -> (Vec<u32>, Vec<Entity>) {
        let mut despawned = Vec::new();
        let mut spawned = Vec::new();

        for template in &self.templates {
            let temp_info = match &template.temporary {
                Some(info) => info,
                None => continue,
            };

            let in_time = temp_info.is_in_spawn_time(current_hour);
            let is_currently_active = self.active_spawns.contains_key(&template.spawn_id);

            if !in_time && is_currently_active {
                // Fora do horário: despawn
                if let Some(entity_id) = self.active_spawns.remove(&template.spawn_id) {
                    despawned.push(entity_id);
                }
            } else if in_time && !is_currently_active {
                // Dentro do horário: spawn
                let entity_id = next_entity_id();
                let entity = VisibleObjectSpawner::spawn_npc(template, entity_id);
                self.active_spawns.insert(template.spawn_id, entity_id);
                spawned.push(entity);
            }
        }

        (despawned, spawned)
    }

    /// Contagem de spawns temporários ativos
    pub fn active_count(&self) -> usize {
        self.active_spawns.len()
    }
}
