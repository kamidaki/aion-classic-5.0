//! Pacote SM_CASTSPELL (Opcode 0x0047)

#[derive(Debug, Clone)]
pub struct SmCastSpell {
    pub caster_id: u32,
    pub target_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub duration: u32,
}
