//! S_CHARACTER_LIST no layout da versao 4.5.
//!
//! ```text
//! [u8  contagem]
//! [u32 chave de sessao]
//! [5 bytes zero]
//! [u8  contagem, de novo]      <- e este que delimita a lista
//! [registro de 758 bytes] x contagem
//! ```
//!
//! Sao **dois pacotes**, nao um: primeiro uma lista vazia (11 bytes de payload), depois a real.
//! Mandando so a segunda, o cliente fecha a conexao.
//!
//! ## A contagem aparece duas vezes
//!
//! Na captura os dois bytes valem 2 (e 0 na lista vazia), entao uma leitura anterior tomou o
//! segundo como o primeiro byte do registro -- um "slot", que valeria 0x02 no personagem do ultimo
//! login. Com 2 personagens os dois layouts produzem os mesmos bytes; a diferenca so aparece com
//! contagem 1. O cabecalho dizia 1, o byte do offset 10 continuava dizendo 2, e o cliente lia um
//! registro a mais do que existia. **Era esse o crash.**
//!
//! O que descartou a leitura antiga:
//!
//! - o `writePlayerInfo()` do Aion-Lightning poe o id do personagem no inicio do registro, sem
//!   nenhum byte antes, e o nome logo depois, em 52 bytes -- exatamente o que a captura mostra se o
//!   registro comecar no offset 11
//! - o campo do offset 144 do registro vale `100000 + raca * 2 + genero`; a conta so fecha nos dois
//!   personagens da captura com o registro comecando em 11
//! - o ultimo byte do payload deixa de ser um rodape solto e passa a ser o ultimo byte do ultimo
//!   registro, igual nos dois
//!
//! Qual dos dois bytes o cliente usa de fato para dimensionar a lista, nao se sabe -- na captura
//! eles nunca discordam. Aqui os dois recebem a contagem, que e a unica combinacao compativel com
//! tudo que foi observado.
//!
//! O que isso resolve: os ids passam a ser os do servidor. Antes a lista era reproduzida inteira da
//! captura, com ids de outra sessao, entao o personagem escolhido nao existia no estado do jogo e a
//! entrada no mundo ficava sem posicao e sem mapa.
//!
//! O que ainda nao resolve: aparencia, equipamento, posicao, classe e raca saem do molde capturado,
//! iguais para todo mundo. Os offsets estao em `docs/protocol/character-list.md`.

use super::molde::{campo, REGISTRO_LEN, REGISTRO_MOLDE};

/// Contagem + chave de sessao + 5 bytes zerados + a contagem de novo.
const CABECALHO_LEN: usize = 11;

