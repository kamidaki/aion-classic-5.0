//! Motor de replay: responde com pacotes de uma sessao real capturada, para os opcodes que o
//! servidor ainda nao sabe construir.
//!
//! Existe como andaime. Cada pacote servido da captura mantem o cliente avancando e revela o
//! proximo ponto do fluxo; a ideia e ir trocando um por um por implementacao de verdade.
//!
//! **E indexado por opcode, nao por posicao.** Uma primeira versao usava um cursor sobre a captura,
//! avancando um passo por pacote recebido. Nao funcionou: o cliente ao vivo manda `C_SYNC_TIME`
//! extras e em cadencia propria, entao o cursor dessincronizava e ele passava a receber respostas
//! fora de lugar -- chegou a repetir `C_HQ_LOGIN`, como se nao tivesse sido atendido. Indexar por
//! opcode e imune a diferenca de ordem.
//!
//! So atende opcodes **sem implementacao**. Se atendesse todos, os handlers ja existentes
//! responderiam junto e o cliente receberia cada pacote duas vezes.
//!
//! Gerar o arquivo com: `python tools/export_replay.py <pcap> replay.bin`

use std::collections::HashMap;
use std::collections::VecDeque;
use std::fs;
use std::path::Path;

use super::server;

/// Chave de sessao em uso quando a captura foi feita. Aparece dentro de varios payloads e e
/// trocada pela da sessao atual no momento do envio.
///
/// Duas capturas da mesma conta, feitas em dias diferentes, trouxeram o mesmo valor -- entao ele
/// identifica a conta, nao a sessao. Continua sendo trocado, porque o cliente ao vivo tem o dele.
const CHAVE_CAPTURADA: u32 = 0x026E_DF39;

/// Id do personagem que estava logado na captura. Mesmo caso da chave: aparece espalhado pelos
/// payloads -- estado, animacao, buffs, spawn -- e precisa virar o id do personagem desta sessao.
///
/// Sem essa troca o cliente recebe dois "eus": o nosso, com o id do banco, e o da captura, com o
/// id de outra sessao. Os pacotes que falam do personagem passam a apontar para um objeto que nao
/// e o que ele controla.
///
/// **Muda a cada captura**, ao contrario da chave acima. Para achar o valor de uma captura nova, e
/// o u32 no offset 0 do payload de `S_STATUS` (0x001) -- se aparecer mais de um, a captura tem mais
/// de um personagem, e vale o mais frequente.
///
/// `AION_ID_CAPTURADO=0x2E4627F1` troca sem recompilar, para alternar entre replays de capturas
/// diferentes -- o valor aqui e o da captura que gera o `replay.bin` padrao.
const ID_CAPTURADO: u32 = 0x2E46_283A;

/// O `ID_CAPTURADO` em uso, com o escape por variavel de ambiente aplicado. Aceita `0x` na frente.
///
/// Resolvido uma vez: e chamado por pacote servido, e reler a variavel -- e imprimir a linha de
/// INFO -- em cada um enche o log a ponto de esconder o que interessa.
fn id_capturado() -> u32 {
    static VALOR: std::sync::OnceLock<u32> = std::sync::OnceLock::new();
    *VALOR.get_or_init(resolve_id_capturado)
}

fn resolve_id_capturado() -> u32 {
    let Ok(bruto) = std::env::var("AION_ID_CAPTURADO") else {
        return ID_CAPTURADO;
    };
    let texto = bruto.trim();
    let sem_prefixo = texto.strip_prefix("0x").or_else(|| texto.strip_prefix("0X"));
    let lido = match sem_prefixo {
        Some(hex) => u32::from_str_radix(hex, 16),
        None => u32::from_str_radix(texto, 16),
    };
    match lido {
        Ok(v) => {
            println!("INFO: AION_ID_CAPTURADO={v:#010X} (no lugar de {ID_CAPTURADO:#010X})");
            v
        }
        Err(_) => {
            eprintln!("WARNING: AION_ID_CAPTURADO={bruto:?} nao e hexadecimal -- usando o padrao");
            ID_CAPTURADO
        }
    }
}

const DIRECAO_SERVIDOR: u8 = 0;

