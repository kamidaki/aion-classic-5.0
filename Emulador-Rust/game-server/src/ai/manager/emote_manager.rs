//! Gerenciador de Emotes e Animações de NPCs (EmoteManager - Padrão Java Aion Classic 2.8 / 4.5)

use crate::message::server as s;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NpcEmote {
    Idle,
    Walk,
    Run,
    Attack,
    Die,
    Cast,
    Return,
    Talk,
}

pub struct EmoteManager;

impl EmoteManager {
    /// Constrói o pacote de estado ou animação de NPC (SM_EMOTE / SM_ACTION)
    pub fn create_npc_action_message(
        npc_id: u32,
        action_type: crate::data::ActionType,
        target_id: u32,
        speed: f32,
    ) -> s::Message {
        s::Message::Action(s::Action::new(npc_id, action_type, speed, target_id))
    }
}
