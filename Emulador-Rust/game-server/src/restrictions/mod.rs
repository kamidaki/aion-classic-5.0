//! Subsistema de Restrições (Restrictions Subsystem).
//! Baseado 100% nas regras do Aion Classic (2.4 / 2.8 / 4.5).

pub mod types;
pub mod restrictions;
pub mod player_restrictions;
pub mod prison_restrictions;
pub mod shutdown_restrictions;
pub mod manager;

#[cfg(test)]
pub mod tests;

pub use types::{
    AbnormalState, CreatureState, ItemInfo, PlayerMode, PlayerState, RestrictionError,
    SkillInfo, SkillType, TargetState,
};
pub use restrictions::Restrictions;
pub use player_restrictions::PlayerRestrictions;
pub use prison_restrictions::PrisonRestrictions;
pub use shutdown_restrictions::ShutdownRestrictions;
pub use manager::RestrictionsManager;
