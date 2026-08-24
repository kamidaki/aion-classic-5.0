//! # ATENCAO: medido, o cliente tambem nao le esta porta
//!
//! O mesmo que acontece na 2106 (ver a nota em `net::ncsoft`) acontece aqui. Medido em 25/08/2026
//! pela janela de recepcao do TCP: o servidor manda os 92 bytes do `AUTH_GREETING`, a janela do
//! cliente cai exatamente 92 e nao se recupera. Ele nao le, nao responde e fecha.
//!
//! O teste foi feito na combinacao que faltava -- `version.dll` instalado e com os patches
//! aplicando, token do pipe no valor original, HQ e STS alinhados com a captura do servidor
//! oficial. Mesmo assim: 92 bytes parados no buffer.
//!
//! ## O que isso estabelece
//!
//! O cliente nao le o socket de login **em nenhuma das duas portas**, com nenhum dos dois
//! protocolos:
//!
//! | porta | protocolo      | recebeu | leu |
//! |-------|----------------|---------|-----|
//! | 2106  | NCSoft/Blowfish| 368 B   | 0   |
//! | 13001 | Gameforge HQ   | 92 B    | 0   |
//!
//! Logo, o bloqueio nao e conteudo de pacote, nem porta, nem escolha de protocolo. Ele abre a
//! conexao e nunca chega ao estado em que a atende. Mexer no que esta abaixo nao muda isso.
//!
//! O layout deste arquivo continua confirmado byte a byte contra a captura do servidor oficial --
//! ver os testes no fim. O que nao esta confirmado e que ele seja suficiente, porque o cliente
//! nunca chegou a le-lo.

//! Protocolo de autenticacao Gameforge HQ (porta 13001).
//!
//! Enquadramento: `[u16 tamanho][u8 opcode][3 bytes zero][payload]`, com o tamanho contando os
//! 6 bytes de cabecalho.
//!
//! A sequencia confirmada contra o servidor oficial da Gameforge (capturas de 21/08 e 23/08 de
//! 2026, cliente Classic EU x64) e:
//!
//! | Sentido | Opcode | Bytes | Papel                                            |
//! |---------|--------|-------|--------------------------------------------------|
//! | S -> C  | `0x05` | 92    | [`AUTH_GREETING`] -- constante                    |
//! | C -> S  | `0x01` | 107   | credenciais em base64, ver [`parse_credentials`]  |
//! | S -> C  | `0x01` | 14    | [`build_login_ok`]                                |
//! | S -> C  | `0x02` | 201   | [`build_server_list`]                             |
//! | C -> S  | `0x02` | 10    | servidor escolhido (u32)                          |
//! | S -> C  | `0x04` | 22    | [`build_play_ok`]                                 |
//!
//! O cliente nunca abre a porta 2106 nesse fluxo: sai daqui direto para o STS (6600) e depois
//! para o game server (7777).

use crate::db::AuthDb;
use base64::Engine;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};

/// Saudacao inicial. Nas duas capturas ela chega **byte a byte identica**, de dias e sessoes
/// diferentes -- e constante do servico, nao um valor de sessao.
///
/// O GUID de aplicacao (`5B4503FA-...`) e o `Program` (0x0C14 = 3092) reaparecem depois no XML
/// `<Connect>` que o cliente manda para o STS na porta 6600.
const AUTH_GREETING: [u8; 92] = [
    0x5c, 0x00, 0x05, 0x00, 0x00, 0x00,
    // auth_key_1: "5B4503FA-8521-4608-BB60-5CFAC87BD63A"
    0x35, 0x42, 0x34, 0x35, 0x30, 0x33, 0x46, 0x41, 0x2d, 0x38, 0x35, 0x32,
    0x31, 0x2d, 0x34, 0x36, 0x30, 0x38, 0x2d, 0x42, 0x42, 0x36, 0x30, 0x2d,
    0x35, 0x43, 0x46, 0x41, 0x43, 0x38, 0x37, 0x42, 0x44, 0x36, 0x33, 0x41,
    0x00,
    // auth_key_2: "7282405F-79E5-49C2-9872-D4F3CC961FF3"
    0x37, 0x32, 0x38, 0x32, 0x34, 0x30, 0x35, 0x46, 0x2d, 0x37, 0x39, 0x45,
    0x35, 0x2d, 0x34, 0x39, 0x43, 0x32, 0x2d, 0x39, 0x38, 0x37, 0x32, 0x2d,
    0x44, 0x34, 0x46, 0x33, 0x43, 0x43, 0x39, 0x36, 0x31, 0x46, 0x46, 0x33,
    0x00,
    // service name: "aiongfc"
    0x61, 0x69, 0x6f, 0x6e, 0x67, 0x66, 0x63, 0x00,
    // Program = 3092
    0x14, 0x0c, 0x00, 0x00,
];

