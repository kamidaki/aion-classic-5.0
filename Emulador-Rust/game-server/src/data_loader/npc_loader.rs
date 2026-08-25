//! Carregador de NPCs — lê `client_npcs.xml` do cliente oficial.

use std::collections::HashMap;
use std::path::Path;
use super::xml_reader::load_catalog;

/// Definição de NPC lida do catálogo oficial do cliente.
#[derive(Debug, Clone)]
pub struct NpcDef {
    pub id: u32,
    pub name: String,
}

/// Carrega todos os NPCs do `client_npcs.xml`.
///
/// Retorna um `HashMap<npc_id, NpcDef>`.
pub fn load_npcs(path: &Path) -> Result<HashMap<u32, NpcDef>, String> {
    load_catalog(path, b"npc_client")
        .map(|v| v.into_iter().map(|(id, name)| (id, NpcDef { id, name })).collect())
}
