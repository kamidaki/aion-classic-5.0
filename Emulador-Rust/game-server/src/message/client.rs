//! Client packets have the following syntax
//! [OPCODE] 2 Bytes
//! [CLIENT] 1 Byte - Always 0x6F
//! [CHECKSUM] 2 Bytes - Checksum should be == bitwise not opcode

use commons::game::{decrypt, decrypt_client_opcode};

use super::server as s;
use crate::consume_le_bytes;
use crate::data::ActionType;
use crate::engine::{Coord, Direction, MoveType};
use crate::session::Account;
use crate::{ClientUpdate, Deserialise};
use crossbeam_channel::Sender;

macro_rules! define_messages {
    ($(($message_const_name:ident, $message:ident, $opcode:expr)),* $(,)?) => {
        $(
            const $message_const_name: u16 = $opcode;
        )*

        #[derive(Debug, Clone)]
        #[repr(u16)]
        pub enum Message {
            $(
                $message($message),
            )*
        }

        impl Message {
            /// Devolve a mensagem quando o opcode tem implementacao, ou o proprio opcode
            /// quando nao tem -- quem chama precisa do numero para servi-lo pelo replay.
            pub fn deserialise(
                mut buf: &mut [u8],
                mut key: &mut [u8; 8],
            ) -> Result<(Self, u16), u16> {
                if buf.len() < 5 {
                    eprintln!("WARNING: Client packet payload too short (len: {})", buf.len());
                    return Err(0xFFFF);
                }

                decrypt(&mut key, buf);

                let mut len = 0;

                let opcode = consume_le_bytes!(len, buf, u16);
                // Skip Server bytes
                len += 1;

                let checksum = consume_le_bytes!(len, buf, u16);

                if checksum != !opcode {
                    eprintln!("WARNING: Packet Checksum Failed, {opcode:02X}-{checksum:02X}");
                    return Err(0xFFFF);
                }
                let opcode = decrypt_client_opcode(opcode);

                buf = &mut buf[len..];
                match opcode {
                    $(
                        $message_const_name => {
                            Ok((Message::$message(<$message>::deserialise(buf)), opcode))
                        }
                    )*
                    _ => {
                        println!("WARNING: Client Opcode {opcode:02X} not implemented");
                        println!("C RAW: {:02X?}", buf);
                        Err(opcode)
                    }
                }
            }

            pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
                match self {
                    $(
                        Self::$message(message) => message.handle(&tx, session),
                    )*
                }
            }
        }
    };
}

// Os numeros abaixo saem de duas fontes: a tabela extraida do `Game.dll` 4.5 e tres capturas do
// servidor oficial da Gameforge (21/08, 23/08 e 24/08 de 2026). Onde as duas discordam, vale a
// captura -- a tabela erra o pareamento nome/numero em pontos conhecidos.
//
// COMO SE DESCOBRE O NUMERO DE UM OPCODE, E O ERRO QUE INVALIDA A ANALISE
// -----------------------------------------------------------------------
// Correlacionar o pedido com a resposta do servidor so vale quando a resposta E resposta. Boa
// parte dos opcodes de servidor e broadcast e vem depois de qualquer coisa.
//
// O teste que separa os dois: para cada opcode de servidor, olhar a distribuicao do pedido de
// cliente imediatamente anterior, nas tres capturas. Se UM opcode de cliente domina >= 70% das
// ocorrencias, e par pedido/resposta e serve de ancora. Distribuicao espalhada = broadcast.
//
// Rodar as duas direcoes nao e zelo excessivo, e o que impede errar: `S_CHANGE_ITEM_DESC` (304
// ocorrencias) parecia confirmar USE_EQUIPMENT_ITEM = 0x033 na direcao pedido -> resposta, e na
// inversa era dominada por 0x02E (152x). Broadcast. Idem `S_BUDDY_LIST` com 0x046, que deu empate
// triplo. Conferir tambem se o payload cabe na struct: `UseEquipmentItem` e `[u8; 9]` e o 0x033
// tem 24 e 56 bytes -- nao cabia.
//
// JA TESTADOS E REJEITADOS -- nao retentar sem prova nova:
//   0x033 para USE_EQUIPMENT_ITEM     0x046 para QUERY_BUDDY
//
// PARES CONFIRMADOS pelo teste das duas direcoes (>= 70% nas tres capturas):
//
//   | pedido  | resposta                | dominancia | nome aqui                  |
//   |---------|-------------------------|------------|----------------------------|
//   | `0x8B`  | S_SA_ACCOUNT_ITEM_NOTI  | 100% 10/10 | SA_ACCOUNT_ITEM_QUERY      |
//   | `0x03`  | S_ASK_QUIT_RESULT       | 100%       | ASK_QUIT                   |
//   | `0x12`  | S_SYNC_TIME             |  81%       | SYNC_TIME                  |
//   | `0x5E`  | S_CHARACTER_LIST        |  75%       | SESSION_KEY_ECHO           |
//   | `0xBE`  | S_CHANGE_CHANNEL        |  70%       | ROUTE_INFO                 |
//   | `0xA8`  | S_0x102                 |  77%       | QUERY_BLOCK                |
//   | `0xC5`  | S_0x19D / S_0x0A3       |  87% / 77% | REQUEST_SERIAL_KILLER_LIST |
//   | `0x21`  | S_0x0CB                 |  75%       | USE_SKILL                  |
//   | `0xAA`  | S_LOAD_CLIENT_SETTINGS  |  83%       | CUR_STATUS (ver abaixo)    |
//
// SOBRE O 0xAA: o numero esta certo, o nome e que engana. `CurStatus` e struct unitaria (o pedido
// chega com 0 bytes, como na captura) e o handler ja devolve o blob zlib de configuracoes de UI --
// ou seja, ja E o pedido de settings do cliente. Quem esta morto e SAVE_CLIENT_SETTINGS no 0x00A,
// que nunca aparece em captura nenhuma. Nao "corrigir" o 0xAA.
//
// OS QUE AINDA FALTAM
// -------------------
// Continuam com numero suspeito, sem prova: SAVE_CLIENT_SETTINGS (0x0A), CHAT_MESSAGE_PUBLIC
// (0x1B), CHANGE_TARGET (0x1F), USE_EQUIPMENT_ITEM (0x26), ACTION (0x2B), ALIVE (0x2C),
// DIALOG_SELECT (0x36), ASK_LOG (0x3E), QUERY_BUDDY (0x6E), LOOT (0x9A), LOOT_ITEM (0x9B) e
// _D8 (0xD8). SHOW_DIALOG (0x34) saiu dessa lista: aparece na captura de 24/08, com 28 e 42 bytes.
//
// Do outro lado, estes pedidos do cliente NAO tem handler e comandam resposta com dominancia alta
// -- sao os alvos com melhor razao entre esforco e retorno:
//
//   | pedido  | bytes | resposta                        | dominancia |
//   |---------|-------|---------------------------------|------------|
//   | `0xFFFE`|  16   | S_0x045, S_0x014, S_0x0FD       | 78/75/100% |
//   | `0x114` |   7   | S_0x13C                         |  94%       |
//   | `0x06F` |   0   | S_0x07F                         |  80%       |
//   | `0xFFEB`|  19   | S_0x018                         |  80%       |
//
// (`0xFFFE` e `0xFFEB` sao o que a desofuscacao devolve; 383 e poucas ocorrencias. Cair em valor
// negativo significa que o pedido chega com opcode cifrado baixo -- ver `decrypt_client_opcode`.)
define_messages!(
    (VERSION, Version, 0x00),
    (ASK_QUIT, AskQuit, 0x03),
    (ENTER_WORLD, EnterWorld, 0x18),
    (LEVEL_READY, LevelReady, 0x19),
    (READY_TO_QUIT, ReadyToQuit, 0x04),
    (SAVE_CLIENT_SETTINGS, SaveClientSettings, 0x0A),
    (SYNC_TIME, SyncTime, 0x12),
    (CHANGE_TARGET, ChangeTarget, 0x1F),
    (ATTACK, Attack, 0x20),
    (USE_SKILL, UseSkill, 0x21),
    (USE_EQUIPMENT_ITEM, UseEquipmentItem, 0x26),
    (ACTION, Action, 0x2B),
    (ALIVE, Alive, 0x2C),
    (MOVE_NEW, MoveNew, 0x30),
    (ASK_LOG, AskLog, 0x3E),
    (QUERY_BUDDY, QueryBuddy, 0x6E),
    (CHARACTER_LIST, CharacterList, 0x96),
    (LOOT, Loot, 0x9A),
    (LOOT_ITEM, LootItem, 0x9B),
    (RECIPE_LIST, RecipeList, 0xB6),
    (RECONNECT_AUTH, ReconnectAuth, 0xB8),
    (INSTANCE_DUNGEON_COOLTIMES, InstanceDungeonCooltimes, 0xC1),
    (REQUEST_GUILD_HISTORY, RequestGuildHistory, 0xC5),
    (_D8, _00D8, 0xD8),
    (CREATE_CHARACTER, CreateCharacter, 0x5F),
    (CUR_STATUS, CurStatus, 0xAA),
    (QUERY_BLOCK, QueryBlock, 0xA8),
    (SIGN_CLIENT, SignClient, 0x86),
    (SA_ACCOUNT_ITEM_QUERY, SaAccountItemQuery, 0x8B),
    (ROUTE_INFO, RouteInfo, 0xBE),
    (SECOND_PASSWORD, SecondPassword, 0xD2),
    (READY_ENTER_WORLD_ACK, ReadyEnterWorldAck, 0xE2),
    (HQ_LOGIN, HqLogin, 0xF0),
    (L2AUTH_LOGIN, L2AuthLogin, 0x5D),
    (SESSION_KEY_ECHO, SessionKeyEcho, 0x5E),
    (MACHINE_INFO, MachineInfo, 0xD6),
    (CHAT_MESSAGE_PUBLIC, ChatMessagePublic, 0x1B),
    (SHOW_DIALOG, ShowDialog, 0x34),
    (DIALOG_SELECT, DialogSelect, 0x36),
    (DELETE_CHARACTER, DeleteCharacter, 0x05),
    (WIND_PATH, WindPath, 0x46),
    (PATH_FLY, PathFly, 0x31),
    (BUY_SELL, BuySell, 0x33),
    (MAIL_READ, MailRead, 0x87),
    (MAIL_POSTMAN, MailPostman, 0xA2),
    (CHECK_NICKNAME, CheckNickName, 0x28),
    (QUIT, Quit, 0x48),
    (RECONNECT, Reconnect, 0x4A),
    (GUILD_USER_BUY_BUFF, GuildUserBuyBuff, 0xC6),
    (GUILD_MANAGE, GuildManage, 0xC7),
    (PARTY, Party, 0x60),
    (PARTY_BY_NAME, PartyByName, 0x61),
    (ADD_BUDDY, AddBuddy, 0x6F),
    (GLOBAL_TRADE_REGISTER, GlobalTradeRegister, 0x0100),
    (GLOBAL_TRADE_SALESLOG, GlobalTradeSaleslog, 0x0101),
    (GLOBAL_TRADE_BUY, GlobalTradeBuy, 0x0102),
    (GLOBAL_TRADE_AVG_PRICE, GlobalTradeAvgPrice, 0x0103),
    (CHAT_MESSAGE_WHISPER, ChatMessageWhisper, 0x1C),
);

/// O cliente devolve a chave de sessao que recebeu do auth server, logo apos o
/// C_READY_ENTER_WORLD_ACK. Na captura real chega como [B6 CA 62 02].
///
/// A tabela extraida do Game.dll chama 0x5E de C_GET_OFF_VEHICLE, o que nao bate com o conteudo --
/// o pareamento nome/numero daquela tabela erra em alguns pontos. O nome aqui vem do que o pacote
/// carrega.
#[derive(Debug, Clone)]
pub struct SessionKeyEcho {
    chave: u32,
}

impl SessionKeyEcho {
    pub fn handle(&self, _: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        if self.chave != session.auth_server.id {
            println!(
                "WARNING: chave devolvida pelo cliente (0x{:08X}) difere da do HqLogin (0x{:08X})",
                self.chave, session.auth_server.id
            );
        }
        vec![]
    }
}

impl Deserialise for SessionKeyEcho {
    fn deserialise(buf: &[u8]) -> Self {
        Self {
            chave: u32::from_le_bytes(buf[..4].try_into().unwrap()),
        }
    }
}

/// Identificacao da maquina: MAC, id de hardware e o IP do cliente, em UTF-16.
///
/// E o ultimo pacote antes de o servidor real mandar a lista de personagens, e por isso e daqui que
/// a nossa lista sai.
#[derive(Debug, Clone)]
pub struct MachineInfo {
    bruto: Vec<u8>,
}

impl MachineInfo {
    pub fn handle(&self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        // Duas listas de personagem convivem aqui.
        //
        // A CONSTRUIDA (padrao) monta o pacote no layout 4.5 a partir do banco. E o unico caminho
        // que serve a longo prazo: sem ids do proprio servidor, o personagem escolhido nao existe
        // no estado do jogo e o mundo carrega sem posicao nem mapa.
        //
        // Ela ja derrubou o cliente, e a causa era o cabecalho: a contagem de personagens aparece
        // duas vezes, e a leitura antiga do layout so escrevia a primeira -- entao com 1 personagem
        // o cliente lia 2 registros de um pacote que so tinha 1. Ver `lista_personagens`.
        //
        // A CAPTURADA (AION_LISTA_CAPTURADA=1) reproduz os bytes da sessao real. Chega na tela de
        // personagem com os personagens da conta capturada, e serve de comparacao quando a
        // construida for suspeita de alguma coisa.
        if std::env::var("AION_LISTA_CAPTURADA").is_err() {
            println!("INFO: MachineInfo -> lista CONSTRUIDA (layout 4.5, do banco)");
            tx.send(session.send(Message::CharacterList(CharacterList)))
                .unwrap();
            return vec![s::Message::BuilderLevel(s::BuilderLevel::new())];
        }

        println!(
            "INFO: MachineInfo recebido ({} bytes); enviando a lista capturada",
            self.bruto.len()
        );
        use super::capturado as cap;
        let chave = session.auth_server.id;
        vec![
            s::Message::Bruto(s::Bruto::new(
                cap::BUILDER_LEVEL_OPCODE,
                cap::com_chave_de_sessao(&cap::BUILDER_LEVEL, chave),
            )),
            s::Message::Bruto(s::Bruto::new(
                cap::CHARACTER_LIST_1_OPCODE,
                cap::com_chave_de_sessao(&cap::CHARACTER_LIST_1, chave),
            )),
            s::Message::Bruto(s::Bruto::new(
                cap::CHARACTER_LIST_2_OPCODE,
                cap::com_chave_de_sessao(&cap::CHARACTER_LIST_2, chave),
            )),
        ]
    }
}

impl Deserialise for MachineInfo {
    fn deserialise(buf: &[u8]) -> Self {
        Self {
            bruto: buf.to_vec(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct SyncTime {
    /// On a SyncTime Request this is current session time
    /// On a SyncTime Acknowledgement this is the server uptime
    ticks: u32,
    /// 0 means request
    /// 1 means ack
    ty: u8,
    unknown: [u8; 4],
    /// The
    sequence: u32,
}
impl SyncTime {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        // ty is set to 1 when its an ack
        if self.ty == 0 {
            vec![s::Message::SyncTime(s::SyncTime::new(self.ticks))]
        } else {
            vec![]
        }
    }
}
impl Deserialise for SyncTime {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self {
            ticks: u32::from_le_bytes([buf[0], buf[1], buf[2], buf[3]]),
            ty: buf[4],
            unknown: [buf[5], buf[6], buf[7], buf[8]],
            sequence: u32::from_le_bytes([buf[9], buf[10], buf[11], buf[12]]),
        }
    }
}

// TODO: Get this from external state
#[derive(Debug, Clone)]
pub struct CharacterList;
impl CharacterList {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::CharacterList(self))).unwrap();
        vec![s::Message::BuilderLevel(s::BuilderLevel::new())]
    }
}
impl Deserialise for CharacterList {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

/// Client sends a packet chosing which character they wish to log in as
#[derive(Debug, Clone)]
pub struct EnterWorld {
    pub character_id: u32,
}
impl Deserialise for EnterWorld {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _ptr = 0;
        Self {
            character_id: consume_le_bytes!(_ptr, buf, u32),
        }
    }
}

