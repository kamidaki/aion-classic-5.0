//! Tipos de Dados do SpawnEngine (Padrão Java Aion Classic 2.8 / 4.5)

use std::time::Instant;

/// Tipos de Handlers de Spawn (SpawnHandlerType)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpawnHandlerType {
    Standard,
    Rift,
    StaticDoor,
    StaticObject,
    Gatherable,
    Base,
    Siege,
    Invasion,
    Temporary,
    Event,
    Custom,
}

impl Default for SpawnHandlerType {
    fn default() -> Self {
        Self::Standard
    }
}

/// Informações de Spawn Temporário (Ciclo Dia/Noite ou Horário de Jogo)
#[derive(Debug, Clone, PartialEq)]
pub struct TemporarySpawnInfo {
    pub start_hour: u8,
    pub end_hour: u8,
    pub spawn_chance: f32,
}

impl TemporarySpawnInfo {
    pub fn new(start_hour: u8, end_hour: u8, spawn_chance: f32) -> Self {
        Self {
            start_hour,
            end_hour,
            spawn_chance,
        }
    }

    pub fn is_in_spawn_time(&self, current_hour: u8) -> bool {
        if self.start_hour <= self.end_hour {
            current_hour >= self.start_hour && current_hour < self.end_hour
        } else {
            // Horário cruza a meia-noite (ex: 22h às 04h)
            current_hour >= self.start_hour || current_hour < self.end_hour
        }
    }
}

/// Ponto de Rota de Patrulha / Walker Waypoint
#[derive(Debug, Clone, PartialEq)]
pub struct WalkerPoint {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub rest_time_ms: u32,
    pub step: u32,
}

impl WalkerPoint {
    pub fn new(x: f32, y: f32, z: f32, rest_time_ms: u32, step: u32) -> Self {
        Self {
            x,
            y,
            z,
            rest_time_ms,
            step,
        }
    }
}

/// Rota de Patrulha de NPCs (Walker Route)
#[derive(Debug, Clone, PartialEq)]
pub struct WalkerRoute {
    pub route_id: String,
    pub points: Vec<WalkerPoint>,
    pub is_loop: bool,
}

impl WalkerRoute {
    pub fn new(route_id: impl Into<String>, points: Vec<WalkerPoint>, is_loop: bool) -> Self {
        Self {
            route_id: route_id.into(),
            points,
            is_loop,
        }
    }
}

/// Template de Spawn de Porta Estática (StaticDoorTemplate)
#[derive(Debug, Clone, PartialEq)]
pub struct StaticDoorTemplate {
    pub door_id: u32,
    pub world_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub is_open: bool,
    pub door_type: u8,
}

/// Porta Estática Instanciada (StaticDoor)
#[derive(Debug, Clone, PartialEq)]
pub struct StaticDoor {
    pub door_id: u32,
    pub world_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub is_open: bool,
    pub door_type: u8,
}

/// Template de Objeto Estático (StaticObjectTemplate - Baús, Pontos de Bind, Postbox)
#[derive(Debug, Clone, PartialEq)]
pub struct StaticObjectTemplate {
    pub object_id: u32,
    pub world_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub object_type: u8,
}

/// Objeto Estático Instanciado
#[derive(Debug, Clone, PartialEq)]
pub struct StaticObject {
    pub object_id: u32,
    pub world_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub object_type: u8,
}

/// Template de Fenda Dimensional (RiftSpawnTemplate)
#[derive(Debug, Clone, PartialEq)]
pub struct RiftSpawnTemplate {
    pub rift_id: u32,
    pub world_id: u32,
    pub dest_world_id: u32,
    pub dest_x: f32,
    pub dest_y: f32,
    pub dest_z: f32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub min_level: u8,
    pub max_level: u8,
    pub max_entries: u32,
    pub duration_secs: u32,
}

/// Instância Ativa de Fenda Dimensional
#[derive(Debug, Clone)]
pub struct RiftInstance {
    pub template: RiftSpawnTemplate,
    pub entity_id: u32,
    pub current_entries: u32,
    pub spawned_at: Instant,
    pub is_active: bool,
}

/// Template de Spawn Geral (SpawnTemplate)
#[derive(Debug, Clone)]
pub struct SpawnTemplate {
    pub spawn_id: u32,
    pub npc_id: u32,
    pub name_id: u32,
    pub world_id: u32,
    pub instance_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub respawn_time: u32,
    pub respawn_variance: u32,
    pub is_no_respawn: bool,
    pub walker_id: Option<String>,
    pub handler_type: SpawnHandlerType,
    pub temporary: Option<TemporarySpawnInfo>,
    pub state: u8,
    pub payload: Vec<u8>,
}

impl SpawnTemplate {
    pub fn new(
        spawn_id: u32,
        npc_id: u32,
        name_id: u32,
        world_id: u32,
        x: f32,
        y: f32,
        z: f32,
        heading: u8,
        respawn_time: u32,
    ) -> Self {
        Self {
            spawn_id,
            npc_id,
            name_id,
            world_id,
            instance_id: 1,
            x,
            y,
            z,
            heading,
            respawn_time,
            respawn_variance: 0,
            is_no_respawn: respawn_time == 0,
            walker_id: None,
            handler_type: SpawnHandlerType::Standard,
            temporary: None,
            state: 0,
            payload: Vec::new(),
        }
    }
}

/// Tarefa de Respawn Agendada
#[derive(Debug, Clone)]
pub struct RespawnTask {
    pub entity_id: u32,
    pub template_id: u32,
    pub respawn_at: Instant,
}
