use std::{
    collections::HashMap,
    io::{Read, Write},
    net::TcpStream,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};

mod character;
pub mod craft;
pub mod data;
pub mod engine;
pub mod entity;
pub mod environment;
mod message;
pub mod instance;
pub mod housing;
pub mod mundo;
pub mod pet;
mod session;
pub mod social;
mod state;
pub mod web_services;

use crossbeam_channel::{Receiver, Sender};
use krypt::game::{gen_xor_key, gen_xor_seed};
use message::{client as c, server as s, ClientMessages};
use session::Account;

use self::state::State;

const TICK_RATE: f32 = 144.;

trait Serialise {
    fn serialise(&self, buf: &mut [u8]) -> usize;
}

trait Deserialise {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized;
}

/// Copy a buffer into a another buffer
/// ```
/// let mut len = 0;
/// let mut buf = [0u8; 100];
/// let data = [1,3,3,7];
///
/// copy_bytes!(len, buf, data);
/// ```
#[macro_export]
macro_rules! copy_bytes {
    ($ptr:expr, $buf:expr, $value:expr) => {
        let buffer_length = $value.len();
        $buf[$ptr..$ptr + buffer_length].copy_from_slice(&$value);
        $ptr += buffer_length;
    };
}

/// Serialise any value that implements .to_le_bytes() onto the given buffer
/// ```
/// let mut len = 0;
/// let mut buf = [0u8; 100];
/// let id: 32 = 13371337;
///
/// to_le_bytes!(len, buf, id);
/// ```
#[macro_export]
macro_rules! to_le_bytes {
    ($ptr:expr, $buf:expr, $value:expr) => {
        let size = core::mem::size_of_val(&$value);
        $buf[$ptr..$ptr + size].copy_from_slice(&$value.to_le_bytes());
        $ptr += size;
    };
}

/// Deserialise any value that implements .from_le_bytes() onto the given buffer
/// ```
/// let mut len = 0;
/// let mut buf = [0u8; 100];
///
/// let id = consume_le_bytes!(len, buf, u16);
/// ```
#[macro_export]
macro_rules! consume_le_bytes {
    ($ptr:expr, $buf:expr, $ty:ty) => {{
        let size = core::mem::size_of::<$ty>();
        let ret =
            <$ty>::from_le_bytes($buf[$ptr..$ptr + size].try_into().unwrap());
        $ptr += size;
        ret
    }};
}

#[derive(Debug, Clone)]
pub struct ServerUpdate {
    message: s::Message,
}
impl ServerUpdate {
    pub fn new(message: s::Message) -> Self {
        Self { message }
    }
    pub fn message(&self) -> &s::Message {
        &self.message
    }
}

#[derive(Clone)]
pub struct ClientUpdate {
    message: c::Message,
    client_id: u16,
    character_id: u32,
    session_token: String,
    /// Chave que o auth server entregou e o cliente repetiu no HqLogin. O cabecalho do
    /// S_CHARACTER_LIST a carrega, e a thread do jogo nao tem acesso ao Account.
    chave_de_sessao: u32,
}

impl ClientUpdate {
    pub fn client_id(&self) -> u16 {
        self.client_id
    }
    pub fn character_id(&self) -> u32 {
        self.character_id
    }
    pub fn chave_de_sessao(&self) -> u32 {
        self.chave_de_sessao
    }
    pub fn message(&self) -> &c::Message {
        &self.message
    }
    pub fn session_token(&self) -> &str {
        &self.session_token
    }
    pub fn new(client_id: u16, character_id: u32, message: c::Message) -> Self {
        Self::new_with_token(client_id, character_id, message, String::new(), 0)
    }
    pub fn new_with_token(
        client_id: u16,
        character_id: u32,
        message: c::Message,
        session_token: String,
        chave_de_sessao: u32,
    ) -> Self {
        Self {
            message,
            client_id,
            character_id,
            session_token,
            chave_de_sessao,
        }
    }
}

/// Long lived buffers that store ServerUpdates during calculation before they
/// are sent to the players.
///
/// `direct` and `others` are keyed by client_id. Rather than draining
/// (which drops + reallocates the inner Vecs), we track which keys received
/// messages in a separate `dirty_*` list and `clear()` only those Vecs after
/// the send pass, retaining their capacity for the next tick.
struct Messages {
    /// Only send to the requesting client
    direct: HashMap<u16, Vec<ServerUpdate>>,
    dirty_direct: Vec<u16>,
    /// Only send to other clients
    others: HashMap<u16, Vec<ServerUpdate>>,
    dirty_others: Vec<u16>,
    /// Send to all clients
    pub broadcast: Vec<ServerUpdate>,
}

impl Messages {
    pub fn new() -> Self {
        Self {
            direct: HashMap::with_capacity(100),
            dirty_direct: Vec::with_capacity(100),
            others: HashMap::with_capacity(100),
            dirty_others: Vec::with_capacity(100),
            broadcast: Vec::with_capacity(100),
        }
    }

