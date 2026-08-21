//! S_CHARACTER_LIST no layout da versao 4.5.
//!
//! ```text
//! [u8  marca: 0x02 na lista com personagens, 0x00 na vazia]
//! [u32 chave de sessao]
//! [5 bytes zero]
//! [u8  contagem de personagens]
//! [registro de 758 bytes] x contagem
//! ```
//!
//! Sao **dois pacotes**, nao um: primeiro uma lista vazia (11 bytes de payload), depois a real.
//! Mandando so a segunda, o cliente fecha a conexao.
//!
//! ## Os dois bytes do cabecalho
//!
//! Na captura o byte 0 e o byte 10 valem a mesma coisa -- 2 na lista de 2 personagens, 0 na vazia
//! -- entao uma leitura anterior tomou o do offset 10 como o primeiro byte do registro, um "slot"
//! que valeria 0x02 no personagem do ultimo login. Com 2 personagens as duas leituras produzem os
//! mesmos bytes; a diferenca so aparece com 1.
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
//! E os dois bytes do cabecalho tem papeis diferentes: o byte 10 e a contagem, e o byte 0 e uma
//! marca que precisa valer 0x02 -- ver [`MARCA_DE_LISTA`] para a tabela de rodadas que separou um
//! do outro. Mandar a contagem no byte 0 fazia o cliente parar na tela de servidor, sem mensagem.
//!
//! O que isso resolve: os ids passam a ser os do servidor. Antes a lista era reproduzida inteira da
//! captura, com ids de outra sessao, entao o personagem escolhido nao existia no estado do jogo e a
//! entrada no mundo ficava sem posicao e sem mapa.
//!
//! O que ainda nao resolve: aparencia, equipamento, posicao, classe e raca saem do molde capturado,
//! iguais para todo mundo. Os offsets estao em `docs/protocol/character-list.md`.

use super::molde::{campo, REGISTRO_LEN, REGISTRO_MOLDE};

/// Marca + chave de sessao + 5 bytes zerados + a contagem.
const CABECALHO_LEN: usize = 11;

/// O byte 0 do cabecalho, na lista que tem personagens. **Nao e contagem** -- e o cliente que
/// disse isso, em quatro rodadas:
///
/// ```text
///   byte 0   byte 10   registros   resultado
///     02       02          2       passa (replay da captura)
///     01       02          1       para na tela de servidor
///     01       01          1       para na tela de servidor
///     02       01          1       passa: tela de personagem e mundo
/// ```
///
/// A captura so tem dois casos -- 0 na lista vazia e 2 na lista de 2 personagens -- e nos dois a
/// contagem e a marca coincidem, o que escondeu a diferenca. Com 1 personagem elas se separam: o
/// que importa e o byte 0 valer `0x02`, e o byte 10 e que acompanha a contagem.
///
/// O significado continua desconhecido -- tipo de lista, numero de slots da conta, outra coisa. O
/// que se sabe e que `0x02` serve para 0, 1 e 2 registros (a lista vazia tambem foi aceita com
/// `0x02` no lugar do `0x00` da captura). Aqui a lista vazia mantem o `0x00`, que e o que o
/// servidor real manda; para experimentar outros valores existe `AION_CABECALHO`.
///
/// Se um dia a conta tiver 3 personagens, e o primeiro caso capaz de separar "constante" de
/// "numero de slots": vale conferir se `0x02` ainda serve.
const MARCA_DE_LISTA: u8 = 0x02;

/// Personagem, do ponto de vista desta lista.
#[derive(Debug, Clone)]
pub struct Personagem {
    pub id: u32,
    pub nome: String,
    pub nivel: u16,
    /// Os 140 bytes que o cliente mandou na criacao. Quando presentes substituem o trecho 4..144
    /// do molde -- nome, genero, raca, classe, voz, cores, rosto e altura de uma vez. Sem eles o
    /// personagem sai com a cara do molde capturado.
    pub aparencia: Option<Vec<u8>>,
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
        let marca = if self.personagens.is_empty() {
            0x00
        } else {
            MARCA_DE_LISTA
        };
        let (byte0, byte10) = cabecalho_de_teste(marca, contagem);
        let mut len = 0;

        buf[len] = byte0;
        len += 1;
        buf[len..len + 4].copy_from_slice(&self.chave_de_sessao.to_le_bytes());
        len += 4;
        buf[len..len + 5].fill(0);
        len += 5;
        buf[len] = byte10;
        len += 1;

        for personagem in &self.personagens {
            escreve_registro(&mut buf[len..len + REGISTRO_LEN], personagem);
            len += REGISTRO_LEN;
        }

        len
    }
}

