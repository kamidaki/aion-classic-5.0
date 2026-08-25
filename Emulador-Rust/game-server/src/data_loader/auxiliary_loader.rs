//! Carregador de tabelas auxiliares de itens (Sets, Tinturas, Fusões, Upgrades e Receitas).

use std::collections::HashMap;
use std::path::Path;
use crate::data::item::{DyeColorTemplate, ItemComposeTemplate, ItemUpgradeTemplate, RgbColor, SetBonus, SetItemTemplate, UpgradeStep};

pub struct AuxiliaryItemData {
    pub sets: HashMap<u32, SetItemTemplate>,
    pub dyes: HashMap<u32, DyeColorTemplate>,
    pub composes: HashMap<u32, ItemComposeTemplate>,
    pub upgrades: HashMap<u32, ItemUpgradeTemplate>,
}

impl AuxiliaryItemData {
    pub fn new() -> Self {
        Self {
            sets: HashMap::new(),
            dyes: HashMap::new(),
            composes: HashMap::new(),
            upgrades: HashMap::new(),
        }
    }
}

pub fn load_set_items<P: AsRef<Path>>(path: P) -> HashMap<u32, SetItemTemplate> {
    let mut map = HashMap::new();
    let p = path.as_ref();
    if !p.exists() {
        return map;
    }

    if let Ok(content) = std::fs::read_to_string(p) {
        let mut pos = 0;
        while let Some(start_tag) = content[pos..].find("<client_setitem>") {
            let block_start = pos + start_tag;
            let block_end = match content[block_start..].find("</client_setitem>") {
                Some(e) => block_start + e + 17,
                None => break,
            };

            let block = &content[block_start..block_end];
            let id = extract_tag_u32(block, "id").unwrap_or(0);
            let name = extract_tag_str(block, "name").unwrap_or_default();
            let desc = extract_tag_str(block, "desc").unwrap_or_default();

            if id != 0 {
                let mut set_tmpl = SetItemTemplate::new(id, name, desc);
                // Extrai itens do conjunto (item1 .. item16)
                for i in 1..=16 {
                    let tag = format!("item{}", i);
                    if let Some(item_name) = extract_tag_str(block, &tag) {
                        set_tmpl.item_names.push(item_name);
                    }
                }
                // Extrai bônus de peças (piece_bonus2 .. piece_bonus6)
                for count in 2..=6 {
                    let tag = format!("piece_bonus{}", count);
                    if let Some(bonus_str) = extract_tag_str(block, &tag) {
                        set_tmpl.piece_bonuses.insert(count as u8, parse_stats_str(&bonus_str));
                    }
                }
                if let Some(fullset_str) = extract_tag_str(block, "fullset_bonus") {
                    set_tmpl.fullset_bonus = Some(parse_stats_str(&fullset_str));
                }
                map.insert(id, set_tmpl);
            }

            pos = block_end;
        }
    }

    map
}

pub fn load_dye_colors<P: AsRef<Path>>(path: P) -> HashMap<u32, DyeColorTemplate> {
    let mut map = HashMap::new();
    let p = path.as_ref();
    if !p.exists() {
        return map;
    }

    if let Ok(content) = std::fs::read_to_string(p) {
        let mut pos = 0;
        while let Some(start_tag) = content[pos..].find("<client_dye_color>") {
            let block_start = pos + start_tag;
            let block_end = match content[block_start..].find("</client_dye_color>") {
                Some(e) => block_start + e + 18,
                None => break,
            };

            let block = &content[block_start..block_end];
            let id = extract_tag_u32(block, "id").unwrap_or(0);
            let name = extract_tag_str(block, "name").unwrap_or_default();
            let desc = extract_tag_str(block, "desc").unwrap_or_default();
            let color_str = extract_tag_str(block, "dyeing_color").unwrap_or_default();
            let color = RgbColor::from_rgb_str(&color_str).unwrap_or_default();

            if id != 0 {
                let mut dye_tmpl = DyeColorTemplate {
                    id,
                    name,
                    desc,
                    color,
                    dye_item_names: Vec::new(),
                };

                let mut sub_pos = 0;
                while let Some(di_start) = block[sub_pos..].find("<dye_item>") {
                    let d_start = sub_pos + di_start + 10;
                    if let Some(di_end) = block[d_start..].find("</dye_item>") {
                        let item_n = block[d_start..d_start + di_end].trim().to_string();
                        if !item_n.is_empty() {
                            dye_tmpl.dye_item_names.push(item_n);
                        }
                        sub_pos = d_start + di_end + 11;
                    } else {
                        break;
                    }
                }

                map.insert(id, dye_tmpl);
            }

            pos = block_end;
        }
    }

    map
}

