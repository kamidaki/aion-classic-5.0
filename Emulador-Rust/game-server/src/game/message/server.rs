use commons::game::encrypt_server_opcode;

use crate::{
    copy_bytes,
    game::{
        character::Character,
        data::{
            gear::{Gear, LootItem, RawItem},
            item::ItemInventario,
            npc,
            skill::Skill,
            ActionType,
        },
        engine::{damage::Hit, Coord, Direction, MoveType},
        entity::Entity,
    },
    to_le_bytes,
};

use crate::game::Serialise;

/// Byte fixo que separa o opcode do checksum no cabecalho. A captura do servidor da Gameforge
/// mostra 0x65; o 0x40 que estava aqui vinha da versao 2.5.
const SERVER_BYTE: u8 = 0x65;
const LENGTH_LEN: usize = 2;

const VERSION_CHECK: u16 = 0x0000;
const STATUS: u16 = 0x0001;
const HIT_POINT: u16 = 0x0003;
const HIT_POINT_MP: u16 = 0x0004;
const HIT_POINT_OTHER: u16 = 0x0005;
const HIT_POINT_DP: u16 = 0x0006;
const EXP_UPDATE: u16 = 0x0008;
const ENTER_WORLD_CHECK: u16 = 0x000D;
const PUT_NPC: u16 = 0x000E;
const REQUEST_TELEPORT: u16 = 0x0014;
const REMOVE_OBJECT: u16 = 0x0016;
const WORLD: u16 = 0x000F;
const MESSAGE_CODE: u16 = 0x0019;
const LOAD_INVENTORY: u16 = 0x001A;
const CHANGE_ITEM_DESC: u16 = 0x001D;
const LOAD_CLIENT_SETTINGS: u16 = 0x001E;
const PUT_USER: u16 = 0x0020;
const USE_SKILL: u16 = 0x0021;
const UPDATE_PLAYER_APPEARANCE: u16 = 0x0024;
const ACTION: u16 = 0x0025;
const TIME: u16 = 0x0026;
const SYNC_TIME: u16 = 0x0027;
const NPC_CHANGED_TARGET: u16 = 0x0028;
const TARGET_INFO: u16 = 0x0029;
const SKILL_SUCCEDED: u16 = 0x002B;
const ADD_SKILL: u16 = 0x002C;
const ABNORMAL_STATUS: u16 = 0x0031;
const ABNORMAL_STATUS_OTHER: u16 = 0x0032;
const ATTACK: u16 = 0x0036;
const MOVE_NEW: u16 = 0x0037;
const DIALOG_WINDOW: u16 = 0x003C;
const WEATHER: u16 = 0x0042;
const INVISIBLE_LEVEL: u16 = 0x0043;
const QUEST_LIST: u16 = 0x0047;
const KEY: u16 = 0x0047;
const ASK_QUIT_RESULT: u16 = 0x0061;
const LOAD_ITEM_COOLTIME: u16 = 0x0066;
const BUDDY_LIST: u16 = 0x0083;
const GUILD_INFO: u16 = 0x006D;
const GUILD_MEMBER_INFO: u16 = 0x009C;
const GUILD_EMBLEM_IMG_DATA: u16 = 0x00D5;
const USER_GUILD_DONATION: u16 = 0x0158;
const USER_GUILD_COIN: u16 = 0x0165;
const GUILD_OPENED_BUFF_TREE_INFO: u16 = 0x0166;
const SA_ACCOUNT_ITEM_NOTI: u16 = 0x0088;
const WORLD_SCENE_STATUS: u16 = 0x008B;
const ALIVE: u16 = 0x008D;
const CUSTOM_ANIM: u16 = 0x0093;
const MAIL: u16 = 0x00A0;
const WIND_PATH_RESULT: u16 = 0x00A2;
const WIND_STATE_INFO: u16 = 0x00A3;
const PARTY_MATCH: u16 = 0x00A5;
const USER_SELL_HISTORY_LIST: u16 = 0x00A6;
const TITLE: u16 = 0x00AF;
const ALLIANCE_INFO: u16 = 0x00F5;
const ALLIANCE_MEMBER_INFO: u16 = 0x00F6;
const GLOBAL_TRADE_LIST: u16 = 0x013C;
const GLOBAL_TRADE_COMMIT: u16 = 0x013F;
const GLOBAL_TRADE_SALESLOG: u16 = 0x0141;
const GLOBAL_TRADE_STATE: u16 = 0x0144;
const GLOBAL_TRADE_HISTORY: u16 = 0x0145;
const SECOND_PASSWORD: u16 = 0x00B0;
const L2AUTH_LOGIN_CHECK: u16 = 0x00C6;
const CHARACTER_LIST: u16 = 0x00C7;
const CREATE_CHARACTER: u16 = 0x00C8;
const DELETE_CHARACTER: u16 = 0x00C9;
const LOOT_ITEMLIST: u16 = 0x00CD;
const LOOT: u16 = 0xCC;
const RECIPE_LIST: u16 = 0x00CE;
const SKILL_PENALTY_STATUS_OTHER: u16 = 0x00D8;
const CUR_STATUS: u16 = 0x00E3;
const CHANGE_CHANNEL: u16 = 0x00E5;
const SIGN_CLIENT: u16 = 0x00E6;
const BUILDER_LEVEL: u16 = 0x00EE;
const WORLD_INFO: u16 = 0x00EC;
const STORE_SALE_INFO: u16 = 0x00FD;
const INVINCIBLE_TIME: u16 = 0x00FE;
const RECONNECT_KEY: u16 = 0x00FF;
const _0102: u16 = 0x0102;
const REPLY_NP_LOGIN_GAMESVR: u16 = 0x0106;
const REPLY_NP_AUTH_TOKEN: u16 = 0x0108;
const NPSHOP_GOODS_COUNT: u16 = 0x010A;
const SERVER_ENV: u16 = 0x010E;
const RESULT_PASSPORT: u16 = 0x0113;
const GAMEPASS_INFO: u16 = 0x0119;
const READY_ENTER_WORLD: u16 = 0x011D;
const _0151: u16 = 0x0151;

#[derive(Debug, Clone)]
pub enum Message {
    VersionCheck(VersionCheck),
    HitPoint(HitPoint),
    HitPointOther(HitPointOther),
    Status(Status),
    World(World),
    EnterWorldCheck(EnterWorldCheck),
    ReconnectKey(ReconnectKey),
    LoadClientSettings(LoadClientSettings),
    PutUser(PutUser),
    CreateCharacter(CreateCharacter),
    AddSkill45(AddSkill45),
    CarregaInventario45(CarregaInventario45),
    RemoveObject(RemoveObject),
    TargetInfo(TargetInfo),
    SyncTime(SyncTime),
    NpcChangedTarget(NpcChangedTarget),
    MoveNew(MoveNew),
    Key(Key),
    BuddyList(BuddyList),
    Alive(Alive),
    Attack(Attack),
    L2AuthLoginCheck(L2AuthLoginCheck),
    CharacterList(CharacterList),
    RecipeList(RecipeList),
    CurStatus(CurStatus),
    BuilderLevel(BuilderLevel),
    ReplyNpLoginGamesvr(ReplyNpLoginGamesvr),
    ReplyNpAuthToken(ReplyNpAuthToken),
    NpShopGoodsCount(NpShopGoodsCount),
    ReadyEnterWorld(ReadyEnterWorld),
    ServerEnv(ServerEnv),
    SaAccountItemNoti(SaAccountItemNoti),
    SecondPassword(SecondPassword),
    AddSkill(AddSkill),
    LoadInventory(LoadInventory),
    ChangeItemDesc(ChangeItemDesc),
    Action(Action),
    ChangeChannel(ChangeChannel),
    Time(Time),
    WorldInfo(WorldInfo),
    Loot(Loot),
    LootItemlist(LootItemlist),
    WorldSceneStatus(WorldSceneStatus),
    GamepassInfo(GamepassInfo),
    MessageCode(MessageCode),
    _0102(_0102),
    AbnormalStatus(AbnormalStatus),
    AbnormalStatusOther(AbnormalStatusOther),
    InvincibleTime(InvincibleTime),
    InvisibleLevel(InvisibleLevel),
    SignClient(SignClient),
    _0151(_0151),
    Weather(Weather),
    ResultPassport(ResultPassport),
    UseSkill(UseSkill),
    SkillSucceded(SkillSucceded),
    CustomAnim(CustomAnim),
    Title(Title),
    LoadItemCooltime(LoadItemCooltime),
    AskQuitResult(AskQuitResult),
    PutNpc(PutNpc),
    Bruto(Bruto),
    ListaPersonagens45(ListaPersonagens45),
    DeleteCharacter(DeleteCharacter),
    DialogWindow(DialogWindow),
    RequestTeleport(RequestTeleport),
    WindStateInfo(WindStateInfo),
    WindPathResult(WindPathResult),
    SkillPenaltyStatusOther(SkillPenaltyStatusOther),
    HitPointMp(HitPointMp),
    HitPointDp(HitPointDp),
    ExpUpdate(ExpUpdate),
    QuestList(QuestList),
    UserSellHistoryList(UserSellHistoryList),
    StoreSaleInfo(StoreSaleInfo),
    UpdatePlayerAppearance(UpdatePlayerAppearance),
    Mail(Mail),
    GuildInfo(GuildInfo),
    GuildMemberInfo(GuildMemberInfo),
    GuildEmblemImgData(GuildEmblemImgData),
    UserGuildDonation(UserGuildDonation),
    UserGuildCoin(UserGuildCoin),
    GuildOpenedBuffTreeInfo(GuildOpenedBuffTreeInfo),
    AllianceInfo(AllianceInfo),
    AllianceMemberInfo(AllianceMemberInfo),
    GlobalTradeList(GlobalTradeList),
    GlobalTradeCommit(GlobalTradeCommit),
    GlobalTradeSaleslog(GlobalTradeSaleslog),
    GlobalTradeState(GlobalTradeState),
    GlobalTradeHistory(GlobalTradeHistory),
}

impl Serialise for Message {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = match self {
            Message::VersionCheck(msg) => msg.serialise(&mut buf[2..]),
            Message::Status(msg) => msg.serialise(&mut buf[2..]),
            Message::World(msg) => msg.serialise(&mut buf[2..]),
            Message::PutNpc(msg) => msg.serialise(&mut buf[2..]),
            Message::EnterWorldCheck(msg) => msg.serialise(&mut buf[2..]),
            Message::LoadClientSettings(msg) => msg.serialise(&mut buf[2..]),
            Message::UseSkill(msg) => msg.serialise(&mut buf[2..]),
            Message::SkillSucceded(msg) => msg.serialise(&mut buf[2..]),
            Message::PutUser(msg) => msg.serialise(&mut buf[2..]),
            Message::CreateCharacter(msg) => msg.serialise(&mut buf[2..]),
            Message::AddSkill45(msg) => msg.serialise(&mut buf[2..]),
            Message::CarregaInventario45(msg) => msg.serialise(&mut buf[2..]),
            Message::RemoveObject(msg) => msg.serialise(&mut buf[2..]),
            Message::CharacterList(msg) => msg.serialise(&mut buf[2..]),
            Message::CurStatus(msg) => msg.serialise(&mut buf[2..]),
            Message::Key(msg) => msg.serialise(&mut buf[2..]),
            Message::ServerEnv(msg) => msg.serialise(&mut buf[2..]),
            Message::SyncTime(msg) => msg.serialise(&mut buf[2..]),
            Message::NpcChangedTarget(msg) => msg.serialise(&mut buf[2..]),
            Message::Action(msg) => msg.serialise(&mut buf[2..]),
            Message::MoveNew(msg) => msg.serialise(&mut buf[2..]),
            Message::NpShopGoodsCount(msg) => msg.serialise(&mut buf[2..]),
            Message::ReplyNpAuthToken(msg) => msg.serialise(&mut buf[2..]),
            Message::ReplyNpLoginGamesvr(msg) => msg.serialise(&mut buf[2..]),
            Message::ReadyEnterWorld(msg) => msg.serialise(&mut buf[2..]),
            Message::L2AuthLoginCheck(msg) => msg.serialise(&mut buf[2..]),
            Message::BuilderLevel(msg) => msg.serialise(&mut buf[2..]),
            Message::Alive(msg) => msg.serialise(&mut buf[2..]),
            Message::TargetInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::SaAccountItemNoti(msg) => msg.serialise(&mut buf[2..]),
            Message::SecondPassword(msg) => msg.serialise(&mut buf[2..]),
            Message::AbnormalStatus(msg) => msg.serialise(&mut buf[2..]),
            Message::_0102(msg) => msg.serialise(&mut buf[2..]),
            Message::RecipeList(msg) => msg.serialise(&mut buf[2..]),
            Message::BuddyList(msg) => msg.serialise(&mut buf[2..]),
            Message::AddSkill(msg) => msg.serialise(&mut buf[2..]),
            Message::Attack(msg) => msg.serialise(&mut buf[2..]),
            Message::LoadInventory(msg) => msg.serialise(&mut buf[2..]),
            Message::ChangeItemDesc(msg) => msg.serialise(&mut buf[2..]),
            Message::ChangeChannel(msg) => msg.serialise(&mut buf[2..]),
            Message::Time(msg) => msg.serialise(&mut buf[2..]),
            Message::Loot(msg) => msg.serialise(&mut buf[2..]),
            Message::LootItemlist(msg) => msg.serialise(&mut buf[2..]),
            Message::WorldInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::GamepassInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::MessageCode(msg) => msg.serialise(&mut buf[2..]),
            Message::_0151(msg) => msg.serialise(&mut buf[2..]),
            Message::AbnormalStatusOther(msg) => msg.serialise(&mut buf[2..]),
            Message::InvincibleTime(msg) => msg.serialise(&mut buf[2..]),
            Message::InvisibleLevel(msg) => msg.serialise(&mut buf[2..]),
            Message::WorldSceneStatus(msg) => msg.serialise(&mut buf[2..]),
            Message::SignClient(msg) => msg.serialise(&mut buf[2..]),
            Message::Weather(msg) => msg.serialise(&mut buf[2..]),
            Message::ResultPassport(msg) => msg.serialise(&mut buf[2..]),
            Message::CustomAnim(msg) => msg.serialise(&mut buf[2..]),
            Message::Title(msg) => msg.serialise(&mut buf[2..]),
            Message::LoadItemCooltime(msg) => msg.serialise(&mut buf[2..]),
            Message::AskQuitResult(msg) => msg.serialise(&mut buf[2..]),
            Message::ReconnectKey(msg) => msg.serialise(&mut buf[2..]),
            Message::HitPointOther(msg) => msg.serialise(&mut buf[2..]),
            Message::HitPoint(msg) => msg.serialise(&mut buf[2..]),
            Message::Bruto(msg) => msg.serialise(&mut buf[2..]),
            Message::ListaPersonagens45(msg) => msg.serialise(&mut buf[2..]),
            Message::DeleteCharacter(msg) => msg.serialise(&mut buf[2..]),
            Message::DialogWindow(msg) => msg.serialise(&mut buf[2..]),
            Message::RequestTeleport(msg) => msg.serialise(&mut buf[2..]),
            Message::WindStateInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::WindPathResult(msg) => msg.serialise(&mut buf[2..]),
            Message::SkillPenaltyStatusOther(msg) => msg.serialise(&mut buf[2..]),
            Message::HitPointMp(msg) => msg.serialise(&mut buf[2..]),
            Message::HitPointDp(msg) => msg.serialise(&mut buf[2..]),
            Message::ExpUpdate(msg) => msg.serialise(&mut buf[2..]),
            Message::QuestList(msg) => msg.serialise(&mut buf[2..]),
            Message::UserSellHistoryList(msg) => msg.serialise(&mut buf[2..]),
            Message::StoreSaleInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::UpdatePlayerAppearance(msg) => msg.serialise(&mut buf[2..]),
            Message::Mail(msg) => msg.serialise(&mut buf[2..]),
            Message::GuildInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::GuildMemberInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::GuildEmblemImgData(msg) => msg.serialise(&mut buf[2..]),
            Message::UserGuildDonation(msg) => msg.serialise(&mut buf[2..]),
            Message::UserGuildCoin(msg) => msg.serialise(&mut buf[2..]),
            Message::GuildOpenedBuffTreeInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::AllianceInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::AllianceMemberInfo(msg) => msg.serialise(&mut buf[2..]),
            Message::GlobalTradeList(msg) => msg.serialise(&mut buf[2..]),
            Message::GlobalTradeCommit(msg) => msg.serialise(&mut buf[2..]),
            Message::GlobalTradeSaleslog(msg) => msg.serialise(&mut buf[2..]),
            Message::GlobalTradeState(msg) => msg.serialise(&mut buf[2..]),
            Message::GlobalTradeHistory(msg) => msg.serialise(&mut buf[2..]),
        };

