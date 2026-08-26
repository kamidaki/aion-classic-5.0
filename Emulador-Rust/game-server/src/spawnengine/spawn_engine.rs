//! SpawnEngine - Orquestrador Central de Povoamento e Ciclo de Vida de Spawns (Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::time::{Duration, Instant};

use crate::entity::Entity;
use crate::spawnengine::instance_rift_spawn_manager::InstanceRiftSpawnManager;
use crate::spawnengine::static_door_spawn_manager::StaticDoorSpawnManager;
use crate::spawnengine::static_object_spawn_manager::StaticObjectSpawnManager;
use crate::spawnengine::temporary_spawn_engine::TemporarySpawnEngine;
use crate::spawnengine::types::{RespawnTask, SpawnHandlerType, SpawnTemplate};
use crate::spawnengine::visible_object_spawner::VisibleObjectSpawner;
use crate::spawnengine::walker_formator::WalkerFormator;

pub struct SpawnEngine {
    pub templates: HashMap<u32, SpawnTemplate>,
    pub spawns_by_world: HashMap<u32, Vec<u32>>,
    pub entity_to_template: HashMap<u32, u32>,
    pub respawn_queue: Vec<RespawnTask>,
    pub door_manager: StaticDoorSpawnManager,
    pub object_manager: StaticObjectSpawnManager,
    pub temporary_engine: TemporarySpawnEngine,
    pub rift_manager: InstanceRiftSpawnManager,
    pub walker_formator: WalkerFormator,
    next_entity_id: u32,
}

impl Default for SpawnEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl SpawnEngine {
    pub fn new() -> Self {
        Self {
            templates: HashMap::new(),
            spawns_by_world: HashMap::new(),
            entity_to_template: HashMap::new(),
            respawn_queue: Vec::new(),
            door_manager: StaticDoorSpawnManager::new(),
            object_manager: StaticObjectSpawnManager::new(),
            temporary_engine: TemporarySpawnEngine::new(),
            rift_manager: InstanceRiftSpawnManager::new(),
            walker_formator: WalkerFormator::new(),
            next_entity_id: 0x8000_0001,
        }
    }

    /// Aloca um novo ID de entidade dinâmico para NPCs (bit 0x8000_0000 ligado)
    pub fn next_id(&mut self) -> u32 {
        let id = self.next_entity_id;
        self.next_entity_id = self.next_entity_id.saturating_add(1);
        id
    }

    /// Carrega templates de spawn a partir do arquivo CSV oficial (`data/spawns.csv`)
    pub fn load_from_csv(&mut self, path: &Path) -> Result<usize, String> {
        let file = File::open(path).map_err(|e| e.to_string())?;
        let reader = BufReader::new(file);

        let mut count = 0;
        for line_res in reader.lines() {
            let line = line_res.map_err(|e| e.to_string())?;
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') || line.starts_with("mapa") {
                continue;
            }

            let parts: Vec<&str> = line.split(',').collect();
            if parts.len() >= 6 {
                let world_id = parts[0].trim().parse().unwrap_or(0);
                let npc_id = parts[1].trim().parse().unwrap_or(0);
                let name_id = parts[2].trim().parse().unwrap_or(0);
                let x = parts[3].trim().parse().unwrap_or(0.0);
                let y = parts[4].trim().parse().unwrap_or(0.0);
                let z = parts[5].trim().parse().unwrap_or(0.0);
                let heading = if parts.len() > 6 {
                    parts[6].trim().parse().unwrap_or(0)
                } else {
                    0
                };

                let payload = if parts.len() > 7 {
                    hex_to_bytes(parts[7]).unwrap_or_default()
                } else {
                    Vec::new()
                };

                let spawn_id = (self.templates.len() as u32) + 1;
                let mut template = SpawnTemplate::new(
                    spawn_id,
                    npc_id,
                    name_id,
                    world_id,
                    x,
                    y,
                    z,
                    heading,
                    295, // Tempo de respawn padrão (Classic ~5 min)
                );
                template.payload = payload;

                self.templates.insert(spawn_id, template);
                self.spawns_by_world.entry(world_id).or_default().push(spawn_id);
                count += 1;
            }
        }

