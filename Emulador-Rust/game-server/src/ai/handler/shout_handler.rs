//! Handler de Falas e Gritos de IA (ShoutEventHandler - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct ShoutEventHandler;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShoutEventType {
    Aggro,
    HpLow,
    Died,
    SkillCast,
}

impl ShoutEventHandler {
    /// Determina se o NPC deve emitir um balão de fala / shout
    pub fn get_shout_message(
        npc_name: &str,
        event_type: ShoutEventType,
    ) -> Option<String> {
        match event_type {
            ShoutEventType::Aggro => Some(format!("{npc_name}: Intruder detected! Prepare to fight!")),
            ShoutEventType::HpLow => Some(format!("{npc_name}: You will not defeat me so easily!")),
            ShoutEventType::Died => Some(format!("{npc_name}: Ugh... I have failed...")),
            ShoutEventType::SkillCast => Some(format!("{npc_name}: Feel my wrath!")),
        }
    }
}
