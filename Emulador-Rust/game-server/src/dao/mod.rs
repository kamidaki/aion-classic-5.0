pub mod schema;
pub mod account_dao;
pub mod session_dao;
pub mod character_dao;
pub mod inventory_dao;
pub mod skill_dao;
pub mod quest_dao;
pub mod mail_dao;
pub mod guild_dao;
pub mod broker_dao;
pub mod buddy_dao;

pub use schema::init_schema;
pub use account_dao::{AccountDao, AccountData};
pub use session_dao::SessionDao;
pub use character_dao::{CharacterDao, PersistedCharacter};
pub use inventory_dao::{InventoryDao, ItemPersistido, OBJ_ID_BASE, KINAH_ITEM_ID};
pub use skill_dao::SkillDao;
pub use quest_dao::{QuestDao, QuestPersistida};
pub use mail_dao::MailDao;
pub use guild_dao::GuildDao;
pub use broker_dao::BrokerDao;
pub use buddy_dao::BuddyDao;

use rusqlite::{Connection, Result};
use std::path::Path;

/// Fachada unificada de banco de dados (Db Facade) que delega operações aos DAOs específicos
pub struct Db {
    pub conn: Connection,
}

impl Db {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let db = Self { conn };
        db.init_schema()?;
        Ok(db)
    }

    pub fn init_schema(&self) -> Result<()> {
        schema::init_schema(&self.conn)
    }

    pub fn migrate(&self) -> Result<()> {
        self.conn.execute_batch("
            PRAGMA journal_mode = WAL;
            PRAGMA busy_timeout = 5000;
            PRAGMA synchronous = NORMAL;
            PRAGMA foreign_keys = ON;
        ")?;
        self.init_schema()?;
        self.conn.execute_batch("PRAGMA user_version = 2;")?;
        Ok(())
    }

    // --- Métodos de Sessão e Contas ---
    pub fn lookup_session(&self, token: &str) -> Result<Option<String>> {
        SessionDao::lookup_session(&self.conn, token)
    }

    pub fn resolver_sessao(&self, account_id: u32, session_key: u32) -> Result<Option<String>> {
        SessionDao::resolver_sessao(&self.conn, account_id, session_key)
    }

    // --- Métodos de Personagem ---
    pub fn base_stats_for_class(class_id: u32) -> (u32, u32) {
        CharacterDao::base_stats_for_class(class_id)
    }

    pub fn initial_skills_for_class(class_id: u32) -> Vec<(u32, u8)> {
        SkillDao::initial_skills_for_class(class_id)
    }

    pub fn criar_personagem(
        &self,
        username: &str,
        nome: &str,
        aparencia: &[u8],
    ) -> Result<PersistedCharacter> {
        CharacterDao::criar_personagem(&self.conn, username, nome, aparencia)
    }

    pub fn criar_personagem_com_xml(
        &self,
        username: &str,
        nome: &str,
        aparencia: &[u8],
        ponto: Option<crate::mundo::PontoDeEntrada>,
        itens: &[(u32, u32)],
    ) -> Result<PersistedCharacter> {
        CharacterDao::criar_personagem_com_xml(&self.conn, username, nome, aparencia, ponto, itens)
    }

    pub fn personagens_da_conta(&self, username: &str) -> Result<Vec<PersistedCharacter>> {
        CharacterDao::personagens_da_conta(&self.conn, username)
    }

    pub fn verificar_nome_em_uso(&self, name: &str) -> Result<bool> {
        CharacterDao::verificar_nome_em_uso(&self.conn, name)
    }

    pub fn deletar_personagem(&self, username: &str, character_id: u32) -> Result<bool> {
        CharacterDao::deletar_personagem(&self.conn, username, character_id)
    }

    pub fn get_first_character(&self, username: &str) -> Result<Option<PersistedCharacter>> {
        CharacterDao::get_first_character(&self.conn, username)
    }

    pub fn buscar_personagem_por_nome(&self, name: &str) -> Result<Option<PersistedCharacter>> {
        CharacterDao::buscar_personagem_por_nome(&self.conn, name)
    }

    pub fn save_character(
        &self,
        id: u32,
        x: f32,
        y: f32,
        z: f32,
        map_id: u32,
        heading: u8,
        level: u16,
        exp: u64,
        hp: u32,
        mp: u32,
    ) -> Result<()> {
        CharacterDao::save_character(&self.conn, id, x, y, z, map_id, heading, level, exp, hp, mp)
    }

    // --- Métodos de Inventário e Itens ---
    pub fn garante_kit_inicial(&self, character_id: u32, itens: &[(u32, u32)]) -> Result<bool> {
        InventoryDao::garante_kit_inicial(&self.conn, character_id, itens)
    }

    pub fn itens_do_personagem(&self, character_id: u32) -> Result<Vec<ItemPersistido>> {
        InventoryDao::itens_do_personagem(&self.conn, character_id)
    }

    pub fn adicionar_item(
        &self,
        character_id: u32,
        item_id: u32,
        quantidade: u64,
        posicao: u16,
    ) -> Result<u32> {
        InventoryDao::adicionar_item(&self.conn, character_id, item_id, quantidade, posicao)
    }

    pub fn remover_item(&self, character_id: u32, item_id: u32, quantidade: u64) -> Result<bool> {
        InventoryDao::remover_item(&self.conn, character_id, item_id, quantidade)
    }

    pub fn obter_kinah(&self, character_id: u32) -> Result<u64> {
        InventoryDao::obter_kinah(&self.conn, character_id)
    }

    pub fn alterar_kinah(&self, character_id: u32, delta: i64) -> Result<bool> {
        InventoryDao::alterar_kinah(&self.conn, character_id, delta)
    }

    pub fn transferir_item_entre_personagens(
        &mut self,
        remetente_id: u32,
        destinatario_id: u32,
        item_id: u32,
        quantidade: u32,
    ) -> Result<bool> {
        InventoryDao::transferir_item_entre_personagens(&mut self.conn, remetente_id, destinatario_id, item_id, quantidade)
    }

    // --- Métodos de Skills ---
    pub fn salvar_skills(&self, char_id: u32, skills: &[(u32, u8)]) -> Result<()> {
        SkillDao::salvar_skills(&self.conn, char_id, skills)
    }

    pub fn carregar_skills(&self, char_id: u32) -> Result<Vec<(u32, u8)>> {
        SkillDao::carregar_skills(&self.conn, char_id)
    }

    // --- Métodos de Missões (Quests) ---
    pub fn salvar_quest(
        &self,
        character_id: u32,
        quest_id: u32,
        status: &str,
        quest_vars: u32,
        complete_count: u32,
    ) -> Result<()> {
        QuestDao::salvar_quest(&self.conn, character_id, quest_id, status, quest_vars, complete_count)
    }

    pub fn save_quest(
        &self,
        character_id: u32,
        quest_id: u32,
        status: u8,
        flags: u32,
        vars: [u32; 4],
        start_ts: u32,
    ) -> Result<()> {
        QuestDao::save_quest(&self.conn, character_id, quest_id, status, flags, vars, start_ts)
    }

    pub fn quests_do_personagem(&self, character_id: u32) -> Result<Vec<QuestPersistida>> {
        QuestDao::quests_do_personagem(&self.conn, character_id)
    }

    pub fn salvar_quests(&self, character_id: u32, quests: &[QuestPersistida]) -> Result<()> {
        QuestDao::salvar_quests(&self.conn, character_id, quests)
    }

    pub fn carregar_quests(&self, character_id: u32) -> Result<Vec<QuestPersistida>> {
        QuestDao::carregar_quests(&self.conn, character_id)
    }

    // --- Métodos de Correio (Mail) ---
    pub fn salvar_carta(
        &self,
        recipient_id: u32,
        sender_name: &str,
        title: &str,
        body: &str,
        letter_type: u8,
        item_template_id: u32,
        item_quantity: u32,
        kinah_amount: u64,
    ) -> Result<u32> {
        MailDao::salvar_carta(&self.conn, recipient_id, sender_name, title, body, letter_type, item_template_id, item_quantity, kinah_amount)
    }

    pub fn cartas_do_personagem(&self, recipient_id: u32) -> Result<Vec<crate::mail::Letter>> {
        MailDao::cartas_do_personagem(&self.conn, recipient_id)
    }

    pub fn marcar_carta_lida(&self, letter_id: u32) -> Result<bool> {
        MailDao::marcar_carta_lida(&self.conn, letter_id)
    }

    pub fn deletar_carta(&self, letter_id: u32) -> Result<bool> {
        MailDao::deletar_carta(&self.conn, letter_id)
    }

    pub fn extrair_anexos_carta(&self, letter_id: u32) -> Result<bool> {
        MailDao::extrair_anexos_carta(&self.conn, letter_id)
    }

    // --- Métodos de Guilda / Legião ---
    pub fn criar_guild(&self, name: &str, race: u8, leader_id: u32) -> Result<u32> {
        GuildDao::criar_guild(&self.conn, name, race, leader_id)
    }

    pub fn adicionar_membro_guild(&self, guild_id: u32, player_id: u32, rank_index: u8) -> Result<()> {
        GuildDao::adicionar_membro_guild(&self.conn, guild_id, player_id, rank_index)
    }

    pub fn remover_membro_guild(&self, guild_id: u32, player_id: u32) -> Result<bool> {
        GuildDao::remover_membro_guild(&self.conn, guild_id, player_id)
    }

    pub fn guild_do_jogador(&self, player_id: u32) -> Result<Option<crate::guild::Guild>> {
        GuildDao::guild_do_jogador(&self.conn, player_id)
    }

    // --- Métodos de Amigos (Buddies) ---
    pub fn adicionar_amigo(&self, player_id: u32, buddy_id: u32) -> Result<()> {
        BuddyDao::adicionar_amigo(&self.conn, player_id, buddy_id)
    }

    pub fn remover_amigo(&self, player_id: u32, buddy_id: u32) -> Result<bool> {
        BuddyDao::remover_amigo(&self.conn, player_id, buddy_id)
    }

    pub fn amigos_do_personagem(&self, player_id: u32) -> Result<Vec<crate::message::server::BuddyEntry>> {
        BuddyDao::amigos_do_personagem(&self.conn, player_id)
    }

    // --- Métodos do Broker / Mercado ---
    pub fn salvar_anuncio_broker(
        &self,
        seller_id: u32,
        seller_name: &str,
        item_template_id: u32,
        quantity: u32,
        price_per_unit: u64,
        expiry_ts: u64,
        quality: u8,
        enhance_level: u8,
    ) -> Result<u32> {
        BrokerDao::salvar_anuncio_broker(&self.conn, seller_id, seller_name, item_template_id, quantity, price_per_unit, expiry_ts, quality, enhance_level)
    }

    pub fn listar_anuncios_broker(
        &self,
        page: u32,
        page_size: u8,
    ) -> Result<(u32, Vec<crate::message::server::GlobalTradeListingEntry>)> {
        BrokerDao::listar_anuncios_broker(&self.conn, page, page_size)
    }

    pub fn comprar_anuncio_broker(&self, listing_id: u32) -> Result<Option<(u32, String, u32, u32, u64)>> {
        BrokerDao::comprar_anuncio_broker(&self.conn, listing_id)
    }

    pub fn salvar_historico_broker(
        &self,
        player_id: u32,
        item_template_id: u32,
        quantity: u32,
        price: u64,
        timestamp: u64,
        trade_type: u8,
    ) -> Result<()> {
        BrokerDao::salvar_historico_broker(&self.conn, player_id, item_template_id, quantity, price, timestamp, trade_type)
    }

    pub fn historico_vendas_item(
        &self,
        item_template_id: u32,
        quality: u8,
    ) -> Result<Vec<crate::message::server::GlobalTradeSaleslogEntry>> {
        BrokerDao::historico_vendas_item(&self.conn, item_template_id, quality)
    }

    pub fn preco_medio_item(&self, item_template_id: u32) -> Result<u64> {
        BrokerDao::preco_medio_item(&self.conn, item_template_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::params;

    fn in_memory() -> Db {
        let conn = Connection::open_in_memory().unwrap();
        let db = Db { conn };
        db.init_schema().unwrap();
        db
    }

    fn grava_sessao(db: &Db, token: &str, conta: &str, account_id: u32, key: u32, expires_at: i64) {
        db.conn
            .execute(
                "INSERT INTO sessions (token, account_name, account_id, session_key, created_at, expires_at)
                 VALUES (?1, ?2, ?3, ?4, 0, ?5)",
                params![token, conta, account_id as i64, key as i64, expires_at],
            )
            .unwrap();
    }

    fn daqui_a(segundos: i64) -> i64 {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64
            + segundos
    }

    #[test]
    fn resolver_sessao_casa_o_par_do_hq_login() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(600));

        assert_eq!(
            db.resolver_sessao(40_820_537, 0x161E).unwrap().as_deref(),
            Some("kamidaki")
        );
    }

    #[test]
    fn resolver_sessao_recusa_chave_errada() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(600));

        assert_eq!(db.resolver_sessao(40_820_537, 0x3939).unwrap(), None);
        assert_eq!(db.resolver_sessao(1, 0x161E).unwrap(), None);
    }

    #[test]
    fn resolver_sessao_recusa_sessao_expirada() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x161E, daqui_a(-1));
        assert_eq!(db.resolver_sessao(40_820_537, 0x161E).unwrap(), None);
    }

    #[test]
    fn resolver_sessao_pega_a_mais_recente_da_conta() {
        let db = in_memory();
        grava_sessao(&db, "tok1", "kamidaki", 40_820_537, 0x1111, daqui_a(600));
        grava_sessao(&db, "tok2", "kamidaki", 40_820_537, 0x2222, daqui_a(600));

        assert_eq!(
            db.resolver_sessao(40_820_537, 0x2222).unwrap().as_deref(),
            Some("kamidaki")
        );
    }

    #[test]
    fn skills_salvar_e_carregar_e_migrate() {
        let db = in_memory();
        db.migrate().unwrap();

        let mut aparencia = vec![0u8; 140];
        aparencia[56..60].copy_from_slice(&0u32.to_le_bytes()); // Elyos
        aparencia[60..64].copy_from_slice(&1u32.to_le_bytes()); // Gladiator (Warrior)

        let itens_iniciais = vec![(182400001, 0), (101301127, 1)];
        let criado = db.criar_personagem_com_xml("conta_teste", "Guerreiro", &aparencia, None, &itens_iniciais).unwrap();
        assert_eq!(criado.level, 1);
        assert_eq!(criado.hp, 1278);
        assert_eq!(criado.mp, 577);
        assert_eq!(criado.map_id, 210010000); // Elyos (Poeta Classic 2.8) - lido do player_initial_data.xml

        let itens = db.itens_do_personagem(criado.id).unwrap();
        assert_eq!(itens.len(), 2);

        let skills = db.carregar_skills(criado.id).unwrap();
        assert_eq!(skills.len(), 4);
    }

    #[test]
    fn test_quest_persistence_save_load() {
        let db = in_memory();
        let mut aparencia = vec![0u8; 140];
        let p = db.criar_personagem("teste_q", "QuestHero", &aparencia).unwrap();

        let quests = vec![
            QuestPersistida {
                quest_id: 1001,
                status: "IN_PROGRESS".to_string(),
                quest_vars: 3,
                complete_count: 0,
            },
            QuestPersistida {
                quest_id: 1002,
                status: "COMPLETE".to_string(),
                quest_vars: 0,
                complete_count: 1,
            },
        ];

        db.salvar_quests(p.id, &quests).expect("deve salvar quests");
        let carregadas = db.carregar_quests(p.id).expect("deve carregar quests");
        assert_eq!(carregadas.len(), 2);
        assert!(carregadas.iter().any(|q| q.quest_id == 1001 && q.quest_vars == 3));
        assert!(carregadas.iter().any(|q| q.quest_id == 1002 && q.status == "COMPLETE"));
    }

    #[test]
    fn test_atomic_item_transfer_between_characters() {
        let mut db = in_memory();
        let mut aparencia = vec![0u8; 140];
        let p1 = db.criar_personagem("c1", "Sender", &aparencia).unwrap();
        let p2 = db.criar_personagem("c2", "Receiver", &aparencia).unwrap();

        db.conn.execute(
            "INSERT INTO character_items (character_id, item_id, quantidade, posicao) VALUES (?1, 160000001, 50, 0)",
            params![p1.id as i64],
        ).unwrap();

        let sucesso = db.transferir_item_entre_personagens(p1.id, p2.id, 160000001, 20).unwrap();
        assert!(sucesso);

        let itens_p1 = db.itens_do_personagem(p1.id).unwrap();
        let pocao_p1 = itens_p1.iter().find(|i| i.item_id == 160000001).unwrap();
        assert_eq!(pocao_p1.quantidade, 30);

        let itens_p2 = db.itens_do_personagem(p2.id).unwrap();
        let pocao_p2 = itens_p2.iter().find(|i| i.item_id == 160000001).unwrap();
        assert_eq!(pocao_p2.quantidade, 20);
    }
}
