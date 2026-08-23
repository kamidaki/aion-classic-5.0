mod channels;
mod config;
mod protocol;

use channels::ChannelManager;
use config::load_config;
use protocol::{ChatClientPacket, ChatServerPackets};
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let _instance_guard = match commons::single_instance::SingleInstanceGuard::acquire(
        "Chat Server",
        "Local\\EmuRust_ChatServer_Mutex",
    ) {
        Some(g) => g,
        None => {
            std::process::exit(1);
        }
    };

    println!("INFO: [ChatServer] Starting Aion Classic Dedicated Chat Server...");


    let cfg_path = "config/launcher.json";
    let cfg = load_config(cfg_path);

    if !cfg.enabled {
        println!("WARN: [ChatServer] Chat server is disabled in configuration.");
        return Ok(());
    }

    let bind_addr = format!("{}:{}", cfg.bind_address, cfg.port);
    let listener = match TcpListener::bind(&bind_addr).await {
        Ok(l) => {
            println!("INFO: [ChatServer] Listening on {}", bind_addr);
            l
        }
        Err(e) => {
            eprintln!("ERROR: [ChatServer] Failed to bind to {}: {}", bind_addr, e);
            return Err(e.into());
        }
    };

    let channel_manager = Arc::new(ChannelManager::new(cfg.anti_flood_messages_per_sec));

    println!("INFO: [ChatServer] Initialized channel manager with {} default channels", 4);
    println!("INFO: [ChatServer] Ready to accept client and inter-server connections.");

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                let mgr = Arc::clone(&channel_manager);
                tokio::spawn(async move {
                    handle_client(socket, addr, mgr).await;
                });
            }
            Err(e) => {
                eprintln!("WARN: [ChatServer] Accept failed: {}", e);
            }
        }
    }
}

async fn handle_client(
    mut socket: TcpStream,
    addr: std::net::SocketAddr,
    channel_manager: Arc<ChannelManager>,
) {
    println!("DEBUG: [ChatServer] New incoming connection from {}", addr);
    let mut buf = [0u8; 4096];
    let mut authenticated_player_id: Option<u32> = None;
    let mut player_name = format!("Player_{}", addr.port());

    loop {
        match socket.read(&mut buf).await {
            Ok(0) => {
                println!("INFO: [ChatServer] Client {} disconnected cleanly", addr);
                break;
            }
            Ok(n) => {
                let data = &buf[..n];
                if let Some(packet) = ChatClientPacket::parse(data) {
                    match packet {
                        ChatClientPacket::Init { client_version } => {
                            println!("DEBUG: [ChatServer] CM_CHAT_INI received from {} (version: {})", addr, client_version);
                            let reply = ChatServerPackets::sm_chat_ini();
                            if let Err(e) = socket.write_all(&reply).await {
                                eprintln!("ERROR: [ChatServer] Failed to send SM_CHAT_INI: {}", e);
                                break;
                            }
                        }
                        ChatClientPacket::PlayerAuth { player_id, token } => {
                            println!("INFO: [ChatServer] PlayerAuth for player_id: {} (token len: {})", player_id, token.len());
                            authenticated_player_id = Some(player_id);
                            player_name = format!("Player_{}", player_id);
                            let reply = ChatServerPackets::sm_player_auth_response(true);
                            let _ = socket.write_all(&reply).await;
                        }
                        ChatClientPacket::ChannelJoin { channel_id } => {
                            println!("DEBUG: [ChatServer] ChannelJoin request for channel_id: {}", channel_id);
                            let reply = ChatServerPackets::sm_channel_response(channel_id, true);
                            let _ = socket.write_all(&reply).await;
                        }
                        ChatClientPacket::ChannelLeave { channel_id } => {
                            println!("DEBUG: [ChatServer] ChannelLeave request for channel_id: {}", channel_id);
                            let reply = ChatServerPackets::sm_channel_response(channel_id, false);
                            let _ = socket.write_all(&reply).await;
                        }
                        ChatClientPacket::ChannelMessage { channel_id, message } => {
                            let pid = authenticated_player_id.unwrap_or(1000);
                            println!("INFO: [ChatServer] Channel {} message from {}: {}", channel_id, player_name, message);
                            if let Err(err) = channel_manager.broadcast(pid, player_name.clone(), channel_id, message.clone()) {
                                println!("WARN: [ChatServer] Broadcast error: {}", err);
                            }
                        }
                        ChatClientPacket::Ping => {
                            // Keepalive ok
                        }
                        ChatClientPacket::Unknown(op) => {
                            println!("DEBUG: [ChatServer] Unknown chat opcode 0x{:02X} from {}", op, addr);
                        }
                    }
                }
            }
            Err(e) => {
                println!("DEBUG: [ChatServer] Socket error from {}: {}", addr, e);
                break;
            }
        }
    }
}