/// Pacotes de servidor que o replay nao pode servir, porque nos ja mandamos os nossos.
///
/// O `S_WORLD` duplicado faz o cliente carregar o mundo duas vezes -- a tela de carregamento
/// aparece duas seguidas. O `S_CHARACTER_LIST` traria de volta os personagens da conta capturada,
/// por cima da lista que sai do banco.
const NAO_REPLAYAR: [u16; 2] = [
    0x00F, // S_WORLD
    0x0C7, // S_CHARACTER_LIST
];

/// Um pacote de servidor da captura: opcode ja decifrado e payload sem o prelude.
type PacoteServidor = (u16, Vec<u8>);

pub struct Replay {
    /// Para cada opcode de cliente, os lotes de resposta que o servidor real deu, na ordem em que
    /// ocorreram. Cada lote e consumido uma vez.
    respostas: HashMap<u16, VecDeque<Vec<PacoteServidor>>>,
}

impl Replay {
    /// Carrega a sessao capturada. Devolve `None` se o arquivo nao existir -- o replay e opcional,
    /// e o servidor roda sem ele.
    pub fn carregar(caminho: &Path) -> Option<Self> {
        let dados = fs::read(caminho).ok()?;
        let mut entradas: Vec<(u8, u16, Vec<u8>)> = Vec::new();
        let mut i = 0;

        while i + 7 <= dados.len() {
            let direcao = dados[i];
            let opcode = u16::from_le_bytes([dados[i + 1], dados[i + 2]]);
            let tamanho =
                u32::from_le_bytes([dados[i + 3], dados[i + 4], dados[i + 5], dados[i + 6]])
                    as usize;
            i += 7;

            if i + tamanho > dados.len() {
                eprintln!("WARNING: replay truncado, parando em {} entradas", entradas.len());
                break;
            }
            entradas.push((direcao, opcode, dados[i..i + tamanho].to_vec()));
            i += tamanho;
        }

        // agrupa: cada pacote de cliente leva consigo os pacotes de servidor que vieram depois
        // dele, ate o proximo de cliente
        let mut respostas: HashMap<u16, VecDeque<Vec<PacoteServidor>>> = HashMap::new();
        let mut j = 0;
        while j < entradas.len() {
            if entradas[j].0 == DIRECAO_SERVIDOR {
                j += 1;
                continue;
            }
            let opcode_cliente = entradas[j].1;
            j += 1;

            let mut lote = Vec::new();
            while j < entradas.len() && entradas[j].0 == DIRECAO_SERVIDOR {
                lote.push((entradas[j].1, entradas[j].2.clone()));
                j += 1;
            }
            if !lote.is_empty() {
                respostas.entry(opcode_cliente).or_default().push_back(lote);
            }
        }

        let total: usize = respostas.values().map(|v| v.len()).sum();
        println!(
            "INFO: replay carregado de {}: {} opcodes de cliente, {} lotes de resposta",
            caminho.display(),
            respostas.len(),
            total
        );

        Some(Self { respostas })
    }

    /// Resposta capturada para um opcode de cliente. Cada lote e devolvido uma unica vez; quando
    /// acabam, devolve vazio em vez de repetir -- repetir faria o cliente receber estado velho.
    pub fn resposta_para(
        &mut self,
        opcode: u16,
        chave_da_sessao: u32,
        id_do_personagem: u32,
    ) -> Vec<server::Message> {
        let Some(fila) = self.respostas.get_mut(&opcode) else {
            return Vec::new();
        };
        let Some(lote) = fila.pop_front() else {
            return Vec::new();
        };

        println!(
            "INFO: replay atende opcode 0x{opcode:02X} com {} pacote(s)",
            lote.len()
        );

        lote.into_iter()
            .filter(|(op, _)| !NAO_REPLAYAR.contains(op))
            .map(|(op, payload)| {
                let payload = com_chave_de_sessao(&payload, chave_da_sessao);
                let payload = if id_do_personagem == 0 {
                    payload
                } else {
                    troca(&payload, id_capturado(), id_do_personagem)
                };
                server::Message::Bruto(server::Bruto::new(op, payload))
            })
            .collect()
    }
}

/// Troca a chave de sessao da captura pela da sessao atual, onde quer que ela apareca.
///
/// A busca e pela sequencia de bytes, nao por offset: os payloads sao grandes e o campo aparece em
/// posicoes diferentes conforme o pacote.
fn com_chave_de_sessao(payload: &[u8], chave: u32) -> Vec<u8> {
    troca(payload, CHAVE_CAPTURADA, chave)
}

