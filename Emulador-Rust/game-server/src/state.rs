//! Orquestrador Central do Estado do Jogo (State / WorldManager - Padrão Java AION)
//!
//! Delega a lógica de cada pacote para a camada modular de serviços (`services::*`).

use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use std::time::Instant;

use crate::data_loader::GameData;
use crate::dataholders::DataManager;
use crate::db::Db;
use crate::character::Character;
use crate::engine::Coord;
use crate::entity::Entity;
use crate::message::client as c;
use crate::{ClientUpdate, Messages};
use crate::services::*;

pub struct State {
    pub characters: HashMap<u32, Character>,
    pub entities: Vec<Entity>,
    pub put_npc: HashMap<u32, Vec<u8>>,
    pub npcs_em_cena: HashMap<u32, (HashSet<u32>, Coord)>,
    pub burst: Vec<(u16, Vec<u8>)>,
    pub mundo_enviado: HashSet<u32>,
    pub windstream_service: WindstreamService,
    pub attack_timers: HashMap<u32, (u32, Instant)>,
    pub guild_manager: GuildManager,
    pub party_service: PartyService,
    pub chat_timestamps: HashMap<u32, Vec<Instant>>,
    pub teleport_service: TeleportService,
    pub title_service: TitleService,
    pub trade_service: TradeService,
    pub restrictions: crate::restrictions::RestrictionsManager,
    pub spawn_engine: crate::spawnengine::SpawnEngine,
    pub skill_engine: crate::skillengine::SkillEngine,
    pub ai_engine: crate::ai::AIEngine,
    pub instance_service: crate::instance::InstanceService,
    pub db: Db,
    pub game_data: Arc<GameData>,
    pub data_manager: Arc<DataManager>,
}

impl State {
    pub fn new(db: Db, game_data: Arc<GameData>) -> Self {
        let mut entities = Vec::with_capacity(1000);
        let mut put_npc: HashMap<u32, Vec<u8>> = HashMap::new();

        let mosbear = Entity::new(
            2147586830,
            Coord::new(1816., 589., 256.),
            crate::data::npc::Id::StarvedMosbear,
            crate::data::npc::Name::StarvedMosbear,
        );
        if let Some(def) = game_data.npcs.get(&(crate::data::npc::Id::StarvedMosbear as u32)) {
            println!(
                "INFO: spawned entity {} (id {}) -> catalog name: {}",
                mosbear.id(),
                crate::data::npc::Id::StarvedMosbear as u32,
                def.name
            );
        }
        entities.push(mosbear);

        // Inicializa o SpawnEngine e carrega todos os spawns oficiais
        let mut spawn_engine = crate::spawnengine::SpawnEngine::new();
        let spawn_csv = std::path::Path::new("data/spawns.csv");
        if spawn_csv.exists() {
            if let Ok(count) = spawn_engine.load_from_csv(spawn_csv) {
                println!("INFO: [SpawnEngine] {} templates de spawn carregados do CSV", count);
            }
        }
        spawn_engine.spawn_all(&mut entities, &mut put_npc);

        if !game_data.spawns.is_empty() && entities.len() <= 1 {
            for (i, sp) in game_data.spawns.iter().enumerate() {
                let id = 0x8000_0000 | (i as u32 + 1);
                entities.push(Entity::novo(
                    id,
                    Coord::new(sp.x, sp.y, sp.z),
                    sp.npc_id,
                    sp.nome_id,
                ));

                let mut payload = sp.payload.clone();
                let off = crate::data_loader::OFFSET_ID_ENTIDADE;
                if payload.len() >= off + 4 {
                    payload[off..off + 4].copy_from_slice(&id.to_le_bytes());
                    put_npc.insert(id, payload);
                }
            }
        }
        if !entities.is_empty() {
            println!("INFO: {} NPCs instanciados pelo SpawnEngine no mundo", entities.len());
        }

        // Carrega os DataHolders com os XMLs oficiais do client
        let client_dir = std::path::Path::new("data/client");
        let root_data = std::path::Path::new("data");
        let data_manager = Arc::new(DataManager::load_all(client_dir, root_data));

        // Inicializa o Motor de IA e registra todas as entidades ativas
        let mut ai_engine = crate::ai::AIEngine::new();
        for entity in &entities {
            ai_engine.register_ai(entity.id(), crate::ai::AIName::Monster);
        }

        Self {
            characters: HashMap::with_capacity(1000),
            entities,
            put_npc,
            npcs_em_cena: HashMap::new(),
            mundo_enviado: HashSet::new(),
            burst: if std::env::var("AION_BURST").is_ok() {
                let caminho = std::env::var("AION_REPLAY").unwrap_or_else(|_| "replay.bin".to_string());
                super::message::replay::burst_de_entrada(std::path::Path::new(&caminho))
            } else {
                Vec::new()
            },
            windstream_service: WindstreamService::new(),
            attack_timers: HashMap::new(),
            guild_manager: GuildManager::new(),
            party_service: PartyService::new(),
            chat_timestamps: HashMap::new(),
            teleport_service: TeleportService::new(),
            title_service: TitleService::from_data(&game_data.titles),
            trade_service: TradeService::from_data(&game_data.goods_lists),
            restrictions: crate::restrictions::RestrictionsManager::new(),
            spawn_engine,
            skill_engine: crate::skillengine::SkillEngine::new(),
            ai_engine,
            instance_service: crate::instance::InstanceService::new(),
            db,
            game_data,
            data_manager,
        }
    }

