# PLAN-06: Loja NPC e Buyback (C_BUY_SELL 0x033, S_STORE_SALE_INFO 0x0FD, S_USER_SELL_HISTORY_LIST 0x0A6)

**Status:** `[ ]`  
**Prioridade:** MÉDIA-ALTA — 35 pacotes capturados: compra, venda e buyback.

---

## Contexto da Captura Wireshark

### C_BUY_SELL (0x033) — compra ou venda na loja NPC

```
[u32 npc_object_id]
[u32 item_unique_id]   — 0 para compra, ID do item para venda
[u32 item_template_id] — ID do template para compra
[u32 quantity]
[u8  action]           — 0=comprar, 1=vender
```

### S_STORE_SALE_INFO (0x0FD) — resposta do servidor após transação

```
[u8  result]           — 0=sucesso, 1=kinah insuficiente, 2=inventário cheio, 3=item não vendável
[u32 item_unique_id]
[u32 item_template_id]
[u32 quantity]
[u64 price_paid]       — kinah gasto/recebido
[u64 kinah_current]    — kinah atual após transação
```

### S_USER_SELL_HISTORY_LIST (0x0A6) — lista de itens vendidos recentemente (Buyback)

```
[u8  count]
-- para cada item (max 20):
  [u32 item_unique_id]     — ID temporário para recompra
  [u32 item_template_id]
  [u32 quantity]
  [u64 buyback_price]      — preço para recomprar (=preço original de venda)
  [u64 sell_timestamp]     — quando foi vendido (unix timestamp)
```

---

## Estado Atual do Código

**`client.rs`:** Nenhum handler para `C_BUY_SELL` (0x033). Cai no `WARNING: not implemented`.  
**`server.rs`:** Nenhum `StoreSaleInfo` ou `UserSellHistoryList`.  
**`game-server/src/game/trade.rs`:** Tem estrutura de `TradeSession` mas é para trade P2P, não NPC.

---

## Tarefas

### 1. Adicionar C_BUY_SELL (0x033) em client.rs

```rust
define_messages!(
    // ...
    (BUY_SELL, BuySell, 0x33),
    (SELL_HISTORY, SellHistory, 0x0A6_CLIENT_OPCODE), // verificar opcode CM real
);

#[derive(Debug, Clone)]
pub struct BuySell {
    pub npc_object_id: u32,
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub action: u8,  // 0=comprar, 1=vender
}

impl Deserialise for BuySell {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        Self {
            npc_object_id:    consume_le_bytes!(ptr, buf, u32),
            item_unique_id:   consume_le_bytes!(ptr, buf, u32),
            item_template_id: consume_le_bytes!(ptr, buf, u32),
            quantity:         consume_le_bytes!(ptr, buf, u32),
            action:           buf[ptr],
        }
    }
}
```

### 2. Adicionar S_STORE_SALE_INFO (0x0FD) em server.rs

```rust
const STORE_SALE_INFO: u16 = 0x00FD;

pub struct StoreSaleInfo {
    pub result: u8,
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub price_paid: u64,
    pub kinah_current: u64,
}

impl Serialise for StoreSaleInfo {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, STORE_SALE_INFO, &mut ptr);
        buf[ptr] = self.result; ptr += 1;
        to_le_bytes!(ptr, buf, self.item_unique_id);
        to_le_bytes!(ptr, buf, self.item_template_id);
        to_le_bytes!(ptr, buf, self.quantity);
        to_le_bytes!(ptr, buf, self.price_paid);
        to_le_bytes!(ptr, buf, self.kinah_current);
        prepend_length(buf, ptr)
    }
}
```

### 3. Adicionar S_USER_SELL_HISTORY_LIST (0x0A6) em server.rs

```rust
const USER_SELL_HISTORY_LIST: u16 = 0x00A6;

pub struct SellHistoryEntry {
    pub item_unique_id: u32,
    pub item_template_id: u32,
    pub quantity: u32,
    pub buyback_price: u64,
    pub sell_timestamp: u64,
}

pub struct UserSellHistoryList {
    pub entries: Vec<SellHistoryEntry>,
}
```

