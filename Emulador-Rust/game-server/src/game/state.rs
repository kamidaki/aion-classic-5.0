use std::collections::HashMap;
use std::collections::HashSet;
use std::sync::Arc;

use crate::data_loader::GameData;
use crate::db::Db;

use super::character::Character;
use super::message::lista_personagens;
use super::mundo;
use super::data::gear::LootItem;
use super::data::{npc, ActionType};
use super::engine::Coord;
use super::entity::Entity;
use super::message::{client as c, server as s};
use super::{ClientUpdate, Messages, ServerUpdate};

/// Nome interno da classe no XML do cliente, e o da classe base de que ela herda skills.
///
/// O numero vem do bloco de criacao; os nomes sao os que o `client_skill_learns.xml` usa, que nao
/// sao os nomes de tela: gladiador e `BATTLEMASTER`, templario e `KNIGHT`, feiticeiro e `WIZARD`.
///
/// O par foi conferido contra a captura: um feiticeiro (classe 7) de nivel 11 recebeu 29 skills, e
/// `WIZARD` + `MAGE` + universais preve todas as 29.
fn classe_no_xml(classe: u32) -> (&'static str, &'static str) {
    match classe {
        0 => ("FIGHTER", "FIGHTER"),
        1 => ("BATTLEMASTER", "FIGHTER"),
        2 => ("KNIGHT", "FIGHTER"),
        3 => ("SCOUT", "SCOUT"),
        4 => ("ASSASSIN", "SCOUT"),
        5 => ("RANGER", "SCOUT"),
        6 => ("MAGE", "MAGE"),
        7 => ("WIZARD", "MAGE"),
        8 => ("ELEMENTALLIST", "MAGE"),
        9 => ("PRIEST", "PRIEST"),
        10 => ("CLERIC", "PRIEST"),
        11 => ("CHANTER", "PRIEST"),
        13 => ("GUNNER", "GUNNER"),
        // As classes de 4.7 em diante nao aparecem na criacao da 4.5. Sem nome, o personagem so
        // recebe as universais -- melhor que mandar skill de outra classe.
        _ => ("", ""),
    }
}

/// A classe cujo kit inicial o personagem recebe.
///
/// E a classe **especifica**, nao a base: assassino e ranger sao os dois SCOUT e recebem armaduras
/// diferentes -- `lt_torso_n_l1_assassin_1a` contra `lt_torso_n_l1_ranger_1a`. Conferido na
/// captura de 22/08/2026, que gravou a criacao de um assassino, um templario e um ranger.
///
/// Os nomes sao os do catalogo do cliente, e batem com os de `classe_no_xml`.
fn classe_do_kit(classe: u32) -> &'static str {
    match classe {
        1 => "BATTLEMASTER",
        2 => "KNIGHT",
        4 => "ASSASSIN",
        5 => "RANGER",
        7 => "WIZARD",
        8 => "ELEMENTALLIST",
        10 => "CLERIC",
        11 => "CHANTER",
        // As classes base (0, 3, 6, 9) nao aparecem na criacao da 4.5 -- o jogador escolhe a
        // classe final direto. As de 4.7 em diante nao existem aqui.
        _ => "",
    }
}

/// Ate onde o servidor manda NPC, em metros.
///
/// Existe porque mandar o mundo inteiro estoura o buffer de envio: 1008 NPCs a ~110 bytes dao uns
/// 110 KB contra os 64 KB do buffer, e o `PutNpc` entrava em panico no meio de um pacote --
/// derrubando a conexao com o cliente ja dentro do mundo.
///
/// Mas o limite nao e so pratico: e o que o servidor real faz. O cliente so recebe o que esta no
/// alcance de visao, e foi por isso que a captura trouxe 89 NPCs na entrada e o resto foi chegando
/// conforme a personagem andava. A 100 metros ficam ~155 NPCs, uns 17 KB.
///
/// Ajustavel com `AION_VISAO`.
const VISAO_PADRAO: f32 = 100.0;

/// Quanto o personagem precisa andar para o servidor recalcular quem esta em cena.
///
/// O cliente manda posicao a cada passo -- 1220 pacotes de movimento nos 22 minutos da captura --
/// e refazer a conta em todos seria varrer mil NPCs por passo sem nada mudar.
const PASSO_DO_STREAM: f32 = 20.0;

fn raio_de_visao() -> f32 {
    std::env::var("AION_VISAO")
        .ok()
        .and_then(|v| v.trim().parse().ok())
        .unwrap_or(VISAO_PADRAO)
}

/// Classe de quem nao tem bloco de criacao -- o personagem automatico, que sai do molde do Durak.
/// 11 e a da personagem capturada, que e o que o STATUS ja trazia.
const CLASSE_DO_MOLDE: u32 = 11;

