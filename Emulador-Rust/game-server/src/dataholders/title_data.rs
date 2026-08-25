//! TitleDataHolder - Catálogo de Títulos e Atributos de Personagem (PC/client_titles.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Default)]
pub struct TitleDef {
    pub id: u16,
    pub name: String,
    pub desc: String,
    pub race: u8,
    pub bonus_hp: i32,
    pub bonus_mp: i32,
    pub bonus_speed: f32,
    pub bonus_fly_speed: f32,
    pub bonus_p_atk: i32,
    pub bonus_m_atk: i32,
    pub bonus_p_def: i32,
    pub bonus_m_def: i32,
    pub bonus_p_crit: i32,
    pub bonus_m_crit: i32,
}

#[derive(Debug, Clone, Default)]
pub struct TitleDataHolder {
    pub titles: HashMap<u16, TitleDef>,
}

impl TitleDataHolder {
    pub fn new() -> Self {
        Self {
            titles: HashMap::new(),
        }
    }

    pub fn get_title(&self, id: u16) -> Option<&TitleDef> {
        self.titles.get(&id)
    }

    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_title = false;
        let mut cur = TitleDef::default();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_title" {
                        in_title = true;
                        cur = TitleDef::default();
                    } else if in_title {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_title {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => cur.id = text.parse().unwrap_or(0),
                            "name" => cur.name = text,
                            "desc" => cur.desc = text,
                            "race" => {
                                cur.race = if text.contains("pc_light") {
                                    1
                                } else if text.contains("pc_dark") {
                                    2
                                } else {
                                    0
                                }
                            }
                            "hp" => cur.bonus_hp = text.parse().unwrap_or(0),
                            "mp" => cur.bonus_mp = text.parse().unwrap_or(0),
                            "speed" => cur.bonus_speed = text.parse().unwrap_or(0.0),
                            "fly_speed" => cur.bonus_fly_speed = text.parse().unwrap_or(0.0),
                            "phy_attack" => cur.bonus_p_atk = text.parse().unwrap_or(0),
                            "mag_attack" => cur.bonus_m_atk = text.parse().unwrap_or(0),
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_title" && in_title {
                        if cur.id > 0 {
                            self.titles.insert(cur.id, std::mem::take(&mut cur));
                        }
                        in_title = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.titles.len())
    }
}
