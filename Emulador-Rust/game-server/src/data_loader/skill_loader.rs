//! Carregador de Skills — lê `client_skills.xml` e `client_skill_learns.xml` do cliente oficial.
//!
//! São dois arquivos separados:
//! - `client_skills.xml`: mapeia `id -> nome` de cada skill
//! - `client_skill_learns.xml`: mapeia `classe + nível -> nome_da_skill` (árvore de aprendizado)
//!
//! O pacote `S_ADD_SKILL` quer o id numérico, por isso a resolução é feita na carga.

use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashMap;
use std::path::Path;
use super::xml_reader::load_catalog;

/// Uma linha da árvore de aprendizado: que classe ganha que skill, em que nível.
#[derive(Debug, Clone)]
pub struct SkillLearn {
    /// Nome interno da classe no XML do cliente: `WIZARD`, `CHANTER`, `ALL`...
    pub classe: String,
    pub nivel: u16,
    pub skill_id: u32,
}

/// Skills que o servidor oficial concede a todo mundo e que não estão em árvore de classe nenhuma:
/// coleta, coleta aérea e extração de éter. Conferidas na captura.
pub const SKILLS_UNIVERSAIS: [u32; 3] = [30002, 30003, 40009];

/// Para cada skill, se o alvo dela é um inimigo.
///
/// `first_target` no XML vale `Target`, `Me`, `TargetorMe`, `MyPet`, `Point`...
/// Só `Target` age sobre outro; `Me` e o resto, não.
pub fn load_skill_alvo(path: &Path) -> Result<HashMap<u32, bool>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    const REGISTRO: &[u8] = b"skill_base_client";
    let mut buf = Vec::new();
    let mut out = HashMap::new();

    let mut depth = 0usize;
    let mut in_record = false;
    let mut record_depth = 0usize;
    let mut campo: Option<Vec<u8>> = None;
    let (mut id, mut alvo) = (None::<u32>, false);

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let nome = e.name().as_ref().to_vec();
                if !in_record && nome == REGISTRO {
                    in_record = true;
                    record_depth = depth;
                    id = None;
                    alvo = false;
                    campo = None;
                } else if in_record && depth == record_depth + 1 {
                    campo = Some(nome);
                }
            }
            Ok(Event::End(e)) => {
                let nome = e.name().as_ref().to_vec();
                if in_record && depth == record_depth && nome == REGISTRO {
                    if let Some(v) = id.take() {
                        out.insert(v, alvo);
                    }
                    in_record = false;
                    campo = None;
                } else if in_record && depth == record_depth + 1 {
                    campo = None;
                }
                depth = depth.saturating_sub(1);
            }
            Ok(Event::Text(t)) => {
                if in_record && depth == record_depth + 1 {
                    if let Some(f) = &campo {
                        let texto = t.unescape().unwrap_or_default();
                        match f.as_slice() {
                            b"id" => id = texto.trim().parse().ok(),
                            b"first_target" => {
                                alvo = texto.trim().eq_ignore_ascii_case("target")
                            }
                            _ => {}
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

/// Lê a árvore de aprendizado e resolve o nome de cada skill para o id numérico.
///
/// Sao dois arquivos porque o cliente separa as duas coisas:
/// - `client_skills.xml` diz `id -> nome`
/// - `client_skill_learns.xml` diz `classe + nível -> nome`
/// O pacote `S_ADD_SKILL` quer o id.
pub fn load_aprendizado(
    skills: &Path,
    arvore: &Path,
) -> Result<Vec<SkillLearn>, String> {
    let por_nome: HashMap<String, u32> = load_catalog(skills, b"skill_base_client")?
        .into_iter()
        .map(|(id, nome)| (nome, id))
        .collect();

    let mut reader = Reader::from_file(arvore)
        .map_err(|e| format!("open {}: {e}", arvore.display()))?;
    reader.config_mut().trim_text(true);

    const REGISTRO: &[u8] = b"client_skill_learn";
    let mut buf = Vec::new();
    let mut out = Vec::new();

    let mut depth = 0usize;
    let mut in_record = false;
    let mut record_depth = 0usize;
    let mut campo: Option<Vec<u8>> = None;
    let (mut classe, mut nivel, mut skill, mut auto) =
        (String::new(), 0u16, String::new(), false);

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                depth += 1;
                let nome = e.name().as_ref().to_vec();
                if !in_record && nome == REGISTRO {
                    in_record = true;
                    record_depth = depth;
                    classe.clear();
                    skill.clear();
                    nivel = 0;
                    auto = false;
                    campo = None;
                } else if in_record && depth == record_depth + 1 {
                    campo = Some(nome);
                }
            }
            Ok(Event::End(e)) => {
                let nome = e.name().as_ref().to_vec();
                if in_record && depth == record_depth && nome == REGISTRO {
                    // Só o que o cliente aprende sozinho
                    if auto {
                        if let Some(&id) = por_nome.get(skill.as_str()) {
                            out.push(SkillLearn {
                                classe: classe.clone(),
                                nivel,
                                skill_id: id,
                            });
                        }
                    }
                    in_record = false;
                    campo = None;
                } else if in_record && depth == record_depth + 1 {
                    campo = None;
                }
                depth = depth.saturating_sub(1);
            }
            Ok(Event::Text(t)) => {
                if in_record && depth == record_depth + 1 {
                    if let Some(f) = &campo {
                        let texto = t.unescape().unwrap_or_default();
                        match f.as_slice() {
                            b"class" => classe = texto.trim().to_string(),
                            b"pc_level" => nivel = texto.trim().parse().unwrap_or(0),
                            b"skill" => skill = texto.trim().to_string(),
                            b"autolearn" => auto = texto.trim().eq_ignore_ascii_case("true"),
                            _ => {}
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(format!("parse {}: {e}", arvore.display())),
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}
