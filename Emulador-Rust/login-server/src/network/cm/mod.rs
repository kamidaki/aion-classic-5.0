//! Módulo CM (Client → Server) — pacotes recebidos dos clientes.
//!
//! Submodulos por protocolo:
//! - [`ncsoft`] — protocolo NCSoft clássico (porta 2106)
//! - [`hq`]     — protocolo Gameforge HQ (porta 13001)

pub mod ncsoft;
pub mod hq;