/// Personagem, do ponto de vista desta lista.
#[derive(Debug, Clone)]
pub struct Personagem {
    pub id: u32,
    pub nome: String,
    pub nivel: u16,
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
        CABECALHO_LEN + self.personagens.len() * REGISTRO_LEN
    }

    /// Escreve o payload (sem o prelude de opcode) e devolve quantos bytes usou.
    pub fn serialise_payload(&self, buf: &mut [u8]) -> usize {
        let contagem = self.personagens.len() as u8;
        let mut len = 0;

        buf[len] = contagem;
        len += 1;
        buf[len..len + 4].copy_from_slice(&self.chave_de_sessao.to_le_bytes());
        len += 4;
        buf[len..len + 5].fill(0);
        len += 5;
        buf[len] = contagem;
        len += 1;

        for personagem in &self.personagens {
            let registro = &mut buf[len..len + REGISTRO_LEN];
            registro.copy_from_slice(&REGISTRO_MOLDE);

            registro[campo::ID..campo::ID + 4].copy_from_slice(&personagem.id.to_le_bytes());

            escreve_nome(
                &mut registro[campo::NOME..campo::NOME + campo::NOME_MAX_BYTES],
                &personagem.nome,
            );

            registro[campo::NIVEL..campo::NIVEL + 2]
                .copy_from_slice(&personagem.nivel.to_le_bytes());

            len += REGISTRO_LEN;
        }

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

    fn personagem(id: u32, nome: &str, nivel: u16) -> Personagem {
        Personagem {
            id,
            nome: nome.to_string(),
            nivel,
        }
    }

    #[test]
    fn tamanho_bate_com_o_da_captura() {
        // A captura tinha 2 personagens e o payload media 1527 bytes.
        let lista = ListaPersonagens::new(
            0x0262_CAB6,
            vec![personagem(1, "Durak", 60), personagem(2, "Kimmie", 3)],
        );
        assert_eq!(lista.tamanho(), 1527);

        let mut buf = vec![0u8; 4096];
        assert_eq!(lista.serialise_payload(&mut buf), 1527);
    }

    /// O servidor real manda uma lista vazia antes da lista de verdade. Na captura ela tem 11
    /// bytes de payload: so o cabecalho.
    #[test]
    fn lista_vazia_tem_onze_bytes() {
        let lista = ListaPersonagens::new(0x0262_CAB6, Vec::new());
        assert_eq!(lista.tamanho(), 11);

        let mut buf = vec![0u8; 64];
        assert_eq!(lista.serialise_payload(&mut buf), 11);
        assert_eq!(
            &buf[..11],
            &[0x00, 0xB6, 0xCA, 0x62, 0x02, 0, 0, 0, 0, 0, 0x00]
        );
    }

    /// As duas contagens tem que andar juntas. Foi a do offset 10 que ficou para tras na leitura
    /// anterior do layout, e o cliente leu um registro a mais do que existia.
    #[test]
    fn as_duas_contagens_batem_com_o_numero_de_registros() {
        for n in 0..3usize {
            let lista = ListaPersonagens::new(
                0x0262_CAB6,
                (0..n).map(|i| personagem(i as u32, "Durak", 1)).collect(),
            );
            let mut buf = vec![0u8; 4096];
            let escritos = lista.serialise_payload(&mut buf);

            assert_eq!(buf[0] as usize, n, "contagem do offset 0");
            assert_eq!(buf[10] as usize, n, "contagem do offset 10");
            assert_eq!(escritos, CABECALHO_LEN + n * REGISTRO_LEN);
        }
    }

    #[test]
    fn campos_caem_nos_offsets_certos() {
        let lista = ListaPersonagens::new(0x0262_CAB6, vec![personagem(0x2E0F_3384, "Durak", 60)]);
        let mut buf = vec![0u8; 4096];
        lista.serialise_payload(&mut buf);

        assert_eq!(u32::from_le_bytes(buf[1..5].try_into().unwrap()), 0x0262_CAB6);

        let reg = &buf[CABECALHO_LEN..CABECALHO_LEN + REGISTRO_LEN];
        assert_eq!(
            u32::from_le_bytes(reg[campo::ID..campo::ID + 4].try_into().unwrap()),
            0x2E0F_3384
        );
        assert_eq!(&reg[campo::NOME..campo::NOME + 10], b"D\0u\0r\0a\0k\0");
        assert_eq!(
            u16::from_le_bytes(reg[campo::NIVEL..campo::NIVEL + 2].try_into().unwrap()),
            60
        );
    }

    /// O campo de nome tem 52 bytes, e o que vem depois e o genero -- que na captura vale 1 nos
    /// dois personagens. Uma versao anterior estimou 56 bytes de nome, zerou o genero junto, e o
    /// cliente crashou. Este teste fixa a fronteira.
    #[test]
    fn molde_preserva_o_genero_logo_depois_do_nome() {
        let lista = ListaPersonagens::new(0, vec![personagem(1, "Durak", 60)]);
        let mut buf = vec![0u8; 4096];
        lista.serialise_payload(&mut buf);

        let reg = &buf[CABECALHO_LEN..CABECALHO_LEN + REGISTRO_LEN];
        assert_eq!(
            &reg[56..60],
            &[0x01, 0x00, 0x00, 0x00],
            "o genero vem logo depois do nome e nao pode ser zerado"
        );
    }

    /// Com os valores do personagem da captura, o pacote inteiro -- cabecalho e registro -- tem que
    /// sair byte a byte igual ao capturado. E o que garante que o molde nao perdeu nem ganhou byte.
    #[test]
    fn reproduz_o_pacote_capturado() {
        use super::super::capturado::{CHARACTER_LIST_2, CHAVE_CAPTURADA};

        let lista =
            ListaPersonagens::new(CHAVE_CAPTURADA, vec![personagem(0x2E0F_3384, "Durak", 60)]);
        let mut buf = vec![0u8; 4096];
        let escritos = lista.serialise_payload(&mut buf);

        // A captura tem 2 personagens; comparamos ate onde o primeiro registro vai, com a contagem
        // ajustada para 1 nos dois lugares onde ela aparece.
        let mut esperado = CHARACTER_LIST_2[..escritos].to_vec();
        esperado[0] = 1;
        esperado[10] = 1;

        assert_eq!(&buf[..escritos], &esperado[..]);
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
}
