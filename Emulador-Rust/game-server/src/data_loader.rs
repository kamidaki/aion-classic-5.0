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
    ///
    /// `duas_maos` sai do `equipment_slots` do catalogo: `main` e arma de duas maos -- arco,
    /// orbe, cajado, lanca --, `main_or_sub` e de uma mao. A diferenca importa no pacote: o
    /// registro de arma de duas maos abre com um bloco de item composto, e o de uma mao nao.
    Arma { principal: u64, secundario: u64, duas_maos: bool },
    /// Escudo. Tem bloco proprio, de 20 bytes, e vai sempre na mao secundaria.
    Escudo(u64),
    /// Peca de armadura de corpo -- peitoral, calca, luva, bota, ombreira.
    Armadura(u64),
    /// Acessorio: elmo, colar, brinco, anel, cinto, asa.
    Acessorio { principal: u64, secundario: u64 },
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

#[derive(Debug, Clone, Default)]
pub struct TitleDef {
    pub id: u16,
    pub name: String,
    pub desc: String,
    pub race: u8,
    pub bonus_hp: i32,
    pub bonus_mp: i32,
    pub bonus_speed: f32,
    pub bonus_fly_speed: f32,
    pub bonus_p_atk: i32,
    pub bonus_m_atk: i32,
    pub bonus_p_def: i32,
    pub bonus_m_def: i32,
    pub bonus_p_crit: i32,
    pub bonus_m_crit: i32,
}

#[derive(Debug, Clone, Default)]
pub struct GoodsListDef {
    pub id: u32,
    pub name: String,
    pub items: Vec<String>,
}

#[derive(Debug, Clone, Default)]
pub struct BattlePassRewardDef {
    pub id: u32,
    pub season_id: u32,
    pub level: u8,
    pub light_basic_name: String,
    pub light_basic_count: u32,
    pub light_unlock_name: String,
    pub light_unlock_count: u32,
    pub dark_basic_name: String,
    pub dark_basic_count: u32,
    pub dark_unlock_name: String,
    pub dark_unlock_count: u32,
}

#[derive(Debug, Clone, Default)]
pub struct AttendanceRewardDef {
    pub id: u32,
    pub name: String,
    pub attend_type: String,
    pub rewards: Vec<(String, u32, u8)>, // (item_name, count, permit_level)
}

#[derive(Debug, Clone, Default)]
pub struct GatherDef {
    pub id: u32,
    pub name: String,
    pub desc: String,
    pub harvest_skill: String,
    pub skill_level: u16,
    pub material1: String,
    pub harvest_count: u32,
}

#[derive(Debug, Default)]
pub struct GameData {
    pub npcs: HashMap<u32, NpcDef>,
    pub items: HashMap<u32, ItemDef>,
    pub aprendizado: Vec<SkillLearn>,
    pub spawns: Vec<Spawn>,
    pub titles: HashMap<u16, TitleDef>,
    pub goods_lists: HashMap<u32, GoodsListDef>,
    pub battlepass_rewards: Vec<BattlePassRewardDef>,
    pub attendance_rewards: Vec<AttendanceRewardDef>,
    pub gather_sources: HashMap<u32, GatherDef>,
    /// Para cada skill, se ela age sobre um **inimigo**. Vem do `first_target` do XML do cliente.
    ///
    /// Existe porque o servidor tratava toda skill igual -- se houvesse alvo, tirava vida. Com
    /// isso a skill de voltar ao ponto de vinculo dava dano em quem estivesse selecionado.
    pub skill_no_alvo: HashMap<u32, bool>,
    /// O kit que cada grupo de classe recebe ao nascer: `(item_id, quantidade)`.
    ///
    /// A chave e a classe base -- `FIGHTER`, `SCOUT`, `MAGE`, `PRIEST` -- porque as duas classes
    /// que saem de cada uma comecam iguais. Ver `data/itens_iniciais.csv`.
    pub itens_iniciais: HashMap<String, Vec<(u32, u32)>>,
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

