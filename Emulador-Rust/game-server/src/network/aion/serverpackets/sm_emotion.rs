//! Pacote SM_EMOTION (Opcode 0x005E)

#[derive(Debug, Clone)]
pub struct SmEmotion {
    pub object_id: u32,
    pub emotion_type: u8,
    pub emotion_id: u32,
    pub target_id: Option<u32>,
}
