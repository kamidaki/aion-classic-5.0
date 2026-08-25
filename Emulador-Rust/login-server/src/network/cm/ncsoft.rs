//! Pacotes Client → Server do protocolo NCSoft (porta 2106).
//!
//! Cada struct representa um pacote recebido do cliente.
//! A nomenclatura segue o padrão do Java AionEmu: CM_<NOME>.

/// CM_AUTH_GG (opcode 0x07) — cliente responde ao SM_INIT com session_id + dados GameGuard.
#[derive(Debug)]
pub struct CmAuthGg {
    pub session_id: u32,
    /// Dados extras do GameGuard (ignorados nesta implementação).
    pub data: Vec<u8>,
}

impl CmAuthGg {
    /// Deserializa o payload decifrado (já sem os 2 bytes de tamanho).
    pub fn from_payload(payload: &[u8]) -> Option<Self> {
        if payload.len() < 5 {
            return None;
        }
        // payload[0] == opcode (0x07), payload[1..5] == session_id
        let session_id = u32::from_le_bytes(payload[1..5].try_into().ok()?);
        Some(Self {
            session_id,
            data: payload[5..].to_vec(),
        })
    }
}

/// CM_LOGIN (opcode 0x0B) — cliente envia credenciais cifradas com RSA.
#[derive(Debug)]
pub struct CmLogin {
    /// Nome de usuário descriptografado do bloco RSA.
    pub username: String,
    /// Senha descriptografada do bloco RSA.
    pub password: String,
    /// Bytes crus para diagnóstico / re-encrypt caso necessário.
    pub raw_rsa_block: Vec<u8>,
}

/// CM_SERVER_LIST (opcode 0x05) — cliente solicita lista de servidores.
#[derive(Debug)]
pub struct CmServerList;

/// CM_PLAY (opcode 0x02) — cliente escolheu um servidor para entrar.
#[derive(Debug)]
pub struct CmPlay {
    pub server_id: u8,
}

impl CmPlay {
    pub fn from_payload(payload: &[u8]) -> Option<Self> {
        // payload[0] == opcode, payload[1] == server_id
        let server_id = *payload.get(1)?;
        Some(Self { server_id })
    }
}
