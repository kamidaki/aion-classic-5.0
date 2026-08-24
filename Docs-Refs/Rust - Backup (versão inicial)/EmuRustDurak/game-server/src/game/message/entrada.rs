//! Os pacotes que o cliente espera entre a selecao de personagem e o `LevelReady`.
//!
//! # Por que este modulo existe
//!
//! O cliente so responde `LevelReady` -- "terminei de carregar o mapa" -- depois de receber um
//! bloco de estado inicial. Na captura sao **144 pacotes** entre a selecao e o `LevelReady`, e o
//! servidor mandava cerca de vinte.
//!
//! O resto vinha do motor de replay, que indexa os pacotes gravados **pelo opcode que o cliente
//! mandou antes deles**. Isso e fragil de um jeito que custou uma sessao inteira de diagnostico: o
//! maior lote da captura, 51 pacotes, esta indexado sob o `C_SA_GOODSLIST` (0xD5), e o nosso
//! cliente nunca manda esse opcode -- manda `0x122` no lugar. Os 51 ficavam guardados, o cliente
//! esperava algo que estava dentro deles, e a tela de carregamento nao saia.
//!
//! Como o disparo dependia de quais opcodes o cliente resolvia mandar, o sintoma ia e voltava --
//! e um relatorio chegou a descrever a entrada no mundo como resolvida.
//!
//! # O que esta implementado, e o que nao esta
//!
//! Os pacotes **pequenos** do bloco, que sao a maioria e sao quase todos lista vazia ou contador
//! zerado. Cada valor abaixo veio de ler o payload capturado, e o comentario diz o que ele
//! significa.
//!
//! Ficam de fora os grandes: `S_ABYSS_RANKER_INFOS` (7983 bytes), `S_ABYSS_INFO` (5283),
//! `S_LOAD_CHANNEL_CHATTING_BLACKLIST` (2252), `S_CREATE_ACHIEVEMENT_EVENT` (1237),
//! `S_COMBAT_POWER_BUFF_LIST` (793), `S_INSTANCE_DUNGEON_COOLTIMES` (515) e mais alguns. Sao
//! listas de conteudo -- ranking, conquistas, passe de batalha -- e deixa-las de fora tem
//! proposito: **medir quais o cliente realmente exige**. Se ele entrar no mundo sem elas, nao sao
//! pre-requisito de nada e entram depois, com calma.
//!
//! # De onde vem cada valor
//!
//! Da captura de 22 minutos. Os pacotes que carregam o id do personagem sao escritos com o nosso:
//! na captura eles trazem `0x2E46283A`, o id da personagem gravada.

/// Um pacote pronto para envio: opcode e payload, sem o prelude.
pub type Pacote = (u16, Vec<u8>);

