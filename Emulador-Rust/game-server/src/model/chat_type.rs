//! Tipos de Mensagens de Chat (ChatType - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ChatType {
    #[default]
    Normal,
    Shout,
    Whisper,
    Group,
    Alliance,
    Legion,
    Command,
    System,
    SystemNotice,
    Global,
    Announce,
}

impl ChatType {
    pub fn id(&self) -> u8 {
        match self {
            Self::Normal => 0,
            Self::Shout => 1,
            Self::Whisper => 2,
            Self::Group => 3,
            Self::Alliance => 4,
            Self::Legion => 5,
            Self::Command => 6,
            Self::System => 7,
            Self::SystemNotice => 8,
            Self::Global => 9,
            Self::Announce => 10,
        }
    }

    pub fn from_id(id: u8) -> Self {
        match id {
            0 => Self::Normal,
            1 => Self::Shout,
            2 => Self::Whisper,
            3 => Self::Group,
            4 => Self::Alliance,
            5 => Self::Legion,
            6 => Self::Command,
            7 => Self::System,
            8 => Self::SystemNotice,
            9 => Self::Global,
            10 => Self::Announce,
            _ => Self::Normal,
        }
    }
}
