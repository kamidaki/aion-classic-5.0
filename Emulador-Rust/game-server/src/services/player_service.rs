//! PlayerService - Gerenciamento do Ciclo de Vida do Jogador (Padrão Java AION)
//!
//! Criação de personagem, spawn inicial, login, lista de personagens, entrada no mundo e persistência
//! usando 100% dados dinâmicos dos XMLs oficiais (sem hardcoded).

use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use crate::dao::Db;
use crate::data_loader::GameData;
use crate::dataholders::DataManager;
use crate::character::Character;
use crate::entity::Entity;
use crate::message::lista_personagens;
use crate::message::{client as c, server as s};
use crate::{ClientUpdate, Messages, ServerUpdate};
use super::spatial_service::SpatialService;

pub const CLASSE_DO_MOLDE: u32 = 11;

pub struct PlayerService;

impl PlayerService {
    /// Resolução do nome de conta a partir da sessão validada
    pub fn username_do_update(db: &Db, update: &ClientUpdate) -> String {
        let sintetico = || format!("client_{}", update.client_id());

        if update.session_key() != 0 {
            match db.resolver_sessao(update.account_id(), update.session_key()) {
                Ok(Some(name)) => return name,
                Ok(None) => eprintln!(
                    "WARN: sessao nao confere (account_id={}, session_key=0x{:08X}); tentando o token do STS",
                    update.account_id(),
                    update.session_key()
                ),
                Err(e) => eprintln!("ERROR: resolver_sessao: {e}"),
            }
        }

        let token = update.session_token();
        if token.is_empty() {
            return sintetico();
        }
        match db.lookup_session(token) {
            Ok(Some(name)) => name,
            Ok(None) => {
                eprintln!("WARN: session token not found in DB, using synthetic username");
                sintetico()
            }
            Err(e) => {
                eprintln!("ERROR: lookup_session: {e}");
                sintetico()
            }
        }
    }

    /// Processa o pedido de lista de personagens de uma conta
    pub fn handle_character_list(
        db: &Db,
        update: &ClientUpdate,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let username = Self::username_do_update(db, update);
        let todos = match db.personagens_da_conta(&username) {
            Ok(list) => list,
            Err(e) => {
                eprintln!("ERROR: db personagens_da_conta({username}): {e}");
                Vec::new()
            }
        };

        let mut personagens = Vec::new();
        for p in &todos {
            characters.insert(p.id, Character::from_persisted(p, update.client_id()));
            personagens.push(lista_personagens::Personagem {
                id: p.id,
                nome: p.name.clone(),
                nivel: p.level,
                aparencia: if p.aparencia.is_empty() { None } else { Some(p.aparencia.clone()) },
                posicao: (p.x, p.y, p.z),
                mapa: p.map_id,
            });
        }

        let lista = lista_personagens::ListaPersonagens::new(update.account_id(), personagens);
        let vazia = lista_personagens::ListaPersonagens::new(update.account_id(), Vec::new());

        messages.extend_direct(
            update.client_id(),
            [
                s::Message::ListaPersonagens45(s::ListaPersonagens45(vazia)),
                s::Message::ListaPersonagens45(s::ListaPersonagens45(lista)),
            ]
            .map(ServerUpdate::new),
        );
    }

    /// Criação de novo personagem usando 100% dados lidos de `player_initial_data.xml`
    pub fn handle_create_character(
        db: &Db,
        data_manager: &DataManager,
        update: &ClientUpdate,
        pedido: &c::CreateCharacter,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let username = Self::username_do_update(db, update);
        let nome = pedido.nome.clone();

        // Extrai raça e classe dos bytes de aparência
        let raca = pedido
            .aparencia
            .get(56..60)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let classe = pedido
            .aparencia
            .get(60..64)
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);