// Os nomes vem de `docs/protocol/opcodes_server.csv`. Os `DESCONHECIDO_*` nao tem nome na tabela
// extraida do Game.dll -- sao identificados pelo numero e pelo lugar que ocupam na sequencia.
const RESULT_PASSPORT: u16 = 0x133;
const CLEAR_ACHIEVEMENT_EVENT: u16 = 0x116;
const LOAD_FINISHEDQUEST: u16 = 0x07a;
const LOAD_WORKINGQUEST: u16 = 0x046;
const TITLE: u16 = 0x0af;
const CUSTOM_ANIM: u16 = 0x093;
const USER_CLASSIC_WARDROBE_LOAD: u16 = 0x122;
const RANKING_BADGE: u16 = 0x138;
const STORY_BOOK_FINISHED: u16 = 0x14c;
const STORY_BOOK_REGISTERED: u16 = 0x14d;
const DESCONHECIDO_177: u16 = 0x177;
const DESCONHECIDO_197: u16 = 0x197;
const DESCONHECIDO_1A8: u16 = 0x1a8;
const LOAD_PROMOTION: u16 = 0x109;
const LOAD_ITEM_COOLTIME: u16 = 0x066;
const LOAD_EQUIPMENT_CHANGE: u16 = 0x12f;
const CHANGE_CHANNEL: u16 = 0x0e5;
const EVENT: u16 = 0x081;
const RESURRECT_LOC_INFO: u16 = 0x0eb;
const USER_BIND_STONE_INFO: u16 = 0x146;
const TIME: u16 = 0x026;
const USER_APPLY_JOIN_GUILD_INFO: u16 = 0x151;
const LOAD_WAREHOUSE: u16 = 0x0a7;
const ADDREMOVE_SOCIAL: u16 = 0x04e;
const BUDDY_LIST: u16 = 0x083;
const LOAD_PVP_ENV: u16 = 0x0bc;
const TAX_INFO: u16 = 0x0fc;
const LOAD_GATHERCOMBINE_COOLTIME: u16 = 0x0a4;
const CHAT_ACCUSE: u16 = 0x121;
const SPAM_FILTER_FLAG: u16 = 0x126;
const CHANNEL_CHATTING_BLACKLIST_SETTING: u16 = 0x12c;
const CHANNEL_CHATTING_PERMISSION: u16 = 0x128;
const RANKING_BADGE_LIST: u16 = 0x13a;
const DESCONHECIDO_170: u16 = 0x170;
const DESCONHECIDO_183: u16 = 0x183;
const HOTSPOT: u16 = 0x1af;
const BM_PACK_LIST: u16 = 0x101;
const MAIL: u16 = 0x0a0;
const LOAD_MACRO: u16 = 0x0e7;
const GLOBAL_TRADE_SALESLOG: u16 = 0x141;
const SPECIAL_COMBINE_RECIPE_INFO: u16 = 0x1ab;
const DESCONHECIDO_1AA: u16 = 0x1aa;
const ABNORMAL_STATUS: u16 = 0x031;
const NPSHOP_GOODS_COUNT: u16 = 0x10a;

/// Quantas paginas de armazem o servidor anuncia.
///
/// Na captura sao 24 pacotes identicos de `S_LOAD_WAREHOUSE`, um por pagina, todos com o payload
/// de pagina vazia -- a personagem gravada tinha o armazem sem nada e ainda assim recebeu as 24.
const PAGINAS_DE_ARMAZEM: usize = 24;

fn com_id(id: u32, resto: &[u8]) -> Vec<u8> {
    let mut v = id.to_le_bytes().to_vec();
    v.extend_from_slice(resto);
    v
}

/// Os pacotes que vao **antes** do `S_STATUS`, logo depois da segunda senha.
///
/// Na captura ocupam de #30 a #77: o estado que o cliente monta antes de ter mundo -- conquistas,
/// quests, titulo, guarda-roupa. Quase tudo vazio.
pub fn antes_do_mundo(id_do_personagem: u32) -> Vec<Pacote> {
    let id = id_do_personagem;
    vec![
        // Passaporte. Primeiro u32 e 1 (ativo), depois o id do personagem, e um contador que na
        // captura vale 0x17. O resto e zero.
        (RESULT_PASSPORT, {
            let mut p = vec![0u8; 24];
            p[0] = 1;
            p[8..12].copy_from_slice(&id.to_le_bytes());
            p[12] = 0x17;
            p
        }),
        // Limpa a lista de eventos de conquista antes da nova. Payload vazio.
        (CLEAR_ACHIEVEMENT_EVENT, Vec::new()),
        // Quests terminadas e em andamento. O 1 e cabecalho de lista, nao quantidade: os dois
        // pacotes tem 4 bytes e a personagem gravada tinha quest em andamento.
        (LOAD_FINISHEDQUEST, vec![1, 0, 0, 0]),
        (LOAD_WORKINGQUEST, vec![1, 0, 0, 0]),
        // Nenhum titulo em uso.
        (TITLE, vec![2, 1, 0, 0, 0]),
        (CUSTOM_ANIM, vec![1, 0, 0]),
        // Guarda-roupa e emblema de ranking, vazios.
        (USER_CLASSIC_WARDROBE_LOAD, vec![1, 0, 0, 0, 0, 0, 1]),
        (RANKING_BADGE, vec![0, 0, 0, 0, 1]),
        // Livro de historia: o id do personagem e duas listas vazias.
        (STORY_BOOK_FINISHED, com_id(id, &[0, 0])),
        (STORY_BOOK_REGISTERED, com_id(id, &[0, 0])),
        (DESCONHECIDO_177, vec![0, 0, 1, 0, 0, 0]),
        (DESCONHECIDO_197, com_id(id, &[0, 0])),
        (DESCONHECIDO_1A8, com_id(id, &[0, 0])),
        (LOAD_PROMOTION, vec![1, 0, 0]),
        // Nenhum item em recarga.
        (LOAD_ITEM_COOLTIME, vec![0, 0]),
    ]
}