        len += LENGTH_LEN;
        buf[..LENGTH_LEN].copy_from_slice(&(len as u16).to_le_bytes());
        len
    }
}

/// S_CHARACTER_LIST no layout 4.5. Ver [`super::lista_personagens`].
#[derive(Debug, Clone)]
pub struct ListaPersonagens45(pub super::lista_personagens::ListaPersonagens);

impl Serialise for ListaPersonagens45 {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = add_prelude(CHARACTER_LIST, buf);
        len += self.0.serialise_payload(&mut buf[len..]);
        len
    }
}

/// Pacote montado a partir de bytes capturados de uma sessao real.
///
/// Serve para reproduzir um pacote antes de entender o layout dele campo a campo. O prelude
/// (opcode, SERVER_BYTE, checksum) e construido normalmente; so o payload vem pronto.
#[derive(Debug, Clone)]
pub struct Bruto {
    opcode: u16,
    payload: Vec<u8>,
}

impl Bruto {
    pub fn new(opcode: u16, payload: Vec<u8>) -> Self {
        Self { opcode, payload }
    }
}

impl Serialise for Bruto {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = add_prelude(self.opcode, buf);
        buf[len..len + self.payload.len()].copy_from_slice(&self.payload);
        len + self.payload.len()
    }
}

/// Returns a buffer with the opcode, [SERVER_BYTE] and checksum
#[inline(always)]
fn add_prelude(opcode: u16, buf: &mut [u8]) -> usize {
    let opcode = encrypt_server_opcode(opcode);
    let checksum = !opcode;

    let mut len = 0;
    to_le_bytes!(len, buf, opcode);
    to_le_bytes!(len, buf, SERVER_BYTE);
    to_le_bytes!(len, buf, checksum);
    len
}

#[derive(Debug, Clone)]
pub struct Key {
    key: u32,
}
impl Key {
    pub fn new(key: u32) -> Self {
        Self { key }
    }
}
impl Serialise for Key {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(KEY, buf);

        buf[len..len + 4].copy_from_slice(&self.key.to_le_bytes());
        len += 4;

        len
    }
}

#[link(name = "kernel32")]
#[allow(non_snake_case)]
extern "system" {
    fn GetTickCount() -> u32;
}

#[derive(Debug, Clone)]
pub struct SyncTime {
    server_uptime_ticks: u32,
    session_ticks: u32,
    _unknown: [u8; 4],
    sequence: u32,
}
impl SyncTime {
    pub fn new(session_ticks: u32) -> Self {
        Self {
            server_uptime_ticks: unsafe { GetTickCount() },
            session_ticks,
            _unknown: [0x0, 0x0, 0x0, 0x0],
            sequence: 1,
        }
    }
}
impl Serialise for SyncTime {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SYNC_TIME, buf);

        let server_uptime_ticks = self.server_uptime_ticks.to_le_bytes();
        buf[len..len + server_uptime_ticks.len()]
            .copy_from_slice(&server_uptime_ticks);
        len += server_uptime_ticks.len();

        let session_ticks = self.session_ticks.to_le_bytes();
        buf[len..len + session_ticks.len()].copy_from_slice(&session_ticks);
        len += server_uptime_ticks.len();

        buf[len..len + self._unknown.len()].copy_from_slice(&self._unknown);
        len += self._unknown.len();

        let sequence = self.sequence.to_le_bytes();
        buf[len..len + sequence.len()].copy_from_slice(&sequence);
        len += sequence.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct VersionCheck {
    opcode: u8,
    server_id: u8,
    server_build_date1: [u8; 4],
    server_build_date2: [u8; 4],
    _unknown_static1: [u8; 4],
    server_build_date3: [u8; 4],
    server_start_epoch: [u8; 4],
    _unknown_static2: [u8; 3],
    _unknown_rand1: [u8; 4],
    _unknown_static3: [u8; 23],
}

impl VersionCheck {
    pub fn new() -> Self {
        Self {
            opcode: 0,
            server_id: 15,
            server_build_date1: [0xE3, 0xAB, 0x03, 0x00],
            server_build_date2: [0xE3, 0xAB, 0x03, 0x00],
            _unknown_static1: [0u8; 4],
            server_build_date3: [0xE3, 0xAB, 0x03, 0x00],
            server_start_epoch: [0x47, 0x04, 0x85, 0x66],
            _unknown_static2: [0x00, 0x02, 0x00],
            _unknown_rand1: [0x90, 0xD2, 0x8C, 0x95],
            _unknown_static3: [
                0x66, 0xF0, 0xF1, 0xFF, 0xFF, 0xF0, 0xF1, 0xFF, 0xFF, 0x01,
                0x00, 0x00, 0x4F, 0x6E, 0x53, 0x9F, 0x01, 0x28, 0x9B, 0x02,
                0x00, 0x00, 0x00,
            ],
        }
    }
}

impl Serialise for VersionCheck {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(VERSION_CHECK, buf);

        buf[len] = self.opcode;
        len += 1;
        buf[len] = self.server_id;
        len += 1;
        buf[len..len + 4].copy_from_slice(&self.server_build_date1);
        len += 4;
        buf[len..len + 4].copy_from_slice(&self.server_build_date2);
        len += 4;
        buf[len..len + 4].copy_from_slice(&self._unknown_static1);
        len += 4;
        buf[len..len + 4].copy_from_slice(&self.server_build_date3);
        len += 4;
        buf[len..len + 4].copy_from_slice(&self.server_start_epoch);
        len += 4;
        buf[len..len + 3].copy_from_slice(&self._unknown_static2);
        len += 3;
        buf[len..len + 4].copy_from_slice(&self._unknown_rand1);
        len += 4;
        buf[len..len + 23].copy_from_slice(&self._unknown_static3);
        len += 23;

        len
    }
}

#[derive(Debug, Clone)]
pub struct NpShopGoodsCount {
    pub raw: [u8; 4],
}
impl NpShopGoodsCount {
    pub fn new() -> Self {
        Self { raw: [1, 0, 0, 0] }
    }
}
impl Serialise for NpShopGoodsCount {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        len += add_prelude(NPSHOP_GOODS_COUNT, buf);
        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct ReadyEnterWorld {
    pub unknown_static1: [u8; 2],
    pub unknown_rand1: [u8; 4],
}

impl ReadyEnterWorld {
    pub fn new() -> Self {
        Self {
            unknown_static1: [0u8; 2],
            unknown_rand1: [0xFF, 0x39, 0x60, 0x05],
        }
    }
}
impl Serialise for ReadyEnterWorld {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        len += add_prelude(READY_ENTER_WORLD, buf);

        buf[len..len + self.unknown_static1.len()]
            .copy_from_slice(&self.unknown_static1);
        len += self.unknown_static1.len();
        buf[len..len + self.unknown_rand1.len()]
            .copy_from_slice(&self.unknown_rand1);
        len += self.unknown_rand1.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct ReplyNpLoginGamesvr {
    pub raw: [u8; 2],
}
impl ReplyNpLoginGamesvr {
    pub fn new() -> Self {
        Self { raw: [0, 1] }
    }
}
impl Serialise for ReplyNpLoginGamesvr {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        len += add_prelude(REPLY_NP_LOGIN_GAMESVR, buf);
        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct ServerEnv {
    _unknown: [u8; 33],
}
impl ServerEnv {
    pub fn new() -> Self {
        Self {
            _unknown: [
                0x5E, 0x01, 0x01, 0x0A, 0x01, 0x0A, 0x0A, 0x0A, 0x02, 0x00,
                0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00,
                0x01, 0x37, 0x00, 0x00, 0x00, 0x37, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00,
            ],
        }
    }
}
impl Serialise for ServerEnv {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        len += add_prelude(SERVER_ENV, buf);
        buf[len..len + self._unknown.len()].copy_from_slice(&self._unknown);
        len += self._unknown.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct ReplyNpAuthToken {
    _unknown: [u8; 150],
}
impl ReplyNpAuthToken {
    /// Tamanho fixo do campo do token, medido na captura.
    const TOKEN_LEN: usize = 100;

    /// O que vem depois do token: um identificador de produto, "aiongfc", e tres bytes. Iguais na
    /// captura inteira, entao sao do cliente e nao da conta.
    const APP: &'static [u8] = b"8B557374-1872-47BC-983D-7582071214A6 aiongfc ";

    /// Devolve ao cliente o token que ele mesmo mandou no `C_HQ_LOGIN`.
    ///
    /// O payload daqui era o da captura, byte a byte -- e o token de uma conta real da Gameforge,
    /// uma credencial, dentro do binario e de qualquer copia dele. Devolver o do proprio cliente e
    /// o comportamento certo e tira a credencial do fonte.
    ///
    /// Token maior que o campo e truncado, menor e preenchido com zeros: o campo tem tamanho fixo.
    pub fn para(token: &str) -> Self {
        let mut payload = [0u8; 150];
        payload[0] = 0x01;

        let bytes = token.as_bytes();
        let n = bytes.len().min(Self::TOKEN_LEN);
        payload[1..1 + n].copy_from_slice(&bytes[..n]);

        // 1 (marca) + 100 (token) + 1 (terminador) e o resto e o identificador do cliente
        let inicio_do_app = 1 + Self::TOKEN_LEN + 1;
        payload[inicio_do_app..].copy_from_slice(Self::APP);

        Self { _unknown: payload }
    }
}
impl Serialise for ReplyNpAuthToken {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        len += add_prelude(REPLY_NP_AUTH_TOKEN, buf);
        buf[len..len + self._unknown.len()].copy_from_slice(&self._unknown);
        len += self._unknown.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct CharacterList {
    unknown1: u8,
    auth_server_id: [u8; 4],
    len: u8,
    character_id: u32,
    name: String,
    header: [u8; 238],
    gear: Gear,
    last_logged_in: u32,
    footer: [u8; 146],
}
impl CharacterList {
    pub fn new(
        auth_server_id: [u8; 4],
        name: String,
        gear: Gear,
        last_logged_in: u32,
        character_id: u32,
    ) -> Self {
        let header = [
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x02, 0x00,
            0x00, 0x00, 0xAB, 0xAB, 0xBC, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0xE9,
            0x02, 0x0F, 0x00, 0xCE, 0xB4, 0xCA, 0x00, 0x00, 0x0A, 0x00, 0x00,
            0x00, 0x02, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x09, 0x83, 0x8F, 0x00, 0x03, 0x00, 0x00, 0x00, 0x83, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x04, 0xEF, 0xB3, 0xDA, 0xB2,
            0xF0, 0xDF, 0xEF, 0xBA, 0xF4, 0xCE, 0x00, 0x00, 0xF0, 0xF4, 0xF5,
            0xE4, 0x00, 0x00, 0x00, 0x66, 0x66, 0x26, 0x3F, 0xA3, 0x86, 0x01,
            0x00, 0x30, 0x64, 0x1D, 0x0D, // Coords
            0x92, 0xDA, 0xEB, 0x44, 0xFC, 0x67, 0x2F, 0x44, 0x2D, 0x15, 0x81,
            0x43, // Direction?
            0x11, 0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00, 0x34, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00,
        ];

        let footer = [
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00,
            0x00, 0x04, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xC5, 0x01, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00,
        ];

        Self {
            unknown1: 2,
            auth_server_id,
            len: 1,
            character_id,
            name,
            header,
            last_logged_in,
            gear,
            footer,
        }
    }
}
impl Serialise for CharacterList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(CHARACTER_LIST, buf);

        buf[len] = self.unknown1;
        len += 1;

        buf[len..len + self.auth_server_id.len()]
            .copy_from_slice(&self.auth_server_id);
        len += self.auth_server_id.len();

        buf[len] = self.len;
        len += 1;

        to_le_bytes!(len, buf, self.character_id);

        self.name.encode_utf16().for_each(|c| {
            buf[len + 0] = c as u8;
            buf[len + 1] = (c >> 8) as u8;
            len += 2;
        });

        buf[len..len + self.header.len()].copy_from_slice(&self.header);
        len += self.header.len();

        buf[len..len + 4].copy_from_slice(&self.last_logged_in.to_le_bytes());
        len += 4;

        len += self.gear.serialiase_character_list(&mut buf[len..]);

