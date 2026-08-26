//! Status da Missão (QuestStatus - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum QuestStatus {
    #[default]
    None,
    Start,
    Reward,
    Complete,
    Locked,
}

impl QuestStatus {
    pub fn id(&self) -> u8 {
        match self {
            Self::None => 0,
            Self::Start => 1,
            Self::Reward => 2,
            Self::Complete => 3,
            Self::Locked => 4,
        }
    }

    pub fn from_id(id: u8) -> Self {
        match id {
            1 => Self::Start,
            2 => Self::Reward,
            3 => Self::Complete,
            4 => Self::Locked,
            _ => Self::None,
        }
    }
}
