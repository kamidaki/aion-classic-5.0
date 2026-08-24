# PLAN-08: Sistema de Correio (C_MAIL_READ 0x086, C_MAIL_POSTMAN 0x0A2, S_MAIL 0x0A0)

**Status:** `[x]`  
**Prioridade:** MÉDIA — 36 pacotes capturados cobrindo 4 variantes de carta.

---

## Contexto da Captura Wireshark

4 variantes testadas: carta com item, com Kinah, sem anexo, e carta vazia. 25 ocorrências de S_MAIL.

### S_MAIL (0x0A0) — lista de cartas na caixa de entrada

```
[u16 letter_count]
-- para cada carta:
  [u32 letter_id]
  [u32 sender_id]           — ID de personagem do remetente (0 se sistema)
  [u16 sender_name_len]
  [u8* sender_name]         — UTF-16LE, sender_name_len bytes
  [u16 title_len]
  [u8* title]               — UTF-16LE
  [u8  letter_type]         — 0=normal, 1=express (mensageiro NPC), 2=sistema
  [u8  is_read]             — 0 ou 1
  [u8  has_attachment]      — 0=sem anexo, 1=tem item, 2=tem kinah, 3=ambos
  -- se has_attachment & 1:
    [u32 item_template_id]
    [u32 item_quantity]
  -- se has_attachment & 2:
    [u64 kinah_amount]
  [u64 timestamp]           — unix timestamp
```

### C_MAIL_READ (0x086) — cliente abre/lê uma carta

```
[u32 letter_id]
[u8  action]    — 0=abrir (marcar lida), 1=coletar item, 2=coletar kinah, 3=deletar
```

### C_MAIL_POSTMAN (0x0A2) — cliente envia uma carta

```
[u16 recipient_name_len]
[u8* recipient_name]       — UTF-16LE
[u16 title_len]
[u8* title]               — UTF-16LE
[u16 body_len]
[u8* body]                — UTF-16LE
[u8  letter_type]         — 0=normal, 1=express
[u32 item_unique_id]      — 0 se sem item
[u32 item_quantity]       — 0 se sem item
[u64 kinah_amount]        — 0 se sem kinah
```

---

## Estado Atual do Código

**`game-server/src/game/mail.rs`:** Estruturas `Letter`, `Mailbox` definidas.  
**Problema crítico:** Nenhum handler de C_MAIL_READ ou C_MAIL_POSTMAN em `client.rs`. S_MAIL (0x0A0) não está em `server.rs`. A `Mailbox` não é integrada ao `Character` nem ao `State`.

---

## Tarefas

### 1. Adicionar handlers em client.rs

```rust
define_messages!(
    // ...
    (MAIL_READ, MailRead, 0x86),
    (MAIL_POSTMAN, MailPostman, 0xA2),
);

#[derive(Debug, Clone)]
pub struct MailRead {
    pub letter_id: u32,
    pub action: u8,
}

#[derive(Debug, Clone)]
pub struct MailPostman {
    pub recipient_name: String,
    pub title: String,
    pub body: String,
    pub letter_type: u8,
    pub item_unique_id: u32,
    pub item_quantity: u32,
    pub kinah_amount: u64,
}

impl Deserialise for MailPostman {
    fn deserialise(buf: &[u8]) -> Self {
        let mut ptr = 0;
        let rname_len = consume_le_bytes!(ptr, buf, u16) as usize;
        let recipient_name = String::from_utf16_lossy(
            &buf[ptr..ptr+rname_len].chunks(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .collect::<Vec<_>>()
        );
        ptr += rname_len;
        // Repetir para title e body...
        let title_len = consume_le_bytes!(ptr, buf, u16) as usize;
        let title = decode_utf16le(&buf[ptr..ptr+title_len]);
        ptr += title_len;
        let body_len = consume_le_bytes!(ptr, buf, u16) as usize;
        let body = decode_utf16le(&buf[ptr..ptr+body_len]);
        ptr += body_len;
        let letter_type = buf[ptr]; ptr += 1;
        let item_unique_id = consume_le_bytes!(ptr, buf, u32);
        let item_quantity = consume_le_bytes!(ptr, buf, u32);
        let kinah_amount = consume_le_bytes!(ptr, buf, u64);
        Self { recipient_name, title, body, letter_type, item_unique_id, item_quantity, kinah_amount }
    }
}
```

### 2. Adicionar S_MAIL (0x0A0) em server.rs

