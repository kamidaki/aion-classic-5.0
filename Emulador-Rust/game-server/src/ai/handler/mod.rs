//! Módulo de Handlers de Eventos da IA

pub mod activate_handler;
pub mod aggro_handler;
pub mod attack_handler;
pub mod died_handler;
pub mod returning_handler;
pub mod shout_handler;
pub mod talk_handler;
pub mod think_handler;

pub use activate_handler::*;
pub use aggro_handler::*;
pub use attack_handler::*;
pub use died_handler::*;
pub use returning_handler::*;
pub use shout_handler::*;
pub use talk_handler::*;
pub use think_handler::*;
