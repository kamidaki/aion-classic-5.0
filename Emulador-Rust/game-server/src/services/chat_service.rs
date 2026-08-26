//! ChatService - Gerenciamento de Chat, Comandos GM e Anti-Flood (Padrão Java AION)

use std::collections::HashMap;
use std::time::{Duration, Instant};

use crate::character::Character;
use crate::engine::Coord;
use crate::guild::GuildManager;
use crate::message::{client as c, server as s};
use crate::social::{resolve_goto_location, GmCommand, PartyService};
use crate::{Messages, ServerUpdate};

pub struct ChatService;

impl ChatService {
    /// Validação de anti-flood: no máximo 5 mensagens a cada 5 segundos
    pub fn check_flood(char_id: u32, chat_timestamps: &mut HashMap<u32, Vec<Instant>>) -> bool {
        let now = Instant::now();
        let timestamps = chat_timestamps.entry(char_id).or_default();
        timestamps.retain(|&t| now.duration_since(t) < Duration::from_secs(5));
        if timestamps.len() >= 5 {
            return false;
        }
        timestamps.push(now);
        true
    }

    /// Processa o recebimento e roteamento de mensagens de chat
    pub fn handle_chat_public(
        character_id: u32,
        client_id: u16,
        msg: &c::ChatMessagePublic,
        characters: &mut HashMap<u32, Character>,
        chat_timestamps: &mut HashMap<u32, Vec<Instant>>,
        party_service: &PartyService,
        guild_manager: &GuildManager,
        restrictions: &crate::restrictions::RestrictionsManager,
        messages: &mut Messages,
    ) {
        if !Self::check_flood(character_id, chat_timestamps) {
            println!("WARN: [ChatService] Player {character_id} dropped for chat flood");
            return;
        }

        let Some(character) = characters.get(&character_id) else {
            return;
        };

        // Validação estrita pelo subsistema de restrições (Gag / Prison)
        let player_state = character.to_player_state();
        if let Err(restriction_err) = restrictions.can_chat(&player_state) {
            println!("WARN: [ChatService] Chat restricted for player {character_id}: {:?}", restriction_err);
            return;
        }

        let char_name = character.name().to_string();
        let loc = *character.location();
        let access_level = 100;

        // Verificação e execução de comandos GM
        if let Some(cmd) = GmCommand::parse(&msg.message) {
            if access_level >= 100 {
                match cmd {
                    GmCommand::Teleport { map_id, x, y, z } => {
                        if let Some(character) = characters.get_mut(&character_id) {
                            character.set_location(Coord::new(x, y, z));
                            character.set_spawn_map_id(map_id);
                            messages.push_direct(
                                client_id,
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
                        }
                    }
                    GmCommand::Goto { destination } => {
                        if let Some((map_id, x, y, z)) = resolve_goto_location(&destination) {
                            if let Some(character) = characters.get_mut(&character_id) {
                                character.set_location(Coord::new(x, y, z));
                                character.set_spawn_map_id(map_id);
                                messages.push_direct(
                                    client_id,
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
                            }
                        }
                    }
                    GmCommand::SetLevel { level } => {
                        if let Some(character) = characters.get_mut(&character_id) {
                            character.stats.level = level;
                        }
                    }
                    _ => {
                        println!("INFO: [ChatService] GM command executed: {:?}", cmd);
                    }
                }
                return;
            }
        }

        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs() as u32;

        let chat_packet = s::ChatMessage::new(
            character_id,
            char_name,
            msg.chat_type,
            msg.message.clone(),
            timestamp,
        );

        match msg.chat_type {
            0 => {
                // Normal (50m)
                for other in characters.values() {
                    if loc.distance(&other.location()) <= 50.0 {
                        messages.push_direct(
                            other.client_id(),
                            ServerUpdate::new(s::Message::ChatMessage(chat_packet.clone())),
                        );
                    }
                }
            }
            1 => {
                // Shout (500m)
                for other in characters.values() {
                    if loc.distance(&other.location()) <= 500.0 {
                        messages.push_direct(
                            other.client_id(),
                            ServerUpdate::new(s::Message::ChatMessage(chat_packet.clone())),
                        );
                    }
                }
            }
            3 => {
                // Grupo
                if let Some(gid) = party_service.group_of(character_id) {
                    if let Some(party) = party_service.groups.get(&gid) {
                        for &member_id in &party.members {
                            if let Some(member) = characters.get(&member_id) {
                                messages.push_direct(
                                    member.client_id(),
                                    ServerUpdate::new(s::Message::ChatMessage(chat_packet.clone())),
                                );
                            }
                        }
                    }
                }
            }
            5 => {
                // Legião / Guild
                if let Some(guild) = guild_manager.get_guild_for_player(character_id) {
                    for member in &guild.members {
                        if let Some(online_char) = characters.get(&member.player_id) {
                            messages.push_direct(
                                online_char.client_id(),
                                ServerUpdate::new(s::Message::ChatMessage(chat_packet.clone())),
                            );
                        }
                    }
                }
            }
            _ => {
                // Broadcast geral
                for other in characters.values() {
                    messages.push_direct(
                        other.client_id(),
                        ServerUpdate::new(s::Message::ChatMessage(chat_packet.clone())),
                    );
                }
            }
        }
    }
}
