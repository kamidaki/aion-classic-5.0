use std::collections::HashMap;

use crate::to_le_bytes;

use super::data::gear::RawItem;
use super::data::skill::{Skill, SkillType};
use super::engine::damage::{Hit, Type};
use super::entity::Entity;
use super::{
    data::gear::{Gear, Item, Slot, SlotType},
    engine::Coord,
    message::server as s,
};

#[derive(Debug, Clone, Copy)]
pub struct QuestReward {
    pub exp_reward: u64,
    pub kinah_reward: u64,
}

#[derive(Debug, Clone)]
pub struct Stats {
    pub level: u16,
    pub exp: u64,
    pub exp_to_level: u64,
    pub primary: Primary,
    pub secondary: Secondary,
    pub flight_time_max: u32,
    pub flight_time_current: u32,
    pub hp: Hp,
    pub mp: Mp,
    pub dp: Dp,
    /// Attacks per second in millis
    pub attack_speed: u16,
    pub move_speed: f32,
    pub cast_speed: f32,
}

impl Stats {
    pub fn level(&self) -> u16 {
        self.level
    }
}

#[derive(Debug, Clone)]
pub struct Secondary {
    pub main_hand_attack: u16,
    pub off_hand_attack: u16,
    pub unknown1: u16,
    pub physical_defence: u16,
    pub magic_resist: u16,
    pub unknown2: u16,
    pub unknown3: u16,
    pub unknown4: u16,
    pub evasion: u16,
    pub parry: u16,
    pub block: u16,
    pub main_hand_crit: u16,
    pub off_hand_crit: u16,
    pub crit_spell: u16,
    pub unknown5: u16,
    pub main_hand_accuracy: u16,
    pub off_hand_accuracy: u16,
    pub unknown6: u16,
    pub magic_accuracy: u16,
    pub unknown7: u16,
    pub magic_boost: u16,
    pub healing_boost: u16,
    pub crit_strike_resist: u16,
    pub spell_resist: u16,
    pub strike_fortitude: u16,
    pub spell_fortitude: u16,
}

#[derive(Debug, Clone)]
pub struct Primary {
    power: u16,
    health: u16,
    agility: u16,
    accuracy: u16,
    knowledge: u16,
    will: u16,
}

impl Primary {
    pub fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        to_le_bytes!(len, buf, self.power);
        to_le_bytes!(len, buf, self.health);
        to_le_bytes!(len, buf, self.agility);
        to_le_bytes!(len, buf, self.accuracy);
        to_le_bytes!(len, buf, self.knowledge);
        to_le_bytes!(len, buf, self.will);
        len
    }
}

#[derive(Debug, Clone)]
pub struct Hp {
    max: i32,
    base: i32,
    current: i32,
}
impl Hp {
    pub fn new(hp: i32) -> Self {
        Self {
            max: hp,
            base: hp,
            current: hp,
        }
    }
    pub fn max(&self) -> i32 {
        self.max
    }
    pub fn base(&self) -> i32 {
        self.base
    }
    pub fn current(&self) -> i32 {
        self.current
    }
    pub fn is_dead(&self) -> bool {
        self.current <= 0
    }
    pub fn percent(&self) -> u8 {
        ((self.current as f32 / self.max as f32) * 100.) as u8
    }
    pub fn update(&mut self, x: i32) {
        self.current = (self.current + x).clamp(0, self.max);
    }
}

#[derive(Debug, Clone)]
pub struct Mp {
    max: u32,
    base: u32,
    current: u32,
}
impl Mp {
    pub fn max(&self) -> u32 {
        self.max
    }
    pub fn base(&self) -> u32 {
        self.base
    }
    pub fn current(&self) -> u32 {
        self.current
    }
    pub fn update(&mut self, x: i32) {
        if x < 0 {
            self.current = self.current.saturating_sub((-x) as u32);
        } else {
            self.current = (self.current + x as u32).min(self.max);
        }
    }
}
#[derive(Debug, Clone)]
pub struct Dp {
    max: u16,
    current: u16,
}
impl Dp {
    pub fn max(&self) -> u16 {
        self.max
    }

