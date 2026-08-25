//! Pacotes Client de Movimentação e Física (CM)

#[derive(Debug, Clone, PartialEq)]
pub struct Move {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub move_type: u8,
}

#[derive(Debug, Clone, PartialEq)]
pub struct PlayerMove {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub move_type: u8,
    pub vector_x: f32,
    pub vector_y: f32,
    pub vector_z: f32,
    pub glide_flag: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Windstream {
    pub stream_id: u32,
    pub boost_state: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PathFly {
    pub path_id: u32,
    pub step: u32,
}