/// Tamanho de uma entrada de servidor dentro do `SERVER_LIST`.
const SERVER_ENTRY_LEN: usize = 63;
/// Offset do campo de IP (ASCII, terminado em zero) dentro da entrada.
const ENTRY_IP_OFFSET: usize = 13;
/// Tamanho do campo de IP.
const ENTRY_IP_LEN: usize = 40;
/// Offset da porta (u16 LE) dentro da entrada.
const ENTRY_PORT_OFFSET: usize = 53;

/// Credenciais que o cliente manda no pacote `0x01`.
///
/// O payload e um base64 terminado em zero que, decodificado, vira `"<user_id>:<session_id>"`.
/// Nas duas capturas o `user_id` e o mesmo -- identifica a conta na Gameforge -- e o `session_id`
/// muda a cada login.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Credentials {
    pub user_id: String,
    pub session_id: String,
}

/// Le o quadro `0x01` do cliente e devolve as credenciais.
///
/// Aceita o formato oficial (`base64("a:b")`) e tambem um token cru, para nao derrubar launchers
/// que mandem outra coisa no lugar. Devolve `None` quando nao ha nada aproveitavel.
///
/// A versao anterior lia a partir do offset 3 e exigia que o texto fosse alfanumerico -- os dois
/// erros juntos faziam todo login cair no usuario padrao, porque o payload comeca no offset 6 e
/// base64 contem `+`, `/` e `=`.
pub fn parse_credentials(frame: &[u8]) -> Option<Credentials> {
    // Pula [u16 tamanho][u8 opcode][3 bytes zero].
    let payload = frame.get(6..)?;
    let fim = payload.iter().position(|&b| b == 0).unwrap_or(payload.len());
    let texto = std::str::from_utf8(&payload[..fim]).ok()?.trim();
    if texto.is_empty() {
        return None;
    }

    let decodificado = base64::engine::general_purpose::STANDARD
        .decode(texto)
        .ok()
        .and_then(|b| String::from_utf8(b).ok());

    let bruto = match decodificado {
        Some(s) => s.trim_end_matches('\0').to_string(),
        None => texto.to_string(),
    };

    match bruto.split_once(':') {
        Some((user, sessao)) if !user.is_empty() => Some(Credentials {
            user_id: user.to_string(),
            session_id: sessao.to_string(),
        }),
        _ => Some(Credentials {
            user_id: bruto,
            session_id: String::new(),
        }),
    }
}

/// `LOGIN_OK` (opcode `0x01`, 14 bytes): resultado zero e o id da conta.
///
/// O id daqui e o mesmo que volta no [`build_play_ok`] e o que o cliente repete para o game
/// server no `C_HQ_LOGIN` (0xF0).
pub fn build_login_ok(account_id: u32) -> Vec<u8> {
    let mut pkt = vec![0x0e, 0x00, 0x01, 0x00, 0x00, 0x00];
    pkt.extend_from_slice(&0u32.to_le_bytes()); // resultado: 0 = ok
    pkt.extend_from_slice(&account_id.to_le_bytes());
    pkt
}

