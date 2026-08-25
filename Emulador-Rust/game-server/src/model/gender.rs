//! Gênero de Personagens e NPCs (Gender - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Gender {
    #[default]
    Male,
    Female,
}

impl Gender {
    pub fn id(&self) -> u8 {
        match self {
            Self::Male => 0,
            Self::Female => 1,
        }
    }

    pub fn from_id(id: u8) -> Self {
        if id == 1 {
            Self::Female
        } else {
            Self::Male
        }
    }
}
