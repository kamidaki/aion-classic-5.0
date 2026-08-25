//! Avaliador de Polls e Perguntas de IA (NpcAIPolls - Padrão Java Aion Classic 2.8 / 4.5)

use crate::ai::poll::answer::AIAnswer;
use crate::ai::poll::question::AIQuestion;
use crate::ai::state::AIState;

pub struct NpcAIPolls;

impl NpcAIPolls {
    pub fn ask(question: AIQuestion, state: AIState) -> AIAnswer {
        match question {
            AIQuestion::CanAttackPlayer => {
                if state.is_in_combat() || state == AIState::Idle || state == AIState::Walking {
                    AIAnswer::Positive
                } else {
                    AIAnswer::Negative
                }
            }
            AIQuestion::CanThink => {
                if state.can_think() {
                    AIAnswer::Positive
                } else {
                    AIAnswer::Negative
                }
            }
            AIQuestion::ShouldDecay => {
                if state == AIState::Dead {
                    AIAnswer::Positive
                } else {
                    AIAnswer::Negative
                }
            }
            _ => AIAnswer::Positive,
        }
    }
}