        buf[len..len + self.footer.len()].copy_from_slice(&self.footer);
        len += self.footer.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct L2AuthLoginCheck {
    _unknown: [u8; 1185],
}
impl L2AuthLoginCheck {
    pub fn new() -> Self {
        Self {
            _unknown: [
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x01, 0x01, 0x01, 0x02, 0x02, 0x02, 0x03, 0x03, 0x03, 0x04,
                0x04, 0x04, 0x05, 0x05, 0x05, 0x06, 0x06, 0x06, 0x07, 0x07,
                0x07, 0x08, 0x08, 0x08, 0x09, 0x09, 0x09, 0x0A, 0x0A, 0x0A,
                0x0B, 0x0B, 0x0B, 0x0C, 0x0C, 0x0C, 0x0D, 0x0D, 0x0D, 0x0E,
                0x0E, 0x0E, 0x0F, 0x0F, 0x0F, 0x10, 0x10, 0x10, 0x11, 0x11,
                0x11, 0x12, 0x12, 0x12, 0x13, 0x13, 0x13, 0x14, 0x14, 0x14,
                0x15, 0x15, 0x15, 0x16, 0x16, 0x16, 0x17, 0x17, 0x17, 0x18,
                0x18, 0x18, 0x19, 0x19, 0x19, 0x1A, 0x1A, 0x1A, 0x1B, 0x1B,
                0x1B, 0x1C, 0x1C, 0x1C, 0x1D, 0x1D, 0x1D, 0x1E, 0x1E, 0x1E,
                0x1F, 0x1F, 0x1F, 0x20, 0x20, 0x20, 0x21, 0x21, 0x21, 0x22,
                0x22, 0x22, 0x23, 0x23, 0x23, 0x24, 0x24, 0x24, 0x25, 0x25,
                0x25, 0x26, 0x26, 0x26, 0x27, 0x27, 0x27, 0x28, 0x28, 0x28,
                0x29, 0x29, 0x29, 0x2A, 0x2A, 0x2A, 0x2B, 0x2B, 0x2B, 0x2C,
                0x2C, 0x2C, 0x2D, 0x2D, 0x2D, 0x2E, 0x2E, 0x2E, 0x2F, 0x2F,
                0x2F, 0x30, 0x30, 0x30, 0x31, 0x31, 0x31, 0x32, 0x32, 0x32,
                0x33, 0x33, 0x33, 0x34, 0x34, 0x34, 0x35, 0x35, 0x35, 0x36,
                0x36, 0x36, 0x37, 0x37, 0x37, 0x38, 0x38, 0x38, 0x39, 0x39,
                0x39, 0x3A, 0x3A, 0x3A, 0x3B, 0x3B, 0x3B, 0x3C, 0x3C, 0x3C,
                0x3D, 0x3D, 0x3D, 0x3E, 0x3E, 0x3E, 0x3F, 0x3F, 0x3F, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x01, 0x02, 0x02, 0x02,
                0x03, 0x03, 0x03, 0x04, 0x04, 0x04, 0x05, 0x05, 0x05, 0x06,
                0x06, 0x06, 0x07, 0x07, 0x07, 0x08, 0x08, 0x08, 0x09, 0x09,
                0x09, 0x0A, 0x0A, 0x0A, 0x0B, 0x0B, 0x0B, 0x0C, 0x0C, 0x0C,
                0x0D, 0x0D, 0x0D, 0x0E, 0x0E, 0x0E, 0x0F, 0x0F, 0x0F, 0x10,
                0x10, 0x10, 0x11, 0x11, 0x11, 0x12, 0x12, 0x12, 0x13, 0x13,
                0x13, 0x14, 0x14, 0x14, 0x15, 0x15, 0x15, 0x16, 0x16, 0x16,
                0x17, 0x17, 0x17, 0x18, 0x18, 0x18, 0x19, 0x19, 0x19, 0x1A,
                0x1A, 0x1A, 0x1B, 0x1B, 0x1B, 0x1C, 0x1C, 0x1C, 0x1D, 0x1D,
                0x1D, 0x1E, 0x1E, 0x1E, 0x1F, 0x1F, 0x1F, 0x20, 0x20, 0x20,
                0x21, 0x21, 0x21, 0x22, 0x22, 0x22, 0x23, 0x23, 0x23, 0x24,
                0x24, 0x24, 0x25, 0x25, 0x25, 0x26, 0x26, 0x26, 0x27, 0x27,
                0x27, 0x28, 0x28, 0x28, 0x29, 0x29, 0x29, 0x2A, 0x2A, 0x2A,
                0x2B, 0x2B, 0x2B, 0x2C, 0x2C, 0x2C, 0x2D, 0x2D, 0x2D, 0x2E,
                0x2E, 0x2E, 0x2F, 0x2F, 0x2F, 0x30, 0x30, 0x30, 0x31, 0x31,
                0x31, 0x32, 0x32, 0x32, 0x33, 0x33, 0x33, 0x34, 0x34, 0x34,
                0x35, 0x35, 0x35, 0x36, 0x36, 0x36, 0x37, 0x37, 0x37, 0x38,
                0x38, 0x38, 0x39, 0x39, 0x39, 0x3A, 0x3A, 0x3A, 0x3B, 0x3B,
                0x3B, 0x3C, 0x3C, 0x3C, 0x3D, 0x3D, 0x3D, 0x3E, 0x3E, 0x3E,
                0x3F, 0x3F, 0x3F, 0x61, 0x00, 0x10, 0xAB, 0xD7, 0x17, 0x01,
                0x00, 0x80, 0x46, 0x28, 0x07, 0x01, 0x00, 0xF0, 0x88, 0x8F,
                0x06, 0x01, 0x00, 0x10, 0x35, 0x27, 0x07, 0x01, 0x00, 0x20,
                0x5C, 0x27, 0x07, 0x01, 0x00, 0x10, 0x16, 0x1D, 0x0D, 0x0A,
                0x00, 0x30, 0x64, 0x1D, 0x0D, 0x0A, 0x00, 0x20, 0x3D, 0x1D,
                0x0D, 0x01, 0x00, 0x50, 0xB2, 0x1D, 0x0D, 0x03, 0x00, 0x40,
                0x8B, 0x1D, 0x0D, 0x01, 0x00, 0x70, 0x00, 0x1E, 0x0D, 0x01,
                0x00, 0x10, 0xB9, 0xFE, 0x1E, 0x01, 0x00, 0xB0, 0x50, 0xE3,
                0x11, 0x00, 0x00, 0x30, 0x18, 0xE2, 0x11, 0x00, 0x00, 0x30,
                0x45, 0x13, 0x13, 0x00, 0x00, 0x40, 0x6C, 0x13, 0x13, 0x00,
                0x00, 0xB0, 0xAE, 0x7A, 0x12, 0x00, 0x00, 0xC0, 0xD5, 0x7A,
                0x12, 0x00, 0x00, 0x10, 0xCA, 0xE1, 0x11, 0x00, 0x00, 0x10,
                0xF7, 0x12, 0x13, 0x00, 0x00, 0x20, 0x1E, 0x13, 0x13, 0x00,
                0x00, 0xE0, 0xF2, 0x14, 0x13, 0x00, 0x00, 0x90, 0x60, 0x7A,
                0x12, 0x00, 0x00, 0xA0, 0x87, 0x7A, 0x12, 0x00, 0x00, 0x40,
                0x0E, 0x7C, 0x12, 0x00, 0x00, 0x60, 0xFE, 0xE4, 0x11, 0x00,
                0x00, 0x60, 0x8D, 0xE2, 0x11, 0x00, 0x00, 0x90, 0x02, 0xE3,
                0x11, 0x00, 0x00, 0x80, 0xDB, 0xE2, 0x11, 0x00, 0x00, 0xE0,
                0xC5, 0xE3, 0x11, 0x00, 0x00, 0xC0, 0x77, 0xE3, 0x11, 0x00,
                0x00, 0xD0, 0x9E, 0xE3, 0x11, 0x00, 0x00, 0x50, 0x66, 0xE2,
                0x11, 0x00, 0x00, 0x70, 0xB4, 0xE2, 0x11, 0x00, 0x00, 0xE0,
                0x36, 0xE6, 0x11, 0x00, 0x00, 0xF0, 0xCE, 0xE8, 0x11, 0x00,
                0x00, 0x30, 0xFA, 0xE6, 0x11, 0x00, 0x00, 0xA0, 0x0B, 0xE8,
                0x11, 0x00, 0x00, 0x40, 0x21, 0xE7, 0x11, 0x00, 0x00, 0xB0,
                0x32, 0xE8, 0x11, 0x00, 0x00, 0x00, 0x85, 0xE6, 0x11, 0x00,
                0x00, 0x40, 0x92, 0xE9, 0x11, 0x00, 0x00, 0x50, 0xB9, 0xE9,
                0x11, 0x00, 0x00, 0x10, 0x3B, 0xE4, 0x11, 0x00, 0x00, 0x10,
                0x1D, 0xE9, 0x11, 0x00, 0x00, 0x70, 0x25, 0xE5, 0x11, 0x00,
                0x00, 0x90, 0x2F, 0x14, 0x13, 0x00, 0x00, 0xC0, 0xA4, 0x14,
                0x13, 0x00, 0x00, 0x60, 0xBA, 0x13, 0x13, 0x00, 0x00, 0xD0,
                0xCB, 0x14, 0x13, 0x00, 0x00, 0x50, 0x93, 0x13, 0x13, 0x00,
                0x00, 0xA0, 0x56, 0x14, 0x13, 0x00, 0x00, 0x80, 0x08, 0x14,
                0x13, 0x00, 0x00, 0x00, 0xF6, 0xE8, 0x11, 0x00, 0x00, 0xB0,
                0x7D, 0x14, 0x13, 0x00, 0x00, 0xF0, 0x19, 0x15, 0x13, 0x00,
                0x00, 0x50, 0xD7, 0xE4, 0x11, 0x00, 0x00, 0x30, 0x89, 0xE4,
                0x11, 0x00, 0x00, 0x90, 0x73, 0xE5, 0x11, 0x00, 0x00, 0x20,
                0x44, 0xE9, 0x11, 0x00, 0x00, 0x30, 0x6B, 0xE9, 0x11, 0x00,
                0x00, 0x00, 0x72, 0x7B, 0x12, 0x00, 0x00, 0x70, 0x07, 0xEA,
                0x11, 0x00, 0x00, 0x60, 0xE0, 0xE9, 0x11, 0x00, 0x00, 0x80,
                0x2E, 0xEA, 0x11, 0x00, 0x00, 0x40, 0x3F, 0xE2, 0x11, 0x00,
                0x00, 0xE0, 0x23, 0x7B, 0x12, 0x00, 0x00, 0xF0, 0x4A, 0x7B,
                0x12, 0x00, 0x00, 0x30, 0xE7, 0x7B, 0x12, 0x00, 0x00, 0xD0,
                0xFC, 0x7A, 0x12, 0x00, 0x00, 0x10, 0x99, 0x7B, 0x12, 0x00,
                0x00, 0x20, 0xC0, 0x7B, 0x12, 0x00, 0x00, 0x40, 0xB0, 0xE4,
                0x11, 0x00, 0x00, 0x90, 0x8D, 0xAB, 0x13, 0x00, 0x00, 0xA0,
                0x29, 0xE3, 0x11, 0x00, 0x00, 0xD0, 0x80, 0xE8, 0x11, 0x00,
                0x00, 0x70, 0xE1, 0x13, 0x13, 0x00, 0x00, 0x00, 0x14, 0xE4,
                0x11, 0x00, 0x00, 0xE8, 0x17, 0xE4, 0x11, 0x00, 0x00, 0xF0,
                0xEC, 0xE3, 0x11, 0x00, 0x00, 0xD8, 0xF0, 0xE3, 0x11, 0x00,
                0x00, 0xE0, 0xA7, 0xE8, 0x11, 0x00, 0x00, 0xC0, 0x59, 0xE8,
                0x11, 0x00, 0x00, 0x90, 0x9E, 0x8E, 0x06, 0x01, 0x00, 0xA0,
                0xC5, 0x8E, 0x06, 0x01, 0x00, 0xF0, 0x69, 0x85, 0x0C, 0x0A,
                0x00, 0x80, 0x27, 0x1E, 0x0D, 0x0A, 0x00, 0x20, 0x94, 0xC3,
                0x23, 0x01, 0x00, 0x90, 0x7F, 0x84, 0x0C, 0x0A, 0x00, 0xB0,
                0xCD, 0x84, 0x0C, 0x0A, 0x00, 0xA0, 0xA6, 0x84, 0x0C, 0x01,
                0x00, 0xE0, 0x42, 0x85, 0x0C, 0x03, 0x00, 0xC0, 0xF4, 0x84,
                0x0C, 0x01, 0x00, 0xD0, 0x1B, 0x85, 0x0C, 0x01, 0x00, 0x90,
                0x22, 0x66, 0x1E, 0x01, 0x00, 0x60, 0x44, 0xA8, 0x35, 0x01,
                0x00, 0x10, 0x6D, 0xC3, 0x23, 0x01, 0x00, 0x34, 0x00, 0x30,
                0x00, 0x30, 0x00, 0x32, 0x00, 0x38, 0x00, 0x38, 0x00, 0x35,
                0x00, 0x34, 0x00, 0x00, 0x00,
            ],
        }
    }
}
impl Serialise for L2AuthLoginCheck {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(L2AUTH_LOGIN_CHECK, buf);

        buf[len..len + self._unknown.len()].copy_from_slice(&self._unknown);
        len += self._unknown.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct BuilderLevel {
    pub raw: [u8; 29],
}
impl BuilderLevel {
    pub fn new() -> Self {
        Self {
            raw: [
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ],
        }
    }
}
impl Serialise for BuilderLevel {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(BUILDER_LEVEL, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct SaAccountItemNoti {
    raw: [u8; 4],
}
impl SaAccountItemNoti {
    pub fn new() -> Self {
        Self { raw: [0u8; 4] }
    }
}
impl Serialise for SaAccountItemNoti {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SA_ACCOUNT_ITEM_NOTI, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone, Copy)]
#[repr(u8)]
enum SecondPasswordOpcode {
    Request = 1,
    Response = 2,
}
#[derive(Debug, Clone)]
pub struct SecondPassword {
    opcode: SecondPasswordOpcode,
    unknown: [u8; 11],
}
impl SecondPassword {
    pub fn request() -> Self {
        Self {
            opcode: SecondPasswordOpcode::Request,
            unknown: [0u8; 11],
        }
    }
    /// TODO: Reverse this, this responds okay
    pub fn response() -> Self {
        Self {
            opcode: SecondPasswordOpcode::Response,
            unknown: [
                0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x0, 0x00, 0x00,
            ],
        }
    }
}
impl Serialise for SecondPassword {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SECOND_PASSWORD, buf);

        buf[len] = self.opcode as u8;
        len += 1;

        match self.opcode {
            SecondPasswordOpcode::Request => len,
            SecondPasswordOpcode::Response => {
                buf[len..len + self.unknown.len()]
                    .copy_from_slice(&self.unknown);
                len += self.unknown.len();
                len
            }
        }
    }
}

/// Acknowledges a C_ENTER_WORLD (Opcode 0x000D).
///
/// check_type:
/// - 0x00: entrada normal no mundo
/// - 0x01: retorno de dungeon / instância
#[derive(Debug, Clone)]
pub struct EnterWorldCheck {
    pub check_type: u8,
    pub raw: [u8; 2],
}
impl EnterWorldCheck {
    pub fn new() -> Self {
        Self {
            check_type: 0x00,
            raw: [0u8; 2],
        }
    }
    pub fn with_type(check_type: u8) -> Self {
        Self {
            check_type,
            raw: [0u8; 2],
        }
    }
}
impl Serialise for EnterWorldCheck {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ENTER_WORLD_CHECK, buf);

        to_le_bytes!(len, buf, self.check_type);
        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

/// Tira uma entidade de cena.
///
/// Cinco bytes na captura, sempre: o id da entidade e um zero. E o par do `S_PUT_NPC` -- sem ele,
/// NPC que sai do alcance de visao fica desenhado para sempre.
#[derive(Debug, Clone)]
pub struct RemoveObject {
    entity_id: u32,
}
impl RemoveObject {
    pub fn new(entity_id: u32) -> Self {
        Self { entity_id }
    }
}
impl Serialise for RemoveObject {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(REMOVE_OBJECT, buf);
        buf[len..len + 4].copy_from_slice(&self.entity_id.to_le_bytes());
        len += 4;
        buf[len] = 0;
        len += 1;
        len
    }
}

/// `S_LOAD_INVENTORY` no layout 4.5.
///
/// Da captura: cabecalho de sete bytes, um u16 com quantos registros vem, e os registros. Os
/// sete bytes sao `[u8 primeira leva][u8 cubos de NPC][u8 cubos de quest][u8 ?][3 zeros]` -- a
/// personagem gravada, que tinha comprado expansao de bolsa, mandou `01 03 01 01 00 00 00`; a
/// que nao tinha, `01 00 00 00 00 00 00`.
///
/// A bolsa vem em levas de dez itens, e a ultima e **vazia**: uma leva com zero registros fecha
/// o carregamento. Nas tres vezes que a captura carrega uma bolsa, o ultimo pacote tem os nove
/// bytes do cabecalho e mais nada.
#[derive(Debug, Clone)]
pub struct CarregaInventario45 {
    primeira: bool,
    itens: Vec<ItemInventario>,
}
impl CarregaInventario45 {
    /// Quantos itens cabem numa leva. O servidor oficial nunca passou de dez.
    pub const POR_LEVA: usize = 10;

    pub fn leva(primeira: bool, itens: Vec<ItemInventario>) -> Self {
        Self { primeira, itens }
    }

    /// A leva vazia que fecha o carregamento.
    pub fn fim() -> Self {
        Self { primeira: false, itens: Vec::new() }
    }
}
impl Serialise for CarregaInventario45 {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = add_prelude(LOAD_INVENTORY, buf);

        buf[len] = self.primeira as u8;
        len += 1;
        // Expansoes de bolsa comprada e ganha em quest, e um byte que a captura so mostra ligado
        // junto com elas. Personagem novo nao tem nenhuma.
        buf[len..len + 6].fill(0);
        len += 6;

        buf[len..len + 2].copy_from_slice(&(self.itens.len() as u16).to_le_bytes());
        len += 2;

        for item in &self.itens {
            len += item.escreve(&mut buf[len..]);
        }

        len
    }
}

/// Concede skills ao personagem.
///
/// Formato conferido nos quatro tamanhos que a captura mostra -- 17, 39, 325 e 1975 bytes:
///
/// ```text
/// [u16 quantas][entrada * quantas][u32 zero]
/// entrada = [u16 skill][u16 nivel][u16 zero][u32 quando][u8 zero]   // 11 bytes
/// ```
///
/// 17 = 2 + 1*11 + 4, 39 = 2 + 3*11 + 4, 325 = 2 + 29*11 + 4, 1975 = 2 + 179*11 + 4.
///
/// `quando` e um unix time; na captura todas as entradas de um mesmo lote trazem o mesmo valor,
/// que e o momento em que o personagem as recebeu.
#[derive(Debug, Clone)]
pub struct AddSkill45 {
    skills: Vec<u32>,
    quando: u32,
}
impl AddSkill45 {
    pub fn new(skills: Vec<u32>, quando: u32) -> Self {
        Self { skills, quando }
    }
}
impl Serialise for AddSkill45 {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ADD_SKILL, buf);

        buf[len..len + 2].copy_from_slice(&(self.skills.len() as u16).to_le_bytes());
        len += 2;

        for id in &self.skills {
            buf[len..len + 2].copy_from_slice(&(*id as u16).to_le_bytes());
            len += 2;
            // Nivel da skill. Toda skill concedida por nivel de personagem entra no grau 1; os
            // graus seguintes sao outra linha da arvore, com outro id.
            buf[len..len + 2].copy_from_slice(&1u16.to_le_bytes());
            len += 2;
            buf[len..len + 2].fill(0);
            len += 2;
            buf[len..len + 4].copy_from_slice(&self.quando.to_le_bytes());
            len += 4;
            buf[len] = 0;
            len += 1;
        }

        buf[len..len + 4].fill(0);
        len += 4;

        len
    }
}

/// Resposta ao pedido de criacao de personagem (cliente 0x5F).
///
/// Na captura sao 748 bytes: um u32 de resultado, zero para sucesso, seguido dos primeiros 744
/// bytes do mesmo registro que a lista de personagens usa -- ver
/// [`super::lista_personagens::REGISTRO_CRIACAO_LEN`].
#[derive(Debug, Clone)]
pub struct CreateCharacter {
    personagem: super::lista_personagens::Personagem,
}
impl CreateCharacter {
    pub fn new(personagem: super::lista_personagens::Personagem) -> Self {
        Self { personagem }
    }
}
impl Serialise for CreateCharacter {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        use super::lista_personagens::{escreve_registro, REGISTRO_CRIACAO_LEN};
        use super::molde::REGISTRO_LEN;

        let mut len = 0;
        len += add_prelude(CREATE_CHARACTER, buf);

        // Resultado: zero e sucesso, o unico valor que a captura mostra.
        buf[len..len + 4].fill(0);
        len += 4;

        // O registro completo tem 758 bytes e o pacote leva 744. Montamos inteiro num buffer a
        // parte e copiamos o pedaco -- escrever direto cortaria o campo do meio.
        let mut registro = [0u8; REGISTRO_LEN];
        escreve_registro(&mut registro, &self.personagem);
        buf[len..len + REGISTRO_CRIACAO_LEN]
            .copy_from_slice(&registro[..REGISTRO_CRIACAO_LEN]);
        len += REGISTRO_CRIACAO_LEN;