    /// Push a single message destined for `client_id` only.
    pub fn push_direct(&mut self, client_id: u16, msg: ServerUpdate) {
        let v = self.direct.entry(client_id).or_default();
        if v.is_empty() {
            self.dirty_direct.push(client_id);
        }
        v.push(msg);
    }

    /// Extend messages destined for `client_id` only.
    pub fn extend_direct(
        &mut self,
        client_id: u16,
        iter: impl IntoIterator<Item = ServerUpdate>,
    ) {
        let v = self.direct.entry(client_id).or_default();
        let was_empty = v.is_empty();
        v.extend(iter);
        if was_empty && !v.is_empty() {
            self.dirty_direct.push(client_id);
        }
    }

    /// Push a single message that goes to every client *except* `client_id`.
    pub fn push_others(&mut self, client_id: u16, msg: ServerUpdate) {
        let v = self.others.entry(client_id).or_default();
        if v.is_empty() {
            self.dirty_others.push(client_id);
        }
        v.push(msg);
    }

    /// Extend messages that go to every client *except* `client_id`.
    pub fn extend_others(
        &mut self,
        client_id: u16,
        iter: impl IntoIterator<Item = ServerUpdate>,
    ) {
        let v = self.others.entry(client_id).or_default();
        let was_empty = v.is_empty();
        v.extend(iter);
        if was_empty && !v.is_empty() {
            self.dirty_others.push(client_id);
        }
    }
}

/// Propagates events from one clients to all relevent clients
/// Takes a turn per game tick for the server actions
pub fn game_update(
    clients: Arc<Mutex<HashMap<u16, Sender<Vec<ServerUpdate>>>>>,
    server_rx: Receiver<ClientUpdate>,
    db: crate::db::Db,
    game_data: Arc<crate::data_loader::GameData>,
) {
    let mut disconnected_clients = Vec::with_capacity(100);
    let mut state = State::new(db, game_data);
    let mut messages = Messages::new();

    // Per-client outbox: all categories (broadcast + direct + others) are
    // merged here and sent in a single channel operation per client per tick.
    let mut outbox: HashMap<u16, Vec<ServerUpdate>> = HashMap::with_capacity(100);
    let mut dirty_outbox: Vec<u16> = Vec::with_capacity(100);

    let mut now = Instant::now();
    let mut last_persist = Instant::now();
    const PERSIST_INTERVAL: Duration = Duration::from_secs(10);
    loop {
        // Only update on tick rate
        if now.elapsed() < Duration::from_secs_f32(1. / TICK_RATE) {
            std::thread::yield_now();
            continue;
        }
        now = Instant::now();

        // Respond to client messages
        for update in server_rx.try_iter() {
            state.respond(&update, &mut messages);
        }

        // Server turn
        state.update(&mut messages);

        // Periodic persistence
        if last_persist.elapsed() >= PERSIST_INTERVAL {
            state.persist_all();
            last_persist = Instant::now();
        }

        let mut clients = clients.lock().unwrap();

        // Helper: push to outbox, tracking dirty entries exactly once per key.
        macro_rules! outbox_push {
            ($id:expr, $msg:expr) => {{
                let v = outbox.entry($id).or_default();
                if v.is_empty() {
                    dirty_outbox.push($id);
                }
                v.push($msg);
            }};
        }

        // Broadcast → every connected client
        for message in messages.broadcast.drain(..) {
            println!("[BROADCAST]: {:X?}", message.message());
            for &id in clients.keys() {
                outbox_push!(id, message.clone());
            }
        }

        // Direct → specific client only
        for client_id in messages.dirty_direct.drain(..) {
            let src = messages.direct.get_mut(&client_id).unwrap();
            if clients.contains_key(&client_id) {
                for msg in src.drain(..) {
                    println!("[DIRECT:{:X}]: {:X?}", client_id, msg.message());
                    outbox_push!(client_id, msg);
                }
            } else {
                src.clear();
            }
        }

        // Others → every client except the originator
        for client_id in messages.dirty_others.drain(..) {
            let src = messages.others.get(&client_id).unwrap();
            for &id in clients.keys() {
                if id == client_id {
                    println!("[OTHERS:{:X}]: {:X?}", client_id, src);
                    continue;
                }
                for msg in src {
                    outbox_push!(id, msg.clone());
                }
            }
            messages.others.get_mut(&client_id).unwrap().clear();
        }

        // One channel send per client — replaces N individual sends.
        for client_id in dirty_outbox.drain(..) {
            let batch = outbox.entry(client_id).or_default();
            if let Some(sender) = clients.get(&client_id) {
                // Move the Vec into the channel; the receiver owns it.
                if sender.send(std::mem::take(batch)).is_err() {
                    disconnected_clients.push(client_id);
                }
            } else {
                batch.clear();
            }
        }

        // Remove disconnected clients and clean up their game State.
        for client in disconnected_clients.drain(..) {
            _ = clients.remove(&client);
            state.disconnect_client(client);
        }
    }
}

pub struct Keys {
    client: [u8; 8],
    server: [u8; 8],
}

impl Keys {
    fn new(initial_key: [u8; 8]) -> Self {
        Self {
            client: initial_key,
            server: initial_key,
        }
    }
}

