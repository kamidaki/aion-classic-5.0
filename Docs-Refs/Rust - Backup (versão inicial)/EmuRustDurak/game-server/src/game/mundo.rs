//! Onde um personagem entra no mundo.
//!
//! Estes valores vem da sessao capturada da Gameforge: sao o mapa, a posicao e a direcao com que a
//! Kimmie entrou no jogo, e a unica combinacao que se sabe que o cliente 4.5 aceita de ponta a
//! ponta -- ela aparece duas vezes na captura, no registro dela dentro do `S_CHARACTER_LIST` e
//! depois no `S_WORLD`.
//!
//! Os dois lugares tem que concordar. E pelo mapa do registro que o cliente pre-carrega o cenario,
//! entao mandar um mapa na lista e outro no `S_WORLD` e pedir para o cliente entrar num mundo que
//! ele nao carregou.
//!
//! Por enquanto todo personagem nasce aqui, porque o banco ainda nao guarda mapa -- so x, y e z.
//! Quando guardar, isto vira o valor padrao de personagem novo, e a lista e o `S_WORLD` passam a
//! ler do personagem. Os offsets do registro estao em `docs/protocol/character-list.md`.

/// O ponto de entrada de uma raca: mapa, posicao e direcao.
#[derive(Debug, Clone, Copy)]
pub struct PontoDeEntrada {
    pub mapa: u32,
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub direcao: u8,
}

/// Onde nasce um personagem **elyos**.
///
/// Da captura de 22/08/2026, que gravou a criacao de tres personagens elyos no servidor oficial:
/// assassino, templario e ranger nasceram todos aqui. O `S_WORLD` e o registro de personagem
/// concordam, que e o que o cliente exige.
///
/// Antes disto todo personagem nascia em Pandaemonium, a capital **asmodiana**, porque era de la
/// que vinha a unica captura que existia. Um personagem elyos mandado para a capital inimiga e
/// errado de um jeito visivel: o jogador via "Pandaemonium" no lugar de "Sanctum".
pub const ELYOS: PontoDeEntrada = PontoDeEntrada {
    mapa: 110_030_000,
    x: 1314.705078125,
    y: 1513.3416748046875,
    z: 568.1068115234375,
    direcao: 0,
};

/// Onde nasce um personagem **asmodiano**.
///
/// Da captura de 21/08/2026 -- a Kimmie, que tinha cinco minutos de criada quando a sessao
/// comecou, entao a posicao dela e o ponto de nascimento e nao um lugar qualquer.
pub const ASMODIANO: PontoDeEntrada = PontoDeEntrada {
    mapa: MAPA,
    x: X,
    y: Y,
    z: Z,
    direcao: DIRECAO,
};

/// O ponto de entrada da raca. `0` e elyos, `1` e asmodiano -- o campo esta no offset 60 do
/// registro de personagem, e a captura elyos traz `0` nos tres personagens.
pub fn ponto_de_entrada(raca: u32) -> PontoDeEntrada {
    match raca {
        1 => ASMODIANO,
        _ => ELYOS,
    }
}

/// Pandaemonium, onde nasce personagem novo na 4.5 -- o mapa foi refeito nesta versao.
///
/// O nome sai do `world_maps.xml` da base Java (`server/AL-Game/data/static_data/`), e a escolha
/// sai da captura: a Kimmie tinha sido criada cinco minutos antes da sessao -- data de criacao
/// 07:35, ultimo login 07:40 -- entao a posicao dela e o ponto de nascimento, nao um lugar
/// qualquer onde ela estivesse.
pub const MAPA: u32 = 120_010_000;

/// Posicao exata da captura -- os literais reproduzem os mesmos bits dos floats capturados.
pub const X: f32 = 1295.823974609375;
pub const Y: f32 = 1416.31103515625;
pub const Z: f32 = 208.125;

/// Para onde o personagem esta virado. 1 byte no `S_WORLD`, u32 no registro da lista.
pub const DIRECAO: u8 = 109;