        len
    }
}

/// Resposta ao pedido de deleção de personagem (cliente 0x05 / SM_DELETE_CHARACTER 0x00C9)
#[derive(Debug, Clone)]
pub struct DeleteCharacter {
    pub character_id: u32,
    pub deletion_time: u32,
}

impl DeleteCharacter {
    pub fn new(character_id: u32, deletion_time: u32) -> Self {
        Self { character_id, deletion_time }
    }
}

impl Serialise for DeleteCharacter {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(DELETE_CHARACTER, buf);

        if self.character_id != 0 {
            to_le_bytes!(len, buf, 0_u32); // status: 0 = sucesso
            to_le_bytes!(len, buf, self.character_id);
            to_le_bytes!(len, buf, self.deletion_time);
        } else {
            to_le_bytes!(len, buf, 0x10_u32); // erro
            to_le_bytes!(len, buf, 0_u32);
            to_le_bytes!(len, buf, 0_u32);
        }

        len
    }
}

/// Place a player character into the game
#[derive(Debug, Clone)]
pub struct PutUser {
    pub character: Character,
    header1: [u8; 35],
    header2: [u8; 24],
    footer1: [u8; 81],
    footer2: [u8; 76],
}
impl PutUser {
    pub fn new(character: &Character) -> Self {
        let header1 = [
            0xA3, 0x86, 0x01, 0x00, 0xA3, 0x86, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x9A, 0x01, 0x40, 0x01, 0x00, 0x00, 0x00, 0x26, 0x01,
            0x04, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x11,
        ];

        let header2 = [
            0x00, 0x00, 0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            // Health Percent
            0x5C, 0x00, 0x00, 0xFF,
        ];

        let footer1 = [
            0xAB, 0xAB, 0xBC, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0xE9, 0x02, 0x0F,
            0x00, 0xCE, 0xB4, 0xCA, 0x00, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x02,
            0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x83,
            0x8F, 0x00, 0x03, 0x00, 0x00, 0x00, 0x83, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x07, 0x04, 0xEF, 0xB3, 0xDA, 0xB2, 0xF0, 0xDF,
            0xEF, 0xBA, 0xF4, 0xCE, 0x00, 0x00, 0xF0, 0xF4, 0xF5, 0xE4, 0x00,
            0x02, 0x66, 0x66, 0x26, 0x3F, 0x00, 0x00, 0x80, 0x3E, 0x00, 0x00,
            0x00, 0x40, 0x00, 0x00,
        ];

        let footer2 = [
            0xD6, 0x06, 0xD6, 0x06, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            // Coords Desination?
            0x92, 0xDA, 0xEB, 0x44, 0xFC, 0x67, 0x2F, 0x44, 0x2D, 0x15, 0x81,
            0x43, // ????
            0x00, 0x40, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00,
        ];

        Self {
            character: character.clone(),
            header1,
            footer1,
            footer2,
            header2,
        }
    }
}
impl Serialise for PutUser {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(PUT_USER, buf);

        len += self.character.location().serialise(&mut buf[len..]);

        to_le_bytes!(len, buf, self.character.id());

        buf[len..len + self.header1.len()].copy_from_slice(&self.header1);
        len += self.header1.len();

        len += self.character.serialise_name_utf16(&mut buf[len..]);

        buf[len..len + self.header2.len()].copy_from_slice(&self.header2);
        len += self.header2.len();

        len += self.character.gear.serialiase_put_user(&mut buf[len..]);

        buf[len..len + self.footer1.len()].copy_from_slice(&self.footer1);
        len += self.footer1.len();

        let move_speed =
            (self.character.stats.move_speed.to_bits() >> 16) as u16;
        buf[len..len + 2].copy_from_slice(&move_speed.to_le_bytes());
        len += 2;

        buf[len..len + self.footer2.len()].copy_from_slice(&self.footer2);
        len += self.footer2.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct CurStatus {
    raw: u8,
}
impl CurStatus {
    pub fn new() -> Self {
        Self { raw: 1 }
    }
}
impl Serialise for CurStatus {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(CUR_STATUS, buf);

        buf[len] = self.raw;
        len += 1;

        len
    }
}
#[derive(Debug, Clone)]
pub struct World {
    unknown1: [u8; 13],
    coord: Coord,
    unknown2: [u8; 17],
}
impl World {
    /// O pacote que poe o jogador no mapa. Na captura, 42 bytes:
    ///
    /// ```text
    /// [u32 mapa][u32 mapa de novo][5 zeros][f32 x][f32 y][f32 z][u8 direcao][15 bytes]
    /// ```
    ///
    /// O mapa aparece duas vezes; nao se sabe se os dois tem o mesmo papel, e a captura nao separa
    /// -- os dois valores sao iguais nela. Os 15 bytes do fim comecam com 0x14 e o resto e zero,
    /// igual na captura e no POC.
    ///
    /// O mapa precisa ser o mesmo que o `S_CHARACTER_LIST` declarou no registro do personagem: e
    /// por aquele que o cliente pre-carrega o cenario. Por isso os dois recebem o mesmo
    /// [`crate::game::mundo::PontoDeEntrada`], escolhido pela raca.
    pub fn new(coord: &Coord, ponto: crate::game::mundo::PontoDeEntrada) -> Self {
        let mut unknown1 = [0u8; 13];
        unknown1[0..4].copy_from_slice(&ponto.mapa.to_le_bytes());
        unknown1[4..8].copy_from_slice(&ponto.mapa.to_le_bytes());

        let mut unknown2 = [0u8; 17];
        unknown2[0] = ponto.direcao;
        unknown2[1] = 0x14;

        Self {
            unknown1,
            coord: *coord,
            unknown2,
        }
    }
}
impl Serialise for World {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WORLD, buf);

        buf[len..len + self.unknown1.len()].copy_from_slice(&self.unknown1);
        len += self.unknown1.len();

        len += self.coord.serialise(&mut buf[len..]);

        buf[len..len + self.unknown2.len()].copy_from_slice(&self.unknown2);
        len += self.unknown2.len();

        len
    }
}

#[derive(Debug, Clone)]
pub struct LoadClientSettings {
    ty: u8,
    raw: Vec<u8>,
}
impl LoadClientSettings {
    pub fn new(ty: u8, raw: Vec<u8>) -> Self {
        Self { raw, ty }
    }
}
impl Serialise for LoadClientSettings {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(LOAD_CLIENT_SETTINGS, buf);

        let body_len = self.raw.len() + size_of::<u32>();
        to_le_bytes!(len, buf, self.ty);
        // Length with padding minus type and itself,
        // this is required, dont know why
        to_le_bytes!(len, buf, 7168 as u16);
        to_le_bytes!(len, buf, body_len as u32);
        copy_bytes!(len, buf, self.raw);

        len
    }
}

#[derive(Debug, Clone)]
pub struct _0102 {
    raw: Vec<u8>,
}
impl _0102 {
    pub fn new() -> Self {
        Self {
            raw: [
                0x24, 0xDD, 0xA1, 0xC5, 0x15, 0xDB, 0xDD, 0x10, 0x0B, 0x0C,
                0xAD, 0x32, 0x9A, 0x31, 0xEC, 0x54, 0xAF, 0x22, 0x47, 0xA5,
                0xC7, 0xC5, 0xA2, 0x92, 0xAA, 0x99, 0x47, 0x1B, 0xB9, 0x92,
                0x73, 0x6B,
            ]
            .to_vec(),
        }
    }
}
impl Serialise for _0102 {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(0102, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone, Copy)]
pub enum MoveData {
    Turn { delta: Coord },
    Stop,
    Continue,
    Direct { dest: Coord },
}

// TODO: Prevent malicious Movement
#[derive(Debug, Clone)]
pub struct MoveNew {
    entity_id: u32,
    location: Coord,
    direction: Direction,
    ty: MoveType,
    data: MoveData,
}
impl MoveNew {
    pub fn new(
        entity_id: u32,
        location: Coord,
        direction: Direction,
        ty: MoveType,
        data: MoveData,
    ) -> Self {
        Self {
            entity_id,
            location,
            direction,
            ty,
            data,
        }
    }
}
impl Serialise for MoveNew {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(MOVE_NEW, buf);

        to_le_bytes!(len, buf, self.entity_id);
        len += self.location.serialise(&mut buf[len..]);
        to_le_bytes!(len, buf, self.direction.bits());
        to_le_bytes!(len, buf, self.ty.bits());

        match &self.data {
            MoveData::Turn { delta } => len += delta.serialise(&mut buf[len..]),
            MoveData::Stop => {}
            MoveData::Continue => {}
            MoveData::Direct { dest } => len += dest.serialise(&mut buf[len..]),
        }

        len
    }
}

#[derive(Debug, Clone)]
pub struct RecipeList {
    raw: Vec<u8>,
}
impl RecipeList {
    pub fn new(raw: Vec<u8>) -> Self {
        Self { raw }
    }
}
impl Serialise for RecipeList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(RECIPE_LIST, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BuddyEntry {
    pub player_id: u32,
    pub name: String,
    pub is_online: bool,
    pub map_id: u32,
    pub level: u8,
    pub class_id: u8,
}

#[derive(Debug, Clone)]
pub struct BuddyList {
    pub buddies: Vec<BuddyEntry>,
}
impl BuddyList {
    pub fn new() -> Self {
        Self { buddies: Vec::new() }
    }
    pub fn from_entries(buddies: Vec<BuddyEntry>) -> Self {
        Self { buddies }
    }
}
impl Serialise for BuddyList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(BUDDY_LIST, buf);
        to_le_bytes!(len, buf, self.buddies.len() as u16);
        for b in &self.buddies {
            to_le_bytes!(len, buf, b.player_id);
            let name_utf16: Vec<u8> = b.name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
            to_le_bytes!(len, buf, name_utf16.len() as u16);
            copy_bytes!(len, buf, name_utf16);
            to_le_bytes!(len, buf, b.is_online as u8);
            to_le_bytes!(len, buf, b.map_id);
            to_le_bytes!(len, buf, b.level);
            to_le_bytes!(len, buf, b.class_id);
        }
        len
    }
}

#[derive(Debug, Clone)]
pub struct AddSkill {
    skills: Vec<Skill>,
}
impl AddSkill {
    pub fn new(skills: Vec<Skill>) -> Self {
        Self { skills }
    }
}
impl Serialise for AddSkill {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ADD_SKILL, buf);

        buf[len] = self.skills.len() as u8;
        len += 1;
        // Unknown
        buf[len] = 0;
        len += 1;
        for skill in &self.skills {
            len += skill.serialise(&mut buf[len..])
        }

        len
    }
}

#[derive(Debug, Clone)]
pub struct LoadInventory {
    /// 0x01 on first inventory message else 0x00
    first: bool,
    items: Vec<RawItem>,
}
impl LoadInventory {
    pub fn new(items: Vec<RawItem>) -> Self {
        Self { items, first: true }
    }
    pub fn start(items: Vec<RawItem>) -> Self {
        Self { items, first: true }
    }
    /// Must be called after the last LoadInventory message is sent
    pub fn end() -> Self {
        Self {
            items: vec![],
            first: false,
        }
    }
}
impl Serialise for LoadInventory {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(LOAD_INVENTORY, buf);

        to_le_bytes!(len, buf, self.first as u8);
        to_le_bytes!(len, buf, 3_u8);
        to_le_bytes!(len, buf, 0_u16);
        to_le_bytes!(len, buf, self.items.len() as u16);

        for item in &self.items {
            len += item.serialise(&mut buf[len..]);
        }

        len
    }
}

#[derive(Debug, Clone)]
pub struct ChangeChannel {
    raw: Vec<u8>,
}
impl ChangeChannel {
    pub fn new(raw: Vec<u8>) -> Self {
        Self { raw }
    }
}
impl Serialise for ChangeChannel {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(CHANGE_CHANNEL, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
/// Contains information on player HP/MP/DP etc
#[derive(Debug, Clone)]
pub struct Status {
    character: Character,
    game_time: u32,
}
impl Status {
    pub fn new(character: &Character, game_time: u32) -> Self {
        Self {
            character: character.clone(),
            game_time,
        }
    }
}
impl Serialise for Status {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let stats = &self.character.stats;

        let mut len = 0;
        len += add_prelude(STATUS, buf);

        to_le_bytes!(len, buf, self.character.id());
        to_le_bytes!(len, buf, self.game_time);
        len += stats.primary.serialise(&mut buf[len..]);

        // Resistances??
        let unknown = [
            // Water Resist
            0x00, 0x00, // Wind Resistant
            0x00, 0x00, // Earth
            0x00, 0x00, // Fire
            0x00, 0x00, // ???
            0x00, 0x00, // ???
            0x00, 0x00,
        ];
        copy_bytes!(len, buf, unknown);
        to_le_bytes!(len, buf, stats.level);
        copy_bytes!(len, buf, [0u8; 6]);
        to_le_bytes!(len, buf, stats.exp_to_level);
        copy_bytes!(len, buf, [0u8; 8]);
        to_le_bytes!(len, buf, stats.exp);
        copy_bytes!(len, buf, [0u8; 4]);
        to_le_bytes!(len, buf, stats.hp.max());
        to_le_bytes!(len, buf, stats.hp.current());
        to_le_bytes!(len, buf, stats.mp.max());
        to_le_bytes!(len, buf, stats.mp.current());
        to_le_bytes!(len, buf, stats.dp.max());
        to_le_bytes!(len, buf, stats.dp.current());
        copy_bytes!(len, buf, [0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
        to_le_bytes!(len, buf, stats.flight_time_max);
        to_le_bytes!(len, buf, stats.flight_time_current);
        copy_bytes!(len, buf, [0u8; 2]);
        to_le_bytes!(len, buf, stats.secondary.main_hand_attack);
        to_le_bytes!(len, buf, stats.secondary.off_hand_attack);
        to_le_bytes!(len, buf, stats.secondary.physical_defence);
        copy_bytes!(len, buf, [0xDA, 0x00]);
        to_le_bytes!(len, buf, stats.secondary.magic_resist);
        copy_bytes!(len, buf, [0x00, 0x00, 0xC0, 0x3F]);
        to_le_bytes!(len, buf, stats.attack_speed);
        to_le_bytes!(len, buf, stats.secondary.evasion);
        to_le_bytes!(len, buf, stats.secondary.parry);
        to_le_bytes!(len, buf, stats.secondary.block);
        to_le_bytes!(len, buf, stats.secondary.main_hand_crit);
        to_le_bytes!(len, buf, stats.secondary.off_hand_crit);
        to_le_bytes!(len, buf, stats.secondary.main_hand_accuracy);
        to_le_bytes!(len, buf, stats.secondary.off_hand_accuracy);
        copy_bytes!(len, buf, [0x02, 0x02]);
        to_le_bytes!(len, buf, stats.secondary.magic_accuracy);
        to_le_bytes!(len, buf, stats.secondary.crit_spell);
        copy_bytes!(len, buf, [0x32, 0x00]);
        to_le_bytes!(len, buf, stats.cast_speed);
        to_le_bytes!(len, buf, stats.secondary.unknown7);
        to_le_bytes!(len, buf, stats.secondary.magic_boost);
        to_le_bytes!(len, buf, stats.secondary.healing_boost);
        to_le_bytes!(len, buf, stats.secondary.crit_strike_resist);
        to_le_bytes!(len, buf, stats.secondary.spell_resist);
        to_le_bytes!(len, buf, stats.secondary.strike_fortitude);
        to_le_bytes!(len, buf, stats.secondary.spell_fortitude);
        let unknown = [
            0x58, 0x40, 0x36, 0x00, 0x00, 0x00, 0x27, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Combat talent
            0xCB, 0x07, 0x00, 0x00,
        ];
        copy_bytes!(len, buf, unknown);
        // Modified stats?
        len += self.character.stats.primary.serialise(&mut buf[len..]);
        copy_bytes!(len, buf, [0u8; 12]);
        to_le_bytes!(len, buf, stats.hp.base());
        to_le_bytes!(len, buf, stats.mp.base());
        to_le_bytes!(len, buf, stats.dp.current());
        copy_bytes!(len, buf, [0x00, 0x00, 0x64, 0x00, 0x00, 0x00]);
        to_le_bytes!(len, buf, stats.flight_time_max);
        to_le_bytes!(len, buf, stats.secondary.main_hand_attack);
        to_le_bytes!(len, buf, stats.secondary.off_hand_attack);
        to_le_bytes!(len, buf, stats.secondary.unknown1);
        to_le_bytes!(len, buf, stats.secondary.physical_defence);
        to_le_bytes!(len, buf, stats.secondary.magic_resist);
        to_le_bytes!(len, buf, stats.secondary.unknown2);
        to_le_bytes!(len, buf, stats.secondary.unknown3);
        to_le_bytes!(len, buf, stats.secondary.unknown4);
        to_le_bytes!(len, buf, stats.secondary.evasion);
        to_le_bytes!(len, buf, stats.secondary.parry);
        to_le_bytes!(len, buf, stats.secondary.block);
        to_le_bytes!(len, buf, stats.secondary.main_hand_crit);
        to_le_bytes!(len, buf, stats.secondary.off_hand_crit);
        to_le_bytes!(len, buf, stats.secondary.crit_spell);
        to_le_bytes!(len, buf, stats.secondary.unknown5);
        to_le_bytes!(len, buf, stats.secondary.main_hand_accuracy);
        to_le_bytes!(len, buf, stats.secondary.off_hand_accuracy);
        to_le_bytes!(len, buf, stats.secondary.unknown6);
        to_le_bytes!(len, buf, stats.secondary.magic_accuracy);
        to_le_bytes!(len, buf, stats.secondary.unknown7);
        to_le_bytes!(len, buf, stats.secondary.magic_boost);
        to_le_bytes!(len, buf, stats.secondary.healing_boost);
        to_le_bytes!(len, buf, stats.secondary.crit_strike_resist);
        to_le_bytes!(len, buf, stats.secondary.spell_resist);
        to_le_bytes!(len, buf, stats.secondary.strike_fortitude);
        to_le_bytes!(len, buf, stats.secondary.spell_fortitude);

        len
    }
}
#[derive(Debug, Clone)]
pub struct _0151 {
    raw: [u8; 6],
}
impl _0151 {
    pub fn new() -> Self {
        Self { raw: [0u8; 6] }
    }
}
impl Serialise for _0151 {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(0151, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct WorldInfo {
    raw: [u8; 11],
}
impl WorldInfo {
    pub fn new() -> Self {
        Self {
            raw: [
                0x09, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
                0x00,
            ],
        }
    }
}
impl Serialise for WorldInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WORLD_INFO, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

/// Subscription information
#[derive(Debug, Clone)]
pub struct GamepassInfo {
    raw: Vec<u8>,
}
impl GamepassInfo {
    pub fn new(raw: Vec<u8>) -> Self {
        Self { raw }
    }
}
impl Serialise for GamepassInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GAMEPASS_INFO, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

/// Sends a message to the players chat box
/// TODO: Implement params
#[derive(Debug, Clone)]
pub struct MessageCode {
    message_id: u32,
    params_len: u16,
}
impl MessageCode {
    pub fn new(message_id: u32) -> Self {
        Self {
            message_id,
            params_len: 0,
        }
    }
}
impl Serialise for MessageCode {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(MESSAGE_CODE, buf);

        to_le_bytes!(len, buf, 0x19 as u8);
        copy_bytes!(len, buf, [0u8; 5]);
        to_le_bytes!(len, buf, self.message_id);
        to_le_bytes!(len, buf, self.params_len);

        len
    }
}
/// Efeito de status anormal (buff/debuff)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AbnormalEffect {
    pub skill_id: u32,
    pub remaining_ms: u32,
    pub stack: u8,
}

impl AbnormalEffect {
    pub fn new(skill_id: u32, remaining_ms: u32, stack: u8) -> Self {
        Self {
            skill_id,
            remaining_ms,
            stack,
        }
    }
}

impl Serialise for AbnormalEffect {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        to_le_bytes!(len, buf, self.skill_id);
        to_le_bytes!(len, buf, self.remaining_ms);
        to_le_bytes!(len, buf, self.stack);
        len
    }
}

/// S_ABNORMAL_STATUS (0x031) — buffs/debuffs no jogador LOCAL
#[derive(Debug, Clone)]
pub struct AbnormalStatus {
    pub entity_id: u32,
    pub effects: Vec<AbnormalEffect>,
}

impl AbnormalStatus {
    pub fn new() -> Self {
        Self {
            entity_id: 0,
            effects: Vec::new(),
        }
    }

    pub fn with_effects(entity_id: u32, effects: Vec<AbnormalEffect>) -> Self {
        Self { entity_id, effects }
    }
}

impl Serialise for AbnormalStatus {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ABNORMAL_STATUS, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.effects.len() as u32);
        for eff in &self.effects {
            len += eff.serialise(&mut buf[len..]);
        }
        len
    }
}