/// Escreve um registro de personagem de [`REGISTRO_LEN`] bytes: o molde capturado com os campos
/// que o servidor conhece por cima.
///
/// Serve a lista e tambem o `S_CREATE_CHARACTER`, que leva o mesmo registro -- ver
/// [`REGISTRO_CRIACAO_LEN`].
pub fn escreve_registro(registro: &mut [u8], personagem: &Personagem) {
    registro.copy_from_slice(&REGISTRO_MOLDE);

    registro[campo::ID..campo::ID + 4].copy_from_slice(&personagem.id.to_le_bytes());

    // O bloco da criacao cobre nome, genero, raca, classe, voz, cores, rosto e altura de uma vez:
    // o pedido do cliente carrega exatamente o trecho 4..144 do registro, conferido byte a byte
    // contra a captura. O nome ainda e escrito depois, porque o banco e quem manda nele.
    if let Some(bloco) = &personagem.aparencia {
        if bloco.len() == campo::APARENCIA_LEN {
            registro[campo::NOME..campo::NOME + campo::APARENCIA_LEN].copy_from_slice(bloco);
            // A redundancia que valida o alinhamento do registro; ver molde::campo.
            let genero = u32::from_le_bytes(
                registro[campo::GENERO..campo::GENERO + 4].try_into().unwrap(),
            );
            let raca =
                u32::from_le_bytes(registro[campo::RACA..campo::RACA + 4].try_into().unwrap());
            registro[campo::REDUNDANCIA..campo::REDUNDANCIA + 4]
                .copy_from_slice(&(100_000 + raca * 2 + genero).to_le_bytes());
        } else {
            eprintln!(
                "WARNING: bloco de aparencia com {} bytes (esperado {}); usando o molde",
                bloco.len(),
                campo::APARENCIA_LEN
            );
        }
    }

    escreve_nome(
        &mut registro[campo::NOME..campo::NOME + campo::NOME_MAX_BYTES],
        &personagem.nome,
    );

    registro[campo::NIVEL..campo::NIVEL + 2].copy_from_slice(&personagem.nivel.to_le_bytes());

    escreve_ponto_de_entrada(registro);
}

/// Quanto do registro o `S_CREATE_CHARACTER` leva.
///
/// O pacote de criacao da captura tem 748 bytes: 4 de resultado mais 744 do registro. Comparado com
/// o registro do mesmo personagem na lista seguinte, os 744 batem posicao a posicao -- as unicas
/// diferencas sao mapa, posicao, direcao, nivel e os slots de equipamento, que na criacao ainda nao
/// tem valor de jogo. Os 14 bytes que o registro da lista tem a mais sao todos zero.
pub const REGISTRO_CRIACAO_LEN: usize = 744;

/// Escreve mapa, posicao e direcao por cima do que veio no molde.
///
/// O molde e o registro do Durak, e traz o mapa e a posicao dele. Como o `S_WORLD` manda o ponto de
/// entrada de [`crate::game::mundo`], os dois campos precisam concordar: e pelo mapa daqui que o
/// cliente pre-carrega o cenario, e entrar num mapa que ele nao carregou nao funciona.
fn escreve_ponto_de_entrada(registro: &mut [u8]) {
    use crate::game::mundo;

    registro[campo::MAPA..campo::MAPA + 4].copy_from_slice(&mundo::MAPA.to_le_bytes());

    let posicao = campo::POSICAO;
    registro[posicao..posicao + 4].copy_from_slice(&mundo::X.to_le_bytes());
    registro[posicao + 4..posicao + 8].copy_from_slice(&mundo::Y.to_le_bytes());
    registro[posicao + 8..posicao + 12].copy_from_slice(&mundo::Z.to_le_bytes());

    registro[campo::DIRECAO..campo::DIRECAO + 4]
        .copy_from_slice(&(mundo::DIRECAO as u32).to_le_bytes());
}

