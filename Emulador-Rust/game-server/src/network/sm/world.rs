//! Pacotes do Servidor para Objetos e Entidades do Mundo (SM_PUT_* / SM_WORLD_* - Padrão Classic 4.5)

use crate::engine::Coord;

#[derive(Debug, Clone)]
pub struct SmPutUser {
    pub player_id: u32,
    pub name: String,
    pub pos: Coord,
    pub heading: u8,
    pub class_id: u8,
    pub race_id: u8,
    pub gender_id: u8,
    pub max_hp: i32,
    pub cur_hp: i32,
}

#[derive(Debug, Clone)]
pub struct SmPutNpc {
    pub npc_obj_id: u32,
    pub npc_template_id: u32,
    pub pos: Coord,
    pub heading: u8,
    pub max_hp: i32,
    pub cur_hp: i32,
}

#[derive(Debug, Clone)]
pub struct SmRemoveObject {
    pub object_id: u32,
}

#[derive(Debug, Clone)]
pub struct SmTargetInfo {
    pub target_id: u32,
    pub target_type: u8,
}
