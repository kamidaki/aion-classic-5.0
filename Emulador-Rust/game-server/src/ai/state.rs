//! Estados da Máquina de Estados Finita da IA (AIState / AISubState - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AIState {
    #[default]
    Created,
    Spawned,
    Idle,
    Walking,
    Talking,
    Following,
    Attacking,
    Thinking,
    Evading,
    Returning,
    Dead,
    Despawned,
}

impl AIState {
    pub fn is_in_combat(self) -> bool {
        matches!(self, Self::Attacking | Self::Evading)
    }

    pub fn can_move(self) -> bool {
        !matches!(self, Self::Dead | Self::Despawned | Self::Talking)
    }

    pub fn can_think(self) -> bool {
        !matches!(self, Self::Dead | Self::Despawned)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum AISubState {
    #[default]
    None,
    Casting,
    WalkWait,
    TalkWait,
    Freeze,
    Stunned,
    Sleeping,
    Rooted,
    Feared,
}