/// S_ABNORMAL_STATUS_OTHER (0x032) — buffs/debuffs em OUTROS
#[derive(Debug, Clone)]
pub struct AbnormalStatusOther {
    pub entity_id: u32,
    pub effects: Vec<AbnormalEffect>,
}

impl AbnormalStatusOther {
    pub fn new(entity_id: u32) -> Self {
        Self {
            entity_id,
            effects: Vec::new(),
        }
    }

    pub fn with_effects(entity_id: u32, effects: Vec<AbnormalEffect>) -> Self {
        Self { entity_id, effects }
    }

    pub fn dead(entity_id: u32) -> Self {
        Self {
            entity_id,
            effects: Vec::new(),
        }
    }
}

impl Serialise for AbnormalStatusOther {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ABNORMAL_STATUS_OTHER, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.effects.len() as u32);
        for eff in &self.effects {
            len += eff.serialise(&mut buf[len..]);
        }
        len
    }
}

#[derive(Debug, Clone)]
pub struct Time {
    game_time: u32,
}
impl Time {
    pub fn new(game_time: u32) -> Self {
        Self { game_time }
    }
}
impl Serialise for Time {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(TIME, buf);

        buf[len..len + 4].copy_from_slice(&self.game_time.to_le_bytes());
        len += 4;

        len
    }
}
#[derive(Debug, Clone)]
pub struct InvincibleTime {
    raw: [u8; 4],
}
impl InvincibleTime {
    pub fn start() -> Self {
        Self {
            raw: [0x60, 0xEA, 0x00, 0x00],
        }
    }
    pub fn finish() -> Self {
        Self {
            raw: [0x00, 0x00, 0x00, 0x00],
        }
    }
}
impl Serialise for InvincibleTime {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(INVINCIBLE_TIME, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct InvisibleLevel {
    character_id: u32,
    raw: [u8; 3],
}
impl InvisibleLevel {
    pub fn start(character_id: u32) -> Self {
        Self {
            raw: [0x40, 0x00, 0x01],
            character_id,
        }
    }
    pub fn finish(character_id: u32) -> Self {
        Self {
            raw: [0x00, 0x00, 0x00],
            character_id,
        }
    }
}
impl Serialise for InvisibleLevel {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(INVISIBLE_LEVEL, buf);

        to_le_bytes!(len, buf, self.character_id);
        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct WorldSceneStatus {
    pub scene_id: u32,
    pub status: u8,
    pub raw: [u8; 4],
}
impl WorldSceneStatus {
    pub fn new() -> Self {
        Self {
            scene_id: 0,
            status: 1,
            raw: [0x00, 0x00, 0x00, 0x00],
        }
    }
    pub fn scene(scene_id: u32, status: u8) -> Self {
        Self {
            scene_id,
            status,
            raw: [0x00, 0x00, 0x00, 0x00],
        }
    }
}
impl Serialise for WorldSceneStatus {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WORLD_SCENE_STATUS, buf);

        to_le_bytes!(len, buf, self.status);
        to_le_bytes!(len, buf, self.scene_id);
        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct ResultPassport {
    unknown1: [u8; 8],
    character_id: u32,
    unknown2: [u8; 12],
}
impl ResultPassport {
    pub fn new(character_id: u32) -> Self {
        Self {
            unknown1: [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            character_id,
            unknown2: [
                0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00,
            ],
        }
    }
}
impl Serialise for ResultPassport {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(RESULT_PASSPORT, buf);

        buf[len..len + self.unknown1.len()].copy_from_slice(&self.unknown1);
        len += self.unknown1.len();

        to_le_bytes!(len, buf, self.character_id);

        buf[len..len + self.unknown2.len()].copy_from_slice(&self.unknown2);
        len += self.unknown2.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct Weather {
    raw: [u8; 4],
}
impl Weather {
    pub fn new() -> Self {
        Self {
            raw: [0x00, 0x02, 0x00, 0x00],
        }
    }
}
impl Serialise for Weather {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WEATHER, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct SignClient {
    raw: [u8; 68],
}
impl SignClient {
    pub fn new() -> Self {
        Self {
            raw: [
                0x40, 0x00, 0x00, 0x00, 0x2A, 0xCA, 0x3A, 0x34, 0x7C, 0xA1,
                0xA1, 0xAE, 0x02, 0x67, 0xFE, 0x23, 0x4A, 0x29, 0xB4, 0x32,
                0xCF, 0xF8, 0x4C, 0x44, 0x4D, 0x61, 0x9C, 0xAD, 0x57, 0x31,
                0xC6, 0xA9, 0x78, 0x75, 0x16, 0x55, 0x1B, 0xB5, 0x83, 0x58,
                0x43, 0x26, 0x42, 0x22, 0xA0, 0x48, 0xF3, 0xEF, 0x76, 0xB5,
                0x9D, 0x69, 0x9B, 0x93, 0x6C, 0xC3, 0xD8, 0x46, 0xA1, 0xC2,
                0xB8, 0xA6, 0x72, 0x32, 0x6C, 0xE6, 0xBD, 0x92,
            ],
        }
    }
}
impl Serialise for SignClient {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SIGN_CLIENT, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct Title {
    raw: [u8; 3],
}
impl Title {
    pub fn new() -> Self {
        Self {
            raw: [0x01, 0x34, 0x00],
        }
    }
}
impl Serialise for Title {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(TITLE, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct LoadItemCooltime {
    raw: [u8; 2],
}
impl LoadItemCooltime {
    pub fn new() -> Self {
        Self { raw: [0x00, 0x00] }
    }
}
impl Serialise for LoadItemCooltime {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(LOAD_ITEM_COOLTIME, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}
#[derive(Debug, Clone)]
pub struct CustomAnim {
    raw: [u8; 3],
}
impl CustomAnim {
    pub fn new() -> Self {
        Self {
            raw: [0x01, 0x00, 0x00],
        }
    }
}
impl Serialise for CustomAnim {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(CUSTOM_ANIM, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

/// Place an npc into the game
#[derive(Debug, Clone)]
pub struct PutNpc {
    location: Coord,
    /// Unique ID of specific npc
    entity_id: u32,
    /// Numericos, e nao os enums de antes: a tabela de spawns extraida da captura tem 530 NPCs
    /// distintos, e os enums cobriam quatro.
    status_bar_id: u32,
    appearence_id: u32,
    ty: npc::Type,
    state: npc::State,
    rotation: u8,
    /// Name is an Id that client references to find string of name
    name: u32,
    current_hp_pct: u8,
    current_hp: i32,
    level: u16,
    destination: Coord,
}

impl PutNpc {
    pub fn new(entity: &Entity) -> Self {
        Self {
            location: *entity.location(),
            entity_id: entity.id(),
            status_bar_id: entity.npc_id(),
            appearence_id: entity.npc_id(),
            ty: npc::Type::Aggressive,
            state: npc::State::Alive,
            rotation: 60,
            name: entity.npc_name(),
            current_hp_pct: entity.hp.percent(),
            current_hp: entity.hp.current(),
            level: entity.level(),
            destination: *entity.location(),
        }
    }
}
impl Serialise for PutNpc {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(PUT_NPC, buf);

        len += self.location.serialise(&mut buf[len..]);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.status_bar_id as u32);
        to_le_bytes!(len, buf, self.appearence_id as u32);
        to_le_bytes!(len, buf, self.ty as u8);
        to_le_bytes!(len, buf, self.state as u16);
        to_le_bytes!(len, buf, self.rotation);
        to_le_bytes!(len, buf, self.name as u32);
        copy_bytes!(len, buf, [0u8; 17]);
        to_le_bytes!(len, buf, self.current_hp_pct);
        to_le_bytes!(len, buf, self.current_hp);
        to_le_bytes!(len, buf, self.level as u8);

        let unknown = [
            0x00, 0x00, 0x1F, 0x85, 0xCB, 0x3F, 0x1F, 0x85, 0x2B, 0x40, 0xE7,
            0xFB, 0xA9, 0x3F, 0x5E, 0x08, 0x5E, 0x08, 0x00,
        ];
        copy_bytes!(len, buf, unknown);

        len += self.destination.serialise(&mut buf[len..]);
        let unknown = [
            // MoveType???
            0xE4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ];
        copy_bytes!(len, buf, unknown);

        len
    }
}

#[derive(Debug, Clone)]
pub struct AskQuitResult {
    raw: [u8; 9],
}
impl AskQuitResult {
    pub fn new() -> Self {
        Self {
            raw: [0x01, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF],
        }
    }
}
impl Serialise for AskQuitResult {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ASK_QUIT_RESULT, buf);

        buf[len..len + self.raw.len()].copy_from_slice(&self.raw);
        len += self.raw.len();

        len
    }
}

/// 4 bytes - ID of entity doing action
/// 1 byte - Action ID
/// 1 byte - 0x01
/// 3 bytes - 0x00, 0x00, 0x00
/// 2 bytes - entity speed (f32 bit float but we only serialise 16 bits)
/// OPTIONAL
/// 4 bytes - target id
/// 1 byte - Emote type
/// 2 bytes - 0x00 0x01
#[derive(Debug, Clone)]
pub struct Action {
    entity_id: u32,
    action: ActionType,
    move_speed: f32,
    target_id: u32,
}
impl Action {
    pub fn new(
        entity_id: u32,
        action: ActionType,
        move_speed: f32,
        target_id: u32,
    ) -> Self {
        Self {
            entity_id,
            action,
            move_speed,
            target_id,
        }
    }
}
impl Serialise for Action {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ACTION, buf);

        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, u8::from(self.action));

        // TODO: Unknown
        copy_bytes!(len, buf, [0x00, 0x00, 0x00, 0x00]);

        let move_speed = (self.move_speed.to_bits() >> 16) as u16;
        to_le_bytes!(len, buf, move_speed);

        to_le_bytes!(len, buf, self.target_id);
        match self.action {
            ActionType::StartEmote(emote) => {
                to_le_bytes!(len, buf, u8::from(emote));
                copy_bytes!(len, buf, [0x00, 0x01]);
            }
            _ => {}
        }

        len
    }
}

#[derive(Debug, Clone)]
pub struct Attack {
    attacker_id: u32,
    sequence: u8,
    target_id: u32,
    target_hp_pct: u8,
    attacker_hp_pct: u8,
    hits: Vec<Hit>,
}

impl Attack {
    pub fn new(
        target_id: u32,
        attacker_id: u32,
        sequence: u8,
        hits: Vec<Hit>,
    ) -> Self {
        Self {
            attacker_id,
            sequence,
            target_id,
            target_hp_pct: 0,
            attacker_hp_pct: 0,
            hits,
        }
    }
}

impl Serialise for Attack {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ATTACK, buf);

        to_le_bytes!(len, buf, self.attacker_id);
        to_le_bytes!(len, buf, self.sequence);
        copy_bytes!(len, buf, [0u8; 4]);
        to_le_bytes!(len, buf, self.target_id);
        to_le_bytes!(len, buf, self.target_hp_pct);
        to_le_bytes!(len, buf, self.attacker_hp_pct);
        copy_bytes!(len, buf, [0u8; 4]);
        to_le_bytes!(len, buf, self.hits.len() as u8);

        for hit in &self.hits {
            len += hit.serialise(&mut buf[len..]);
        }

        len
    }
}

#[derive(Debug, Clone)]
pub struct Loot {
    /// Who recieved the loot
    entity_id: u32,
    status: u8,
}

impl Loot {
    pub fn new(entity_id: u32, status: u8) -> Self {
        Self { entity_id, status }
    }
}

impl Serialise for Loot {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(LOOT, buf);

        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.status);

        len
    }
}
#[derive(Debug, Clone)]
pub struct LootItemlist {
    entity_id: u32,
    loot: Vec<LootItem>,
}

impl LootItemlist {
    pub fn new(entity_id: u32, loot: Vec<LootItem>) -> Self {
        Self { entity_id, loot }
    }
}

impl Serialise for LootItemlist {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(LOOT_ITEMLIST, buf);

        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.loot.len() as u16);
        for (i, loot) in self.loot.iter().enumerate() {
            to_le_bytes!(len, buf, i as u32);
            len += loot.serialise(&mut buf[len..]);
            // TODO: Untradable?
            to_le_bytes!(len, buf, 0u16);
        }
        len
    }
}

#[derive(Debug, Clone)]
pub struct ChangeItemDesc {}

impl ChangeItemDesc {
    pub fn new() -> Self {
        Self {}
    }
}

impl Serialise for ChangeItemDesc {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(CHANGE_ITEM_DESC, buf);

        copy_bytes!(
            len,
            buf,
            [
                0xC5, 0xA3, 0x6B, 0xC7, 0x24, 0x00, //foo
                0x83, 0x80, 0x17, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x3E,
                0x63, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x19, 0x00, 0x00, 0x00, 0x00
            ]
        );