    pub fn current(&self) -> u16 {
        self.current
    }

    pub fn update(&mut self, x: i32) {
        if x < 0 {
            self.current = self.current.saturating_sub((-x) as u16);
        } else {
            self.current = (self.current + x as u16).min(self.max);
        }
    }
}

#[derive(Debug, Clone)]
pub struct Character {
    id: u32,
    client_id: u16,
    name: String,
    location: Coord,
    pub spawn_map_id: u32,
    pub heading: u8,
    pub gear: Gear,
    pub stats: Stats,
    pub skills: Vec<Skill>,
    pub items: HashMap<u32, RawItem>,
    pub active_quests: HashMap<u32, s::QuestEntry>,
    pub buyback_history: Vec<s::SellHistoryEntry>,
    pub mailbox: crate::mail::Mailbox,
    pub guild_id: Option<u32>,
    /// Os 140 bytes que o cliente mandou ao criar o personagem. `None` para quem nasceu antes da
    /// criacao existir -- esses caem no molde capturado.
    pub aparencia: Option<Vec<u8>>,
    attack_sequence: u8,
}
impl Character {
    pub fn new(id: u32, client_id: u16, location: Coord) -> Self {
        let mut gear = Gear::new();
        gear.set(Slot::MainHand, Item::new(100000768, SlotType::Visible));
        gear.set(
            Slot::OffHand,
            Item::new(100000768, SlotType::VisibleOffHand),
        );
        gear.set(Slot::Shoulder, Item::new(112300777, SlotType::Visible));
        gear.set(Slot::Chest, Item::new(110300873, SlotType::Visible));
        gear.set(Slot::Legs, Item::new(113300848, SlotType::Visible));
        gear.set(Slot::Boots, Item::new(114300884, SlotType::Visible));
        gear.set(Slot::Gloves, Item::new(111300826, SlotType::Visible));
        gear.set(
            Slot::PowerShardLeft,
            Item::new(169000002, SlotType::Visible),
        );
        gear.set(
            Slot::PowerShardRight,
            Item::new(169000002, SlotType::Visible),
        );

        let skills = vec![
            Skill::new(1, 1, SkillType::Normal),
            Skill::new(4, 1, SkillType::Normal),
            Skill::new(5, 1, SkillType::Normal),
            Skill::new(30, 1, SkillType::Normal),
            Skill::new(564, 1, SkillType::Normal),
            Skill::new(572, 1, SkillType::Normal),
            Skill::new(551, 1, SkillType::Normal),
            Skill::new(19, 1, SkillType::Normal),
            Skill::new(113, 1, SkillType::Normal),
            Skill::new(555, 1, SkillType::Normal),
            Skill::new(559, 1, SkillType::Normal),
            Skill::new(568, 1, SkillType::Normal),
            Skill::new(8, 1, SkillType::Normal),
            Skill::new(9, 1, SkillType::Normal),
            Skill::new(12, 1, SkillType::Normal),
            Skill::new(17, 1, SkillType::Normal),
            Skill::new(112, 1, SkillType::Normal),
            Skill::new(360, 1, SkillType::Normal),
            Skill::new(577, 1, SkillType::Normal),
            Skill::new(565, 1, SkillType::Normal),
            Skill::new(816, 1, SkillType::Normal),
            Skill::new(839, 1, SkillType::Normal),
            Skill::new(889, 1, SkillType::Normal),
            Skill::new(905, 1, SkillType::Normal),
            Skill::new(908, 1, SkillType::Normal),
            Skill::new(552, 1, SkillType::Normal),
            Skill::new(807, 1, SkillType::Normal),
            Skill::new(833, 1, SkillType::Normal),
            Skill::new(912, 1, SkillType::Normal),
            Skill::new(803, 1, SkillType::Normal),
            Skill::new(1801, 1, SkillType::Normal),
            Skill::new_crafting(30002, 99),
            Skill::new_crafting(30003, 99),
            Skill::morph(),
        ];

        let items = [
            // Kinah
            RawItem::new(
                0xC76BA3B4,
                0x0ADF3401,
                0x1569DB,
                0xFFFF,
                vec![0x00, 0x1E, 0x63, 0xED, 0x4F, 0x01, 0x00],
            ),
            // Aldelle's Leather Shoes
            RawItem::new(
                0xC76BA3AC,
                0x06D016E0,
                0x1607EB,
                0xFFFF,
                vec![
                    0x06, 0x20, 0x00, 0x00, 0x00, 0x02, 0x20, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x01,
                    0x00, //
                    0xE0, 0x16, 0xD0, 0x06, //
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x0A, 0x20, 0x00, 0x09, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x7E, 0x02, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Night Sky Sword
            RawItem::new(
                0xC76BA3AD,
                0x05F5E2C4,
                0x15F72F,
                0xFFFF,
                vec![
                    0x06, 0x02, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00,
                    0x02, 0x00, 0x00, 0x00, 0x0B, 0x01, 0x00, 0xC4, 0xE2, 0xF5,
                    0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x1E, 0x00, 0x1D, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x7E, 0x0A, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Minor Power Shard
            RawItem::new(
                0xC76BA3AE,
                0x0A12BC43,
                0x156AE7,
                0xFFFF,
                vec![
                    0x06, 0x00, 0x20, 0x00, 0x00, 0x04, 0x00, 0x20, 0x00, 0x00,
                    0x00, 0x40, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x43, 0xBC, 0x12,
                    0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3A, 0x61, 0x99, 0x00,
                    0x00, 0x00,
                ],
            ),
            // Shania's Jewel Ring
            RawItem::new(
                0xC76BA3AF,
                0x07459784,
                0x17838D,
                0xFFFF,
                vec![
                    0x06, 0x00, 0x01, 0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00,
                    0x00, 0x01, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x84, 0x97, 0x45,
                    0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x12, 0x00, 0x1C, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x2C, 0x41, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Black Opal
            RawItem::new(
                0xC76BA3B0,
                0x0736532D,
                0x169B73,
                0xFFFF,
                vec![
                    0x06, 0x00, 0x04, 0x00, 0x00, 0x04, 0x00, 0x04, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x2D, 0x53, 0x36,
                    0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x12, 0x00, 0x1F, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x2C, 0x41, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Shania's Leather Hat
            RawItem::new(
                0xC76BA3B1,
                0x07736024,
                0x169B31,
                0xFFFF,
                vec![
                    0x06, 0x04, 0x00, 0x00, 0x00, 0x04, 0x04, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x24, 0x60, 0x73,
                    0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x12, 0x00, 0x3D, 0x00,
                    0x00, 0x00, 0x00, 0x0A, 0x1A, 0x00, 0x21, 0x00, 0x00, 0x00,
                    0x00, 0x0A, 0x1C, 0x00, 0x11, 0x00, 0x00, 0x00, 0x00, 0x0A,
                    0x1F, 0x00, 0x26, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x01,
                    0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Anturoon Jerkin
            RawItem::new(
                0xC76BA3B2,
                0x06930FFE,
                0x17891D,
                0xFFFF,
                vec![
                    0x06, 0x08, 0x00, 0x00, 0x00, 0x02, 0x08, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x00,
                    0x00, 0xFE, 0x0F, 0x93, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0A,
                    0x12, 0x00, 0x3D, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00,
                    0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Spirit Ring
            RawItem::new(
                0xC76BA3B3,
                0x074595E5,
                0x169B91,
                0xFFFF,
                vec![
                    0x06, 0x00, 0x02, 0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00,
                    0x00, 0x01, 0x00, 0x00, 0x0B, 0x00, 0x00, 0xE5, 0x95, 0x45,
                    0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x12, 0x00, 0x10, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x2C, 0x41, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Noble's Leather Belt
            RawItem::new(
                0xC76BA3B5,
                0x0754D670,
                0x15AEC7,
                0xFFFF,
                vec![
                    0x06, 0x00, 0x00, 0x01, 0x00, 0x04, 0x00, 0x00, 0x01, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x0B, 0x01, 0x00, 0x70, 0xD6, 0x54,
                    0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x12, 0x00, 0x1B, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x7E, 0x43, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Karmic Sword
            RawItem::new(
                0xC76BA3B6,
                0x05F5E380,
                0x16990D,
                0xFFFF,
                vec![
                    0x06, 0x01, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00,
                    0x02, 0x00, 0x00, 0x00, 0x0B, 0x00, 0x00, 0x80, 0xE3, 0xF5,
                    0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x0A, 0x22, 0x00, 0x0D, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x2C, 0x08, 0x01, 0x00, 0x00, 0x00,
                ],
            ),
            // Fighter's Vambraces
            RawItem::new(
                0xC76BA3B7,
                0x06A250A0,
                0x169A47,
                0xFFFF,
                vec![
                    0x06, 0x10, 0x00, 0x00, 0x00, 0x02, 0x10, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x00,
                    0x00, 0xA0, 0x50, 0xA2, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x01, 0x00,
                    0x00, 0x00,
                ],
            ),
            // Anturoon Breeches
            RawItem::new(
                0xC76BA3B8,
                0x06C0D537,
                0x169A27,
                0xFF,
                vec![
                    0x06, 0x00, 0x10, 0x00, 0x00, 0x02, 0x00, 0x10, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x00,
                    0x00, 0x37, 0xD5, 0xC0, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x01, 0x00,
                    0x00, 0x00,
                ],
            ),
            // Lesser Healing Potion
            RawItem::new(
                0xC76BA3B9,
                0x09A7EC96,
                0x157129,
                0x26,
                vec![0x00, 0x3E, 0x63, 0x04, 0x00, 0x00, 0x00],
            ),
            // Minor Accessory Flux
            RawItem::new(
                0xC76BA3BA,
                0x090F8121,
                0x1596D1,
                0x09,
                vec![0x00, 0x3E, 0x63, 0x03, 0x00, 0x00, 0x00],
            ),
            // Roast Brax
            RawItem::new(
                0xC76BA3BB,
                0x098975AD,
                0x15961,
                0x09,
                vec![0x00, 0x3E, 0x63, 0x03, 0x00, 0x00, 0x00],
            ),
            // Lesser Focus Agent
            RawItem::new(
                0xC76BA3C5,
                0x098975E6,
                0x178083,
                0x11,
                vec![0x00, 0x3E, 0x63, 0x09, 0x00, 0x00, 0x00],
            ),
        ]
        .into_iter()
        .map(|item| (item.id, item))
        .collect();

        Self {
            client_id,
            id,
            location,
            spawn_map_id: 110_070_000,
            heading: 0,
            gear,
            name: String::new(),
            stats: Stats {
                level: 14,
                exp: 226334,
                exp_to_level: 266649,
                primary: Primary {
                    power: 110,
                    health: 100,
                    agility: 110,
                    accuracy: 110,
                    knowledge: 90,
                    will: 90,
                },
                secondary: Secondary {
                    main_hand_attack: 0x38,
                    off_hand_attack: 0x2F,
                    unknown1: 0,
                    physical_defence: 0xA4,
                    magic_resist: 0xBC,
                    unknown2: 0,
                    unknown3: 0,
                    unknown4: 0x3FC0,
                    evasion: 0x1ED,
                    parry: 0x232,
                    block: 0x010A,
                    main_hand_crit: 0x35,
                    off_hand_crit: 0x35,
                    crit_spell: 0x32,
                    unknown5: 0x32,
                    main_hand_accuracy: 0x1D2,
                    off_hand_accuracy: 0x1C5,
                    unknown6: 0x202,
                    magic_accuracy: 0xCC,
                    unknown7: 0x15,
                    magic_boost: 0,
                    healing_boost: 0,
                    crit_strike_resist: 0,
                    spell_resist: 0,
                    strike_fortitude: 0,
                    spell_fortitude: 0,
                },
                flight_time_max: 60,
                flight_time_current: 59,
                hp: Hp {
                    max: 1148,
                    base: 924,
                    current: 1100,
                },
                mp: Mp {
                    max: 1080,
                    base: 1080,
                    current: 1080,
                },
                dp: Dp {
                    max: 4000,
                    current: 2000,
                },
                attack_speed: 1750,
                move_speed: 6.0,
                cast_speed: 1.0,
            },
            skills,
            active_quests: HashMap::new(),
            buyback_history: Vec::new(),
            mailbox: crate::mail::Mailbox::new(),
            guild_id: None,
            aparencia: None,
            attack_sequence: 0,
            items,
        }
    }

    /// Build a Character from persisted DB fields, using hardcoded defaults
    /// for gear/skills/items/stats which are not yet persisted.
    pub fn from_persisted(
        p: &crate::db::PersistedCharacter,
        client_id: u16,
    ) -> Self {
        let mut c = Self::new(p.id, client_id, Coord::new(p.x, p.y, p.z));
        c.name = p.name.clone();
        c.spawn_map_id = p.map_id;
        c.heading = p.heading;
        c.stats.level = p.level;
        c.stats.exp = p.exp;
        c.stats.hp.current = p.hp as i32;
        // keep hp.max from defaults; persisted hp may be lower
        c.stats.mp.current = p.mp;
        c.aparencia = if p.aparencia.is_empty() { None } else { Some(p.aparencia.clone()) };
        c
    }

    pub fn set_id(&mut self, id: u32) {
        self.id = id;
    }
    pub fn id(&self) -> u32 {
        self.id
    }
    pub fn client_id(&self) -> u16 {
        self.client_id
    }
    pub fn name(&self) -> &String {
        &self.name
    }
    pub fn spawn_map_id(&self) -> u32 {
        self.spawn_map_id
    }
    pub fn set_spawn_map_id(&mut self, map_id: u32) {
        self.spawn_map_id = map_id;
    }
    pub fn heading(&self) -> u8 {
        self.heading
    }
    pub fn set_heading(&mut self, heading: u8) {
        self.heading = heading;
    }
    pub fn set_location(&mut self, coord: Coord) {
        self.location = coord;
    }
    pub fn location(&self) -> &Coord {
        &self.location
    }
    pub fn class(&self) -> u32 {
        if let Some(ref ap) = self.aparencia {
            if ap.len() >= 64 {
                return u32::from_le_bytes(ap[60..64].try_into().unwrap_or([11, 0, 0, 0]));
            }
        }
        11
    }
    pub fn class_id(&self) -> u8 {
        self.class() as u8
    }
    pub fn race(&self) -> u8 {
        if let Some(ref ap) = self.aparencia {
            if ap.len() >= 60 {
                return u32::from_le_bytes(ap[56..60].try_into().unwrap_or([1, 0, 0, 0])) as u8;
            }
        }
        1
    }
    pub fn gender(&self) -> u8 {
        if let Some(ref ap) = self.aparencia {
            if ap.len() >= 56 {
                return u32::from_le_bytes(ap[52..56].try_into().unwrap_or([0, 0, 0, 0])) as u8;
            }
        }
        0
    }

    pub fn to_player_state(&self) -> crate::restrictions::PlayerState {
        use crate::restrictions::{AbnormalState, CreatureState, PlayerMode, PlayerState};
        PlayerState {
            object_id: self.id(),
            name: self.name().clone(),
            race: self.race(),
            level: self.stats.level as u8,
            is_online: true,
            is_dead: self.stats.hp.is_dead(),
            state: if self.stats.hp.is_dead() {
                CreatureState::Dead
            } else {
                CreatureState::Normal
            },
            mode: PlayerMode::Normal,
            abnormal_state: AbnormalState::NONE,
            is_casting: false,
            is_in_combat: false,
            is_trading: false,
            is_gagged: false,
            is_in_prison: false,
            is_transformed: false,
            is_avatar_transformed: false,
            is_protection_active: false,
            is_arrow_equipped: true,
            is_bow_equipped: false,
            is_under_stance: false,
            current_zone: String::new(),
            is_in_fortress_zone: false,
            is_in_item_use_zone: false,
            group_id: None,
            is_group_leader: false,
            group_member_count: 0,
            alliance_id: None,
            is_alliance_leader: false,
            alliance_member_count: 0,
        }
    }
    pub fn attack_speed_ms(&self) -> u64 {
        let spd = self.stats.attack_speed;
        if spd > 0 {
            spd as u64
        } else {
            1500
        }
    }
    pub fn start_quest(&mut self, quest_id: u32, timestamp: u32) {
        self.active_quests.insert(
            quest_id,
            s::QuestEntry::new(quest_id, 0, 0, [0; 4], timestamp),
        );
    }
    pub fn complete_quest(&mut self, quest_id: u32) -> Option<QuestReward> {
        if let Some(q) = self.active_quests.get_mut(&quest_id) {
            q.status = 2;
            Some(QuestReward {
                exp_reward: 5000,
                kinah_reward: 1000,
            })
        } else {
            self.active_quests.insert(
                quest_id,
                s::QuestEntry::new(quest_id, 2, 0, [0; 4], 0),
            );
            Some(QuestReward {
                exp_reward: 5000,
                kinah_reward: 1000,
            })
        }
    }
    pub fn build_quest_list(&self) -> s::QuestList {
        s::QuestList::new(self.active_quests.values().cloned().collect())
    }
    pub fn add_exp(&mut self, amount: u64) {
        self.stats.exp += amount;
        while self.stats.exp >= self.stats.exp_to_level && self.stats.level < 65 {
            self.stats.exp -= self.stats.exp_to_level;
            self.stats.level += 1;
            self.stats.exp_to_level = (self.stats.exp_to_level as f64 * 1.2) as u64;
        }
    }
    pub fn add_kinah(&mut self, _amount: u64) {
        // Kinah is tracked and persisted through Db
    }
    pub fn add_item(&mut self, item_id: u32, _quantity: u32) -> u32 {
        let unique_id = 0xC000_0000 | (self.items.len() as u32 + 1);
        self.items.insert(
            unique_id,
            RawItem::new(unique_id, item_id, 0, self.items.len() as u16, vec![0; 32]),
        );
        unique_id
    }
    pub fn sell_item(&mut self, item_unique_id: u32, quantity: u32) -> u64 {
        let item_id = self.items.remove(&item_unique_id).map(|i| i.id).unwrap_or(item_unique_id);
        let sell_price = 500 * quantity as u64;
        let now_ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        self.buyback_history.insert(
            0,
            s::SellHistoryEntry::new(item_unique_id, item_id, quantity, sell_price, now_ts),
        );
        if self.buyback_history.len() > 20 {
            self.buyback_history.truncate(20);
        }
        sell_price
    }
    pub fn build_buyback_list(&self) -> s::UserSellHistoryList {
        s::UserSellHistoryList::new(self.buyback_history.clone())
    }
    pub fn equip_item(&mut self, unique_id: u32, equip_slot: u32) -> Option<u32> {
        let slot_idx = equip_slot as usize;
        let old_item_id = self.gear.get_template_id(slot_idx);
        let new_item_id = self.items.get(&unique_id).map(|i| i.id).unwrap_or(unique_id);

        self.gear.set_slot_item(slot_idx, new_item_id);
        self.stats.secondary.main_hand_attack += 15;
        self.stats.secondary.physical_defence += 20;

        if old_item_id != 0 {
            Some(old_item_id)
        } else {
            None
        }
    }
    pub fn unequip_slot(&mut self, equip_slot: u32) -> Option<u32> {
        let slot_idx = equip_slot as usize;
        let old_item_id = self.gear.get_template_id(slot_idx);
        if old_item_id != 0 {
            self.gear.set_slot_item(slot_idx, 0);
            self.stats.secondary.main_hand_attack = self.stats.secondary.main_hand_attack.saturating_sub(15);
            self.stats.secondary.physical_defence = self.stats.secondary.physical_defence.saturating_sub(20);
            Some(old_item_id)
        } else {
            None
        }
    }
    pub fn equipment_template_ids(&self) -> [u32; 16] {
        let mut ids = [0u32; 16];
        for i in 0..16 {
            ids[i] = self.gear.get_template_id(i);
        }
        ids
    }
    pub fn recalculate_stats(&mut self, _game_data: &crate::data_loader::GameData) -> Stats {
        self.stats.clone()
    }
    pub fn build_inventory_packet(&self) -> s::LoadInventory {
        s::LoadInventory::new(self.items.values().cloned().collect())
    }
    pub fn build_mail_packet(&self) -> s::Mail {
        self.mailbox.build_mail_packet()
    }
    pub fn exp(&self) -> u64 {
        self.stats.exp
    }
    pub fn exp_required(&self) -> u64 {
        self.stats.exp_to_level
    }
    pub fn serialise_name_utf16(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;
        self.name.encode_utf16().for_each(|c| {
            buf[len + 0] = c as u8;
            buf[len + 1] = (c >> 8) as u8;
            len += 2;
        });
        len
    }
    pub fn attack(&mut self, entity: &mut Entity) -> Vec<Hit> {
        let mut dmg = 0;

        let hits = vec![
            Hit::new(110, Type::MainHand),
            Hit::new(48, Type::OffHand),
            Hit::new(4, Type::OffHand),
        ];
        for hit in &hits {
            dmg += hit.damage;
        }
        entity.hp.update(-dmg);
        self.attack_sequence = self.attack_sequence.wrapping_add(1);

        hits
    }

    /// Executa um tique de regeneração periódica de HP, MP e FP.
    pub fn regenerate(&mut self, seated: bool, in_combat: bool) -> (bool, bool) {
        let mut hp_changed = false;
        let mut mp_changed = false;

        let multiplier: f32 = if seated {
            3.0
        } else if in_combat {
            0.2
        } else {
            1.0
        };

        // HP regen
        if self.stats.hp.current < self.stats.hp.max {
            let base_rate = (self.stats.hp.max as f32 * 0.05).max(5.0);
            let gain = (base_rate * multiplier) as i32;
            self.stats.hp.current = (self.stats.hp.current + gain).min(self.stats.hp.max);
            hp_changed = true;
        }

        // MP regen
        if self.stats.mp.current < self.stats.mp.max {
            let base_rate = (self.stats.mp.max as f32 * 0.05).max(5.0);
            let gain = (base_rate * multiplier) as u32;
            self.stats.mp.current = (self.stats.mp.current + gain).min(self.stats.mp.max);
            mp_changed = true;
        }

        // FP regen (no solo)
        if self.stats.flight_time_current < self.stats.flight_time_max {
            self.stats.flight_time_current = (self.stats.flight_time_current + 2).min(self.stats.flight_time_max);
        }

        (hp_changed, mp_changed)
    }

    /// Drena FP quando o personagem está voando ou planando
    pub fn drain_flight_points(&mut self, amount: u32) -> bool {
        if self.stats.flight_time_current > amount {
            self.stats.flight_time_current -= amount;
            true
        } else {
            self.stats.flight_time_current = 0;
            false // FP esgotado
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn character_regeneration_seated_and_combat() {
        let mut c = Character::new(1, 1, Coord::new(0.0, 0.0, 0.0));
        c.stats.hp.current = 100;
        c.stats.mp.current = 100;

        // Normal standing regen
        c.regenerate(false, false);
        assert!(c.stats.hp.current > 100);
        assert!(c.stats.mp.current > 100);

        // Seated regen is significantly faster
        let hp_before = c.stats.hp.current;
        c.regenerate(true, false);
        let seated_gain = c.stats.hp.current - hp_before;

        let hp_before2 = c.stats.hp.current;
        c.regenerate(false, true); // in combat
        let combat_gain = c.stats.hp.current - hp_before2;

        assert!(seated_gain > combat_gain, "Regeneração sentado deve ser mais rápida que em combate");
    }

    #[test]
    fn character_flight_drain_and_empty() {
        let mut c = Character::new(1, 1, Coord::new(0.0, 0.0, 0.0));
        c.stats.flight_time_current = 10;

        assert!(c.drain_flight_points(5));
        assert_eq!(c.stats.flight_time_current, 5);

        assert!(!c.drain_flight_points(10), "Deve indicar que o FP esgotou");
        assert_eq!(c.stats.flight_time_current, 0);
    }
}