pub struct Connection {
    stream: TcpStream,
    keys: Keys,
    account: Account,
    /// Sessao capturada usada para responder o que ainda nao sabemos construir. Opcional: sem o
    /// arquivo o servidor roda normalmente, respondendo so o que tem implementado.
    replay: Option<message::replay::Replay>,
    /// The game server tx to client rx (batched: one Vec per tick)
    rx: Receiver<Vec<ServerUpdate>>,
    /// The client tx to the game server rx
    tx: Sender<ClientUpdate>,
}

impl Connection {
    pub fn new(
        mut stream: TcpStream,
        client_id: u16,
        rx: Receiver<Vec<ServerUpdate>>,
        tx: Sender<ClientUpdate>,
    ) -> Self {
        // Send this accross the network
        let seed = gen_xor_seed();

        // calculated key we keep in memory
        let key = gen_xor_key(seed);

        // S_KEY Packet
        let mut buf = [0u8; 11];
        let len = message::make_key_packet(&mut buf, seed);
        stream.write_all(&buf[..len]).unwrap();

        // O replay so entra se alguem pedir, por `AION_REPLAY`. **Ligado por padrao, ele impedia
        // a entrada no mundo.**
        //
        // O motor indexa os pacotes gravados pelo opcode de cliente que veio antes deles, e
        // devolve o lote de *onde quer que* aquele opcode tenha aparecido na sessao de 22
        // minutos. Durante o carregamento o cliente manda `0x122`, e recebia sete pacotes que na
        // captura respondiam a outra coisa, vinte minutos depois. Nao era pacote faltando: era
        // pacote valido chegando no contexto errado, e o cliente nunca mandava o `LevelReady`.
        //
        // Como o disparo dependia de quais opcodes o cliente resolvia mandar, e cada lote e
        // consumido uma vez so, o sintoma ia e voltava -- e chegou a ser documentado como
        // resolvido. Com o replay fora, o personagem entra em cena com os NPCs em volta.
        //
        // Continua util como instrumento: `AION_REPLAY=replay.bin` liga de novo, para comparar um
        // pacote nosso com o gravado.
        let replay = match std::env::var("AION_REPLAY") {
            Ok(caminho) if !caminho.is_empty() => {
                message::replay::Replay::carregar(std::path::Path::new(&caminho))
            }
            _ => None,
        };

        Self {
            stream,
            keys: Keys::new(key.to_le_bytes()),
            account: Account::new(client_id),
            replay,
            rx,
            tx,
        }
    }

    pub fn handle(mut self) {
        use std::io::ErrorKind;
        /// `ERROR_IO_PENDING` do Windows: a operacao ainda esta pendente, nao e desconexao.
        const ERROR_IO_PENDING: i32 = 997;
        // Allocate once; reused every tick to avoid per-iteration zeroing.
        let mut recv_buffer = [0u8; 1024 * 64];
        let mut send_buffer = [0u8; 1024 * 64];
        loop {
            let messages = match self.stream.read(&mut recv_buffer) {
                // TCP len 0 means close
                Ok(0) => return,
                Ok(len) => ClientMessages::deserialise(
                    &mut recv_buffer[..len],
                    &mut self.keys.client,
                    self.account.no_mundo(),
                ),
                Err(e) => match e.kind() {
                    // Expected when the 1ms read timeout fires — there was
                    // nothing for the client to say this tick. Keep looping
                    // so we can still forward server-originated messages.
                    ErrorKind::WouldBlock | ErrorKind::TimedOut => {
                        ClientMessages::empty()
                    }
                    // Mesmo caso, outro numero. No Windows, um read com timeout
                    // sobre I/O sobreposto pode voltar ERROR_IO_PENDING em vez
                    // de WSAETIMEDOUT, e o Rust nao classifica esse. Tratar como
                    // desconexao derrubava a sessao no meio do login, de vez em
                    // quando, sem nada de errado no fio.
                    _ if e.raw_os_error() == Some(ERROR_IO_PENDING) => {
                        ClientMessages::empty()
                    }
                    // Real disconnect — bail so main::handle() can free the
                    // client slot and the game loop can GC state.
                    _ => {
                        println!("INFO: client read error ({e}); closing");
                        return;
                    }
                },
            };

            let len = messages.handle(
                &mut send_buffer,
                &mut self.keys.server,
                &mut self.account,
                &self.rx,
                &self.tx,
                &mut self.replay,
            );
            if len != 0 {
                // `write_all`, e nao `write`: o segundo pode escrever so parte do buffer e
                // devolver quantos bytes foram -- e o retorno era ignorado. Enquanto os lotes
                // eram pequenos isso nunca aparecia; com os NPCs do mundo (uns 17 KB de uma vez)
                // o socket enche, o resto some em silencio, e o cliente recebe um pacote cortado
                // no meio. Dai ele dessincroniza a decifracao e a sessao morre.
                if let Err(e) = self.stream.write_all(&send_buffer[..len]) {
                    println!("INFO: client write error ({e}); closing");
                    return;
                }
            }
        }
    }
}
