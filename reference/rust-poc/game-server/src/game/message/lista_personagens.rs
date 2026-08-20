//! S_CHARACTER_LIST no layout da versao 4.5.
//!
//! A implementacao anterior era da 2.5 -- header de 238 bytes, gear, footer de 146 -- e o cliente
//! 4.5 **crasha** ao parsea-la. O layout correto foi derivado de uma captura real:
//!
//! ```text
//! [u8  contagem]
//! [u32 chave de sessao]
//! [5 bytes zero]
//! [registro de 758 bytes] x contagem
//! [u8 rodape]
//! ```
//!
//! Cada registro traz 758 bytes, dos quais 607 sao iguais entre dois personagens diferentes da
//! mesma sessao: aparencia, equipamento e campos ainda nao decodificados. Por isso o registro sai
//! de um molde capturado, com os campos conhecidos escritos por cima -- ver
//! [`super::molde`] para os offsets.
//!
//! O que isso resolve: os ids passam a ser os do servidor. Antes a lista era reproduzida inteira
//! da captura, com ids de outra sessao, entao o personagem escolhido nao existia no estado do jogo
//! e a entrada no mundo ficava sem posicao e sem mapa.
//!
//! O que ainda nao resolve: aparencia e equipamento sao os do personagem capturado, iguais para
//! todo mundo. Decodificar esses campos e trabalho separado.

use super::molde::{campo, REGISTRO_LEN, REGISTRO_MOLDE, RODAPE};

/// Cabecalho: contagem + chave de sessao + 5 bytes zerados.
const CABECALHO_LEN: usize = 10;

/// Personagem, do ponto de vista desta lista.
#[derive(Debug, Clone)]
pub struct Personagem {
    pub id: u32,
    pub nome: String,
    pub nivel: u16,
    /// Verdadeiro no personagem do ultimo login. Na captura, esse slot vem com 0x02.
    pub ultimo_login: bool,
}

#[derive(Debug, Clone)]
pub struct ListaPersonagens {
    chave_de_sessao: u32,
    personagens: Vec<Personagem>,
}

impl ListaPersonagens {
    pub fn new(chave_de_sessao: u32, personagens: Vec<Personagem>) -> Self {
        Self {
            chave_de_sessao,
            personagens,
        }
    }

    /// Tamanho do payload que [`Self::serialise_payload`] vai escrever.
    pub fn tamanho(&self) -> usize {
        CABECALHO_LEN + self.personagens.len() * REGISTRO_LEN + RODAPE.len()
    }

    /// Escreve o payload (sem o prelude de opcode) e devolve quantos bytes usou.
    pub fn serialise_payload(&self, buf: &mut [u8]) -> usize {
        let mut len = 0;

        buf[len] = self.personagens.len() as u8;
        len += 1;
        buf[len..len + 4].copy_from_slice(&self.chave_de_sessao.to_le_bytes());
        len += 4;
        buf[len..len + 5].fill(0);
        len += 5;

        for personagem in &self.personagens {
            let registro = &mut buf[len..len + REGISTRO_LEN];
            registro.copy_from_slice(&REGISTRO_MOLDE);

            registro[campo::SLOT] = if personagem.ultimo_login { 0x02 } else { 0x00 };

            registro[campo::ID..campo::ID + 4]
                .copy_from_slice(&personagem.id.to_le_bytes());

            escreve_nome(&mut registro[campo::NOME..campo::NOME + campo::NOME_MAX_BYTES],
                         &personagem.nome);

            registro[campo::NIVEL..campo::NIVEL + 4]
                .copy_from_slice(&(personagem.nivel as u32).to_le_bytes());

            len += REGISTRO_LEN;
        }

        buf[len..len + RODAPE.len()].copy_from_slice(&RODAPE);
        len += RODAPE.len();

        len
    }
}

/// Escreve o nome em UTF-16LE, terminado em nulo, no campo de tamanho fixo.
///
/// O campo ja vem zerado do molde, mas zeramos de novo: o mesmo buffer e reaproveitado entre
/// pacotes, e um nome curto depois de um longo deixaria cauda do anterior.
///
/// Nomes que nao cabem sao truncados em fronteira de caractere -- cortar no meio de um par de
/// bytes produziria um UTF-16 invalido, e o cliente e quem pagaria por isso.
fn escreve_nome(campo: &mut [u8], nome: &str) {
    campo.fill(0);

    let cabe = (campo.len() - 2) / 2; // reserva o terminador
    let mut i = 0;
    for unidade in nome.encode_utf16().take(cabe) {
        campo[i..i + 2].copy_from_slice(&unidade.to_le_bytes());
        i += 2;
    }
}

