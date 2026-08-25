//! Módulo Central de Mensagens do Cliente (CM)

pub mod auth;
pub mod movement;
pub mod combat;
pub mod inventory;
pub mod trade;
pub mod social;
pub mod quest;
pub mod system;

pub use auth::*;
pub use movement::*;
pub use combat::*;
pub use inventory::*;
pub use trade::*;
pub use social::*;
pub use quest::*;
pub use system::*;

use crate::game::message::client::Message as LegacyMessage;

/// Enum unificado de todas as mensagens recebidas do cliente (CM)
pub type ClientMessage = LegacyMessage;
