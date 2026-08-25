//! Módulo SM (Server → Client) — builders de pacotes enviados aos clientes.
//!
//! Submodulos por protocolo:
//! - [`ncsoft`] — protocolo NCSoft clássico (porta 2106): SM_INIT, SM_AUTH_GG, SM_LOGIN_OK, etc.
//! - [`hq`]     — protocolo Gameforge HQ (porta 13001): AUTH_GREETING, LOGIN_OK, etc.

pub mod ncsoft;
pub mod hq;