impl EnterWorld {
    /// A selecao de personagem: 4 bytes com o id que a nossa propria lista mandou, de volta.
    ///
    /// O opcode e 0x18 na 4.5 -- era 0x08 na 2.5, de onde este POC veio. A tabela extraida do
    /// Game.dll chama 0x18 de C_TOGGLE_CHEST; o pareamento nome/numero dela erra em alguns pontos,
    /// e este e mais um. O que vale e o conteudo: os 4 bytes batem com o id do personagem que a
    /// lista declarou, e na captura sao os da Kimmie.
    ///
    /// Sem tratar este pacote a sessao fica com personagem 0, o estado do jogo nao acha ninguem, e
    /// a entrada no mundo nao manda nem mapa nem posicao -- o cliente carrega a HUD inteira sobre o
    /// cenario da tela de selecao.
    ///
    /// A resposta e o pedido de segunda senha, como na captura (`S_2ND_PASSWORD`, 1 byte). O
    /// cliente responde sozinho, sem perguntar nada ao jogador, e so entao vem o
    /// `S_ENTER_WORLD_CHECK` -- que e o que o POC mandava aqui, direto, no fluxo da 2.5.
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        println!("INFO: personagem {} selecionado", self.character_id);
        session.set_character_id(self.character_id);
        session.entrou_no_mundo();

        vec![s::Message::SecondPassword(s::SecondPassword::request())]
    }
}

#[derive(Debug, Clone)]
pub struct SecondPassword;

impl SecondPassword {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![
            s::Message::SecondPassword(s::SecondPassword::response()),
            s::Message::EnterWorldCheck(s::EnterWorldCheck::new()),
        ]
    }
}
impl Deserialise for SecondPassword {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

/// Opcode `0x8B`. Sem resposta a este opcode a tela de personagem trava: nao da para entrar no
/// jogo, criar personagem, nem voltar para a lista de servidores. Os botoes simplesmente nao
/// reagem.
///
/// O numero saiu das capturas, nao da tabela do `Game.dll` -- que chama `0x8B` de
/// `C_CHANGE_TITLE` e erra em pontos conhecidos. Nas duas capturas, todas as 9 ocorrencias de
/// `S_SA_ACCOUNT_ITEM_NOTI` vem imediatamente depois de um `C 0x8B`, e o pedido chega sem
/// payload -- o que casa com esta struct unitaria.
///
/// Antes ficavam dois handlers identicos: este, mapeado no `0xBB` (numero que nao aparece em
/// captura nenhuma, logo nunca disparava), e um `_008B` sem nome no numero certo.
#[derive(Debug, Clone)]
pub struct SaAccountItemQuery;

impl SaAccountItemQuery {
    /// The client will hang unless we respond to this query
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::SaAccountItemNoti(s::SaAccountItemNoti::new())]
    }
}
impl Deserialise for SaAccountItemQuery {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

/// Contains information from server end
#[derive(Debug, Clone)]
pub struct HqLogin {
    id: u32,
    key: u32,
    authn_token: String,
}
impl HqLogin {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        session.auth_server.id = self.id;
        session.auth_server.key = self.key;
        session.session_token = self.authn_token.trim_end_matches('\0').to_string();
        println!(
            "INFO: HqLogin token for client received ({} chars)",
            session.session_token.len()
        );
        vec![
            // Duas vezes, com o mesmo `00 01`. As duas capturas concordam, de contas e dias
            // diferentes -- nao e repeticao acidental de uma sessao.
            s::Message::ReplyNpLoginGamesvr(s::ReplyNpLoginGamesvr::new()),
            s::Message::ReplyNpLoginGamesvr(s::ReplyNpLoginGamesvr::new()),
            s::Message::NpShopGoodsCount(s::NpShopGoodsCount::new()),
            s::Message::ReadyEnterWorld(s::ReadyEnterWorld::new()),
            s::Message::L2AuthLoginCheck(s::L2AuthLoginCheck::new()),
            s::Message::ReplyNpAuthToken(s::ReplyNpAuthToken::para(
                &session.session_token,
            )),
        ]
    }
}

impl Deserialise for HqLogin {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut len = 0;

        let id = consume_le_bytes!(len, buf, u32);
        let key = consume_le_bytes!(len, buf, u32);

        // unknown
        len += 8;

        let authn_token = std::str::from_utf8(&buf[len..]).unwrap_or("").into();
        Self {
            id,
            key,
            authn_token,
        }
    }
}

/// Autenticacao nativa NCSoft (Opcode 0x5D - C_L2AUTH_LOGIN / CM_AUTH_CLIENT)
#[derive(Debug, Clone)]
pub struct L2AuthLogin {
    pub play_ok2: u32,
    pub play_ok1: u32,
    pub account_id: u32,
    pub login_ok: u32,
}

impl L2AuthLogin {
    pub fn handle(
        &self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        session.auth_server.id = self.account_id;
        session.auth_server.key = self.play_ok2;
        println!(
            "INFO: [GameServer] <- [L2AuthLogin/0x5D] Autenticado: account_id={}, play_ok2=0x{:08X}, play_ok1=0x{:08X}",
            self.account_id, self.play_ok2, self.play_ok1
        );

        // Envia a lista de personagens para o client exibir a tela de selecao de personagens
        tx.send(session.send(Message::CharacterList(CharacterList))).unwrap();

        vec![
            s::Message::ReplyNpLoginGamesvr(s::ReplyNpLoginGamesvr::new()),
            s::Message::ReplyNpLoginGamesvr(s::ReplyNpLoginGamesvr::new()),
            s::Message::NpShopGoodsCount(s::NpShopGoodsCount::new()),
            s::Message::ReadyEnterWorld(s::ReadyEnterWorld::new()),
            s::Message::L2AuthLoginCheck(s::L2AuthLoginCheck::new()),
            s::Message::BuilderLevel(s::BuilderLevel::new()),
        ]
    }
}

impl Deserialise for L2AuthLogin {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let play_ok2 = if buf.len() >= 4 { u32::from_le_bytes(buf[0..4].try_into().unwrap()) } else { 0 };
        let play_ok1 = if buf.len() >= 8 { u32::from_le_bytes(buf[4..8].try_into().unwrap()) } else { 0 };
        let account_id = if buf.len() >= 12 { u32::from_le_bytes(buf[8..12].try_into().unwrap()) } else { 0 };
        let login_ok = if buf.len() >= 16 { u32::from_le_bytes(buf[12..16].try_into().unwrap()) } else { 0 };

        Self {
            play_ok2,
            play_ok1,
            account_id,
            login_ok,
        }
    }
}

/// Reports the client versions, OS and game related
/// 00F2
/// [Aion major version] C0 00
/// [Unknown] 28 00
/// [ANSI Encoding] E4 04 00 00
/// [OS Major Version] 06 00 00 00
/// [OS Minor Version] 02 00 00 00
#[allow(dead_code)]
#[derive(Debug, Clone)]
pub struct Version {
    aion_version: u16,
    unknown: [u8; 2],
    ansi_encoding: u32,
    os_major_version: u32,
    os_minor_version: u32,
}
impl Version {
    pub fn handle(
        self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![
            s::Message::VersionCheck(s::VersionCheck::new()),
            s::Message::ServerEnv(s::ServerEnv::new()),
        ]
    }
}

impl Deserialise for Version {
    fn deserialise(mut buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let aion_version = u16::from_le_bytes(buf[..2].try_into().unwrap());
        buf = &buf[2..];

        let unknown = buf[..2].try_into().unwrap();
        buf = &buf[2..];

        let ansi_encoding = u32::from_le_bytes(buf[..4].try_into().unwrap());
        buf = &buf[4..];

        let os_major_version = u32::from_le_bytes(buf[..4].try_into().unwrap());
        buf = &buf[4..];

        let os_minor_version = u32::from_le_bytes(buf[..4].try_into().unwrap());

        Self {
            aion_version,
            unknown,
            ansi_encoding,
            os_major_version,
            os_minor_version,
        }
    }
}

#[derive(Debug, Clone)]
pub struct CurStatus;

impl CurStatus {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        let change_channel = [0x00, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00];

