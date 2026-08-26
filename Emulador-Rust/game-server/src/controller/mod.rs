//! Subsistema de Controladores do Servidor de Jogo (com.aionemu.gameserver.controllers)
//!
//! Arquitetura canônica de 1 arquivo por componente:
//! - `attack/` (AttackStatus, AttackResult, AttackUtil, AggroList, etc.)
//! - `effect/` (EffectController, EffectsContainer, PlayerEffectController, etc.)
//! - `movement/` (CreatureMoveController, PlayerMoveController, NpcMoveController, etc.)
//! - `observer/` (ActionObserver, ObserveController, Collision, Shield, FlyRing, etc.)
//! - Controladores especializados: PlayerController, NpcController, MonsterController, etc.

pub mod attack;
pub mod effect;
pub mod movement;
pub mod observer;

pub mod creature_controller;
pub mod fly_controller;
pub mod fly_ring_controller;
pub mod gatherable_controller;
pub mod house_controller;
pub mod monster_controller;
pub mod npc_controller;
pub mod observe_controller;
pub mod pet_controller;
pub mod player_controller;
pub mod road_controller;
pub mod rv_controller;
pub mod shield_controller;
pub mod siege_weapon_controller;
pub mod static_object_controller;
pub mod summon_controller;
pub mod trap_controller;
pub mod visible_object_controller;

pub use creature_controller::*;
pub use fly_controller::*;
pub use fly_ring_controller::*;
pub use gatherable_controller::*;
pub use house_controller::*;
pub use monster_controller::*;
pub use npc_controller::*;
pub use observe_controller::*;
pub use pet_controller::*;
pub use player_controller::*;
pub use road_controller::*;
pub use rv_controller::*;
pub use shield_controller::*;
pub use siege_weapon_controller::*;
pub use static_object_controller::*;
pub use summon_controller::*;
pub use trap_controller::*;
pub use visible_object_controller::*;

#[cfg(test)]
pub mod tests;
