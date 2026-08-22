//! O registro de item do cliente 4.5, como ele viaja no `S_LOAD_INVENTORY`.
//!
//! # Como o formato foi lido
//!
//! Da captura de 22 minutos, nos 19 `S_LOAD_INVENTORY` e 19 `S_ADD_INVENTORY` que o servidor
//! oficial mandou. O registro e:
//!
//! ```text
//! [u32 id do objeto][u32 id do item][u16 tamanho do bloco][bloco][u16 posicao][u8 tecido]
//! ```
//!
//! O tamanho do bloco fecha os pacotes byte a byte: as tres levas da primeira entrada no mundo --
//! 3350, 2102 e 56 bytes -- percorrem 21 registros e terminam exatamente no fim do payload.
//!
//! O **bloco** e uma sequencia de entradas, cada uma `[u8 tipo][dado]`, com tamanho fixo por
//! tipo. E a mesma estrutura do `ItemInfoBlob` do Aion-Lightning, e os tipos batem: 0x00 e o
//! bloco geral, 0x01 arma, 0x02 armadura, 0x04 acessorio, 0x06 slot equipado, 0x0a bonus,
//! 0x0b soquetes, 0x12 pacote. Dois tamanhos mudaram da versao da base de referencia para a 4.5,
//! e sairam da captura por diferenca: **soquetes tem 261 bytes** (eram 132) e **pacote tem 2**
//! (era 1). Com esses dois numeros, 30 dos 32 blocos de equipamento da captura percorrem inteiro
//! e param no fim -- os dois que sobram sao arma de duas maos, que abre com um bloco composto de
//! tamanho ainda desconhecido.
//!
//! O item que nao se equipa leva **so o bloco geral**, 34 bytes contando o tipo. O que se equipa
//! leva slot equipado, o bloco do slot, soquetes, pacote, os bonus aleatorios e o geral por
//! ultimo.
//!
//! # O que nao escrevemos
//!
//! Os bonus aleatorios (0x0a) -- os atributos extras que um item pode nascer com. Sao opcionais:
//! na captura o mesmo tipo de peca aparece com tres, cinco, seis ou sete deles, e um item sem
//! nenhum (`125040061`) percorre igual. Item novo nasce sem bonus, entao nao ha o que escrever.

use crate::data_loader::{ItemDef, Slot};

/// Quantos bytes o bloco de soquetes ocupa na 4.5.
///
/// Medido na captura: com 261 os blocos de equipamento fecham no byte exato; com os 132 da base
/// de referencia, nenhum fecha.
const SOQUETES_LEN: usize = 261;

/// Quantos bytes o bloco de item composto ocupa.
///
/// Ele abre o registro de toda arma de duas maos. Ficou desconhecido ate a captura de 22/08/2026
/// trazer um arco: ancorando pelo bloco de soquetes -- que e reconhecivel porque carrega o id do
/// proprio item -- o composto termina em 282. Com esse numero, **226 dos 227 registros de item
/// das duas capturas percorrem inteiros e param no fim**.
const COMPOSTO_LEN: usize = 282;

/// O bloco de escudo. Sao 20 bytes, nao 16 como na base de referencia -- medido no escudo que o
/// templario da captura recebeu.
const ESCUDO_LEN: usize = 20;

/// Tipos de entrada dentro do bloco.
const GERAL: u8 = 0x00;
const SLOT_ARMA: u8 = 0x01;
const SLOT_ARMADURA: u8 = 0x02;
const SLOT_ESCUDO: u8 = 0x03;
const SLOT_ACESSORIO: u8 = 0x04;
const SLOT_EQUIPADO: u8 = 0x06;
const SOQUETES: u8 = 0x0b;
const PACOTE: u8 = 0x12;
const COMPOSTO: u8 = 0x0e;

/// A posicao que o servidor manda quando o item nao ocupa casa na bolsa -- porque esta vestido.
pub const POSICAO_INVISIVEL: u16 = 0xFFFF;

