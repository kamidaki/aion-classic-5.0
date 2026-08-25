//! NpcDataHolder - Carregamento do catálogo oficial de NPCs (npcs/client_npcs.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct NpcDef {
    pub id: u32,
    pub name: String,
    pub level: u8,
    pub hp: i32,
    pub title: String,
}

#[derive(Debug, Clone, Default)]
pub struct NpcDataHolder {
    pub npcs: HashMap<u32, NpcDef>,
}

impl NpcDataHolder {
    pub fn new() -> Self {
        Self {
            npcs: HashMap::new(),
        }
    }

    pub fn get_npc_template(&self, id: u32) -> Option<&NpcDef> {
        self.npcs.get(&id)
    }

    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_client_npc = false;
        let mut id = 0u32;
        let mut name = String::new();
        let mut level = 1u8;
        let mut hp = 1000i32;
        let mut title = String::new();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_npc" {
                        in_client_npc = true;
                        id = 0;
                        name.clear();
                        level = 1;
                        hp = 1000;
                        title.clear();
                    } else if in_client_npc {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_client_npc {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => id = text.parse().unwrap_or(0),
                            "name" => name = text,
                            "level" => level = text.parse().unwrap_or(1),
                            "hp" => hp = text.parse().unwrap_or(1000),
                            "title" => title = text,
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_npc" && in_client_npc {
                        if id > 0 {
                            self.npcs.insert(
                                id,
                                NpcDef {
                                    id,
                                    name: std::mem::take(&mut name),
                                    level,
                                    hp,
                                    title: std::mem::take(&mut title),
                                },
                            );
                        }
                        in_client_npc = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.npcs.len())
    }
}