/// Monta uma entrada de 63 bytes do `SERVER_LIST`.
///
/// Layout confirmado na captura:
///
/// ```text
/// [0]      u8   sempre 1
/// [1]      u8   status: 0x04 no servidor jogavel, 0x05 nos demais
/// [2..4]   u16  zero
/// [4]      u8   1 quando a conta tem personagem nesse servidor
/// [5..9]   u32  id do servidor
/// [9..13]  u32  quantidade de personagens
/// [13..53] char ip em ASCII, terminado em zero
/// [53..55] u16  porta
/// [55..63] u8   1 no primeiro byte quando o servidor e o jogavel, resto zero
/// ```
fn build_server_entry(
    server_id: u32,
    ip: &str,
    port: u16,
    char_count: u32,
    jogavel: bool,
) -> [u8; SERVER_ENTRY_LEN] {
    let mut e = [0u8; SERVER_ENTRY_LEN];
    e[0] = 0x01;
    e[1] = if jogavel { 0x04 } else { 0x05 };
    e[4] = jogavel as u8;
    e[5..9].copy_from_slice(&server_id.to_le_bytes());
    e[9..13].copy_from_slice(&char_count.to_le_bytes());

    let ip_bytes = ip.as_bytes();
    // Deixa ao menos um byte zero de terminador dentro do campo.
    let n = ip_bytes.len().min(ENTRY_IP_LEN - 1);
    e[ENTRY_IP_OFFSET..ENTRY_IP_OFFSET + n].copy_from_slice(&ip_bytes[..n]);

    e[ENTRY_PORT_OFFSET..ENTRY_PORT_OFFSET + 2].copy_from_slice(&port.to_le_bytes());
    e[55] = jogavel as u8;
    e
}

/// `SERVER_LIST` (opcode `0x02`, 201 bytes): tres servidores e, no rodape, o id do que o cliente
/// deve trazer pre-selecionado.
///
/// Os dois vizinhos (103 e 121) vao com contagem zero e status `0x05`, como o servidor oficial
/// faz -- o cliente os mostra na lista mas nao entra neles.
pub fn build_server_list(
    announce_ip: &str,
    announce_port: u16,
    server_id: u32,
    char_count: u32,
) -> Vec<u8> {
    let mut pkt = vec![
        0xc9, 0x00, // tamanho = 201
        0x02, 0x00, 0x00, 0x00, // opcode 0x02
        0x03, 0x00, // 3 servidores
    ];
    pkt.extend_from_slice(&build_server_entry(103, "79.110.83.114", 7777, 0, false));
    pkt.extend_from_slice(&build_server_entry(
        server_id,
        announce_ip,
        announce_port,
        char_count,
        true,
    ));
    pkt.extend_from_slice(&build_server_entry(121, "79.110.83.116", 7777, 0, false));
    // Rodape: id do servidor pre-selecionado. Zero aqui deixa a lista sem selecao.
    pkt.extend_from_slice(&server_id.to_le_bytes());
    pkt
}

/// Pacote final do HQ (opcode `0x04`, 22 bytes).
///
/// O ultimo campo e a **chave de sessao**: o cliente a repete intacta para o game server no
/// primeiro pacote autenticado (`C_HQ_LOGIN`, 0xF0) e de novo no `C_SESSION_KEY_ECHO` (0x5E).
/// Por isso precisa ser unica por sessao e estar gravada na tabela `sessions` -- e o unico elo
/// entre o login server e o game server.
pub fn build_play_ok(server_id: u32, account_id: u32, session_key: u32) -> Vec<u8> {
    let mut pkt = vec![
        0x16, 0x00, // tamanho = 22
        0x04, 0x00, 0x00, 0x00, // opcode 0x04
    ];
    pkt.extend_from_slice(&server_id.to_le_bytes());
    pkt.extend_from_slice(&account_id.to_le_bytes());
    pkt.extend_from_slice(&0u32.to_le_bytes()); // codigo de erro: precisa ser zero
    pkt.extend_from_slice(&session_key.to_le_bytes());
    pkt
}

