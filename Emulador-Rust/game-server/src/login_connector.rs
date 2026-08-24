use std::io::{Read, Write};
use std::net::TcpStream;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread::{sleep, spawn};
use std::time::Duration;

#[derive(Debug, Clone)]
pub struct LoginConnectorConfig {
    pub login_address: String,
    pub server_id: u8,
    pub game_port: u16,
    pub max_players: u32,
    pub password: String,
}

pub fn start_login_connector(config: LoginConnectorConfig) -> Arc<AtomicBool> {
    let is_connected = Arc::new(AtomicBool::new(false));
    let connected_clone = is_connected.clone();

    spawn(move || {
        let mut retry_delay = Duration::from_secs(2);

        loop {
            println!(
                "INFO: [GameServer-LoginConnector] Connecting to LoginServer at {} (ServerID: {}, Password: '{}')...",
                config.login_address, config.server_id, config.password
            );

            match TcpStream::connect(&config.login_address) {
                Ok(mut stream) => {
                    let _ = stream.set_read_timeout(Some(Duration::from_secs(10)));
                    let _ = stream.set_write_timeout(Some(Duration::from_secs(5)));

                    // Build CM_GS_AUTH packet
                    let pass_bytes = config.password.as_bytes();
                    let mut payload = Vec::new();
                    payload.push(0x01); // opcode CM_GS_AUTH
                    payload.push(config.server_id);
                    payload.extend_from_slice(&config.game_port.to_le_bytes());
                    payload.extend_from_slice(&config.max_players.to_le_bytes());
                    payload.extend_from_slice(&(pass_bytes.len() as u16).to_le_bytes());
                    payload.extend_from_slice(pass_bytes);

                    let pkt_len = (payload.len() + 2) as u16;
                    let mut pkt = Vec::with_capacity(pkt_len as usize);
                    pkt.extend_from_slice(&pkt_len.to_le_bytes());
                    pkt.extend_from_slice(&payload);

                    if let Err(e) = stream.write_all(&pkt) {
                        eprintln!("ERROR: [GameServer-LoginConnector] Failed to send CM_GS_AUTH: {}", e);
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    // Read SM_GS_AUTH_RESPONSE
                    let mut header = [0u8; 2];
                    if stream.read_exact(&mut header).is_err() {
                        eprintln!("ERROR: [GameServer-LoginConnector] Failed to read auth response header from LoginServer");
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    let resp_len = u16::from_le_bytes(header) as usize;
                    if resp_len < 3 {
                        eprintln!("ERROR: [GameServer-LoginConnector] Invalid auth response length: {}", resp_len);
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    let mut resp_body = vec![0u8; resp_len - 2];
                    if stream.read_exact(&mut resp_body).is_err() {
                        eprintln!("ERROR: [GameServer-LoginConnector] Failed to read auth response body");
                        connected_clone.store(false, Ordering::Relaxed);
                        sleep(retry_delay);
                        continue;
                    }

                    if resp_body[0] == 0x01 {
                        let status = if resp_body.len() > 1 { resp_body[1] } else { 1 };
                        if status == 0 {
                            println!(
                                "INFO: [GameServer-LoginConnector] AUTHENTICATED SUCCESSFULLY with LoginServer! GameServer #{} is now ACTIVE.",
                                config.server_id
                            );
                            connected_clone.store(true, Ordering::Relaxed);
                            retry_delay = Duration::from_secs(2);

                            // Heartbeat loop
                            loop {
                                sleep(Duration::from_secs(15));

                                // CM_GS_PONG / Heartbeat packet
                                let ping_pkt = [0x03, 0x00, 0x02, 0x00];
                                if stream.write_all(&ping_pkt).is_err() {
                                    eprintln!("WARN: [GameServer-LoginConnector] Heartbeat failed. LoginServer connection lost.");
                                    break;
                                }
                            }
                        } else {
                            eprintln!(
                                "ERROR: [GameServer-LoginConnector] Authentication REJECTED by LoginServer: Wrong Password or Unauthorized ServerID"
                            );
                            connected_clone.store(false, Ordering::Relaxed);
                            sleep(Duration::from_secs(10));
                            continue;
                        }
                    }
                }
                Err(e) => {
                    println!(
                        "WARN: [GameServer-LoginConnector] Could not connect to LoginServer ({}: {}). Retrying in {:?}...",
                        config.login_address, e, retry_delay
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