### 4. Implementar lógica de compra/venda no state.rs

```rust
// Handler de BuySell no respond():
match update.message() {
    c::Message::BuySell(msg) => {
        let char = self.characters.get_mut(&update.character_id())?;
        match msg.action {
            0 => {
                // Compra: verificar kinah, verificar inventário, adicionar item
                let item_def = self.game_data.items.get(&msg.item_template_id)?;
                let price = item_def.buy_price * msg.quantity as u64;
                if char.kinah() < price {
                    messages.push_direct(update.client_id(), ServerUpdate::new(
                        s::Message::StoreSaleInfo(s::StoreSaleInfo {
                            result: 1, // kinah insuficiente
                            ..Default::default()
                        })
                    ));
                } else {
                    char.remove_kinah(price);
                    let unique_id = char.add_item(msg.item_template_id, msg.quantity);
                    messages.push_direct(update.client_id(), ServerUpdate::new(
                        s::Message::StoreSaleInfo(s::StoreSaleInfo {
                            result: 0,
                            item_unique_id: unique_id,
                            item_template_id: msg.item_template_id,
                            quantity: msg.quantity,
                            price_paid: price,
                            kinah_current: char.kinah(),
                        })
                    ));
                    // Atualizar inventário no cliente
                    // Emitir SM_INVENTORY_INFO atualizado
                }
            }
            1 => {
                // Venda: remover item, dar kinah, registrar no histórico
                let sell_price = char.sell_item(msg.item_unique_id, msg.quantity);
                char.buyback_history.push(SellHistoryEntry { ... });
                messages.push_direct(update.client_id(), ServerUpdate::new(
                    s::Message::StoreSaleInfo(s::StoreSaleInfo {
                        result: 0,
                        item_unique_id: msg.item_unique_id,
                        item_template_id: msg.item_template_id,
                        quantity: msg.quantity,
                        price_paid: sell_price,
                        kinah_current: char.kinah(),
                    })
                ));
            }
            _ => {}
        }
    }
}
```

### 5. Adicionar template de loja NPC nos dados do jogo

Para cada NPC vendedor, definir lista de items disponíveis com preços.  
Arquivo: `game-server/src/game/data/npc.rs`

```rust
pub struct NpcShopItem {
    pub item_template_id: u32,
    pub infinite_stock: bool,
    pub stock: u32,          // 0 = infinito
    pub buy_price: u64,
}

pub struct NpcTemplate {
    // ... existente ...
    pub shop_items: Vec<NpcShopItem>,
}
```

### 6. Abrir loja via SM_DIALOG_WINDOW antes de BuySell

Quando o cliente faz `C_SHOW_DIALOG` em NPC vendedor:
- `SM_DIALOG_WINDOW { dialog_id: 2 }` → abre janela de loja
- Em seguida enviar a lista de items da loja (formato a verificar na captura — pode ser inline no dialog ou pacote separado)

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Adicionar `BuySell` (0x33) |
| `game-server/src/game/message/server.rs` | Adicionar `StoreSaleInfo` (0xFD), `UserSellHistoryList` (0xA6) |
| `game-server/src/game/state.rs` | Handler de `BuySell` no `respond()` |
| `game-server/src/game/data/npc.rs` | Adicionar `NpcShopItem` e `shop_items` no template |
| `game-server/src/game/character.rs` | Métodos `add_item()`, `sell_item()`, buyback_history |

---

## Verificação

- Abrir loja → dialog_id=2 abre lista de itens.
- Comprar item → kinah diminui, item aparece no inventário.
- Vender item → kinah aumenta, item some do inventário.
- Aba de Buyback → lista de até 20 itens vendidos recentemente com preço de recompra.

---

**Commit:** `git add -A && git commit -m "PLAN-06: Loja NPC funcional — C_BUY_SELL, S_STORE_SALE_INFO, buyback S_USER_SELL_HISTORY_LIST"`