    /// Salva o estado dos personagens no SQLite
    pub fn persist_all(&self) {
        for c in self.characters.values() {
            self.persist_one(c);
        }
    }

    fn persist_one(&self, c: &Character) {
        let loc = c.location();
        if let Err(e) = self.db.save_character(
            c.id(),
            loc.x(),
            loc.y(),
            loc.z(),
            c.spawn_map_id(),
            c.heading(),
            c.stats.level,
            c.stats.exp,
            c.stats.hp.current() as u32,
            c.stats.mp.current(),
        ) {
            eprintln!("ERROR: failed to persist character {}: {e}", c.id());
        }
    }

    /// Desconecta o cliente e persiste o personagem
    pub fn disconnect_client(&mut self, client_id: u16) {
        let to_remove: Vec<u32> = self
            .characters
            .iter()
            .filter(|(_, c)| c.client_id() == client_id)
            .map(|(id, _)| *id)
            .collect();

        for char_id in to_remove {
            if let Some(character) = self.characters.remove(&char_id) {
                self.persist_one(&character);
                println!(
                    "INFO: client {client_id} disconnected, character {} '{}' saved and removed from state",
                    character.id(),
                    character.name()
                );

                for entity in &mut self.entities {
                    if entity.target_id() == Some(character.id()) {
                        entity.clear_target();
                    }
                }
            }
        }
    }

