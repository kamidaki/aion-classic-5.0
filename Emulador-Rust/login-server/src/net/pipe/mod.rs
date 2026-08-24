pub mod wyn;

use crate::db::AuthDb;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::thread;
use wyn::NamedPipe;

#[derive(Deserialize, Debug)]
struct RpcRequest {
    id: Option<serde_json::Value>,
    method: String,
}

#[derive(Serialize)]
struct RpcResponse<T> {
    id: serde_json::Value,
    jsonrpc: &'static str,
    result: T,
}

pub fn spawn_named_pipe_provider(pipe_name: &str, db: Arc<AuthDb>, default_user: String) {
    let name = pipe_name.to_string();
    thread::spawn(move || {
        println!("INFO: [GameforgeRPC] Starting internal Named Pipe provider on {}", name);
        loop {
            match NamedPipe::create(&name) {
                Ok(pipe) => {
                    if pipe.accept().is_ok() {
                        println!("INFO: [GameforgeRPC] Named Pipe client connected.");
                        let mut buf = [0u8; 4096];
                        while let Ok(n) = pipe.read(&mut buf) {
                            if n == 0 {
                                break;
                            }
                            if let Ok(raw_json) = std::str::from_utf8(&buf[..n]) {
                                for line in raw_json.lines() {
                                    if line.trim().is_empty() {
                                        continue;
                                    }
                                    if let Ok(req) = serde_json::from_str::<RpcRequest>(line) {
                                        let req_id = req.id.unwrap_or(serde_json::Value::Null);
                                        println!("INFO: [GameforgeRPC] <- RPC Method: '{}'", req.method);
                                        let response_str = handle_rpc_method(&req.method, req_id, &db, &default_user);
                                        println!("INFO: [GameforgeRPC] -> RPC Response: {}", response_str);
                                        let _ = pipe.write_all(response_str.as_bytes());
                                        let _ = pipe.write_all(b"\n");
                                    }
                                }
                            }
                        }
                        println!("INFO: [GameforgeRPC] Named Pipe client disconnected.");
                        pipe.disconnect();
                    }
                }
                Err(e) => {
                    eprintln!("WARN: [GameforgeRPC] Named Pipe create error: {:?}", e);
                    thread::sleep(std::time::Duration::from_millis(500));
                }
            }
        }
    });
}

fn handle_rpc_method(
    method: &str,
    id: serde_json::Value,
    db: &Arc<AuthDb>,
    default_user: &str,
) -> String {
    match method {
        "ClientLibrary.isClientRunning" => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: true,
            };
            serde_json::to_string(&resp).unwrap()
        }
        "ClientLibrary.initSession" => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: "dbe9ab65-3818-4e8b-86c5-93a1387a55f2",
            };
            serde_json::to_string(&resp).unwrap()
        }
        "ClientLibrary.queryGameDisplayLocale" => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: "en_GB",
            };
            serde_json::to_string(&resp).unwrap()
        }
        // O cliente monta a credencial que manda no HQ (porta 13001) a partir desta resposta: na
        // captura do servidor oficial o pacote 0x01 carrega `base64("<guid>:<guid>")`, dois GUIDs.
        // Devolver aqui um blob de 700 caracteres -- como se fazia antes -- faz o cliente receber
        // a saudacao do HQ, desistir de montar a credencial e desconectar, exibindo
        // "Everything is OK. (0)" antes de fechar.
        //
        // O primeiro GUID identifica a conta e e estavel entre sessoes (confirmado: as duas
        // capturas da mesma conta repetem o mesmo valor). Por isso e constante aqui.
        "ClientLibrary.queryAuthorizationCode" => {
            let token = "3C23F526-D59E-4D52-BC82-42BE869ABAA0";
            let _ = db.register_token(token, default_user);
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: token,
            };
            serde_json::to_string(&resp).unwrap()
        }
        "ClientLibrary.queryGameAccountName" => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: default_user,
            };
            serde_json::to_string(&resp).unwrap()
        }
        "ClientLibrary.queryGameAccountNumericId" => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: 10000001,
            };
            serde_json::to_string(&resp).unwrap()
        }
        _ => {
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: serde_json::Value::Null,
            };
            serde_json::to_string(&resp).unwrap()
        }
    }
}
