//! Carregador de itens — lê `client_items.xml` do cliente oficial.
//!
//! Analisa slot, mascara de direitos, empilhabilidade e tipo de tecido de cada item.

use std::collections::HashMap;
use std::path::Path;
use super::xml_reader::load_catalog_campos;

/// Onde um item se equipa, no formato de bits que o cliente usa.
///
/// Sai do `equipment_slots` do catálogo do cliente. Os números foram conferidos contra a captura:
/// os itens que a personagem gravada usava chegam com exatamente estes bits no bloco de slot --
/// peitoral 8, calca 4096, ombreira 2048, luva 16, bota 32, colar 1024, cinto 65536.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    /// Não equipável: poção, comida, kinah, material.
    Nenhum,
    /// Arma. O bloco de slot é o `SLOTS_WEAPON`, com a mão principal e a secundária.
    ///
    /// `duas_maos` sai do `equipment_slots` do catálogo: `main` é arma de duas mãos -- arco,
    /// orbe, cajado, lança --, `main_or_sub` é de uma mão. A diferença importa no pacote: o
    /// registro de arma de duas mãos abre com um bloco de item composto, e o de uma mão não.
    Arma { principal: u64, secundario: u64, duas_maos: bool },
    /// Escudo. Tem bloco próprio, de 20 bytes, e vai sempre na mão secundária.
    Escudo(u64),
    /// Peça de armadura de corpo -- peitoral, calca, luva, bota, ombreira.
    Armadura(u64),
    /// Acessório: elmo, colar, brinco, anel, cinto, asa.
    Acessorio { principal: u64, secundario: u64 },
}

/// Definição de item lida do catálogo oficial do cliente.
#[derive(Debug, Clone)]
pub struct ItemDef {
    pub id: u32,
    pub name: String,
    /// Máscara de direitos do item -- vender, trocar, guardar no armazém, empilhar.
    pub mascara: u16,
    pub slot: Slot,
    /// O byte que fecha o registro de item. Vale 1 nas peças de armadura de corpo e 0 no resto.
    pub tecido: bool,
}

/// Os slots de armadura de corpo, que são os que o cliente marca como "tecido".
pub const SLOTS_DE_CORPO: [&str; 5] = ["torso", "leg", "glove", "foot", "shoulder"];

/// Traduz o `equipment_slots` do catálogo para os bits que o pacote de item leva.
///
/// Os nomes saem do XML do cliente; os bits, do `ItemSlot` do Aion-Lightning, conferidos um a um
/// contra os itens que a personagem da captura usava.
pub fn slot_do_catalogo(texto: &str) -> Slot {
    const MAO_PRINCIPAL: u64 = 1;
    const MAO_SECUNDARIA: u64 = 1 << 1;

    let bit = |n: u32| 1u64 << n;
    match texto {
        "main_or_sub" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: false,
        },
        "main" => Slot::Arma {
            principal: MAO_PRINCIPAL,
            secundario: MAO_SECUNDARIA,
            duas_maos: true,
        },
        "sub" => Slot::Escudo(MAO_SECUNDARIA),
        "torso" => Slot::Armadura(bit(3)),
        "glove" => Slot::Armadura(bit(4)),
        "foot" => Slot::Armadura(bit(5)),
        "shoulder" => Slot::Armadura(bit(11)),
        "leg" => Slot::Armadura(bit(12)),
        "head" => Slot::Acessorio { principal: bit(2), secundario: 0 },
        "right_or_left_ear" => Slot::Acessorio { principal: bit(6), secundario: bit(7) },
        "right_or_left_finger" => Slot::Acessorio { principal: bit(8), secundario: bit(9) },
        "neck" => Slot::Acessorio { principal: bit(10), secundario: 0 },
        "wing" => Slot::Acessorio { principal: bit(15), secundario: 0 },
        "waist" => Slot::Acessorio { principal: bit(16), secundario: 0 },
        _ => Slot::Nenhum,
    }
}

