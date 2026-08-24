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
    /// Argumentos da chamada. Ficavam descartados -- o cliente pode mandar aqui o que decide o
    /// que devolvemos, e sem registrar nao da para saber.
    #[serde(default)]
    params: Option<serde_json::Value>,
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
                        let mut seq = 0u32;
                        while let Ok(n) = pipe.read(&mut buf) {
                            if n == 0 {
                                break;
                            }
                            match std::str::from_utf8(&buf[..n]) {
                                Ok(raw_json) => {
                                    // O bloco cru, antes de qualquer parse. Se o cliente mandar
                                    // algo que nao entendemos, e aqui que aparece.
                                    println!("DEBUG: [GameforgeRPC] <- {n} bytes crus: {raw_json:?}");
                                    for line in raw_json.lines() {
                                        if line.trim().is_empty() {
                                            continue;
                                        }
                                        match serde_json::from_str::<RpcRequest>(line) {
                                            Ok(req) => {
                                                let req_id = req.id.unwrap_or(serde_json::Value::Null);
                                                seq += 1;
                                                let params = req
                                                    .params
                                                    .as_ref()
                                                    .map(|p| p.to_string())
                                                    .unwrap_or_else(|| "(ausente)".to_string());
                                                println!(
                                                    "INFO: [GameforgeRPC] <- #{seq} '{}' id={req_id} params={params}",
                                                    req.method
                                                );
                                                let response_str = handle_rpc_method(&req.method, req_id, &db, &default_user);
                                                println!("INFO: [GameforgeRPC] -> #{seq} {response_str}");
                                                let _ = pipe.write_all(response_str.as_bytes());
                                                let _ = pipe.write_all(b"\n");
                                            }
                                            // Antes isso era descartado sem dizer nada, e o cliente
                                            // ficava esperando uma resposta que nunca vinha.
                                            Err(e) => eprintln!(
                                                "WARN: [GameforgeRPC] <- LINHA NAO ENTENDIDA ({e}): {line:?}"
                                            ),
                                        }
                                    }
                                }
                                Err(e) => eprintln!(
                                    "WARN: [GameforgeRPC] <- {n} bytes que nao sao UTF-8 ({e}): {:02X?}",
                                    &buf[..n.min(64)]
                                ),
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
        // Token de autorizacao do pipe. NAO e a credencial do HQ.
        //
        // Ja foi trocado por um GUID, no raciocinio de que a captura do HQ mostra
        // `base64("<guid>:<guid>")` no pacote 0x01. Isso confundiu duas coisas diferentes: aquilo
        // e o que o cliente MANDA na porta 13001, e este e o que ele PEDE ao pipe -- ele pode
        // transformar um no outro.
        //
        // Medido: o formato daqui muda o caminho que o cliente toma. Com o blob ele segue para
        // `queryGameAccountNumericId`; com um GUID ele pede `queryGameAccountName` e para de
        // chamar. Por isso o valor original volta.
        "ClientLibrary.queryAuthorizationCode" => {
            let token = "KwfobiQm1RjVyDpaBPeU3j04a632BamHjvQOx5GHCrSMClictcZSGEIPsRnDkh55Lh2L2IK5hLbq2VejEESJoJ0avallkElflKzr8lCn48AnemMhrV8H5NgqJTqUQnRd1G7kOZJedjanqmIY5Md3Bm5mbkfIUUT5i5Zf8ghhiGJuJLF19mEIiMDTI7kqTyvzkKog3MYuaYeC8AyodHTQXjRD9VWtTh9xCIaaiX5satDdEM91SfGA2hN8C4CeOfdvoVPlvPn3RnFCRWIhrxVse9BkhhE0TdzY5ba3iZBwKMJL8VFbJhNKDgMNIYY8mQmQPTdq7zhWmoUDgTXzOQm3iIcWEMdCqXQlNd2tO71idBAdkQIhblxd1tAS1FH7biGcudAX4OZiOeRfYyHnYIJUDmDd8Lt79WhXjXPO5iynzXQqanEFYu88wnAUay1sN7FaJY2lOAMPgG8BX4Dy5ZLnzvl0K6qRxMWkbiJIcFdfQO5G5hLC72H8n0p1laH2uxZt";
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
        // Devolver `null` a um metodo que o cliente precisa e tao ruim quanto nao responder, e
        // sem este aviso passa despercebido.
        outro => {
            eprintln!("WARN: [GameforgeRPC] metodo SEM implementacao: '{outro}' -- respondendo null");
            let resp = RpcResponse {
                id,
                jsonrpc: "2.0",
                result: serde_json::Value::Null,
            };
            serde_json::to_string(&resp).unwrap()
        }
    }
}