        len
    }
}

/// When you target an entity this updates their status bar
#[derive(Debug, Clone)]
pub struct TargetInfo {
    target_id: u32,
    level: u16,
    max_hp: i32,
    hp: i32,
}
impl TargetInfo {
    pub fn new(target_id: u32, level: u16, hp: i32, max_hp: i32) -> Self {
        Self {
            target_id,
            level,
            max_hp,
            hp,
        }
    }
}
impl Serialise for TargetInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(TARGET_INFO, buf);

        to_le_bytes!(len, buf, self.target_id);
        to_le_bytes!(len, buf, self.level);
        to_le_bytes!(len, buf, self.max_hp);
        to_le_bytes!(len, buf, self.hp);

        len
    }
}

#[derive(Debug, Clone)]
pub struct NpcChangedTarget {
    npc_id: u32,
    target_id: u32,
    _unk: u8,
}
impl NpcChangedTarget {
    pub fn new(target_id: u32, npc_id: u32) -> Self {
        Self {
            target_id,
            npc_id,
            // TODO: What is this?
            _unk: 0x35,
        }
    }
}
impl Serialise for NpcChangedTarget {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(NPC_CHANGED_TARGET, buf);

        to_le_bytes!(len, buf, self.npc_id);
        to_le_bytes!(len, buf, self.target_id);
        to_le_bytes!(len, buf, self._unk);

        len
    }
}

#[derive(Debug, Clone)]
pub struct UseSkill {
    character_id: u32,
    skill_id: u16,
    skill_level: u16,
    target_id: u32,
    unknown: [u8; 8],
}
impl UseSkill {
    pub fn new(
        character_id: u32,
        skill_id: u16,
        skill_level: u16,
        target_id: u32,
    ) -> Self {
        Self {
            character_id,
            skill_id,
            skill_level,
            target_id,
            // 0x3F80 is 1.0???
            unknown: [0, 0, 0, 0, 0, 0x80, 0x3F, 0],
        }
    }
}
impl Serialise for UseSkill {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(USE_SKILL, buf);

        to_le_bytes!(len, buf, self.character_id);
        to_le_bytes!(len, buf, self.skill_id);
        to_le_bytes!(len, buf, self.skill_level);
        to_le_bytes!(len, buf, self.target_id);
        buf[len..len + self.unknown.len()].copy_from_slice(&self.unknown);
        len += self.unknown.len();

        len
    }
}

/// Efeito aplicado por habilidade (dano, cura, debuff)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkillEffect {
    pub target_id: u32,
    pub damage: i32,     // negativo = dano, positivo = cura
    pub damage_type: u8, // 0=físico, 1=mágico, 2=true
    pub is_critical: u8,
}

impl SkillEffect {
    pub fn new(target_id: u32, damage: i32, damage_type: u8, is_critical: u8) -> Self {
        Self {
            target_id,
            damage,
            damage_type,
            is_critical,
        }
    }
}

/// S_SKILL_SUCCEDED (0x02B) — servidor confirma execução de habilidade
#[derive(Debug, Clone)]
pub struct SkillSucceded {
    pub caster_id: u32,
    pub target_id: u32,
    pub skill_id: u32,
    pub skill_level: u8,
    pub effects: Vec<SkillEffect>,
}

impl SkillSucceded {
    pub fn new(
        caster_id: u32,
        target_id: u32,
        skill_id: u32,
        skill_level: u8,
        effects: Vec<SkillEffect>,
    ) -> Self {
        Self {
            caster_id,
            target_id,
            skill_id,
            skill_level,
            effects,
        }
    }
}

impl Serialise for SkillSucceded {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SKILL_SUCCEDED, buf);
        to_le_bytes!(len, buf, self.caster_id);
        to_le_bytes!(len, buf, self.target_id);
        to_le_bytes!(len, buf, self.skill_id);
        to_le_bytes!(len, buf, self.skill_level);
        to_le_bytes!(len, buf, self.effects.len() as u32);
        for eff in &self.effects {
            to_le_bytes!(len, buf, eff.target_id);
            to_le_bytes!(len, buf, eff.damage);
            to_le_bytes!(len, buf, eff.damage_type);
            to_le_bytes!(len, buf, eff.is_critical);
        }
        len
    }
}

/// S_SKILL_PENALTY_STATUS_OTHER (0x0D8) — penalidade e cooldown de habilidade
#[derive(Debug, Clone)]
pub struct SkillPenaltyStatusOther {
    pub entity_id: u32,
    pub skill_id: u32,
    pub cooldown_ms: u32,
}

impl SkillPenaltyStatusOther {
    pub fn new(entity_id: u32, skill_id: u32, cooldown_ms: u32) -> Self {
        Self {
            entity_id,
            skill_id,
            cooldown_ms,
        }
    }
}

impl Serialise for SkillPenaltyStatusOther {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(SKILL_PENALTY_STATUS_OTHER, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.skill_id);
        to_le_bytes!(len, buf, self.cooldown_ms);
        len
    }
}

/// S_STATUPDATE_HP (0x03) — HP do jogador local
#[derive(Debug, Clone)]
pub struct HitPoint {
    pub hp_current: u32,
    pub hp_max: u32,
}

impl HitPoint {
    pub fn new(hp_current: u32, hp_max: u32) -> Self {
        Self { hp_current, hp_max }
    }
}

impl Serialise for HitPoint {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(HIT_POINT, buf);
        to_le_bytes!(len, buf, self.hp_current);
        to_le_bytes!(len, buf, self.hp_max);
        len
    }
}

/// S_STATUPDATE_MP (0x04) — MP do jogador local
#[derive(Debug, Clone)]
pub struct HitPointMp {
    pub mp_current: u32,
    pub mp_max: u32,
}

impl HitPointMp {
    pub fn new(mp_current: u32, mp_max: u32) -> Self {
        Self { mp_current, mp_max }
    }
}

impl Serialise for HitPointMp {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(HIT_POINT_MP, buf);
        to_le_bytes!(len, buf, self.mp_current);
        to_le_bytes!(len, buf, self.mp_max);
        len
    }
}

/// S_STATUPDATE_DP (0x06) — DP do jogador local
#[derive(Debug, Clone)]
pub struct HitPointDp {
    pub dp_current: u32,
    pub dp_max: u32,
}

impl HitPointDp {
    pub fn new(dp_current: u32, dp_max: u32) -> Self {
        Self { dp_current, dp_max }
    }
}

impl Serialise for HitPointDp {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(HIT_POINT_DP, buf);
        to_le_bytes!(len, buf, self.dp_current);
        to_le_bytes!(len, buf, self.dp_max);
        len
    }
}

/// S_ATTACK_STATUS (0x05) — HP do alvo após hit
#[derive(Debug, Clone)]
pub struct HitPointOther {
    pub entity_id: u32,
    pub damage: i32,
    pub hp_current: u32,
    pub hp_max: u32,
    pub damage_type: u8,
    pub is_critical: u8,
}

impl HitPointOther {
    pub fn new(
        entity_id: u32,
        damage: i32,
        hp_current: u32,
        hp_max: u32,
        damage_type: u8,
        is_critical: u8,
    ) -> Self {
        Self {
            entity_id,
            damage,
            hp_current,
            hp_max,
            damage_type,
            is_critical,
        }
    }
}

impl Serialise for HitPointOther {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(HIT_POINT_OTHER, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.damage);
        to_le_bytes!(len, buf, self.hp_current);
        to_le_bytes!(len, buf, self.hp_max);
        to_le_bytes!(len, buf, self.damage_type);
        to_le_bytes!(len, buf, self.is_critical);
        len
    }
}

/// TODO: Create real authentication
#[derive(Debug, Clone)]
pub struct ReconnectKey {
    key: [u8; 4],
}
impl ReconnectKey {
    pub fn new() -> Self {
        Self { key: [0u8; 4] }
    }
}
impl Serialise for ReconnectKey {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(RECONNECT_KEY, buf);

        buf[len] = 0;
        len += 1;
        buf[len..len + self.key.len()].copy_from_slice(&self.key);
        len += self.key.len();

        len
    }
}

/// Not sure if this is needed, think it is only called once
#[derive(Debug, Clone)]
pub struct Alive {
    payload: [u8; 2],
}

impl Alive {
    pub fn new() -> Self {
        Self { payload: [0u8; 2] }
    }
}
impl Serialise for Alive {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ALIVE, buf);
        buf[len..len + self.payload.len()].copy_from_slice(&self.payload);
        len += self.payload.len();
        len
    }
}

/// Janela HTML de diálogo com NPC (Opcode 0x3C)
#[derive(Debug, Clone)]
pub struct DialogWindow {
    pub target_id: u32,
    pub dialog_id: u32,
    pub quest_id: u32,
}

impl DialogWindow {
    pub fn new(target_id: u32, dialog_id: u32, quest_id: u32) -> Self {
        Self {
            target_id,
            dialog_id,
            quest_id,
        }
    }
}

impl Serialise for DialogWindow {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(DIALOG_WINDOW, buf);
        to_le_bytes!(len, buf, self.target_id);
        to_le_bytes!(len, buf, self.dialog_id);
        to_le_bytes!(len, buf, self.quest_id);
        len
    }
}

/// Teleporte e posicionamento no mundo (Opcode 0x0014, 22 bytes de payload).
///
/// Layout oficial capturado:
/// - [u8 tipo]         — 0x00=portal NPC, 0x01=zona, 0x02=instância
/// - [u32 map_id]      — ex: 110070000 (Kaisinel Academy), 120070000 (Asmodae Intro)
/// - [u32 instance_id] — ex: 0 (mundo aberto)
/// - [f32 x]
/// - [f32 y]
/// - [f32 z]
/// - [u8 heading]      — direção do personagem (0–120)
#[derive(Debug, Clone)]
pub struct RequestTeleport {
    pub tipo: u8,
    pub map_id: u32,
    pub instance_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub heading: u8,
}

impl RequestTeleport {
    pub fn new(
        tipo: u8,
        map_id: u32,
        instance_id: u32,
        x: f32,
        y: f32,
        z: f32,
        heading: u8,
    ) -> Self {
        Self {
            tipo,
            map_id,
            instance_id,
            x,
            y,
            z,
            heading,
        }
    }
}

impl Serialise for RequestTeleport {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(REQUEST_TELEPORT, buf);

        to_le_bytes!(len, buf, self.tipo);
        to_le_bytes!(len, buf, self.map_id);
        to_le_bytes!(len, buf, self.instance_id);
        to_le_bytes!(len, buf, self.x);
        to_le_bytes!(len, buf, self.y);
        to_le_bytes!(len, buf, self.z);
        to_le_bytes!(len, buf, self.heading);

        len
    }
}

/// Confirmação de estado na corrente de vento (Opcode 0x00A3).
///
/// Layout oficial (13 bytes):
/// - [u32 entity_id]
/// - [u32 windstream_id]
/// - [u8 state]       — 0=fora, 1=dentro, 2=saindo
/// - [f32 speed]       — ex: 22.0
#[derive(Debug, Clone)]
pub struct WindStateInfo {
    pub entity_id: u32,
    pub windstream_id: u32,
    pub state: u8,
    pub speed: f32,
}

impl WindStateInfo {
    pub fn new(entity_id: u32, windstream_id: u32, state: u8, speed: f32) -> Self {
        Self {
            entity_id,
            windstream_id,
            state,
            speed,
        }
    }
}

impl Serialise for WindStateInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WIND_STATE_INFO, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.windstream_id);
        to_le_bytes!(len, buf, self.state);
        to_le_bytes!(len, buf, self.speed);
        len
    }
}

/// Rota pré-calculada de voo em corrente de vento (Opcode 0x00A2).
///
/// Layout oficial:
/// - [u32 entity_id]
/// - [u32 windstream_id]
/// - [u16 waypoint_count]
/// - for each waypoint: [f32 x][f32 y][f32 z]
/// - [f32 duration_ms]
#[derive(Debug, Clone)]
pub struct WindPathResult {
    pub entity_id: u32,
    pub windstream_id: u32,
    pub waypoints: Vec<(f32, f32, f32)>,
    pub duration_ms: f32,
}

impl WindPathResult {
    pub fn new(
        entity_id: u32,
        windstream_id: u32,
        waypoints: Vec<(f32, f32, f32)>,
        duration_ms: f32,
    ) -> Self {
        Self {
            entity_id,
            windstream_id,
            waypoints,
            duration_ms,
        }
    }
}

impl Serialise for WindPathResult {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(WIND_PATH_RESULT, buf);
        to_le_bytes!(len, buf, self.entity_id);
        to_le_bytes!(len, buf, self.windstream_id);
        let count = self.waypoints.len() as u16;
        to_le_bytes!(len, buf, count);
        for wp in &self.waypoints {
            to_le_bytes!(len, buf, wp.0);
            to_le_bytes!(len, buf, wp.1);
            to_le_bytes!(len, buf, wp.2);
        }
        to_le_bytes!(len, buf, self.duration_ms);
        len
    }
}

/// SM_STATUPDATE_EXP (0x08) — Atualização de EXP do jogador
#[derive(Debug, Clone)]
pub struct ExpUpdate {
    pub exp: u64,
    pub exp_required: u64,
}

impl ExpUpdate {
    pub fn new(exp: u64, exp_required: u64) -> Self {
        Self { exp, exp_required }
    }
}

impl Serialise for ExpUpdate {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(EXP_UPDATE, buf);
        to_le_bytes!(len, buf, self.exp);
        to_le_bytes!(len, buf, self.exp_required);
        len
    }
}

/// SM_QUEST_LIST (0x47) — Lista de missões ativas/concluídas do personagem
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuestEntry {
    pub quest_id: u32,
    pub status: u8,
    pub flags: u32,
    pub vars: [u32; 4],
    pub start_timestamp: u32,
}

impl QuestEntry {
    pub fn new(quest_id: u32, status: u8, flags: u32, vars: [u32; 4], start_timestamp: u32) -> Self {
        Self {
            quest_id,
            status,
            flags,
            vars,
            start_timestamp,
        }
    }
}

#[derive(Debug, Clone)]
pub struct QuestList {
    pub quests: Vec<QuestEntry>,
}

impl QuestList {
    pub fn new(quests: Vec<QuestEntry>) -> Self {
        Self { quests }
    }
}

impl Serialise for QuestList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(QUEST_LIST, buf);
        let count = self.quests.len() as u16;
        to_le_bytes!(len, buf, count);
        for q in &self.quests {
            to_le_bytes!(len, buf, q.quest_id);
            to_le_bytes!(len, buf, q.status);
            to_le_bytes!(len, buf, q.flags);
            for v in &q.vars {
                to_le_bytes!(len, buf, *v);
            }
            to_le_bytes!(len, buf, q.start_timestamp);
        }
        len
    }
}

/// SM_STORE_SALE_INFO (0xFD) — Confirmação e resultado de compra/venda em loja NPC
#[derive(Debug, Clone)]
pub struct StoreSaleInfo {
    pub result: u8,
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub price_paid: u64,
    pub kinah_current: u64,
}

impl StoreSaleInfo {
    pub fn new(
        result: u8,
        item_unique_id: u32,
        item_template_id: u32,
        quantity: u32,
        price_paid: u64,
        kinah_current: u64,
    ) -> Self {
        Self {
            result,
            item_unique_id,
            item_template_id,
            quantity,
            price_paid,
            kinah_current,
        }
    }
}

impl Serialise for StoreSaleInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(STORE_SALE_INFO, buf);
        to_le_bytes!(len, buf, self.result);
        to_le_bytes!(len, buf, self.item_unique_id);
        to_le_bytes!(len, buf, self.item_template_id);
        to_le_bytes!(len, buf, self.quantity);
        to_le_bytes!(len, buf, self.price_paid);
        to_le_bytes!(len, buf, self.kinah_current);
        len
    }
}

/// SM_USER_SELL_HISTORY_LIST (0xA6) — Lista de Buyback
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SellHistoryEntry {
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub buyback_price: u64,
    pub sell_timestamp: u64,
}

impl SellHistoryEntry {
    pub fn new(
        item_unique_id: u32,
        item_template_id: u32,
        quantity: u32,
        buyback_price: u64,
        sell_timestamp: u64,
    ) -> Self {
        Self {
            item_unique_id,
            item_template_id,
            quantity,
            buyback_price,
            sell_timestamp,
        }
    }
}

#[derive(Debug, Clone)]
pub struct UserSellHistoryList {
    pub entries: Vec<SellHistoryEntry>,
}

impl UserSellHistoryList {
    pub fn new(entries: Vec<SellHistoryEntry>) -> Self {
        Self { entries }
    }
}

impl Serialise for UserSellHistoryList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(USER_SELL_HISTORY_LIST, buf);
        let count = self.entries.len().min(20) as u8;
        to_le_bytes!(len, buf, count);
        for entry in self.entries.iter().take(20) {
            to_le_bytes!(len, buf, entry.item_unique_id);
            to_le_bytes!(len, buf, entry.item_template_id);
            to_le_bytes!(len, buf, entry.quantity);
            to_le_bytes!(len, buf, entry.buyback_price);
            to_le_bytes!(len, buf, entry.sell_timestamp);
        }
        len
    }
}

