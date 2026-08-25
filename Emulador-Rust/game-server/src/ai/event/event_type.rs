//! Tipos de Eventos de IA (AIEventType / AIEvent - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AIEventType {
    Spawn,
    Respawn,
    Despawn,
    Died,
    Attacked,
    AttackComplete,
    TargetChanged,
    TargetTooFar,
    NotAtHome,
    BackHome,
    Activate,
    Deactivate,
    Freeze,
    Unfreeze,
    MoveValidate,
    MoveArrived,
    FollowStart,
    FollowStop,
    Talk,
    CustomEvent,
}

pub type AIEvent = AIEventType;