#[cfg(test)]
mod test {
    use super::*;

    fn personagem(id: u32, nome: &str, nivel: u16, ultimo: bool) -> Personagem {
        Personagem {
            id,
            nome: nome.to_string(),
            nivel,
            ultimo_login: ultimo,
        }
    }

    #[test]
    fn tamanho_bate_com_o_da_captura() {
        // A captura tinha 2 personagens e o payload media 1527 bytes.
        let lista = ListaPersonagens::new(
            0x0262_CAB6,
            vec![
                personagem(1, "Durak", 60, true),
                personagem(2, "Kimmie", 3, false),
            ],
        );
        assert_eq!(lista.tamanho(), 1527);

        let mut buf = vec![0u8; 4096];
        assert_eq!(lista.serialise_payload(&mut buf), 1527);
    }

    /// O servidor real manda uma lista vazia antes da lista de verdade. Na captura ela tem 11
    /// bytes de payload: so o cabecalho e o rodape.
    #[test]
    fn lista_vazia_tem_onze_bytes() {
        let lista = ListaPersonagens::new(0x0262_CAB6, Vec::new());
        assert_eq!(lista.tamanho(), 11);

        let mut buf = vec![0u8; 64];
        assert_eq!(lista.serialise_payload(&mut buf), 11);
        assert_eq!(buf[0], 0, "contagem zero");
    }

    #[test]
    fn campos_caem_nos_offsets_certos() {
        let lista = ListaPersonagens::new(
            0x0262_CAB6,
            vec![personagem(0x2E0F_3384, "Durak", 60, true)],
        );
        let mut buf = vec![0u8; 4096];
        lista.serialise_payload(&mut buf);

        assert_eq!(buf[0], 1, "contagem");
        assert_eq!(u32::from_le_bytes(buf[1..5].try_into().unwrap()), 0x0262_CAB6);

        let reg = &buf[CABECALHO_LEN..CABECALHO_LEN + REGISTRO_LEN];
        assert_eq!(reg[campo::SLOT], 0x02, "slot do ultimo login");
        assert_eq!(
            u32::from_le_bytes(reg[campo::ID..campo::ID + 4].try_into().unwrap()),
            0x2E0F_3384
        );
        assert_eq!(&reg[campo::NOME..campo::NOME + 10], b"D\0u\0r\0a\0k\0");
        assert_eq!(
            u32::from_le_bytes(
                reg[campo::NIVEL..campo::NIVEL + 4].try_into().unwrap()
            ),
            60
        );
    }

    #[test]
    fn nome_longo_e_truncado_sem_quebrar_o_utf16() {
        let mut campo = [0xFFu8; 12]; // cabe 5 caracteres + terminador
        escreve_nome(&mut campo, "AAAAAAAAAA");

        assert_eq!(&campo[..10], b"A\0A\0A\0A\0A\0");
        assert_eq!(&campo[10..], &[0, 0], "terminador preservado");
    }

    #[test]
    fn nome_curto_nao_deixa_cauda_do_anterior() {
        let mut campo = [0u8; 20];
        escreve_nome(&mut campo, "Kimmie");
        escreve_nome(&mut campo, "Ab");

        assert_eq!(&campo[..4], b"A\0b\0");
        assert!(campo[4..].iter().all(|&b| b == 0), "resto tem que estar limpo");
    }

    #[test]
    fn slot_de_login_so_no_primeiro() {
        let lista = ListaPersonagens::new(
            0,
            vec![
                personagem(1, "Um", 1, true),
                personagem(2, "Dois", 1, false),
            ],
        );
        let mut buf = vec![0u8; 4096];
        lista.serialise_payload(&mut buf);

        assert_eq!(buf[CABECALHO_LEN + campo::SLOT], 0x02);
        assert_eq!(buf[CABECALHO_LEN + REGISTRO_LEN + campo::SLOT], 0x00);
    }
}