/// SM_UPDATE_PLAYER_APPEARANCE (0x24) — Visual dos 16 slots de equipamento
#[derive(Debug, Clone)]
pub struct UpdatePlayerAppearance {
    pub player_id: u32,
    pub items: [u32; 16],
}

impl UpdatePlayerAppearance {
    pub fn new(player_id: u32, items: [u32; 16]) -> Self {
        Self { player_id, items }
    }
}

impl Serialise for UpdatePlayerAppearance {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(UPDATE_PLAYER_APPEARANCE, buf);
        to_le_bytes!(len, buf, self.player_id);
        for item in &self.items {
            to_le_bytes!(len, buf, *item);
        }
        len
    }
}

/// S_MAIL (0x0A0) — Lista de cartas no correio
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MailLetterSummary {
    pub letter_id: u32,
    pub sender_id: u32,
    pub sender_name: String,
    pub title: String,
    pub letter_type: u8,
    pub is_read: u8,
    pub has_attachment: u8, // bitmask: 0x01=item, 0x02=kinah
    pub item_template_id: u32,
    pub item_quantity: u32,
    pub kinah_amount: u64,
    pub timestamp: u64,
}

impl MailLetterSummary {
    pub fn new(
        letter_id: u32,
        sender_id: u32,
        sender_name: String,
        title: String,
        letter_type: u8,
        is_read: u8,
        has_attachment: u8,
        item_template_id: u32,
        item_quantity: u32,
        kinah_amount: u64,
        timestamp: u64,
    ) -> Self {
        Self {
            letter_id,
            sender_id,
            sender_name,
            title,
            letter_type,
            is_read,
            has_attachment,
            item_template_id,
            item_quantity,
            kinah_amount,
            timestamp,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Mail {
    pub letters: Vec<MailLetterSummary>,
}

impl Mail {
    pub fn new(letters: Vec<MailLetterSummary>) -> Self {
        Self { letters }
    }
}

impl Serialise for Mail {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(MAIL, buf);
        to_le_bytes!(len, buf, self.letters.len() as u16);
        for letter in &self.letters {
            to_le_bytes!(len, buf, letter.letter_id);
            to_le_bytes!(len, buf, letter.sender_id);
            let name_utf16: Vec<u8> = letter.sender_name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
            to_le_bytes!(len, buf, name_utf16.len() as u16);
            copy_bytes!(len, buf, name_utf16);
            let title_utf16: Vec<u8> = letter.title.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
            to_le_bytes!(len, buf, title_utf16.len() as u16);
            copy_bytes!(len, buf, title_utf16);
            to_le_bytes!(len, buf, letter.letter_type);
            to_le_bytes!(len, buf, letter.is_read);
            to_le_bytes!(len, buf, letter.has_attachment);
            if letter.has_attachment & 0x01 != 0 {
                to_le_bytes!(len, buf, letter.item_template_id);
                to_le_bytes!(len, buf, letter.item_quantity);
            }
            if letter.has_attachment & 0x02 != 0 {
                to_le_bytes!(len, buf, letter.kinah_amount);
            }
            to_le_bytes!(len, buf, letter.timestamp);
        }
        len
    }
}

/// S_GUILD_INFO (0x006D) — Informações principais da Legião
#[derive(Debug, Clone)]
pub struct GuildInfo {
    pub guild_id: u32,
    pub guild_name: String,
    pub rank: u8,
    pub race: u8,
    pub exp: u32,
    pub contribution_points: u32,
    pub member_count: u16,
    pub member_max: u16,
    pub leader_id: u32,
    pub notice: String,
    pub kinah: u64,
}

impl GuildInfo {
    pub fn new(
        guild_id: u32,
        guild_name: String,
        rank: u8,
        race: u8,
        exp: u32,
        contribution_points: u32,
        member_count: u16,
        member_max: u16,
        leader_id: u32,
        notice: String,
        kinah: u64,
    ) -> Self {
        Self {
            guild_id,
            guild_name,
            rank,
            race,
            exp,
            contribution_points,
            member_count,
            member_max,
            leader_id,
            notice,
            kinah,
        }
    }
}

impl Serialise for GuildInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GUILD_INFO, buf);
        to_le_bytes!(len, buf, self.guild_id);
        let name_utf16: Vec<u8> = self.guild_name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
        to_le_bytes!(len, buf, name_utf16.len() as u16);
        copy_bytes!(len, buf, name_utf16);
        to_le_bytes!(len, buf, self.rank);
        to_le_bytes!(len, buf, self.race);
        to_le_bytes!(len, buf, self.exp);
        to_le_bytes!(len, buf, self.contribution_points);
        to_le_bytes!(len, buf, self.member_count);
        to_le_bytes!(len, buf, self.member_max);
        to_le_bytes!(len, buf, self.leader_id);
        let notice_utf16: Vec<u8> = self.notice.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
        to_le_bytes!(len, buf, notice_utf16.len() as u16);
        copy_bytes!(len, buf, notice_utf16);
        to_le_bytes!(len, buf, self.kinah);
        len
    }
}

/// S_GUILD_MEMBER_INFO (0x009C) — Informações de um membro da Legião
#[derive(Debug, Clone)]
pub struct GuildMemberInfo {
    pub guild_id: u32,
    pub member_id: u32,
    pub guild_rank_index: u8,
    pub name: String,
    pub class_id: u8,
    pub level: u8,
    pub race: u8,
    pub is_online: u8,
    pub last_online_timestamp: u32,
    pub contribution: u64,
    pub map_id: u32,
}

impl GuildMemberInfo {
    pub fn new(
        guild_id: u32,
        member_id: u32,
        guild_rank_index: u8,
        name: String,
        class_id: u8,
        level: u8,
        race: u8,
        is_online: u8,
        last_online_timestamp: u32,
        contribution: u64,
        map_id: u32,
    ) -> Self {
        Self {
            guild_id,
            member_id,
            guild_rank_index,
            name,
            class_id,
            level,
            race,
            is_online,
            last_online_timestamp,
            contribution,
            map_id,
        }
    }
}

impl Serialise for GuildMemberInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GUILD_MEMBER_INFO, buf);
        to_le_bytes!(len, buf, self.guild_id);
        to_le_bytes!(len, buf, self.member_id);
        to_le_bytes!(len, buf, self.guild_rank_index);
        let name_utf16: Vec<u8> = self.name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
        to_le_bytes!(len, buf, name_utf16.len() as u16);
        copy_bytes!(len, buf, name_utf16);
        to_le_bytes!(len, buf, self.class_id);
        to_le_bytes!(len, buf, self.level);
        to_le_bytes!(len, buf, self.race);
        to_le_bytes!(len, buf, self.is_online);
        to_le_bytes!(len, buf, self.last_online_timestamp);
        to_le_bytes!(len, buf, self.contribution);
        to_le_bytes!(len, buf, self.map_id);
        len
    }
}

/// S_GUILD_EMBLEM_IMG_DATA (0x00D5) — Chunks do PNG do emblema
#[derive(Debug, Clone)]
pub struct GuildEmblemImgData {
    pub guild_id: u32,
    pub chunk_index: u16,
    pub total_chunks: u16,
    pub data: Vec<u8>,
}

impl GuildEmblemImgData {
    pub fn new(guild_id: u32, chunk_index: u16, total_chunks: u16, data: Vec<u8>) -> Self {
        Self {
            guild_id,
            chunk_index,
            total_chunks,
            data,
        }
    }
}

impl Serialise for GuildEmblemImgData {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GUILD_EMBLEM_IMG_DATA, buf);
        to_le_bytes!(len, buf, self.guild_id);
        to_le_bytes!(len, buf, self.chunk_index);
        to_le_bytes!(len, buf, self.total_chunks);
        to_le_bytes!(len, buf, self.data.len() as u16);
        copy_bytes!(len, buf, self.data);
        len
    }
}

/// S_USER_GUILD_DONATION (0x0158) — Doações de Legião
#[derive(Debug, Clone)]
pub struct UserGuildDonation {
    pub player_id: u32,
    pub daily_donated: u64,
    pub daily_limit: u64,
    pub total_donated: u64,
    pub last_donation_timestamp: u32,
}

impl UserGuildDonation {
    pub fn new(
        player_id: u32,
        daily_donated: u64,
        daily_limit: u64,
        total_donated: u64,
        last_donation_timestamp: u32,
    ) -> Self {
        Self {
            player_id,
            daily_donated,
            daily_limit,
            total_donated,
            last_donation_timestamp,
        }
    }
}

impl Serialise for UserGuildDonation {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(USER_GUILD_DONATION, buf);
        to_le_bytes!(len, buf, self.player_id);
        to_le_bytes!(len, buf, self.daily_donated);
        to_le_bytes!(len, buf, self.daily_limit);
        to_le_bytes!(len, buf, self.total_donated);
        to_le_bytes!(len, buf, self.last_donation_timestamp);
        len
    }
}

/// S_USER_GUILD_COIN (0x0165) — Saldo de moedas de Legião
#[derive(Debug, Clone)]
pub struct UserGuildCoin {
    pub player_id: u32,
    pub coin_amount: u64,
}

impl UserGuildCoin {
    pub fn new(player_id: u32, coin_amount: u64) -> Self {
        Self {
            player_id,
            coin_amount,
        }
    }
}

impl Serialise for UserGuildCoin {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(USER_GUILD_COIN, buf);
        to_le_bytes!(len, buf, self.player_id);
        to_le_bytes!(len, buf, self.coin_amount);
        len
    }
}

/// S_GUILD_OPENED_BUFF_TREE_INFO (0x0166) — Buffs ativos da árvore de Legião
#[derive(Debug, Clone)]
pub struct GuildBuffEntry {
    pub buff_id: u32,
    pub remaining_ms: u32,
    pub level: u32,
}

#[derive(Debug, Clone)]
pub struct GuildOpenedBuffTreeInfo {
    pub guild_id: u32,
    pub buffs: Vec<GuildBuffEntry>,
}

impl GuildOpenedBuffTreeInfo {
    pub fn new(guild_id: u32, buffs: Vec<GuildBuffEntry>) -> Self {
        Self { guild_id, buffs }
    }
}

impl Serialise for GuildOpenedBuffTreeInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GUILD_OPENED_BUFF_TREE_INFO, buf);
        to_le_bytes!(len, buf, self.guild_id);
        to_le_bytes!(len, buf, self.buffs.len() as u8);
        for buff in &self.buffs {
            to_le_bytes!(len, buf, buff.buff_id);
            to_le_bytes!(len, buf, buff.remaining_ms);
            to_le_bytes!(len, buf, buff.level);
        }
        len
    }
}

/// S_ALLIANCE_INFO (0x00F5) — Informações da Aliança
#[derive(Debug, Clone)]
pub struct AllianceInfo {
    pub alliance_id: u32,
    pub name: String,
    pub leader_id: u32,
    pub member_count: u8,
}

impl AllianceInfo {
    pub fn new(alliance_id: u32, name: String, leader_id: u32, member_count: u8) -> Self {
        Self {
            alliance_id,
            name,
            leader_id,
            member_count,
        }
    }
}

impl Serialise for AllianceInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ALLIANCE_INFO, buf);
        to_le_bytes!(len, buf, self.alliance_id);
        let name_utf16: Vec<u8> = self.name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
        to_le_bytes!(len, buf, name_utf16.len() as u16);
        copy_bytes!(len, buf, name_utf16);
        to_le_bytes!(len, buf, self.leader_id);
        to_le_bytes!(len, buf, self.member_count);
        len
    }
}

/// S_ALLIANCE_MEMBER_INFO (0x00F6) — Membro da Aliança
#[derive(Debug, Clone)]
pub struct AllianceMemberInfo {
    pub alliance_id: u32,
    pub player_id: u32,
    pub group_index: u8,
    pub name: String,
    pub hp_current: u32,
    pub hp_max: u32,
    pub mp_current: u32,
    pub mp_max: u32,
    pub level: u8,
    pub class_id: u8,
    pub is_online: u8,
}

impl AllianceMemberInfo {
    pub fn new(
        alliance_id: u32,
        player_id: u32,
        group_index: u8,
        name: String,
        hp_current: u32,
        hp_max: u32,
        mp_current: u32,
        mp_max: u32,
        level: u8,
        class_id: u8,
        is_online: u8,
    ) -> Self {
        Self {
            alliance_id,
            player_id,
            group_index,
            name,
            hp_current,
            hp_max,
            mp_current,
            mp_max,
            level,
            class_id,
            is_online,
        }
    }
}

impl Serialise for AllianceMemberInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(ALLIANCE_MEMBER_INFO, buf);
        to_le_bytes!(len, buf, self.alliance_id);
        to_le_bytes!(len, buf, self.player_id);
        to_le_bytes!(len, buf, self.group_index);
        let name_utf16: Vec<u8> = self.name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
        to_le_bytes!(len, buf, name_utf16.len() as u16);
        copy_bytes!(len, buf, name_utf16);
        to_le_bytes!(len, buf, self.hp_current);
        to_le_bytes!(len, buf, self.hp_max);
        to_le_bytes!(len, buf, self.mp_current);
        to_le_bytes!(len, buf, self.mp_max);
        to_le_bytes!(len, buf, self.level);
        to_le_bytes!(len, buf, self.class_id);
        to_le_bytes!(len, buf, self.is_online);
        len
    }
}

/// S_GLOBAL_TRADE_LIST (0x013C) — Catálogo do Broker
#[derive(Debug, Clone)]
pub struct GlobalTradeListingEntry {
    pub listing_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub price_per_unit: u64,
    pub seller_name: String,
    pub expiry_timestamp: u64,
    pub quality: u8,
    pub enhance_level: u8,
}

#[derive(Debug, Clone)]
pub struct GlobalTradeList {
    pub total_count: u32,
    pub page_size: u8,
    pub page: u32,
    pub entries: Vec<GlobalTradeListingEntry>,
}

impl GlobalTradeList {
    pub fn new(total_count: u32, page_size: u8, page: u32, entries: Vec<GlobalTradeListingEntry>) -> Self {
        Self {
            total_count,
            page_size,
            page,
            entries,
        }
    }
}

impl Serialise for GlobalTradeList {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GLOBAL_TRADE_LIST, buf);
        to_le_bytes!(len, buf, self.total_count);
        to_le_bytes!(len, buf, self.page_size);
        to_le_bytes!(len, buf, self.page);
        for e in &self.entries {
            to_le_bytes!(len, buf, e.listing_id);
            to_le_bytes!(len, buf, e.item_template_id);
            to_le_bytes!(len, buf, e.quantity);
            to_le_bytes!(len, buf, e.price_per_unit);
            let name_utf16: Vec<u8> = e.seller_name.encode_utf16().flat_map(|c| c.to_le_bytes()).collect();
            to_le_bytes!(len, buf, name_utf16.len() as u16);
            copy_bytes!(len, buf, name_utf16);
            to_le_bytes!(len, buf, e.expiry_timestamp);
            to_le_bytes!(len, buf, e.quality);
            to_le_bytes!(len, buf, e.enhance_level);
        }
        len
    }
}

/// S_GLOBAL_TRADE_SALESLOG (0x0141) — Histórico de vendas do item
#[derive(Debug, Clone)]
pub struct GlobalTradeSaleslogEntry {
    pub item_template_id: u32,
    pub quantity: u32,
    pub price: u64,
    pub timestamp: u64,
    pub quality: u8,
}

#[derive(Debug, Clone)]
pub struct GlobalTradeSaleslog {
    pub entries: Vec<GlobalTradeSaleslogEntry>,
}

impl GlobalTradeSaleslog {
    pub fn new(entries: Vec<GlobalTradeSaleslogEntry>) -> Self {
        Self { entries }
    }
}

impl Serialise for GlobalTradeSaleslog {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GLOBAL_TRADE_SALESLOG, buf);
        to_le_bytes!(len, buf, self.entries.len() as u16);
        for e in &self.entries {
            to_le_bytes!(len, buf, e.item_template_id);
            to_le_bytes!(len, buf, e.quantity);
            to_le_bytes!(len, buf, e.price);
            to_le_bytes!(len, buf, e.timestamp);
            to_le_bytes!(len, buf, e.quality);
        }
        len
    }
}

/// S_GLOBAL_TRADE_COMMIT (0x013F) — Confirmação de ação no broker
#[derive(Debug, Clone)]
pub struct GlobalTradeCommit {
    pub result: u8,
    pub listing_id: u32,
    pub kinah_received: u64,
}

impl GlobalTradeCommit {
    pub fn new(result: u8, listing_id: u32, kinah_received: u64) -> Self {
        Self {
            result,
            listing_id,
            kinah_received,
        }
    }
}

