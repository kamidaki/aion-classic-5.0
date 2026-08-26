//! GatherableDataHolder - Catálogo de Recursos Coletáveis (Gather/client_gather_src.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Default)]
pub struct GatherDef {
    pub id: u32,
    pub name: String,
    pub desc: String,
    pub harvest_skill: String,
    pub skill_level: u16,
    pub material1: String,
    pub harvest_count: u32,
}

#[derive(Debug, Clone, Default)]
pub struct GatherableDataHolder {
    pub gather_sources: HashMap<u32, GatherDef>,
}

impl GatherableDataHolder {
    pub fn new() -> Self {
        Self {
            gather_sources: HashMap::new(),
        }
    }

    pub fn get_gather_source(&self, id: u32) -> Option<&GatherDef> {
        self.gather_sources.get(&id)
    }

    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_gather = false;
        let mut cur = GatherDef::default();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "gather_src" {
                        in_gather = true;
                        cur = GatherDef::default();
                    } else if in_gather {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_gather {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => cur.id = text.parse().unwrap_or(0),
                            "name" => cur.name = text,
                            "desc" => cur.desc = text,
                            "harvest_skill" => cur.harvest_skill = text,
                            "skill_level" => cur.skill_level = text.parse().unwrap_or(1),
                            "material1" => cur.material1 = text,
                            "harvest_count" => cur.harvest_count = text.parse().unwrap_or(3),
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "gather_src" && in_gather {
                        if cur.id > 0 {
                            self.gather_sources.insert(cur.id, std::mem::take(&mut cur));
                        }
                        in_gather = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.gather_sources.len())
    }
}