        Ok(count)
    }

    /// Spawna todos os monstros e NPCs no mundo inicializando as entidades ativas
    pub fn spawn_all(
        &mut self,
        entities: &mut Vec<Entity>,
        put_npc: &mut HashMap<u32, Vec<u8>>,
    ) {
        let templates: Vec<SpawnTemplate> = self
            .templates
            .values()
            .filter(|t| t.handler_type == SpawnHandlerType::Standard)
            .cloned()
            .collect();

        for template in templates {
            let entity_id = self.next_id();
            let entity = VisibleObjectSpawner::spawn_npc(&template, entity_id);

            // Registra mapeamento para controle de respawn futuro
            self.entity_to_template.insert(entity_id, template.spawn_id);

            // Injeta o entity_id no payload pré-compilado de rede (offset 10)
            if !template.payload.is_empty() {
                let mut payload = template.payload.clone();
                let off = crate::data_loader::OFFSET_ID_ENTIDADE;
                if payload.len() >= off + 4 {
                    payload[off..off + 4].copy_from_slice(&entity_id.to_le_bytes());
                    put_npc.insert(entity_id, payload);
                }
            }

            entities.push(entity);
        }
    }

    /// Spawna todos os monstros de uma instância de masmorra específica
    pub fn spawn_instance(&mut self, world_id: u32, instance_id: u32) -> Vec<Entity> {
        let mut spawned = Vec::new();
        let template_ids: Vec<u32> = self.spawns_by_world.get(&world_id).cloned().unwrap_or_default();
        for t_id in template_ids {
            if let Some(template) = self.templates.get(&t_id).cloned() {
                let mut inst_template = template;
                inst_template.instance_id = instance_id;
                let entity_id = self.next_id();
                let entity = VisibleObjectSpawner::spawn_npc(&inst_template, entity_id);
                self.entity_to_template.insert(entity_id, t_id);
                spawned.push(entity);
            }
        }
        spawned
    }

    /// Adiciona dinamicamente um novo spawn persistente (ex: comando GM //spawn)
    pub fn add_new_spawn(
        &mut self,
        world_id: u32,
        npc_id: u32,
        name_id: u32,
        x: f32,
        y: f32,
        z: f32,
        heading: u8,
        respawn_time: u32,
    ) -> Entity {
        let spawn_id = (self.templates.len() as u32) + 1;
        let template = SpawnTemplate::new(
            spawn_id,
            npc_id,
            name_id,
            world_id,
            x,
            y,
            z,
            heading,
            respawn_time,
        );

        self.templates.insert(spawn_id, template.clone());
        self.spawns_by_world.entry(world_id).or_default().push(spawn_id);

        let entity_id = self.next_id();
        let entity = VisibleObjectSpawner::spawn_npc(&template, entity_id);
        self.entity_to_template.insert(entity_id, spawn_id);
        entity
    }

    /// Adiciona um spawn temporário único sem respawn (ex: invocação de quest)
    pub fn add_new_single_time_spawn(
        &mut self,
        world_id: u32,
        npc_id: u32,
        name_id: u32,
        x: f32,
        y: f32,
        z: f32,
        heading: u8,
    ) -> Entity {
        let spawn_id = (self.templates.len() as u32) + 1;
        let mut template = SpawnTemplate::new(
            spawn_id,
            npc_id,
            name_id,
            world_id,
            x,
            y,
            z,
            heading,
            0, // No respawn
        );
        template.is_no_respawn = true;

        let entity_id = self.next_id();
        VisibleObjectSpawner::spawn_npc(&template, entity_id)
    }

    /// Agenda o respawn de um monstro derrotado
    pub fn schedule_respawn(&mut self, entity_id: u32, delay_secs: u32) {
        if let Some(&template_id) = self.entity_to_template.get(&entity_id) {
            let respawn_at = Instant::now() + Duration::from_secs(delay_secs as u64);
            self.respawn_queue.push(RespawnTask {
                entity_id,
                template_id,
                respawn_at,
            });
        }
    }

    /// Executa o ciclo de atualização do SpawnEngine:
    /// - Processa respawns concluídos
    /// - Executa rotas de patrulha
    /// - Processa expiração de rifts
    pub fn tick(
        &mut self,
        now: Instant,
        entities: &mut Vec<Entity>,
        put_npc: &mut HashMap<u32, Vec<u8>>,
    ) {
        // 1. Processa Respawn de Monstros
        let mut i = 0;
        while i < self.respawn_queue.len() {
            if now >= self.respawn_queue[i].respawn_at {
                let task = self.respawn_queue.swap_remove(i);
                let template_opt = self.templates.get(&task.template_id).cloned();
                if let Some(template) = template_opt {
                    if !template.is_no_respawn {
                        let new_entity_id = self.next_id();
                        let new_entity = VisibleObjectSpawner::spawn_npc(&template, new_entity_id);

                        self.entity_to_template.insert(new_entity_id, template.spawn_id);

                        if !template.payload.is_empty() {
                            let mut payload = template.payload.clone();
                            let off = crate::data_loader::OFFSET_ID_ENTIDADE;
                            if payload.len() >= off + 4 {
                                payload[off..off + 4].copy_from_slice(&new_entity_id.to_le_bytes());
                                put_npc.insert(new_entity_id, payload);
                            }
                        }

                        entities.push(new_entity);
                    }
                }
            } else {
                i += 1;
            }
        }

        // 2. Processa movimentação de patrulhas
        self.walker_formator.tick_walkers(entities, now);

        // 3. Processa expiração de Fendas Dimensionais
        let expired_rifts = self.rift_manager.tick_rifts(now);
        for rift_entity_id in expired_rifts {
            entities.retain(|e| e.id() != rift_entity_id);
            put_npc.remove(&rift_entity_id);
        }
    }
}

fn hex_to_bytes(hex: &str) -> Option<Vec<u8>> {
    let hex = hex.trim();
    if hex.len() % 2 != 0 {
        return None;
    }
    let mut bytes = Vec::with_capacity(hex.len() / 2);
    for i in (0..hex.len()).step_by(2) {
        let b = u8::from_str_radix(&hex[i..i + 2], 16).ok()?;
        bytes.push(b);
    }
    Some(bytes)
}