        let titles_path = data_dir.join("PC").join("client_titles.xml");
        match load_titles(&titles_path) {
            Ok(t) => {
                println!("INFO: loaded {} titles from {}", t.len(), titles_path.display());
                gd.titles = t;
            }
            Err(e) => eprintln!("WARN: skipping titles ({}): {e}", titles_path.display()),
        }

        let goods_path = data_dir.join("npcs").join("client_npc_goodslist.xml");
        match load_goods_lists(&goods_path) {
            Ok(g) => {
                println!("INFO: loaded {} goods lists from {}", g.len(), goods_path.display());
                gd.goods_lists = g;
            }
            Err(e) => eprintln!("WARN: skipping goods lists ({}): {e}", goods_path.display()),
        }

        let battlepass_path = data_dir.join("PC").join("client_battlepass_reward.xml");
        match load_battlepass_rewards(&battlepass_path) {
            Ok(bp) => {
                println!("INFO: loaded {} battlepass rewards from {}", bp.len(), battlepass_path.display());
                gd.battlepass_rewards = bp;
            }
            Err(e) => eprintln!("WARN: skipping battlepass rewards ({}): {e}", battlepass_path.display()),
        }

        let login_event_path = data_dir.join("PC").join("client_login_event.xml");
        match load_attendance_rewards(&login_event_path) {
            Ok(att) => {
                println!("INFO: loaded {} attendance login events from {}", att.len(), login_event_path.display());
                gd.attendance_rewards = att;
            }
            Err(e) => eprintln!("WARN: skipping attendance events ({}): {e}", login_event_path.display()),
        }

        let gather_path = data_dir.join("Gather").join("gather_src.xml");
        match load_gather_sources(&gather_path) {
            Ok(g) => {
                println!("INFO: loaded {} gather sources from {}", g.len(), gather_path.display());
                gd.gather_sources = g;
            }
            Err(e) => eprintln!("WARN: skipping gather sources ({}): {e}", gather_path.display()),
        }

        gd
    }

    /// Le o kit inicial de `data/itens_iniciais.csv`.
    ///
    /// Fica fora do `load` pelo mesmo motivo dos spawns: nao vem do catalogo do cliente. O
    /// conteudo e do `player_initial_data.xml` da base de referencia, que nao acompanha o
    /// repositorio -- por isso a tabela virou arquivo nosso, com os ids ja conferidos contra o
    /// catalogo 4.5.
    pub fn carrega_itens_iniciais(&mut self, caminho: &Path) {
        let texto = match std::fs::read_to_string(caminho) {
            Ok(t) => t,
            Err(e) => {
                eprintln!("WARN: sem kit inicial ({}): {e}", caminho.display());
                return;
            }
        };

        for linha in texto.lines() {
            let linha = linha.trim();
            if linha.is_empty() || linha.starts_with('#') {
                continue;
            }
            let campos: Vec<&str> = linha.split(',').collect();
            if campos.len() != 3 {
                continue;
            }
            if let (Ok(item), Ok(quantidade)) =
                (campos[1].trim().parse::<u32>(), campos[2].trim().parse::<u32>())
            {
                self.itens_iniciais
                    .entry(campos[0].trim().to_ascii_uppercase())
                    .or_default()
                    .push((item, quantidade));
            }
        }
        println!(
            "INFO: kit inicial de {} classes lido de {}",
            self.itens_iniciais.len(),
            caminho.display()
        );
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
        // Arma de uma mao. O par de slots e (1, 2) -- conferido no `SLOTS_WEAPON` do item
        // 100001443, e de novo na espada e na adaga da captura de 22/08.
        "main_or_sub" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: false,
        },
        // Arma de duas maos: arco, orbe, grimorio, cajado, lanca, espadao. Mesmo par de slots, e
        // um bloco de item composto na frente. Conferido no arco `bow_n_l1_1a` da captura.
        "main" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: true,
        },
        // So escudo usa `sub`. Bloco proprio de 20 bytes, com a mascara da mao secundaria --
        // medido no `shield_n_l1_1a` que o templario da captura recebeu.
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
    let registros = load_catalog_campos(path, record_tag, &[b"name"])?;
    Ok(registros
        .into_iter()
        .map(|(id, campos)| {
            (id, campos.get(b"name".as_slice()).cloned().unwrap_or_default())
        })
        .collect())
}