```rust
const MAIL: u16 = 0x00A0;

pub struct MailLetterSummary {
    pub letter_id: u32,
    pub sender_id: u32,
    pub sender_name: String,
    pub title: String,
    pub letter_type: u8,
    pub is_read: u8,
    pub has_attachment: u8,  // bitmask: 0x01=item, 0x02=kinah
    pub item_template_id: u32,
    pub item_quantity: u32,
    pub kinah_amount: u64,
    pub timestamp: u64,
}

pub struct Mail {
    pub letters: Vec<MailLetterSummary>,
}

impl Serialise for Mail {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, MAIL, &mut ptr);
        to_le_bytes!(ptr, buf, self.letters.len() as u16);
        for letter in &self.letters {
            to_le_bytes!(ptr, buf, letter.letter_id);
            to_le_bytes!(ptr, buf, letter.sender_id);
            let name_utf16 = encode_utf16le(&letter.sender_name);
            to_le_bytes!(ptr, buf, name_utf16.len() as u16);
            copy_bytes!(ptr, buf, name_utf16);
            let title_utf16 = encode_utf16le(&letter.title);
            to_le_bytes!(ptr, buf, title_utf16.len() as u16);
            copy_bytes!(ptr, buf, title_utf16);
            buf[ptr] = letter.letter_type; ptr += 1;
            buf[ptr] = letter.is_read; ptr += 1;
            buf[ptr] = letter.has_attachment; ptr += 1;
            if letter.has_attachment & 0x01 != 0 {
                to_le_bytes!(ptr, buf, letter.item_template_id);
                to_le_bytes!(ptr, buf, letter.item_quantity);
            }
            if letter.has_attachment & 0x02 != 0 {
                to_le_bytes!(ptr, buf, letter.kinah_amount);
            }
            to_le_bytes!(ptr, buf, letter.timestamp);
        }
        prepend_length(buf, ptr)
    }
}
```

### 3. Implementar handlers no state.rs

**MailRead:**
- action=0: marcar como lida, não emite resposta (ou re-envia S_MAIL atualizado).
- action=1: remover item da carta e adicionar ao inventário do jogador, emitir S_MAIL atualizado.
- action=2: adicionar kinah ao jogador, emitir S_MAIL atualizado.
- action=3: deletar carta.

**MailPostman:**
1. Verificar se o recipient existe no banco.
2. Cobrar custo de envio (normal: 10 kinah, express: 500 kinah).
3. Se tem item: remover do inventário do remetente.
4. Criar Letter no Mailbox do destinatário.
5. Se destinatário está online: emitir S_MAIL atualizado para ele.

### 4. Emitir S_MAIL no spawn inicial

Após C_LEVEL_READY, enviar S_MAIL com as cartas do personagem:
```rust
messages.push_direct(client_id, s::Message::Mail(char.build_mail_packet()));
```

### 5. Tabela no banco de dados

```sql
CREATE TABLE IF NOT EXISTS character_mail (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id     INTEGER NOT NULL,
    sender_id        INTEGER NOT NULL DEFAULT 0,
    sender_name      TEXT NOT NULL DEFAULT 'System',
    title            TEXT NOT NULL DEFAULT '',
    body             TEXT NOT NULL DEFAULT '',
    letter_type      INTEGER NOT NULL DEFAULT 0,
    is_read          INTEGER NOT NULL DEFAULT 0,
    item_template_id INTEGER NOT NULL DEFAULT 0,
    item_quantity    INTEGER NOT NULL DEFAULT 0,
    kinah_amount     INTEGER NOT NULL DEFAULT 0,
    timestamp        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (recipient_id) REFERENCES players(id)
);
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/client.rs` | Adicionar `MailRead` (0x86), `MailPostman` (0xA2) |
| `game-server/src/game/message/server.rs` | Adicionar `Mail` (0xA0) |
| `game-server/src/game/state.rs` | Handlers de MailRead e MailPostman |
| `game-server/src/game/mail.rs` | Conectar Mailbox ao Character, métodos de coleta/deleção |
| `game-server/src/db.rs` | CRUD para character_mail |

---

## Verificação

- Login → S_MAIL lista todas as cartas não lidas.
- Abrir carta → marcada como lida.
- Coletar item/kinah → item entra no inventário / kinah somado.
- Enviar carta → destinatário online recebe S_MAIL atualizado.
- Carta express (mensageiro NPC) → tipo correto no campo letter_type.

---

**Commit:** `git add -A && git commit -m "PLAN-08: Sistema de correio — S_MAIL, C_MAIL_READ, C_MAIL_POSTMAN com 4 variantes (item/kinah/sem anexo/vazio)"`
