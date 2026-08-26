//! SkillDataHolder & SkillTreeDataHolder - Catálogo de Habilidades e Árvore de Aprendizado

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct SkillLearn {
    pub classe: String,
    pub nivel: u16,
    pub skill_id: u32,
}

#[derive(Debug, Clone, Default)]
pub struct SkillDataHolder {
    pub skill_targets_enemy: HashMap<u32, bool>,
    pub skill_learn_tree: Vec<SkillLearn>,
}

impl SkillDataHolder {
    pub fn new() -> Self {
        Self {
            skill_targets_enemy: HashMap::new(),
            skill_learn_tree: Vec::new(),
        }
    }

    pub fn is_enemy_target(&self, skill_id: u32) -> bool {
        self.skill_targets_enemy.get(&skill_id).copied().unwrap_or(true)
    }

    pub fn get_skills_for_class(&self, class_name: &str, level: u16) -> Vec<u32> {
        self.skill_learn_tree
            .iter()
            .filter(|sl| sl.nivel <= level && (sl.classe.eq_ignore_ascii_case(class_name) || sl.classe.eq_ignore_ascii_case("all")))
            .map(|sl| sl.skill_id)
            .collect()
    }

    pub fn load_skills_catalog(&mut self, skills_path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(skills_path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_client_skill = false;
        let mut id = 0u32;
        let mut first_target = String::new();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_skill" {
                        in_client_skill = true;
                        id = 0;
                        first_target.clear();
                    } else if in_client_skill {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_client_skill {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => id = text.parse().unwrap_or(0),
                            "first_target" => first_target = text,
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_skill" && in_client_skill {
                        if id > 0 {
                            let is_enemy = first_target.eq_ignore_ascii_case("target")
                                || first_target.eq_ignore_ascii_case("enemy")
                                || first_target.is_empty();
                            self.skill_targets_enemy.insert(id, is_enemy);
                        }
                        in_client_skill = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.skill_targets_enemy.len())
    }

    pub fn load_learn_tree(&mut self, learns_path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(learns_path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_rule = false;
        let mut classe = String::new();
        let mut nivel = 1u16;
        let mut skill_id = 0u32;
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_skill_learn" {
                        in_rule = true;
                        classe.clear();
                        nivel = 1;
                        skill_id = 0;
                    } else if in_rule {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_rule {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "class" => classe = text,
                            "level" => nivel = text.parse().unwrap_or(1),
                            "skill_id" => skill_id = text.parse().unwrap_or(0),
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_skill_learn" && in_rule {
                        if skill_id > 0 {
                            self.skill_learn_tree.push(SkillLearn {
                                classe: std::mem::take(&mut classe),
                                nivel,
                                skill_id,
                            });
                        }
                        in_rule = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.skill_learn_tree.len())
    }
}
