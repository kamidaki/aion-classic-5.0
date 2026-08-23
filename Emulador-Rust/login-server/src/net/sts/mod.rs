pub mod api;
pub mod protocol;

use api::StsSession;
use crate::db::AuthDb;
use protocol::StsFrame;
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

                                while let Some((frame, consumed)) = StsFrame::parse(&read_buf) {
                                    // Parse HTTP Path
                                    let header_str = String::from_utf8_lossy(&read_buf[..consumed]);
                                    let path = if let Some(line) = header_str.lines().next() {
                                        let parts: Vec<&str> = line.split_whitespace().collect();
                                        if parts.len() >= 2 { parts[1] } else { "/Sts/Ping" }
                                    } else {
                                        "/Sts/Ping"
                                    };

                                    let (reply_xml, seq) = session.handle_request(path, &frame.body);
                                    let reply_frame = StsFrame {
                                        body: reply_xml.into_bytes(),
                                    };
                                    let resp_bytes = reply_frame.encode(seq);
                                    if let Err(e) = socket.write_all(&resp_bytes).await {
                                        eprintln!("ERROR: [LoginServer-STS] Write error: {}", e);
                                        break;
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
