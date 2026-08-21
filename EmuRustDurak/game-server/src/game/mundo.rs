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
