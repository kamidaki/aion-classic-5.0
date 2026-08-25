//! Pacotes Client de Sistema, Ping, VersionCheck e Pets (CM)

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VersionCheck {
    pub version: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TimeCheck {
    pub client_time: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Ping {
    pub tick_count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LevelReady {
    pub map_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Captcha {
    pub code: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Pet {
    pub pet_id: u32,
    pub action: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PetEmote {
    pub pet_id: u32,
    pub emote_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Disconnect;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Emotion {
    pub emotion_id: u8,
    pub target_obj_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RegisterAutogroup {
    pub instance_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MailRead {
    pub mail_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MailPostman {
    pub recipient: String,
    pub title: String,
    pub body: String,
    pub item_obj_id: u32,
    pub item_count: u32,
    pub kinah: u64,
}