        let ui = [
            0x76, 0x7C, 0x00, 0x00, 0x78, 0x9C, 0xCD, 0x5D, 0x4B, 0x73, 0x23,
            0xB7, 0x11, 0x46, 0xAE, 0xA9, 0xCA, 0x7F, 0xD8, 0xF2, 0xDD, 0x31,
            0xE7, 0x3D, 0x53, 0x95, 0xC8, 0x65, 0xEF, 0x7A, 0x73, 0xCB, 0x25,
            0xC9, 0x59, 0x45, 0xAD, 0xA8, 0x47, 0x2D, 0x29, 0xC9, 0x22, 0xB5,
            0xB2, 0xFC, 0x1B, 0xF3, 0xA3, 0x02, 0x74, 0x4F, 0xE3, 0x35, 0x68,
            0xA0, 0x47, 0xF4, 0x21, 0xC5, 0xDA, 0xE5, 0x68, 0xF0, 0xF5, 0xD7,
            0x40, 0xA3, 0xF1, 0xEE, 0x19, 0xFE, 0x57, 0xFD, 0x49, 0xFD, 0x4D,
            0xFD, 0xA8, 0x7E, 0x53, 0x07, 0xB5, 0x57, 0x1F, 0xD4, 0x37, 0xB5,
            0x53, 0xCF, 0xEA, 0xA8, 0xEE, 0xD5, 0xA3, 0x7A, 0x50, 0x7F, 0x57,
            0xDF, 0xA9, 0x4A, 0xFD, 0x55, 0x6D, 0xF4, 0xF7, 0x07, 0x9D, 0xF2,
            0xA0, 0xBE, 0xE8, 0xFB, 0xD7, 0x3A, 0xF5, 0x41, 0xDD, 0x42, 0xEA,
            0x7F, 0xD4, 0xBF, 0xD5, 0x67, 0xF5, 0xBD, 0x46, 0xF5, 0xFA, 0xAF,
            0x1F, 0xD5, 0x85, 0xFA, 0x8B, 0xFA, 0xB3, 0x66, 0x7C, 0x54, 0x4F,
            0xEA, 0x34, 0xB3, 0x1C, 0xED, 0xDD, 0xAD, 0xD6, 0x71, 0x02, 0x0D,
            0x97, 0xC0, 0x64, 0xD2, 0x1E, 0xF5, 0xBD, 0x9D, 0xFE, 0xFB, 0x49,
            0x5F, 0x19, 0x64, 0xA3, 0xB9, 0x2A, 0xFD, 0xFF, 0x46, 0xD5, 0x9A,
            0x73, 0xD0, 0x52, 0x3F, 0x88, 0xE4, 0x50, 0xC3, 0x95, 0xC6, 0x5E,
            0xEB, 0xBC, 0x99, 0x94, 0xA3, 0xBA, 0xD3, 0x69, 0xAF, 0xFA, 0xCA,
            0xCF, 0xCD, 0x85, 0x66, 0x37, 0x9C, 0x12, 0x24, 0x71, 0x1E, 0x75,
            0xCA, 0xAD, 0xC6, 0xBF, 0xCC, 0xF8, 0x07, 0x7D, 0x75, 0xD0, 0xE9,
            0x27, 0x9D, 0xA3, 0x17, 0x7D, 0x07, 0xF9, 0x38, 0x94, 0xCF, 0x72,
            0x00, 0xDB, 0xDD, 0x27, 0x65, 0x5D, 0x9A, 0x2F, 0xE1, 0xF2, 0xF6,
            0x45, 0x5F, 0x6D, 0xB5, 0xD4, 0x85, 0xBA, 0x01, 0x8B, 0x1C, 0x03,
            0xE9, 0x14, 0x2E, 0xCD, 0x73, 0xAD, 0x53, 0x0F, 0xFA, 0x9F, 0xC9,
            0x65, 0x2A, 0x1F, 0x1C, 0xB2, 0xCC, 0x96, 0x2F, 0x5F, 0x59, 0xC6,
            0xD7, 0x60, 0xE4, 0xB7, 0x50, 0xD3, 0x4F, 0x50, 0x1A, 0xF4, 0xBE,
            0x37, 0x8D, 0xEA, 0xB5, 0x6F, 0x38, 0x56, 0x1E, 0x47, 0x6C, 0x2F,
            0xDA, 0x5E, 0x37, 0x1A, 0x69, 0x6C, 0x76, 0xAF, 0x75, 0x3E, 0x80,
            0xD4, 0x9B, 0xC6, 0x9B, 0x52, 0x11, 0x57, 0x1E, 0x15, 0x73, 0x1D,
            0x75, 0xDA, 0x56, 0xFF, 0x7B, 0x11, 0xE7, 0x75, 0xAD, 0x24, 0x6A,
            0xFC, 0x02, 0x96, 0xBA, 0x04, 0x6B, 0xFD, 0x06, 0x96, 0xBB, 0x07,
            0x06, 0xCA, 0x37, 0x9F, 0x1E, 0xCA, 0x3F, 0x81, 0x96, 0x4B, 0xB0,
            0x34, 0xB6, 0xF1, 0x93, 0xFE, 0xCB, 0xD4, 0xC7, 0xB3, 0xBE, 0xF7,
            0x3B, 0xF8, 0xBB, 0x29, 0x79, 0xEC, 0x5B, 0xEB, 0xE5, 0x25, 0x7A,
            0xE9, 0xEA, 0x1E, 0x70, 0x6B, 0xB5, 0x2E, 0xA5, 0x43, 0x9D, 0xCF,
            0x3A, 0x37, 0x27, 0xB0, 0xB4, 0xA9, 0xBB, 0x9D, 0xB6, 0xC9, 0x85,
            0xEE, 0x4B, 0x7C, 0xDE, 0x14, 0x82, 0x38, 0xEE, 0xF4, 0xFD, 0x9D,
            0x46, 0x3D, 0xDA, 0x7E, 0xC0, 0x94, 0x13, 0xAD, 0x6A, 0x4A, 0xFB,
            0xA6, 0x2D, 0x4F, 0x7D, 0x88, 0x14, 0x2D, 0xE7, 0xAE, 0xBC, 0xBC,
            0xCA, 0xD0, 0x72, 0xEE, 0x1A, 0x7A, 0x57, 0x29, 0x77, 0xBD, 0x8A,
            0xBB, 0xD1, 0xE8, 0x56, 0xCC, 0xDD, 0xAC, 0xE2, 0x6E, 0x35, 0xBA,
            0x13, 0x73, 0xB7, 0xAB, 0xB8, 0x3B, 0x68, 0xA3, 0x52, 0xEE, 0x6E,
            0x15, 0x77, 0xAF, 0xD1, 0x83, 0x98, 0xBB, 0x5F, 0xC5, 0x3D, 0x68,
            0xF4, 0x28, 0xE6, 0x1E, 0x56, 0x71, 0x8F, 0x1A, 0x3D, 0x89, 0xB9,
            0xC7, 0x55, 0xDC, 0x13, 0xB4, 0x9D, 0x8D, 0x98, 0x7D, 0x8A, 0xD8,
            0xF7, 0xD0, 0x17, 0xEC, 0xE6, 0x79, 0xC0, 0x1E, 0x50, 0x97, 0xD0,
            0xC6, 0xBE, 0x0F, 0xDA, 0x24, 0x8F, 0x2B, 0xB3, 0x55, 0x33, 0xDB,
            0xA4, 0xED, 0x66, 0x3E, 0x75, 0xE0, 0x21, 0xBC, 0x8C, 0x84, 0x19,
            0x73, 0xDA, 0x69, 0xAB, 0x4D, 0xFA, 0xD3, 0x69, 0xEE, 0x72, 0xAE,
            0x2B, 0x71, 0xBE, 0x31, 0xE7, 0x83, 0x66, 0x1F, 0x75, 0x1B, 0xEB,
            0xB4, 0x06, 0x09, 0xBB, 0x2C, 0xEF, 0x35, 0x70, 0xB7, 0xFA, 0xDB,
            0xE4, 0xBD, 0x85, 0x79, 0x5A, 0x89, 0x3B, 0xEE, 0x43, 0xD2, 0xA8,
            0x66, 0xB6, 0x77, 0x0F, 0xB6, 0xDE, 0xE8, 0xEF, 0x56, 0xC0, 0x1D,
            0xF7, 0x21, 0x69, 0x54, 0xEB, 0x71, 0x9B, 0x3C, 0xF7, 0x3A, 0xF7,
            0x65, 0xEE, 0xB8, 0x0F, 0x49, 0xA3, 0x3A, 0xE0, 0x6E, 0x66, 0x8B,
            0xF4, 0xFA, 0xEF, 0x32, 0x73, 0xDC, 0x83, 0xA4, 0x51, 0xFD, 0x3B,
            0xEA, 0x31, 0xEE, 0x3F, 0xD2, 0xA8, 0xC1, 0xAB, 0xC5, 0x51, 0xFF,
            0xDF, 0x05, 0xBD, 0x36, 0x2F, 0x53, 0x66, 0x1E, 0x67, 0x4B, 0x37,
            0x90, 0xEF, 0x41, 0xD7, 0xE3, 0x28, 0x68, 0x37, 0x71, 0xEF, 0x91,
            0x46, 0x4D, 0xB6, 0x45, 0x9A, 0x3C, 0xCB, 0x5A, 0xE4, 0xB2, 0xE7,
            0x78, 0xD4, 0x57, 0x5F, 0x13, 0x73, 0x8D, 0x30, 0xD5, 0x97, 0x39,
            0x68, 0xD4, 0x6D, 0xC0, 0x7B, 0xA1, 0x57, 0x3B, 0xFE, 0xE7, 0x93,
            0xFE, 0xFC, 0xA4, 0x3F, 0x9F, 0xF4, 0x75, 0x0D, 0x3E, 0x50, 0xEB,
            0xCF, 0x4F, 0xBA, 0xF4, 0x26, 0xD5, 0x7C, 0xFB, 0xD7, 0x1B, 0x9D,
            0xFE, 0x51, 0x97, 0xE1, 0x93, 0x2E, 0xC3, 0xA4, 0xAF, 0x7E, 0xD1,
            0xDF, 0x9F, 0xF4, 0xB7, 0x29, 0xD7, 0x2F, 0xFA, 0xCA, 0xB4, 0x45,
            0x83, 0xFD, 0x59, 0x7F, 0xFF, 0x7C, 0xE6, 0xF5, 0x47, 0x5D, 0xB3,
            0x9F, 0xBC, 0x9C, 0xFA, 0x18, 0x93, 0x9B, 0x8F, 0x5A, 0x37, 0x5E,
            0xD7, 0x90, 0x33, 0xBC, 0x1E, 0x74, 0x19, 0xA6, 0xC5, 0xF5, 0xA8,
            0xF3, 0xFD, 0xD9, 0xDE, 0xFD, 0x6C, 0x25, 0xFD, 0xEB, 0xCD, 0xFC,
            0xA1, 0xEB, 0xCF, 0xC9, 0x8F, 0xCF, 0xFF, 0xC7, 0x7C, 0xE2, 0x3C,
            0xFC, 0x91, 0xDC, 0xFF, 0x7F, 0x1F, 0xE3, 0x2F, 0x66, 0x65, 0xFC,
            0xD1, 0x96, 0x77, 0x13, 0xF9, 0x98, 0x7F, 0xED, 0x63, 0x42, 0x1E,
            0xE7, 0xB7, 0x29, 0x9B, 0xF9, 0xF7, 0xF0, 0x7A, 0x80, 0x3E, 0xBF,
            0x02, 0x8F, 0x0A, 0xF3, 0xB0, 0xC6, 0x27, 0x07, 0xED, 0x47, 0x3F,
            0x69, 0x6F, 0xFA, 0xAC, 0xB9, 0x7C, 0x4E, 0xD7, 0x0E, 0x53, 0x2D,
            0xCE, 0x6F, 0x91, 0x66, 0xED, 0x74, 0xA5, 0x70, 0x95, 0xF6, 0x04,
            0xEB, 0x5C, 0x1C, 0xD5, 0xBB, 0x60, 0x4E, 0xC1, 0xA1, 0x4A, 0x4C,
            0x95, 0x88, 0x29, 0x1E, 0x2F, 0x53, 0x98, 0x5A, 0xC4, 0x14, 0x8F,
            0x8F, 0x29, 0x4C, 0x23, 0x62, 0x8A, 0x47, 0xC3, 0x14, 0xA6, 0x15,
            0x31, 0xC5, 0x63, 0x5F, 0x0A, 0xD3, 0x89, 0x98, 0xE2, 0xB1, 0x2E,
            0x85, 0x31, 0xD7, 0x7B, 0x98, 0x83, 0x77, 0x05, 0x36, 0x42, 0xA6,
            0x18, 0xC9, 0x6B, 0x96, 0xF3, 0xC0, 0x14, 0x22, 0xC7, 0x80, 0x1E,
            0xD0, 0x67, 0x18, 0xB8, 0xDA, 0xA7, 0xF4, 0x3A, 0x5A, 0xC1, 0xA5,
            0xD2, 0x73, 0xF2, 0xF1, 0x4A, 0x2A, 0x95, 0x9E, 0x93, 0x6F, 0xBD,
            0xBD, 0x01, 0x2E, 0x3D, 0x27, 0xDF, 0x15, 0xE4, 0xB9, 0x5A, 0xA5,
            0x74, 0x33, 0x7F, 0xBF, 0x9C, 0xD7, 0xC8, 0x75, 0xB0, 0xFE, 0xE1,
            0x91, 0x65, 0xBE, 0x4A, 0xCC, 0x57, 0xAA, 0x1F, 0x44, 0xD5, 0x85,
            0x52, 0x3A, 0x54, 0x99, 0xAB, 0x81, 0xF5, 0x52, 0x39, 0x67, 0xA5,
            0x9A, 0x43, 0x54, 0xA9, 0xFE, 0x1C, 0xAA, 0xCC, 0x55, 0xAA, 0x4B,
            0x87, 0x2A, 0x73, 0xF5, 0x22, 0xAE, 0x78, 0x16, 0x1A, 0xA3, 0x4C,
            0x9F, 0x4E, 0xED, 0x74, 0x82, 0xB1, 0x65, 0x80, 0x79, 0xDD, 0x34,
            0xCF, 0x45, 0x7B, 0x18, 0x23, 0x5A, 0xFD, 0x2F, 0x67, 0x4F, 0xC7,
            0x52, 0xD6, 0x55, 0xFD, 0x21, 0xBA, 0x4A, 0x5E, 0x85, 0xA8, 0x1A,
            0x3C, 0xC1, 0xAC, 0xE9, 0x70, 0xAD, 0xD1, 0xC2, 0xFC, 0x7D, 0x80,
            0x99, 0xF0, 0xA8, 0xFF, 0xDA, 0xE8, 0x7F, 0x03, 0xA4, 0x94, 0xF4,
            0x95, 0x3C, 0x0F, 0x51, 0xCD, 0x5C, 0x36, 0x33, 0xE7, 0x6C, 0x40,
            0x93, 0x99, 0xCB, 0xE1, 0x2A, 0xA7, 0x03, 0x5D, 0x03, 0x94, 0xAE,
            0xCA, 0xF6, 0x48, 0x8E, 0xAB, 0xAC, 0xB1, 0xE4, 0x9D, 0x0E, 0x55,
            0xE6, 0x2A, 0x79, 0xA7, 0x43, 0x95, 0xB9, 0x4A, 0xDE, 0xE9, 0x50,
            0x29, 0xAE, 0x07, 0xD8, 0x17, 0xDC, 0x41, 0x3D, 0x7F, 0xD0, 0x69,
            0xD7, 0xB0, 0x43, 0xBB, 0x85, 0x13, 0x0E, 0xDA, 0xC7, 0xFE, 0x4E,
            0xCB, 0xFE, 0x13, 0x66, 0x24, 0x07, 0x18, 0x8B, 0x96, 0xBA, 0x7C,
            0x96, 0x92, 0x9E, 0x3A, 0xAB, 0xE7, 0xA3, 0xD6, 0x73, 0x80, 0x13,
            0x8A, 0x53, 0x56, 0x0F, 0xE7, 0x25, 0x0E, 0xD1, 0x64, 0xF5, 0xFC,
            0x03, 0x76, 0x42, 0x5F, 0xF4, 0x18, 0x9B, 0xD3, 0xC2, 0x79, 0x86,
            0x43, 0xB4, 0x59, 0x2D, 0x39, 0x6E, 0xCE, 0x53, 0x1C, 0xA2, 0x7B,
            0x37, 0x37, 0xE7, 0x39, 0x0E, 0xD1, 0xBF, 0x9B, 0x9B, 0xF3, 0x24,
            0x77, 0xC6, 0x61, 0x7C, 0xC0, 0x3F, 0x03, 0xC9, 0xE1, 0xF2, 0x4C,
            0xB5, 0x90, 0x89, 0xF3, 0x06, 0x87, 0x68, 0x84, 0x4C, 0x5C, 0x8D,
            0x3B, 0x44, 0xCB, 0xAC, 0xA3, 0xD3, 0xC8, 0x3C, 0x57, 0x27, 0xE6,
            0xE2, 0x6A, 0xD4, 0x21, 0x7A, 0x31, 0x17, 0x57, 0x83, 0x66, 0x27,
            0xF2, 0x30, 0x9F, 0x0A, 0x9E, 0xA0, 0xBE, 0x9F, 0x14, 0xCD, 0x67,
            0x96, 0x7C, 0x3C, 0x5A, 0xCE, 0x5D, 0xAD, 0xE2, 0xE6, 0xFC, 0x25,
            0x8D, 0xAE, 0x57, 0x71, 0x73, 0x1E, 0x94, 0x46, 0x37, 0xAB, 0xB8,
            0x39, 0x9F, 0x4A, 0xA3, 0xDB, 0x55, 0xDC, 0x9C, 0x8F, 0xA5, 0xD1,
            0xDD, 0x2A, 0x6E, 0xCE, 0xE7, 0xD2, 0xE8, 0x7E, 0x15, 0x37, 0xEF,
            0x83, 0x78, 0xEE, 0xE8, 0xF6, 0xA2, 0x53, 0x8C, 0x3E, 0x26, 0xCF,
            0x52, 0x0B, 0x58, 0xF8, 0xBA, 0x27, 0x44, 0x23, 0x60, 0xE1, 0x6B,
            0x99, 0x10, 0xAD, 0x80, 0x85, 0xAF, 0x4F, 0x42, 0x74, 0x02, 0x96,
            0xB8, 0xE6, 0x5E, 0x61, 0x9F, 0xF0, 0x7A, 0x6E, 0xFF, 0xE6, 0xAC,
            0xF5, 0x8B, 0x3A, 0xCD, 0xAD, 0xD5, 0x9F, 0x3B, 0xE4, 0x70, 0x12,
            0xBE, 0x4A, 0xC8, 0x17, 0xD7, 0x1B, 0x87, 0x8B, 0xD7, 0x2A, 0x39,
            0x9C, 0x84, 0xAF, 0x11, 0xF2, 0xC5, 0x75, 0xC9, 0xE1, 0xE2, 0x39,
            0x61, 0x0E, 0x27, 0xE1, 0x8B, 0xE7, 0x85, 0x39, 0x9C, 0x84, 0x2F,
            0x9E, 0x1B, 0xE6, 0x70, 0x3C, 0xDF, 0x11, 0xCE, 0xB9, 0x4D, 0x2C,
            0xC0, 0x38, 0xEF, 0xF5, 0x9B, 0x99, 0x76, 0xCB, 0xF2, 0x3A, 0xBC,
            0xE3, 0xDC, 0x42, 0xDC, 0x0C, 0xEE, 0x54, 0x9B, 0xBF, 0xEE, 0xE1,
            0xC4, 0xEB, 0xA8, 0xBE, 0xEA, 0x2B, 0xDC, 0xDD, 0x88, 0x47, 0xE7,
            0xB2, 0x44, 0x8A, 0xDD, 0xC4, 0x16, 0x98, 0xD6, 0xB0, 0x9F, 0x7B,
            0x1C, 0x09, 0x3F, 0x2F, 0xE3, 0x6B, 0x30, 0x76, 0xBA, 0x81, 0x93,
            0xBA, 0x53, 0x50, 0xC6, 0x8D, 0xC7, 0xC8, 0x61, 0x62, 0x1E, 0x17,
            0xF1, 0xB3, 0x81, 0x15, 0x53, 0x0F, 0x3B, 0x2F, 0x31, 0x53, 0x18,
            0xDF, 0xF3, 0x05, 0xCE, 0xEF, 0xCB, 0xF1, 0x16, 0x25, 0x1C, 0xB1,
            0x3D, 0x42, 0x4F, 0x8C, 0x69, 0x06, 0xFF, 0x08, 0xFB, 0x8E, 0xA6,
            0xB7, 0x7E, 0x5A, 0x58, 0x2B, 0x8F, 0x25, 0xC6, 0xA3, 0xED, 0x8B,
            0x9C, 0x55, 0xFC, 0x7B, 0x21, 0xAE, 0x5C, 0x0E, 0x49, 0x94, 0xC8,
            0xB5, 0xCE, 0x87, 0x59, 0xE5, 0x98, 0xD8, 0xA3, 0x13, 0xAC, 0x74,
            0x5C, 0x14, 0x4B, 0x3C, 0x1F, 0xCA, 0x63, 0x89, 0xEF, 0x05, 0xEE,
            0x1A, 0xAF, 0xDB, 0x43, 0x9C, 0xC5, 0x57, 0x75, 0x09, 0xE7, 0xB4,
            0xD7, 0x50, 0x93, 0x31, 0x63, 0x1E, 0x8D, 0x9C, 0x3B, 0xF5, 0xAB,
            0xC6, 0x19, 0x5B, 0x1D, 0x20, 0xFF, 0x27, 0xEB, 0xD3, 0xE4, 0x81,
            0x9B, 0xEC, 0x6C, 0xFC, 0x5F, 0xFA, 0xFB, 0xA4, 0x11, 0xD8, 0xE7,
            0x4B, 0xD8, 0xE4, 0x9A, 0xF3, 0xAB, 0x3E, 0xD2, 0x5C, 0x0B, 0x35,
            0x57, 0x2B, 0x34, 0xE7, 0xD7, 0x81, 0xA4, 0xB9, 0x11, 0x6A, 0xAE,
            0x57, 0x68, 0xCE, 0xAF, 0x0C, 0x49, 0x73, 0x2B, 0xD4, 0xDC, 0xAC,
            0xD0, 0x9C, 0x5F, 0x2D, 0x92, 0xE6, 0x4E, 0xA8, 0xB9, 0x5D, 0xA1,
            0x39, 0xBF, 0x96, 0x24, 0xCD, 0xBD, 0x50, 0x73, 0xB7, 0x42, 0x73,
            0x7E, 0xA5, 0x49, 0x9A, 0x07, 0xA1, 0xE6, 0x7E, 0x85, 0xE6, 0x41,
            0xA4, 0x79, 0x14, 0x6A, 0x76, 0x67, 0xC1, 0xA6, 0x0F, 0x38, 0xCE,
            0x88, 0x6D, 0x10, 0x35, 0x19, 0xF6, 0x0E, 0x3C, 0xCE, 0xF1, 0x7C,
            0x53, 0x18, 0x47, 0x76, 0x02, 0x1D, 0x38, 0x22, 0xDF, 0xCF, 0x91,
            0x77, 0xC4, 0x91, 0xC3, 0x10, 0xD3, 0xBD, 0x17, 0x27, 0xFA, 0x0A,
            0xF8, 0xEB, 0x44, 0x7E, 0xD2, 0x28, 0xE2, 0x30, 0xE7, 0xC0, 0x66,
            0x2C, 0x7C, 0x84, 0xFE, 0x91, 0xCA, 0x6F, 0xAE, 0xCC, 0xD8, 0xFB,
            0x04, 0x77, 0x97, 0x9C, 0x32, 0x29, 0xA7, 0xE3, 0x59, 0x23, 0x4C,
            0x39, 0x6E, 0xA1, 0x2E, 0x4C, 0xD4, 0x69, 0xE5, 0x8D, 0x75, 0x3D,
            0x9C, 0xD0, 0x9B, 0x5D, 0xCA, 0x66, 0x6E, 0x07, 0x65, 0x99, 0x1C,
            0x77, 0xFD, 0x0E, 0xEE, 0x5A, 0xC8, 0xDD, 0xBC, 0x83, 0xBB, 0x11,
            0x72, 0xB7, 0xEF, 0xE0, 0x6E, 0xB3, 0xDC, 0x6E, 0xFD, 0x7F, 0xA3,
            0xEB, 0xCF, 0x44, 0xA0, 0x1E, 0xED, 0x8A, 0xAD, 0x8C, 0x43, 0xBE,
            0x5B, 0x98, 0x5B, 0x5C, 0x41, 0x4B, 0xD9, 0xC3, 0x18, 0xF7, 0xAC,
            0xDC, 0xBA, 0x83, 0x46, 0xFD, 0x12, 0x8A, 0xB8, 0x28, 0xDD, 0xF8,
            0x8C, 0x19, 0xE5, 0x6F, 0xE6, 0xF9, 0x53, 0xE8, 0xF1, 0xA5, 0x7D,
            0x2A, 0x29, 0x4F, 0x4A, 0x6F, 0x3E, 0x4E, 0x5A, 0x82, 0x5C, 0x72,
            0x86, 0x33, 0xA0, 0x54, 0x4A, 0x4A, 0xA6, 0x34, 0x1B, 0x92, 0xA1,
            0x91, 0xF9, 0x0E, 0x66, 0x67, 0xD7, 0xD0, 0x57, 0x6C, 0xC1, 0x76,
            0xC6, 0xFE, 0x26, 0x3E, 0xF6, 0x39, 0x9A, 0xD9, 0xE5, 0x91, 0xC4,
            0xF6, 0x32, 0x6B, 0xA5, 0xFA, 0x0B, 0x7B, 0x80, 0x65, 0x3A, 0xCA,
            0xE1, 0x8A, 0x00, 0x23, 0x55, 0x8D, 0xFD, 0xAF, 0xC1, 0x27, 0xCC,
            0xF5, 0x09, 0x66, 0xDA, 0x4F, 0xD0, 0x3B, 0x52, 0xF4, 0xF7, 0x51,
            0x51, 0xE4, 0xBD, 0x5B, 0x93, 0x9E, 0xC3, 0x70, 0x5E, 0x1E, 0xAA,
            0xB3, 0xF3, 0x50, 0x9D, 0x9D, 0x87, 0xFA, 0xEC, 0x3C, 0xD4, 0x67,
            0xE7, 0xA1, 0x39, 0x3B, 0x0F, 0xCD, 0xD9, 0x79, 0x68, 0xCF, 0xCE,
            0x43, 0x7B, 0x76, 0x1E, 0xBA, 0xB3, 0xF3, 0xD0, 0x9D, 0x9D, 0x87,
            0xFE, 0xEC, 0x3C, 0xF4, 0xD9, 0x3C, 0xFC, 0x0A, 0xBD, 0x82, 0x1F,
            0x61, 0x5F, 0x42, 0x49, 0xB8, 0x4C, 0x5B, 0xAC, 0xE7, 0x55, 0x6E,
            0x99, 0x33, 0xDF, 0x72, 0x1D, 0x0E, 0x63, 0xC5, 0xCD, 0x47, 0xC2,
            0x9A, 0x6F, 0x8B, 0x0E, 0x57, 0x5B, 0xD6, 0x46, 0xC0, 0x9A, 0x6F,
            0x5D, 0x0E, 0xD7, 0x58, 0xD6, 0x4E, 0xC0, 0x9A, 0x6F, 0x2F, 0x0E,
            0xD7, 0xCE, 0xAC, 0x74, 0xA2, 0x5A, 0x46, 0x4B, 0x58, 0x3B, 0xCB,
            0x3A, 0x08, 0x58, 0xF3, 0x3E, 0xED, 0x70, 0x79, 0xCF, 0x0D, 0x71,
            0x8E, 0xEF, 0xDB, 0x3C, 0x0F, 0xC7, 0x68, 0xE8, 0x4B, 0x98, 0x47,
            0x98, 0x11, 0xF4, 0x5E, 0x2D, 0x9F, 0x9A, 0x28, 0xE3, 0x79, 0x5E,
            0x17, 0xFF, 0xB8, 0x61, 0xB9, 0xE2, 0x18, 0xC9, 0x14, 0xC6, 0x9D,
            0x90, 0xE5, 0x57, 0xF3, 0x9F, 0xF4, 0xB7, 0xC9, 0xFD, 0x0B, 0xCC,
            0xC5, 0x3F, 0xA8, 0x8F, 0xFA, 0xEA, 0x2A, 0x53, 0x0E, 0x9F, 0x57,
            0xA6, 0x3F, 0xBF, 0xA6, 0x27, 0x7D, 0xB4, 0x9F, 0x50, 0xE2, 0x92,
            0xE9, 0x2C, 0x9D, 0xEA, 0x92, 0xCE, 0x5A, 0xA0, 0xB3, 0x16, 0xEA,
            0xCC, 0xAF, 0xE3, 0x9D, 0xCE, 0x46, 0xA0, 0xB3, 0x11, 0xEA, 0xCC,
            0xAF, 0xE0, 0x9D, 0xCE, 0x56, 0xA0, 0xB3, 0x15, 0xEA, 0xCC, 0xAF,
            0xDD, 0x9D, 0xCE, 0x4E, 0xA0, 0xB3, 0x13, 0xEA, 0xCC, 0xAF, 0xDA,
            0x9D, 0xCE, 0x5E, 0xA0, 0x33, 0xDF, 0xAE, 0x1D, 0x2E, 0xBF, 0x5E,
            0x77, 0x3A, 0x07, 0x81, 0xCE, 0x41, 0xA8, 0x73, 0x14, 0xEA, 0x1C,
            0x05, 0x3A, 0xC7, 0xAC, 0x4E, 0x5C, 0x6D, 0xEF, 0x60, 0x66, 0xCD,
            0x71, 0xF9, 0x18, 0x9E, 0x89, 0xD6, 0x22, 0x17, 0x19, 0x4B, 0x38,
            0x4C, 0x99, 0xC7, 0x3C, 0x89, 0x42, 0xBB, 0x1F, 0xE1, 0xFA, 0x40,
            0x2E, 0xC5, 0x6B, 0x09, 0xD7, 0x43, 0x39, 0x44, 0x8E, 0xA3, 0xB4,
            0x3E, 0x5A, 0x27, 0x85, 0x9A, 0xBE, 0xAA, 0x1D, 0xCC, 0x96, 0x64,
            0x3B, 0x1D, 0x25, 0xB4, 0xE3, 0x7C, 0x53, 0xF8, 0x54, 0xE2, 0x93,
            0x96, 0xFD, 0xA0, 0xF0, 0x59, 0xD8, 0xCF, 0xFA, 0x7F, 0xA3, 0xDD,
            0x78, 0x58, 0x0D, 0xD1, 0x51, 0xDF, 0x45, 0x32, 0x17, 0x30, 0x6E,
            0x6C, 0xA0, 0xBF, 0xAA, 0x21, 0x7E, 0x69, 0x63, 0xF5, 0xBE, 0x81,
            0xCF, 0xD0, 0x55, 0x15, 0xE1, 0x6A, 0x06, 0x57, 0x07, 0xB8, 0x7E,
            0x7E, 0xB2, 0x69, 0x89, 0x6B, 0x2C, 0x0E, 0x9F, 0xE8, 0x68, 0x18,
            0x5C, 0x27, 0xCC, 0x5F, 0x3F, 0xE3, 0xE8, 0x19, 0xE6, 0x25, 0x62,
            0x98, 0x11, 0x2D, 0x9B, 0xA7, 0x71, 0x46, 0x74, 0xAC, 0x96, 0xC9,
            0x22, 0x2A, 0xD6, 0x4E, 0x1B, 0x8B, 0xE1, 0x6C, 0x54, 0x59, 0x6B,
            0x76, 0x6C, 0xB9, 0x2B, 0x6B, 0xC9, 0x31, 0xA3, 0xAB, 0xB1, 0x65,
            0xAA, 0xC0, 0x3A, 0x1C, 0xAE, 0xB5, 0xD6, 0xE1, 0xCA, 0x5E, 0x59,
            0x4B, 0xB7, 0xF0, 0xFC, 0x4E, 0xC7, 0xE2, 0xC8, 0xD2, 0x15, 0xEC,
            0x11, 0xE5, 0x4A, 0x30, 0xD8, 0x12, 0xF4, 0x2C, 0x66, 0xB4, 0x39,
            0xE3, 0x31, 0x93, 0xC5, 0x70, 0xB9, 0xAA, 0xAD, 0xD5, 0xFB, 0xB9,
            0xD7, 0x4C, 0x61, 0x2A, 0x9B, 0x1F, 0xCE, 0x52, 0xB5, 0x67, 0x75,
            0xAE, 0x5C, 0xB5, 0xB5, 0x94, 0xB1, 0x6B, 0xCB, 0xA2, 0xC8, 0x4E,
            0xA5, 0x96, 0x50, 0x5B, 0x1B, 0x0C, 0x19, 0x9D, 0x93, 0xC5, 0x70,
            0x1A, 0x1B, 0x6B, 0x83, 0x81, 0xB5, 0x53, 0x63, 0x6D, 0x30, 0x64,
            0x5A, 0xA6, 0xB3, 0x01, 0xD7, 0x0E, 0x1A, 0xEB, 0x79, 0x55, 0xA6,
            0x76, 0x1B, 0xEB, 0x77, 0x63, 0x46, 0x5B, 0x6F, 0x73, 0xC4, 0xD5,
            0x4A, 0xE3, 0x59, 0x88, 0xD3, 0xD5, 0xDA, 0xD2, 0x57, 0x36, 0xFE,
            0x32, 0x85, 0xAA, 0x3C, 0x14, 0x67, 0xED, 0xD6, 0x5A, 0xA0, 0xB2,
            0x6B, 0xC8, 0x14, 0xAA, 0xF1, 0x50, 0x9C, 0xC5, 0x5B, 0x6B, 0x83,
            0x0A, 0x5A, 0x0C, 0x87, 0xEA, 0x3C, 0x14, 0x67, 0x87, 0xD6, 0x6B,
            0x7B, 0x15, 0xEB, 0xE7, 0xAD, 0x6D, 0x77, 0x9C, 0xCD, 0x5B, 0x6B,
            0xCF, 0x0A, 0x5A, 0x17, 0x87, 0x9A, 0x2C, 0x6A, 0x62, 0x2D, 0xDA,
            0x79, 0x3D, 0x39, 0x8F, 0x69, 0x3D, 0x26, 0xCE, 0xA7, 0x3A, 0xCF,
            0x06, 0x23, 0x5B, 0xBA, 0xCE, 0xDA, 0x20, 0x87, 0x19, 0x2C, 0x13,
            0x57, 0xC7, 0xBD, 0xE7, 0x2F, 0x75, 0x06, 0x45, 0xFE, 0xC2, 0xB7,
            0xF4, 0xDE, 0x7A, 0x0B, 0x8F, 0xF0, 0xFB, 0xE9, 0x96, 0xF5, 0x95,
            0xDE, 0xDA, 0xA9, 0x9D, 0x4F, 0xE8, 0x39, 0x5C, 0x17, 0xE0, 0x38,
            0x7F, 0xE9, 0xAD, 0xAD, 0x10, 0xC7, 0xD9, 0xAB, 0xB7, 0xF6, 0x1A,
            0xD8, 0xB1, 0xA6, 0xB7, 0x3E, 0x83, 0xE3, 0x03, 0xAF, 0xD3, 0x79,
            0x0D, 0x8E, 0x0F, 0x5C, 0x69, 0x07, 0x5B, 0x03, 0x23, 0xF4, 0x96,
            0x5C, 0x1D, 0x0C, 0x5E, 0xBF, 0xCD, 0x59, 0x78, 0xF0, 0xEA, 0xA0,
            0xCA, 0xF4, 0x5B, 0x83, 0xD7, 0x66, 0x7B, 0xB0, 0x30, 0x67, 0x93,
            0xC1, 0xEB, 0xBB, 0xEA, 0x4C, 0xBF, 0x33, 0xD8, 0xBA, 0xE0, 0xE7,
            0x26, 0x43, 0x50, 0x0F, 0xFC, 0x48, 0x37, 0x78, 0x7E, 0x8B, 0xB6,
            0xE3, 0xCB, 0x3B, 0x06, 0xB6, 0xE3, 0x5A, 0xDE, 0x60, 0x6B, 0x63,
            0x64, 0x31, 0xA3, 0xAD, 0x07, 0x9C, 0x45, 0x70, 0x16, 0x19, 0xBD,
            0xBE, 0x13, 0x6D, 0xC7, 0x95, 0x63, 0xF4, 0x46, 0x90, 0x3A, 0x33,
            0x62, 0x8D, 0x51, 0x6D, 0x34, 0x19, 0x64, 0x1B, 0x21, 0x39, 0xAF,
            0x1A, 0xBD, 0x5E, 0xA4, 0x9F, 0x9F, 0x0B, 0xE0, 0x90, 0x7D, 0x84,
            0xE4, 0x7C, 0x7A, 0x8C, 0xEA, 0xA5, 0x61, 0x7D, 0x75, 0xF2, 0x46,
            0x0E, 0x44, 0x72, 0xD6, 0x9C, 0x16, 0x65, 0xE7, 0xFA, 0xE1, 0x29,
            0x2A, 0x7B, 0x9B, 0x99, 0x9D, 0x76, 0x11, 0x92, 0x6B, 0xCD, 0xD3,
            0xA2, 0xEC, 0x9C, 0x77, 0x4C, 0xD6, 0x83, 0xF8, 0x9E, 0xDB, 0xCC,
            0x79, 0x37, 0x01, 0x1F, 0x5F, 0xE7, 0x06, 0xEB, 0x74, 0x4F, 0x6C,
            0x0E, 0x0D, 0xCE, 0x59, 0xBD, 0xCE, 0xE2, 0xDC, 0xEC, 0x80, 0x9F,
            0x71, 0x6F, 0xBC, 0x96, 0xC0, 0xCF, 0x6D, 0xAB, 0xA0, 0x1C, 0x5D,
            0xA6, 0xDD, 0xE3, 0xA8, 0x41, 0x7A, 0xB9, 0x5A, 0xAE, 0x60, 0xDD,
            0xE5, 0x33, 0x6E, 0x32, 0xB3, 0x74, 0xD7, 0x23, 0xF2, 0xF5, 0x51,
            0x79, 0xFD, 0x61, 0x05, 0xBD, 0x66, 0x6E, 0x76, 0x3D, 0x44, 0xFE,
            0xD8, 0x67, 0xEA, 0xC5, 0xF5, 0x8D, 0xE3, 0xBC, 0x7B, 0xCE, 0xCF,
            0xC7, 0xFD, 0xB1, 0x93, 0xF7, 0x8A, 0x29, 0x98, 0x6D, 0x71, 0x7C,
            0xF5, 0x62, 0x4D, 0xC1, 0xF7, 0xA4, 0xB5, 0xB7, 0xAA, 0xA0, 0x12,
            0xE5, 0xB0, 0x63, 0x84, 0xE5, 0xF3, 0xE0, 0x56, 0x07, 0x75, 0x66,
            0x4E, 0x54, 0x7B, 0xB3, 0x6C, 0xEA, 0xA3, 0x79, 0x3B, 0x7D, 0x80,
            0x7F, 0x9C, 0xC5, 0xBB, 0x39, 0xBD, 0x54, 0x8B, 0xB5, 0x65, 0xE2,
            0x7B, 0x13, 0x5C, 0xB7, 0xA0, 0x36, 0xDE, 0x1E, 0x8D, 0xE5, 0xE1,
            0xD7, 0x3F, 0xAD, 0xC5, 0xE4, 0xD7, 0x2B, 0x95, 0x1D, 0xCD, 0x78,
            0xDC, 0xE4, 0xE1, 0xF8, 0x3A, 0x6D, 0x66, 0x6B, 0x12, 0x8E, 0xB3,
            0x67, 0xE3, 0x59, 0xB4, 0xCA, 0xAE, 0x71, 0xEA, 0x00, 0x97, 0x5F,
            0x9D, 0x10, 0x8E, 0xEF, 0x15, 0x70, 0x85, 0xE2, 0xF8, 0xB8, 0xBE,
            0xBF, 0x09, 0xEC, 0x92, 0xEF, 0x8B, 0x42, 0xCD, 0x39, 0xE4, 0x60,
            0x91, 0x75, 0x66, 0x65, 0x40, 0xBD, 0xA0, 0xAB, 0x15, 0xBE, 0x47,
            0xDA, 0x04, 0xF5, 0x92, 0xDB, 0x5D, 0x70, 0x1E, 0x83, 0x25, 0x0A,
            0x3D, 0x19, 0xF7, 0x91, 0xE8, 0x6F, 0xB7, 0xFB, 0x44, 0x29, 0xE6,
            0x54, 0x10, 0xA3, 0x22, 0xCC, 0xA9, 0x0B, 0x46, 0xE0, 0xE3, 0x1B,
            0xA6, 0x1E, 0x14, 0xBE, 0xD1, 0x2E, 0xDE, 0xED, 0x92, 0x48, 0x10,
            0xF7, 0x23, 0xC4, 0x0E, 0xE0, 0xDD, 0x7C, 0x24, 0x69, 0x09, 0x8B,
            0x8C, 0x87, 0xF9, 0xD4, 0x26, 0xDE, 0x3B, 0x5C, 0xDE, 0xF7, 0xF1,
            0x0F, 0xF3, 0x69, 0x8F, 0x89, 0x12, 0xCE, 0xBD, 0xEF, 0x4C, 0x8A,
            0xE6, 0xB8, 0x6F, 0xA1, 0x0C, 0xCB, 0x33, 0xA8, 0x1C, 0x92, 0xE3,
            0x2A, 0xEF, 0x6B, 0xAE, 0x91, 0x71, 0x5A, 0x1E, 0x6C, 0x5C, 0x2A,
            0x9E, 0x0A, 0x6F, 0x55, 0xEA, 0xFD, 0x1F, 0x39, 0xA4, 0xE3, 0x7A,
            0x52, 0xFE, 0xD3, 0xE8, 0x34, 0xC3, 0x20, 0xF9, 0x38, 0x95, 0xE4,
            0x76, 0x73, 0x3C, 0xD1, 0x03, 0xE4, 0xF1, 0x4D, 0xB9, 0xC8, 0xA4,
            0x69, 0x9E, 0xDF, 0x55, 0x70, 0x85, 0x3C, 0x3C, 0x1A, 0xF9, 0xCC,
            0x3B, 0x4E, 0x5E, 0xAD, 0x3E, 0xB7, 0x03, 0x7D, 0x00, 0xFC, 0x57,
            0x85, 0x3B, 0xE6, 0xF4, 0x54, 0x84, 0x0C, 0x8D, 0xCC, 0x8F, 0x50,
            0xDB, 0xE8, 0x05, 0xF4, 0x1E, 0xA6, 0x57, 0x7D, 0xE7, 0x2A, 0xF2,
            0xDC, 0x1C, 0x0E, 0x99, 0xB0, 0x36, 0x4E, 0x90, 0x7B, 0x8C, 0xA7,
            0x3A, 0x80, 0x4D, 0x29, 0x52, 0x08, 0x6D, 0x56, 0x42, 0x2D, 0xB9,
            0x4C, 0x4B, 0xDC, 0xDA, 0x53, 0x81, 0x25, 0x4B, 0x98, 0x9E, 0x92,
            0x37, 0x6D, 0xEC, 0xC4, 0xC8, 0x52, 0xDA, 0x52, 0x8E, 0x6A, 0x00,
            0xDF, 0x48, 0x49, 0xAB, 0xA5, 0x76, 0xC1, 0x11, 0xD6, 0x94, 0x9F,
            0xF2, 0xAC, 0x28, 0x62, 0x3C, 0x97, 0x87, 0x14, 0x8A, 0xB8, 0x76,
            0xD0, 0x03, 0x51, 0x3C, 0xB5, 0x8B, 0xDC, 0x0E, 0xEB, 0x26, 0x87,
            0x0B, 0x99, 0xCA, 0xED, 0xAD, 0x8C, 0x24, 0x46, 0x13, 0x1B, 0xF7,
            0x06, 0x56, 0x37, 0xED, 0xD2, 0xD4, 0x25, 0xF6, 0x90, 0x26, 0x5A,
            0xD4, 0x3D, 0xD7, 0x56, 0xC6, 0x49, 0xF8, 0x6A, 0x21, 0x5F, 0x5D,
            0xE0, 0x0B, 0xFB, 0xD3, 0x3C, 0x86, 0x78, 0x4C, 0xD9, 0xE9, 0x64,
            0xE5, 0xD2, 0x1B, 0x17, 0x76, 0xEA, 0x37, 0xB5, 0x83, 0xD8, 0x4F,
            0x8C, 0xAE, 0x0B, 0xFB, 0x16, 0xB9, 0x5C, 0x5A, 0x8F, 0xA9, 0xCB,
            0x17, 0x60, 0xC3, 0xEB, 0x6F, 0x02, 0x1D, 0x69, 0x19, 0xE2, 0x3F,
            0x16, 0x62, 0x08, 0x52, 0x08, 0x94, 0x75, 0x11, 0x0A, 0xB1, 0x05,
            0x53, 0x29, 0x4E, 0x06, 0x9F, 0x07, 0xB8, 0x52, 0x18, 0x55, 0x77,
            0x03, 0xA3, 0x0C, 0x3D, 0x23, 0x19, 0xEA, 0x2E, 0xA1, 0xCB, 0x9C,
            0xD5, 0x2A, 0xCE, 0x4A, 0xC4, 0x59, 0xAF, 0xE2, 0xAC, 0x33, 0x9C,
            0x38, 0x2F, 0x71, 0xCF, 0xA7, 0x6D, 0x02, 0x0B, 0x96, 0xB1, 0x52,
            0x5E, 0xD7, 0xEE, 0x64, 0x58, 0x29, 0xAF, 0x7B, 0xB3, 0x89, 0x0C,
            0xCB, 0xF1, 0x52, 0x3B, 0xE5, 0x4B, 0xEF, 0x10, 0x1C, 0x87, 0xA9,
            0x8B, 0x27, 0x15, 0xC6, 0xA1, 0xD2, 0x53, 0xBA, 0xBD, 0x7D, 0x6F,
            0x1F, 0xED, 0x6F, 0xAF, 0x91, 0x5F, 0xA7, 0xB1, 0x52, 0x17, 0xF3,
            0x9B, 0x17, 0xBA, 0x79, 0x1E, 0xCD, 0x95, 0x89, 0x97, 0x2F, 0x69,
            0xC4, 0xB1, 0x25, 0x7C, 0xBB, 0x8D, 0x0C, 0x2D, 0x65, 0xAE, 0x56,
            0x31, 0xE7, 0xF3, 0x4C, 0xF3, 0x8C, 0x4D, 0x34, 0x3E, 0x95, 0xB0,
            0x65, 0xC6, 0xF8, 0x89, 0xFA, 0x12, 0xB6, 0xCC, 0x18, 0x3F, 0x59,
            0x5F, 0xC2, 0x96, 0x19, 0x1B, 0x41, 0x6F, 0x91, 0x7A, 0xCE, 0x3E,
            0x87, 0x5A, 0x3E, 0x6B, 0x5F, 0x42, 0x97, 0x39, 0xE3, 0xF5, 0x80,
            0x0C, 0xCB, 0xF1, 0x96, 0x67, 0x14, 0x6B, 0x64, 0x50, 0x0B, 0xA6,
            0x7E, 0x55, 0xB9, 0x27, 0x00, 0x96, 0x18, 0x92, 0x35, 0x2B, 0x99,
            0x3B, 0x85, 0x4F, 0x62, 0xA4, 0x9E, 0x49, 0xF3, 0x6B, 0xBD, 0x8C,
            0x46, 0xD6, 0x23, 0x44, 0xD6, 0xEF, 0xE6, 0x19, 0xF0, 0x95, 0x27,
            0xF7, 0x00, 0xE3, 0xDF, 0xD1, 0x2B, 0xAF, 0x04, 0x9B, 0x62, 0xBD,
            0xD3, 0xDF, 0x84, 0xC4, 0xFD, 0xF7, 0x31, 0xC1, 0x17, 0xA2, 0x52,
            0x3C, 0xE6, 0x59, 0xD4, 0x6B, 0x9D, 0x7A, 0xA7, 0x70, 0x0F, 0x38,
            0xC5, 0xE2, 0x63, 0x88, 0x03, 0xDF, 0xE8, 0x7C, 0x9A, 0x67, 0x26,
            0xFC, 0x5B, 0x13, 0x73, 0x48, 0x9F, 0xEB, 0x15, 0xE6, 0xA1, 0x57,
            0x5A, 0x9F, 0x7B, 0x73, 0x8A, 0x7B, 0x1A, 0x3E, 0xAC, 0x07, 0x99,
            0x44, 0xCC, 0xFE, 0xC5, 0x5B, 0x3D, 0xE7, 0x38, 0x97, 0xB8, 0x98,
            0xE9, 0x5A, 0xDF, 0xA7, 0x77, 0x84, 0xA5, 0x39, 0x7C, 0x04, 0x27,
            0x1D, 0xF7, 0x52, 0x69, 0x04, 0x27, 0x1D, 0xF7, 0x48, 0x69, 0x04,
            0x27, 0xBD, 0xEC, 0x7D, 0xD2, 0x98, 0x58, 0xFE, 0xCE, 0xCE, 0xB1,
            0xEA, 0x48, 0xCA, 0xA5, 0xA4, 0x65, 0xDC, 0x33, 0x02, 0xA9, 0x94,
            0xB4, 0x4C, 0xCD, 0xCA, 0xA4, 0xCA, 0x86, 0x29, 0x0D, 0x2B, 0xC3,
            0x97, 0xC7, 0xBD, 0x43, 0x22, 0x95, 0x12, 0xCB, 0xD0, 0x5C, 0xD9,
            0xBD, 0xA1, 0x9D, 0xF7, 0xA5, 0x34, 0x76, 0xC9, 0x88, 0x2B, 0x43,
            0xB7, 0xBE, 0xB8, 0x0C, 0xD6, 0x7C, 0xB4, 0xDA, 0xE0, 0xB5, 0x48,
            0xE5, 0x63, 0xCD, 0x61, 0xB4, 0x6C, 0x9A, 0x3D, 0x15, 0x51, 0x9B,
            0x4A, 0xE5, 0xFD, 0x39, 0x15, 0x1F, 0x9B, 0x4A, 0xE5, 0x7D, 0x3A,
            0x15, 0xED, 0x9A, 0x4A, 0x8D, 0xDF, 0x5B, 0xC3, 0x61, 0x78, 0x86,
            0x56, 0xC0, 0x90, 0xF2, 0x8A, 0x30, 0x66, 0xB4, 0xC4, 0xD0, 0x65,
            0x19, 0x7A, 0x01, 0x43, 0x9F, 0x60, 0x78, 0x02, 0x0F, 0x33, 0x6F,
            0x18, 0xB8, 0x51, 0x18, 0x3B, 0x8E, 0x23, 0xC0, 0x1E, 0x46, 0xE5,
            0xF8, 0x69, 0xA6, 0x35, 0x72, 0x4B, 0x4D, 0x7B, 0x65, 0x7E, 0xBD,
            0x02, 0xF7, 0xD8, 0xC2, 0x38, 0xF5, 0xC7, 0xAC, 0xA6, 0x92, 0x5C,
            0xAC, 0xC9, 0x5F, 0x33, 0xCA, 0xF5, 0x94, 0xA4, 0x62, 0x2D, 0xC7,
            0x79, 0xEF, 0x0B, 0xDB, 0xE8, 0x0B, 0x8C, 0xBA, 0x69, 0xE6, 0x14,
            0x72, 0xC9, 0x66, 0xE2, 0x60, 0xF1, 0xB7, 0x0E, 0x76, 0x41, 0xAD,
            0x99, 0x7C, 0x6C, 0x61, 0x04, 0xBC, 0xCD, 0x68, 0x90, 0x49, 0xC7,
            0x5A, 0x4F, 0xD0, 0xE2, 0x6F, 0x15, 0xEE, 0xC8, 0xE0, 0x33, 0x2D,
            0xF7, 0xB3, 0x0D, 0x24, 0x7A, 0xE5, 0xF2, 0x6B, 0x34, 0xBB, 0xF7,
            0x43, 0xF8, 0xBF, 0x79, 0xF2, 0x9E, 0x3C, 0x70, 0x4C, 0xF9, 0xDC,
            0x9C, 0xA3, 0xBF, 0xA4, 0xD1, 0xA5, 0xE6, 0x76, 0x4A, 0x78, 0xDC,
            0x92, 0xC7, 0x1F, 0x7F, 0x70, 0xDE, 0x46, 0x5E, 0x6C, 0x76, 0x84,
            0xBE, 0x41, 0x9B, 0xBC, 0x04, 0xCF, 0xD8, 0xC3, 0x0C, 0x38, 0x2C,
            0xC5, 0xFB, 0x79, 0x96, 0x39, 0x09, 0x77, 0x6E, 0x52, 0x29, 0x29,
            0x99, 0xD2, 0xEC, 0x5E, 0x86, 0x26, 0xE6, 0x47, 0x88, 0x02, 0xC6,
            0xE7, 0xB5, 0x6E, 0x95, 0xBF, 0x97, 0xBE, 0x4C, 0x5B, 0xCA, 0xEC,
            0x20, 0xC6, 0x99, 0x93, 0xA2, 0xD4, 0xA5, 0xDC, 0x8D, 0xFA, 0x8D,
            0x95, 0xC2, 0x34, 0x92, 0x89, 0x7B, 0x02, 0xB7, 0xBA, 0x68, 0x61,
            0x1F, 0xB8, 0x83, 0x15, 0x3F, 0xC5, 0xFE, 0xE4, 0xF0, 0xC4, 0x68,
            0x62, 0x9F, 0x0F, 0xF3, 0x8A, 0xDF, 0xF4, 0x55, 0x6F, 0xF3, 0x0E,
            0xEB, 0xC5, 0xFC, 0x5E, 0xCA, 0x8D, 0x8D, 0x5D, 0xC9, 0x61, 0x1D,
            0xDB, 0x13, 0x68, 0xC0, 0x5F, 0x43, 0x89, 0x57, 0x56, 0xB1, 0xF7,
            0x94, 0xD0, 0xC4, 0xFA, 0x06, 0x65, 0xD8, 0x29, 0xFC, 0x35, 0x19,
            0xDA, 0x4D, 0xBC, 0x85, 0x2B, 0xDA, 0x57, 0xA7, 0xD9, 0x94, 0x04,
            0x9B, 0xE7, 0x3D, 0x81, 0xEF, 0x1E, 0xBC, 0x15, 0xA8, 0x04, 0x89,
            0x9C, 0x61, 0x6B, 0x76, 0xBF, 0x78, 0xE3, 0x97, 0x9B, 0xC3, 0xA4,
            0x18, 0x5C, 0xAB, 0xA2, 0x5F, 0xE9, 0x89, 0xDB, 0x7A, 0x19, 0x9F,
            0xE2, 0x2D, 0xB7, 0x1B, 0x29, 0x9E, 0xD8, 0xC9, 0x12, 0xE1, 0x9B,
            0xEE, 0xAF, 0x94, 0x39, 0x2F, 0x30, 0xBE, 0x72, 0xB0, 0x3B, 0x39,
            0x1D, 0x9C, 0x97, 0xB7, 0x10, 0x35, 0x31, 0xCD, 0xBA, 0x64, 0xD2,
            0x72, 0x5D, 0xF4, 0x56, 0xB1, 0x11, 0x62, 0x20, 0x5B, 0x7B, 0x62,
            0x2D, 0x95, 0x95, 0x6B, 0xA2, 0x37, 0x8F, 0xD5, 0xF3, 0x49, 0xF2,
            0xA0, 0x2A, 0x6B, 0x41, 0x99, 0xB4, 0x5C, 0x17, 0xBD, 0x9F, 0xAC,
            0x82, 0x55, 0x73, 0xED, 0xC5, 0x0E, 0x49, 0xA5, 0xE5, 0xBA, 0x3A,
            0xAF, 0x5C, 0xD8, 0xA3, 0x4C, 0xF3, 0x4A, 0x5D, 0x2A, 0x9D, 0xD7,
            0x65, 0x70, 0x4F, 0xEF, 0xF0, 0x09, 0x27, 0x27, 0xE1, 0x47, 0x3F,
            0xE8, 0xE6, 0x78, 0x80, 0xDA, 0x46, 0xE0, 0x97, 0xA5, 0x24, 0xEC,
            0x54, 0xF7, 0xCD, 0xFC, 0x44, 0x66, 0x65, 0x23, 0x41, 0xCA, 0x72,
            0x12, 0x7E, 0xAA, 0xEF, 0x8D, 0xC2, 0xDF, 0xAE, 0x68, 0x6C, 0x64,
            0x6D, 0x59, 0x4E, 0xC2, 0xDF, 0x59, 0xEB, 0x4F, 0x10, 0xD9, 0x58,
            0xC3, 0xBF, 0x32, 0x3F, 0x57, 0xBB, 0x2F, 0xEA, 0x38, 0xD7, 0x3F,
            0xEF, 0x19, 0xA8, 0x11, 0x6D, 0x85, 0x96, 0xEB, 0x6C, 0xAC, 0xC6,
            0x7B, 0xD8, 0xD6, 0xE4, 0x03, 0x73, 0xEF, 0x72, 0xD0, 0x83, 0x57,
            0xE3, 0x33, 0x35, 0xA9, 0xFE, 0xA1, 0xC4, 0xB3, 0xD4, 0xED, 0xF6,
            0x23, 0xAB, 0x05, 0x5F, 0xBC, 0x57, 0x69, 0x76, 0x7B, 0xF0, 0x79,
            0x70, 0xFE, 0xED, 0x15, 0xD4, 0x93, 0x94, 0x91, 0xC4, 0xF9, 0x08,
            0xCF, 0xCA, 0xBD, 0xC1, 0xA8, 0x52, 0x7A, 0x33, 0x47, 0x88, 0xF6,
            0x39, 0x68, 0x64, 0xC7, 0x37, 0xE3, 0x1C, 0x60, 0x4D, 0x40, 0x67,
            0x77, 0xCB, 0x11, 0xA8, 0x84, 0x4F, 0xF1, 0xDE, 0xC1, 0x0E, 0xDF,
            0x0E, 0xCA, 0x81, 0x56, 0x5A, 0xFE, 0x7A, 0xA0, 0x44, 0x22, 0xC5,
            0xFD, 0x3A, 0x8F, 0x51, 0x77, 0xCA, 0x9D, 0x37, 0xD2, 0x1E, 0xA0,
            0xF1, 0x1F, 0x63, 0xCD, 0xA3, 0x67, 0xDD, 0xF7, 0xC8, 0x4A, 0xF5,
            0xBA, 0xB8, 0x84, 0xF5, 0x7A, 0x53, 0xB2, 0xA4, 0x17, 0xDF, 0x07,
            0x62, 0x50, 0xF7, 0x76, 0x66, 0x62, 0x4E, 0x6E, 0x31, 0x06, 0xC8,
            0xA4, 0x5C, 0x2F, 0xE6, 0x1D, 0x32, 0x19, 0x5F, 0x43, 0x38, 0xE2,
            0xE3, 0x19, 0xEE, 0xD6, 0x3B, 0x71, 0x71, 0x65, 0x91, 0xA1, 0x7D,
            0x6E, 0xD9, 0x73, 0x83, 0x12, 0x2C, 0xB1, 0x62, 0x4C, 0xC1, 0xF3,
            0xBC, 0x72, 0xC4, 0x67, 0xB9, 0x30, 0x96, 0x1F, 0x23, 0xBF, 0x5B,
            0xDB, 0xFB, 0xC7, 0x48, 0x62, 0x30, 0x11, 0x23, 0xB4, 0x12, 0xFC,
            0x02, 0x11, 0x2F, 0xF8, 0x9E, 0x06, 0x53, 0x1F, 0xB8, 0x3F, 0x7D,
            0x12, 0xB4, 0x2A, 0x09, 0x4B, 0x59, 0xA7, 0xC9, 0xE1, 0x57, 0x28,
            0xE5, 0xFB, 0x35, 0x3A, 0x8E, 0x94, 0xBE, 0x70, 0xCF, 0x9D, 0x56,
            0xFD, 0x6B, 0xB4, 0xA5, 0x19, 0x48, 0x97, 0x99, 0xCF, 0x23, 0x66,
            0x3B, 0xF7, 0x5E, 0x37, 0x90, 0x3F, 0xDA, 0x13, 0x71, 0x2B, 0x9E,
            0x12, 0x32, 0xE4, 0x73, 0xAB, 0xA3, 0xE5, 0x5C, 0x3D, 0x8F, 0x41,
            0x9E, 0x57, 0xD8, 0x79, 0xCA, 0xAD, 0xA0, 0x53, 0x08, 0x92, 0xF5,
            0xDF, 0xA4, 0xE9, 0xCE, 0x1D, 0xDD, 0x89, 0x79, 0x0E, 0x91, 0xE7,
            0xA8, 0x8A, 0x1C, 0x55, 0x81, 0xA3, 0x29, 0x30, 0x34, 0x05, 0xF9,
            0xB6, 0x20, 0xDF, 0x16, 0xE4, 0xBB, 0x82, 0x7C, 0x57, 0x90, 0xEF,
            0x0B, 0xF2, 0x7D, 0x41, 0x7E, 0x28, 0xC8, 0x0F, 0x05, 0xF9, 0xB1,
            0x20, 0x3F, 0x16, 0xE4, 0xA7, 0x82, 0xFC, 0xE4, 0xC9, 0xE3, 0xB3,
            0xE4, 0x57, 0x0A, 0x7F, 0x3D, 0xE6, 0x51, 0xE1, 0xBA, 0x3A, 0xFF,
            0xC6, 0xAB, 0xB5, 0x52, 0xA8, 0xEB, 0x77, 0xE8, 0xE9, 0xAF, 0xB5,
            0x8F, 0x57, 0x73, 0xAB, 0xAB, 0x21, 0x2A, 0x80, 0x9E, 0xDB, 0x0C,
            0xD3, 0x97, 0x32, 0x5B, 0x85, 0x4F, 0xF0, 0x55, 0x73, 0x8C, 0x70,
            0x0B, 0xB3, 0xB6, 0x69, 0x9E, 0x33, 0xC5, 0xC8, 0x58, 0xDE, 0x9D,
            0xA9, 0x84, 0xF7, 0x96, 0xB8, 0x6D, 0x12, 0x99, 0xE2, 0x6C, 0x12,
            0xC8, 0x26, 0x81, 0x6B, 0x13, 0xB8, 0x36, 0xC2, 0xED, 0x6D, 0xC9,
            0x7D, 0xE4, 0x3E, 0x69, 0x0F, 0xBA, 0x7B, 0x09, 0x23, 0x65, 0x0A,
            0x7F, 0xE9, 0x8D, 0xA1, 0x7E, 0x8A, 0x79, 0xAF, 0xDC, 0x86, 0xD1,
            0xE2, 0xD2, 0x42, 0xB9, 0x54, 0xAE, 0x52, 0x79, 0x22, 0xCB, 0x2F,
            0x91, 0xB1, 0xED, 0xF0, 0xEE, 0x55, 0x12, 0x7B, 0x95, 0xC0, 0xC6,
            0x75, 0xB7, 0x4F, 0xD4, 0xDD, 0x3E, 0x59, 0x77, 0xFB, 0x64, 0xDD,
            0xED, 0x13, 0x75, 0xB7, 0x4F, 0xD4, 0xDD, 0x3E, 0x51, 0x77, 0xFB,
            0x44, 0xDD, 0xBD, 0xD8, 0x5D, 0x1D, 0x7A, 0xA7, 0x52, 0x28, 0x93,
            0x4A, 0x47, 0xF9, 0x1F, 0x82, 0x96, 0x42, 0xF7, 0x95, 0xFA, 0x1F,
            0xD4, 0x89, 0x20, 0x4A,
        ];
        let keybinds = [
            0xF4, 0x05, 0x00, 0x00, 0x78, 0x9C, 0x95, 0x54, 0xD1, 0x4E, 0xC2,
            0x40, 0x10, 0x1C, 0x5F, 0x4D, 0xFC, 0x87, 0xC6, 0x77, 0x85, 0xBB,
            0x5E, 0x4B, 0x49, 0x10, 0x22, 0x31, 0x7E, 0x81, 0x3E, 0x1B, 0x41,
            0xA3, 0x46, 0x04, 0x05, 0x35, 0x7C, 0xA4, 0x1F, 0xE5, 0xF4, 0x6A,
            0xE9, 0x6E, 0xBB, 0x90, 0x98, 0x4B, 0xDA, 0xDE, 0xEE, 0xDC, 0xEC,
            0xEC, 0xEE, 0x6D, 0x7F, 0x70, 0x84, 0x11, 0x26, 0xD8, 0xE2, 0x0D,
            0x0B, 0x24, 0xF8, 0xC6, 0x23, 0xD6, 0xD8, 0xE0, 0x05, 0x2B, 0x2C,
            0x71, 0x81, 0x53, 0x38, 0x9C, 0xA3, 0xCF, 0x77, 0x42, 0xCF, 0x12,
            0x73, 0xDA, 0x1F, 0xE8, 0x5D, 0xE2, 0x29, 0x7A, 0x6F, 0x71, 0x83,
            0x6B, 0x9C, 0x11, 0x95, 0x73, 0x37, 0xC1, 0x18, 0x27, 0x38, 0x26,
            0xE3, 0x0A, 0xEF, 0xF8, 0xFC, 0x63, 0xD9, 0xEC, 0xAC, 0x73, 0x3C,
            0xE3, 0x3E, 0x9E, 0xDE, 0xE0, 0x95, 0xEF, 0x05, 0xD7, 0x98, 0x27,
            0x33, 0x46, 0x90, 0x2B, 0x6D, 0xED, 0x9D, 0xDA, 0x15, 0x2D, 0x6F,
            0x7B, 0x79, 0x4C, 0xE3, 0xB3, 0x61, 0x0B, 0x8A, 0x73, 0x8A, 0x2B,
            0x3E, 0x07, 0xEA, 0x44, 0x9B, 0xC1, 0x66, 0x76, 0xA6, 0x35, 0xC5,
            0x50, 0xF1, 0x5F, 0x46, 0x5C, 0xAA, 0x10, 0x87, 0xF4, 0x56, 0xFA,
            0xF6, 0xC5, 0x2C, 0xFD, 0x85, 0xF2, 0x07, 0x56, 0x4C, 0x72, 0x06,
            0x46, 0x3C, 0x14, 0x63, 0x84, 0xDE, 0x9E, 0xCA, 0x57, 0x5D, 0xF9,
            0xC0, 0x17, 0x2D, 0x73, 0xDA, 0x67, 0xC4, 0xAC, 0x71, 0xA7, 0xBA,
            0x77, 0xC7, 0xBE, 0x6F, 0x05, 0x76, 0xC6, 0xEF, 0x3E, 0x6F, 0x83,
            0x67, 0x96, 0x09, 0x3B, 0x97, 0xF1, 0xAB, 0x8C, 0x50, 0x79, 0x6A,
            0x84, 0xDB, 0x21, 0x8A, 0x58, 0xEB, 0x2E, 0x22, 0x15, 0x1C, 0xE5,
            0x0D, 0xE8, 0x22, 0x82, 0x8A, 0x62, 0x21, 0x86, 0x02, 0x51, 0x77,
            0xC8, 0xD2, 0xD2, 0xA8, 0x71, 0x51, 0x8F, 0x8D, 0xF2, 0x1D, 0x36,
            0x3B, 0xB3, 0x20, 0x72, 0x4B, 0xB9, 0x2C, 0x4C, 0x2E, 0xB8, 0x06,
            0x26, 0x8F, 0x17, 0x55, 0x2C, 0xE2, 0x09, 0x0B, 0xD3, 0x28, 0x2F,
            0xEF, 0x98, 0x55, 0x03, 0x4F, 0xAB, 0xCE, 0x2E, 0x98, 0xA8, 0x5C,
            0xA1, 0xBC, 0xD2, 0x2D, 0x7B, 0xEB, 0xA9, 0x57, 0xD6, 0x7D, 0x68,
            0xF6, 0xAE, 0xAF, 0xF2, 0xB3, 0xFB, 0xEB, 0x54, 0x9D, 0x6C, 0x9E,
            0x20, 0xF2, 0x73, 0x66, 0x9D, 0x52, 0x91, 0x5F, 0xB6, 0xBB, 0xF1,
            0x16, 0x2E, 0x8F, 0xB9, 0x25, 0xB1, 0x96, 0x41, 0xCC, 0xB1, 0xD5,
            0xA1, 0x72, 0xA6, 0x1A, 0xB4, 0x9C, 0x3D, 0x4B, 0x43, 0x88, 0xF9,
            0x76, 0xD1, 0x85, 0x99, 0x79, 0x88, 0x8A, 0x6B, 0x74, 0x3D, 0xC3,
            0x59, 0xAC, 0x94, 0x85, 0xCE, 0x3B, 0xE8, 0xAE, 0x92, 0xAA, 0x43,
            0xBD, 0x7F, 0xCD, 0x6A, 0xCF, 0xFC, 0x0B, 0x03, 0xBF, 0x9D, 0x7E,
            0xBB, 0x81,
        ];