/// Um item na bolsa do personagem.
#[derive(Debug, Clone)]
pub struct ItemInventario {
    /// Id do objeto, unico por item existente no mundo. Na captura todos comecam em `0xC0`.
    pub obj_id: u32,
    pub item_id: u32,
    pub quantidade: u64,
    /// Casa da bolsa, ou [`POSICAO_INVISIVEL`] para o que esta vestido.
    pub posicao: u16,
    pub mascara: u16,
    pub slot: Slot,
    pub tecido: bool,
}

impl ItemInventario {
    pub fn novo(obj_id: u32, item_id: u32, quantidade: u64, posicao: u16, def: Option<&ItemDef>) -> Self {
        Self {
            obj_id,
            item_id,
            quantidade,
            posicao,
            // Sem o item no catalogo nao da para calcular a mascara. Zero e o valor honesto: o
            // item aparece na bolsa sem direito a vender, trocar nem guardar, em vez de aparecer
            // com direitos inventados.
            mascara: def.map(|d| d.mascara).unwrap_or(0),
            slot: def.map(|d| d.slot).unwrap_or(Slot::Nenhum),
            tecido: def.map(|d| d.tecido).unwrap_or(false),
        }
    }

    /// Quantos bytes o registro inteiro ocupa.
    pub fn tamanho(&self) -> usize {
        4 + 4 + 2 + self.tamanho_do_bloco() + 2 + 1
    }

    fn tamanho_do_bloco(&self) -> usize {
        let geral = 1 + 33;
        let comum = (1 + 8) + (1 + SOQUETES_LEN) + (1 + 2) + geral;
        match self.slot {
            Slot::Nenhum => geral,
            Slot::Arma { duas_maos, .. } => {
                let composto = if duas_maos { 1 + COMPOSTO_LEN } else { 0 };
                composto + comum + (1 + 16)
            }
            Slot::Acessorio { .. } => comum + (1 + 16),
            Slot::Escudo(_) => comum + (1 + ESCUDO_LEN),
            Slot::Armadura(_) => comum + (1 + 20),
        }
    }

    /// Escreve o registro em `buf` e devolve quantos bytes usou.
    pub fn escreve(&self, buf: &mut [u8]) -> usize {
        let mut n = 0;
        let u16le = |buf: &mut [u8], n: &mut usize, v: u16| {
            buf[*n..*n + 2].copy_from_slice(&v.to_le_bytes());
            *n += 2;
        };

        buf[n..n + 4].copy_from_slice(&self.obj_id.to_le_bytes());
        n += 4;
        buf[n..n + 4].copy_from_slice(&self.item_id.to_le_bytes());
        n += 4;
        u16le(buf, &mut n, self.tamanho_do_bloco() as u16);

        n += self.escreve_bloco(&mut buf[n..]);

        u16le(buf, &mut n, self.posicao);
        buf[n] = self.tecido as u8;
        n + 1
    }

