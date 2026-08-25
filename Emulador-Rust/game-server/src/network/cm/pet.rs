//! Pacotes do Cliente para Mascotes e Evocações (CM_PET_* / CM_SUMMON_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmPet {
    pub pet_id: u32,
    pub action_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmPetEmote {
    pub pet_id: u32,
    pub emote_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmSummonCommand {
    pub summon_id: u32,
    pub command_id: u8,
    pub target_id: Option<u32>,
}

#[derive(Debug, Clone)]
pub struct CmSummonAttack {
    pub summon_id: u32,
    pub target_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmSummonCastSpell {
    pub summon_id: u32,
    pub skill_id: u32,
    pub target_id: u32,
}