pub struct State {
    characters: HashMap<u32, Character>,
    entities: Vec<Entity>,
    /// O `S_PUT_NPC` capturado de cada entidade, por id. Ver `data_loader::Spawn::payload`.
    put_npc: HashMap<u32, Vec<u8>>,
    /// Que NPCs cada personagem ja tem desenhados, e de onde a lista foi calculada.
    ///
    /// O cliente nao esquece um NPC sozinho: quem entrou em cena fica ate receber um
    /// `S_REMOVE_OBJECT`. Guardar o conjunto e o que permite mandar so a diferenca quando o
    /// personagem anda, em vez de reenviar tudo.
    npcs_em_cena: HashMap<u32, (HashSet<u32>, Coord)>,
    /// O bloco de entrada capturado, por posicao. Vazio a menos que `AION_BURST=1`.
    ///
    /// Instrumento de medicao -- ver `message::replay::burst_de_entrada`.
    burst: Vec<(u16, Vec<u8>)>,
    /// Quem ja recebeu a ordem de entrar no mundo nesta selecao de personagem.
    ///
    /// O `S_STATUS` + `S_WORLD` sai no primeiro `C_CUR_STATUS` e **so nele**. Na captura o
    /// servidor oficial manda o `S_WORLD` uma vez, antes do primeiro `C_CUR_STATUS` do cliente --
    /// nao e resposta a ele. Mandar de novo no segundo pedido reinicia o carregamento do mapa no
    /// meio, e o cliente nunca chega a mandar o `LevelReady`: fica preso na tela de carregamento.
    mundo_enviado: HashSet<u32>,
    pub windstream_service: crate::game::environment::WindstreamService,
    db: Db,
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

        // O mundo de verdade: NPCs nas posicoes que o servidor oficial usou. Ids de entidade tem o
        // bit alto ligado, como o do mosbear acima -- e o que o cliente 4.5 espera.
        let mut put_npc: HashMap<u32, Vec<u8>> = HashMap::new();
        for (i, sp) in game_data.spawns.iter().enumerate() {
            let id = 0x8000_0000 | (i as u32 + 1);
            entities.push(Entity::novo(
                id,
                Coord::new(sp.x, sp.y, sp.z),
                sp.npc_id,
                sp.nome_id,
            ));

            // O pacote capturado deste NPC, com o id de entidade trocado pelo nosso.
            let mut payload = sp.payload.clone();
            let off = crate::data_loader::OFFSET_ID_ENTIDADE;
            if payload.len() >= off + 4 {
                payload[off..off + 4].copy_from_slice(&id.to_le_bytes());
                put_npc.insert(id, payload);
            }
        }
        if !game_data.spawns.is_empty() {
            println!("INFO: {} NPCs no mundo", game_data.spawns.len());
        }

        Self {
            characters: HashMap::with_capacity(1000),
            entities,
            put_npc,
            npcs_em_cena: HashMap::new(),
            mundo_enviado: HashSet::new(),
            burst: if std::env::var("AION_BURST").is_ok() {
                let caminho = std::env::var("AION_REPLAY")
                    .unwrap_or_else(|_| "replay.bin".to_string());
                super::message::replay::burst_de_entrada(std::path::Path::new(&caminho))
            } else {
                Vec::new()
            },
            windstream_service: crate::game::environment::WindstreamService::new(),
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
            c.spawn_map_id(),
            c.heading(),
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

    /// Popula a cena de quem acabou de entrar no mundo, e diz quantos foram.
    fn povoa_cena(
        &mut self,
        character_id: u32,
        client_id: u16,
        aqui: Coord,
        messages: &mut Messages,
    ) {
        // Entrar no mundo e o caso em que ninguem esta em cena ainda.
        self.npcs_em_cena.remove(&character_id);
        let (enviados, _) =
            self.atualiza_npcs_em_cena(character_id, client_id, aqui, messages);
        println!(
            "INFO: {enviados} NPCs em cena de {} (raio {:.0}m)",
            self.entities.len(),
            raio_de_visao()
        );
    }

    /// Manda os NPCs que entraram no alcance e tira os que sairam.
    ///
    /// Devolve `(entraram, sairam)`. Chamado na entrada no mundo e a cada `PASSO_DO_STREAM` metros
    /// andados.
    fn atualiza_npcs_em_cena(
        &mut self,
        character_id: u32,
        client_id: u16,
        aqui: Coord,
        messages: &mut Messages,
    ) -> (usize, usize) {
        let raio = raio_de_visao();
        let perto: HashSet<u32> = self
            .entities
            .iter()
            .filter(|e| {
                let la = e.location();
                let dx = la.x() - aqui.x();
                let dy = la.y() - aqui.y();
                let dz = la.z() - aqui.z();
                dx * dx + dy * dy + dz * dz <= raio * raio
            })
            .map(|e| e.id())
            .collect();

        let em_cena = match self.npcs_em_cena.get(&character_id) {
            Some((c, _)) => c.clone(),
            None => HashSet::new(),
        };

        let entraram: Vec<u32> = perto.difference(&em_cena).copied().collect();
        let sairam: Vec<u32> = em_cena.difference(&perto).copied().collect();

        for id in &sairam {
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::RemoveObject(s::RemoveObject::new(*id))),
            );
        }
        for id in &entraram {
            let Some(entity) = self.entities.iter().find(|e| e.id() == *id) else {
                continue;
            };
            // O pacote capturado quando existe; o do POC so para o mob escrito a mao.
            let msg = match self.put_npc.get(id) {
                Some(p) => s::Message::Bruto(s::Bruto::new(
                    super::message::capturado::PUT_NPC_OPCODE,
                    p.clone(),
                )),
                None => s::Message::PutNpc(s::PutNpc::new(entity)),
            };
            messages.push_direct(client_id, ServerUpdate::new(msg));
        }