        tx.send(session.send(Message::CurStatus(self))).unwrap();

        let game_time = 148641933;
        vec![
            s::Message::LoadClientSettings(s::LoadClientSettings::new(
                0,
                ui.to_vec(),
            )),
            s::Message::LoadClientSettings(s::LoadClientSettings::new(
                1,
                keybinds.to_vec(),
            )),
            s::Message::LoadItemCooltime(s::LoadItemCooltime::new()),
            s::Message::ChangeChannel(s::ChangeChannel::new(
                change_channel.to_vec(),
            )),
            s::Message::Weather(s::Weather::new()),
            s::Message::Time(s::Time::new(game_time)),
            s::Message::GamepassInfo(s::GamepassInfo::new(
                [
                    0x01, 0x00, 0x00, 0x00, 0x10, 0x3B, 0x64, 0x99, 0xFF, 0xFF,
                    0xFF, 0xFF, 0x10, 0x3B, 0x64, 0x99, 0xFF, 0xFF, 0xFF, 0xFF,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                ]
                .to_vec(),
            )),
            s::Message::GamepassInfo(s::GamepassInfo::new(
                [
                    0x01, 0x00, 0x00, 0x00, 0x10, 0x3B, 0x64, 0x99, 0xFF, 0xFF,
                    0xFF, 0xFF, 0x10, 0x3B, 0x64, 0x99, 0xFF, 0xFF, 0xFF, 0xFF,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                ]
                .to_vec(),
            )),
            s::Message::GamepassInfo(s::GamepassInfo::new(
                [
                    0x02, 0x00, 0x00, 0x00, 0x10, 0x3B, 0x64, 0x99, 0xFF, 0xFF,
                    0xFF, 0xFF, 0x10, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                ]
                .to_vec(),
            )),
        ]
    }
}
impl Deserialise for CurStatus {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct ReadyToQuit;

impl ReadyToQuit {
    /// O servidor oficial responde com `S_ALIVE`, dois bytes zero -- nas duas capturas, no mesmo
    /// ponto: logo depois da lista de personagens. Ficava sem resposta aqui.
    ///
    /// O nome do opcode na tabela extraida do `Game.dll` e `C_READY_TO_QUIT`, o que nao combina
    /// com receber um "estou vivo" de volta; e mais um ponto onde o pareamento nome-numero erra.
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::Alive(s::Alive::new())]
    }
}
impl Deserialise for ReadyToQuit {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct AskQuit;

impl AskQuit {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::AskQuitResult(s::AskQuitResult::new())]
    }
}
impl Deserialise for AskQuit {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct Quit;

impl Quit {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::AskQuitResult(s::AskQuitResult::new())]
    }
}

