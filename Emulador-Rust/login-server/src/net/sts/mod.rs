pub mod api;
pub mod constantes;
pub mod protocol;

use api::StsSession;
use crate::db::AuthDb;
use protocol::{encode_reply, StsRequest};
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

pub async fn run_sts_server(bind_addr: &str, db: Arc<AuthDb>, dev_user: String) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("INFO: [LoginServer-STS] Listening on {}", bind_addr);

    loop {
        match listener.accept().await {
            Ok((mut socket, addr)) => {
                println!("INFO: [LoginServer-STS] Incoming client connection from {}", addr);
                let db_clone = Arc::clone(&db);
                let user_clone = dev_user.clone();
                tokio::spawn(async move {
                    let mut session = StsSession::new(db_clone, user_clone);
                    let mut buf = [0u8; 8192];
                    let mut read_buf = Vec::new();

                    loop {
                        match socket.read(&mut buf).await {
                            Ok(0) => {
                                println!("INFO: [LoginServer-STS] Connection closed by {}", addr);
                                break;
                            }
                            Ok(n) => {
                                read_buf.extend_from_slice(&buf[..n]);

                                while let Some((req, consumed)) = StsRequest::parse(&read_buf) {
                                    // Nem toda rota tem resposta: o servidor oficial fica calado
                                    // no /Sts/Connect.
                                    if let Some((corpo, seq)) = session.handle_request(&req) {
                                        let resp = encode_reply(&corpo, seq);
                                        if let Err(e) = socket.write_all(&resp).await {
                                            eprintln!("ERROR: [LoginServer-STS] Write error: {}", e);
                                            break;
                                        }
                                        println!(
                                            "INFO: [LoginServer-STS] -> {} ({} bytes, s={}R)",
                                            req.path, corpo.len(), seq
                                        );
                                    }

                                    read_buf.drain(..consumed);
                                }
                            }
                            Err(e) => {
                                eprintln!("ERROR: [LoginServer-STS] Read error from {}: {}", addr, e);
                                break;
                            }
                        }
                    }
                });
            }
            Err(e) => {
                eprintln!("WARN: [LoginServer-STS] Accept error: {}", e);
            }
        }
    }
}
