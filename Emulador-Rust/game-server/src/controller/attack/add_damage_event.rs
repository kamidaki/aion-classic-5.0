//! Evento de Dano Adicional (AddDamageEvent - Padrão Java Aion Classic 2.8 / 4.5)

#[derive(Debug, Clone)]
pub struct AddDamageEvent {
    pub attacker_id: u32,
    pub target_id: u32,
    pub damage: i32,
}

impl AddDamageEvent {
    pub fn new(attacker_id: u32, target_id: u32, damage: i32) -> Self {
        Self {
            attacker_id,
            target_id,
            damage,
        }
    }
}
