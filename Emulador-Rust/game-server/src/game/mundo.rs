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

/// Onde nasce um personagem **elyos** (Kaisinel Academy - Tutorial).
pub const ELYOS: PontoDeEntrada = PontoDeEntrada {
    mapa: 110_070_000,
    x: 457.0,
    y: 251.0,
    z: 127.04,
    direcao: 0,
};

/// Onde nasce um personagem **asmodiano** (Asmodae Intro Zone - Tutorial).
pub const ASMODIANO: PontoDeEntrada = PontoDeEntrada {
    mapa: 120_070_000,
    x: 457.0,
    y: 251.0,
    z: 127.04,
    direcao: 0,
};

/// O ponto de entrada da raca. `0` e elyos, `1` e asmodiano -- o campo esta no offset 60 do
/// registro de personagem, e a captura elyos traz `0` nos tres personagens.
pub fn ponto_de_entrada(raca: u32) -> PontoDeEntrada {
    match raca {
        1 => ASMODIANO,
        _ => ELYOS,
    }
}

/// Zona de introdução tutorial 4.5.
pub const MAPA: u32 = 120_070_000;

/// Posicao exata da captura de spawn inicial.
pub const X: f32 = 457.0;
pub const Y: f32 = 251.0;
pub const Z: f32 = 127.04;

/// Para onde o personagem esta virado. 1 byte no `S_WORLD`, u32 no registro da lista.
pub const DIRECAO: u8 = 0;
