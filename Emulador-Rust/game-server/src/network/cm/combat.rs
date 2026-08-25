//! Pacotes Client de Combate e Habilidades (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Attack {
    pub target_obj_id: u32,
    pub attack_type: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CastSpell {
    pub skill_id: u16,
    pub skill_level: u8,
    pub target_obj_id: u32,
    pub hit_time: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TargetSelect {
    pub target_obj_id: u32,
    pub target_type: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CancelAction {
    pub cancel_type: u8,
}
