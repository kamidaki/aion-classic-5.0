//! Estrutura Base de IA Comportamental (AbstractAI / BaseAI - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::event::AIEventType;
use crate::ai::hate_table::HateTable;
use crate::ai::state::{AIState, AISubState};

pub trait AbstractAI: Send + Sync {
    fn get_state(&self) -> AIState;
    fn set_state(&mut self, state: AIState);
    fn get_sub_state(&self) -> AISubState;
    fn set_sub_state(&mut self, sub_state: AISubState);
    fn handle_event(&mut self, event: AIEventType);
    fn think(&mut self, dt: f32);
}

#[derive(Debug, Clone)]
pub struct BaseAI {
    pub object_id: u32,
    pub state: AIState,
    pub sub_state: AISubState,
    pub hate_table: HateTable,
    pub target_id: Option<u32>,
    pub attack_range: f32,
    pub aggro_range: f32,
}

impl BaseAI {
    pub fn new(object_id: u32, attack_range: f32, aggro_range: f32) -> Self {
        Self {
            object_id,
            state: AIState::Created,
            sub_state: AISubState::None,
            hate_table: HateTable::new(),
            target_id: None,
            attack_range,
            aggro_range,
        }
    }
}