impl Deserialise for Quit {
    fn deserialise(_: &[u8]) -> Self {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct Reconnect;

impl Reconnect {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::ReconnectKey(s::ReconnectKey::new())]
    }
}

impl Deserialise for Reconnect {
    fn deserialise(_: &[u8]) -> Self {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct CheckNickName {
    pub name: String,
}

impl CheckNickName {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::CheckNickName(self))).unwrap();
        vec![]
    }
}

impl Deserialise for CheckNickName {
    fn deserialise(buf: &[u8]) -> Self {
        let u16_chars: Vec<u16> = buf
            .chunks_exact(2)
            .map(|c| u16::from_le_bytes([c[0], c[1]]))
            .skip_while(|&c| c < 32 && c != 0)
            .take_while(|&c| c != 0)
            .collect();
        let name = String::from_utf16_lossy(&u16_chars).trim().to_string();
        Self { name }
    }
}

#[derive(Debug, Clone)]
pub struct _00D8;
impl _00D8 {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::_0102(s::_0102::new())]
    }
}
impl Deserialise for _00D8 {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

/// Quantos bytes do pedido de criacao sao o bloco do registro (de `NOME` ate `REDUNDANCIA`).
const APARENCIA_LEN: usize = super::molde::campo::APARENCIA_LEN;

/// Pedido de criacao de personagem.
///
/// O payload da captura tem 162 bytes: a chave de sessao, um codigo numerico de 8 digitos, o nome,
/// e um bloco grande de aparencia -- cores em RGBA, sliders de rosto e corpo, e a altura como float
/// no fim. Por enquanto so o **nome** e lido: e o que o registro de personagem sabe escrever hoje.
/// Aparencia continua vindo do molde capturado, como no resto da lista.
///
/// As duas cadeias sao UTF-16 terminadas em nulo, uma atras da outra.
#[derive(Debug, Clone)]
pub struct CreateCharacter {
    pub nome: String,
    /// O trecho do pedido que e, byte a byte, o `4..144` do registro de personagem.
    pub aparencia: Vec<u8>,
}
impl CreateCharacter {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        // Precisa do banco, entao quem responde e o game loop -- mesma rota do CharacterList.
        tx.send(session.send(Message::CreateCharacter(self))).unwrap();
        Vec::new()
    }
}
impl Deserialise for CreateCharacter {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        // [u32 chave][utf16 codigo][utf16 nome]
        let mut ptr = 4;
        let mut cadeia = || {
            let mut chars = Vec::new();
            while ptr + 1 < buf.len() {
                let c = u16::from_le_bytes([buf[ptr], buf[ptr + 1]]);
                ptr += 2;
                if c == 0 {
                    break;
                }
                chars.push(c);
            }
            String::from_utf16_lossy(&chars)
        };

