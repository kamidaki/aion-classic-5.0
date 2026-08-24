//! Rotas do STS.
//!
//! O cliente Classic EU chama exatamente tres, nesta ordem (identico nas capturas de 21/08 e
//! 23/08 de 2026):
//!
//! | Rota                     | `s:` | Resposta                     |
//! |--------------------------|------|------------------------------|
//! | `/Sts/Connect`           | -    | **nenhuma**                  |
//! | `/Auth/LoginTokenStart`  | 1    | 863 bytes, `s:1R`            |
//! | `/Auth/TokenKeyData`     | 2    | `<Reply/>`, `s:2R`           |
//!
//! Dali em diante o trafego vira AES e sai do alcance da captura.
//!
//! As rotas `/Auth/LoginStart` e `/Auth/RequestGameToken`, que esta implementacao atendia, **nao
//! aparecem em captura nenhuma**. Ficaram no lugar para nao quebrar launcher que as use, mas nao
//! sao o caminho do cliente oficial.

use super::constantes::{SERVER_PUBLIC_KEY, SERVER_SIGNATURE};
use super::protocol::StsRequest;
use crate::db::AuthDb;
use base64::Engine;
use std::sync::Arc;

pub struct StsSession {
    pub authn_token: String,
    pub db: Arc<AuthDb>,
    pub dev_user: String,
}

impl StsSession {
    pub fn new(db: Arc<AuthDb>, dev_user: String) -> Self {
        Self {
            authn_token: dev_user.clone(),
            db,
            dev_user,
        }
    }