/// Os pacotes que fecham a entrada, **depois** do `S_WORLD`.
///
/// Na captura estao espalhados de #77 a #183, cortados ao meio pelo `S_WORLD`. Aqui vao todos
/// depois: o que o cliente cobra e a presenca deles. O `S_WORLD` e que tem lugar fixo, e ja e
/// mandado no ponto certo.
pub fn depois_do_mundo(id_do_personagem: u32, game_time: u32) -> Vec<Pacote> {
    let id = id_do_personagem;
    let mut p: Vec<Pacote> = vec![
        (LOAD_EQUIPMENT_CHANGE, vec![0, 0]),
        // Canal 0, capacidade 20 (0x14).
        (CHANGE_CHANNEL, vec![0, 0, 0, 0, 0x14, 0, 0, 0]),
        (EVENT, vec![6, 0]),
        // Ponto de ressurreicao. Na captura sao tres floats de posicao e um id de mapa -- o
        // obelisco de onde a personagem renasceria. Vai zerado enquanto nao houver obelisco:
        // renascer ainda nao existe, e o cliente aceita a lista sem destino.
        (RESURRECT_LOC_INFO, vec![0u8; 22]),
        // Pedra de vinculo: id do personagem, nenhum vinculo.
        (USER_BIND_STONE_INFO, com_id(id, &[0, 0, 0, 0])),
        (TIME, game_time.to_le_bytes().to_vec()),
        (USER_APPLY_JOIN_GUILD_INFO, vec![0u8; 6]),
    ];

    // O armazem, uma pagina vazia de cada vez -- 24 vezes, como na captura.
    for _ in 0..PAGINAS_DE_ARMAZEM {
        p.push((LOAD_WAREHOUSE, vec![1, 1, 0, 0, 0, 0, 0]));
    }

    p.extend([
        (TITLE, vec![2, 1, 0, 0]),
        // Amigos e bloqueados: listas vazias.
        (ADDREMOVE_SOCIAL, vec![0, 0, 0]),
        (BUDDY_LIST, vec![0, 0, 0]),
        (LOAD_PVP_ENV, vec![0, 0]),
        // Imposto das lojas, tres bytes. Os valores sao os das lojas oficiais.
        (TAX_INFO, vec![0x53, 0x6e, 0x69]),
        // Nada em recarga de coleta nem de fabricacao.
        (LOAD_GATHERCOMBINE_COOLTIME, vec![1, 0, 0]),
        (LOAD_GATHERCOMBINE_COOLTIME, vec![1, 0, 0]),
        // Denuncia de chat, filtro de spam e permissoes de canal: id do personagem e nada mais.
        (CHAT_ACCUSE, com_id(id, &[0])),
        (SPAM_FILTER_FLAG, com_id(id, &[0, 0, 0, 0])),
        (CHANNEL_CHATTING_BLACKLIST_SETTING, vec![1]),
        (CHANNEL_CHATTING_PERMISSION, vec![1]),
        (RANKING_BADGE_LIST, vec![0u8; 6]),
        (DESCONHECIDO_170, vec![0, 0]),
        (DESCONHECIDO_183, vec![1, 0]),
        (HOTSPOT, vec![0u8; 5]),
        (BM_PACK_LIST, vec![0, 0]),
        // Caixa de correio vazia.
        (MAIL, vec![0u8; 9]),
        // Macros do personagem: nenhum.
        (LOAD_MACRO, com_id(id, &[1, 0, 0])),
        // Registro de vendas do mercado global, vazio. O 1 do offset 14 e cabecalho.
        (GLOBAL_TRADE_SALESLOG, {
            let mut v = vec![0u8; 17];
            v[14] = 1;
            v
        }),
        (SPECIAL_COMBINE_RECIPE_INFO, vec![0, 0, 2]),
        (DESCONHECIDO_1AA, vec![1, 0, 0]),
        // Nenhum efeito ativo sobre o personagem. O 0x40 do offset 12 e constante na captura.
        (ABNORMAL_STATUS, {
            let mut v = vec![0u8; 15];
            v[12] = 0x40;
            v
        }),
        (NPSHOP_GOODS_COUNT, vec![0u8; 4]),
    ]);

    p
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Os tamanhos sao os da captura. Um pacote com tamanho errado desloca a leitura do cliente,
    /// e o sintoma disso -- tela de carregamento parada -- e o mesmo de meia duzia de outras
    /// coisas, entao vale travar aqui.
    #[test]
    fn os_tamanhos_batem_com_a_captura() {
        let esperado: &[(u16, usize)] = &[
            (RESULT_PASSPORT, 24),
            (CLEAR_ACHIEVEMENT_EVENT, 0),
            (LOAD_FINISHEDQUEST, 4),
            (LOAD_WORKINGQUEST, 4),
            (TITLE, 5),
            (CUSTOM_ANIM, 3),
            (USER_CLASSIC_WARDROBE_LOAD, 7),
            (RANKING_BADGE, 5),
            (STORY_BOOK_FINISHED, 6),
            (STORY_BOOK_REGISTERED, 6),
            (DESCONHECIDO_177, 6),
            (DESCONHECIDO_197, 6),
            (DESCONHECIDO_1A8, 6),
            (LOAD_PROMOTION, 3),
            (LOAD_ITEM_COOLTIME, 2),
        ];
        let feitos = antes_do_mundo(0x1234_5678);
        assert_eq!(feitos.len(), esperado.len());
        for ((op, payload), (op_esperado, tam)) in feitos.iter().zip(esperado) {
            assert_eq!(op, op_esperado);
            assert_eq!(payload.len(), *tam, "opcode 0x{op:03x}");
        }
    }

    /// O id do personagem entra nos pacotes que o carregam -- na captura eles trazem o id da
    /// personagem gravada, e mandar aquele numero faria o cliente falar de outro objeto.
    #[test]
    fn o_id_do_personagem_e_escrito() {
        let id = 0x0BAD_F00Du32;
        for (op, payload) in antes_do_mundo(id) {
            if op == STORY_BOOK_FINISHED || op == STORY_BOOK_REGISTERED {
                assert_eq!(&payload[0..4], &id.to_le_bytes());
            }
        }
        for (op, payload) in depois_do_mundo(id, 0) {
            if op == USER_BIND_STONE_INFO || op == CHAT_ACCUSE || op == LOAD_MACRO {
                assert_eq!(&payload[0..4], &id.to_le_bytes(), "opcode 0x{op:03x}");
            }
        }
    }

    /// O armazem sai completo: 24 paginas vazias, como na captura.
    #[test]
    fn o_armazem_tem_as_24_paginas() {
        let paginas = depois_do_mundo(1, 0)
            .into_iter()
            .filter(|(op, _)| *op == LOAD_WAREHOUSE)
            .count();
        assert_eq!(paginas, PAGINAS_DE_ARMAZEM);
    }
}