        let _codigo = cadeia();
        let nome = cadeia();

        // O bloco comeca no inicio do campo de nome -- tamanho fixo, como no registro -- e vai ate
        // o fim do payload. `ptr` parou logo depois do nulo do nome, entao voltamos ao inicio dele.
        let inicio = 4 + 2 * (_codigo.encode_utf16().count() + 1);
        let aparencia = buf
            .get(inicio..inicio + APARENCIA_LEN)
            .map(<[u8]>::to_vec)
            .unwrap_or_default();

        Self { nome, aparencia }
    }
}

#[derive(Debug, Clone)]
pub struct DeleteCharacter {
    pub character_id: u32,
}

impl DeleteCharacter {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::DeleteCharacter(self))).unwrap();
        Vec::new()
    }
}

impl Deserialise for DeleteCharacter {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut len = 0;
        let _play_ok = if buf.len() >= 4 { consume_le_bytes!(len, buf, u32) } else { 0 };
        let character_id = if buf.len() >= 8 { consume_le_bytes!(len, buf, u32) } else { 0 };
        Self { character_id }
    }
}

#[derive(Debug, Clone)]
pub struct RecipeList;
impl RecipeList {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::RecipeList(s::RecipeList::new(
            [
                0x03, 0x00, 0x49, 0x30, 0x3D, 0x09, 0x00, 0x4A, 0x30, 0x3D,
                0x09, 0x00, 0x4D, 0x30, 0x3D, 0x09, 0x00,
            ]
            .to_vec(),
        ))]
    }
}
impl Deserialise for RecipeList {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct QueryBuddy;
impl QueryBuddy {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::BuddyList(s::BuddyList::new())]
    }
}
impl Deserialise for QueryBuddy {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct QueryBlock;
impl QueryBlock {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for QueryBlock {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone, Copy)]
enum MoveData {
    Stop,
    Continue {
        time: u32,
    },
    Turn {
        delta: Coord,
        time: u32,
    },
    Direct {
        dest: Coord,
        time: u32,
    },
    GlideTurn {
        delta: Coord,
        unknown: u8,
        time: u32,
    },
    GlideContinue {
        unknown: u8,
        time: u32,
    },
}

#[derive(Debug, Clone)]
pub struct MoveNew {
    coord: Coord,
    direction: Direction,
    ty: MoveType,
    data: MoveData,
}
impl MoveNew {
    /// O primeiro passo encerra a protecao de login.
    ///
    /// Ate ai o personagem fica piscando -- e o estado que o `S_INVISIBLE_LEVEL` ligou no spawn.
    /// Na captura o par que desliga vem logo depois do primeiro `C_MOVE_NEW`: o
    /// `S_INVISIBLE_LEVEL` com `[id][00 00 00]` e o `S_INVINCIBLE_TIME` zerado. E o comportamento
    /// classico do Aion -- a invencibilidade de entrada acaba quando o jogador se mexe.
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        let id = session.character_id();
        let primeiro_passo = session.desliga_protecao_de_login();

