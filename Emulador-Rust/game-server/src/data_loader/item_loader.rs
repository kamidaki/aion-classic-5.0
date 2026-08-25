//! Carregador de itens do cliente Aion (`client_items.xml`).
//!
//! Realiza streaming de alta velocidade, extraindo templates completos de itens:
//! - Slots, Mãos, Asas, Elmos, Armaduras, Acessórios e Máscaras
//! - Restrições de Classe, Nível, Raça e Gênero
//! - Atributos de Combate Físicos e Mágicos
//! - Modificadores: Manastones, Fusão (Armsfusion), Encantamento, Tintura (Dye), Remodelagem (Skin)
//! - Associação automática de nomes reais através da tabela de strings oficial.

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use crate::data::item::{
    AccessoryType, ArmorType, AttackType, GenderPermitted, ItemCategory, ItemModifiers,
    ItemQuality, ItemRestrictions, ItemSlot, ItemStats, ItemTemplate, PlayerClassMask,
    RacePermitted, WeaponType,
};
use super::string_loader::StringTable;

/// Representação legada de ItemDef mantida para compatibilidade com o protocolo de rede.
#[derive(Debug, Clone)]
pub struct ItemDef {
    pub id: u32,
    pub name: String,
    pub mascara: u16,
    pub slot: Slot,
    pub tecido: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    Nenhum,
    Arma { principal: u64, secundario: u64, duas_maos: bool },
    Escudo(u64),
    Armadura(u64),
    Acessorio { principal: u64, secundario: u64 },
}

pub const SLOTS_DE_CORPO: [&str; 5] = ["torso", "leg", "glove", "foot", "shoulder"];

pub fn slot_do_catalogo(texto: &str) -> Slot {
    const MAO_PRINCIPAL: u64 = 1;
    const MAO_SECUNDARIA: u64 = 1 << 1;
    let bit = |n: u32| 1u64 << n;

    match texto.trim().to_lowercase().as_str() {
        "main_or_sub" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: false,
        },
        "main" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: true,
        },
        "sub" => Slot::Escudo(MAO_SECUNDARIA),
        "torso" => Slot::Armadura(bit(3)),
        "glove" => Slot::Armadura(bit(4)),
        "foot" => Slot::Armadura(bit(5)),
        "shoulder" => Slot::Armadura(bit(11)),
        "leg" => Slot::Armadura(bit(12)),
        "head" => Slot::Acessorio { principal: bit(2), secundario: 0 },
        "right_or_left_ear" => Slot::Acessorio { principal: bit(6), secundario: bit(7) },
        "right_or_left_finger" => Slot::Acessorio { principal: bit(8), secundario: bit(9) },
        "neck" => Slot::Acessorio { principal: bit(10), secundario: 0 },
        "wing" => Slot::Acessorio { principal: bit(15), secundario: 0 },
        "waist" => Slot::Acessorio { principal: bit(16), secundario: 0 },
        _ => Slot::Nenhum,
    }
}

pub fn mascara_do_item(campos: &HashMap<&str, &str>, slot_texto: &str) -> u16 {
    let ligado = |nome: &str| {
        campos
            .get(nome)
            .map(|v| v.trim().eq_ignore_ascii_case("true"))
            .unwrap_or(false)
    };
    let empilhavel = campos
        .get("max_stack_count")
        .and_then(|v| v.trim().parse::<u32>().ok())
        .map(|n| n != 1)
        .unwrap_or(false);

    let mut m: u16 = 0;
    if ligado("can_exchange") { m |= 1 << 2; }
    if ligado("can_sell_to_npc") { m |= 1 << 3; }
    if ligado("can_deposit_to_character_warehouse") { m |= 1 << 5; }
    if ligado("can_deposit_to_account_warehouse") { m |= 1 << 6; }
    if ligado("can_deposit_to_guild_warehouse") { m |= 1 << 7; }
    if ligado("breakable") { m |= 1 << 8; }
    if ligado("soul_bind") { m |= 1 << 9; }
    if !empilhavel && slot_texto.is_empty() { m |= 1 << 10; }
    if ligado("remove_when_logout") { m |= 1 << 15; }

    m
}