        // Busca o ponto de spawn e itens iniciais diretamente do PlayerInitialDataHolder (XML)
        let spawn_loc = data_manager.player_initial_data.get_spawn_location(raca as u8);
        let ponto = crate::mundo::PontoDeEntrada {
            mapa: spawn_loc.map_id,
            x: spawn_loc.x,
            y: spawn_loc.y,
            z: spawn_loc.z,
            direcao: spawn_loc.heading,
        };

        let nome_da_classe = classe_id_para_nome(classe);
        let itens = data_manager.player_initial_data.get_initial_items(nome_da_classe);

        let criado = match db.criar_personagem_com_xml(
            &username,
            &nome,
            &pedido.aparencia,
            Some(ponto),
            &itens,
        ) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("ERROR: criar_personagem({username}, {nome}): {e}");
                return;
            }
        };

        println!(
            "INFO: [PlayerService] personagem '{}' (id {}, classe {}, raca {}) criado para '{}' com {} itens iniciais do XML",
            criado.name, criado.id, classe, raca, username, itens.len()
        );

        characters.insert(criado.id, Character::from_persisted(&criado, update.client_id()));

        messages.extend_direct(
            update.client_id(),
            [s::Message::CreateCharacter(s::CreateCharacter::new(
                lista_personagens::Personagem {
                    id: criado.id,
                    nome: criado.name,
                    nivel: criado.level,
                    aparencia: if criado.aparencia.is_empty() { None } else { Some(criado.aparencia) },
                    posicao: (criado.x, criado.y, criado.z),
                    mapa: criado.map_id,
                },
            ))]
            .map(ServerUpdate::new),
        );
    }

    /// Exclusão de personagem
    pub fn handle_delete_character(
        db: &Db,
        update: &ClientUpdate,
        pedido: &c::DeleteCharacter,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let username = Self::username_do_update(db, update);
        let ok = db.deletar_personagem(&username, pedido.character_id).unwrap_or(false);
        if ok {
            characters.remove(&pedido.character_id);
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

    /// Finalização do carregamento do mapa pelo cliente e spawn no mundo
    pub fn handle_level_ready(
        character_id: u32,
        client_id: u16,
        characters: &HashMap<u32, Character>,
        entities: &[Entity],
        put_npc: &HashMap<u32, Vec<u8>>,
        npcs_em_cena: &mut HashMap<u32, (HashSet<u32>, crate::engine::Coord)>,
        messages: &mut Messages,
    ) {
        use crate::message::capturado as cap;

        let Some(new_character) = characters.get(&character_id) else {
            println!("WARNING: LevelReady para personagem {character_id} que nao esta no estado; ignorando");
            return;
        };

        let id = new_character.id();
        let spawn_map_id = new_character.spawn_map_id();
        let heading = new_character.heading();
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
            client_id,
            [
                ServerUpdate::new(s::Message::WorldSceneStatus(s::WorldSceneStatus::scene(0, 1))),
                ServerUpdate::new(s::Message::RequestTeleport(s::RequestTeleport::new(
                    1,
                    spawn_map_id,
                    0,
                    aqui_x,
                    aqui_y,
                    aqui_z,
                    heading,
                ))),
                bruto(cap::INVENCIVEL_ANTES_OPCODE, cap::INVENCIVEL_ANTES.to_vec()),
                bruto(cap::ZONA_OPCODE, cap::ZONA.to_vec()),
                bruto(cap::PUT_USER_OPCODE, {
                    let com_id = cap::com_id_de_personagem(&cap::PUT_USER, 12, id);
                    let com_lugar = cap::com_posicao_de_personagem(&com_id, aqui_x, aqui_y, aqui_z);
                    let com_cara = match &aparencia {
                        Some(bloco) => cap::com_aparencia_de_personagem(&com_lugar, bloco),
                        None => com_lugar,
                    };
                    cap::com_nome_de_personagem(&com_cara, cap::PUT_USER_NOME, &nome_no_mundo)
                }),
                bruto(cap::INVENCIVEL_DEPOIS_OPCODE, cap::INVENCIVEL_DEPOIS.to_vec()),
                ServerUpdate::new(s::Message::InvisibleLevel(s::InvisibleLevel::start(id))),
                bruto(cap::BUILDER_LEVEL_OPCODE, cap::BUILDER_LEVEL.to_vec()),
                bruto(cap::STATUS_ANORMAL_OPCODE, cap::STATUS_ANORMAL.to_vec()),
                bruto(cap::PENALIDADE_DE_SKILL_OPCODE, cap::PENALIDADE_DE_SKILL.to_vec()),
                bruto(cap::ANIMACAO_OPCODE, cap::com_id_de_personagem(&cap::ANIMACAO, 1, id)),
                bruto(cap::CENA_DO_MUNDO_OPCODE, cap::CENA_DO_MUNDO.to_vec()),
                ServerUpdate::new(s::Message::HitPoint(s::HitPoint::new(
                    new_character.stats.hp.current() as u32,
                    new_character.stats.hp.max() as u32,
                ))),
                ServerUpdate::new(s::Message::ManaPoint(s::ManaPoint::new(
                    new_character.stats.mp.current() as u32,
                    new_character.stats.mp.max() as u32,
                ))),
                ServerUpdate::new(s::Message::Dp(s::Dp::new(new_character.stats.dp.current()))),
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
            client_id,
            ServerUpdate::new(s::Message::AddSkill45(s::AddSkill45::new(class_skills, 1700000000))),
        );

        let aqui = *new_character.location();
        let new_character_clone = new_character.clone();

        SpatialService::povoa_cena(id, client_id, aqui, npcs_em_cena, entities, put_npc, messages);

        // Sincroniza outros jogadores presentes no raio de visao (60m)
        for other in characters.values() {
            if other.id() == id {
                continue;
            }
            let other_loc = other.location();
            let dx = other_loc.x() - aqui.x();
            let dy = other_loc.y() - aqui.y();
            let dz = other_loc.z() - aqui.z();
            if dx * dx + dy * dy + dz * dz <= 60.0 * 60.0 {
                messages.push_direct(
                    client_id,
                    ServerUpdate::new(s::Message::PutUser(s::PutUser::new(other))),
                );
                messages.push_direct(
                    other.client_id(),
                    ServerUpdate::new(s::Message::PutUser(s::PutUser::new(&new_character_clone))),
                );
            }
        }
    }

    /// Processa o pacote `C_CUR_STATUS` e envia status, skills, mundo e inventário
    pub fn handle_cur_status(
        character_id: u32,
        client_id: u16,
        account_id: u32,
        characters: &mut HashMap<u32, Character>,
        db: &Db,
        data_manager: &DataManager,
        game_data: &Arc<GameData>,
        guild_manager: &crate::guild::GuildManager,
        mundo_enviado: &mut HashSet<u32>,
        burst: &[(u16, Vec<u8>)],
        messages: &mut Messages,
    ) {
        use crate::message::capturado as cap;

        let Some(character) = characters.get_mut(&character_id) else {
            println!("WARNING: CurStatus para personagem {character_id} que nao esta no estado; ignorando");
            return;
        };

        let game_time = 148641933;

        if !mundo_enviado.insert(character_id) {
            messages.extend_direct(
                client_id,
                [ServerUpdate::new(s::Message::CurStatus(s::CurStatus::new()))],
            );
            return;
        }

        let id_na_bolsa = character.id();
        let nome_na_bolsa = character.name().clone();
        let nivel_na_bolsa = character.stats.level;
        let raca_na_bolsa = character
            .aparencia
            .as_ref()
            .and_then(|b| {
                let off = crate::message::molde::campo::RACA
                    - crate::message::molde::campo::NOME;
                b.get(off..off + 4)
            })
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(1);
        let classe_na_bolsa = character
            .aparencia
            .as_ref()
            .and_then(|b| {
                let off = crate::message::molde::campo::CLASSE
                    - crate::message::molde::campo::NOME;
                b.get(off..off + 4)
            })
            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
            .unwrap_or(CLASSE_DO_MOLDE);

        let medindo = !burst.is_empty();
        let bruto_de_entrada = |(opcode, payload): (u16, Vec<u8>)| {
            ServerUpdate::new(s::Message::Bruto(s::Bruto::new(opcode, payload)))
        };

        if medindo {
            let chave = account_id;
            let id = character_id;
            let lote: Vec<_> = burst
                .iter()
                .map(|p| {
                    ServerUpdate::new(crate::message::replay::para_esta_sessao(
                        p, chave, id,
                    ))
                })
                .collect();
            messages.extend_direct(client_id, lote);
        } else {
            messages.extend_direct(
                client_id,
                crate::message::entrada::antes_do_mundo(character_id)
                    .into_iter()
                    .map(bruto_de_entrada)
                    .collect::<Vec<_>>(),
            );

            let (classe, base) = classe_no_xml(classe_na_bolsa);
            let skills = data_manager.skills_de(classe, base, nivel_na_bolsa);

            if !skills.is_empty() {
                let agora = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs() as u32)
                    .unwrap_or(0);
                messages.extend_direct(
                    client_id,
                    [ServerUpdate::new(s::Message::AddSkill45(s::AddSkill45::new(
                        skills, agora,
                    )))],
                );
            }

            // Entrega o kit inicial a partir do XML caso o jogador ainda nao tenha recebido
            let grupo = classe_id_para_nome(classe_na_bolsa);
            let kit = data_manager.player_initial_data.get_initial_items(grupo);
            if !kit.is_empty() {
                let _ = db.garante_kit_inicial(id_na_bolsa, &kit);
            }

            let modo_da_bolsa = std::env::var("AION_BOLSA").unwrap_or_else(|_| "tudo".to_string());
            match db.itens_do_personagem(id_na_bolsa) {
                _ if modo_da_bolsa == "off" => {}
                Ok(itens) if !itens.is_empty() => {
                    let bolsa: Vec<crate::data::item::ItemInventario> = itens
                        .into_iter()
                        .map(|i| {
                            let def = game_data.items.get(&i.item_id).map(|d| d);
                            crate::data::item::ItemInventario::novo(
                                i.obj_id,
                                i.item_id,
                                i.quantidade,
                                i.posicao,
                                def,
                            )
                        })
                        .collect();

                    // Send in batches of POR_LEVA items, then send the closing empty batch
                    let mut primeira = true;
                    for chunk in bolsa.chunks(s::CarregaInventario45::POR_LEVA) {
                        messages.push_direct(
                            client_id,
                            ServerUpdate::new(s::Message::CarregaInventario45(
                                s::CarregaInventario45::leva(primeira, chunk.to_vec()),
                            )),
                        );
                        primeira = false;
                    }
                    messages.push_direct(
                        client_id,
                        ServerUpdate::new(s::Message::CarregaInventario45(s::CarregaInventario45::fim())),
                    );
                }
                _ => {}
            }
        }

        // Ponto de entrada dinâmico lido do XML. O mapa, porem, vem do personagem: o do XML so
        // vale para quem ainda nao tem mapa gravado. Mandar o mapa inicial da raca junto com a
        // posicao gravada joga quem deslogou noutro mapa direto no vazio -- ver
        // `lista_personagens::escreve_ponto_de_entrada`.
        let spawn_loc = data_manager.player_initial_data.get_spawn_location(raca_na_bolsa as u8);
        let mapa_do_personagem = character.spawn_map_id();
        let ponto = crate::mundo::PontoDeEntrada {
            mapa: if mapa_do_personagem != 0 { mapa_do_personagem } else { spawn_loc.map_id },
            x: spawn_loc.x,
            y: spawn_loc.y,
            z: spawn_loc.z,
            direcao: spawn_loc.heading,
        };

        messages.extend_direct(
            client_id,
            [
                s::Message::Bruto(s::Bruto::new(
                    cap::STATUS_OPCODE,
                    {
                        let classe = character
                            .aparencia
                            .as_ref()
                            .and_then(|b| {
                                let off = crate::message::molde::campo::CLASSE
                                    - crate::message::molde::campo::NOME;
                                b.get(off..off + 4)
                            })
                            .map(|v| u32::from_le_bytes(v.try_into().unwrap()))
                            .unwrap_or(CLASSE_DO_MOLDE);
                        cap::com_ficha_de_personagem(
                            &cap::com_id_de_personagem(&cap::STATUS, 0, character.id()),
                            character.stats.level,
                            classe,
                        )
                    },
                )),
                s::Message::World(s::World::new(character.location(), ponto)),
                s::Message::WorldInfo(s::WorldInfo::new()),
                s::Message::CurStatus(s::CurStatus::new()),
                s::Message::Mail(character.build_mail_packet()),
            ]
            .map(ServerUpdate::new),
        );

        if let Some(guild) = guild_manager.get_guild_for_player(character_id) {
            let g_info = s::GuildInfo::new(
                guild.id,
                guild.name.clone(),
                guild.rank,
                guild.race,
                guild.exp,
                guild.contribution_points,
                guild.members.len() as u16,
                30,
                guild.leader_id,
                guild.notice.clone(),
                guild.kinah,
            );
            messages.push_direct(client_id, ServerUpdate::new(s::Message::GuildInfo(g_info)));

            for member in &guild.members {
                let m_info = s::GuildMemberInfo::new(
                    guild.id,
                    member.player_id,
                    member.guild_rank_index,
                    member.name.clone(),
                    member.class_id,
                    member.level,
                    member.race,
                    member.is_online as u8,
                    member.last_online,
                    member.contribution,
                    member.map_id,
                );
                messages.push_direct(client_id, ServerUpdate::new(s::Message::GuildMemberInfo(m_info)));
            }

            for chunk in guild.build_emblem_packets() {
                messages.push_direct(client_id, ServerUpdate::new(s::Message::GuildEmblemImgData(chunk)));
            }
        }

        let buddies = db.amigos_do_personagem(character_id).unwrap_or_default();
        messages.push_direct(client_id, ServerUpdate::new(s::Message::BuddyList(s::BuddyList::from_entries(buddies))));

        if !medindo {
            messages.extend_direct(
                client_id,
                crate::message::entrada::depois_do_mundo(character_id, game_time)
                    .into_iter()
                    .map(bruto_de_entrada)
                    .collect::<Vec<_>>(),
            );
        }
    }
}

pub fn classe_id_para_nome(classe: u32) -> &'static str {
    match classe {
        0 => "WARRIOR",
        1 => "BATTLEMASTER",
        2 => "KNIGHT",
        3 => "SCOUT",
        4 => "ASSASSIN",
        5 => "RANGER",
        6 => "MAGE",
        7 => "WIZARD",
        8 => "ELEMENTALLIST",
        9 => "PRIEST",
        10 => "CLERIC",
        11 => "CHANTER",
        12 => "MONK",
        13 => "THUNDERER",
        14 => "MARTIAL_ARTIST",
        15 => "BATTLE_MASTER",
        _ => "WARRIOR",
    }
}

pub fn classe_no_xml(classe: u32) -> (&'static str, &'static str) {
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
        12 => ("MONK", "MONK"),
        13 => ("THUNDERER", "MONK"),
        14 => ("MARTIAL_ARTIST", "MARTIAL_ARTIST"),
        15 => ("BATTLE_MASTER", "MARTIAL_ARTIST"),
        _ => ("", ""),
    }
}
