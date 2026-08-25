//! GoodsListDataHolder - Catálogo de Itens de Venda em Lojas de NPCs

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone, Default)]
pub struct GoodsListDef {
    pub id: u32,
    pub name: String,
    pub items: Vec<String>,
}

#[derive(Debug, Clone, Default)]
pub struct GoodsListDataHolder {
    pub goods_lists: HashMap<u32, GoodsListDef>,
}

impl GoodsListDataHolder {
    pub fn new() -> Self {
        Self {
            goods_lists: HashMap::new(),
        }
    }

    pub fn get_goods_list(&self, id: u32) -> Option<&GoodsListDef> {
        self.goods_lists.get(&id)
    }

    pub fn load_from_file(&mut self, path: &Path) -> Result<usize, String> {
        let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
        reader.config_mut().trim_text(true);

        let mut buf = Vec::with_capacity(4096);
        let mut in_goods = false;
        let mut id = 0u32;
        let mut name = String::new();
        let mut items = Vec::new();
        let mut current_tag = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "goodslist" {
                        in_goods = true;
                        id = 0;
                        name.clear();
                        items.clear();
                    } else if in_goods {
                        current_tag = tag;
                    }
                }
                Ok(Event::Text(e)) => {
                    if in_goods {
                        let text = e.unescape().unwrap_or_default().trim().to_string();
                        match current_tag.as_str() {
                            "id" => id = text.parse().unwrap_or(0),
                            "name" => name = text,
                            "item" => items.push(text),
                            _ => {}
                        }
                    }
                }
                Ok(Event::End(e)) => {
                    let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                    if tag == "goodslist" && in_goods {
                        if id > 0 {
                            self.goods_lists.insert(
                                id,
                                GoodsListDef {
                                    id,
                                    name: std::mem::take(&mut name),
                                    items: std::mem::take(&mut items),
                                },
                            );
                        }
                        in_goods = false;
                    }
                    current_tag.clear();
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(e.to_string()),
                _ => {}
            }
            buf.clear();
        }

        Ok(self.goods_lists.len())
    }
}