/// Troca todas as ocorrencias de um u32 por outro, alinhando a busca ao proprio campo.
///
/// A busca e pela sequencia de bytes, nao por offset: os payloads sao grandes e os campos aparecem
/// em posicoes diferentes conforme o pacote. O risco e trocar uma coincidencia -- quatro bytes de
/// aparencia ou de id de item que por acaso batam -- mas os dois valores trocados aqui sao
/// especificos o bastante para isso ser improvavel.
fn troca(payload: &[u8], de: u32, para: u32) -> Vec<u8> {
    let de = de.to_le_bytes();
    let para = para.to_le_bytes();
    let mut saida = payload.to_vec();
    let mut i = 0;
    while i + 4 <= saida.len() {
        if saida[i..i + 4] == de {
            saida[i..i + 4].copy_from_slice(&para);
            i += 4;
        } else {
            i += 1;
        }
    }
    saida
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn troca_a_chave_em_todas_as_ocorrencias() {
        let mut payload = vec![0x00; 16];
        payload[1..5].copy_from_slice(&CHAVE_CAPTURADA.to_le_bytes());
        payload[10..14].copy_from_slice(&CHAVE_CAPTURADA.to_le_bytes());

        let saida = com_chave_de_sessao(&payload, 0x0262_CAB6);

        assert_eq!(&saida[1..5], &0x0262_CAB6u32.to_le_bytes());
        assert_eq!(&saida[10..14], &0x0262_CAB6u32.to_le_bytes());
        assert_eq!(saida[0], 0x00);
        assert_eq!(saida[5], 0x00);
    }

    #[test]
    fn nao_troca_o_que_apenas_se_parece() {
        let mut payload = CHAVE_CAPTURADA.to_le_bytes().to_vec();
        payload[0] ^= 0xFF;
        let original = payload.clone();

        assert_eq!(com_chave_de_sessao(&payload, 0x1234_5678), original);
    }

    #[test]
    fn cada_lote_e_servido_uma_vez_so() {
        let mut respostas = HashMap::new();
        let mut fila = VecDeque::new();
        fila.push_back(vec![(0x0001u16, vec![1, 2, 3])]);
        respostas.insert(0xD6u16, fila);
        let mut replay = Replay { respostas };

        assert_eq!(replay.resposta_para(0xD6, 0, 0).len(), 1);
        assert!(replay.resposta_para(0xD6, 0, 0).is_empty());
    }

    /// O S_WORLD replayado faz o cliente carregar o mundo de novo -- a tela de carregamento aparece
    /// duas vezes seguidas -- e o S_CHARACTER_LIST traria de volta os personagens da captura.
    #[test]
    fn nao_replaya_o_que_nos_mesmos_mandamos() {
        let mut respostas = HashMap::new();
        let mut fila = VecDeque::new();
        fila.push_back(vec![
            (0x000Fu16, vec![1]), // S_WORLD
            (0x00C7u16, vec![2]), // S_CHARACTER_LIST
            (0x0001u16, vec![3]), // S_STATUS, esse passa
        ]);
        respostas.insert(0xD6u16, fila);
        let mut replay = Replay { respostas };

        assert_eq!(replay.resposta_para(0xD6, 0, 0).len(), 1);
    }

    /// O id do personagem da captura aparece espalhado pelos payloads replayados. Sem trocar, o
    /// cliente recebe pacotes que falam de um personagem que nao e o dele.
    #[test]
    fn troca_o_id_do_personagem_no_lote() {
        let payload = [
            ID_CAPTURADO.to_le_bytes().as_slice(),
            &[0xAA, 0xBB],
            ID_CAPTURADO.to_le_bytes().as_slice(),
        ]
        .concat();

        let trocado = troca(&payload, ID_CAPTURADO, 0x0000_000E);

        assert_eq!(&trocado[0..4], &0x0000_000Eu32.to_le_bytes());
        assert_eq!(&trocado[4..6], &[0xAA, 0xBB]);
        assert_eq!(&trocado[6..10], &0x0000_000Eu32.to_le_bytes());
    }

    #[test]
    fn opcode_sem_resposta_na_captura_devolve_vazio() {
        let mut replay = Replay { respostas: HashMap::new() };
        assert!(replay.resposta_para(0x1234, 0, 0).is_empty());
    }
}
