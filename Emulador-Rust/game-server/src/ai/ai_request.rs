//! Requisições Assíncronas de IA (AIRequest - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub enum AIRequest {
    ChangeTarget(u32),
    MoveToLocation(f32, f32, f32),
    UseSkill(u32, u8),
    SayShout(String),
    ReturnHome,
    Despawn,
}
