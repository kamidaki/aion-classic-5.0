//! Serialização de registros de itens do inventário no protocolo de rede.

use crate::data_loader::{ItemDef, Slot};

const SOQUETES_LEN: usize = 261;
const COMPOSTO_LEN: usize = 282;
const ESCUDO_LEN: usize = 20;

const GERAL: u8 = 0x00;
const SLOT_ARMA: u8 = 0x01;
const SLOT_ARMADURA: u8 = 0x02;
const SLOT_ESCUDO: u8 = 0x03;
const SLOT_ACESSORIO: u8 = 0x04;
const SLOT_EQUIPADO: u8 = 0x06;
const SOQUETES: u8 = 0x0b;
const PACOTE: u8 = 0x12;
const COMPOSTO: u8 = 0x0e;

pub const POSICAO_INVISIVEL: u16 = 0xFFFF;

/// Um item no inventário / bolsa do jogador.
#[derive(Debug, Clone)]
pub struct ItemInventario {
    pub obj_id: u32,
    pub item_id: u32,
    pub quantidade: u64,
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
            mascara: def.map(|d| d.mascara).unwrap_or(0),
            slot: def.map(|d| d.slot).unwrap_or(Slot::Nenhum),
            tecido: def.map(|d| d.tecido).unwrap_or(false),
        }
    }

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
            Slot::Escudo(bits) => Some((SLOT_ESCUDO, bits, 0, ESCUDO_LEN - 16)),
            Slot::Armadura(bits) => Some((SLOT_ARMADURA, bits, 0, 4)),
        } {
            buf[n] = SLOT_EQUIPADO;
            n += 1;
            u64le(buf, &mut n, 0);

            buf[n] = tipo;
            n += 1;
            u64le(buf, &mut n, principal);
            u64le(buf, &mut n, secundario);
            buf[n..n + extra].fill(0);
            n += extra;

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

        buf[n] = GERAL;
        n += 1;
        let geral = &mut buf[n..n + 33];
        geral.fill(0);
        geral[0..2].copy_from_slice(&self.mascara.to_le_bytes());
        geral[2..10].copy_from_slice(&self.quantidade.to_le_bytes());
        geral[31..33].copy_from_slice(&15u16.to_le_bytes());
        n + 33
    }
}