    fn escreve_bloco(&self, buf: &mut [u8]) -> usize {
        let mut n = 0;

        let u64le = |buf: &mut [u8], n: &mut usize, v: u64| {
            buf[*n..*n + 8].copy_from_slice(&v.to_le_bytes());
            *n += 8;
        };

        // Arma de duas maos abre com o bloco de item composto -- fusao, pedras da arma fundida.
        // Arma nova nao tem nada disso, entao vai zerado; o que o cliente cobra e o tamanho.
        if matches!(self.slot, Slot::Arma { duas_maos: true, .. }) {
            buf[n] = COMPOSTO;
            n += 1;
            buf[n..n + COMPOSTO_LEN].fill(0);
            n += COMPOSTO_LEN;
        }

        if let Some((tipo, principal, secundario, extra)) = match self.slot {
            Slot::Nenhum => None,
            Slot::Arma { principal, secundario, .. } => {
                Some((SLOT_ARMA, principal, secundario, 0))
            }
            Slot::Acessorio { principal, secundario } => {
                Some((SLOT_ACESSORIO, principal, secundario, 0))
            }
            // O escudo tem o mesmo tamanho da armadura, e so a mao secundaria preenchida.
            Slot::Escudo(bits) => Some((SLOT_ESCUDO, bits, 0, ESCUDO_LEN - 16)),
            // O bloco de armadura tem quatro bytes a mais que o de acessorio: se a peca aceita
            // tintura, e a cor em tres bytes. Peca nova nao tem cor.
            Slot::Armadura(bits) => Some((SLOT_ARMADURA, bits, 0, 4)),
        } {
            // Slot equipado: zero enquanto o item esta na bolsa. Na captura, o que a personagem
            // estava usando trazia aqui os bits do slot, e o que estava guardado trazia zero.
            buf[n] = SLOT_EQUIPADO;
            n += 1;
            u64le(buf, &mut n, 0);

            buf[n] = tipo;
            n += 1;
            u64le(buf, &mut n, principal);
            u64le(buf, &mut n, secundario);
            buf[n..n + extra].fill(0);
            n += extra;

            // Soquetes: manastones, encantamento, aparencia trocada. Item novo nao tem nada
            // disso, mas o id de aparencia e o do proprio item -- e o que a captura mostra em
            // todos, e e o que diz ao cliente qual modelo desenhar.
            buf[n] = SOQUETES;
            n += 1;
            let soquetes = &mut buf[n..n + SOQUETES_LEN];
            soquetes.fill(0);
            soquetes[2..6].copy_from_slice(&self.item_id.to_le_bytes());
            n += SOQUETES_LEN;

            buf[n] = PACOTE;
            n += 1;
            buf[n..n + 2].fill(0);
            n += 2;
        }

        // Bloco geral, o ultimo de todos e o unico que o item comum tem.
        buf[n] = GERAL;
        n += 1;
        let geral = &mut buf[n..n + 33];
        geral.fill(0);
        geral[0..2].copy_from_slice(&self.mascara.to_le_bytes());
        geral[2..10].copy_from_slice(&self.quantidade.to_le_bytes());
        // Nome de quem criou o item: cadeia vazia, so o terminador, em geral[10..12].
        // Os campos de validade e de troca temporaria ficam em zero -- item novo nao expira.
        // Os dois ultimos bytes valem 15 em todos os itens da captura, sem excecao.
        geral[31..33].copy_from_slice(&15u16.to_le_bytes());
        n + 33
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bytes(hex: &str) -> Vec<u8> {
        (0..hex.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&hex[i..i + 2], 16).unwrap())
            .collect()
    }

    /// O registro de um item comum sai byte a byte igual ao do servidor oficial.
    ///
    /// Os 47 bytes abaixo sao o registro do item 164000224 (uma pocao, dez unidades) como ele
    /// veio no `S_LOAD_INVENTORY` da captura. E o teste mais direto que da para fazer sem o
    /// cliente aberto: se a nossa conta de tamanho ou a ordem dos campos estiver errada, o
    /// resultado nao bate.
    #[test]
    fn item_comum_bate_com_a_captura() {
        let esperado = bytes(concat!(
            "a49b24c0",          // id do objeto
            "e071c609",          // id do item -- 164000224
            "2200",              // 34 bytes de bloco
            "00",                // bloco geral
            "2c61",              // mascara
            "0a00000000000000",  // dez unidades
            "000000000000000000000000000000000000000000",
            "0f00",              // os dois bytes que fecham o bloco geral
            "ffff",              // sem casa na bolsa
            "00"                 // nao e peca de corpo
        ));

        let item = ItemInventario {
            obj_id: 0xC024_9BA4,
            item_id: 164_000_224,
            quantidade: 10,
            posicao: POSICAO_INVISIVEL,
            mascara: 0x612C,
            slot: Slot::Nenhum,
            tecido: false,
        };

        let mut buf = [0u8; 128];
        let n = item.escreve(&mut buf);

        assert_eq!(n, esperado.len());
        assert_eq!(n, item.tamanho());
        assert_eq!(&buf[..n], &esperado[..]);
    }