/// A máscara de direitos que vai no bloco `GENERAL_INFO` de cada item.
///
/// Foi ajustada contra a captura: das 119 máscaras que o servidor oficial mandou, esta conta
/// reproduz 108 byte a byte. As 11 que sobram são todas item de quest, e diferem só no bit 10.
pub fn mascara_do_item(campos: &HashMap<Vec<u8>, String>, slot_texto: &str) -> u16 {
    let ligado = |nome: &[u8]| {
        campos
            .get(nome)
            .map(|v| v.trim().eq_ignore_ascii_case("true"))
            .unwrap_or(false)
    };
    let empilhavel = campos
        .get(b"max_stack_count".as_slice())
        .and_then(|v| v.trim().parse::<u32>().ok())
        .map(|n| n != 1)
        .unwrap_or(false);

    let mut m: u16 = 0;
    if ligado(b"lore") { m |= 1 << 0; }
    if ligado(b"can_exchange") { m |= (1 << 1) | (1 << 9); }
    if ligado(b"can_sell_to_npc") { m |= 1 << 2; }
    if ligado(b"can_deposit_to_character_warehouse") { m |= 1 << 3; }
    if ligado(b"can_deposit_to_account_warehouse") { m |= 1 << 4; }
    if ligado(b"breakable") { m |= 1 << 5; }
    if ligado(b"soul_bind") { m |= 1 << 6; }
    if !matches!(slot_texto, "main" | "main_or_sub" | "sub")
        && !SLOTS_DE_CORPO.contains(&slot_texto)
    {
        m |= 1 << 8;
    }
    if ligado(b"can_composite_weapon") { m |= 1 << 11; }
    if empilhavel { m |= 1 << 13; }
    if matches!(slot_texto, "none" | "right_or_left_finger" | "waist") { m |= 1 << 14; }
    if ligado(b"cannot_extraction") { m |= 1 << 15; }
    m
}

/// Carrega todos os itens do `client_items.xml`.
///
/// Retorna um `HashMap<item_id, ItemDef>`.
pub fn load_items(path: &Path) -> Result<HashMap<u32, ItemDef>, String> {
    const CAMPOS: [&[u8]; 12] = [
        b"name",
        b"equipment_slots",
        b"max_stack_count",
        b"lore",
        b"can_exchange",
        b"can_sell_to_npc",
        b"can_deposit_to_character_warehouse",
        b"can_deposit_to_account_warehouse",
        b"breakable",
        b"soul_bind",
        b"can_composite_weapon",
        b"cannot_extraction",
    ];

    let registros = load_catalog_campos(path, b"client_item", &CAMPOS)?;
    Ok(registros
        .into_iter()
        .map(|(id, campos)| {
            let slot_texto = campos
                .get(b"equipment_slots".as_slice())
                .map(|s| s.trim().to_string())
                .unwrap_or_else(|| "none".to_string());
            let def = ItemDef {
                id,
                name: campos.get(b"name".as_slice()).cloned().unwrap_or_default(),
                mascara: mascara_do_item(&campos, &slot_texto),
                slot: slot_do_catalogo(&slot_texto),
                tecido: SLOTS_DE_CORPO.contains(&slot_texto.as_str()),
            };
            (id, def)
        })
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn campos(pares: &[(&str, &str)]) -> HashMap<Vec<u8>, String> {
        pares.iter()
            .map(|(k, v)| (k.as_bytes().to_vec(), v.to_string()))
            .collect()
    }

    /// A máscara calculada bate com a que o servidor oficial mandou.
    #[test]
    fn mascara_reproduz_a_captura() {
        let pocao = campos(&[
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("breakable", "TRUE"),
            ("max_stack_count", "100"),
        ]);
        assert_eq!(mascara_do_item(&pocao, "none"), 0x612C, "item 164000224");

        let peitoral = campos(&[
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("breakable", "TRUE"),
            ("cannot_extraction", "TRUE"),
            ("max_stack_count", "1"),
        ]);
        assert_eq!(mascara_do_item(&peitoral, "torso"), 0x802C, "item 110101547");

        let kinah = campos(&[
            ("can_exchange", "TRUE"),
            ("can_sell_to_npc", "TRUE"),
            ("can_deposit_to_character_warehouse", "TRUE"),
            ("can_deposit_to_account_warehouse", "TRUE"),
            ("max_stack_count", "0"),
        ]);
        assert_eq!(mascara_do_item(&kinah, "none"), 0x631E, "item 182400001");
    }

    /// Os bits de slot são os que a captura mostra nos itens que a personagem usava.
    #[test]
    fn slots_batem_com_a_captura() {
        assert!(matches!(slot_do_catalogo("torso"), Slot::Armadura(8)));
        assert!(matches!(slot_do_catalogo("leg"), Slot::Armadura(4096)));
        assert!(matches!(slot_do_catalogo("shoulder"), Slot::Armadura(2048)));
        assert!(matches!(
            slot_do_catalogo("neck"),
            Slot::Acessorio { principal: 1024, .. }
        ));
        assert!(matches!(
            slot_do_catalogo("waist"),
            Slot::Acessorio { principal: 65536, .. }
        ));
        assert!(matches!(
            slot_do_catalogo("main_or_sub"),
            Slot::Arma { principal: 1, secundario: 2, duas_maos: false }
        ));
        assert!(matches!(
            slot_do_catalogo("main"),
            Slot::Arma { duas_maos: true, .. }
        ));
        assert!(matches!(slot_do_catalogo("sub"), Slot::Escudo(2)));
        assert!(matches!(slot_do_catalogo("none"), Slot::Nenhum));
    }
}
