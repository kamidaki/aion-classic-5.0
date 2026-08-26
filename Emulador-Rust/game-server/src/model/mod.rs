//! Subsistema Central de Modelos e Entidades de Domínio (Model - Padrão Java Aion Classic 2.8 / 4.5)

pub mod abyss_rank;
pub mod account;
pub mod announcement;
pub mod broker;
pub mod chat_type;
pub mod craft;
pub mod dialog;
pub mod drop;
pub mod emotion;
pub mod flypath;
pub mod game_engine;
pub mod gameobjects;
pub mod gender;
pub mod items;
pub mod npc_type;
pub mod petition;
pub mod player_class;
pub mod race;
pub mod siege;
pub mod stats;
pub mod team;
pub mod teleport_animation;
pub mod trade;
pub mod tribe_class;

#[cfg(test)]
pub mod tests;

// Re-exportações de tipos fundamentais para uso conveniente
pub use abyss_rank::*;
pub use account::*;
pub use announcement::*;
pub use broker::*;
pub use chat_type::*;
pub use craft::*;
pub use dialog::*;
pub mod model_drop {
    pub use super::drop::*;
}
pub use emotion::*;
pub use flypath::*;
pub use game_engine::*;
pub use gameobjects::*;
pub use gender::*;
pub use items::*;
pub use npc_type::*;
pub use petition::*;
pub use player_class::*;
pub use race::*;
pub use siege::*;
pub use stats::*;
pub use team::*;
pub use teleport_animation::*;
pub mod model_trade {
    pub use super::trade::*;
}
pub use tribe_class::*;
