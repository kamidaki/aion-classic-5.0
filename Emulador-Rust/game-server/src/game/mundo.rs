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
///
/// Medido na captura do servidor oficial (`conta-nova-2026-08-24.pcapng`): o primeiro pacote de
/// movimento do personagem (`C 0x0030`, pacote #258) sai de `x=1312.34 y=1510.76 z=568.26`, e os
/// seguintes mostram ele andando a partir dali (#437 em 1316.96, #439 em 1321.62...).
///
/// Os valores anteriores eram `457 / 251 / 127.04`, com um comentario dizendo "posicao exata da
/// captura de spawn inicial". **Nao eram**: essa combinacao nao aparece em nenhum dos 21.964
/// pacotes da captura. Com `z=127` num terreno que esta em `z=568`, o personagem nascia 440
/// metros abaixo do chao -- dentro da geometria.
pub const ELYOS: PontoDeEntrada = PontoDeEntrada {
    mapa: 110_070_000,
    x: 1312.34,
    y: 1510.76,
    z: 568.26,
    direcao: 0,
};

/// Onde nasce um personagem **asmodiano** (Asmodae Intro Zone - Tutorial).
///
/// **NAO VERIFICADO.** A unica captura que temos e de conta elyos, entao nao ha medicao do spawn
/// asmodiano. O que se sabe e que copiar as coordenadas elyos para ca esta errado -- era o que
/// havia antes, e mapas diferentes nao compartilham ponto de entrada.
///
/// Enquanto nao houver captura asmodiana, aqui ficam as coordenadas elyos como PLACEHOLDER
/// declarado, e nao como fato medido: e melhor que o valor antigo (que enterrava o personagem em
/// qualquer um dos dois mapas), mas continua sendo palpite para o lado asmodiano.
pub const ASMODIANO: PontoDeEntrada = PontoDeEntrada {
    mapa: 120_070_000,
    x: 1312.34,
    y: 1510.76,
    z: 568.26,
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

/// Posicao de spawn medida na captura oficial -- ver [`ELYOS`] para a evidencia.
pub const X: f32 = 1312.34;
pub const Y: f32 = 1510.76;
pub const Z: f32 = 568.26;

/// Para onde o personagem esta virado. 1 byte no `S_WORLD`, u32 no registro da lista.
pub const DIRECAO: u8 = 0;