/// Carregador de streaming otimizado que produz tanto `HashMap<u32, ItemTemplate>` quanto `HashMap<u32, ItemDef>`.
pub fn load_items_full<P: AsRef<Path>>(
    path: P,
    strings: &StringTable,
) -> (HashMap<u32, ItemTemplate>, HashMap<u32, ItemDef>) {
    let mut templates = HashMap::with_capacity(80000);
    let mut legacy_defs = HashMap::with_capacity(80000);

    let p = path.as_ref();
    if !p.exists() {
        return (templates, legacy_defs);
    }

    let file = match File::open(p) {
        Ok(f) => f,
        Err(_) => return (templates, legacy_defs),
    };

    let reader = BufReader::with_capacity(1024 * 1024, file);
    let mut in_item = false;
    let mut item_fields: HashMap<String, String> = HashMap::with_capacity(64);

    for line in reader.lines().flatten() {
        let trimmed = line.trim();
        if trimmed.starts_with("<client_item>") {
            in_item = true;
            item_fields.clear();
            continue;
        }

        if trimmed.starts_with("</client_item>") {
            if in_item {
                if let Some(id_str) = item_fields.get("id") {
                    if let Ok(id) = id_str.parse::<u32>() {
                        let tmpl = build_item_template(id, &item_fields, strings);
                        let legacy_def = ItemDef {
                            id: tmpl.id,
                            name: tmpl.name.clone(),
                            mascara: tmpl.mask,
                            slot: slot_do_catalogo(item_fields.get("equipment_slots").map(|s| s.as_str()).unwrap_or("")),
                            tecido: SLOTS_DE_CORPO.iter().any(|&s| item_fields.get("equipment_slots").map(|v| v.as_str()) == Some(s)),
                        };

                        templates.insert(id, tmpl);
                        legacy_defs.insert(id, legacy_def);
                    }
                }
                in_item = false;
            }
            continue;
        }

        if in_item {
            if let Some(tag_open) = trimmed.find('<') {
                if let Some(tag_close) = trimmed[tag_open + 1..].find('>') {
                    let tag_name = &trimmed[tag_open + 1..tag_open + 1 + tag_close];
                    let close_tag = format!("</{}>", tag_name);
                    if let Some(val_end) = trimmed.find(&close_tag) {
                        let val_start = tag_open + 1 + tag_close + 1;
                        if val_end >= val_start {
                            let value = trimmed[val_start..val_end].trim().to_string();
                            item_fields.insert(tag_name.to_string(), value);
                        }
                    }
                }
            }
        }
    }

    println!("INFO: Loaded {} complete item templates from {}", templates.len(), p.display());
    (templates, legacy_defs)
}

/// Carrega apenas a lista compatível legada para `GameData`.
pub fn load_items<P: AsRef<Path>>(path: P) -> HashMap<u32, ItemDef> {
    let dummy_strings = StringTable::new();
    let (_, defs) = load_items_full(path, &dummy_strings);
    defs
}

