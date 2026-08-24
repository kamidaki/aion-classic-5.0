use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LetterType {
    Regular,
    Express,
    System,
    Blackcloud,
}

#[derive(Debug, Clone)]
pub struct Letter {
    pub id: u32,
    pub sender_name: String,
    pub recipient_id: u32,
    pub title: String,
    pub message: String,
    pub attached_item_id: u32,
    pub attached_item_count: u32,
    pub attached_kinah: u64,
    pub is_read: bool,
    pub is_express: bool,
    pub letter_type: LetterType,
    pub timestamp_sec: u64,
}

impl Letter {
    pub fn new(
        id: u32,
        sender_name: String,
        recipient_id: u32,
        title: String,
        message: String,
        attached_item_id: u32,
        attached_item_count: u32,
        attached_kinah: u64,
        letter_type: LetterType,
    ) -> Self {
        let timestamp_sec = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        let is_express = matches!(letter_type, LetterType::Express);
        Self {
            id,
            sender_name,
            recipient_id,
            title,
            message,
            attached_item_id,
            attached_item_count,
            attached_kinah,
            is_read: false,
            is_express,
            letter_type,
            timestamp_sec,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct Mailbox {
    pub letters: HashMap<u32, Letter>,
    next_letter_id: u32,
}

impl Mailbox {
    pub const MAX_LETTERS: usize = 100;
    pub const REGULAR_COST: u64 = 10;
    pub const EXPRESS_COST: u64 = 500;

    pub fn new() -> Self {
        Self {
            letters: HashMap::new(),
            next_letter_id: 1,
        }
    }

    pub fn can_receive(&self) -> bool {
        self.letters.len() < Self::MAX_LETTERS
    }

    pub fn add_letter(&mut self, mut letter: Letter) -> Option<u32> {
        if !self.can_receive() {
            return None;
        }
        let id = self.next_letter_id;
        self.next_letter_id = self.next_letter_id.wrapping_add(1);
        letter.id = id;
        self.letters.insert(id, letter);
        Some(id)
    }

    pub fn read_letter(&mut self, letter_id: u32) -> Option<&Letter> {
        if let Some(l) = self.letters.get_mut(&letter_id) {
            l.is_read = true;
            Some(l)
        } else {
            None
        }
    }

    pub fn extract_kinah(&mut self, letter_id: u32) -> u64 {
        if let Some(l) = self.letters.get_mut(&letter_id) {
            let k = l.attached_kinah;
            l.attached_kinah = 0;
            k
        } else {
            0
        }
    }

    pub fn extract_item(&mut self, letter_id: u32) -> Option<(u32, u32)> {
        if let Some(l) = self.letters.get_mut(&letter_id) {
            if l.attached_item_id != 0 && l.attached_item_count > 0 {
                let res = (l.attached_item_id, l.attached_item_count);
                l.attached_item_id = 0;
                l.attached_item_count = 0;
                Some(res)
            } else {
                None
            }
        } else {
            None
        }
    }

    pub fn delete_letter(&mut self, letter_id: u32) -> bool {
        if let Some(l) = self.letters.get(&letter_id) {
            // Cannot delete if unextracted attachments remain
            if l.attached_kinah > 0 || l.attached_item_id != 0 {
                return false;
            }
            self.letters.remove(&letter_id).is_some()
        } else {
            false
        }
    }

    pub fn unread_count(&self) -> usize {
        self.letters.values().filter(|l| !l.is_read).count()
    }

    pub fn build_mail_packet(&self) -> crate::game::message::server::Mail {
        let mut summaries = Vec::new();
        for letter in self.letters.values() {
            let mut has_attachment = 0u8;
            if letter.attached_item_id != 0 && letter.attached_item_count > 0 {
                has_attachment |= 0x01;
            }
            if letter.attached_kinah > 0 {
                has_attachment |= 0x02;
            }
            let letter_type_u8 = match letter.letter_type {
                LetterType::Regular => 0,
                LetterType::Express => 1,
                LetterType::System => 2,
                LetterType::Blackcloud => 3,
            };
            summaries.push(crate::game::message::server::MailLetterSummary::new(
                letter.id,
                0,
                letter.sender_name.clone(),
                letter.title.clone(),
                letter_type_u8,
                letter.is_read as u8,
                has_attachment,
                letter.attached_item_id,
                letter.attached_item_count,
                letter.attached_kinah,
                letter.timestamp_sec,
            ));
        }
        crate::game::message::server::Mail::new(summaries)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mailbox_flow() {
        let mut mb = Mailbox::new();
        assert!(mb.can_receive());

        let letter = Letter::new(
            0,
            "ShugoTrader".to_string(),
            1001,
            "Item Votado".to_string(),
            "Voce comprou o item".to_string(),
            10000001,
            1,
            50000,
            LetterType::System,
        );

        let id = mb.add_letter(letter).expect("deve adicionar");
        assert_eq!(mb.unread_count(), 1);

        let l = mb.read_letter(id).expect("deve ler");
        assert!(l.is_read);
        assert_eq!(mb.unread_count(), 0);

        let kinah = mb.extract_kinah(id);
        assert_eq!(kinah, 50000);

        let item = mb.extract_item(id).expect("deve extrair item");
        assert_eq!(item, (10000001, 1));

        // Nao pode ter sobrado nada
        assert!(mb.delete_letter(id));
        assert_eq!(mb.letters.len(), 0);
    }
}