pub fn load_item_upgrades<P: AsRef<Path>>(path: P) -> HashMap<u32, ItemUpgradeTemplate> {
    let mut map = HashMap::new();
    let p = path.as_ref();
    if !p.exists() {
        return map;
    }

    if let Ok(content) = std::fs::read_to_string(p) {
        let mut pos = 0;
        while let Some(start_tag) = content[pos..].find("<client_item_upgrade>") {
            let block_start = pos + start_tag;
            let block_end = match content[block_start..].find("</client_item_upgrade>") {
                Some(e) => block_start + e + 21,
                None => break,
            };

            let block = &content[block_start..block_end];
            let id = extract_tag_u32(block, "id").unwrap_or(0);
            let name = extract_tag_str(block, "name").unwrap_or_default();
            let upgrade_item_name = extract_tag_str(block, "upgrade_item_name").unwrap_or_default();

            if id != 0 {
                let mut tmpl = ItemUpgradeTemplate {
                    id,
                    name,
                    upgrade_item_name,
                    steps: Vec::new(),
                };

                let mut sub_pos = 0;
                while let Some(d_start) = block[sub_pos..].find("<data>") {
                    let st = sub_pos + d_start;
                    if let Some(d_end) = block[st..].find("</data>") {
                        let step_block = &block[st..st + d_end + 7];
                        let step = UpgradeStep {
                            enchant_count: extract_tag_u32(step_block, "upgrade_enchant_count").unwrap_or(0),
                            rate: extract_tag_u32(step_block, "up_upgrade_item_rate").unwrap_or(10000),
                            result_item: extract_tag_str(step_block, "up_upgrade_item").unwrap_or_default(),
                            result_count: extract_tag_u32(step_block, "up_upgrade_item_cnt").unwrap_or(1),
                            required_kinah: extract_tag_u64(step_block, "need_qina").unwrap_or(0),
                            required_ap: extract_tag_u64(step_block, "need_abyss_point").unwrap_or(0),
                        };
                        tmpl.steps.push(step);
                        sub_pos = st + d_end + 7;
                    } else {
                        break;
                    }
                }

                map.insert(id, tmpl);
            }

            pos = block_end;
        }
    }

    map
}

pub fn load_item_composes<P: AsRef<Path>>(path: P) -> HashMap<u32, ItemComposeTemplate> {
    let mut map = HashMap::new();
    let p = path.as_ref();
    if !p.exists() {
        return map;
    }

    if let Ok(content) = std::fs::read_to_string(p) {
        let mut pos = 0;
        while let Some(start_tag) = content[pos..].find("<client_item_compose>") {
            let block_start = pos + start_tag;
            let block_end = match content[block_start..].find("</client_item_compose>") {
                Some(e) => block_start + e + 21,
                None => break,
            };

            let block = &content[block_start..block_end];
            let id = extract_tag_u32(block, "id").unwrap_or(0);
            let name = extract_tag_str(block, "name").unwrap_or_default();
            let group_desc = extract_tag_str(block, "compose_group_desc").unwrap_or_default();
            let fee = extract_tag_u64(block, "compose_fee_6ea").unwrap_or(0);
            let same_rate = extract_tag_u32(block, "same_rate_6ea").unwrap_or(0);
            let same_result = extract_tag_str(block, "same_result_item_6ea").unwrap_or_default();
            let up_rate = extract_tag_u32(block, "up_rate_6ea").unwrap_or(0);
            let up_result = extract_tag_str(block, "up_result_item_6ea").unwrap_or_default();
            let top_rate = extract_tag_u32(block, "top_rate_6ea").unwrap_or(0);
            let top_result = extract_tag_str(block, "top_result_item_6ea").unwrap_or_default();

            if id != 0 {
                map.insert(
                    id,
                    ItemComposeTemplate {
                        id,
                        name,
                        group_desc,
                        fee,
                        same_rate,
                        same_result,
                        up_rate,
                        up_result,
                        top_rate,
                        top_result,
                    },
                );
            }

            pos = block_end;
        }
    }

    map
}

fn parse_stats_str(s: &str) -> SetBonus {
    let mut stats = HashMap::new();
    for part in s.split(';') {
        let trimmed = part.trim();
        if let Some(space_idx) = trimmed.find(' ') {
            let key = trimmed[..space_idx].trim().to_string();
            let val_str = trimmed[space_idx + 1..].trim().trim_end_matches('%');
            if let Ok(val) = val_str.parse::<i32>() {
                stats.insert(key, val);
            }
        }
    }
    SetBonus { stats }
}

fn extract_tag_str(block: &str, tag: &str) -> Option<String> {
    let open = format!("<{}>", tag);
    let close = format!("</{}>", tag);
    let start = block.find(&open)? + open.len();
    let end = block[start..].find(&close)?;
    Some(block[start..start + end].trim().to_string())
}

fn extract_tag_u32(block: &str, tag: &str) -> Option<u32> {
    extract_tag_str(block, tag)?.parse::<u32>().ok()
}

fn extract_tag_u64(block: &str, tag: &str) -> Option<u64> {
    extract_tag_str(block, tag)?.parse::<u64>().ok()
}
