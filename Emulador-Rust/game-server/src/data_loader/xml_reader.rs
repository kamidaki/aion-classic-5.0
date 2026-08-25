//! Utilitários genéricos de parse XML — base de todos os loaders de catálogos do cliente.

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;

/// Streaming parse: para cada elemento `record_tag`, extrai `<id>` e `<name>`.
/// Ignora registros sem id numérico.
pub fn load_catalog(path: &Path, record_tag: &[u8]) -> Result<Vec<(u32, String)>, String> {
    let registros = load_catalog_campos(path, record_tag, &[b"name"])?;
    Ok(registros
        .into_iter()
        .map(|(id, campos)| (id, campos.get(b"name".as_slice()).cloned().unwrap_or_default()))
        .collect())
}

/// Percorre o XML e guarda os campos pedidos de cada `record_tag`, em vez de só o nome.
pub fn load_catalog_campos(
    path: &Path,
    record_tag: &[u8],
    campos_pedidos: &[&[u8]],
) -> Result<Vec<(u32, HashMap<Vec<u8>, String>)>, String> {
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
    let mut cur_campos: HashMap<Vec<u8>, String> = HashMap::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let name = e.name().as_ref().to_vec();
                if !in_record && name == record_tag {
                    in_record = true;
                    record_depth = depth;
                    cur_id = None;
                    cur_campos.clear();
                    current_field = None;
                } else if in_record && depth == record_depth + 1 {
                    current_field = Some(name);
                }
            }
            Ok(Event::End(e)) => {
                let name = e.name().as_ref().to_vec();
                if in_record && depth == record_depth && name == record_tag {
                    if let Some(id) = cur_id.take() {
                        out.push((id, std::mem::take(&mut cur_campos)));
                    }
                    in_record = false;
                    current_field = None;
                    cur_id = None;
                    cur_campos.clear();
                } else if in_record && depth == record_depth + 1 {
                    current_field = None;
                }
                depth = depth.saturating_sub(1);
            }
            Ok(Event::Text(t)) => {
                if let Some(field) = &current_field {
                    if in_record && depth == record_depth + 1 {
                        let text = t.unescape().unwrap_or_default();
                        if field.as_slice() == b"id" {
                            cur_id = text.trim().parse().ok();
                        } else if campos_pedidos.contains(&field.as_slice()) {
                            cur_campos.insert(field.clone(), text.into_owned());
                        }
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

/// Lê itens iniciais de player_initial_data.xml.
pub fn carrega_itens_iniciais_xml(path: &Path) -> Result<HashMap<String, Vec<(u32, u32)>>, String> {
    let mut data_holder = crate::dataholders::player_initial_data::PlayerInitialDataHolder::new();
    data_holder.load_from_file(path)?;
    Ok(data_holder.class_items)
}

/// Lê lista de spawns de monstros/NPCs de spawns.xml.
pub fn carrega_spawns_xml(path: &Path) -> Result<Vec<super::Spawn>, String> {
    if !path.exists() {
        return Ok(Vec::new());
    }

    let mut reader = Reader::from_file(path).map_err(|e| e.to_string())?;
    reader.config_mut().trim_text(true);

    let mut buf = Vec::new();
    let mut spawns = Vec::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Empty(e)) | Ok(Event::Start(e)) => {
                let name = e.name();
                if name.as_ref() == b"spawn" {
                    let mut mapa = 0u32;
                    let mut npc_id = 0u32;
                    let mut nome_id = 0u32;
                    let mut x = 0.0f32;
                    let mut y = 0.0f32;
                    let mut z = 0.0f32;

                    for attr in e.attributes().flatten() {
                        let val = String::from_utf8_lossy(&attr.value);
                        match attr.key.as_ref() {
                            b"map" | b"map_id" | b"world" => mapa = val.parse().unwrap_or(0),
                            b"npc_id" | b"id" => npc_id = val.parse().unwrap_or(0),
                            b"name_id" => nome_id = val.parse().unwrap_or(0),
                            b"x" => x = val.parse().unwrap_or(0.0),
                            b"y" => y = val.parse().unwrap_or(0.0),
                            b"z" => z = val.parse().unwrap_or(0.0),
                            _ => {}
                        }
                    }

                    if npc_id != 0 {
                        spawns.push(super::Spawn {
                            mapa,
                            npc_id,
                            nome_id,
                            x,
                            y,
                            z,
                            payload: Vec::new(),
                        });
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("error reading spawns XML: {e}")),
            _ => {}
        }
        buf.clear();
    }

    Ok(spawns)
}