        tx.send(session.send(Message::MoveNew(self))).unwrap();

        if primeiro_passo {
            println!("INFO: primeiro passo do personagem {id}; fim da protecao de login");
            return vec![
                s::Message::InvisibleLevel(s::InvisibleLevel::finish(id)),
                s::Message::InvincibleTime(s::InvincibleTime::finish()),
            ];
        }
        vec![]
    }

    pub fn location(&self) -> Coord {
        self.coord
    }

    pub fn calculate(&self, entity_id: u32) -> s::MoveNew {
        let data = match self.data {
            MoveData::Continue { .. } | MoveData::GlideContinue { .. } => {
                s::MoveData::Continue
            }
            MoveData::Turn { delta, .. } | MoveData::GlideTurn { delta, .. } => {
                s::MoveData::Turn { delta }
            }
            MoveData::Stop => s::MoveData::Stop,
            MoveData::Direct { dest, .. } => s::MoveData::Direct { dest },
        };
        s::MoveNew::new(entity_id, self.coord, self.direction, self.ty, data)
    }
}
impl Deserialise for MoveNew {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _len = 0;
        let coord = Coord::deserialise(&buf[..12].try_into().unwrap());
        _len += Coord::LEN;

        let direction = Direction::new(consume_le_bytes!(_len, buf, u8));

        let ty: MoveType = consume_le_bytes!(_len, buf, u8).into();

        let data = if ty.contains(MoveType::FALL) {
            MoveData::Continue {
                time: consume_le_bytes!(_len, buf, u32),
            }
        } else if ty.contains(MoveType::TURN) {
            let delta = Coord::new(
                consume_le_bytes!(_len, buf, f32),
                consume_le_bytes!(_len, buf, f32),
                consume_le_bytes!(_len, buf, f32),
            );
            if ty.contains(MoveType::GLIDE) {
                MoveData::GlideTurn {
                    delta,
                    unknown: consume_le_bytes!(_len, buf, u8),
                    time: consume_le_bytes!(_len, buf, u32),
                }
            } else {
                MoveData::Turn {
                    delta,
                    time: consume_le_bytes!(_len, buf, u32),
                }
            }
        } else if ty.contains(MoveType::CONTINUE) {
            if ty.contains(MoveType::GLIDE) {
                MoveData::GlideContinue {
                    unknown: consume_le_bytes!(_len, buf, u8),
                    time: consume_le_bytes!(_len, buf, u32),
                }
            } else {
                MoveData::Continue {
                    time: consume_le_bytes!(_len, buf, u32),
                }
            }
        } else {
            MoveData::Stop
        };

        Self {
            coord,
            direction,
            ty,
            data,
        }
    }
}
#[derive(Debug, Clone)]
pub struct RequestSerialKillerList;
impl RequestSerialKillerList {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for RequestSerialKillerList {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}
#[derive(Debug, Clone)]
pub struct InstanceDungeonCooltimes;
impl InstanceDungeonCooltimes {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for InstanceDungeonCooltimes {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}
#[derive(Debug, Clone)]
pub struct SignClient {
    unknown: [u8; 10],
}
impl SignClient {
    /// Responder aqui e obrigatorio: sem resposta o cliente reenvia o pedido sem parar e o
    /// personagem fica plantado no lugar.
    ///
    /// Medido na captura do servidor oficial (`conta-nova-2026-08-24.pcapng`, 21.964 pacotes):
    /// `C 0x0086` aparece exatamente 2 vezes (#259 e #14960) e `S 0x00E6` de 68 bytes aparece
    /// exatamente 2 vezes (#265 e #14969), uma depois de cada pedido -- sem sobra de nenhum dos
    /// dois lados. Com a resposta comentada, uma sessao nossa mandou `0x0086` 89 vezes e o
    /// `0x0030` (mover) so 4; no oficial o mover e 39,8% de tudo que o cliente manda.
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::SignClient(s::SignClient::new())]
    }
}
impl Deserialise for SignClient {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self {
            unknown: buf.try_into().unwrap(),
        }
    }
}

/// TODO: Most likely compressed or encoded
#[derive(Debug, Clone)]
pub struct SaveClientSettings {
    ty: u8,
    raw: Vec<u8>,
}
impl SaveClientSettings {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for SaveClientSettings {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _len = 0;
        let ty = consume_le_bytes!(_len, buf, u8);
        _ = consume_le_bytes!(_len, buf, u16);
        let body_len = consume_le_bytes!(_len, buf, u16) as usize;
        Self {
            ty,
            raw: buf[_len..body_len].to_vec(),
        }
    }
}
#[derive(Debug, Clone)]
pub struct RouteInfo;
impl RouteInfo {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for RouteInfo {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct ReadyEnterWorldAck {
    unknown: [u8; 4],
}
impl ReadyEnterWorldAck {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for ReadyEnterWorldAck {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self {
            unknown: buf.try_into().unwrap(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct AskLog;
impl AskLog {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for AskLog {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

/// The world has been drawn by the client and its ready for objects
/// to be placed. Order matters, before put_NPC you cannot reference its ID in
/// game. Npcs must be placed afterwards
#[derive(Debug, Clone)]
pub struct LevelReady;
impl LevelReady {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        session.liga_protecao_de_login();
        tx.send(session.send(Message::LevelReady(self))).unwrap();

        vec![s::Message::InvincibleTime(s::InvincibleTime::finish())]
    }
}
impl Deserialise for LevelReady {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}
#[derive(Debug, Clone)]
pub struct UseSkill {
    pub skill_id: u16,
    pub skill_level: u16,
    pub target_id: u32,
    pub cast_type: u8,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
    pub unknown: Vec<u8>,
}
impl UseSkill {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::UseSkill(self))).unwrap();

        vec![]
    }
}
impl Deserialise for UseSkill {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut ptr = 0;

        let skill_id = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) } else { 0 };
        let skill_level = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u16) } else { 1 };
        let target_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let cast_type = if buf.len() >= 9 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let x = if buf.len() >= 13 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let y = if buf.len() >= 17 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let z = if buf.len() >= 21 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let heading = if buf.len() >= 22 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let unknown = if buf.len() > ptr { buf[ptr..].to_vec() } else { Vec::new() };

        Self {
            skill_id,
            skill_level,
            target_id,
            cast_type,
            x,
            y,
            z,
            heading,
            unknown,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Action {
    pub ty: ActionType,
    raw: Vec<u8>,
}
impl Action {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::Action(self))).unwrap();

        vec![]
    }
}
impl Deserialise for Action {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self {
            ty: ActionType::deserialise(buf),
            raw: buf.to_vec(),
        }
    }
}

#[derive(Debug, Clone)]
#[repr(u8)]
pub enum LootAction {
    Start = 0,
    Stop = 1,
}

impl From<u8> for LootAction {
    fn from(value: u8) -> Self {
        match value {
            0 => Self::Start,
            1 => Self::Stop,
            _ => unreachable!("Invalid LootAction"),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Loot {
    pub entity_id: u32,
    pub action: LootAction,
}
impl Loot {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::Loot(self))).unwrap();

        vec![]
    }
}

impl Deserialise for Loot {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _len = 0;
        let entity_id = consume_le_bytes!(_len, buf, u32);
        let action = consume_le_bytes!(_len, buf, u8).into();
        Self { entity_id, action }
    }
}

#[derive(Debug, Clone)]
pub struct LootItem {
    pub entity_id: u32,
    pub index: u32,
}
impl LootItem {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::LootItem(self))).unwrap();

        vec![]
    }
}

impl Deserialise for LootItem {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _len = 0;
        let entity_id = consume_le_bytes!(_len, buf, u32);
        let index = consume_le_bytes!(_len, buf, u32);
        Self { entity_id, index }
    }
}

#[derive(Debug, Clone)]
pub struct ChangeTarget {
    pub target_id: u32,
}
impl ChangeTarget {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        account: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(account.send(Message::ChangeTarget(self))).unwrap();

        vec![]
    }
}
impl Deserialise for ChangeTarget {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut _len = 0;
        let target_id = consume_le_bytes!(_len, buf, u32);

        Self { target_id }
    }
}

/// When an attack is recieved from a client it just tells us who it is attacking
/// and what the attack sequence number is, we send this update to the main game
/// loop for damage calculations
#[derive(Debug, Clone)]
pub struct Attack {
    pub target_id: u32,
    sequence: u8,
    _unknown: Vec<u8>,
}
impl Attack {
    pub fn handle(
        self,
        tx: &Sender<ClientUpdate>,
        session: &mut Account,
    ) -> Vec<s::Message> {
        tx.send(session.send(Message::Attack(self))).unwrap();
        vec![]
    }
}
impl Deserialise for Attack {
    fn deserialise(buf: &[u8]) -> Self
    where
        Self: Sized,
    {
        let mut ptr = 0;

        let target_id = consume_le_bytes!(ptr, buf, u32);
        let sequence = consume_le_bytes!(ptr, buf, u8);

        let _unknown = buf[ptr..].to_vec();

        Self {
            target_id,
            sequence,
            _unknown,
        }
    }
}
#[derive(Debug, Clone)]
pub struct UseEquipmentItem {
    pub item_unique_id: u32,
    pub equip_action: u8,
    pub equip_slot: u32,
}
impl UseEquipmentItem {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::UseEquipmentItem(self))).unwrap();
        vec![]
    }
}
impl Deserialise for UseEquipmentItem {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let item_unique_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let equip_action = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let equip_slot = if buf.len() >= 9 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self {
            item_unique_id,
            equip_action,
            equip_slot,
        }
    }
}
#[derive(Debug, Clone)]
pub struct ReconnectAuth;
impl ReconnectAuth {
    /// O cliente manda este pacote no meio da sessao, ja dentro do mundo, e **o servidor real nao
    /// responde nada**: na captura, depois do 0xB8 vem so a continuacao dos spawns de NPC.
    ///
    /// O POC respondia com um S_RECONNECT_KEY, que nao aparece em ponto nenhum da captura. Mandar
    /// uma chave de reconexao para um cliente que esta dentro do mundo e pedir para ele reconectar.
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![]
    }
}
impl Deserialise for ReconnectAuth {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct Alive;
impl Alive {
    pub fn handle(
        &self,
        _: &Sender<ClientUpdate>,
        _: &mut Account,
    ) -> Vec<s::Message> {
        vec![s::Message::Alive(s::Alive::new())]
    }
}
impl Deserialise for Alive {
    fn deserialise(_: &[u8]) -> Self
    where
        Self: Sized,
    {
        Self
    }
}

#[derive(Debug, Clone)]
pub struct ChatMessagePublic {
    pub chat_type: u8,
    pub message: String,
}
impl ChatMessagePublic {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::ChatMessagePublic(self))).unwrap();
        vec![]
    }
}
impl Deserialise for ChatMessagePublic {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let chat_type = if !buf.is_empty() { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let message = if buf.len() > ptr {
            let u16_slice: Vec<u16> = buf[ptr..]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };
        Self { chat_type, message }
    }
}

#[derive(Debug, Clone)]
pub struct ShowDialog {
    pub target_id: u32,
    pub dialog_id: u32,
}
impl ShowDialog {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::ShowDialog(self))).unwrap();
        vec![]
    }
}
impl Deserialise for ShowDialog {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let target_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let dialog_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self { target_id, dialog_id }
    }
}

#[derive(Debug, Clone)]
pub struct DialogSelect {
    pub target_id: u32,
    pub dialog_id: u32,
    pub last_page: u32,
    pub quest_id: u32,
}
impl DialogSelect {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::DialogSelect(self))).unwrap();
        vec![]
    }
}
impl Deserialise for DialogSelect {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let target_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let dialog_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let last_page = if buf.len() >= 12 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quest_id = if buf.len() >= 16 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self { target_id, dialog_id, last_page, quest_id }
    }
}

/// Cliente solicita entrada ou saída em corrente de vento (Opcode 0x46).
#[derive(Debug, Clone)]
pub struct WindPath {
    pub windstream_id: u32,
    pub action: u8, // 1=entrar, 2=sair
    /// `false` quando o pacote veio sem payload -- nesse caso nao ha pedido a atender.
    pub pedido: bool,
}

impl WindPath {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        if !self.pedido {
            // Corpo vazio: o servidor oficial cala. Encaminhar isto ao mundo e o que gerava a
            // resposta de voo fora de hora, no meio do carregamento.
            return vec![];
        }
        tx.send(session.send(Message::WindPath(self))).unwrap();
        vec![]
    }
}

impl Deserialise for WindPath {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        // Sem os 5 bytes de payload nao existe pedido: nao se inventa `windstream_id` nem
        // `action`. O 0x46 vazio aparece na captura oficial (pacotes #138 e #1425) e o servidor
        // real nao responde nada nas duas vezes; inventar `action = 1` fazia o nosso responder
        // com pacotes de corrente de vento no meio da entrada no mundo, e o cliente congelava.
        if buf.len() < 5 {
            return Self { windstream_id: 0, action: 0, pedido: false };
        }
        let windstream_id = consume_le_bytes!(ptr, buf, u32);
        let action = consume_le_bytes!(ptr, buf, u8);
        Self {
            windstream_id,
            action,
            pedido: true,
        }
    }
}

