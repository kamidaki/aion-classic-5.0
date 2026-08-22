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

fn hex_para_bytes(texto: &str) -> Option<Vec<u8>> {
    let texto = texto.trim();
    if texto.len() % 2 != 0 {
        return None;
    }
    (0..texto.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&texto[i..i + 2], 16).ok())
        .collect()
}

/// Um NPC parado no mundo, com a posicao que o servidor oficial usou.
#[derive(Debug, Clone)]
pub struct Spawn {
    pub mapa: u32,
    pub npc_id: u32,
    /// Id da string do nome -- o pacote leva o numero, nao o texto.
    pub nome_id: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    /// O `S_PUT_NPC` que o servidor oficial mandou para este NPC, sem o prelude.
    ///
    /// Guardamos o pacote inteiro porque ele tem tamanho variavel -- de 107 a 267 bytes na captura
    /// -- e o nosso `PutNpc` e implementacao da 2.5, de tamanho fixo, que o cliente 4.5 ignora.
    /// So o id de entidade e trocado no envio; ver [`OFFSET_ID_ENTIDADE`].
    pub payload: Vec<u8>,
}

/// Onde fica o id de entidade dentro do payload de [`Spawn`].
///
/// Tem o bit alto ligado (`0x80......`), que e o que o cliente 4.5 espera de id de entidade.
pub const OFFSET_ID_ENTIDADE: usize = 12;

/// Uma linha da arvore de aprendizado: que classe ganha que skill, em que nivel.
#[derive(Debug, Clone)]
pub struct SkillLearn {
    /// Nome interno da classe no XML do cliente: `WIZARD`, `CHANTER`, `ALL`...
    pub classe: String,
    pub nivel: u16,
    pub skill_id: u32,
}

/// Skills que o servidor oficial concede a todo mundo e que nao estao em arvore de classe nenhuma:
/// coleta, coleta aerea e extracao de eter. Conferidas na captura -- aparecem no `S_ADD_SKILL` de
/// um feiticeiro, e o XML nao as atribui a classe alguma.
pub const SKILLS_UNIVERSAIS: [u32; 3] = [30002, 30003, 40009];

#[derive(Debug, Default)]
pub struct GameData {
    pub npcs: HashMap<u32, NpcDef>,
    pub items: HashMap<u32, ItemDef>,
    pub aprendizado: Vec<SkillLearn>,
    pub spawns: Vec<Spawn>,
    /// Para cada skill, se ela age sobre um **inimigo**. Vem do `first_target` do XML do cliente.
    ///
    /// Existe porque o servidor tratava toda skill igual -- se houvesse alvo, tirava vida. Com
    /// isso a skill de voltar ao ponto de vinculo dava dano em quem estivesse selecionado.
    pub skill_no_alvo: HashMap<u32, bool>,
}

impl GameData {
    /// As skills que um personagem desta classe e deste nivel ja deveria ter.
    ///
    /// Reproduz o que o servidor oficial concedeu na captura: para um feiticeiro de nivel 11, as
    /// 29 skills do `S_ADD_SKILL` gravado sao todas previstas por aqui.
    pub fn skills_de(&self, classe: &str, base: &str, nivel: u16) -> Vec<u32> {
        let mut ids: Vec<u32> = self
            .aprendizado
            .iter()
            .filter(|a| a.nivel <= nivel && (a.classe == classe || a.classe == base
                || a.classe.eq_ignore_ascii_case("all")))
            .map(|a| a.skill_id)
            .collect();
        ids.extend_from_slice(&SKILLS_UNIVERSAIS);
        ids.sort_unstable();
        ids.dedup();
        ids
    }
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

        let skills_path = data_dir.join("skills").join("client_skills.xml");
        let arvore_path = data_dir.join("skills").join("client_skill_learns.xml");
        match load_skill_alvo(&skills_path) {
            Ok(m) => {
                println!("INFO: loaded targeting for {} skills", m.len());
                gd.skill_no_alvo = m;
            }
            Err(e) => eprintln!("WARN: skipping skill targeting ({}): {e}", skills_path.display()),
        }

        match load_aprendizado(&skills_path, &arvore_path) {
            Ok(a) => {
                println!("INFO: loaded {} skill learn rules from {}", a.len(), arvore_path.display());
                gd.aprendizado = a;
            }
            Err(e) => eprintln!("WARN: skipping skills ({}): {e}", arvore_path.display()),
        }

        gd
    }

    /// Le a tabela de spawns gerada por `tools/extrai_spawns.py`.
    ///
    /// Fica fora do `load` porque nao vem do XML do cliente: posicionamento de NPC nao esta em
    /// catalogo nenhum -- mora nos arquivos de nivel e no servidor -- e a unica fonte que temos
    /// para a 4.5 e a captura.
    pub fn carrega_spawns(&mut self, caminho: &Path) {
        let texto = match std::fs::read_to_string(caminho) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("WARN: sem tabela de spawns ({}): {e}", caminho.display());
                return;
            }
        };

        for linha in texto.lines() {
            let linha = linha.trim();
            if linha.is_empty() || linha.starts_with('#') {
                continue;
            }
            let campos: Vec<&str> = linha.split(',').collect();
            if campos.len() != 7 {
                continue;
            }
            let Some(payload) = hex_para_bytes(campos[6]) else {
                continue;
            };
            let ler_u32 = |i: usize| campos[i].parse::<u32>().ok();
            let ler_f32 = |i: usize| campos[i].parse::<f32>().ok();
            if let (Some(mapa), Some(npc_id), Some(nome_id), Some(x), Some(y), Some(z)) = (
                ler_u32(0),
                ler_u32(1),
                ler_u32(2),
                ler_f32(3),
                ler_f32(4),
                ler_f32(5),
            ) {
                self.spawns.push(Spawn { mapa, npc_id, nome_id, x, y, z, payload });
            }
        }
        println!(
            "INFO: loaded {} NPC spawns from {}",
            self.spawns.len(),
            caminho.display()
        );
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

/// Para cada skill, se o alvo dela e um inimigo.
///
/// `first_target` no XML do cliente vale `Target`, `Me`, `TargetorMe`, `MyPet`, `Point`... -- e a
/// grafia varia entre maiuscula e minuscula. So `Target` age sobre outro; `Me` e o resto, nao.
fn load_skill_alvo(path: &Path) -> Result<HashMap<u32, bool>, String> {
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

/// Le a arvore de aprendizado e resolve o nome de cada skill para o id numerico.
///
/// Sao dois arquivos porque o cliente separa as duas coisas: `client_skills.xml` diz `id -> nome`,
/// e `client_skill_learns.xml` diz `classe + nivel -> nome`. O pacote `S_ADD_SKILL` quer o id.
fn load_aprendizado(
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
                    // So o que o cliente aprende sozinho: o resto depende de livro, estigma ou
                    // NPC, e o servidor oficial nao mandou nada disso no login.
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