    /// Roteamento modular de pacotes do cliente para os respectivos serviços
    pub fn respond(&mut self, update: &ClientUpdate, messages: &mut Messages) {
        match &update.message() {
            c::Message::MoveNew(move_new) => {
                SpatialService::handle_move(
                    update.character_id(),
                    update.client_id(),
                    move_new,
                    &mut self.characters,
                    &mut self.npcs_em_cena,
                    &self.entities,
                    &self.put_npc,
                    messages,
                );
            }
            c::Message::UseSkill(use_skill) => {
                SkillService::handle_use_skill(
                    update,
                    use_skill,
                    &mut self.characters,
                    &mut self.entities,
                    &self.restrictions,
                    &mut self.skill_engine,
                    messages,
                );
            }
            c::Message::Attack(attack) => {
                CombatService::handle_attack(
                    update.character_id(),
                    attack,
                    &mut self.characters,
                    &mut self.entities,
                    &mut self.attack_timers,
                    &self.restrictions,
                    &mut self.spawn_engine,
                    messages,
                );
            }
            c::Message::ChangeTarget(change_target) => {
                CombatService::handle_change_target(change_target, &self.entities, messages);
            }
            c::Message::Action(action) => {
                CombatService::handle_action(
                    update.character_id(),
                    action,
                    &mut self.characters,
                    messages,
                );
            }
            c::Message::Loot(msg) => match msg.action {
                c::LootAction::Start => {
                    ItemService::handle_loot_start(
                        update.character_id(),
                        update.client_id(),
                        msg.entity_id,
                        &mut self.characters,
                        messages,
                    );
                }
                c::LootAction::Stop => {}
            },
            c::Message::LootItem(msg) => {
                ItemService::handle_loot_item(
                    update.character_id(),
                    update.client_id(),
                    msg.entity_id,
                    &mut self.characters,
                    messages,
                );
            }
            c::Message::CharacterList(_) => {
                PlayerService::handle_character_list(
                    &self.db,
                    update,
                    &mut self.characters,
                    messages,
                );
            }
            c::Message::CreateCharacter(pedido) => {
                PlayerService::handle_create_character(
                    &self.db,
                    &self.data_manager,
                    update,
                    pedido,
                    &mut self.characters,
                    messages,
                );
            }
            c::Message::DeleteCharacter(pedido) => {
                PlayerService::handle_delete_character(
                    &self.db,
                    update,
                    pedido,
                    &mut self.characters,
                    messages,
                );
            }
            c::Message::EnterWorld(selecao) => {
                self.mundo_enviado.remove(&selecao.character_id);
            }
            c::Message::LevelReady(_) => {
                PlayerService::handle_level_ready(
                    update.character_id(),
                    update.client_id(),
                    &self.characters,
                    &self.entities,
                    &self.put_npc,
                    &mut self.npcs_em_cena,
                    messages,
                );
            }
            c::Message::CurStatus(_) => {
                PlayerService::handle_cur_status(
                    update.character_id(),
                    update.client_id(),
                    update.account_id(),
                    &mut self.characters,
                    &self.db,
                    &self.data_manager,
                    &self.game_data,
                    &self.guild_manager,
                    &mut self.mundo_enviado,
                    &self.burst,
                    messages,
                );
            }
            c::Message::ChatMessagePublic(msg) => {
                ChatService::handle_chat_public(
                    update.character_id(),
                    update.client_id(),
                    msg,
                    &mut self.characters,
                    &mut self.chat_timestamps,
                    &self.party_service,
                    &self.guild_manager,
                    &self.restrictions,
                    messages,
                );
            }
            c::Message::ShowDialog(dialog) => {
                DialogService::handle_show_dialog(
                    update.character_id(),
                    update.client_id(),
                    dialog,
                    &self.entities,
                    &self.game_data,
                    messages,
                );
            }
            c::Message::DialogSelect(sel) => {
                DialogService::handle_dialog_select(
                    update.character_id(),
                    update.client_id(),
                    sel,
                    &mut self.characters,
                    &self.teleport_service,
                    &self.db,
                    &mut self.npcs_em_cena,
                    &mut self.mundo_enviado,
                    messages,
                );
            }
            c::Message::BuySell(buy_sell) => {
                ItemService::handle_buy_sell(
                    update.character_id(),
                    update.client_id(),
                    buy_sell,
                    &mut self.characters,
                    &self.db,
                    messages,
                );
            }
            c::Message::UseEquipmentItem(equip) => {
                ItemService::handle_use_equipment_item(
                    update.character_id(),
                    update.client_id(),
                    equip,
                    &mut self.characters,
                    &self.game_data,
                    messages,
                );
            }
            c::Message::MailRead(mail_read) => {
                MailService::handle_mail_read(
                    update.character_id(),
                    update.client_id(),
                    mail_read,
                    &mut self.characters,
                    &self.db,
                    messages,
                );
            }
            c::Message::MailPostman(postman) => {
                MailService::handle_mail_postman(
                    update.character_id(),
                    update.client_id(),
                    postman,
                    &mut self.characters,
                    &self.db,
                    messages,
                );
            }
            c::Message::WindPath(wind_path) => {
                EnvironmentService::handle_wind_path(
                    update.character_id(),
                    update.client_id(),
                    wind_path,
                    &self.windstream_service,
                    messages,
                );
            }
            _ => {}
        }
    }

    /// Tick de servidor: recalcula timers de ataque, respawn, AI, skills e efeitos
    pub fn update(&mut self, _messages: &mut Messages) {
        let now = Instant::now();

        // Atualiza SpawnEngine (respawns, patrulhas walker, ciclo temporário, expiração de rifts)
        self.spawn_engine.tick(now, &mut self.entities, &mut self.put_npc);

        // Atualiza SkillEngine (efeitos contínuos, DoTs, HoTs, correntes e timers de CC)
        self.skill_engine.tick(now, &mut self.characters, &mut self.entities);

        // Atualiza AI Engine (ciclo de decisão, auto-aggro, perseguição, habilidades de monstros)
        self.ai_engine.tick(now, &mut self.entities, &mut self.characters, _messages);

        // Limpa timers de ataque de alvos mortos
        self.attack_timers.retain(|_, (target_id, _)| {
            self.entities
                .iter()
                .find(|e| e.id() == *target_id)
                .map(|e| e.is_alive())
                .unwrap_or(false)
        });
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;

    fn make_test_db() -> Db {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        let db = Db { conn };
        db.init_schema().unwrap();
        db
    }

    #[test]
    fn streaming_espacial_calcula_entidades_dentro_e_fora_do_raio() {
        let db = make_test_db();

        let game_data = Arc::new(GameData::default());

        let mut state = State::new(db, game_data);
        let aqui = Coord::new(100.0, 100.0, 100.0);
        let mut messages = Messages::new();

        let (entraram, sairam) = SpatialService::atualiza_npcs_em_cena(
            1,
            1,
            aqui,
            &mut state.npcs_em_cena,
            &state.entities,
            &state.put_npc,
            &mut messages,
        );
        assert_eq!(sairam, 0);
        assert!(entraram <= state.entities.len());
    }
}
