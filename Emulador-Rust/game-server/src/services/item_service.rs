//! ItemService - Gerenciamento de Equipamentos, Itens, Compras e Vendas em NPCs (Padrão Java AION)

use std::collections::HashMap;
use std::sync::Arc;

use crate::dao::Db;
use crate::data_loader::GameData;
use crate::character::Character;
use crate::data::gear::LootItem;
use crate::data::ActionType;
use crate::message::{client as c, server as s};
use crate::{Messages, ServerUpdate};

pub struct ItemService;

impl ItemService {
    /// Processa compra ou venda de itens em comerciantes NPCs
    pub fn handle_buy_sell(
        character_id: u32,
        client_id: u16,
        buy_sell: &c::BuySell,
        characters: &mut HashMap<u32, Character>,
        db: &Db,
        messages: &mut Messages,
    ) {
        println!(
            "INFO: [ItemService] Player {} BuySell (npc: {}, action: {}, item_unique: {}, item_template: {}, qty: {})",
            character_id,
            buy_sell.npc_object_id,
            buy_sell.action,
            buy_sell.item_unique_id,
            buy_sell.item_template_id,
            buy_sell.quantity
        );

        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        match buy_sell.action {
            0 => {
                // Compra
                let current_kinah = db.obter_kinah(character_id).unwrap_or(0);
                let unit_price = 1000u64;
                let total_price = unit_price * buy_sell.quantity.max(1) as u64;

                if current_kinah < total_price {
                    messages.push_direct(
                        client_id,
                        ServerUpdate::new(s::Message::StoreSaleInfo(s::StoreSaleInfo::new(
                            1, // kinah insuficiente
                            0,
                            buy_sell.item_template_id,
                            buy_sell.quantity,
                            0,
                            current_kinah,
                        ))),
                    );
                } else {
                    let _ = db.alterar_kinah(character_id, -(total_price as i64));
                    let new_kinah = db.obter_kinah(character_id).unwrap_or(0);
                    let unique_id = character.add_item(buy_sell.item_template_id, buy_sell.quantity);
                    let _ = db.adicionar_item(character_id, buy_sell.item_template_id, buy_sell.quantity as u64, 0);

                    messages.push_direct(
                        client_id,
                        ServerUpdate::new(s::Message::StoreSaleInfo(s::StoreSaleInfo::new(
                            0, // sucesso
                            unique_id,
                            buy_sell.item_template_id,
                            buy_sell.quantity,
                            total_price,
                            new_kinah,
                        ))),
                    );
                }
            }
            1 => {
                // Venda
                let sell_price = character.sell_item(buy_sell.item_unique_id, buy_sell.quantity);
                let _ = db.alterar_kinah(character_id, sell_price as i64);
                let _ = db.remover_item(character_id, buy_sell.item_template_id, buy_sell.quantity as u64);
                let new_kinah = db.obter_kinah(character_id).unwrap_or(0);

                messages.push_direct(
                    client_id,
                    ServerUpdate::new(s::Message::StoreSaleInfo(s::StoreSaleInfo::new(
                        0, // sucesso
                        buy_sell.item_unique_id,
                        buy_sell.item_template_id,
                        buy_sell.quantity,
                        sell_price,
                        new_kinah,
                    ))),
                );
                messages.push_direct(
                    client_id,
                    ServerUpdate::new(s::Message::UserSellHistoryList(character.build_buyback_list())),
                );
            }
            _ => {}
        }
    }

    /// Processa ação de equipar ou desequipar itens
    pub fn handle_use_equipment_item(
        character_id: u32,
        client_id: u16,
        equip: &c::UseEquipmentItem,
        characters: &mut HashMap<u32, Character>,
        game_data: &Arc<GameData>,
        messages: &mut Messages,
    ) {
        println!(
            "INFO: [ItemService] Player {} UseEquipmentItem (unique_id: {}, action: {}, slot: {})",
            character_id, equip.item_unique_id, equip.equip_action, equip.equip_slot
        );

        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        match equip.equip_action {
            0 => {
                let _ = character.equip_item(equip.item_unique_id, equip.equip_slot);
            }
            1 => {
                let _ = character.unequip_slot(equip.equip_slot);
            }
            _ => {}
        }

        let _new_stats = character.recalculate_stats(game_data);
        messages.push_direct(
            client_id,
            ServerUpdate::new(s::Message::Status(s::Status::new(character, 0))),
        );

        messages.push_others(
            client_id,
            ServerUpdate::new(s::Message::UpdatePlayerAppearance(s::UpdatePlayerAppearance::new(
                character_id,
                character.equipment_template_ids(),
            ))),
        );

        messages.push_direct(
            client_id,
            ServerUpdate::new(s::Message::LoadInventory(character.build_inventory_packet())),
        );
    }

    /// Processa início da coleta de loot
    pub fn handle_loot_start(
        character_id: u32,
        client_id: u16,
        entity_id: u32,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        messages.broadcast.push(ServerUpdate::new(s::Message::Action(s::Action::new(
            character.id(),
            ActionType::Loot,
            character.stats.move_speed,
            entity_id,
        ))));

        messages.extend_direct(
            client_id,
            [
                s::Message::LootItemlist(s::LootItemlist::new(
                    entity_id,
                    vec![LootItem::new(0x098975E6, 1)],
                )),
                s::Message::Loot(s::Loot::new(entity_id, 2)),
            ]
            .map(ServerUpdate::new),
        );
    }

    /// Processa conclusão da coleta de um item de loot
    pub fn handle_loot_item(
        character_id: u32,
        client_id: u16,
        entity_id: u32,
        characters: &mut HashMap<u32, Character>,
        messages: &mut Messages,
    ) {
        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        messages.extend_direct(
            client_id,
            [
                s::Message::ChangeItemDesc(s::ChangeItemDesc::new()),
                s::Message::Action(s::Action::new(
                    character.id(),
                    ActionType::EndLoot,
                    character.stats.move_speed,
                    entity_id,
                )),
                s::Message::Loot(s::Loot::new(entity_id, 3)),
            ]
            .map(ServerUpdate::new),
        );
    }
}
