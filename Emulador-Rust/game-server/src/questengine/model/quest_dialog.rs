//! Identificadores e Enums de Diálogos de Missão (QuestDialog - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum QuestDialog {
    #[default]
    StartDialog,
    AskQuest,
    AcceptQuest,
    RefuseQuest,
    SelectReward,
    SelectReward1,
    SelectReward2,
    SelectReward3,
    SelectReward4,
    FinishDialog,
    UseObject,
    Step1,
    Step2,
    Step3,
    Step4,
    Step5,
    Step6,
    Step7,
    Step8,
    Step9,
    Step10,
    CheckUserHasItem,
    Custom(u32),
}

impl QuestDialog {
    pub fn id(&self) -> u32 {
        match self {
            Self::StartDialog => 10,
            Self::AskQuest => 25,
            Self::AcceptQuest => 10000,
            Self::RefuseQuest => 10001,
            Self::SelectReward => 5,
            Self::SelectReward1 => 6,
            Self::SelectReward2 => 7,
            Self::SelectReward3 => 8,
            Self::SelectReward4 => 9,
            Self::FinishDialog => 20,
            Self::UseObject => 10002,
            Self::Step1 => 1011,
            Self::Step2 => 1012,
            Self::Step3 => 1013,
            Self::Step4 => 1014,
            Self::Step5 => 1015,
            Self::Step6 => 1016,
            Self::Step7 => 1017,
            Self::Step8 => 1018,
            Self::Step9 => 1019,
            Self::Step10 => 1020,
            Self::CheckUserHasItem => 34,
            Self::Custom(id) => *id,
        }
    }

    pub fn from_id(id: u32) -> Self {
        match id {
            10 => Self::StartDialog,
            25 => Self::AskQuest,
            10000 => Self::AcceptQuest,
            10001 => Self::RefuseQuest,
            5 => Self::SelectReward,
            6 => Self::SelectReward1,
            7 => Self::SelectReward2,
            8 => Self::SelectReward3,
            9 => Self::SelectReward4,
            20 => Self::FinishDialog,
            10002 => Self::UseObject,
            1011 => Self::Step1,
            1012 => Self::Step2,
            1013 => Self::Step3,
            1014 => Self::Step4,
            1015 => Self::Step5,
            1016 => Self::Step6,
            1017 => Self::Step7,
            1018 => Self::Step8,
            1019 => Self::Step9,
            1020 => Self::Step10,
            34 => Self::CheckUserHasItem,
            other => Self::Custom(other),
        }
    }
}