impl Serialise for GlobalTradeCommit {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GLOBAL_TRADE_COMMIT, buf);
        to_le_bytes!(len, buf, self.result);
        to_le_bytes!(len, buf, self.listing_id);
        to_le_bytes!(len, buf, self.kinah_received);
        len
    }
}

/// S_GLOBAL_TRADE_STATE (0x0144) — Estado do jogador no broker
#[derive(Debug, Clone)]
pub struct GlobalTradeState {
    pub broker_fee_percent: u8,
    pub kinah_pending: u64,
    pub active_listings: u8,
    pub max_listings: u8,
}

impl GlobalTradeState {
    pub fn new(broker_fee_percent: u8, kinah_pending: u64, active_listings: u8, max_listings: u8) -> Self {
        Self {
            broker_fee_percent,
            kinah_pending,
            active_listings,
            max_listings,
        }
    }
}

impl Serialise for GlobalTradeState {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GLOBAL_TRADE_STATE, buf);
        to_le_bytes!(len, buf, self.broker_fee_percent);
        to_le_bytes!(len, buf, self.kinah_pending);
        to_le_bytes!(len, buf, self.active_listings);
        to_le_bytes!(len, buf, self.max_listings);
        len
    }
}

/// S_GLOBAL_TRADE_HISTORY (0x0145) — Histórico de transações pessoais
#[derive(Debug, Clone)]
pub struct GlobalTradeHistoryEntry {
    pub item_template_id: u32,
    pub quantity: u32,
    pub price: u64,
    pub timestamp: u64,
    pub trade_type: u8,
}

#[derive(Debug, Clone)]
pub struct GlobalTradeHistory {
    pub entries: Vec<GlobalTradeHistoryEntry>,
}

impl GlobalTradeHistory {
    pub fn new(entries: Vec<GlobalTradeHistoryEntry>) -> Self {
        Self { entries }
    }
}

impl Serialise for GlobalTradeHistory {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        len += add_prelude(GLOBAL_TRADE_HISTORY, buf);
        to_le_bytes!(len, buf, self.entries.len() as u16);
        for e in &self.entries {
            to_le_bytes!(len, buf, e.item_template_id);
            to_le_bytes!(len, buf, e.quantity);
            to_le_bytes!(len, buf, e.price);
            to_le_bytes!(len, buf, e.timestamp);
            to_le_bytes!(len, buf, e.trade_type);
        }
        len
    }
}

#[cfg(test)]
mod testes_de_inventario {
    use super::*;
    use crate::data_loader::Slot;

    #[test]
    fn test_skill_succeded_serialise() {
        let eff = SkillEffect::new(200, -250, 0, 1);
        let ss = SkillSucceded::new(100, 200, 1001, 1, vec![eff]);
        let mut buf = [0u8; 64];
        let n = ss.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 4 + 4 + 1 + 4 + (4 + 4 + 1 + 1), "5 prelude + 27 payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 100);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 200);
        assert_eq!(u32::from_le_bytes(buf[13..17].try_into().unwrap()), 1001);
        assert_eq!(buf[17], 1);
        assert_eq!(u32::from_le_bytes(buf[18..22].try_into().unwrap()), 1); // 1 effect
        assert_eq!(u32::from_le_bytes(buf[22..26].try_into().unwrap()), 200);
        assert_eq!(i32::from_le_bytes(buf[26..30].try_into().unwrap()), -250);
        assert_eq!(buf[30], 0); // damage_type
        assert_eq!(buf[31], 1); // is_critical
    }

    #[test]
    fn test_abnormal_status_serialise() {
        let eff = AbnormalEffect::new(1001, 30000, 1);
        let ab = AbnormalStatus::with_effects(12345, vec![eff]);
        let mut buf = [0u8; 64];
        let n = ab.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 4 + (4 + 4 + 1), "5 prelude + 17 payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 12345);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1); // 1 effect
        assert_eq!(u32::from_le_bytes(buf[13..17].try_into().unwrap()), 1001);
        assert_eq!(u32::from_le_bytes(buf[17..21].try_into().unwrap()), 30000);
        assert_eq!(buf[21], 1);
    }

    #[test]
    fn test_hit_point_other_serialise() {
        let hpo = HitPointOther::new(200, 150, 850, 1000, 0, 1);
        let mut buf = [0u8; 64];
        let n = hpo.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 4 + 4 + 4 + 1 + 1, "5 prelude + 18 payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 200);
        assert_eq!(i32::from_le_bytes(buf[9..13].try_into().unwrap()), 150);
        assert_eq!(u32::from_le_bytes(buf[13..17].try_into().unwrap()), 850);
        assert_eq!(u32::from_le_bytes(buf[17..21].try_into().unwrap()), 1000);
        assert_eq!(buf[21], 0);
        assert_eq!(buf[22], 1);
    }

    #[test]
    fn test_hit_point_statupdates_serialise() {
        let hp = HitPoint::new(1000, 1500);
        let mut buf = [0u8; 32];
        let n = hp.serialise(&mut buf);
        assert_eq!(n, 5 + 8);
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 1000);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1500);

        let mp = HitPointMp::new(800, 1200);
        let n = mp.serialise(&mut buf);
        assert_eq!(n, 5 + 8);
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 800);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1200);

        let dp = HitPointDp::new(2000, 4000);
        let n = dp.serialise(&mut buf);
        assert_eq!(n, 5 + 8);
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 2000);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 4000);
    }

    #[test]
    fn test_exp_update_serialise() {
        let exp = ExpUpdate::new(125000, 250000);
        let mut buf = [0u8; 32];
        let n = exp.serialise(&mut buf);
        assert_eq!(n, 5 + 8 + 8);
        assert_eq!(u64::from_le_bytes(buf[5..13].try_into().unwrap()), 125000);
        assert_eq!(u64::from_le_bytes(buf[13..21].try_into().unwrap()), 250000);
    }

    #[test]
    fn test_quest_list_serialise() {
        let q = QuestEntry::new(1001, 0, 1, [2, 0, 0, 0], 1600000000);
        let ql = QuestList::new(vec![q]);
        let mut buf = [0u8; 64];
        let n = ql.serialise(&mut buf);
        assert_eq!(n, 5 + 2 + (4 + 1 + 4 + 16 + 4));
        assert_eq!(u16::from_le_bytes(buf[5..7].try_into().unwrap()), 1); // 1 quest
        assert_eq!(u32::from_le_bytes(buf[7..11].try_into().unwrap()), 1001);
        assert_eq!(buf[11], 0); // status
        assert_eq!(u32::from_le_bytes(buf[12..16].try_into().unwrap()), 1); // flags
        assert_eq!(u32::from_le_bytes(buf[16..20].try_into().unwrap()), 2); // var 0
        assert_eq!(u32::from_le_bytes(buf[32..36].try_into().unwrap()), 1600000000); // start_ts
    }

    #[test]
    fn test_store_sale_info_serialise() {
        let ssi = StoreSaleInfo::new(0, 100, 100001, 5, 2500, 7500);
        let mut buf = [0u8; 64];
        let n = ssi.serialise(&mut buf);
        assert_eq!(n, 5 + 1 + 4 + 4 + 4 + 8 + 8);
        assert_eq!(buf[5], 0); // result
        assert_eq!(u32::from_le_bytes(buf[6..10].try_into().unwrap()), 100);
        assert_eq!(u32::from_le_bytes(buf[10..14].try_into().unwrap()), 100001);
        assert_eq!(u32::from_le_bytes(buf[14..18].try_into().unwrap()), 5);
        assert_eq!(u64::from_le_bytes(buf[18..26].try_into().unwrap()), 2500);
        assert_eq!(u64::from_le_bytes(buf[26..34].try_into().unwrap()), 7500);
    }

    #[test]
    fn test_user_sell_history_list_serialise() {
        let entry = SellHistoryEntry::new(100, 100001, 2, 1000, 1600000000);
        let hist = UserSellHistoryList::new(vec![entry]);
        let mut buf = [0u8; 64];
        let n = hist.serialise(&mut buf);
        assert_eq!(n, 5 + 1 + (4 + 4 + 4 + 8 + 8));
        assert_eq!(buf[5], 1); // count = 1
        assert_eq!(u32::from_le_bytes(buf[6..10].try_into().unwrap()), 100);
        assert_eq!(u32::from_le_bytes(buf[10..14].try_into().unwrap()), 100001);
        assert_eq!(u32::from_le_bytes(buf[14..18].try_into().unwrap()), 2);
        assert_eq!(u64::from_le_bytes(buf[18..26].try_into().unwrap()), 1000);
        assert_eq!(u64::from_le_bytes(buf[26..34].try_into().unwrap()), 1600000000);
    }

    #[test]
    fn test_mail_serialise() {
        let l = MailLetterSummary::new(
            1,
            100,
            "Shugo".into(),
            "Welcome".into(),
            0,
            0,
            3,
            100000768,
            1,
            5000,
            1600000000,
        );
        let m = Mail::new(vec![l]);
        let mut buf = [0u8; 128];
        let n = m.serialise(&mut buf);
        assert!(n > 5 + 2);
        assert_eq!(u16::from_le_bytes(buf[5..7].try_into().unwrap()), 1); // 1 letter
        assert_eq!(u32::from_le_bytes(buf[7..11].try_into().unwrap()), 1); // letter_id
        assert_eq!(u32::from_le_bytes(buf[11..15].try_into().unwrap()), 100); // sender_id
    }

    #[test]
    fn test_guild_packets_serialise() {
        let g_info = GuildInfo::new(
            1,
            "Pantheon".into(),
            3,
            0,
            15000,
            2500,
            5,
            30,
            1001,
            "Notice".into(),
            100000,
        );
        let mut buf = [0u8; 128];
        let n = g_info.serialise(&mut buf);
        assert!(n > 5 + 4);

        let g_member = GuildMemberInfo::new(
            1,
            1001,
            1,
            "Ares".into(),
            1,
            50,
            0,
            1,
            0,
            5000,
            110010000,
        );
        let n_m = g_member.serialise(&mut buf);
        assert!(n_m > 5 + 8);
    }

    #[test]
    fn test_buddy_and_alliance_serialise() {
        let b = BuddyEntry {
            player_id: 1002,
            name: "Loki".into(),
            is_online: true,
            map_id: 110010000,
            level: 45,
            class_id: 4,
        };
        let bl = BuddyList::from_entries(vec![b]);
        let mut buf = [0u8; 128];
        let n = bl.serialise(&mut buf);
        assert!(n > 5 + 2);

        let ai = AllianceInfo::new(1, "LegionAlliance".into(), 1001, 12);
        let n_ai = ai.serialise(&mut buf);
        assert!(n_ai > 5 + 4);

        let gtl = GlobalTradeList::new(1, 20, 0, vec![GlobalTradeListingEntry {
            listing_id: 101,
            item_template_id: 182000001,
            quantity: 5,
            price_per_unit: 10000,
            seller_name: "Trader".into(),
            expiry_timestamp: 1700000000,
            quality: 2,
            enhance_level: 0,
        }]);
        let n_gtl = gtl.serialise(&mut buf);
        assert!(n_gtl > 5 + 8);
    }

    #[test]
    fn test_update_player_appearance_serialise() {
        let mut items = [0u32; 16];
        items[0] = 100000768; // MainHand
        items[3] = 110300873; // Chest
        let app = UpdatePlayerAppearance::new(12345, items);
        let mut buf = [0u8; 128];
        let n = app.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 16 * 4);
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 12345);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 100000768);
        assert_eq!(u32::from_le_bytes(buf[21..25].try_into().unwrap()), 110300873);
    }

    #[test]
    fn test_skill_penalty_status_other_serialise() {
        let sp = SkillPenaltyStatusOther::new(12345, 1001, 3000);
        let mut buf = [0u8; 64];
        let n = sp.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 4 + 4, "5 prelude + 12 payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 12345);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1001);
        assert_eq!(u32::from_le_bytes(buf[13..17].try_into().unwrap()), 3000);
    }

    #[test]
    fn test_wind_state_info_serialise_13_bytes() {
        let ws = WindStateInfo::new(12345, 1, 1, 22.0);
        let mut buf = [0u8; 64];
        let n = ws.serialise(&mut buf);
        assert_eq!(n, 5 + 13, "5 bytes prelude + 13 bytes payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 12345);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1);
        assert_eq!(buf[13], 1, "state = 1");
        assert_eq!(f32::from_le_bytes(buf[14..18].try_into().unwrap()), 22.0);
    }

    #[test]
    fn test_wind_path_result_serialise() {
        let waypoints = vec![(100.0, 200.0, 300.0), (110.0, 210.0, 310.0)];
        let wpr = WindPathResult::new(12345, 1, waypoints, 5000.0);
        let mut buf = [0u8; 128];
        let n = wpr.serialise(&mut buf);
        assert_eq!(n, 5 + 4 + 4 + 2 + 24 + 4, "5 prelude + 38 payload");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 12345);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 1);
        assert_eq!(u16::from_le_bytes(buf[13..15].try_into().unwrap()), 2);
        assert_eq!(f32::from_le_bytes(buf[15..19].try_into().unwrap()), 100.0);
        assert_eq!(f32::from_le_bytes(buf[35..39].try_into().unwrap()), 310.0);
        assert_eq!(f32::from_le_bytes(buf[39..43].try_into().unwrap()), 5000.0);
    }

    #[test]
    fn test_request_teleport_serialise_22_bytes() {
        let tp = RequestTeleport::new(1, 110070000, 0, 457.0, 251.0, 127.04, 0);
        let mut buf = [0u8; 64];
        let n = tp.serialise(&mut buf);
        assert_eq!(n, 5 + 22, "5 bytes prelude + 22 bytes payload");
        assert_eq!(buf[5], 1, "tipo = 1");
        assert_eq!(u32::from_le_bytes(buf[6..10].try_into().unwrap()), 110070000);
        assert_eq!(u32::from_le_bytes(buf[10..14].try_into().unwrap()), 0);
        assert_eq!(f32::from_le_bytes(buf[14..18].try_into().unwrap()), 457.0);
        assert_eq!(f32::from_le_bytes(buf[18..22].try_into().unwrap()), 251.0);
        assert_eq!(f32::from_le_bytes(buf[22..26].try_into().unwrap()), 127.04);
        assert_eq!(buf[26], 0, "heading = 0");
    }

    #[test]
    fn test_dialog_window_serialise() {
        let dialog = DialogWindow::new(2147586830, 10, 0);
        let mut buf = [0u8; 64];
        let n = dialog.serialise(&mut buf);
        assert_eq!(n, 5 + 12, "5 bytes prelude + 12 bytes payload (3 x u32)");
        assert_eq!(u32::from_le_bytes(buf[5..9].try_into().unwrap()), 2147586830);
        assert_eq!(u32::from_le_bytes(buf[9..13].try_into().unwrap()), 10);
        assert_eq!(u32::from_le_bytes(buf[13..17].try_into().unwrap()), 0);
    }

    fn item(item_id: u32, posicao: u16, slot: Slot) -> ItemInventario {
        ItemInventario {
            obj_id: 0xC000_0000 | posicao as u32,
            item_id,
            quantidade: 1,
            posicao,
            mascara: 0x612C,
            slot,
            tecido: false,
        }
    }

    /// O tamanho da leva e o do cabecalho mais o de cada registro, sem sobra.
    ///
    /// E a mesma conta que fecha os pacotes da captura: nove bytes de cabecalho e registros
    /// encostados um no outro. Se sobrar ou faltar um byte, o cliente perde o passo na leitura e
    /// o resto do pacote vira lixo.
    #[test]
    fn a_leva_fecha_no_byte() {
        let itens = vec![
            item(182_400_001, 0, Slot::Nenhum),
            item(100_000_094, 1, Slot::Arma { principal: 1, secundario: 2, duas_maos: false }),
        ];
        let esperado: usize = itens.iter().map(|i| i.tamanho()).sum();

        let leva = CarregaInventario45::leva(true, itens);
        let mut buf = [0u8; 1024];
        let n = leva.serialise(&mut buf);

        // 5 bytes de prelude, 9 de cabecalho.
        assert_eq!(n, 5 + 9 + esperado);
        assert_eq!(buf[5], 1, "primeira leva");
        assert_eq!(&buf[6..12], &[0u8; 6], "sem expansao de bolsa");
        assert_eq!(u16::from_le_bytes(buf[12..14].try_into().unwrap()), 2);
    }

    /// A leva que fecha o carregamento nao leva registro nenhum.
    #[test]
    fn a_leva_final_e_vazia() {
        let mut buf = [0u8; 64];
        let n = CarregaInventario45::fim().serialise(&mut buf);

        assert_eq!(n, 5 + 9, "nove bytes de payload, como na captura");
        assert_eq!(buf[5], 0, "nao e a primeira leva");
        assert_eq!(u16::from_le_bytes(buf[12..14].try_into().unwrap()), 0);
    }
}
