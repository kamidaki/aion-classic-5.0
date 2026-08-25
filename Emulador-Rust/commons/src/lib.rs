//! Commons library for Aion Classic Rust Emulator.
//!
//! # Modules
//! - [`crypto`]: Cryptographic ciphers (Game XOR cipher, STS protocol cipher)
//! - [`utils`]: Server utilities (Single instance lock, system helpers)

pub mod crypto;
pub mod utils;

// Backward-compatible re-exports for existing modules:
pub use crypto::game;
pub use crypto::sts;
pub use utils::single_instance;
