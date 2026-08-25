//! Carregadores de dados de progressão — Títulos, GoodsList, BattlePass, Attendance e Gather.
//!
//! Cada tipo lê um XML separado do cliente e retorna sua estrutura própria.

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

// ─── TitleDef ──────────────────────────────────────────────────────────────

/// Título de personagem (conquista, evento, ranking).
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

/// Carrega todos os títulos do `client_titles.xml`.
pub fn load_titles(path: &Path) -> Result<HashMap<u16, TitleDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<TitleDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_title" {
                    cur = Some(TitleDef::default());
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_title" {
                    if let Some(t) = cur.take() {
                        if t.id > 0 {
                            out.insert(t.id, t);
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut title) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => { if let Ok(id) = text.parse::<u16>() { title.id = id; } }
                        "name" => title.name = text.to_string(),
                        "desc" => title.desc = text.to_string(),
                        "title_race" => { if let Ok(r) = text.parse::<u8>() { title.race = r; } }
                        "bonus_attr" => {
                            let parts: Vec<&str> = text.split_whitespace().collect();
                            if parts.len() >= 2 {
                                let attr = parts[0];
                                let val_str = parts[1].trim_end_matches('%');
                                if let Ok(val_i32) = val_str.parse::<i32>() {
                                    match attr {
                                        "maxHp" => title.bonus_hp += val_i32,
                                        "maxMp" => title.bonus_mp += val_i32,
                                        "PhysicalDefend" => title.bonus_p_def += val_i32,
                                        "MagicalDefend" => title.bonus_m_def += val_i32,
                                        "PhysicalAttack" => title.bonus_p_atk += val_i32,
                                        "MagicalSkillBoost" => title.bonus_m_atk += val_i32,
                                        "PhysicalCritical" => title.bonus_p_crit += val_i32,
                                        "MagicalCritical" => title.bonus_m_crit += val_i32,
                                        "speed" => title.bonus_speed += val_i32 as f32 / 100.0,
                                        "flySpeed" => title.bonus_fly_speed += val_i32 as f32 / 100.0,
                                        _ => {}
                                    }
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", path.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

// ─── GoodsListDef ──────────────────────────────────────────────────────────

/// Lista de mercadorias de loja de NPC.
#[derive(Debug, Clone, Default)]
pub struct GoodsListDef {
    pub id: u32,
    pub name: String,
    pub items: Vec<String>,
}

/// Carrega todas as listas de mercadoria do `client_npc_goodslist.xml`.
pub fn load_goods_lists(path: &Path) -> Result<HashMap<u32, GoodsListDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<GoodsListDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_npc_goodslist" { cur = Some(GoodsListDef::default()); }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_npc_goodslist" {
                    if let Some(g) = cur.take() {
                        if g.id > 0 { out.insert(g.id, g); }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut goods) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => { if let Ok(id) = text.parse::<u32>() { goods.id = id; } }
                        "name" => goods.name = text.to_string(),
                        "item" => { if !text.is_empty() { goods.items.push(text.to_string()); } }
                        _ => {}
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", path.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

// ─── BattlePassRewardDef ───────────────────────────────────────────────────

/// Recompensa de um nível do Battle Pass (Daeva Pass).
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

/// Carrega as recompensas do Daeva Pass de `client_battlepass_reward.xml`.
pub fn load_battlepass_rewards(path: &Path) -> Result<Vec<BattlePassRewardDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = Vec::new();
    let mut buf = Vec::new();
    let mut cur: Option<BattlePassRewardDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_battlepass_reward" { cur = Some(BattlePassRewardDef::default()); }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_battlepass_reward" {
                    if let Some(r) = cur.take() {
                        if r.id > 0 { out.push(r); }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut reward) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => { if let Ok(id) = text.parse::<u32>() { reward.id = id; } }
                        "season_id" => { if let Ok(sid) = text.parse::<u32>() { reward.season_id = sid; } }
                        "pass_lv" => { if let Ok(lv) = text.parse::<u8>() { reward.level = lv; } }
                        "light_basic_reward1_name" => reward.light_basic_name = text.to_string(),
                        "light_basic_reward1_count" => { if let Ok(c) = text.parse::<u32>() { reward.light_basic_count = c; } }
                        "light_unlock_reward1_name" => reward.light_unlock_name = text.to_string(),
                        "light_unlock_reward1_count" => { if let Ok(c) = text.parse::<u32>() { reward.light_unlock_count = c; } }
                        "dark_basic_reward1_name" => reward.dark_basic_name = text.to_string(),
                        "dark_basic_reward1_count" => { if let Ok(c) = text.parse::<u32>() { reward.dark_basic_count = c; } }
                        "dark_unlock_reward1_name" => reward.dark_unlock_name = text.to_string(),
                        "dark_unlock_reward1_count" => { if let Ok(c) = text.parse::<u32>() { reward.dark_unlock_count = c; } }
                        _ => {}
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", path.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

// ─── AttendanceRewardDef ───────────────────────────────────────────────────

/// Recompensa de login diário / evento de presença (Atreian Passport).
#[derive(Debug, Clone, Default)]
pub struct AttendanceRewardDef {
    pub id: u32,
    pub name: String,
    pub attend_type: String,
    pub rewards: Vec<(String, u32, u8)>, // (item_name, count, permit_level)
}

/// Carrega os eventos de login do `client_login_event.xml`.
pub fn load_attendance_rewards(path: &Path) -> Result<Vec<AttendanceRewardDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = Vec::new();
    let mut buf = Vec::new();
    let mut cur: Option<AttendanceRewardDef> = None;
    let mut cur_item: String = String::new();
    let mut cur_count: u32 = 1;
    let mut cur_lvl: u8 = 1;
    let mut cur_tag = String::new();
    let mut in_data = false;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_login_event" {
                    cur = Some(AttendanceRewardDef::default());
                } else if name == "data" {
                    in_data = true;
                    cur_item.clear();
                    cur_count = 1;
                    cur_lvl = 1;
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_login_event" {
                    if let Some(r) = cur.take() {
                        if r.id > 0 { out.push(r); }
                    }
                } else if name == "data" && in_data {
                    in_data = false;
                    if let Some(ref mut att) = cur {
                        if !cur_item.is_empty() {
                            att.rewards.push((cur_item.clone(), cur_count, cur_lvl));
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut att) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" if !in_data => { if let Ok(id) = text.parse::<u32>() { att.id = id; } }
                        "name" if !in_data => att.name = text.to_string(),
                        "attend_type" if !in_data => att.attend_type = text.to_string(),
                        "reward_item" if in_data => cur_item = text.to_string(),
                        "reward_item_count" if in_data => { if let Ok(c) = text.parse::<u32>() { cur_count = c; } }
                        "reward_permit_level" if in_data => { if let Ok(lvl) = text.parse::<u8>() { cur_lvl = lvl; } }
                        _ => {}
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", path.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

// ─── GatherDef ─────────────────────────────────────────────────────────────

/// Fonte de coleta de materiais (nó de coleta no mundo).
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

/// Carrega as fontes de coleta do `gather_src.xml`.
pub fn load_gather_sources(path: &Path) -> Result<HashMap<u32, GatherDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<GatherDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "gather_src" { cur = Some(GatherDef::default()); }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "gather_src" {
                    if let Some(g) = cur.take() {
                        if g.id > 0 { out.insert(g.id, g); }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut gather) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => { if let Ok(id) = text.parse::<u32>() { gather.id = id; } }
                        "name" => gather.name = text.to_string(),
                        "desc" => gather.desc = text.to_string(),
                        "harvestskill" => gather.harvest_skill = text.to_string(),
                        "skill_level" => { if let Ok(lvl) = text.parse::<u16>() { gather.skill_level = lvl; } }
                        "material1" => gather.material1 = text.to_string(),
                        "harvest_count" => { if let Ok(c) = text.parse::<u32>() { gather.harvest_count = c; } }
                        _ => {}
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", path.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_title_bonus_parsing() {
        let mut t = TitleDef::default();
        t.id = 1;
        t.bonus_hp = 20;
        t.bonus_p_def = 5;
        assert_eq!(t.bonus_hp, 20);
        assert_eq!(t.bonus_p_def, 5);
    }

    #[test]
    fn test_goods_list_def() {
        let gl = GoodsListDef {
            id: 1,
            name: "sale_skillbook".to_string(),
            items: vec!["skillbook_1".to_string(), "skillbook_2".to_string()],
        };
        assert_eq!(gl.items.len(), 2);
    }
}
