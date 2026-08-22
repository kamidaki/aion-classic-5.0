use std::sync::Arc;
use serde::{Deserialize, Serialize};

use crate::db::AuthDb;

mod wyn;

const GAME_LANG: &str = "en-GB";
const PIPE_NAME: &str = "\\\\.\\pipe\\GameforgeClientJSONRPC\0";
const MAX_INSTANCES: u32 = 255;
const AUTHN_TOKEN: &str = "NDZDRjg1OUEtMDQyNi00N0JELUE5NUEtNTYzQTc4QkIwN0Q0OjUzNjUwMUFFLTBDRUUtNDEzNC05NUY1LUIyRUFDQzQzODExQgA=";

#[derive(Deserialize, Debug)]
struct RpcRequest {
    id: usize,
    jsonrpc: String,
    method: String,
    #[serde(default)]
    params: RpcParams,
}

#[derive(Deserialize, Debug, Default)]
struct RpcParams {
    #[serde(rename = "sessionId", default)]
    session_id: String,
}

#[derive(Serialize, Debug)]
struct RpcResponse {
    id: usize,
    jsonrpc: String,
    result: RpcResult,
}

#[derive(Serialize, Debug)]
struct RpcError {
    id: usize,
    jsonrpc: String,
    error: RpcErrorBody,
}

#[derive(Serialize, Debug)]
struct RpcErrorBody {
    code: i32,
    message: String,
}

#[derive(Serialize, Debug)]
#[serde(untagged)]
enum RpcResult {
    Bool(bool),
    Str(String),
}

fn handle_message(req: &RpcRequest, default_username: &str, db: &Arc<AuthDb>) -> String {
    println!("[GameforgeRPC] RPC ← {}", req.method);

    let result: Option<RpcResult> = match req.method.as_str() {
        "ClientLibrary.isClientRunning" => Some(RpcResult::Bool(true)),
        "ClientLibrary.initSession" => Some(RpcResult::Str(req.params.session_id.clone())),
        "ClientLibrary.queryGameDisplayLocale" => Some(RpcResult::Str(GAME_LANG.into())),
        "ClientLibrary.queryAuthorizationCode" => {
            // Auto register the session with default dev account
            let _ = db.get_or_create_account(default_username, true);
            let _ = db.register_session(AUTHN_TOKEN, default_username);
            Some(RpcResult::Str(AUTHN_TOKEN.into()))
        }
        "ClientLibrary.queryGameAccountName" => Some(RpcResult::Str(default_username.to_string())),
        "ClientLibrary.queryGameAccountNumericId" => {
            let id = stable_numeric_id(default_username);
            Some(RpcResult::Str(id))
        }
        method => {
            println!("[GameforgeRPC] WARN: unknown RPC method '{method}', returning error");
            None
        }
    };

    match result {
        Some(r) => {
            let response = RpcResponse {
                id: req.id,
                jsonrpc: req.jsonrpc.clone(),
                result: r,
            };
            serde_json::to_string(&response).unwrap()
        }
        None => {
            let err = RpcError {
                id: req.id,
                jsonrpc: req.jsonrpc.clone(),
                error: RpcErrorBody {
                    code: -32601,
                    message: format!("method not found: {}", req.method),
                },
            };
            serde_json::to_string(&err).unwrap()
        }
    }
}

fn stable_numeric_id(username: &str) -> String {
    let hash = username.bytes().fold(5381u64, |acc, b| {
        acc.wrapping_mul(33).wrapping_add(b as u64)
    });
    (hash % 1_000_000_000).to_string()
}

pub fn start_pipe_server(default_username: String, db: Arc<AuthDb>) {
    std::thread::spawn(move || {
        println!("[GameforgeRPC] Starting internal Named Pipe provider on {PIPE_NAME}");
        let mut pendente = match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
            Ok(p) => p,
            Err(e) => {
                eprintln!("[GameforgeRPC] ERROR: CreateNamedPipe failed: {e}");
                return;
            }
        };

        loop {
            if let Err(e) = pendente.listen() {
                eprintln!("[GameforgeRPC] ERROR: ConnectNamedPipe failed: {e}");
                let _ = pendente.close();
                match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
                    Ok(p) => pendente = p,
                    Err(e) => {
                        eprintln!("[GameforgeRPC] ERROR: CreateNamedPipe failed: {e}");
                        std::thread::sleep(std::time::Duration::from_secs(1));
                        continue;
                    }
                }
                continue;
            }

            let atual = pendente;
            pendente = match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
                Ok(p) => p,
                Err(e) => {
                    eprintln!("[GameforgeRPC] ERROR: CreateNamedPipe failed: {e}");
                    handle_session(&atual, &default_username, &db);
                    let _ = atual.close();
                    std::thread::sleep(std::time::Duration::from_secs(1));
                    match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
                        Ok(p) => p,
                        Err(e) => {
                            eprintln!("[GameforgeRPC] ERROR: CreateNamedPipe failed: {e}");
                            return;
                        }
                    }
                }
            };

            let default_username = default_username.clone();
            let db = db.clone();
            std::thread::spawn(move || {
                handle_session(&atual, &default_username, &db);
                let _ = atual.close();
            });
        }
    });
}

fn handle_session(pipe: &wyn::Pipe, default_username: &str, db: &Arc<AuthDb>) {
    let mut buffer = [0u8; 10 * 1024];
    loop {
        let len = match pipe.read(&mut buffer) {
            Ok(0) => return,
            Ok(n) => n as usize,
            Err(e) => {
                eprintln!("[GameforgeRPC] ERROR: read failed: {e}");
                return;
            }
        };

        match serde_json::from_slice::<RpcRequest>(&buffer[..len]) {
            Ok(req) => {
                let payload = handle_message(&req, default_username, db);
                if let Err(e) = pipe.write(payload.as_bytes()) {
                    eprintln!("[GameforgeRPC] ERROR: write failed: {e}");
                    return;
                }
            }
            Err(e) => {
                eprintln!(
                    "[GameforgeRPC] WARN: invalid JSON-RPC: {e} | raw: {:?}",
                    std::str::from_utf8(&buffer[..len])
                );
            }
        }
    }
}
