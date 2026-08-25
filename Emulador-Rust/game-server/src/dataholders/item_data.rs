//! ItemDataHolder - Carregamento do catálogo oficial de itens (items/client_items.xml)

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    Nenhum,
    Arma { principal: u64, secundario: u64, duas_maos: bool },
    Escudo(u64),
    Armadura(u64),
    Acessorio { principal: u64, secundario: u64 },
}

#[derive(Debug, Clone)]
pub struct ItemDef {
    pub id: u32,
    pub name: String,
    pub mascara: u16,
    pub slot: Slot,
    pub tecido: bool,
}

#[derive(Debug, Clone, Default)]
pub struct ItemDataHolder {
    pub items: HashMap<u32, ItemDef>,
}

impl ItemDataHolder {
    pub fn new() -> Self {
        Self {
            items: HashMap::new(),
        }
    }

    pub fn get_item_template(&self, id: u32) -> Option<&ItemDef> {
        self.items.get(&id)
    }

    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_client_item = false;
        let mut id = 0u32;
        let mut name = String::new();
        let mut slot_str = String::new();
        let mut can_trade = true;
        let mut can_sell = true;
        let mut can_deposit = true;
        let mut can_split = false;
        let mut armor_type = String::new();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_item" {
                        in_client_item = true;
                        id = 0;
                        name.clear();
                        slot_str.clear();
                        can_trade = true;
                        can_sell = true;
                        can_deposit = true;
                        can_split = false;
                        armor_type.clear();
                    } else if in_client_item {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_client_item {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => id = text.parse().unwrap_or(0),
                            "name" => name = text,
                            "equipment_slots" => slot_str = text,
                            "can_trade" => can_trade = text != "0" && text != "false",
                            "can_sell" => can_sell = text != "0" && text != "false",
                            "can_deposit_to_character_warehouse" => {
                                can_deposit = text != "0" && text != "false"
                            }
                            "can_split" => can_split = text == "1" || text == "true",
                            "armor_type" => armor_type = text,
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "client_item" && in_client_item {
                        if id > 0 {
                            let slot = parse_slot(&slot_str);
                            let tecido = armor_type == "robe" || armor_type == "clothes";
                            let mut mascara = 0u16;
                            if can_trade { mascara |= 0x0001; }
                            if can_sell { mascara |= 0x0002; }
                            if can_deposit { mascara |= 0x0004; }
                            if can_split { mascara |= 0x0008; }

                            self.items.insert(
                                id,
                                ItemDef {
                                    id,
                                    name: std::mem::take(&mut name),
                                    mascara,
                                    slot,
                                    tecido,
                                },
                            );
                        }
                        in_client_item = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.items.len())
    }
}

fn parse_slot(slot_str: &str) -> Slot {
    match slot_str {
        "main" => Slot::Arma { principal: 1, secundario: 0, duas_maos: true },
        "main_or_sub" => Slot::Arma { principal: 1, secundario: 2, duas_maos: false },
        "sub" => Slot::Escudo(2),
        "torso" => Slot::Armadura(8),
        "leg" => Slot::Armadura(4096),
        "shoulder" => Slot::Armadura(2048),
        "glove" => Slot::Armadura(16),
        "foot" => Slot::Armadura(32),
        "head" => Slot::Acessorio { principal: 4, secundario: 4 },
        "neck" => Slot::Acessorio { principal: 1024, secundario: 1024 },
        "waist" => Slot::Acessorio { principal: 65536, secundario: 65536 },
        "ear" => Slot::Acessorio { principal: 256, secundario: 512 },
        "finger" => Slot::Acessorio { principal: 8192, secundario: 16384 },
        "wing" => Slot::Acessorio { principal: 131072, secundario: 131072 },
        _ => Slot::Nenhum,
    }
}
