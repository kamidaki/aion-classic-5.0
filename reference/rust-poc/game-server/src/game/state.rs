use std::collections::HashMap;
use std::sync::Arc;

use crate::data_loader::GameData;
use crate::db::Db;

use super::character::Character;
use super::message::lista_personagens;
use super::data::gear::LootItem;
use super::data::{npc, ActionType};
use super::engine::Coord;
use super::entity::Entity;
use super::message::{client as c, server as s};
use super::{ClientUpdate, Messages, ServerUpdate};

pub struct State {
    characters: HashMap<u32, Character>,
    entities: Vec<Entity>,
    db: Db,
    #[allow(dead_code)]
    game_data: Arc<GameData>,
}

impl State {
    pub fn new(db: Db, game_data: Arc<GameData>) -> Self {
        let mut entities = Vec::with_capacity(1000);

        let mosbear = Entity::new(
            2147586830,
            Coord::new(1816., 589., 256.),
            npc::Id::StarvedMosbear,
            npc::Name::StarvedMosbear,
        );
        if let Some(def) = game_data.npcs.get(&(npc::Id::StarvedMosbear as u32)) {
            println!(
                "INFO: spawned entity {} (id {}) -> catalog name: {}",
                mosbear.id(),
                npc::Id::StarvedMosbear as u32,
                def.name
            );
        }
        entities.push(mosbear);

        Self {
            characters: HashMap::with_capacity(1000),
            entities,
            db,
            game_data,
        }
    }