/// Escape para bissecao: `AION_CABECALHO="2,1"` escreve 2 no offset 0 e 1 no offset 10. Campo
/// vazio ou ausente fica com o valor normal. Existe porque o significado do byte 0 ainda nao esta
/// fechado -- ver [`MARCA_DE_LISTA`] -- e trocar os dois bytes sem recompilar e o que permite
/// perguntar para o cliente.
fn cabecalho_de_teste(marca: u8, contagem: u8) -> (u8, u8) {
    let Ok(spec) = std::env::var("AION_CABECALHO") else {
        return (marca, contagem);
    };

    let mut campos = spec.split(',');
    let mut le = |rotulo: &str, normal: u8| match campos.next().map(str::trim) {
        Some(v) if !v.is_empty() => match v.parse::<u8>() {
            Ok(n) => {
                println!("INFO: AION_CABECALHO: byte {rotulo} = {n} (em vez de {normal})");
                n
            }
            Err(_) => {
                eprintln!("WARN: AION_CABECALHO: '{v}' nao e um byte; usando {normal}");
                normal
            }
        },
        _ => normal,
    };

    (le("0", marca), le("10", contagem))
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
            aparencia: None,
        }
    }

    /// O bloco da criacao cobre exatamente de `NOME` ate `REDUNDANCIA`, e e o mesmo tamanho que o
    /// pedido do cliente carrega -- foi conferido byte a byte contra a captura.
    #[test]
    fn bloco_de_aparencia_vai_do_nome_ate_a_redundancia() {
        assert_eq!(campo::APARENCIA_LEN, 140);
        assert_eq!(campo::NOME + campo::APARENCIA_LEN, campo::REDUNDANCIA);
    }

    /// Com bloco, o registro sai com genero, raca e classe do jogador -- e a redundancia recalculada
    /// a partir deles, que e o que prova que o alinhamento nao andou.
    #[test]
    fn aparencia_escreve_raca_classe_e_recalcula_a_redundancia() {
        let mut bloco = vec![0u8; campo::APARENCIA_LEN];
        let genero: u32 = 1;
        let raca: u32 = 1;
        let classe: u32 = 7;
        bloco[campo::GENERO - campo::NOME..][..4].copy_from_slice(&genero.to_le_bytes());
        bloco[campo::RACA - campo::NOME..][..4].copy_from_slice(&raca.to_le_bytes());
        bloco[campo::CLASSE - campo::NOME..][..4].copy_from_slice(&classe.to_le_bytes());

        let mut registro = [0u8; REGISTRO_LEN];
        escreve_registro(
            &mut registro,
            &Personagem {
                id: 7,
                nome: "Krime".to_string(),
                nivel: 1,
                aparencia: Some(bloco),
            },
        );

        let ler = |off: usize| u32::from_le_bytes(registro[off..off + 4].try_into().unwrap());
        assert_eq!(ler(campo::GENERO), genero);
        assert_eq!(ler(campo::RACA), raca);
        assert_eq!(ler(campo::CLASSE), classe);
        assert_eq!(ler(campo::REDUNDANCIA), 100_000 + raca * 2 + genero);

        // O nome continua vindo do banco, escrito depois do bloco.
        let nome = String::from_utf16_lossy(
            &registro[campo::NOME..campo::NOME + 10]
                .chunks(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .collect::<Vec<_>>(),
        );
        assert!(nome.starts_with("Krime"), "nome saiu como {nome:?}");
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

    /// A marca nao acompanha a contagem. Foi tratar o byte 0 como contagem que fez o cliente parar
    /// na tela de servidor com 1 personagem, sem mensagem nenhuma.
    #[test]
    fn marca_e_contagem_tem_papeis_diferentes() {
        for n in 0..3usize {
            let lista = ListaPersonagens::new(
                0x0262_CAB6,
                (0..n).map(|i| personagem(i as u32, "Durak", 1)).collect(),
            );
            let mut buf = vec![0u8; 4096];
            let escritos = lista.serialise_payload(&mut buf);

            let marca_esperada = if n == 0 { 0x00 } else { MARCA_DE_LISTA };
            assert_eq!(buf[0], marca_esperada, "marca do offset 0, com {n} personagens");
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

        // A captura tem 2 personagens; comparamos ate onde o primeiro registro vai. Muda a
        // contagem, e mudam os campos que o servidor escreve por cima do molde -- aqui, o ponto de
        // entrada. O resto tem que sair byte a byte igual, que e o que prova que o molde nao
        // perdeu nem ganhou byte.
        let mut esperado = CHARACTER_LIST_2[..escritos].to_vec();
        esperado[10] = 1;
        escreve_ponto_de_entrada(&mut esperado[CABECALHO_LEN..CABECALHO_LEN + REGISTRO_LEN]);

        assert_eq!(&buf[..escritos], &esperado[..]);
    }

    /// O mapa que a lista declara e o que o cliente pre-carrega. Se ele discordar do que o
    /// `S_WORLD` mandar depois, o cliente entra num mundo que nao carregou.
    #[test]
    fn a_lista_declara_o_mesmo_ponto_de_entrada_do_s_world() {
        use crate::game::mundo;

        let lista = ListaPersonagens::new(0, vec![personagem(1, "Durak", 60)]);
        let mut buf = vec![0u8; 4096];
        lista.serialise_payload(&mut buf);

        let reg = &buf[CABECALHO_LEN..CABECALHO_LEN + REGISTRO_LEN];
        let u32_em = |o: usize| u32::from_le_bytes(reg[o..o + 4].try_into().unwrap());
        let f32_em = |o: usize| f32::from_le_bytes(reg[o..o + 4].try_into().unwrap());

        assert_eq!(u32_em(campo::MAPA), mundo::MAPA);
        assert_eq!(f32_em(campo::POSICAO), mundo::X);
        assert_eq!(f32_em(campo::POSICAO + 4), mundo::Y);
        assert_eq!(f32_em(campo::POSICAO + 8), mundo::Z);
        assert_eq!(u32_em(campo::DIRECAO), mundo::DIRECAO as u32);
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
