//! Emoções e Ações Sociais (EmotionType / EmotionId - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum EmotionType {
    #[default]
    SelectTarget,
    Jump,
    Sit,
    Stand,
    ChairSit,
    Fly,
    Land,
    Die,
    Resurrect,
    Emote,
    Windstream,
    WindstreamEnd,
    OpenDoor,
    CloseDoor,
}

impl EmotionType {
    pub fn id(&self) -> u8 {
        match self {
            Self::SelectTarget => 0,
            Self::Jump => 1,
            Self::Sit => 2,
            Self::Stand => 3,
            Self::ChairSit => 4,
            Self::Fly => 5,
            Self::Land => 6,
            Self::Die => 7,
            Self::Resurrect => 8,
            Self::Emote => 9,
            Self::Windstream => 10,
            Self::WindstreamEnd => 11,
            Self::OpenDoor => 12,
            Self::CloseDoor => 13,
        }
    }
}