        let contagem = (entraram.len(), sairam.len());
        self.npcs_em_cena.insert(character_id, (perto, aqui));
        contagem
    }

    pub fn respond(&mut self, update: &ClientUpdate, messages: &mut Messages) {
        match &update.message() {
            c::Message::MoveNew(move_new) => {
                let character =
                    self.characters.get_mut(&update.character_id).unwrap();

                let s_move_new =
                    s::Message::MoveNew(move_new.calculate(character.id()));
                character.set_location(move_new.location());
                let aqui = *character.location();
                let id = character.id();

                messages
                    .push_others(update.client_id(), ServerUpdate::new(s_move_new));

                // NPC entra e sai de cena conforme o personagem anda. So recalcula depois de
                // PASSO_DO_STREAM metros -- ver a constante.
                let andou = match self.npcs_em_cena.get(&id) {
                    Some((_, de_onde)) => {
                        let dx = aqui.x() - de_onde.x();
                        let dy = aqui.y() - de_onde.y();
                        let dz = aqui.z() - de_onde.z();
                        dx * dx + dy * dy + dz * dz >= PASSO_DO_STREAM * PASSO_DO_STREAM
                    }
                    None => true,
                };
                if andou {
                    let (entraram, sairam) =
                        self.atualiza_npcs_em_cena(id, update.client_id(), aqui, messages);
                    if entraram + sairam > 0 {
                        println!("INFO: cena: +{entraram} -{sairam} NPCs");
                    }
                }
            }
            c::Message::UseSkill(use_skill) => {
                if !self.characters.contains_key(&update.character_id) {
                    return;
                }

                let character = self.characters.get_mut(&update.character_id).unwrap();
                let char_id = character.id();
                let is_self_or_aoe = use_skill.target_id == 0 || use_skill.target_id == char_id;

                if is_self_or_aoe {
                    // Self-buff ou skill utilitária/área
                    let eff = s::AbnormalEffect::new(use_skill.skill_id as u32, 30000, 1);
                    messages.push_direct(
                        update.client_id(),
                        ServerUpdate::new(s::Message::AbnormalStatus(s::AbnormalStatus::with_effects(
                            char_id,
                            vec![eff.clone()],
                        ))),
                    );
                    messages.push_others(
                        update.client_id(),
                        ServerUpdate::new(s::Message::AbnormalStatusOther(s::AbnormalStatusOther::with_effects(
                            char_id,
                            vec![eff],
                        ))),
                    );
                    messages.push_direct(
                        update.client_id(),
                        ServerUpdate::new(s::Message::SkillPenaltyStatusOther(s::SkillPenaltyStatusOther::new(
                            char_id,
                            use_skill.skill_id as u32,
                            5000,
                        ))),
                    );
                    let skill_effect = s::SkillEffect::new(char_id, 0, 1, 0);
                    messages.push_direct(
                        update.client_id(),
                        ServerUpdate::new(s::Message::SkillSucceded(s::SkillSucceded::new(
                            char_id,
                            char_id,
                            use_skill.skill_id as u32,
                            use_skill.skill_level as u8,
                            vec![skill_effect],
                        ))),
                    );
                } else if let Some(entity) = self.entities.iter_mut().find(|entity| {
                    entity.id() == use_skill.target_id && entity.is_alive()
                }) {
                    let hit = crate::game::engine::damage::CombatEngine::calculate_physical_hit(
                        character.stats.secondary.main_hand_attack,
                        1.5,
                        100,
                        character.stats.secondary.main_hand_accuracy,
                        100,
                        100,
                        100,
                        character.stats.secondary.main_hand_crit,
                        50,
                        1.5,
                    );
                    let damage = hit.damage.max(1);
                    let is_crit = if hit.ty == crate::game::engine::damage::Type::Critical { 1 } else { 0 };
                    entity.hp.update(-damage);

                    let eff = s::SkillEffect::new(entity.id(), -damage, 0, is_crit);
                    messages.broadcast.extend(
                        [
                            s::Message::UseSkill(s::UseSkill::new(
                                char_id,
                                use_skill.skill_id,
                                use_skill.skill_level,
                                use_skill.target_id,
                            )),
                            s::Message::SkillSucceded(s::SkillSucceded::new(
                                char_id,
                                use_skill.target_id,
                                use_skill.skill_id as u32,
                                use_skill.skill_level as u8,
                                vec![eff],
                            )),
                            s::Message::SkillPenaltyStatusOther(s::SkillPenaltyStatusOther::new(
                                char_id,
                                use_skill.skill_id as u32,
                                3000,
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
                                    char_id,
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
                        posicao: (mundo::X, mundo::Y, mundo::Z),
                    }
                } else {
                    lista_personagens::Personagem {
                        id: character.id(),
                        nome: character.name().clone(),
                        nivel: character.stats.level,
                        aparencia: persisted.aparencia.clone(),
                        posicao: {
                            let l = character.location();
                            (l.x(), l.y(), l.z())
                        },
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
                                    posicao: (p.x, p.y, p.z),
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
                            posicao: (criado.x, criado.y, criado.z),
                        },
                    ))]
                    .map(ServerUpdate::new),
                );
            }
            c::Message::DeleteCharacter(pedido) => {
                let username = self.username_do_update(&update);
                let ok = self
                    .db
                    .deletar_personagem(&username, pedido.character_id)
                    .unwrap_or(false);
                if ok {
                    self.characters.remove(&pedido.character_id);
                    println!(
                        "INFO: personagem (id {}) deletado da conta '{}'",
                        pedido.character_id, username
                    );
                }
                messages.extend_direct(
                    update.client_id(),
                    [s::Message::DeleteCharacter(s::DeleteCharacter::new(
                        if ok { pedido.character_id } else { 0 },
                        0,
                    ))]
                    .map(ServerUpdate::new),
                );
            }
            c::Message::EnterWorld(selecao) => {
                // Selecionou personagem: a proxima entrada no mundo vale de novo. Sem isto, sair
                // para a lista e voltar deixaria o cliente sem o S_WORLD.
                self.mundo_enviado.remove(&selecao.character_id);
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
                let spawn_map_id = new_character.spawn_map_id();
                let heading = new_character.heading();
                // O nome tambem: sem escrever por cima, todo mundo entra no mundo como `Kimmie`,
                // que e quem estava logada na captura de onde o PUT_USER saiu.
                let nome_no_mundo = new_character.name().clone();
                let (aqui_x, aqui_y, aqui_z) = {
                    let l = new_character.location();
                    (l.x(), l.y(), l.z())
                };
                let aparencia = new_character.aparencia.clone();
                let bruto = |opcode, payload: Vec<u8>| {
                    ServerUpdate::new(s::Message::Bruto(s::Bruto::new(opcode, payload)))
                };
                messages.extend_direct(
                    update.client_id(),
                    [
                        ServerUpdate::new(s::Message::WorldSceneStatus(
                            s::WorldSceneStatus::scene(0, 1),
                        )),
                        ServerUpdate::new(s::Message::RequestTeleport(
                            s::RequestTeleport::new(
                                1,
                                spawn_map_id,
                                0,
                                aqui_x,
                                aqui_y,
                                aqui_z,
                                heading,
                            ),
                        )),
                        bruto(cap::INVENCIVEL_ANTES_OPCODE, cap::INVENCIVEL_ANTES.to_vec()),
                        bruto(cap::ZONA_OPCODE, cap::ZONA.to_vec()),
                        bruto(cap::PUT_USER_OPCODE, {
                            // A ordem importa: a aparencia escreve em offsets fixos, e o nome muda
                            // o tamanho do pacote e desloca tudo o que vem depois dele.
                            let com_id =
                                cap::com_id_de_personagem(&cap::PUT_USER, 12, id);
                            // A posicao do corpo. O blob traz a da captura cravada, e sem trocar
                            // ela o personagem aparece onde a Kimmie estava -- 360 metros abaixo
                            // do chao, se o mapa for Sanctum.
                            let com_lugar = cap::com_posicao_de_personagem(
                                &com_id,
                                aqui_x,
                                aqui_y,
                                aqui_z,
                            );
                            let com_cara = match &aparencia {
                                Some(bloco) => {
                                    cap::com_aparencia_de_personagem(&com_lugar, bloco)
                                }
                                None => com_lugar,
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

                let class_skills = match new_character.class() {
                    1 => vec![1001, 1002, 1003, 1004],
                    2 => vec![1001, 1002, 1015, 1016],
                    4 => vec![2001, 2002, 2003, 2004],
                    5 => vec![2001, 2002, 2015, 2016],
                    7 => vec![3001, 3002, 3003, 3004],
                    8 => vec![3001, 3002, 3015, 3016],
                    10 => vec![4001, 4002, 4003, 4004],
                    11 => vec![4001, 4002, 4015, 4016],
                    _ => vec![1001, 1002, 1003],
                };
                messages.push_direct(
                    update.client_id(),
                    ServerUpdate::new(s::Message::AddSkill45(s::AddSkill45::new(
                        class_skills,
                        1700000000,
                    ))),
                );

                // Os NPCs do mundo, so os que estao perto. Ficavam atras do portao dos pacotes
                // 2.5 junto com o resto, e por isso nem o unico mob escrito a mao aparecia.
                // A chamada em si fica no fim do handler: ela pega `&mut self`, e
                // `new_character` e um emprestimo de `self.characters` que ainda esta em uso.
                let aqui = *new_character.location();
                let id_do_personagem = new_character.id();
                let new_character_clone = new_character.clone();

                if std::env::var("AION_PACOTES_25").is_err() {
                    self.povoa_cena(id_do_personagem, update.client_id(), aqui, messages);

                    // Sincroniza outros jogadores presentes no raio de visao (60m)
                    for other in self.characters.values() {
                        if other.id() == id_do_personagem {
                            continue;
                        }
                        let other_loc = other.location();
                        let dx = other_loc.x() - aqui.x();
                        let dy = other_loc.y() - aqui.y();
                        let dz = other_loc.z() - aqui.z();
                        if dx * dx + dy * dy + dz * dz <= 60.0 * 60.0 {
                            messages.push_direct(
                                update.client_id(),
                                ServerUpdate::new(s::Message::PutUser(s::PutUser::new(other))),
                            );
                            messages.push_direct(
                                other.client_id(),
                                ServerUpdate::new(s::Message::PutUser(s::PutUser::new(&new_character_clone))),
                            );
                        }
                    }
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

                self.povoa_cena(id_do_personagem, update.client_id(), aqui, messages);
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

                // O cliente pede status varias vezes enquanto carrega. A entrada no mundo sai uma
                // vez so -- ver `mundo_enviado`. Nas outras, so o S_CUR_STATUS.
                if !self.mundo_enviado.insert(update.character_id()) {
                    messages.extend_direct(
                        update.client_id(),
                        [ServerUpdate::new(s::Message::CurStatus(s::CurStatus::new()))],
                    );
                    return;
                }

                // Quem entrou: id, nome, nivel e classe. A classe sai do bloco de criacao,
                // no mesmo offset que o registro da lista usa.
                let id_na_bolsa = character.id();
                let nome_na_bolsa = character.name().clone();
                let nivel_na_bolsa = character.stats.level;
                let raca_na_bolsa = character
                    .aparencia
                    .as_ref()
                    .and_then(|b| {
                        let off = super::message::molde::campo::RACA
                            - super::message::molde::campo::NOME;
                        b.get(off..off + 4)
                    })
                    .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
                    .unwrap_or(1);
                let classe_na_bolsa = character
                    .aparencia
                    .as_ref()
                    .and_then(|b| {
                        let off = super::message::molde::campo::CLASSE
                            - super::message::molde::campo::NOME;
                        b.get(off..off + 4)
                    })
                    .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
                    .unwrap_or(CLASSE_DO_MOLDE);

                // Medicao: com AION_BURST, o bloco inteiro da captura sai no lugar do nosso, e
                // tambem no lugar das skills e da bolsa -- senao o cliente recebe cada coisa duas
                // vezes. E para responder se o que falta e quantidade de pacote; nao e solucao.
                let medindo = !self.burst.is_empty();
                let bruto_de_entrada = |(opcode, payload): (u16, Vec<u8>)| {
                    ServerUpdate::new(s::Message::Bruto(s::Bruto::new(opcode, payload)))
                };
                if medindo {
                    println!(
                        "INFO: AION_BURST: mandando os {} pacotes capturados da janela de entrada",
                        self.burst.len()
                    );
                    let chave = update.chave_de_sessao();
                    let id = update.character_id();
                    let lote: Vec<_> = self
                        .burst
                        .iter()
                        .map(|p| {
                            ServerUpdate::new(super::message::replay::para_esta_sessao(
                                p, chave, id,
                            ))
                        })
                        .collect();
                    messages.extend_direct(update.client_id(), lote);
                } else {
                    messages.extend_direct(
                        update.client_id(),
                        super::message::entrada::antes_do_mundo(update.character_id())
                            .into_iter()
                            .map(bruto_de_entrada)
                            .collect::<Vec<_>>(),
                    );
                }

                // Skills. Na captura elas vem aqui -- 22 pacotes entre #32 e #53, logo
                // depois da segunda senha e antes da bolsa --, nao depois do LevelReady, que era
                // onde o servidor as mandava. O conteudo sai do XML do proprio cliente, pela
                // classe e pelo nivel; a captura serviu para provar o formato e conferir a regra,
                // que acertou as 29 skills do feiticeiro gravado.
                let (classe, base) = classe_no_xml(classe_na_bolsa);
                let skills = self.game_data.skills_de(classe, base, nivel_na_bolsa);
                println!(
                    "INFO: {} skills para '{nome_na_bolsa}' (classe {classe_na_bolsa} = {}, nivel {nivel_na_bolsa})",
                    skills.len(),
                    if classe.is_empty() { "<sem nome>" } else { classe },
                );
                if !skills.is_empty() && !medindo {
                    let agora = std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map(|d| d.as_secs() as u32)
                        .unwrap_or(0);
                    messages.extend_direct(
                        update.client_id(),
                        [ServerUpdate::new(s::Message::AddSkill45(
                            s::AddSkill45::new(skills, agora),
                        ))],
                    );
                }

                // A bolsa, antes do S_STATUS -- e onde ela cai na captura, entre o
                // S_LOAD_ITEM_COOLTIME e o S_STATUS.
                //
                // O kit inicial e entregue aqui, e nao na criacao do personagem, por dois
                // motivos: a classe ja esta resolvida neste ponto, e quem foi criado antes desta
                // versao tambem recebe -- uma vez so, marcada no personagem.
                let grupo = classe_do_kit(classe_na_bolsa);
                if let Some(kit) = self.game_data.itens_iniciais.get(grupo) {
                    match self.db.garante_kit_inicial(id_na_bolsa, kit) {
                        Ok(true) => println!(
                            "INFO: kit inicial de {grupo} ({} itens) para '{nome_na_bolsa}'",
                            kit.len()
                        ),
                        Ok(false) => {}
                        Err(e) => {
                            eprintln!("ERROR: garante_kit_inicial({id_na_bolsa}): {e}")
                        }
                    }
                }
                // Bissecao do pacote de bolsa, porque a falha dele nao tem sintoma proprio: o
                // cliente para na tela de carregamento, que e o mesmo sintoma de meia duzia de
                // outras coisas. `off` nao manda nada; `simples` manda so o que nao se equipa.
                let modo_da_bolsa =
                    std::env::var("AION_BOLSA").unwrap_or_else(|_| "tudo".to_string());
                match self.db.itens_do_personagem(id_na_bolsa) {
                    _ if medindo || modo_da_bolsa == "off" => {
                        println!("INFO: bolsa desligada (AION_BOLSA=off)");
                    }
                    Ok(itens) if !itens.is_empty() => {
                        let bolsa: Vec<_> = itens
                            .into_iter()
                            .filter(|i| {
                                modo_da_bolsa != "simples"
                                    || self
                                        .game_data
                                        .items
                                        .get(&i.item_id)
                                        .map(|d| {
                                            matches!(d.slot, crate::data_loader::Slot::Nenhum)
                                        })
                                        .unwrap_or(true)
                            })
                            .map(|i| {
                                super::data::item::ItemInventario::novo(
                                    i.obj_id,
                                    i.item_id,
                                    i.quantidade,
                                    i.posicao,
                                    self.game_data.items.get(&i.item_id),
                                )
                            })
                            .collect();
                        println!(
                            "INFO: {} itens na bolsa de '{nome_na_bolsa}'",
                            bolsa.len()
                        );

                        // Em levas de dez, como na captura, e uma leva vazia para fechar. Sem ela
                        // o cliente fica esperando o resto da bolsa.
                        let mut levas: Vec<ServerUpdate> = bolsa
                            .chunks(s::CarregaInventario45::POR_LEVA)
                            .enumerate()
                            .map(|(n, pedaco)| {
                                ServerUpdate::new(s::Message::CarregaInventario45(
                                    s::CarregaInventario45::leva(n == 0, pedaco.to_vec()),
                                ))
                            })
                            .collect();
                        levas.push(ServerUpdate::new(s::Message::CarregaInventario45(
                            s::CarregaInventario45::fim(),
                        )));
                        messages.extend_direct(update.client_id(), levas);
                    }
                    Ok(_) => {}
                    Err(e) => {
                        eprintln!("ERROR: itens_do_personagem({id_na_bolsa}): {e}")
                    }
                }

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
                            {
                                // Nivel e classe por cima do capturado -- sem isso a ficha mostra
                                // a personagem da captura, nivel 3 e Chanter, seja quem for que
                                // entrou. A classe sai do bloco de criacao, no mesmo offset que o
                                // registro da lista usa.
                                let classe = character
                                    .aparencia
                                    .as_ref()
                                    .and_then(|b| {
                                        let off = super::message::molde::campo::CLASSE
                                            - super::message::molde::campo::NOME;
                                        b.get(off..off + 4)
                                    })
                                    .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
                                    .unwrap_or(CLASSE_DO_MOLDE);
                                cap::com_ficha_de_personagem(
                                    &cap::com_id_de_personagem(
                                        &cap::STATUS,
                                        0,
                                        character.id(),
                                    ),
                                    character.stats.level,
                                    classe,
                                )
                            },
                        )),
                        // O S_WORLD e o que poe o jogador no mapa, e ja foi conferido contra a
                        // captura.
                        // O mapa vem da raca do personagem, e tem que ser o mesmo que o
                        // registro da lista declarou -- e por aquele que o cliente pre-carrega o
                        // cenario. Mandar um elyos para Pandaemonium e o que fazia o jogador ver
                        // a capital errada.
                        s::Message::World(s::World::new(
                            character.location(),
                            mundo::ponto_de_entrada(raca_na_bolsa),
                        )),
                        // Estes dois sao implementacao do POC e batem com a captura: o
                        // S_WORLD_INFO sai byte a byte igual ao pacote #100 da sessao real, e o
                        // S_CUR_STATUS tem 1 byte nos dois. O resto do que o POC mandava aqui e
                        // 2.5 e continua desligado, mais abaixo.
                        s::Message::WorldInfo(s::WorldInfo::new()),
                        s::Message::CurStatus(s::CurStatus::new()),
                    ]
                    .map(ServerUpdate::new),
                );

                // O resto do bloco: armazem, correio, macros, filtros de chat. Na captura estao
                // espalhados dos dois lados do S_WORLD; o que o cliente cobra e a presenca, e o
                // S_WORLD -- que tem lugar fixo -- ja foi.
                if !medindo {
                    messages.extend_direct(
                        update.client_id(),
                        super::message::entrada::depois_do_mundo(
                            update.character_id(),
                            game_time,
                        )
                        .into_iter()
                        .map(bruto_de_entrada)
                        .collect::<Vec<_>>(),
                    );
                }

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
            c::Message::ChatMessagePublic(chat) => {
                let Some(character) = self.characters.get_mut(&update.character_id()) else {
                    return;
                };
                let text = chat.message.trim();
                println!("[CHAT:{}] {}", character.name(), text);

                if let Some(cmd) = crate::game::social::GmCommand::parse(text) {
                    match cmd {
                        crate::game::social::GmCommand::Goto { destination } => {
                            if let Some((map_id, x, y, z)) = crate::game::social::resolve_goto_location(&destination) {
                                println!("INFO: Teleporting {} via .goto {} to map {} ({:.1}, {:.1}, {:.1})", character.name(), destination, map_id, x, y, z);
                                character.set_location(Coord::new(x, y, z));
                                character.set_spawn_map_id(map_id);
                                let char_id = character.id();
                                let loc = *character.location();
                                messages.push_direct(
                                    update.client_id(),
                                    ServerUpdate::new(s::Message::RequestTeleport(s::RequestTeleport::new(
                                        1,
                                        map_id,
                                        0,
                                        x,
                                        y,
                                        z,
                                        0,
                                    ))),
                                );
                                self.povoa_cena(char_id, update.client_id(), loc, messages);
                            }
                        }
                        crate::game::social::GmCommand::SetLevel { level } => {
                            character.stats.level = level;
                            println!("INFO: SetLevel {} for {}", level, character.name());
                        }
                        crate::game::social::GmCommand::Teleport { map_id, x, y, z } => {
                            println!("INFO: Teleporting {} to map {} ({:.1}, {:.1}, {:.1})", character.name(), map_id, x, y, z);
                            character.set_location(Coord::new(x, y, z));
                            character.set_spawn_map_id(map_id);
                            let char_id = character.id();
                            let loc = *character.location();
                            messages.push_direct(
                                update.client_id(),
                                ServerUpdate::new(s::Message::RequestTeleport(s::RequestTeleport::new(
                                    1,
                                    map_id,
                                    0,
                                    x,
                                    y,
                                    z,
                                    0,
                                ))),
                            );
                            self.povoa_cena(char_id, update.client_id(), loc, messages);
                        }
                        crate::game::social::GmCommand::Spawn { npc_id } => {
                            println!("INFO: GM Spawn NPC {} near {}", npc_id, character.name());
                        }
                        _ => (),
                    }
                }
            }
            c::Message::ShowDialog(dialog) => {
                println!("INFO: Player {} opened dialog with target {} (dialog_id: {})", update.character_id(), dialog.target_id, dialog.dialog_id);
                let dialog_id = if dialog.dialog_id == 0 { 10 } else { dialog.dialog_id };
                messages.push_direct(
                    update.client_id(),
                    ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                        dialog.target_id,
                        dialog_id,
                        0,
                    ))),
                );
            }
            c::Message::DialogSelect(sel) => {
                println!("INFO: Player {} selected dialog option {} for target {} (quest: {})", update.character_id(), sel.dialog_id, sel.target_id, sel.quest_id);
                messages.push_direct(
                    update.client_id(),
                    ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                        sel.target_id,
                        sel.dialog_id,
                        sel.quest_id,
                    ))),
                );
            }
            c::Message::MoveNew(ref move_new) => {
                if let Some(character) = self.characters.get_mut(&update.character_id()) {
                    character.set_location(move_new.location());
                    let s_move = move_new.calculate(character.id());
                    messages.push_others(
                        update.client_id(),
                        ServerUpdate::new(s::Message::MoveNew(s_move)),
                    );
                }
            }
            c::Message::WindPath(wind_path) => {
                println!(
                    "INFO: Player {} WindPath request (stream_id: {}, action: {})",
                    update.character_id(),
                    wind_path.windstream_id,
                    wind_path.action
                );
                let char_id = update.character_id();
                if wind_path.action == 1 {
                    // Entrar na corrente
                    let waypoints = self
                        .windstream_service
                        .get_waypoints(wind_path.windstream_id)
                        .unwrap_or_else(|| {
                            vec![
                                (1300.0, 1400.0, 300.0),
                                (1350.0, 1450.0, 320.0),
                                (1400.0, 1500.0, 310.0),
                                (1450.0, 1550.0, 290.0),
                            ]
                        });
                    let duration_ms = (waypoints.len() as f32) * 2000.0;
                    messages.extend_direct(
                        update.client_id(),
                        [
                            ServerUpdate::new(s::Message::WindPathResult(s::WindPathResult::new(
                                char_id,
                                wind_path.windstream_id,
                                waypoints,
                                duration_ms,
                            ))),
                            ServerUpdate::new(s::Message::WindStateInfo(s::WindStateInfo::new(
                                char_id,
                                wind_path.windstream_id,
                                1, // dentro
                                22.0,
                            ))),
                        ],
                    );
                } else {
                    // Sair da corrente
                    messages.push_direct(
                        update.client_id(),
                        ServerUpdate::new(s::Message::WindStateInfo(s::WindStateInfo::new(
                            char_id,
                            wind_path.windstream_id,
                            0, // fora
                            0.0,
                        ))),
                    );
                }
            }
            c::Message::PathFly(path_fly) => {
                if let Some(character) = self.characters.get_mut(&update.character_id()) {
                    character.set_location(Coord::new(path_fly.x, path_fly.y, path_fly.z));
                }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn streaming_espacial_calcula_entidades_dentro_e_fora_do_raio() {
        let db = Db::open(":memory:").unwrap();
        let game_data = Arc::new(GameData {
            spawns: vec![
                crate::data_loader::Spawn {
                    mapa: 120010000,
                    x: 100.0,
                    y: 100.0,
                    z: 0.0,
                    npc_id: 210001,
                    nome_id: 210001,
                    payload: vec![0u8; 32],
                },
                crate::data_loader::Spawn {
                    mapa: 120010000,
                    x: 500.0,
                    y: 500.0,
                    z: 0.0,
                    npc_id: 210002,
                    nome_id: 210002,
                    payload: vec![0u8; 32],
                },
            ],
            npcs: HashMap::new(),
            items: HashMap::new(),
            aprendizado: Vec::new(),
            skill_no_alvo: HashMap::new(),
            itens_iniciais: HashMap::new(),
        });

        let mut state = State::new(db, game_data);
        let mut messages = Messages::new();

        // Personagem entra perto do primeiro NPC (a 10m dele)
        let (entraram, sairam) = state.atualiza_npcs_em_cena(1, 1, Coord::new(105.0, 100.0, 0.0), &mut messages);
        assert_eq!(entraram, 1, "Apenas o NPC próximo (100, 100) deve entrar na cena");
        assert_eq!(sairam, 0, "Nenhum NPC deve sair na primeira inserção");

        // Personagem anda para perto do segundo NPC (a 500, 500)
        let (entraram2, sairam2) = state.atualiza_npcs_em_cena(1, 1, Coord::new(505.0, 500.0, 0.0), &mut messages);
        assert_eq!(entraram2, 1, "O segundo NPC deve entrar na cena");
        assert_eq!(sairam2, 1, "O primeiro NPC deve sair da cena por estar fora do raio");
    }
}
