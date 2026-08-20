use std::sync::{Arc, Mutex};

use serde::{Deserialize, Serialize};

use super::LauncherState;

mod wyn;

const GAME_LANG: &str = "en-GB";
const PIPE_NAME: &str = "\\\\.\\pipe\\GameforgeClientJSONRPC\0";
const MAX_INSTANCES: u32 = 255;

// ---------------------------------------------------------------------------
// JSON-RPC types
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// RPC dispatch
// ---------------------------------------------------------------------------

fn handle_message(req: &RpcRequest, state: &Arc<Mutex<LauncherState>>) -> String {
    println!("[GCLIENT] RPC ← {}", req.method);

    let result: Option<RpcResult> = match req.method.as_str() {
        // Is the Gameforge client running? We always say yes.
        "ClientLibrary.isClientRunning" => Some(RpcResult::Bool(true)),

        // Echo the session_id back — the game uses this to track its own session.
        "ClientLibrary.initSession" => Some(RpcResult::Str(req.params.session_id.clone())),

        // Display locale for the game client.
        "ClientLibrary.queryGameDisplayLocale" => Some(RpcResult::Str(GAME_LANG.into())),

        // The auth code the client forwards to the STS server.
        // Must match AUTHN_TOKEN in sts-server so the HQ auth flow completes.
        "ClientLibrary.queryAuthorizationCode" => Some(RpcResult::Str(
            "OUUwNTRFODktQzBCRC00NzkyLTlBMjItMzMxMTZEOUVBQkI3OjY3NDA2NzQ4LTI0NTUtNEQxMy1CRUVFLTFGNjc2NDQxRjRFQwA=".into(),
        )),

        // Account display name shown in-game.
        "ClientLibrary.queryGameAccountName" => {
            let s = state.lock().unwrap();
            Some(RpcResult::Str(s.username.clone()))
        }

        // Numeric account ID — derive a stable number from the username.
        "ClientLibrary.queryGameAccountNumericId" => {
            let s = state.lock().unwrap();
            let id = stable_numeric_id(&s.username);
            Some(RpcResult::Str(id))
        }

        method => {
            println!("[GCLIENT] WARN: unknown RPC method '{method}', returning error");
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

/// Derives a stable numeric string ID from a username by hashing it.
/// The Aion client uses this as an opaque account identifier.
fn stable_numeric_id(username: &str) -> String {
    // Simple djb2-style hash → positive decimal string
    let hash = username.bytes().fold(5381u64, |acc, b| {
        acc.wrapping_mul(33).wrapping_add(b as u64)
    });
    (hash % 1_000_000_000).to_string()
}

// ---------------------------------------------------------------------------
// Pipe server
// ---------------------------------------------------------------------------

/// Runs the named-pipe JSON-RPC server that the Aion client connects to.
///
/// Keeps accepting connections and for each connection handles **all** RPC
/// messages until the client disconnects (broken pipe), then waits for the
/// next connection. This "long-lived" loop matches how the real GameForge
/// client behaves — the game sends several calls in one session.
pub fn listen(state: Arc<Mutex<LauncherState>>) {
    println!("[GCLIENT] INFO: pipe server starting on {PIPE_NAME}");

    // O cliente Aion abre uma conexao nova para cada chamada RPC: conecta, pergunta, desconecta.
    // A versao anterior criava a instancia, atendia a sessao inteira, fechava e so entao criava a
    // proxima -- e nesse intervalo o nome do pipe deixava de existir no sistema. Uma conexao que
    // caisse ali recebia "arquivo nao encontrado", e o cliente desistia do fluxo Gameforge e caia
    // no formulario de login manual. Como a janela durava todo o tempo de atendimento, dava certo
    // numa rodada e falhava na seguinte sem nada mudar.
    //
    // Agora a proxima instancia e criada assim que um cliente conecta, antes de atende-lo. O nome
    // nunca some, e conexoes que chegam durante o atendimento ficam enfileiradas em vez de falhar.
    let mut pendente = match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("[GCLIENT] ERROR: CreateNamedPipe failed: {e}");
            return;
        }
    };

    loop {
        println!("[GCLIENT] INFO: waiting for client...");
        if let Err(e) = pendente.listen() {
            eprintln!("[GCLIENT] ERROR: ConnectNamedPipe failed: {e}");
            let _ = pendente.close();
            match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
                Ok(p) => pendente = p,
                Err(e) => {
                    eprintln!("[GCLIENT] ERROR: CreateNamedPipe failed: {e}");
                    std::thread::sleep(std::time::Duration::from_secs(1));
                    continue;
                }
            }
            continue;
        }
        println!("[GCLIENT] INFO: client connected");

        let atual = pendente;
        pendente = match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
            Ok(p) => p,
            Err(e) => {
                eprintln!("[GCLIENT] ERROR: CreateNamedPipe failed: {e}");
                handle_session(&atual, &state);
                let _ = atual.close();
                std::thread::sleep(std::time::Duration::from_secs(1));
                match wyn::Pipe::new(PIPE_NAME, MAX_INSTANCES) {
                    Ok(p) => p,
                    Err(e) => {
                        eprintln!("[GCLIENT] ERROR: CreateNamedPipe failed: {e}");
                        return;
                    }
                }
            }
        };

        handle_session(&atual, &state);
        let _ = atual.close();
    }
}

/// Atende todas as mensagens de uma conexao, ate o cliente desconectar.
fn handle_session(pipe: &wyn::Pipe, state: &Arc<Mutex<LauncherState>>) {
    let mut buffer = [0u8; 10 * 1024];
    loop {
        let len = match pipe.read(&mut buffer) {
            Ok(0) => {
                println!("[GCLIENT] INFO: client disconnected");
                return;
            }
            Ok(n) => n as usize,
            Err(e) => {
                eprintln!("[GCLIENT] ERROR: read failed: {e}");
                return;
            }
        };

        match serde_json::from_slice::<RpcRequest>(&buffer[..len]) {
            Ok(req) => {
                let payload = handle_message(&req, state);
                println!("[GCLIENT] RPC -> {payload}");
                if let Err(e) = pipe.write(payload.as_bytes()) {
                    eprintln!("[GCLIENT] ERROR: write failed: {e}");
                    return;
                }
            }
            Err(e) => {
                eprintln!(
                    "[GCLIENT] WARN: invalid JSON-RPC: {e} | raw: {:?}",
                    std::str::from_utf8(&buffer[..len])
                );
            }
        }
    }
}
