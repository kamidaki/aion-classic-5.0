//! DaevaPassDataHolder & AtreianPassportDataHolder - Recompensas de Passe e Login Diário

use quick_xml::events::Event;
use quick_xml::Reader;
use std::path::Path;

#[derive(Debug, Clone, Default)]
pub struct BattlePassRewardDef {
    pub id: u32,
    pub season_id: u32,
    pub level: u8,
    pub light_basic_name: String,
    pub light_basic_count: u32,
    pub light_unlock_name: String,
    pub light_unlock_count: u32,
    pub dark_basic_name: String,
    pub dark_basic_count: u32,
    pub dark_unlock_name: String,
    pub dark_unlock_count: u32,
}

#[derive(Debug, Clone, Default)]
pub struct AttendanceRewardDef {
    pub id: u32,
    pub name: String,
    pub attend_type: String,
    pub rewards: Vec<(String, u32, u8)>, // (item_name, count, permit_level)
}

#[derive(Debug, Clone, Default)]
pub struct PassDataHolder {
    pub battlepass_rewards: Vec<BattlePassRewardDef>,
    pub attendance_rewards: Vec<AttendanceRewardDef>,
}

impl PassDataHolder {
    pub fn new() -> Self {
        Self {
            battlepass_rewards: Vec::new(),
            attendance_rewards: Vec::new(),
        }
    }

    pub fn load_battlepass_rewards(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_reward = false;
        let mut cur = BattlePassRewardDef::default();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "battlepass_reward" {
                        in_reward = true;
                        cur = BattlePassRewardDef::default();
                    } else if in_reward {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_reward {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => cur.id = text.parse().unwrap_or(0),
                            "season_id" => cur.season_id = text.parse().unwrap_or(1),
                            "level" => cur.level = text.parse().unwrap_or(1),
                            "light_basic_name" => cur.light_basic_name = text,
                            "light_basic_count" => cur.light_basic_count = text.parse().unwrap_or(1),
                            "dark_basic_name" => cur.dark_basic_name = text,
                            "dark_basic_count" => cur.dark_basic_count = text.parse().unwrap_or(1),
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "battlepass_reward" && in_reward {
                        if cur.id > 0 {
                            self.battlepass_rewards.push(std::mem::take(&mut cur));
                        }
                        in_reward = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.battlepass_rewards.len())
    }

    pub fn load_attendance_rewards(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_event = false;
        let mut cur = AttendanceRewardDef::default();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "login_event" {
                        in_event = true;
                        cur = AttendanceRewardDef::default();
                    } else if in_event {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_event {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => cur.id = text.parse().unwrap_or(0),
                            "name" => cur.name = text,
                            "attend_type" => cur.attend_type = text,
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "login_event" && in_event {
                        if cur.id > 0 {
                            self.attendance_rewards.push(std::mem::take(&mut cur));
                        }
                        in_event = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.attendance_rewards.len())
    }
}