    /// O equipamento monta os cinco blocos na ordem da captura, e nos tamanhos dela.
    ///
    /// Os tamanhos sao os que fecham os 30 blocos de equipamento gravados: 261 bytes de soquetes
    /// e 2 de pacote. Uma arma sem bonus da 325 bytes de bloco -- que e exatamente o tamanho do
    /// item 125040061 da captura, o unico que nasceu sem bonus nenhum.
    #[test]
    fn arma_monta_os_blocos_na_ordem() {
        let item = ItemInventario {
            obj_id: 0xC000_0001,
            item_id: 100_000_094,
            quantidade: 1,
            posicao: 3,
            mascara: 0x882C,
            slot: Slot::Arma { principal: 1, secundario: 2, duas_maos: false },
            tecido: false,
        };

        let mut buf = [0u8; 512];
        let n = item.escreve(&mut buf);
        assert_eq!(n, item.tamanho());

        let bloco = &buf[10..n - 3];
        assert_eq!(bloco.len(), 325, "arma sem bonus tem 325 bytes de bloco");

        assert_eq!(bloco[0], SLOT_EQUIPADO);
        // Item na bolsa nao esta vestido: os oito bytes do slot equipado sao zero.
        assert_eq!(&bloco[1..9], &[0u8; 8]);

        assert_eq!(bloco[9], SLOT_ARMA);
        assert_eq!(bloco[10], 1, "mao principal");
        assert_eq!(bloco[18], 2, "mao secundaria");

        assert_eq!(bloco[26], SOQUETES);
        // O id de aparencia e o do proprio item -- e o que diz ao cliente qual modelo desenhar.
        assert_eq!(
            u32::from_le_bytes(bloco[29..33].try_into().unwrap()),
            100_000_094
        );

        assert_eq!(bloco[26 + 1 + SOQUETES_LEN], PACOTE);
        assert_eq!(bloco[26 + 1 + SOQUETES_LEN + 3], GERAL);

        // A casa da bolsa e o byte de peca de corpo fecham o registro.
        assert_eq!(u16::from_le_bytes(buf[n - 3..n - 1].try_into().unwrap()), 3);
        assert_eq!(buf[n - 1], 0);
    }

    /// Arma de duas maos e escudo fecham nos tamanhos da captura.
    ///
    /// O arco `bow_n_l1_1a` que o ranger recebeu tem 632 bytes de bloco, com tres bonus
    /// aleatorios; sem eles -- que e o caso de item novo -- sobram 608. O escudo do templario tem
    /// 361 com quatro bonus, 329 sem. Se o bloco composto ou o de escudo estiverem com o tamanho
    /// errado, estas contas nao batem.
    #[test]
    fn duas_maos_e_escudo_batem_com_a_captura() {
        let arco = ItemInventario {
            obj_id: 0xC000_0003,
            item_id: 101_701_219,
            quantidade: 1,
            posicao: 0,
            mascara: 0,
            slot: Slot::Arma { principal: 1, secundario: 2, duas_maos: true },
            tecido: false,
        };
        let mut buf = [0u8; 1024];
        let n = arco.escreve(&mut buf);
        assert_eq!(n - 13, 608, "arco: 632 na captura, menos os tres bonus");
        assert_eq!(buf[10], COMPOSTO, "arma de duas maos abre com o bloco composto");
        assert_eq!(buf[10 + 1 + COMPOSTO_LEN], SLOT_EQUIPADO);

        let escudo = ItemInventario {
            obj_id: 0xC000_0004,
            item_id: 115_001_470,
            quantidade: 1,
            posicao: 1,
            mascara: 0,
            slot: Slot::Escudo(2),
            tecido: false,
        };
        let n = escudo.escreve(&mut buf);
        assert_eq!(n - 13, 329, "escudo: 361 na captura, menos os quatro bonus");
        assert_eq!(buf[10 + 9], SLOT_ESCUDO);
        assert_eq!(buf[10 + 10], 2, "escudo vai na mao secundaria");
    }

    /// A peca de corpo tem quatro bytes a mais que o acessorio, e o byte de tecido ligado.
    #[test]
    fn armadura_tem_o_bloco_maior_e_o_byte_de_tecido() {
        let peitoral = ItemInventario {
            obj_id: 0xC000_0002,
            item_id: 110_500_003,
            quantidade: 1,
            posicao: 4,
            mascara: 0x002C,
            slot: Slot::Armadura(1 << 3),
            tecido: true,
        };

        let mut buf = [0u8; 512];
        let n = peitoral.escreve(&mut buf);

        assert_eq!(&buf[10..n - 3].len(), &329);
        assert_eq!(buf[10 + 9], SLOT_ARMADURA);
        assert_eq!(buf[10 + 10], 1 << 3, "peitoral");
        assert_eq!(buf[n - 1], 1, "peca de corpo");
    }
}