    /// Devolve o corpo da resposta e a sequencia a ecoar, ou `None` para ficar calado.
    pub fn handle_request(&mut self, req: &StsRequest) -> Option<(String, u32)> {
        let body_str = String::from_utf8_lossy(&req.body);
        let seq = req.seq.unwrap_or(0);
        println!(
            "INFO: [LoginServer-STS] <- {} (s={:?}, {} bytes)",
            req.path,
            req.seq,
            req.body.len()
        );

        match req.path.as_str() {
            // O servidor oficial nao responde a esta rota. Responder aqui adianta a sequencia e
            // desencontra tudo que vem depois.
            "/Sts/Connect" => {
                if let Some(programa) = campo(&body_str, "Program") {
                    println!("INFO: [LoginServer-STS] Connect do programa {programa} (silencio, como o oficial)");
                }
                None
            }

            "/Auth/LoginTokenStart" => {
                let client_rand = campo(&body_str, "ClientRand").unwrap_or_default();
                println!(
                    "INFO: [LoginServer-STS] LoginTokenStart, ClientRand de {} chars",
                    client_rand.len()
                );
                Some((resposta_login_token_start(&server_rand()), seq))
            }

            "/Auth/TokenKeyData" => {
                if let Some(provedor) = campo(&body_str, "AuthProviderCode") {
                    println!("INFO: [LoginServer-STS] TokenKeyData do provedor '{provedor}'");
                }
                Some(("<Reply/>\n".to_string(), seq))
            }

            // --- rotas que o cliente oficial nao usa, mantidas para launchers alternativos ---
            "/Auth/LoginStart" => {
                let mut username = self.dev_user.clone();
                if let Some(raw) = campo(&body_str, "LoginName") {
                    if !raw.trim().is_empty() {
                        username = raw.split('@').next().unwrap_or(&raw).to_string();
                    }
                }

                println!("INFO: [LoginServer-STS] /Auth/LoginStart (fora do fluxo oficial) para '{username}'");
                self.authn_token = username.clone();
                let _ = self.db.get_or_create_account(&username, true);

                let xml = format!(
                    r#"<Reply><UserId>46CF859A-0426-47BD-A95A-563A78BB07D4</UserId><UserStatus>1</UserStatus><Created>2023-04-25T10:47:54Z</Created><UserMarketCode>22</UserMarketCode><UserCenter>22</UserCenter><LoginName>{}@local</LoginName><UserName>{}</UserName><IsLoginNameValidated>0</IsLoginNameValidated><LoginCenter>22</LoginCenter><GameAccountId>10000001</GameAccountId><AccessMask>134217727</AccessMask><Session>6D5F3085-362A-4D6D-9010-D9C8F7CBEB16</Session><LocationId>6D5F3085-362A-4D6D-9010-D9C8F7CBEB16</LocationId><UserCredentialCode>gameforge</UserCredentialCode><ExternalAccounts><ExternalAccount><AuthProviderCode>gameforge</AuthProviderCode><ExternalAccountKey>dbe9ab65-3818-4e8b-86c5-93a1387a55f2</ExternalAccountKey><ExternalAccountName>{}</ExternalAccountName></ExternalAccount></ExternalAccounts></Reply>"#,
                    username, username, username
                );
                Some((xml, seq))
            }

            "/Auth/RequestGameToken" => {
                let username = if self.authn_token.is_empty() {
                    self.dev_user.clone()
                } else {
                    self.authn_token.clone()
                };

                let acc_id = match self.db.get_or_create_account(&username, true) {
                    Ok(Some(a)) => a.id as u32,
                    _ => 1,
                };
                // Chave sorteada por sessao, como o HQ faz. Antes ia um 0x026EDF39 fixo -- que e o
                // id de conta que aparece na captura do servidor oficial, nao uma chave.
                let session_key: u32 = rand::random();
                let token = self
                    .db
                    .issue_session(acc_id, &username, session_key)
                    .unwrap_or_else(|_| "6D5F3085".to_string());
                println!("INFO: [LoginServer-STS] GameToken '{token}' para '{username}'");
                Some((format!(r#"<Reply><GameToken>{token}</GameToken></Reply>"#), seq))
            }

            "/Sts/Ping" => Some(("<Reply/>\n".to_string(), seq)),

            "/Auth/LogoutMyClient" => {
                println!("INFO: [LoginServer-STS] Client logged out");
                Some(("<Reply/>\n".to_string(), seq))
            }

            outra => {
                println!("WARN: [LoginServer-STS] Rota nao tratada: '{outra}'");
                Some(("<Reply/>\n".to_string(), seq))
            }
        }
    }
}

/// Le `<Tag>conteudo</Tag>` do corpo, sem montar um parser de XML inteiro para tres campos.
fn campo(xml: &str, tag: &str) -> Option<String> {
    let abre = format!("<{tag}>");
    let fecha = format!("</{tag}>");
    let i = xml.find(&abre)? + abre.len();
    let j = xml[i..].find(&fecha)? + i;
    Some(xml[i..j].to_string())
}

/// 32 bytes aleatorios em base64 -- 44 caracteres, o tamanho que o servidor oficial manda.
fn server_rand() -> String {
    let bytes: [u8; 32] = rand::random();
    base64::engine::general_purpose::STANDARD.encode(bytes)
}

/// Monta a resposta do `/Auth/LoginTokenStart`.
///
/// Dos tres campos, so o `ServerRand` muda entre sessoes; a chave publica e a assinatura chegam
/// identicas nas duas capturas, entao vao das constantes. Com um `ServerRand` de 44 caracteres o
/// corpo fecha em 863 bytes, o mesmo tamanho da captura.
fn resposta_login_token_start(server_rand: &str) -> String {
    format!(
        "<Reply>\n\
         <ServerRand>{server_rand}</ServerRand>\n\
         <ServerPublicKey>{SERVER_PUBLIC_KEY}</ServerPublicKey>\n\
         <ServerSignature>{SERVER_SIGNATURE}</ServerSignature>\n\
         </Reply>\n"
    )
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn a_resposta_do_login_token_start_tem_o_tamanho_da_captura() {
        // Na captura: l:863, com ServerRand de 44 caracteres.
        let corpo = resposta_login_token_start("5jEASIljaA5MFXWCBFfVR2zUzIyc9/TWw70JTpKopfk=");
        assert_eq!(corpo.len(), 863);
        assert!(corpo.starts_with("<Reply>\n<ServerRand>"));
        assert!(corpo.ends_with("</ServerSignature>\n</Reply>\n"));
    }

    #[test]
    fn o_server_rand_tem_44_caracteres_e_muda_a_cada_chamada() {
        let a = server_rand();
        let b = server_rand();
        assert_eq!(a.len(), 44);
        assert_eq!(b.len(), 44);
        assert_ne!(a, b, "ServerRand e material de sessao, nao pode repetir");
        // E com ele o corpo continua fechando no tamanho da captura.
        assert_eq!(resposta_login_token_start(&a).len(), 863);
    }

    #[test]
    fn as_constantes_decodificam_no_tamanho_certo() {
        let eng = base64::engine::general_purpose::STANDARD;
        let pk = eng.decode(SERVER_PUBLIC_KEY).expect("base64 valido");
        assert_eq!(pk.len(), 268, "u32 tipo + u32 expoente + u32 tamanho + modulo[256]");
        assert_eq!(u32::from_le_bytes(pk[4..8].try_into().unwrap()), 65537, "expoente");
        assert_eq!(u32::from_le_bytes(pk[8..12].try_into().unwrap()), 256, "tamanho do modulo");

        assert_eq!(eng.decode(SERVER_SIGNATURE).expect("base64 valido").len(), 256);
    }

    #[test]
    fn campo_le_o_conteudo_da_tag() {
        assert_eq!(campo("<Request><ClientRand>abc</ClientRand></Request>", "ClientRand").as_deref(), Some("abc"));
        assert_eq!(campo("<Connect> <Program>3092</Program> </Connect>", "Program").as_deref(), Some("3092"));
        assert_eq!(campo("<Reply/>", "Program"), None);
    }
}