/// Cliente reporta progresso de voo em corrente de vento (Opcode 0x31).
#[derive(Debug, Clone)]
pub struct PathFly {
    pub entity_id: u32,
    pub windstream_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub progress: f32,
}

impl PathFly {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::PathFly(self))).unwrap();
        vec![]
    }
}

impl Deserialise for PathFly {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let entity_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let windstream_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let x = if buf.len() >= 12 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let y = if buf.len() >= 16 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let z = if buf.len() >= 20 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        let progress = if buf.len() >= 24 { consume_le_bytes!(ptr, buf, f32) } else { 0.0 };
        Self {
            entity_id,
            windstream_id,
            x,
            y,
            z,
            progress,
        }
    }
}

/// Cliente solicita compra ou venda em loja de NPC (Opcode 0x33).
#[derive(Debug, Clone)]
pub struct BuySell {
    pub npc_object_id: u32,
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub action: u8, // 0=comprar, 1=vender
}

impl BuySell {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::BuySell(self))).unwrap();
        vec![]
    }
}

impl Deserialise for BuySell {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let npc_object_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let item_unique_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let item_template_id = if buf.len() >= 12 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quantity = if buf.len() >= 16 { consume_le_bytes!(ptr, buf, u32) } else { 1 };
        let action = if buf.len() >= 17 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        Self {
            npc_object_id,
            item_unique_id,
            item_template_id,
            quantity,
            action,
        }
    }
}

/// Cliente lê/interage com carta do correio (Opcode 0x86).
#[derive(Debug, Clone)]
pub struct MailRead {
    pub letter_id: u32,
    pub action: u8,
}

impl MailRead {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::MailRead(self))).unwrap();
        vec![]
    }
}

impl Deserialise for MailRead {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let letter_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let action = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        Self { letter_id, action }
    }
}

/// Cliente envia carta pelo correio (Opcode 0xA2).
#[derive(Debug, Clone)]
pub struct MailPostman {
    pub recipient_name: String,
    pub title: String,
    pub body: String,
    pub letter_type: u8,
    pub item_unique_id: u32,
    pub item_quantity: u32,
    pub kinah_amount: u64,
}

impl MailPostman {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::MailPostman(self))).unwrap();
        vec![]
    }
}

impl Deserialise for MailPostman {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let rname_len = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let recipient_name = if buf.len() >= ptr + rname_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + rname_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            ptr += rname_len;
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };

        let title_len = if buf.len() >= ptr + 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let title = if buf.len() >= ptr + title_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + title_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            ptr += title_len;
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };

        let body_len = if buf.len() >= ptr + 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let body = if buf.len() >= ptr + body_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + body_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            ptr += body_len;
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };

        let letter_type = if buf.len() > ptr { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let item_unique_id = if buf.len() >= ptr + 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let item_quantity = if buf.len() >= ptr + 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let kinah_amount = if buf.len() >= ptr + 8 { consume_le_bytes!(ptr, buf, u64) } else { 0 };

        Self {
            recipient_name,
            title,
            body,
            letter_type,
            item_unique_id,
            item_quantity,
            kinah_amount,
        }
    }
}

/// Cliente solicita histórico da Legião (Opcode 0xC5).
#[derive(Debug, Clone)]
pub struct RequestGuildHistory {
    pub page: u16,
}

impl RequestGuildHistory {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::RequestGuildHistory(self))).unwrap();
        vec![]
    }
}

impl Deserialise for RequestGuildHistory {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let page = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) } else { 0 };
        Self { page }
    }
}

/// Cliente compra ou ativa buff de Legião (Opcode 0xC6).
#[derive(Debug, Clone)]
pub struct GuildUserBuyBuff {
    pub buff_id: u32,
}

impl GuildUserBuyBuff {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GuildUserBuyBuff(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GuildUserBuyBuff {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let buff_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self { buff_id }
    }
}

/// Operações de Legião enviadas pelo cliente (Opcode 0xC7).
#[derive(Debug, Clone)]
pub struct GuildManage {
    pub action: u8,
    pub target_id: u32,
}

impl GuildManage {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GuildManage(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GuildManage {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let action = if buf.len() >= 1 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let target_id = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self { action, target_id }
    }
}

/// Cliente interage com grupo/party (Opcode 0x60).
#[derive(Debug, Clone)]
pub struct Party {
    pub target_player_id: u32,
    pub action: u8,
}

impl Party {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::Party(self))).unwrap();
        vec![]
    }
}

impl Deserialise for Party {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let target_player_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let action = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        Self { target_player_id, action }
    }
}

/// Cliente convida para grupo por nome (Opcode 0x61).
#[derive(Debug, Clone)]
pub struct PartyByName {
    pub name: String,
}

impl PartyByName {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::PartyByName(self))).unwrap();
        vec![]
    }
}

impl Deserialise for PartyByName {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let name_len = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let name = if buf.len() >= ptr + name_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + name_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };
        Self { name }
    }
}

/// Cliente adiciona ou remove amigo (Opcode 0x6F).
#[derive(Debug, Clone)]
pub struct AddBuddy {
    pub name: String,
    pub action: u8,
}

impl AddBuddy {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::AddBuddy(self))).unwrap();
        vec![]
    }
}

impl Deserialise for AddBuddy {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let name_len = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let name = if buf.len() >= ptr + name_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + name_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            ptr += name_len;
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };
        let action = if buf.len() > ptr { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        Self { name, action }
    }
}

/// Cliente registra item no broker (Opcode 0x0100).
#[derive(Debug, Clone)]
pub struct GlobalTradeRegister {
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub price_per_unit: u64,
}

impl GlobalTradeRegister {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GlobalTradeRegister(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GlobalTradeRegister {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let item_unique_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let item_template_id = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quantity = if buf.len() >= 12 { consume_le_bytes!(ptr, buf, u32) } else { 1 };
        let price_per_unit = if buf.len() >= 20 { consume_le_bytes!(ptr, buf, u64) } else { 0 };
        Self {
            item_unique_id,
            item_template_id,
            quantity,
            price_per_unit,
        }
    }
}

/// Cliente consulta histórico de vendas do broker (Opcode 0x0101).
#[derive(Debug, Clone)]
pub struct GlobalTradeSaleslog {
    pub item_template_id: u32,
    pub quality: u8,
    pub page: u32,
}

impl GlobalTradeSaleslog {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GlobalTradeSaleslog(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GlobalTradeSaleslog {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let item_template_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quality = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        let page = if buf.len() >= 9 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        Self {
            item_template_id,
            quality,
            page,
        }
    }
}

/// Cliente compra item no broker (Opcode 0x0102).
#[derive(Debug, Clone)]
pub struct GlobalTradeBuy {
    pub listing_id: u32,
    pub quantity: u32,
}

impl GlobalTradeBuy {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GlobalTradeBuy(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GlobalTradeBuy {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let listing_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quantity = if buf.len() >= 8 { consume_le_bytes!(ptr, buf, u32) } else { 1 };
        Self { listing_id, quantity }
    }
}

/// Cliente consulta preço médio no broker (Opcode 0x0103).
#[derive(Debug, Clone)]
pub struct GlobalTradeAvgPrice {
    pub item_template_id: u32,
    pub quality: u8,
}

impl GlobalTradeAvgPrice {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::GlobalTradeAvgPrice(self))).unwrap();
        vec![]
    }
}

impl Deserialise for GlobalTradeAvgPrice {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let item_template_id = if buf.len() >= 4 { consume_le_bytes!(ptr, buf, u32) } else { 0 };
        let quality = if buf.len() >= 5 { consume_le_bytes!(ptr, buf, u8) } else { 0 };
        Self {
            item_template_id,
            quality,
        }
    }
}

/// Cliente envia whisper privado (Opcode 0x1C).
#[derive(Debug, Clone)]
pub struct ChatMessageWhisper {
    pub target_name: String,
    pub message: String,
}

impl ChatMessageWhisper {
    pub fn handle(self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::ChatMessageWhisper(self))).unwrap();
        vec![]
    }
}

impl Deserialise for ChatMessageWhisper {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let target_len = if buf.len() >= 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let target_name = if buf.len() >= ptr + target_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + target_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            ptr += target_len;
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };
        let msg_len = if buf.len() >= ptr + 2 { consume_le_bytes!(ptr, buf, u16) as usize } else { 0 };
        let message = if buf.len() >= ptr + msg_len {
            let u16_slice: Vec<u16> = buf[ptr..ptr + msg_len]
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .take_while(|&c| c != 0)
                .collect();
            String::from_utf16_lossy(&u16_slice)
        } else {
            String::new()
        };
        Self { target_name, message }
    }
}

#[cfg(test)]
mod testes_de_opcode {
    use super::*;

    /// O 0x46 de corpo vazio nao e pedido de voo.
    ///
    /// Na captura oficial ele aparece assim duas vezes (pacotes #138 e #1425) e o servidor real
    /// nao responde nada. O parser inventava `action = 1` (entrar), o servidor devolvia os
    /// pacotes de corrente de vento no meio da entrada no mundo, e o cliente travava.
    #[test]
    fn wind_path_vazio_nao_e_pedido() {
        let vazio = WindPath::deserialise(&[]);
        assert!(!vazio.pedido, "corpo vazio nao pode virar pedido de voo");
        assert_eq!(vazio.action, 0, "sem payload nao se inventa acao");

        let curto = WindPath::deserialise(&[0x01, 0x00, 0x00, 0x00]);
        assert!(!curto.pedido, "payload incompleto nao pode virar pedido");
    }

    /// Com os 5 bytes de payload o pedido e real e os campos saem do fio.
    #[test]
    fn wind_path_com_payload_le_os_campos() {
        let p = WindPath::deserialise(&[0x2A, 0x00, 0x00, 0x00, 0x02]);
        assert!(p.pedido);
        assert_eq!(p.windstream_id, 42);
        assert_eq!(p.action, 2, "2 = sair da corrente");
    }
    use commons::game::{encrypt, encrypt_client_opcode, gen_xor_key};

    /// Monta um pacote de cliente como o cliente o manda: opcode cifrado, byte de servidor,
    /// checksum e payload, tudo cifrado a partir do offset do opcode.
    fn pacote_do_cliente(opcode: u16, payload: &[u8], chave: &mut [u8; 8]) -> Vec<u8> {
        let cifrado = encrypt_client_opcode(opcode);
        let mut buf = Vec::new();
        buf.extend_from_slice(&cifrado.to_le_bytes());
        buf.push(0x6F); // byte de servidor
        buf.extend_from_slice(&(!cifrado).to_le_bytes());
        buf.extend_from_slice(payload);
        encrypt(chave, &mut buf);
        buf
    }

    fn chave_nova() -> [u8; 8] {
        gen_xor_key(0x1234_5678).to_le_bytes()
    }

    /// Os tres opcodes renumerados a partir das capturas precisam cair no handler certo.
    ///
    /// Se alguem trocar um numero por engano, o pacote passa a cair no ramo "not implemented" e
    /// este teste quebra -- que e exatamente o sintoma que os 16 opcodes errados produziam.
    #[test]
    fn opcodes_renumerados_caem_no_handler_certo() {
        let casos: [(u16, &[u8], fn(&Message) -> bool); 3] = [
            (0x8B, &[], |m| matches!(m, Message::SaAccountItemQuery(_))),
            (0xB6, &[], |m| matches!(m, Message::RecipeList(_))),
            (0x86, &[0u8; 10], |m| matches!(m, Message::SignClient(_))),
        ];

        for (opcode, payload, e_o_esperado) in casos {
            let mut chave_envio = chave_nova();
            let mut buf = pacote_do_cliente(opcode, payload, &mut chave_envio);

            let mut chave_leitura = chave_nova();
            let (msg, lido) = Message::deserialise(&mut buf, &mut chave_leitura)
                .unwrap_or_else(|op| panic!("opcode 0x{opcode:02X} caiu como nao implementado (0x{op:02X})"));

            assert_eq!(lido, opcode, "opcode desofuscado nao confere");
            assert!(e_o_esperado(&msg), "0x{opcode:02X} caiu no handler errado: {msg:?}");
        }
    }

    /// Os numeros antigos nao podem continuar respondendo: eram justamente os que nunca chegavam.
    #[test]
    fn opcodes_antigos_nao_tem_mais_handler() {
        for antigo in [0xBBu16, 0x9E, 0xAE] {
            let mut chave_envio = chave_nova();
            let mut buf = pacote_do_cliente(antigo, &[], &mut chave_envio);

            let mut chave_leitura = chave_nova();
            assert!(
                Message::deserialise(&mut buf, &mut chave_leitura).is_err(),
                "0x{antigo:02X} ainda tem handler"
            );
        }
    }

    // ==============================================================================    // Prova contra o cliente oficial. Quadros capturados em 24/08/2026 numa sessao real contra
    // o servidor da Gameforge -- estes bytes sairam do `Aion.bin`, nao de um teste.
    //
    // O teste acima cifra o proprio pacote e confere que ele volta; este exige que o caminho de
    // desserializacao aceite o que o cliente de verdade manda, com a chave derivada do S_KEY.
    // ==============================================================================
    /// Seed do S_KEY da mesma sessao. O quadro do servidor viaja em claro e carrega este valor.
    const SEED_OFICIAL: u32 = 0x73CB_9F92;

    /// C_VERSION, 23 bytes no wire.
    const CLIENTE_1: &str = "1700a8d4be626ba0807e14869e2ceff5db3a227c65ad42";
    /// C_SYNC_TIME, 20 bytes.
    const CLIENTE_2: &str = "14008ff399575e590fd887f1d436c98aa4456834";
    /// C_SYNC_TIME de novo -- so abre se a chave tiver avancado pelos dois anteriores.
    const CLIENTE_3: &str = "1400611d77b9b04eb563cbbcf7d156e8c726e5b9";

    fn de_hex(h: &str) -> Vec<u8> {
        (0..h.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&h[i..i + 2], 16).unwrap())
            .collect()
    }

    #[test]
    fn desserializa_pacotes_reais_do_cliente_oficial() {
        let mut chave = gen_xor_key(SEED_OFICIAL).to_le_bytes();

        let casos: [(&str, u16, fn(&Message) -> bool); 3] = [
            (CLIENTE_1, 0x000, |m| matches!(m, Message::Version(_))),
            (CLIENTE_2, 0x012, |m| matches!(m, Message::SyncTime(_))),
            (CLIENTE_3, 0x012, |m| matches!(m, Message::SyncTime(_))),
        ];

        for (hex, opcode_esperado, e_o_esperado) in casos {
            let quadro = de_hex(hex);
            let mut corpo = quadro[2..].to_vec();

            let (msg, opcode) = Message::deserialise(&mut corpo, &mut chave).unwrap_or_else(|op| {
                panic!("pacote real do cliente recusado (opcode 0x{op:03X})")
            });

            assert_eq!(opcode, opcode_esperado, "opcode desofuscado");
            assert!(e_o_esperado(&msg), "caiu no handler errado: {msg:?}");
        }
    }

    #[test]
    fn com_a_chave_errada_o_pacote_real_e_recusado() {
        // Guarda: o checksum do cabecalho e a unica defesa contra chave dessincronizada. Se ele
        // parasse de ser conferido, um pacote decifrado errado viraria opcode aleatorio.
        let mut chave = gen_xor_key(SEED_OFICIAL ^ 1).to_le_bytes();
        let quadro = de_hex(CLIENTE_1);
        let mut corpo = quadro[2..].to_vec();

        assert!(
            Message::deserialise(&mut corpo, &mut chave).is_err(),
            "com a chave errada o checksum nao pode fechar"
        );
    }

    #[test]
    fn a_chave_do_cliente_avanca_pelo_tamanho_de_cada_pacote() {
        // Se a chave nao avancasse, o segundo pacote da sessao real nao abriria.
        let mut chave = gen_xor_key(SEED_OFICIAL).to_le_bytes();
        let inicial = chave;

        let quadro = de_hex(CLIENTE_1);
        let mut corpo = quadro[2..].to_vec();
        let _ = Message::deserialise(&mut corpo, &mut chave).expect("primeiro pacote");

        assert_ne!(chave, inicial, "a chave tem que avancar");
        assert_eq!(
            u64::from_le_bytes(chave),
            u64::from_le_bytes(inicial) + (quadro.len() - 2) as u64,
            "avanca exatamente pelo tamanho do corpo decifrado"
        );
    }
}
