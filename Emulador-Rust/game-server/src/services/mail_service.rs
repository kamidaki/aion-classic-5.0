//! MailService - Gerenciamento de Correio, Cartas e Envio de Itens (Padrão Java AION)

use std::collections::HashMap;

use crate::dao::Db;
use crate::character::Character;
use crate::mail::{Letter, LetterType};
use crate::message::{client as c, server as s};
use crate::{Messages, ServerUpdate};

pub struct MailService;

impl MailService {
    /// Processa leitura e extração de anexos de uma carta
    pub fn handle_mail_read(
        character_id: u32,
        client_id: u16,
        mail_read: &c::MailRead,
        characters: &mut HashMap<u32, Character>,
        db: &Db,
        messages: &mut Messages,
    ) {
        println!(
            "INFO: [MailService] Player {} MailRead (letter_id: {}, action: {})",
            character_id, mail_read.letter_id, mail_read.action
        );

        let Some(character) = characters.get_mut(&character_id) else {
            return;
        };

        match mail_read.action {
            0 => {
                let _ = character.mailbox.read_letter(mail_read.letter_id);
                let _ = db.marcar_carta_lida(mail_read.letter_id);
            }
            1 => {
                if let Some((item_id, count)) = character.mailbox.extract_item(mail_read.letter_id) {
                    character.add_item(item_id, count);
                    let _ = db.adicionar_item(character_id, item_id, count as u64, 0);
                    let _ = db.extrair_anexos_carta(mail_read.letter_id);
                }
            }
            2 => {
                let kinah = character.mailbox.extract_kinah(mail_read.letter_id);
                if kinah > 0 {
                    character.add_kinah(kinah);
                    let _ = db.alterar_kinah(character_id, kinah as i64);
                    let _ = db.extrair_anexos_carta(mail_read.letter_id);
                }
            }
            3 => {
                if character.mailbox.delete_letter(mail_read.letter_id) {
                    let _ = db.deletar_carta(mail_read.letter_id);
                }
            }
            _ => {}
        }

        messages.push_direct(
            client_id,
            ServerUpdate::new(s::Message::Mail(character.build_mail_packet())),
        );
    }

    /// Processa envio de carta para outro jogador com itens e kinah
    pub fn handle_mail_postman(
        character_id: u32,
        client_id: u16,
        postman: &c::MailPostman,
        characters: &mut HashMap<u32, Character>,
        db: &Db,
        messages: &mut Messages,
    ) {
        println!(
            "INFO: [MailService] Player {} MailPostman (recipient: {}, title: {}, type: {}, item: {}, kinah: {})",
            character_id, postman.recipient_name, postman.title, postman.letter_type, postman.item_unique_id, postman.kinah_amount
        );

        let cost = (if postman.letter_type == 1 { 500u64 } else { 10u64 }) + postman.kinah_amount;
        let current_kinah = db.obter_kinah(character_id).unwrap_or(0);

        if current_kinah < cost {
            return;
        }

        let mut item_template_id = 0;
        let mut sender_name = String::new();
        let mut sender_mail_pkt = None;

        if let Some(character) = characters.get_mut(&character_id) {
            let _ = db.alterar_kinah(character_id, -(cost as i64));
            if postman.item_unique_id != 0 {
                item_template_id = character.items.remove(&postman.item_unique_id).map(|i| i.id).unwrap_or(0);
            }
            sender_name = character.name().clone();
            sender_mail_pkt = Some(character.build_mail_packet());
        }

        let letter_type_enum = match postman.letter_type {
            1 => LetterType::Express,
            _ => LetterType::Regular,
        };

        let letter = Letter::new(
            0,
            sender_name.clone(),
            0,
            postman.title.clone(),
            postman.body.clone(),
            item_template_id,
            postman.item_quantity,
            postman.kinah_amount,
            letter_type_enum,
        );

        let mut recipient_info = None;
        for (other_id, other_char) in characters.iter_mut() {
            if *other_id != character_id && other_char.name() == &postman.recipient_name {
                other_char.mailbox.add_letter(letter.clone());
                recipient_info = Some((*other_id, other_char.client_id(), other_char.build_mail_packet()));
                break;
            }
        }

        if let Some((recip_id, recip_client_id, recip_pkt)) = recipient_info {
            let _ = db.salvar_carta(
                recip_id,
                &sender_name,
                &postman.title,
                &postman.body,
                postman.letter_type,
                item_template_id,
                postman.item_quantity,
                postman.kinah_amount,
            );
            messages.push_direct(
                recip_client_id,
                ServerUpdate::new(s::Message::Mail(recip_pkt)),
            );
        }

        if let Some(pkt) = sender_mail_pkt {
            messages.push_direct(
                client_id,
                ServerUpdate::new(s::Message::Mail(pkt)),
            );
        }
    }
}
