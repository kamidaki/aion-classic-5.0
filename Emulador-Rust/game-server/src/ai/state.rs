//! Estados da Máquina de Estados Finita da IA (AI FSM States)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AIState {
    Created,
    Idle,
    Walking,
    Thinking,
    Attacking,
    Evading,
    Returning,
    Dead,
    Following,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AISubState {
    None,
    Casting,
    Stunned,
    Sleeping,
    Rooted,
    Feared,
}