pub async fn run_hq_server(
    bind_addr: &str,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
    security: Arc<crate::security::SecurityManager>,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("INFO: [LoginServer-HQ] Listening on {}", bind_addr);

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                let db_clone = Arc::clone(&db);
                let ip_clone = announce_ip.clone();
                let def_user = default_user.clone();
                let sec_clone = Arc::clone(&security);
                tokio::spawn(async move {
                    handle_hq_client(
                        socket,
                        addr,
                        ip_clone,
                        announce_port,
                        default_server_id,
                        db_clone,
                        auto_create,
                        def_user,
                        sec_clone,
                    )
                    .await;
                });
            }
            Err(e) => {
                eprintln!("WARN: [LoginServer-HQ] Accept error: {}", e);
            }
        }
    }
}

async fn handle_hq_client(
    mut socket: TcpStream,
    addr: std::net::SocketAddr,
    announce_ip: String,
    announce_port: u16,
    default_server_id: u8,
    db: Arc<AuthDb>,
    auto_create: bool,
    default_user: String,
    security: Arc<crate::security::SecurityManager>,
) {
    if !security.check_connection(addr.ip()) {
        println!("WARN: [LoginServer-HQ] Connection from {} rejected by rate-limiter.", addr);
        return;
    }
    println!("INFO: [LoginServer-HQ] Incoming client connection from {}", addr);

    // 1. AUTH_GREETING (92 bytes)
    if let Err(e) = socket.write_all(&AUTH_GREETING).await {
        eprintln!("ERROR: [LoginServer-HQ] Failed to send AUTH_GREETING: {}", e);
        return;
    }
    println!("INFO: [LoginServer-HQ] -> Sent AUTH_GREETING (92 bytes, Opcode 0x05)");

    let mut buf = [0u8; 1024];

    // 2. CREDENTIALS
    let n = match socket.read(&mut buf).await {
        Ok(n) if n > 0 => n,
        Ok(_) => {
            println!("INFO: [LoginServer-HQ] Client disconnected during credentials phase.");
            return;
        }
        Err(e) => {
            eprintln!("ERROR: [LoginServer-HQ] Read error on credentials: {}", e);
            return;
        }
    };

    let username = match parse_credentials(&buf[..n]) {
        Some(cred) => {
            println!(
                "INFO: [LoginServer-HQ] <- CREDENTIALS: user_id='{}', session_id {}",
                cred.user_id,
                if cred.session_id.is_empty() { "ausente" } else { "presente" }
            );
            cred.user_id
        }
        None => {
            println!(
                "WARN: [LoginServer-HQ] <- CREDENTIALS ilegivel ({} bytes); usando '{}'",
                n, default_user
            );
            default_user.clone()
        }
    };

    let account_id = match db.get_or_create_account(&username, auto_create) {
        Ok(Some(a)) => a.id as u32,
        _ => {
            println!("WARN: [LoginServer-HQ] Conta '{}' indisponivel; usando id 1", username);
            1
        }
    };
    let char_count = db.get_character_count(&username);
    println!(
        "INFO: [LoginServer-HQ] Authentication accepted for '{}' (account_id={})",
        username, account_id
    );

    // 3. LOGIN_OK (14 bytes)
    if let Err(e) = socket.write_all(&build_login_ok(account_id)).await {
        eprintln!("ERROR: [LoginServer-HQ] Failed to send LOGIN_OK: {}", e);
        return;
    }
    println!(
        "INFO: [LoginServer-HQ] -> Sent LOGIN_OK (14 bytes, account_id=0x{:08X})",
        account_id
    );

    // 4. SERVER_LIST (201 bytes)
    let server_list = build_server_list(
        &announce_ip,
        announce_port,
        default_server_id as u32,
        char_count as u32,
    );
    if let Err(e) = socket.write_all(&server_list).await {
        eprintln!("ERROR: [LoginServer-HQ] Failed to send SERVER_LIST: {}", e);
        return;
    }
    println!(
        "INFO: [LoginServer-HQ] -> Sent SERVER_LIST (201 bytes, servidor {} em {}:{}, {} personagens)",
        default_server_id, announce_ip, announce_port, char_count
    );

    // 5. SERVER_SELECT
    let n2 = match socket.read(&mut buf).await {
        Ok(n) if n > 0 => n,
        Ok(_) => {
            println!("INFO: [LoginServer-HQ] Client disconnected waiting for SERVER_SELECT.");
            return;
        }
        Err(e) => {
            eprintln!("ERROR: [LoginServer-HQ] Read error on SERVER_SELECT: {}", e);
            return;
        }
    };

    let server_id = if n2 >= 10 {
        u32::from_le_bytes(buf[6..10].try_into().unwrap_or([default_server_id, 0, 0, 0]))
    } else {
        default_server_id as u32
    };
    println!("INFO: [LoginServer-HQ] <- Player selected server ID {}", server_id);

    // 6. Chave de sessao: sorteada aqui, gravada no banco e devolvida ao cliente, que a repassa
    //    ao game server. Precisa ser diferente a cada login -- antes ia um 0x0AD6 fixo, o que
    //    tornava a tabela `sessions` inutil para validar quem entrava.
    let session_key: u32 = rand::random();
    if let Err(e) = db.issue_session(account_id, &username, session_key) {
        eprintln!("ERROR: [LoginServer-HQ] Falha ao gravar a sessao de '{}': {}", username, e);
        return;
    }

    if let Err(e) = socket
        .write_all(&build_play_ok(server_id, account_id, session_key))
        .await
    {
        eprintln!("ERROR: [LoginServer-HQ] Failed to send PLAY_OK: {}", e);
        return;
    }
    println!(
        "INFO: [LoginServer-HQ] -> Sent PLAY_OK (22 bytes, servidor {}, session_key=0x{:08X}). Sessao de '{}' pronta para o game server.",
        server_id, session_key, username
    );
}

