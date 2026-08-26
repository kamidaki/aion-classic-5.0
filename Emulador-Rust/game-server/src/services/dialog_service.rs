//! DialogService - Gerenciamento de Diálogos com NPCs e Missões (Padrão Java AION)

use std::collections::{HashMap, HashSet};
use std::sync::Arc;

use crate::dao::Db;
use crate::data_loader::GameData;
use crate::character::Character;
use crate::engine::Coord;
use crate::entity::Entity;
use crate::message::{client as c, server as s};
use crate::teleport::TeleportService;
use crate::{Messages, ServerUpdate};

pub struct DialogService;

impl DialogService {
    /// Processa abertura da janela de diálogo com um NPC
    pub fn handle_show_dialog(
        character_id: u32,
        client_id: u16,
        dialog: &c::ShowDialog,
        entities: &[Entity],
        game_data: &Arc<GameData>,
        messages: &mut Messages,
    ) {
        let dialog_id = if let Some(entity) = entities.iter().find(|e| e.id() == dialog.target_id) {
            if let Some(def) = game_data.npcs.get(&entity.npc_id()) {
                if def.name.to_lowercase().contains("teleport") || def.name.to_lowercase().contains("flight") {
                    10
                } else if def.name.to_lowercase().contains("merchant") || def.name.to_lowercase().contains("trader") {
                    2
                } else {
                    18
                }
            } else {
                18
            }
        } else if dialog.dialog_id != 0 {
            dialog.dialog_id
        } else {
            18
        };

        println!(
            "INFO: [DialogService] Player {} opened dialog with target {} (dialog_id: {})",
            character_id, dialog.target_id, dialog_id
        );
        messages.push_direct(
            client_id,
            ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                dialog.target_id,
                dialog_id,
                0,
            ))),
        );
    }

    /// Processa a seleção de uma opção de diálogo (aceitar quest, completar quest, teleporte)
    pub fn handle_dialog_select(
        character_id: u32,
        client_id: u16,
        sel: &c::DialogSelect,
        characters: &mut HashMap<u32, Character>,
        teleport_service: &TeleportService,
        db: &Db,
        npcs_em_cena: &mut HashMap<u32, (HashSet<u32>, Coord)>,
        mundo_enviado: &mut HashSet<u32>,
        messages: &mut Messages,
    ) {
        let now_ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs() as u32;

        println!(
            "INFO: [DialogService] Player {} selected dialog option {} for target {} (quest: {})",
            character_id, sel.dialog_id, sel.target_id, sel.quest_id
        );

        match sel.dialog_id {
            10003 => {
                // Aceitar quest
                let quest_id = if sel.quest_id != 0 { sel.quest_id } else { 1001 };
                if let Some(character) = characters.get_mut(&character_id) {
                    character.start_quest(quest_id, now_ts);
                    let _ = db.save_quest(character_id, quest_id, 0, 0, [0; 4], now_ts);
                    messages.push_direct(
                        client_id,
                        ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                            sel.target_id,
                            0,
                            0,
                        ))),
                    );
                }
            }
            10004 => {
                // Completar quest
                let quest_id = if sel.quest_id != 0 { sel.quest_id } else { 1001 };
                if let Some(character) = characters.get_mut(&character_id) {
                    if let Some(reward) = character.complete_quest(quest_id) {
                        character.add_exp(reward.exp_reward);
                        character.add_kinah(reward.kinah_reward);
                        let _ = db.save_quest(character_id, quest_id, 2, 0, [0; 4], now_ts);
                        let _ = db.alterar_kinah(character_id, reward.kinah_reward as i64);

                        messages.push_direct(
                            client_id,
                            ServerUpdate::new(s::Message::ExpUpdate(s::ExpUpdate::new(
                                character.exp(),
                                character.exp_required(),
                            ))),
                        );
                        messages.push_direct(
                            client_id,
                            ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                                sel.target_id,
                                0,
                                0,
                            ))),
                        );
                    }
                }
            }
            10 | _ => {
                let loc_id = if sel.dialog_id == 10 { sel.last_page } else { sel.dialog_id };
                if let Some(loc) = teleport_service.locations.get(&loc_id).cloned() {
                    let race = characters.get(&character_id).map(|c| c.race()).unwrap_or(0);
                    let level = characters.get(&character_id).map(|c| c.stats.level as u8).unwrap_or(1);
                    if let Ok((loc_ref, _rem)) = teleport_service.validate_and_teleport(loc.loc_id, level, race, 1000000) {
                        if let Some(character) = characters.get_mut(&character_id) {
                            character.set_location(Coord::new(loc_ref.x, loc_ref.y, loc_ref.z));
                            character.set_spawn_map_id(loc_ref.map_id);
                            character.set_heading(loc_ref.heading);
                        }
                        npcs_em_cena.remove(&character_id);
                        mundo_enviado.remove(&character_id);
                        messages.push_direct(
                            client_id,
                            ServerUpdate::new(s::Message::RequestTeleport(s::RequestTeleport::new(
                                0,
                                loc_ref.map_id,
                                0,
                                loc_ref.x,
                                loc_ref.y,
                                loc_ref.z,
                                loc_ref.heading,
                            ))),
                        );
                        messages.push_direct(
                            client_id,
                            ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                                sel.target_id,
                                0,
                                0,
                            ))),
                        );
                        return;
                    }
                }
                messages.push_direct(
                    client_id,
                    ServerUpdate::new(s::Message::DialogWindow(s::DialogWindow::new(
                        sel.target_id,
                        sel.dialog_id,
                        sel.quest_id,
                    ))),
                );
            }
        }
    }
}
