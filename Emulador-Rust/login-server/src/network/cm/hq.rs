//! Pacotes Client → Server do protocolo Gameforge HQ (porta 13001).
//!
//! Cada struct representa um pacote recebido do cliente.

/// CM_HQ_CREDENTIALS (opcode 0x01) — cliente envia credenciais em base64.
#[derive(Debug)]
pub struct CmHqCredentials {
    /// Token ou credenciais base64 enviados pelo cliente HQ.
    pub credentials: Vec<u8>,
}

/// CM_HQ_SELECT_SERVER (opcode 0x02) — cliente escolheu um servidor na lista HQ.
#[derive(Debug)]
pub struct CmHqSelectServer {
    pub server_id: u32,
}

impl CmHqSelectServer {
    pub fn from_payload(payload: &[u8]) -> Option<Self> {
        if payload.len() < 5 {
            return None;
        }
        let server_id = u32::from_le_bytes(payload[1..5].try_into().ok()?);
        Some(Self { server_id })
    }
}
