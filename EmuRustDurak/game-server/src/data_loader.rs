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

/// Onde um item se equipa, no formato de bits que o cliente usa.
///
/// Sai do `equipment_slots` do catalogo do cliente. Os numeros foram conferidos contra a captura:
/// os itens que a personagem gravada usava chegam com exatamente estes bits no bloco de slot --
/// peitoral 8, calca 4096, ombreira 2048, luva 16, bota 32, colar 1024, cinto 65536.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    /// Nao equipavel: pocao, comida, kinah, material.
    Nenhum,
    /// Arma. O bloco de slot e o `SLOTS_WEAPON`, com a mao principal e a secundaria.
    Arma { principal: u64, secundario: u64 },
    /// Peca de armadura de corpo -- peitoral, calca, luva, bota, ombreira.
    Armadura(u64),
    /// Acessorio: elmo, colar, brinco, anel, cinto, asa.
    Acessorio { principal: u64, secundario: u64 },
}

impl Slot {
    pub fn equipavel(&self) -> bool {
        !matches!(self, Slot::Nenhum)
    }
}

#[derive(Debug, Clone)]
pub struct ItemDef {
    pub id: u32,
    pub name: String,
    /// Mascara de direitos do item -- vender, trocar, guardar no armazem, empilhar.
    ///
    /// Ver [`mascara_do_item`]: e calculada dos campos do catalogo, e reproduz 108 das 119
    /// mascaras que a captura mostra.
    pub mascara: u16,
    pub slot: Slot,
    /// O byte que fecha o registro de item. Vale 1 nas pecas de armadura de corpo e 0 no resto.
    pub tecido: bool,
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

/// Os slots de armadura de corpo, que sao os que o cliente marca como "tecido".
const SLOTS_DE_CORPO: [&str; 5] = ["torso", "leg", "glove", "foot", "shoulder"];

/// Traduz o `equipment_slots` do catalogo para os bits que o pacote de item leva.
///
/// Os nomes saem do XML do cliente; os bits, do `ItemSlot` do Aion-Lightning, conferidos um a um
/// contra os itens que a personagem da captura usava.
fn slot_do_catalogo(texto: &str) -> Slot {
    const MAO_PRINCIPAL: u64 = 1;
    const MAO_SECUNDARIA: u64 = 1 << 1;

    let bit = |n: u32| 1u64 << n;
    match texto {
        // Arma de uma mao que pode ir nas duas maos, e arma que so vai na principal. Nos dois
        // casos a captura mostra o par (1, 2) -- ver o `SLOTS_WEAPON` do item 100001443.
        "main_or_sub" | "main" | "sub" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
        },
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

/// A mascara de direitos que vai no bloco `GENERAL_INFO` de cada item.
///
/// Foi ajustada contra a captura: das 119 mascaras que o servidor oficial mandou, esta conta
/// reproduz 108 byte a byte. As 11 que sobram sao todas item de quest, e diferem so no bit 10 --
/// que nao casa com campo nenhum do catalogo e por isso fica desligado aqui.
///
/// Os bits 8 e 14 nao vem de um campo booleano: sao decididos pelo tipo de slot, e o agrupamento
/// saiu da propria captura (o 8 desliga em arma e armadura de corpo; o 14 liga no que nao se
/// equipa, mais anel e cinto).
fn mascara_do_item(campos: &HashMap<Vec<u8>, String>, slot_texto: &str) -> u16 {
    let ligado = |nome: &[u8]| {
        campos
            .get(nome)
            .map(|v| v.trim().eq_ignore_ascii_case("true"))
            .unwrap_or(false)
    };
    let empilhavel = campos
        .get(b"max_stack_count".as_slice())
        .and_then(|v| v.trim().parse::<u32>().ok())
        .map(|n| n != 1)
        .unwrap_or(false);

    let mut m: u16 = 0;
    if ligado(b"lore") {
        m |= 1 << 0;
    }
    if ligado(b"can_exchange") {
        // O mesmo campo acende dois bits: na captura, os 15 itens trocaveis tem os dois, e os
        // outros 104 nao tem nenhum.
        m |= (1 << 1) | (1 << 9);
    }
    if ligado(b"can_sell_to_npc") {
        m |= 1 << 2;
    }
    if ligado(b"can_deposit_to_character_warehouse") {
        m |= 1 << 3;
    }
    if ligado(b"can_deposit_to_account_warehouse") {
        m |= 1 << 4;
    }
    if ligado(b"breakable") {
        m |= 1 << 5;
    }
    if ligado(b"soul_bind") {
        m |= 1 << 6;
    }
    if !matches!(slot_texto, "main" | "main_or_sub" | "sub")
        && !SLOTS_DE_CORPO.contains(&slot_texto)
    {
        m |= 1 << 8;
    }
    if ligado(b"can_composite_weapon") {
        m |= 1 << 11;
    }
    if empilhavel {
        m |= 1 << 13;
    }
    if matches!(slot_texto, "none" | "right_or_left_finger" | "waist") {
        m |= 1 << 14;
    }
    if ligado(b"cannot_extraction") {
        m |= 1 << 15;
    }
    m
}

fn load_items(path: &Path) -> Result<HashMap<u32, ItemDef>, String> {
    const CAMPOS: [&[u8]; 12] = [
        b"name",
        b"equipment_slots",
        b"max_stack_count",
        b"lore",
        b"can_exchange",
        b"can_sell_to_npc",
        b"can_deposit_to_character_warehouse",
        b"can_deposit_to_account_warehouse",
        b"breakable",
        b"soul_bind",
        b"can_composite_weapon",
        b"cannot_extraction",
    ];

    let registros = load_catalog_campos(path, b"client_item", &CAMPOS)?;
    Ok(registros
        .into_iter()
        .map(|(id, campos)| {
            let slot_texto = campos
                .get(b"equipment_slots".as_slice())
                .map(|s| s.trim().to_string())
                .unwrap_or_else(|| "none".to_string());
            let def = ItemDef {
                id,
                name: campos
                    .get(b"name".as_slice())
                    .cloned()
                    .unwrap_or_default(),
                mascara: mascara_do_item(&campos, &slot_texto),
                slot: slot_do_catalogo(&slot_texto),
                tecido: SLOTS_DE_CORPO.contains(&slot_texto.as_str()),
            };
            (id, def)
        })
        .collect())
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

/// Streaming parse: for each element named `record_tag`, extract the `<id>`
/// and the specified `campos` children. Skips records without a parseable id.
fn load_catalog_campos(
    path: &Path,
    record_tag: &[u8],
    campos: &[&[u8]],
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
                        } else if campos.iter().any(|&c| c == field.as_slice()) {
                            cur_campos.insert(field.clone(), text.into_owned());
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