/// O mesmo percurso, guardando os campos pedidos em vez de so o nome.
///
/// Existe porque o catalogo de itens tem 189 MB e cada item precisa de uma duzia de campos --
/// slot, tamanho da pilha e os booleanos que formam a mascara. Ler o arquivo uma vez e escolher
/// na hora e mais barato que uma passada por campo, e guardar o registro inteiro custaria
/// memoria a toa.
fn load_catalog_campos(
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
            Err(e) => {
                return Err(format!("parse {}: {e}", path.display()));
            }
            _ => {}
        }
        buf.clear();
    }

    Ok(out)
}

fn load_titles(path: &Path) -> Result<HashMap<u16, TitleDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<TitleDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_title" {
                    cur = Some(TitleDef::default());
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_title" {
                    if let Some(t) = cur.take() {
                        if t.id > 0 {
                            out.insert(t.id, t);
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut title) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => {
                            if let Ok(id) = text.parse::<u16>() {
                                title.id = id;
                            }
                        }
                        "name" => title.name = text.to_string(),
                        "desc" => title.desc = text.to_string(),
                        "title_race" => {
                            if let Ok(r) = text.parse::<u8>() {
                                title.race = r;
                            }
                        }
                        "bonus_attr" => {
                            let parts: Vec<&str> = text.split_whitespace().collect();
                            if parts.len() >= 2 {
                                let attr = parts[0];
                                let val_str = parts[1].trim_end_matches('%');
                                if let Ok(val_i32) = val_str.parse::<i32>() {
                                    match attr {
                                        "maxHp" => title.bonus_hp += val_i32,
                                        "maxMp" => title.bonus_mp += val_i32,
                                        "PhysicalDefend" => title.bonus_p_def += val_i32,
                                        "MagicalDefend" => title.bonus_m_def += val_i32,
                                        "PhysicalAttack" => title.bonus_p_atk += val_i32,
                                        "MagicalSkillBoost" => title.bonus_m_atk += val_i32,
                                        "PhysicalCritical" => title.bonus_p_crit += val_i32,
                                        "MagicalCritical" => title.bonus_m_crit += val_i32,
                                        "speed" => title.bonus_speed += val_i32 as f32 / 100.0,
                                        "flySpeed" => title.bonus_fly_speed += val_i32 as f32 / 100.0,
                                        _ => {}
                                    }
                                }
                            }
                        }
                        _ => {}
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

fn load_goods_lists(path: &Path) -> Result<HashMap<u32, GoodsListDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<GoodsListDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_npc_goodslist" {
                    cur = Some(GoodsListDef::default());
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_npc_goodslist" {
                    if let Some(g) = cur.take() {
                        if g.id > 0 {
                            out.insert(g.id, g);
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut goods) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => {
                            if let Ok(id) = text.parse::<u32>() {
                                goods.id = id;
                            }
                        }
                        "name" => goods.name = text.to_string(),
                        "item" => {
                            if !text.is_empty() {
                                goods.items.push(text.to_string());
                            }
                        }
                        _ => {}
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

fn load_battlepass_rewards(path: &Path) -> Result<Vec<BattlePassRewardDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = Vec::new();
    let mut buf = Vec::new();
    let mut cur: Option<BattlePassRewardDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_battlepass_reward" {
                    cur = Some(BattlePassRewardDef::default());
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_battlepass_reward" {
                    if let Some(r) = cur.take() {
                        if r.id > 0 {
                            out.push(r);
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut reward) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => {
                            if let Ok(id) = text.parse::<u32>() {
                                reward.id = id;
                            }
                        }
                        "season_id" => {
                            if let Ok(sid) = text.parse::<u32>() {
                                reward.season_id = sid;
                            }
                        }
                        "pass_lv" => {
                            if let Ok(lv) = text.parse::<u8>() {
                                reward.level = lv;
                            }
                        }
                        "light_basic_reward1_name" => reward.light_basic_name = text.to_string(),
                        "light_basic_reward1_count" => {
                            if let Ok(c) = text.parse::<u32>() {
                                reward.light_basic_count = c;
                            }
                        }
                        "light_unlock_reward1_name" => reward.light_unlock_name = text.to_string(),
                        "light_unlock_reward1_count" => {
                            if let Ok(c) = text.parse::<u32>() {
                                reward.light_unlock_count = c;
                            }
                        }
                        "dark_basic_reward1_name" => reward.dark_basic_name = text.to_string(),
                        "dark_basic_reward1_count" => {
                            if let Ok(c) = text.parse::<u32>() {
                                reward.dark_basic_count = c;
                            }
                        }
                        "dark_unlock_reward1_name" => reward.dark_unlock_name = text.to_string(),
                        "dark_unlock_reward1_count" => {
                            if let Ok(c) = text.parse::<u32>() {
                                reward.dark_unlock_count = c;
                            }
                        }
                        _ => {}
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

fn load_attendance_rewards(path: &Path) -> Result<Vec<AttendanceRewardDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = Vec::new();
    let mut buf = Vec::new();
    let mut cur: Option<AttendanceRewardDef> = None;
    let mut cur_item: String = String::new();
    let mut cur_count: u32 = 1;
    let mut cur_lvl: u8 = 1;
    let mut cur_tag = String::new();
    let mut in_data = false;

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_login_event" {
                    cur = Some(AttendanceRewardDef::default());
                } else if name == "data" {
                    in_data = true;
                    cur_item.clear();
                    cur_count = 1;
                    cur_lvl = 1;
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "client_login_event" {
                    if let Some(r) = cur.take() {
                        if r.id > 0 {
                            out.push(r);
                        }
                    }
                } else if name == "data" && in_data {
                    in_data = false;
                    if let Some(ref mut att) = cur {
                        if !cur_item.is_empty() {
                            att.rewards.push((cur_item.clone(), cur_count, cur_lvl));
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut att) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" if !in_data => {
                            if let Ok(id) = text.parse::<u32>() {
                                att.id = id;
                            }
                        }
                        "name" if !in_data => att.name = text.to_string(),
                        "attend_type" if !in_data => att.attend_type = text.to_string(),
                        "reward_item" if in_data => cur_item = text.to_string(),
                        "reward_item_count" if in_data => {
                            if let Ok(c) = text.parse::<u32>() {
                                cur_count = c;
                            }
                        }
                        "reward_permit_level" if in_data => {
                            if let Ok(lvl) = text.parse::<u8>() {
                                cur_lvl = lvl;
                            }
                        }
                        _ => {}
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

fn load_gather_sources(path: &Path) -> Result<HashMap<u32, GatherDef>, String> {
    let mut reader = Reader::from_file(path)
        .map_err(|e| format!("open {}: {e}", path.display()))?;
    reader.config_mut().trim_text(true);

    let mut out = HashMap::new();
    let mut buf = Vec::new();
    let mut cur: Option<GatherDef> = None;
    let mut cur_tag = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "gather_src" {
                    cur = Some(GatherDef::default());
                }
                cur_tag = name;
            }
            Ok(Event::End(e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if name == "gather_src" {
                    if let Some(g) = cur.take() {
                        if g.id > 0 {
                            out.insert(g.id, g);
                        }
                    }
                }
                cur_tag.clear();
            }
            Ok(Event::Text(t)) => {
                if let Some(ref mut gather) = cur {
                    let text = t.unescape().unwrap_or_default();
                    let text = text.trim();
                    match cur_tag.as_str() {
                        "id" => {
                            if let Ok(id) = text.parse::<u32>() {
                                gather.id = id;
                            }
                        }
                        "name" => gather.name = text.to_string(),
                        "desc" => gather.desc = text.to_string(),
                        "harvestskill" => gather.harvest_skill = text.to_string(),
                        "skill_level" => {
                            if let Ok(lvl) = text.parse::<u16>() {
                                gather.skill_level = lvl;
                            }
                        }
                        "material1" => gather.material1 = text.to_string(),
                        "harvest_count" => {
                            if let Ok(c) = text.parse::<u32>() {
                                gather.harvest_count = c;
                            }
                        }
                        _ => {}
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

#[cfg(test)]
mod tests {
    use super::*;

    fn campos(pares: &[(&str, &str)]) -> HashMap<Vec<u8>, String> {
        pares
            .iter()
            .map(|(k, v)| (k.as_bytes().to_vec(), v.to_string()))
            .collect()
    }

    /// A mascara calculada bate com a que o servidor oficial mandou.
    ///
    /// Os tres itens abaixo saem da captura, e os campos sao os do catalogo do cliente 4.5. Sao
    /// os tres casos que separam os bits: uma pocao empilhavel que nao se troca, um peitoral que
    /// nao se empilha nem se extrai, e o kinah, que e trocavel e vai nos dois armazens.
    #[test]
    fn mascara_reproduz_a_captura() {
        let pocao = campos(&[
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("breakable", "TRUE"),
            ("max_stack_count", "100"),
        ]);
        assert_eq!(mascara_do_item(&pocao, "none"), 0x612C, "item 164000224");

        let peitoral = campos(&[
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("breakable", "TRUE"),
            ("cannot_extraction", "TRUE"),
            ("max_stack_count", "1"),
        ]);
        assert_eq!(mascara_do_item(&peitoral, "torso"), 0x802C, "item 110101547");

        let kinah = campos(&[
            ("can_exchange", "TRUE"),
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("can_deposit_to_account_warehouse", "TRUE"),
            ("max_stack_count", "0"),
        ]);
        assert_eq!(mascara_do_item(&kinah, "none"), 0x631E, "item 182400001");
    }

    /// Os bits de slot sao os que a captura mostra nos itens que a personagem usava.
    #[test]
    fn slots_batem_com_a_captura() {
        assert!(matches!(slot_do_catalogo("torso"), Slot::Armadura(8)));
        assert!(matches!(slot_do_catalogo("leg"), Slot::Armadura(4096)));
        assert!(matches!(slot_do_catalogo("shoulder"), Slot::Armadura(2048)));
        assert!(matches!(
            slot_do_catalogo("neck"),
            Slot::Acessorio { principal: 1024, .. }
        ));
        assert!(matches!(
            slot_do_catalogo("waist"),
            Slot::Acessorio { principal: 65536, .. }
        ));
        assert!(matches!(
            slot_do_catalogo("main_or_sub"),
            Slot::Arma { principal: 1, secundario: 2, duas_maos: false }
        ));
        // Arma de duas maos: mesmo par de slots, e o bloco composto na frente.
        assert!(matches!(
            slot_do_catalogo("main"),
            Slot::Arma { duas_maos: true, .. }
        ));
        // So escudo usa `sub`, e ele vai na mao secundaria.
        assert!(matches!(slot_do_catalogo("sub"), Slot::Escudo(2)));
        assert!(matches!(slot_do_catalogo("none"), Slot::Nenhum));
    }

    #[test]
    fn test_title_bonus_parsing() {
        let mut t = TitleDef::default();
        t.id = 1;
        t.bonus_hp = 20;
        t.bonus_p_def = 5;
        assert_eq!(t.bonus_hp, 20);
        assert_eq!(t.bonus_p_def, 5);
    }

    #[test]
    fn test_goods_list_def() {
        let gl = GoodsListDef {
            id: 1,
            name: "sale_skillbook".to_string(),
            items: vec!["skillbook_1".to_string(), "skillbook_2".to_string()],
        };
        assert_eq!(gl.items.len(), 2);
    }
}
