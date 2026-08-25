//! Motor Central de Inteligência Artificial (AI Engine) - Padrão Java Aion Classic 2.8 / 4.5

pub mod abstract_ai;
pub mod aggressive_ai;
pub mod ai_engine;
pub mod ai_name;
pub mod ai_request;
pub mod attack_intention;
pub mod boss_ai;
pub mod guard_ai;
pub mod hate_table;
pub mod kisk_ai;
pub mod monster_ai;
pub mod npc_ai;
pub mod servant_ai;
pub mod state;
pub mod trap_ai;

// Submódulos organizados
pub mod event;
pub mod follow;
pub mod handler;
pub mod manager;
pub mod poll;
pub mod scenario;

#[cfg(test)]
pub mod tests;

// Re-exportações de alta conveniência e compatibilidade
pub use abstract_ai::{AbstractAI, BaseAI};
pub use aggressive_ai::AggressiveNpcAI;
pub use ai_engine::{AIEngine, EntityAI};
pub use ai_name::AIName;
pub use ai_request::AIRequest;
pub use attack_intention::AttackIntention;
pub use boss_ai::{BossAI, BossPhase};
pub use event::{AIEvent, AIEventListener, AIEventLog, AIEventType};
pub use follow::{FollowStartService, FollowSummonTaskAI};
pub use guard_ai::{Faction, GuardAI};
pub use handler::{
    ActivateEventHandler, AggroEventHandler, AttackEventHandler, DiedEventHandler,
    ReturningEventHandler, ShoutEventHandler, TalkEventHandler, ThinkEventHandler,
};
pub use hate_table::{HateEntry, HateTable};
pub use kisk_ai::KiskAI;
pub use manager::{
    AttackManager, EmoteManager, FollowManager, NpcEmote, SkillAttackManager, WalkManager,
};
pub use monster_ai::MonsterAI;
pub use npc_ai::NpcAI;
pub use poll::{AIAnswer, AIQuestion, NpcAIPolls};
pub use scenario::{AIScenario, ScenarioTemplate, WalkScenario};
pub use servant_ai::ServantAI;
pub use state::{AIState, AISubState};
pub use trap_ai::TrapAI;

pub struct AiNames;
impl AiNames {
    pub const NPC: &'static str = "npc";
    pub const MONSTER: &'static str = "monster";
    pub const AGGRESSIVE: &'static str = "aggressive";
    pub const GUARD: &'static str = "guard";
    pub const BOSS: &'static str = "boss";
    pub const TRAP: &'static str = "trap";
    pub const SERVANT: &'static str = "servant";
    pub const TOTEM: &'static str = "totem";
    pub const KISK: &'static str = "kisk";
}
