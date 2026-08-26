//! Inter-server communication with GameServer (Port 9021).

pub mod listener;

pub use listener::start_internal_gs_listener;
