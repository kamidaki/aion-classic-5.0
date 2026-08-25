use rusqlite::{Connection, Result};

/// Inicializa o esquema de tabelas e configurações de desempenho do SQLite
pub fn init_schema(conn: &Connection) -> Result<()> {
    conn.execute_batch(
        "
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        CREATE TABLE IF NOT EXISTS account_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL DEFAULT '',
            access_level INTEGER NOT NULL DEFAULT 0,
            membership INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
            last_ip TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES account_data(id),
            name TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            exp INTEGER NOT NULL DEFAULT 0,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            map_id INTEGER NOT NULL DEFAULT 110070000,
            heading INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL DEFAULT 100,
            mp INTEGER NOT NULL DEFAULT 100,
            aparencia BLOB,
            kit_inicial INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
        );
        CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);
        CREATE TABLE IF NOT EXISTS character_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            item_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            posicao INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_items_character ON character_items(character_id);
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            account_name TEXT NOT NULL,
            account_id INTEGER NOT NULL DEFAULT 1,
            session_key INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
            expires_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS player_quests (
            character_id INTEGER NOT NULL REFERENCES characters(id),
            quest_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            quest_vars INTEGER DEFAULT 0,
            complete_count INTEGER DEFAULT 0,
            PRIMARY KEY(character_id, quest_id)
        );
        CREATE INDEX IF NOT EXISTS idx_quests_character ON player_quests(character_id);
        CREATE TABLE IF NOT EXISTS character_mail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id INTEGER NOT NULL REFERENCES characters(id),
            sender_id INTEGER NOT NULL DEFAULT 0,
            sender_name TEXT NOT NULL DEFAULT 'System',
            title TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL DEFAULT '',
            letter_type INTEGER NOT NULL DEFAULT 0,
            is_read INTEGER NOT NULL DEFAULT 0,
            item_template_id INTEGER NOT NULL DEFAULT 0,
            item_quantity INTEGER NOT NULL DEFAULT 0,
            kinah_amount INTEGER NOT NULL DEFAULT 0,
            timestamp INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_mail_recipient ON character_mail(recipient_id);
        CREATE TABLE IF NOT EXISTS guilds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            rank INTEGER NOT NULL DEFAULT 1,
            race INTEGER NOT NULL DEFAULT 0,
            exp INTEGER NOT NULL DEFAULT 0,
            leader_id INTEGER NOT NULL,
            notice TEXT NOT NULL DEFAULT '',
            kinah INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INTEGER NOT NULL REFERENCES guilds(id),
            player_id INTEGER NOT NULL REFERENCES characters(id),
            rank_index INTEGER NOT NULL DEFAULT 5,
            contribution INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, player_id)
        );
        CREATE INDEX IF NOT EXISTS idx_guild_members_player ON guild_members(player_id);
        CREATE TABLE IF NOT EXISTS character_buddies (
            player_id INTEGER NOT NULL REFERENCES characters(id),
            buddy_id INTEGER NOT NULL REFERENCES characters(id),
            PRIMARY KEY (player_id, buddy_id)
        );
        CREATE INDEX IF NOT EXISTS idx_buddies_player ON character_buddies(player_id);
        CREATE TABLE IF NOT EXISTS broker_listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            seller_name TEXT NOT NULL,
            item_template_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_per_unit INTEGER NOT NULL,
            expiry_ts INTEGER NOT NULL,
            quality INTEGER NOT NULL DEFAULT 0,
            enhance_level INTEGER NOT NULL DEFAULT 0,
            is_sold INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_broker_active ON broker_listings(is_sold, expiry_ts);
        CREATE TABLE IF NOT EXISTS broker_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            item_template_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            type INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_broker_history_player ON broker_history(player_id);
        CREATE TABLE IF NOT EXISTS character_skills (
            character_id INTEGER NOT NULL REFERENCES characters(id),
            skill_id INTEGER NOT NULL,
            skill_level INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (character_id, skill_id)
        );
        CREATE INDEX IF NOT EXISTS idx_skills_character ON character_skills(character_id);

        -- Tabelas adicionais da referencia Classic 2.4 / 4.8 Retail
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            account_id INTEGER NOT NULL,
            account_name TEXT NOT NULL DEFAULT '',
            exp INTEGER NOT NULL DEFAULT 0,
            x REAL NOT NULL DEFAULT 457.0,
            y REAL NOT NULL DEFAULT 251.0,
            z REAL NOT NULL DEFAULT 127.04,
            heading INTEGER NOT NULL DEFAULT 0,
            world_id INTEGER NOT NULL DEFAULT 110070000,
            gender INTEGER NOT NULL DEFAULT 0,
            race INTEGER NOT NULL DEFAULT 0,
            player_class INTEGER NOT NULL DEFAULT 1,
            creation_date INTEGER NOT NULL DEFAULT 0,
            last_online INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL DEFAULT 1000,
            mp INTEGER NOT NULL DEFAULT 1000,
            dp INTEGER NOT NULL DEFAULT 0,
            title_id INTEGER NOT NULL DEFAULT 0,
            kinah INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS inventory (
            item_unique_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            item_count INTEGER NOT NULL DEFAULT 1,
            item_color INTEGER NOT NULL DEFAULT 0,
            item_owner INTEGER NOT NULL,
            item_creator TEXT DEFAULT '',
            item_location INTEGER NOT NULL DEFAULT 0,
            is_equiped INTEGER NOT NULL DEFAULT 0,
            is_soul_bound INTEGER NOT NULL DEFAULT 0,
            slot INTEGER NOT NULL DEFAULT 0,
            enchant INTEGER NOT NULL DEFAULT 0,
            fusioned_item INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS player_skills (
            player_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            skill_level INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (player_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS legions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            rank INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            contribution_points INTEGER NOT NULL DEFAULT 0,
            leader_id INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS legion_members (
            legion_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            nickname TEXT DEFAULT '',
            rank INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (legion_id, player_id)
        );

        CREATE TABLE IF NOT EXISTS abyss_rank (
            player_id INTEGER PRIMARY KEY,
            daily_ap INTEGER NOT NULL DEFAULT 0,
            weekly_ap INTEGER NOT NULL DEFAULT 0,
            ap INTEGER NOT NULL DEFAULT 0,
            rank INTEGER NOT NULL DEFAULT 1,
            top_ranking INTEGER NOT NULL DEFAULT 0,
            daily_kill INTEGER NOT NULL DEFAULT 0,
            weekly_kill INTEGER NOT NULL DEFAULT 0,
            all_kill INTEGER NOT NULL DEFAULT 0,
            max_rank INTEGER NOT NULL DEFAULT 1,
            last_kill INTEGER NOT NULL DEFAULT 0,
            last_ap INTEGER NOT NULL DEFAULT 0,
            gp INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS player_titles (
            player_id INTEGER NOT NULL,
            title_id INTEGER NOT NULL,
            remaining_time INTEGER NOT NULL DEFAULT -1,
            PRIMARY KEY (player_id, title_id)
        );

        CREATE TABLE IF NOT EXISTS player_effects (
            player_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            skill_lvl INTEGER NOT NULL DEFAULT 1,
            current_time INTEGER NOT NULL DEFAULT 0,
            end_time INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (player_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS player_bind_point (
            player_id INTEGER PRIMARY KEY,
            map_id INTEGER NOT NULL DEFAULT 110070000,
            x REAL NOT NULL DEFAULT 457.0,
            y REAL NOT NULL DEFAULT 251.0,
            z REAL NOT NULL DEFAULT 127.04,
            heading INTEGER NOT NULL DEFAULT 0
        );
        ",
    )?;

    // Compatibilidade com colunas legadas se existirem
    let _ = conn.execute("ALTER TABLE characters ADD COLUMN aparencia BLOB", []);
    let _ = conn.execute("ALTER TABLE characters ADD COLUMN kit_inicial INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE characters ADD COLUMN map_id INTEGER NOT NULL DEFAULT 110070000", []);
    let _ = conn.execute("ALTER TABLE characters ADD COLUMN heading INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN name TEXT", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN password TEXT NOT NULL DEFAULT ''", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN access_level INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN membership INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN last_ip TEXT NOT NULL DEFAULT ''", []);
    let _ = conn.execute("ALTER TABLE account_data ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0", []);

    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN account_name TEXT", []);
    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN username TEXT", []);
    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1", []);
    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN session_key INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN created_at INTEGER NOT NULL DEFAULT 0", []);
    let _ = conn.execute("ALTER TABLE sessions ADD COLUMN expires_at INTEGER NOT NULL DEFAULT 0", []);

    // Anexa login.db se existir para permitir consultas cruzadas de sessao
    let _ = conn.execute("ATTACH DATABASE 'data/Banco de Dados/login.db' AS login_db", []);
    let _ = conn.execute("ATTACH DATABASE 'login.db' AS login_db", []);

    Ok(())
}
