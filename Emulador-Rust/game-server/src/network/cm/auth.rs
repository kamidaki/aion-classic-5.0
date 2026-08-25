//! Pacotes Client de Autenticação e Lobby (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CharacterList;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CreateCharacter {
    pub name: String,
    pub aparencia: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckNickname {
    pub name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeleteCharacter {
    pub character_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RestoreCharacter {
    pub character_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EnterWorld {
    pub character_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Quit {
    pub quit_type: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReconnectAuth;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Lobby {
    pub character_id: u32,
}
