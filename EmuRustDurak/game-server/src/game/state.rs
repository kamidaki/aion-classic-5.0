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

    /// Nome de conta desta sessao.
    ///
    /// Sai do token que o STS gravou. Sem token -- clientes de bancada que pulam o STS -- vale um
    /// sintetico pelo id do cliente, para a sessao nao morrer por causa disso.
    fn username_do_update(&self, update: &ClientUpdate) -> String {
        let token = update.session_token();
        if token.is_empty() {
            return format!("client_{}", update.client_id());
        }
        match self.db.lookup_session(token) {
            Ok(Some(name)) => {
                println!("INFO: session token resolved to username '{name}'");
                name
            }
            Ok(None) => {
                eprintln!("WARN: session token not found in DB, using synthetic username");
                format!("client_{}", update.client_id())
            }
            Err(e) => {
                eprintln!("ERROR: lookup_session: {e}");
                format!("client_{}", update.client_id())
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
                let username = self.username_do_update(&update);
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
                // E teste de bisseccao: com esses valores o pacote sai byte a byte igual ao
                // capturado, entao se o cliente aceitar com eles e recusar com os nossos, o
                // problema esta no dado (id, nivel, nome) e nao no formato.
                let usar_capturado = std::env::var("AION_PERSONAGEM_CAPTURADO").is_ok();
                let personagem = if usar_capturado {
                    println!("INFO: usando o personagem da captura (teste de bisseccao)");
                    lista_personagens::Personagem {
                        id: 0x2E0F_3384,
                        nome: "Durak".to_string(),
                        nivel: 60,
                        aparencia: None,
                    }
                } else {
                    lista_personagens::Personagem {
                        id: character.id(),
                        nome: character.name().clone(),
                        nivel: character.stats.level,
                        aparencia: persisted.aparencia.clone(),
                    }
                };

                // A conta pode ter mais de um personagem desde que dá para criar. O primeiro vem do
                // `load_or_create_character` acima -- e o que entra no estado do jogo -- e os
                // demais saem do banco.
                let mut personagens = vec![personagem];
                if !usar_capturado {
                    match self.db.personagens_da_conta(&username) {
                        Ok(todos) => {
                            for p in todos {
                                if p.id == character.id() {
                                    continue;
                                }
                                // Sem isso o personagem aparece na lista mas nao da para entrar
                                // com ele: o EnterWorld procura no estado e nao acha.
                                self.characters.insert(
                                    p.id,
                                    Character::from_persisted(&p, update.client_id()),
                                );
                                personagens.push(lista_personagens::Personagem {
                                    id: p.id,
                                    nome: p.name,
                                    nivel: p.level,
                                    aparencia: p.aparencia,
                                });
                            }
                        }
                        Err(e) => {
                            eprintln!("ERROR: personagens_da_conta({username}): {e}")
                        }
                    }
                }

                let lista = lista_personagens::ListaPersonagens::new(
                    update.chave_de_sessao(),
                    personagens,
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
            c::Message::CreateCharacter(pedido) => {
                let username = self.username_do_update(&update);
                let nome = pedido.nome.clone();

                let criado = match self
                    .db
                    .criar_personagem(&username, &nome, &pedido.aparencia)
                {
                    Ok(c) => c,
                    Err(e) => {
                        eprintln!("ERROR: criar_personagem({username}, {nome}): {e}");
                        return;
                    }
                };
                println!(
                    "INFO: personagem '{}' criado (id {}) para '{}'",
                    criado.name, criado.id, username
                );

                // O cliente entra no mundo direto depois de criar, sem pedir a lista de novo --
                // entao inserir no estado so quando a lista e montada chega tarde demais, e o
                // EnterWorld nao acha o personagem.
                self.characters.insert(
                    criado.id,
                    Character::from_persisted(&criado, update.client_id()),
                );

                messages.extend_direct(
                    update.client_id(),
                    [s::Message::CreateCharacter(s::CreateCharacter::new(
                        lista_personagens::Personagem {
                            id: criado.id,
                            nome: criado.name,
                            nivel: criado.level,
                            aparencia: criado.aparencia,
                        },
                    ))]
                    .map(ServerUpdate::new),
                );
            }
            c::Message::LevelReady(_) => {
                // O cliente avisa que terminou de carregar o mapa -- opcode 0x19 na 4.5, 0x09 na
                // 2.5. Sem personagem no estado nao ha o que aparecer, e derrubar a thread do jogo
                // aqui tiraria todo mundo do ar.
                let Some(new_character) =
                    self.characters.get(&update.character_id())
                else {
                    println!(
                        "WARNING: LevelReady para personagem {} que nao esta no estado; ignorando",
                        update.character_id()
                    );
                    return;
                };

                // O S_PUT_USER e o que faz o personagem aparecer no mundo. O da captura tem 481
                // bytes e o do POC, que e da 2.5, nao chega perto -- entao aqui vai o capturado,
                // com o nosso id por cima. A posicao dentro dele ja e a certa: o ponto de entrada
                // de `mundo` foi tirado desta mesma sessao.
                //
                // Depois dele vem o S_INVISIBLE_LEVEL, que fecha o spawn. Sem ele o personagem
                // aparece piscando: o cliente o desenha, mas nao o considera dentro do mundo -- a
                // UI nao responde e so o teclado anda. Na captura esse pacote traz [id][40 00 01],
                // que e o que o POC chama de `start`; o `finish` ([00 00 00]) e que estava sendo
                // mandado aqui, e e o contrario do que o servidor real faz.
                // Sao oito pacotes, na ordem da captura -- ver `capturado`. O S_PUT_USER e o
                // S_INVISIBLE_LEVEL sozinhos deixam o personagem piscando.
                use super::message::capturado as cap;
                let id = new_character.id();
                // O nome tambem: sem escrever por cima, todo mundo entra no mundo como `Kimmie`,
                // que e quem estava logada na captura de onde o PUT_USER saiu.
                let nome_no_mundo = new_character.name().clone();
                let aparencia = new_character.aparencia.clone();
                let bruto = |opcode, payload: Vec<u8>| {
                    ServerUpdate::new(s::Message::Bruto(s::Bruto::new(opcode, payload)))
                };
                messages.extend_direct(
                    update.client_id(),
                    [
                        bruto(cap::INVENCIVEL_ANTES_OPCODE, cap::INVENCIVEL_ANTES.to_vec()),
                        bruto(cap::ZONA_OPCODE, cap::ZONA.to_vec()),
                        bruto(cap::PUT_USER_OPCODE, {
                            // A ordem importa: a aparencia escreve em offsets fixos, e o nome muda
                            // o tamanho do pacote e desloca tudo o que vem depois dele.
                            let com_id =
                                cap::com_id_de_personagem(&cap::PUT_USER, 12, id);
                            let com_cara = match &aparencia {
                                Some(bloco) => {
                                    cap::com_aparencia_de_personagem(&com_id, bloco)
                                }
                                None => com_id,
                            };
                            cap::com_nome_de_personagem(
                                &com_cara,
                                cap::PUT_USER_NOME,
                                &nome_no_mundo,
                            )
                        }),
                        bruto(cap::INVENCIVEL_DEPOIS_OPCODE, cap::INVENCIVEL_DEPOIS.to_vec()),
                        ServerUpdate::new(s::Message::InvisibleLevel(
                            s::InvisibleLevel::start(id),
                        )),
                        bruto(cap::BUILDER_LEVEL_OPCODE, cap::BUILDER_LEVEL.to_vec()),
                        bruto(cap::STATUS_ANORMAL_OPCODE, cap::STATUS_ANORMAL.to_vec()),
                        bruto(
                            cap::PENALIDADE_DE_SKILL_OPCODE,
                            cap::PENALIDADE_DE_SKILL.to_vec(),
                        ),
                        bruto(
                            cap::ANIMACAO_OPCODE,
                            cap::com_id_de_personagem(&cap::ANIMACAO, 1, id),
                        ),
                        bruto(cap::CENA_DO_MUNDO_OPCODE, cap::CENA_DO_MUNDO.to_vec()),
                        // Vida e mana do personagem. Na captura sao dois pares de u32 -- valor
                        // atual e maximo -- e o formato do POC e o mesmo.
                        ServerUpdate::new(s::Message::HitPoint(s::HitPoint::new(
                            new_character.stats.hp.current(),
                            new_character.stats.hp.max(),
                        ))),
                    ],
                );

                if std::env::var("AION_PACOTES_25").is_err() {
                    return;
                }

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

                // Na captura o S_STATUS vem antes do S_WORLD. E ele que da ao cliente o proprio
                // personagem: sem ele o mapa carrega e nao ha ninguem para controlar. O do POC e
                // da 2.5 (312 bytes contra 396), entao aqui vai o capturado com o nosso id por
                // cima, ate ele ser decodificado campo a campo.
                use super::message::capturado as cap;
                messages.extend_direct(
                    update.client_id(),
                    [
                        s::Message::Bruto(s::Bruto::new(
                            cap::STATUS_OPCODE,
                            cap::com_id_de_personagem(&cap::STATUS, 0, character.id()),
                        )),
                        // O S_WORLD e o que poe o jogador no mapa, e ja foi conferido contra a
                        // captura.
                        s::Message::World(s::World::new(character.location())),
                        // Estes dois sao implementacao do POC e batem com a captura: o
                        // S_WORLD_INFO sai byte a byte igual ao pacote #100 da sessao real, e o
                        // S_CUR_STATUS tem 1 byte nos dois. O resto do que o POC mandava aqui e
                        // 2.5 e continua desligado, mais abaixo.
                        s::Message::WorldInfo(s::WorldInfo::new()),
                        s::Message::CurStatus(s::CurStatus::new()),
                    ]
                    .map(ServerUpdate::new),
                );

                // O resto e implementacao da 2.5 e nenhum bate de tamanho com a 4.5: S_STATUS sai
                // com 312 bytes contra 389 da captura, S_ADD_SKILL 376 contra 325,
                // S_LOAD_INVENTORY 1907 contra 3363. Com eles ligados o cliente carrega
                // Pandaemonium e crasha logo depois.
                //
                // Ficam atras de AION_PACOTES_25=1 ate cada um ser reescrito para o layout 4.5,
                // um de cada vez, conferindo o tamanho contra a captura. Na sessao real o
                // S_STATUS vem *antes* do S_WORLD, nao depois -- a ordem aqui ja esta corrigida.
                if std::env::var("AION_PACOTES_25").is_err() {
                    return;
                }

                println!("INFO: mandando tambem os pacotes 2.5 (AION_PACOTES_25)");
                messages.extend_direct(
                    update.client_id(),
                    [
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
