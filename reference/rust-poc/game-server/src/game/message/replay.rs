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
const CHAVE_CAPTURADA: u32 = 0x026E_DF39;

const DIRECAO_SERVIDOR: u8 = 0;

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
    pub fn resposta_para(&mut self, opcode: u16, chave_da_sessao: u32) -> Vec<server::Message> {
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
            .map(|(op, payload)| {
                server::Message::Bruto(server::Bruto::new(
                    op,
                    com_chave_de_sessao(&payload, chave_da_sessao),
                ))
            })
            .collect()
    }
}

/// Troca a chave de sessao da captura pela da sessao atual, onde quer que ela apareca.
///
/// A busca e pela sequencia de bytes, nao por offset: os payloads sao grandes e o campo aparece em
/// posicoes diferentes conforme o pacote.
fn com_chave_de_sessao(payload: &[u8], chave: u32) -> Vec<u8> {
    let de = CHAVE_CAPTURADA.to_le_bytes();
    let para = chave.to_le_bytes();
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
        fila.push_back(vec![(0x00C7u16, vec![1, 2, 3])]);
        respostas.insert(0xD6u16, fila);
        let mut replay = Replay { respostas };

        assert_eq!(replay.resposta_para(0xD6, 0).len(), 1);
        assert!(replay.resposta_para(0xD6, 0).is_empty());
    }

    #[test]
    fn opcode_sem_resposta_na_captura_devolve_vazio() {
        let mut replay = Replay { respostas: HashMap::new() };
        assert!(replay.resposta_para(0x1234, 0).is_empty());
    }
}
