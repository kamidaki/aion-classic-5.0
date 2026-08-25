//! Pacote CM_EMOTION (Opcode 0x005E)

#[derive(Debug, Clone)]
pub struct CmEmotion {
    pub emotion_type: u8,
    pub emotion_id: u32,
    pub target_id: Option<u32>,
}
