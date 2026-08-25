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
///
/// Existe porque o catálogo de itens tem ~189 MB e cada item precisa de uma dúzia de campos.
/// Ler o arquivo uma vez e escolher na hora é mais barato que uma passada por campo.
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
