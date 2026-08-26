//! Encryption utilities for Aion servers.
//!
//! Submodules:
//! - [`game`]: Game packet XOR stream cipher & opcode encryption/decryption.
//! - [`sts`]: STS login protocol RSA/AES/RC4 encryption.

pub mod game;
pub mod sts;

pub use game as game_crypto;
pub use sts as sts_crypto;
