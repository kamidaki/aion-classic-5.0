//! Módulo `network` do Chat Server — organização modular equivalente ao Java AionEmu.
//!
//! # Estrutura
//!
//! ```text
//! network/
//! ├── mod.rs          ← este arquivo
//! ├── connection.rs   ← ChatConnectionState
//! ├── cm/             ← Client → Server packets (CM_*)
//! │   └── mod.rs
//! ├── sm/             ← Server → Client packets (SM_*)
//! │   └── mod.rs
//! └── internal/       ← Inter-server GS listener (Port 9021)
//!     └── listener.rs
//! ```

pub mod connection;
pub mod cm;
pub mod sm;
pub mod internal;

pub use connection::ChatConnectionState;
pub use internal::start_internal_gs_listener;
