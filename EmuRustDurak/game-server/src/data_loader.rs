//! Loads game data from the extracted client XML catalogues.
//!
//! The client ships with binary XML in its .pak archives; our `pak` crate
//! extracts them, and `bxml` converts them to text XML. This module reads the
//! resulting files at server startup so we stop hard-coding item/NPC IDs.
//!
//! Only the fields we actually need are parsed — the full catalogue is
//! hundreds of megabytes.

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct NpcDef {
    pub id: u32,
    pub name: String,
}

#[derive(Debug, Clone)]
pub struct ItemDef {
    pub id: u32,
    pub name: String,
}

#[derive(Debug, Default)]
pub struct GameData {
    pub npcs: HashMap<u32, NpcDef>,
    pub items: HashMap<u32, ItemDef>,
}

impl GameData {
    pub fn load(data_dir: &Path) -> Self {
        let mut gd = Self::default();
        let npcs_path = data_dir.join("npcs").join("client_npcs.xml");
        let items_path = data_dir.join("items").join("client_items.xml");

        match load_npcs(&npcs_path) {
            Ok(npcs) => {
                println!("INFO: loaded {} NPCs from {}", npcs.len(), npcs_path.display());
                gd.npcs = npcs;
            }
            Err(e) => eprintln!("WARN: skipping NPCs ({}): {e}", npcs_path.display()),
        }

        match load_items(&items_path) {
            Ok(items) => {
                println!("INFO: loaded {} items from {}", items.len(), items_path.display());
                gd.items = items;
            }
            Err(e) => eprintln!("WARN: skipping items ({}): {e}", items_path.display()),
        }

        gd
    }
}

fn load_npcs(path: &Path) -> Result<HashMap<u32, NpcDef>, String> {
    load_catalog(path, b"npc_client")
        .map(|v| v.into_iter().map(|(id, name)| (id, NpcDef { id, name })).collect())
}

fn load_items(path: &Path) -> Result<HashMap<u32, ItemDef>, String> {
    load_catalog(path, b"client_item")
        .map(|v| v.into_iter().map(|(id, name)| (id, ItemDef { id, name })).collect())
}

/// Streaming parse: for each element named `record_tag`, extract the `<id>`
/// and `<name>` children. Skips records without a parseable id.
fn load_catalog(path: &Path, record_tag: &[u8]) -> Result<Vec<(u32, String)>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut buf = Vec::new();
    let mut out = Vec::new();

    let mut depth = 0usize;
    let mut in_record = false;
    let mut record_depth = 0usize;
    let mut current_field: Option<Vec<u8>> = None;
    let mut cur_id: Option<u32> = None;
    let mut cur_name: Option<String> = None;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if !in_record && name == record_tag {
                    in_record = true;
                    record_depth = depth;
                    cur_id = None;
                    cur_name = None;
                    current_field = None;
                } else if in_record && depth == record_depth + 1 {
                    current_field = Some(name);
                }
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_record && depth == record_depth && name == record_tag {
                    if let Some(id) = cur_id.take() {
                        out.push((id, cur_name.take().unwrap_or_default()));
                    }
                    in_record = false;
                    current_field = None;
                    cur_id = None;
                    cur_name = None;
                } else if in_record && depth == record_depth + 1 {
                    current_field = None;
                }
                depth = depth.saturating_sub(1);
            }
            Ok(Event::Text(t)) => {
                if let Some(field) = &current_field {
                    if in_record && depth == record_depth + 1 {
                        let text = t.unescape().unwrap_or_default();
                        match field.as_slice() {
                            b"id" => {
                                cur_id = text.trim().parse().ok();
                            }
                            b"name" => {
                                cur_name = Some(text.into_owned());
                            }
                            _ => {}
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => {
                return Err(format!("parse {}: {e}", path.display()));
            }
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}
