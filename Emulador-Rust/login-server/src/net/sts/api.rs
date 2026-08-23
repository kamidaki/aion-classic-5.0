use crate::db::AuthDb;
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

    pub fn handle_request(&mut self, path: &str, body: &[u8]) -> (String, u32) {
        let body_str = String::from_utf8_lossy(body);
        println!("INFO: [LoginServer-STS] <- STS Request: '{}' (Body len: {} bytes)", path, body.len());

        match path {
            "/Sts/Connect" => {
                let xml = r#"<Reply><ServerVersion>1</ServerVersion></Reply>"#;
                println!("INFO: [LoginServer-STS] -> Response /Sts/Connect: ServerVersion 1");
                (xml.to_string(), 1)
            }
            "/Auth/LoginStart" => {
                // Extract login name if present
                let mut username = self.dev_user.clone();
                if let Some(start) = body_str.find("<LoginName>") {
                    if let Some(end) = body_str[start..].find("</LoginName>") {
                        let raw = &body_str[start + 11..start + end];
                        if !raw.trim().is_empty() {
                            username = raw.split('@').next().unwrap_or(raw).to_string();
                        }
                    }
                }

                println!("INFO: [LoginServer-STS] Processing /Auth/LoginStart for username '{}'", username);
                self.authn_token = username.clone();
                let _ = self.db.get_or_create_account(&username, true);

                let xml = format!(
                    r#"<Reply><UserId>46CF859A-0426-47BD-A95A-563A78BB07D4</UserId><UserStatus>1</UserStatus><Created>2023-04-25T10:47:54Z</Created><UserMarketCode>22</UserMarketCode><UserCenter>22</UserCenter><LoginName>{}@local</LoginName><UserName>{}</UserName><IsLoginNameValidated>0</IsLoginNameValidated><LoginCenter>22</LoginCenter><GameAccountId>10000001</GameAccountId><AccessMask>134217727</AccessMask><Session>6D5F3085-362A-4D6D-9010-D9C8F7CBEB16</Session><LocationId>6D5F3085-362A-4D6D-9010-D9C8F7CBEB16</LocationId><UserCredentialCode>gameforge</UserCredentialCode><ExternalAccounts><ExternalAccount><AuthProviderCode>gameforge</AuthProviderCode><ExternalAccountKey>dbe9ab65-3818-4e8b-86c5-93a1387a55f2</ExternalAccountKey><ExternalAccountName>{}</ExternalAccountName></ExternalAccount></ExternalAccounts></Reply>"#,
                    username, username, username
                );
                (xml, 1)
            }
            "/Auth/RequestGameToken" => {
                let username = if !self.authn_token.is_empty() {
                    self.authn_token.clone()
                } else {
                    self.dev_user.clone()
                };

                let acc = self.db.get_or_create_account(&username, true);
                let acc_id = match acc {
                    Ok(Some(a)) => a.id as u32,
                    _ => 1,
                };
                let token = self.db.issue_session(acc_id, &username, 0x026edf39).unwrap_or_else(|_| "6D5F3085".to_string());
                println!("INFO: [LoginServer-STS] Issued GameToken '{}' for username '{}'", token, username);
                let xml = format!(r#"<Reply><GameToken>{}</GameToken></Reply>"#, token);
                (xml, 2)
            }
            "/Sts/Ping" => {
                (r#"<Reply/>"#.to_string(), 0)
            }
            "/Auth/LogoutMyClient" => {
                println!("INFO: [LoginServer-STS] Client logged out");
                (r#"<Reply/>"#.to_string(), 2)
            }
            _ => {
                println!("WARN: [LoginServer-STS] Unhandled endpoint: '{}'", path);
                (r#"<Reply/>"#.to_string(), 0)
            }
        }
    }
}
