//! InstanceRiftSpawnManager - Gerenciador de Fendas Dimensionais e Invasões PvP (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::engine::Coord;
use crate::entity::Entity;
use crate::spawnengine::types::{RiftInstance, RiftSpawnTemplate};
use crate::spawnengine::visible_object_spawner::VisibleObjectSpawner;

#[derive(Debug, Default)]
pub struct InstanceRiftSpawnManager {
    templates: HashMap<u32, RiftSpawnTemplate>,
    active_rifts: HashMap<u32, RiftInstance>,
}

impl InstanceRiftSpawnManager {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registra um template de fenda dimensional
    pub fn register_rift_template(&mut self, template: RiftSpawnTemplate) {
        self.templates.insert(template.rift_id, template);
    }

    /// Abre uma fenda dimensional no mapa
    pub fn open_rift(&mut self, rift_id: u32, entity_id: u32) -> Option<Entity> {
        let template = self.templates.get(&rift_id)?.clone();
        let entity = VisibleObjectSpawner::spawn_rift(&template, entity_id);

        let instance = RiftInstance {
            template,
            entity_id,
            current_entries: 0,
            spawned_at: Instant::now(),
            is_active: true,
        };

        self.active_rifts.insert(rift_id, instance);
        Some(entity)
    }

    /// Fecha manualmente uma fenda dimensional
    pub fn close_rift(&mut self, rift_id: u32) -> Option<u32> {
        let instance = self.active_rifts.remove(&rift_id)?;
        Some(instance.entity_id)
    }

    /// Processa a travessia de um jogador através da fenda dimensional
    pub fn use_rift(&mut self, rift_id: u32, player_level: u8) -> Result<(u32, Coord), String> {
        let rift = self
            .active_rifts
            .get_mut(&rift_id)
            .ok_or_else(|| "Fenda dimensional inativa ou não encontrada".to_string())?;

        if player_level < rift.template.min_level {
            return Err("Nível muito baixo para utilizar esta fenda".to_string());
        }

        if player_level > rift.template.max_level {
            return Err("Nível muito alto para utilizar esta fenda".to_string());
        }

        if rift.current_entries >= rift.template.max_entries {
            return Err("Limite de entradas da fenda atingido".to_string());
        }

        rift.current_entries += 1;
        let dest_world_id = rift.template.dest_world_id;
        let dest_coord = Coord::new(
            rift.template.dest_x,
            rift.template.dest_y,
            rift.template.dest_z,
        );

        Ok((dest_world_id, dest_coord))
    }

    /// Verifica expiração de fendas ativas por tempo de duração
    pub fn tick_rifts(&mut self, now: Instant) -> Vec<u32> {
        let mut expired_entity_ids = Vec::new();
        let mut to_remove = Vec::new();

        for (rift_id, rift) in &self.active_rifts {
            let duration = Duration::from_secs(rift.template.duration_secs as u64);
            if now.duration_since(rift.spawned_at) >= duration
                || rift.current_entries >= rift.template.max_entries
            {
                expired_entity_ids.push(rift.entity_id);
                to_remove.push(*rift_id);
            }
        }

        for id in to_remove {
            self.active_rifts.remove(&id);
        }

        expired_entity_ids
    }

    /// Retorna fendas ativas
    pub fn active_rift_count(&self) -> usize {
        self.active_rifts.len()
    }
}