fn build_item_template(id: u32, fields: &HashMap<String, String>, strings: &StringTable) -> ItemTemplate {
    let name = fields.get("name").cloned().unwrap_or_default();
    let desc = fields.get("desc").cloned().unwrap_or_default();
    let clean_name = strings
        .get(&desc)
        .map(|s| s.to_string())
        .unwrap_or_else(|| name.clone());

    let eq_slot_str = fields.get("equipment_slots").map(|s| s.as_str()).unwrap_or("");
    let slot = ItemSlot::from_xml_str(eq_slot_str);

    let weapon_type = fields.get("weapon_type").and_then(|w| WeaponType::from_xml_str(w));
    let armor_type = fields.get("armor_type").and_then(|a| ArmorType::from_xml_str(a));
    let accessory_type = fields.get("equipment_slots").and_then(|a| AccessoryType::from_xml_str(a));

    let quality = fields.get("quality").map(|q| ItemQuality::from_xml_str(q)).unwrap_or_default();
    let level = fields.get("level").and_then(|l| l.parse::<u8>().ok()).unwrap_or(1);
    let price = fields.get("price").and_then(|p| p.parse::<u64>().ok()).unwrap_or(0);
    let max_stack_count = fields.get("max_stack_count").and_then(|s| s.parse::<u32>().ok()).unwrap_or(1);

    let mut str_map: HashMap<&str, &str> = HashMap::with_capacity(fields.len());
    for (k, v) in fields {
        str_map.insert(k.as_str(), v.as_str());
    }
    let mask = mascara_do_item(&str_map, eq_slot_str);

    // Categoria do item
    let category = if weapon_type.is_some() {
        ItemCategory::Weapon
    } else if armor_type.is_some() {
        ItemCategory::Armor
    } else if accessory_type.is_some() {
        ItemCategory::Accessory
    } else if name.contains("stigma") {
        ItemCategory::Stigma
    } else if name.contains("dye") {
        ItemCategory::Dye
    } else if name.contains("skin") {
        ItemCategory::Skin
    } else if max_stack_count > 1 && (name.contains("potion") || name.contains("scroll") || name.contains("food")) {
        ItemCategory::Consumable
    } else {
        ItemCategory::Normal
    };

    // Estatísticas de combate
    let stats = ItemStats {
        min_damage: fields.get("min_damage").and_then(|v| v.parse().ok()).unwrap_or(0),
        max_damage: fields.get("max_damage").and_then(|v| v.parse().ok()).unwrap_or(0),
        attack_type: if fields.get("attack_type").map(|v| v == "magical").unwrap_or(false) {
            AttackType::Magical
        } else {
            AttackType::Physical
        },
        attack_delay: fields.get("attack_delay").and_then(|v| v.parse().ok()).unwrap_or(0),
        hit_count: fields.get("hit_count").and_then(|v| v.parse().ok()).unwrap_or(1),
        attack_range: fields.get("attack_range").and_then(|v| v.parse().ok()).unwrap_or(1.5),
        hit_accuracy: fields.get("hit_accuracy").and_then(|v| v.parse().ok()).unwrap_or(0),
        critical: fields.get("critical").and_then(|v| v.parse().ok()).unwrap_or(0),
        magical_skill_boost: fields.get("magical_skill_boost").and_then(|v| v.parse().ok()).unwrap_or(0),
        magical_hit_accuracy: fields.get("magical_hit_accuracy").and_then(|v| v.parse().ok()).unwrap_or(0),
        physical_defend: fields.get("physical_defend").and_then(|v| v.parse().ok()).unwrap_or(0),
        magical_defend: fields.get("magical_defend").and_then(|v| v.parse().ok()).unwrap_or(0),
        magic_resist: fields.get("magic_resist").and_then(|v| v.parse().ok()).unwrap_or(0),
        parry: fields.get("parry").and_then(|v| v.parse().ok()).unwrap_or(0),
        block: fields.get("block").and_then(|v| v.parse().ok()).unwrap_or(0),
        damage_reduce: fields.get("damage_reduce").and_then(|v| v.parse().ok()).unwrap_or(0),
        dodge: fields.get("dodge").and_then(|v| v.parse().ok()).unwrap_or(0),
        max_hp: fields.get("max_hp").and_then(|v| v.parse().ok()).unwrap_or(0),
        max_mp: fields.get("max_mp").and_then(|v| v.parse().ok()).unwrap_or(0),
        speed: fields.get("speed").and_then(|v| v.parse().ok()).unwrap_or(0),
        fly_speed: fields.get("fly_speed").and_then(|v| v.parse().ok()).unwrap_or(0),
        fly_time: fields.get("fly_time").and_then(|v| v.parse().ok()).unwrap_or(0),
        pvp_attack_ratio: fields.get("pvp_attack_ratio").and_then(|v| v.parse().ok()).unwrap_or(0.0),
        pvp_defend_ratio: fields.get("pvp_defend_ratio").and_then(|v| v.parse().ok()).unwrap_or(0.0),
    };

    // Máscara de classes
    let mut class_mask_val = 0u32;
    if fields.get("warrior").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::WARRIOR.0; }
    if fields.get("fighter").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::GLADIATOR.0; }
    if fields.get("knight").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::TEMPLAR.0; }
    if fields.get("scout").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::SCOUT.0; }
    if fields.get("assassin").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::ASSASSIN.0; }
    if fields.get("ranger").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::RANGER.0; }
    if fields.get("mage").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::MAGE.0; }
    if fields.get("wizard").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::SORCERER.0; }
    if fields.get("elementalist").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::SPIRITMASTER.0; }
    if fields.get("priest").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::PRIEST.0; }
    if fields.get("cleric").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::CLERIC.0; }
    if fields.get("chanter").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::CHANTER.0; }
    if fields.get("gunner").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::GUNNER.0; }
    if fields.get("thunderer").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::AETHERTECH.0; }
    if fields.get("orchestrator").map(|v| v == "1").unwrap_or(false) { class_mask_val |= PlayerClassMask::SONGWEAVER.0; }

    let restrictions = ItemRestrictions {
        min_level: level,
        max_level: fields.get("max_level").and_then(|v| v.parse().ok()).unwrap_or(65),
        class_mask: PlayerClassMask(class_mask_val),
        race: match fields.get("race_permitted").map(|s| s.as_str()) {
            Some("pc_light") => RacePermitted::Elyos,
            Some("pc_dark") => RacePermitted::Asmodian,
            _ => RacePermitted::All,
        },
        gender: match fields.get("gender_permitted").map(|s| s.as_str()) {
            Some("male") => GenderPermitted::Male,
            Some("female") => GenderPermitted::Female,
            _ => GenderPermitted::All,
        },
        soul_bind: fields.get("soul_bind").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        can_exchange: fields.get("can_exchange").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        can_sell_to_npc: fields.get("can_sell_to_npc").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(true),
        can_deposit_character_warehouse: fields.get("can_deposit_to_character_warehouse").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(true),
        can_deposit_account_warehouse: fields.get("can_deposit_to_account_warehouse").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(true),
        can_deposit_guild_warehouse: fields.get("can_deposit_to_guild_warehouse").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(true),
        breakable: fields.get("breakable").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(true),
    };

    let modifiers = ItemModifiers {
        option_slot_bonus: fields.get("option_slot_bonus").and_then(|v| v.parse().ok()).unwrap_or(0),
        no_enchant: fields.get("no_enchant").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        can_proc_enchant: fields.get("can_proc_enchant").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        can_composite: fields.get("can_composite_weapon").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        cannot_changeskin: fields.get("cannot_changeskin").map(|v| v == "1" || v.eq_ignore_ascii_case("true")).unwrap_or(false),
        dye: fields.get("dye").map(|v| v.eq_ignore_ascii_case("true")).unwrap_or(false),
        soul_bind: restrictions.soul_bind,
        charge_capacity: fields.get("charge_capacity").and_then(|v| v.parse().ok()).unwrap_or(0),
        max_enchant_level: 15,
    };

    ItemTemplate {
        id,
        name,
        clean_name,
        desc,
        category,
        quality,
        slot,
        weapon_type,
        armor_type,
        accessory_type,
        level,
        price,
        max_stack_count,
        mask,
        stats,
        restrictions,
        modifiers,
    }
}
