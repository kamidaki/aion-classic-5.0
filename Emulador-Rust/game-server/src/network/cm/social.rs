//! Pacotes Client de Chat, Grupo, Guilda e Amigos (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChatMessagePublic {
    pub message_type: u8,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChatMessageWhisper {
    pub recipient: String,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Party {
    pub action: u8,
    pub player_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PartyByName {
    pub action: u8,
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AddBuddy {
    pub action: u8,
    pub player_name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Guild {
    pub action: u8,
    pub target_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RequestGuildHistory {
    pub page: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuildUserBuyBuff {
    pub buff_id: u32,
}