#[cfg(test)]
mod test {
    use super::*;

    /// Bytes copiados da captura de 21/08/2026 (`jogo.pcapng`, stream 0), conta 40820537,
    /// servidor 23 em 79.110.83.115:7777, 2 personagens.
    const CAPTURA_LOGIN_OK: &str = "0e00010000000000000039df6e02";

    const CAPTURA_SERVER_LIST: &str = concat!(
        "c90002000000",
        "0300",
        "0105000000670000000000000037392e3131302e38332e3131340000000000",
        "00000000000000000000000000000000000000000000611e0000000000000000",
        "0104000001170000000200000037392e3131302e38332e3131350000000000",
        "00000000000000000000000000000000000000000000611e0100000000000000",
        "0105000000790000000000000037392e3131302e38332e3131360000000000",
        "00000000000000000000000000000000000000000000611e0000000000000000",
        "17000000",
    );

    const CAPTURA_PLAY_OK_21: &str = "1600040000001700000039df6e020000000 01e160000";
    const CAPTURA_PLAY_OK_23: &str = "1600040000001700000039df6e0200000000 39390000";

    fn hex(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }

    #[test]
    fn greeting_confere_com_a_captura() {
        assert_eq!(AUTH_GREETING.len(), 92);
        assert_eq!(
            u16::from_le_bytes([AUTH_GREETING[0], AUTH_GREETING[1]]) as usize,
            AUTH_GREETING.len()
        );
        assert_eq!(AUTH_GREETING[2], 0x05);
    }

    #[test]
    fn credenciais_da_captura_de_21_sao_lidas() {
        let mut frame = vec![0x6b, 0x00, 0x01, 0x00, 0x00, 0x00];
        frame.extend_from_slice(
            b"M0MyM0Y1MjYtRDU5RS00RDUyLUJDODItNDJCRTg2OUFCQUEwOjg4MjgwMzFDLUYxRjEtNDVERS1CMDA3LUMwRDIzMDY2OUY1Mg==",
        );
        frame.push(0x00);
        assert_eq!(frame.len(), 0x6b, "o quadro real tem 107 bytes");

        let cred = parse_credentials(&frame).expect("credenciais devem ser lidas");
        assert_eq!(cred.user_id, "3C23F526-D59E-4D52-BC82-42BE869ABAA0");
        assert_eq!(cred.session_id, "8828031C-F1F1-45DE-B007-C0D230669F52");
    }

