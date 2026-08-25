//! Módulo `network` do Login Server — organização modular equivalente ao Java AionEmu.
//!
//! # Estrutura
//!
//! ```text
//! network/
//! ├── mod.rs         ← este arquivo (ponto de entrada)
//! ├── connection.rs  ← ConnectionState, LoginSession
//! ├── cm/            ← Client → Server packets
//! │   ├── mod.rs
//! │   ├── ncsoft.rs  ← CM_AUTH_GG, CM_LOGIN, CM_PLAY, CM_SERVER_LIST
//! │   └── hq.rs      ← CM_HQ_CREDENTIALS, CM_HQ_SELECT_SERVER
//! └── sm/            ← Server → Client packets (builders)
//!     ├── mod.rs
//!     ├── ncsoft.rs  ← SM_INIT, SM_AUTH_GG, SM_LOGIN_OK, SM_SERVER_LIST, SM_PLAY_OK
//!     └── hq.rs      ← AUTH_GREETING, LOGIN_OK, SERVER_LIST, PLAY_OK
//! ```
//!
//! # Equivalência com Java AionEmu
//!
//! | Java (loginserver)              | Rust                                    |
//! |---------------------------------|-----------------------------------------|
//! | `network/clientpackets/CM_*.java` | `network/cm/ncsoft.rs` + `cm/hq.rs`    |
//! | `network/serverpackets/SM_*.java` | `network/sm/ncsoft.rs` + `sm/hq.rs`    |
//! | `LoginConnection.java`           | `network/connection.rs`                 |
//! | `NCSoftLoginServer.java`         | `net/ncsoft.rs` (implementação)         |
//! | `HQLoginServer.java`             | `net/hq.rs` (implementação)             |

pub mod connection;
pub mod cm;
pub mod sm;

// Re-exportações convenientes para o resto do crate
pub use connection::{ConnectionState, LoginSession};
