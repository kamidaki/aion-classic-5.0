use std::io::{Read, Write};
use std::net::TcpStream;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread::{sleep, spawn};
use std::time::Duration;

#[derive(Debug, Clone)]
pub struct ChatConnectorConfig {
    pub chat_address: String,
    pub server_id: u8,
    pub password: String,
}

pub fn start_chat_connector(config: ChatConnectorConfig) -> Arc<AtomicBool> {
    let is_connected = Arc::new(AtomicBool::new(false));
    let connected_clone = is_connected.clone();

    spawn(move || {
        let mut retry_delay = Duration::from_secs(2);

        loop {
            println!(
                "INFO: [GameServer-ChatConnector] Connecting to ChatServer at {} (ServerID: {}, Password: '{}')...",
                config.chat_address, config.server_id, config.password
            );

            match TcpStream::connect(&config.chat_address) {
                Ok(mut stream) => {
                    let _ = stream.set_read_timeout(Some(Duration::from_secs(10)));
                    let _ = stream.set_write_timeout(Some(Duration::from_secs(5)));

                    // Build CM_CS_AUTH packet
                    let pass_bytes = config.password.as_bytes();
                    let mut payload = Vec::new();
                    payload.push(0x01); // opcode CM_CS_AUTH
                    payload.push(config.server_id);
                    payload.extend_from_slice(&(pass_bytes.len() as u16).to_le_bytes());
                    payload.extend_from_slice(pass_bytes);

                    let pkt_len = (payload.len() + 2) as u16;
                    let mut pkt = Vec::with_capacity(pkt_len as usize);
                    pkt.extend_from_slice(&pkt_len.to_le_bytes());
                    pkt.extend_from_slice(&payload);

                    if let Err(e) = stream.write_all(&pkt) {
                        eprintln!("ERROR: [GameServer-ChatConnector] Failed to send CM_CS_AUTH: {}", e);
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    // Read SM_CS_AUTH_RESPONSE
                    let mut header = [0u8; 2];
                    if stream.read_exact(&mut header).is_err() {
                        eprintln!("ERROR: [GameServer-ChatConnector] Failed to read auth response header from ChatServer");
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    let resp_len = u16::from_le_bytes(header) as usize;
                    if resp_len < 3 {
                        eprintln!("ERROR: [GameServer-ChatConnector] Invalid auth response length: {}", resp_len);
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    let mut resp_body = vec![0u8; resp_len - 2];
                    if stream.read_exact(&mut resp_body).is_err() {
                        eprintln!("ERROR: [GameServer-ChatConnector] Failed to read auth response body");
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    if resp_body[0] == 0x01 {
                        let status = if resp_body.len() > 1 { resp_body[1] } else { 1 };
                        if status == 0 {
                            println!(
                                "INFO: [GameServer-ChatConnector] AUTHENTICATED SUCCESSFULLY with ChatServer! Chat channels ACTIVE."
                            );
                            connected_clone.store(true, Ordering::Relaxed);
                            retry_delay = Duration::from_secs(2);

                            // Heartbeat loop
                            loop {
                                sleep(Duration::from_secs(15));

                                let ping_pkt = [0x03, 0x00, 0x02, 0x00];
                                if stream.write_all(&ping_pkt).is_err() {
                                    eprintln!("WARN: [GameServer-ChatConnector] Heartbeat failed. ChatServer connection lost.");
                                    break;
                                }
                            }
                        } else {
                            eprintln!(
                                "ERROR: [GameServer-ChatConnector] Authentication REJECTED by ChatServer: Wrong Password"
                            );
                            connected_clone.store(false, Ordering::Relaxed);
                            sleep(Duration::from_secs(10));
                            continue;
                        }
                    }
                }
                Err(e) => {
                    println!(
                        "WARN: [GameServer-ChatConnector] Could not connect to ChatServer ({}: {}). Retrying in {:?}...",
                        config.chat_address, e, retry_delay
                    );
                    connected_clone.store(false, Ordering::Relaxed);
                    sleep(retry_delay);
                    retry_delay = (retry_delay * 2).min(Duration::from_secs(15));
                }
            }
        }
    });

    is_connected
}