    /// Save all in-memory character state to the database.
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
            c.stats.level,
            c.stats.exp,
            c.stats.hp.current(),
            c.stats.mp.current(),
        ) {
            eprintln!("ERROR: failed to persist character {}: {e}", c.id());
        }
    }

    /// Remove all characters owned by a disconnected client and persist their
    /// final state. Called from the game loop after the sender channel for
    /// `client_id` has been dropped.
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

                // Drop aggro from any mob targeting this character.
                for entity in &mut self.entities {
                    if entity.target_id() == Some(character.id()) {
                        entity.clear_target();
                    }
                }
            }
        }
    }

    pub fn respond(&mut self, update: &ClientUpdate, messages: &mut Messages) {
        match &update.message() {
            c::Message::MoveNew(move_new) => {
                let character =
                    self.characters.get_mut(&update.character_id).unwrap();

                let s_move_new =
                    s::Message::MoveNew(move_new.calculate(character.id()));
                character.set_location(move_new.location());

                messages
                    .push_others(update.client_id(), ServerUpdate::new(s_move_new));
            }
            c::Message::UseSkill(use_skill) => {
                let character =
                    self.characters.get_mut(&update.character_id).unwrap();

                if let Some(entity) = self.entities.iter_mut().find(|entity| {
                    entity.id() == use_skill.target_id && entity.is_alive()
                }) {
                    let damage = 250;
                    entity.hp.update(-damage);
                    messages.broadcast.extend(
                        [
                            s::Message::UseSkill(s::UseSkill::new(
                                character.id(),
                                use_skill.skill_id,
                                use_skill.skill_level,
                                use_skill.target_id,
                            )),
                            s::Message::SkillSucceded(s::SkillSucceded::new(
                                character.id(),
                                use_skill.target_id,
                                use_skill.skill_id,
                                use_skill.skill_level,
                                0,
                                vec![super::engine::damage::Hit::new(
                                    damage,
                                    super::engine::damage::Type::MainHand,
                                )],
                            )),
                            s::Message::HitPointOther(s::HitPointOther::new(
                                entity.id(),
                                entity.hp.percent(),
                            )),
                        ]
                        .map(ServerUpdate::new),
                    );

                    if entity.is_dead() {
                        messages.broadcast.extend(
                            [
                                s::Message::Action(s::Action::new(
                                    entity.id(),
                                    ActionType::Die,
                                    character.stats.move_speed,
                                    character.id(),
                                )),
                                s::Message::Loot(s::Loot::new(entity.id(), 0)),
                            ]
                            .map(ServerUpdate::new),
                        );
                    }
                }
            }
            c::Message::Attack(attack) => {
                if let Some(entity) = self.entities.iter_mut().find(|entity| {
                    entity.id() == attack.target_id && entity.is_alive()
                }) {
                    // Calculate the client attack and broadcast it
                    let character = self
                        .characters
                        .get_mut(&update.character_id())
                        .unwrap();
                    let hits = character.attack(entity);
                    let s_hit_point_other =
                        s::HitPointOther::new(entity.id(), entity.hp.percent());

                    messages.broadcast.extend(
                        [
                            s::Message::Attack(s::Attack::new(
                                entity.id(),
                                character.id(),
                                0,
                                hits,
                            )),
                            s::Message::HitPointOther(s_hit_point_other),
                        ]
                        .map(ServerUpdate::new),
                    );

                    if entity.is_dead() {
                        messages.broadcast.extend(
                            [
                                s::Message::Action(s::Action::new(
                                    entity.id(),
                                    ActionType::Die,
                                    character.stats.move_speed,
                                    character.id(),
                                )),
                                s::Message::Loot(s::Loot::new(entity.id(), 0)),
                            ]
                            .map(ServerUpdate::new),
                        );
                    }

                    // Gain aggro if mob is not fighting
                    if entity.target_id().is_none() {
                        let target = entity.set_taget(character.id());

                        messages.broadcast.extend(
                            [
                                s::Message::NpcChangedTarget(target),
                                s::Message::Action(s::Action::new(
                                    entity.id(),
                                    ActionType::EntityDrawWeapon,
                                    character.stats.move_speed,
                                    character.id(),
                                )),
                                s::Message::Action(s::Action::new(
                                    entity.id(),
                                    ActionType::Attack,
                                    character.stats.move_speed,
                                    character.id(),
                                )),
                            ]
                            .map(ServerUpdate::new),
                        );
                    }
                }
            }
            c::Message::ChangeTarget(change_target) => {
                if let Some(entity) = self
                    .entities
                    .iter()
                    .find(|entity| entity.id() == change_target.target_id)
                {
                    messages.broadcast.push(ServerUpdate::new(
                        s::Message::TargetInfo(s::TargetInfo::new(
                            change_target.target_id,
                            entity.level(),
                            entity.hp.current(),
                            entity.hp.max(),
                        )),
                    ));
                }
            }
            c::Message::Action(action) => {
                let character =
                    self.characters.get_mut(&update.character_id).unwrap();

                messages
                    .broadcast
                    .push(ServerUpdate::new(s::Message::Action(
                        s::Action::new(
                            character.id(),
                            action.ty,
                            character.stats.move_speed,
                            0,
                        ),
                    )));
            }
            c::Message::Loot(msg) => match msg.action {
                c::LootAction::Start => {
                    let character =
                        self.characters.get_mut(&update.character_id).unwrap();

                    messages.broadcast.push(ServerUpdate::new(
                        s::Message::Action(s::Action::new(
                            character.id(),
                            ActionType::Loot,
                            character.stats.move_speed,
                            msg.entity_id,
                        )),
                    ));

                    messages.extend_direct(
                        update.client_id(),
                        [
                            s::Message::LootItemlist(s::LootItemlist::new(
                                msg.entity_id,
                                vec![LootItem::new(0x098975E6, 1)],
                            )),
                            s::Message::Loot(s::Loot::new(msg.entity_id, 2)),
                        ]
                        .map(ServerUpdate::new),
                    );
                }
                c::LootAction::Stop => {}
            },
            c::Message::LootItem(msg) => {
                let character =
                    self.characters.get_mut(&update.character_id).unwrap();

                messages.extend_direct(
                    update.client_id(),
                    [
                        s::Message::ChangeItemDesc(s::ChangeItemDesc::new()),
                        s::Message::Action(s::Action::new(
                            character.id(),
                            ActionType::EndLoot,
                            character.stats.move_speed,
                            msg.entity_id,
                        )),
                        s::Message::Loot(s::Loot::new(msg.entity_id, 3)),
                    ]
                    .map(ServerUpdate::new),
                );
            }
            c::Message::CharacterList(_) => {
                // Resolve the real username via the session token STS
                // persisted when issuing RequestGameToken. Fall back to a
                // synthetic username keyed by client_id so bench clients that
                // skip STS still work.
                let token = update.session_token();
                let username = if token.is_empty() {
                    format!("client_{}", update.client_id())
                } else {
                    match self.db.lookup_session(token) {
                        Ok(Some(name)) => {
                            println!(
                                "INFO: session token resolved to username '{name}'"
                            );
                            name
                        }
                        Ok(None) => {
                            eprintln!(
                                "WARN: session token not found in DB, using synthetic username"
                            );
                            format!("client_{}", update.client_id())
                        }
                        Err(e) => {
                            eprintln!("ERROR: lookup_session: {e}");
                            format!("client_{}", update.client_id())
                        }
                    }
                };
                let persisted = match self
                    .db
                    .load_or_create_character(&username)
                {
                    Ok(p) => p,
                    Err(e) => {
                        eprintln!(
                            "ERROR: db load_or_create_character({username}): {e}"
                        );
                        return;
                    }
                };
                let character =
                    Character::from_persisted(&persisted, update.client_id());

                // Layout 4.5. A implementacao antiga (s::CharacterList) e da 2.5 e faz o cliente
                // 4.5 crashar -- ver game::message::lista_personagens.
                // AION_PERSONAGEM_CAPTURADO=1 manda os valores exatos do personagem da captura.
                // E teste de bisseccao: o serializador reproduz o registro capturado byte a byte,
                // entao se o cliente aceitar com estes valores e recusar com os nossos, o problema
                // esta no dado (id, nivel, nome) e nao no formato.
                let usar_capturado = std::env::var("AION_PERSONAGEM_CAPTURADO").is_ok();
                let personagem = if usar_capturado {
                    println!("INFO: usando o personagem da captura (teste de bisseccao)");
                    lista_personagens::Personagem {
                        id: 0x2E0F_3384,
                        nome: "Durak".to_string(),
                        nivel: 60,
                        ultimo_login: true,
                    }
                } else {
                    lista_personagens::Personagem {
                        id: character.id(),
                        nome: character.name().clone(),
                        nivel: character.stats.level,
                        ultimo_login: true,
                    }
                };

                let lista = lista_personagens::ListaPersonagens::new(
                    update.chave_de_sessao(),
                    vec![personagem],
                );

                // Sao dois pacotes, nao um. Na captura o servidor manda primeiro uma lista vazia
                // (contagem zero, 11 bytes de payload) e so depois a lista de verdade. Mandando so
                // a segunda, o cliente fecha a conexao.
                let vazia = lista_personagens::ListaPersonagens::new(
                    update.chave_de_sessao(),
                    Vec::new(),
                );

                messages.extend_direct(
                    update.client_id(),
                    [
                        s::Message::ListaPersonagens45(s::ListaPersonagens45(vazia)),
                        s::Message::ListaPersonagens45(s::ListaPersonagens45(lista)),
                    ]
                    .map(ServerUpdate::new),
                );
                self.characters.insert(character.id(), character);
            }
            c::Message::LevelReady(_) => {
                let new_character =
                    self.characters.get(&update.character_id()).unwrap();

                // Load logging in character for all players
                messages.broadcast.extend(
                    [
                        s::Message::PutUser(s::PutUser::new(&new_character)),
                        s::Message::InvisibleLevel(s::InvisibleLevel::finish(
                            new_character.id(),
                        )),
                    ]
                    .map(ServerUpdate::new),
                );

                // Load all exisiting players for logging in character
                for character in &mut self.characters.values() {
                    // Skip ourselves
                    if character.id() == new_character.id() {
                        continue;
                    }

                    messages.extend_direct(
                        update.client_id(),
                        [
                            s::Message::PutUser(s::PutUser::new(&character)),
                            s::Message::InvisibleLevel(
                                s::InvisibleLevel::finish(character.id()),
                            ),
                        ]
                        .map(ServerUpdate::new),
                    );
                }

                // Load all entities for logging in player
                for entity in &self.entities {
                    messages.push_direct(
                        update.client_id(),
                        ServerUpdate::new(s::Message::PutNpc(s::PutNpc::new(entity))),
                    );
                }
            }
            c::Message::CurStatus(_) => {
                // O cliente pode pedir status antes de existir personagem no estado -- acontece,
                // por exemplo, quando a lista de personagens vem do replay e nao passou pelo
                // caminho que popula o estado. Derrubar a thread do jogo por causa disso tira
                // todos os jogadores do ar, entao aqui so ignoramos o pedido.
                let Some(character) = self.characters.get_mut(&update.character_id()) else {
                    println!(
                        "WARNING: CurStatus para personagem {} que nao esta no estado; ignorando",
                        update.character_id()
                    );
                    return;
                };

                let game_time = 148641933;
                messages.extend_direct(
                    update.client_id(),
                    [
                        // Most important packet
                        s::Message::World(s::World::new(character.location())),
                        // Required
                        s::Message::Status(s::Status::new(&character, game_time)),
                        s::Message::WorldInfo(s::WorldInfo::new()),
                        s::Message::CurStatus(s::CurStatus::new()),
                        s::Message::AddSkill(s::AddSkill::new(
                            character.skills.clone(),
                        )),
                        s::Message::LoadInventory(s::LoadInventory::start(
                            character.items.values().cloned().collect(),
                        )),
                        s::Message::LoadInventory(s::LoadInventory::end()),
                    ]
                        .map(ServerUpdate::new),
                    );
            }
            _ => (),
        }
    }

    pub fn update(&mut self, messages: &mut Messages) {
        // Run update for all entities
        for entity in &mut self.entities {
            if entity.hp.current() <= 0 {
                continue;
            }

            let target_id = match entity.target_id() {
                Some(id) => id,
                None => continue,
            };

            let target = self.characters.get_mut(&target_id).unwrap();

            match entity.attack(target) {
                Some(hits) => {
                    let attack =
                        s::Attack::new(target.id(), entity.id(), 0, hits);
                    messages.broadcast.extend(
                        [
                            s::Message::Attack(attack),
                            s::Message::HitPointOther(s::HitPointOther::new(
                                target.id(),
                                target.stats.hp.percent(),
                            )),
                        ]
                        .map(ServerUpdate::new),
                    );
                    messages.push_direct(
                        target.client_id(),
                        ServerUpdate::new(s::Message::HitPoint(s::HitPoint::new(
                            target.stats.hp.current(),
                            target.stats.hp.max(),
                        ))),
                    )
                }
                None => continue,
            };
        }
    }
}