    #[test]
    fn credenciais_da_captura_de_23_tem_o_mesmo_usuario() {
        // Mesma conta, sessao diferente: e o que prova que o primeiro GUID identifica a conta
        // e o segundo e descartavel.
        let mut frame = vec![0x6b, 0x00, 0x01, 0x00, 0x00, 0x00];
        frame.extend_from_slice(
            b"M0MyM0Y1MjYtRDU5RS00RDUyLUJDODItNDJCRTg2OUFCQUEwOjE5NDYzQ0YxLTM4NDgtNDYzMC1CNDM5LTFFRkJGNDdCMDJFRg==",
        );
        frame.push(0x00);

        let cred = parse_credentials(&frame).expect("credenciais devem ser lidas");
        assert_eq!(cred.user_id, "3C23F526-D59E-4D52-BC82-42BE869ABAA0");
        assert_eq!(cred.session_id, "19463CF1-3848-4630-B439-1EFBF47B02EF");
    }

    #[test]
    fn credenciais_aceitam_token_cru() {
        // Launcher que nao use base64 nao pode derrubar o login.
        let mut frame = vec![0x0f, 0x00, 0x01, 0x00, 0x00, 0x00];
        frame.extend_from_slice(b"jogador1\0");
        let cred = parse_credentials(&frame).expect("token cru deve passar");
        assert_eq!(cred.user_id, "jogador1");
        assert_eq!(cred.session_id, "");
    }

    #[test]
    fn credenciais_vazias_devolvem_none() {
        assert_eq!(parse_credentials(&[0x06, 0x00, 0x01, 0x00, 0x00, 0x00]), None);
        assert_eq!(parse_credentials(&[0x00, 0x00]), None);
    }

    #[test]
    fn login_ok_bate_byte_a_byte_com_a_captura() {
        assert_eq!(hex(&build_login_ok(40820537)), CAPTURA_LOGIN_OK);
    }

    #[test]
    fn server_list_bate_byte_a_byte_com_a_captura() {
        let pkt = build_server_list("79.110.83.115", 7777, 23, 2);
        assert_eq!(pkt.len(), 201);
        assert_eq!(hex(&pkt), CAPTURA_SERVER_LIST.replace(' ', ""));
    }

    #[test]
    fn server_list_so_muda_a_contagem_de_personagens() {
        // Entre 21/08 e 23/08 a mesma conta passou de 2 para 3 personagens, e esse foi o unico
        // byte que mudou no pacote inteiro.
        let dois = build_server_list("79.110.83.115", 7777, 23, 2);
        let tres = build_server_list("79.110.83.115", 7777, 23, 3);
        let diferentes: Vec<usize> = (0..dois.len()).filter(|&i| dois[i] != tres[i]).collect();
        assert_eq!(diferentes, vec![8 + SERVER_ENTRY_LEN + 9]);
    }

    #[test]
    fn play_ok_bate_byte_a_byte_com_as_duas_capturas() {
        let p21 = build_play_ok(23, 40820537, 0x161E);
        assert_eq!(p21.len(), 22);
        assert_eq!(hex(&p21), CAPTURA_PLAY_OK_21.replace(' ', ""));

        let p23 = build_play_ok(23, 40820537, 0x3939);
        assert_eq!(hex(&p23), CAPTURA_PLAY_OK_23.replace(' ', ""));
    }

    #[test]
    fn ip_longo_nao_invade_o_campo_da_porta() {
        let pkt = build_server_list(
            "255.255.255.255:9999999999999999999999999999999999999999",
            7777,
            23,
            0,
        );
        let entrada = &pkt[8 + SERVER_ENTRY_LEN..8 + 2 * SERVER_ENTRY_LEN];
        assert_eq!(
            entrada[ENTRY_IP_OFFSET + ENTRY_IP_LEN - 1],
            0,
            "o campo de IP precisa terminar em zero"
        );
        assert_eq!(
            u16::from_le_bytes([entrada[ENTRY_PORT_OFFSET], entrada[ENTRY_PORT_OFFSET + 1]]),
            7777
        );
    }
}
