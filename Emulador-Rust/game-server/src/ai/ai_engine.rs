//! Orquestrador Central do Motor de IA (AIEngine - Padrão Java Aion Classic 2.8 / 4.5)

use std::collections::HashMap;
use std::time::Instant;

use crate::ai::abstract_ai::AbstractAI;
use crate::ai::aggressive_ai::AggressiveNpcAI;
use crate::ai::ai_name::AIName;
use crate::ai::boss_ai::BossAI;
use crate::ai::event::AIEventType;
use crate::ai::guard_ai::{Faction, GuardAI};
use crate::ai::kisk_ai::KiskAI;
use crate::ai::monster_ai::MonsterAI;
use crate::ai::npc_ai::NpcAI;
use crate::ai::servant_ai::ServantAI;
use crate::ai::state::AIState;
use crate::ai::trap_ai::TrapAI;
use crate::character::Character;
use crate::engine::Coord;
use crate::entity::Entity;
pub use crate::Messages;

/// Instância Concreta de IA associada a uma Entidade
pub enum EntityAI {
    Npc(NpcAI),
    Monster(MonsterAI),
    Aggressive(AggressiveNpcAI),
    Guard(GuardAI),
    Boss(BossAI),
    Trap(TrapAI),
    Servant(ServantAI),
    Kisk(KiskAI),
}

impl EntityAI {
    pub fn get_state(&self) -> AIState {
        match self {
            Self::Npc(ai) => ai.get_state(),
            Self::Monster(ai) => ai.get_state(),
            Self::Aggressive(ai) => ai.get_state(),
            Self::Guard(ai) => ai.get_state(),
            Self::Boss(ai) => ai.get_state(),
            Self::Trap(ai) => ai.get_state(),
            Self::Servant(ai) => ai.get_state(),
            Self::Kisk(ai) => ai.get_state(),
        }
    }

    pub fn handle_event(&mut self, event: AIEventType) {
        match self {
            Self::Npc(ai) => ai.handle_event(event),
            Self::Monster(ai) => ai.handle_event(event),
            Self::Aggressive(ai) => ai.handle_event(event),
            Self::Guard(ai) => ai.handle_event(event),
            Self::Boss(ai) => ai.handle_event(event),
            Self::Trap(ai) => ai.handle_event(event),
            Self::Servant(ai) => ai.handle_event(event),
            Self::Kisk(ai) => ai.handle_event(event),
        }
    }

    pub fn think(&mut self, dt: f32) {
        match self {
            Self::Npc(ai) => ai.think(dt),
            Self::Monster(ai) => ai.think(dt),
            Self::Aggressive(ai) => ai.think(dt),
            Self::Guard(ai) => ai.think(dt),
            Self::Boss(ai) => ai.think(dt),
            Self::Trap(ai) => ai.think(dt),
            Self::Servant(ai) => ai.think(dt),
            Self::Kisk(ai) => ai.think(dt),
        }
    }
}

/// Motor Central de IA
pub struct AIEngine {
    pub active_ai: HashMap<u32, EntityAI>,
    pub last_tick: Instant,
}

impl Default for AIEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl AIEngine {
    pub fn new() -> Self {
        Self {
            active_ai: HashMap::new(),
            last_tick: Instant::now(),
        }
    }

    /// Registra uma nova IA para a entidade de acordo com o nome de IA / AIName
    pub fn register_ai(&mut self, entity_id: u32, ai_name: AIName) {
        let ai = match ai_name {
            AIName::Npc | AIName::Postbox | AIName::Portal => EntityAI::Npc(NpcAI::new(entity_id)),
            AIName::Monster => EntityAI::Monster(MonsterAI::new(entity_id, 2.0, 10.0, 1.5)),
            AIName::Aggressive => EntityAI::Aggressive(AggressiveNpcAI::new(entity_id, 2.0, 15.0, 1.5)),
            AIName::Guard => EntityAI::Guard(GuardAI::new(entity_id, Faction::Elyos, 5.0, 20.0)),
            AIName::Boss => EntityAI::Boss(BossAI::new(entity_id, 3.0, 20.0, 2.0)),
            AIName::Trap => EntityAI::Trap(TrapAI::new(entity_id, 0, 3.0, 1001)),
            AIName::Servant | AIName::Totem => EntityAI::Servant(ServantAI::new(entity_id, 0, 1001, 3.0, 30.0)),
            AIName::Kisk => EntityAI::Kisk(KiskAI::new(entity_id, 0, 100, 24)),
            _ => EntityAI::Npc(NpcAI::new(entity_id)),
        };

        self.active_ai.insert(entity_id, ai);
    }

    /// Remove a IA de uma entidade que foi destruída ou despawnada
    pub fn unregister_ai(&mut self, entity_id: u32) {
        self.active_ai.remove(&entity_id);
    }

    /// Dispara um evento de IA para uma entidade específica
    pub fn on_ai_event(&mut self, entity_id: u32, event: AIEventType) {
        if let Some(ai) = self.active_ai.get_mut(&entity_id) {
            ai.handle_event(event);
        }
    }

    /// Ciclo de atualização em tempo real de todas as IAs ativas no mundo
    pub fn tick(
        &mut self,
        now: Instant,
        entities: &mut [Entity],
        characters: &mut HashMap<u32, Character>,
        _messages: &mut Messages,
    ) {
        let dt = now.duration_since(self.last_tick).as_secs_f32().min(1.0);
        self.last_tick = now;

        for entity in entities.iter_mut() {
            let entity_id = entity.id();

            if let Some(ai) = self.active_ai.get_mut(&entity_id) {
                ai.think(dt);

                // Processamento de aggro para monstros agressivos
                if let EntityAI::Aggressive(aggro_ai) = ai {
                    let state = aggro_ai.get_state();
                    if state == AIState::Idle || state == AIState::Walking {
                        for character in characters.values() {
                            let dist = entity.location().distance(character.location());
                            if aggro_ai.check_see_player(character.id(), dist) {
                                entity.set_taget(character.id());
                                break;
                            }
                        }
                    }
                }
            }
        }
    }
}
