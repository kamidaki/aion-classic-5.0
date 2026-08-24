# PLAN-12: Chat Channels — SM_MESSAGE 0x18, Whisper, Canais Regionais, Anti-Flood

**Status:** `[x]`  
**Prioridade:** MÉDIA — base do sistema de comunicação do jogo.

---

## Contexto da Captura Wireshark

O chat server roda na porta 10241. O game server também processa chat de canal público.

### C_CHAT_MESSAGE_PUBLIC (0x1B) — mensagem pública do cliente

```
[u8  channel_type]    — ver enum abaixo
[u16 message_len]
[u8* message]         — UTF-16LE
```

**Enum de canais (verificado na captura):**
```
0  = Normal (zona local)
1  = Shout (grito — área maior)
2  = Whisper (privado — ver C_CHAT_MESSAGE_WHISPER)
3  = Group (grupo)
4  = Alliance
5  = Legion
6  = World (LFG / global)
7  = Trade
8  = System
9  = Command (GM)
```

### C_CHAT_MESSAGE_WHISPER (0x1C) — susurro privado

```
[u16 target_name_len]
[u8* target_name]     — UTF-16LE
[u16 message_len]
[u8* message]         — UTF-16LE
```

### SM_MESSAGE (0x18) — entrega de mensagem de chat

```
[u32 sender_id]
[u16 sender_name_len]
[u8* sender_name]     — UTF-16LE
[u8  channel_type]
[u16 message_len]
[u8* message]         — UTF-16LE
[u32 timestamp]       — unix timestamp
```

### SM_SYSTEM_MESSAGE (0x19) — mensagem de sistema

```
[u32 message_code]    — código pré-traduzido pelo cliente
[u32 param1]          — parâmetro variável (nome, ID, etc)
```

---

## Estado Atual do Código

**`client.rs`:** `ChatMessagePublic` (0x1B) implementado — repassa para state via tx.  
**`server.rs`:** Tem `Message` (0x18 = `MESSAGE_CODE`) mas esse é o de sistema (0x19). O SM_MESSAGE real (0x18) não está mapeado corretamente — há confusão entre os opcodes.  
**`chat-server/src/main.rs`:** Servidor de chat existe mas só implementa conexão básica — canais globais não redirecionam para o game-server.

**Problema crítico de opcode:** O atual código tem `MESSAGE_CODE: u16 = 0x0019` mas o enum chama de `MessageCode`. O SM_MESSAGE real de chat é 0x0018. Verificar se há sobreposição.

---

## Tarefas

### 1. Separar SM_MESSAGE (0x18) de SM_SYSTEM_MESSAGE (0x19) em server.rs

```rust
// SM_MESSAGE: entrega de chat
const SM_CHAT_MESSAGE: u16 = 0x0018;

pub struct ChatMessage {
    pub sender_id: u32,
    pub sender_name: String,
    pub channel_type: u8,
    pub message: String,
    pub timestamp: u32,
}

impl Serialise for ChatMessage {
    fn serialise(&self, buf: &mut [u8]) -> usize {
        let mut ptr = 0;
        write_header(buf, SM_CHAT_MESSAGE, &mut ptr);
        to_le_bytes!(ptr, buf, self.sender_id);
        let name_utf16 = encode_utf16le(&self.sender_name);
        to_le_bytes!(ptr, buf, name_utf16.len() as u16);
        copy_bytes!(ptr, buf, name_utf16);
        buf[ptr] = self.channel_type; ptr += 1;
        let msg_utf16 = encode_utf16le(&self.message);
        to_le_bytes!(ptr, buf, msg_utf16.len() as u16);
        copy_bytes!(ptr, buf, msg_utf16);
        to_le_bytes!(ptr, buf, self.timestamp);
        prepend_length(buf, ptr)
    }
}
```

### 2. Adicionar handler C_CHAT_MESSAGE_WHISPER (0x1C)

```rust
define_messages!(
    (CHAT_MESSAGE_WHISPER, ChatMessageWhisper, 0x1C),
);

#[derive(Debug, Clone)]
pub struct ChatMessageWhisper {
    pub target_name: String,
    pub message: String,
}

impl ChatMessageWhisper {
    pub fn handle(&self, tx: &Sender<ClientUpdate>, session: &mut Account) -> Vec<s::Message> {
        tx.send(session.send(Message::ChatMessageWhisper(self.clone()))).unwrap();
        vec![]
    }
}
```

### 3. Implementar roteamento de chat no state.rs

```rust
c::Message::ChatMessagePublic(msg) => {
    let char = self.characters.get(&update.character_id())?;
    let chat_msg = s::Message::ChatMessage(s::ChatMessage {
        sender_id: char.id(),
        sender_name: char.name().to_string(),
        channel_type: msg.channel_type,
        message: msg.message.clone(),
        timestamp: current_timestamp(),
    });

    match msg.channel_type {
        0 => {
            // Normal: só quem está no raio de chat (~50m)
            let receiver_ids = self.players_in_radius(char.location(), 50.0);
            for rid in receiver_ids {
                messages.push_direct(rid, ServerUpdate::new(chat_msg.clone()));
            }
        }
        1 => {
            // Shout: raio maior (~500m)
            let receiver_ids = self.players_in_radius(char.location(), 500.0);
            for rid in receiver_ids { messages.push_direct(rid, ServerUpdate::new(chat_msg.clone())); }
        }
        6 | 7 => {
            // World/Trade: broadcast global
            messages.broadcast.push(ServerUpdate::new(chat_msg));
        }
        3 => {
            // Group: só membros do grupo
            if let Some(group_id) = self.social.party.group_of(char.id()) {
                // Enviar para cada membro
            }
        }
        5 => {
            // Legion: só membros da legião
        }
        _ => {}
    }
}
```

### 4. Implementar whisper no state.rs

```rust
c::Message::ChatMessageWhisper(msg) => {
    let char = self.characters.get(&update.character_id())?;
    // Encontrar jogador alvo online
    if let Some(target_client_id) = self.find_player_by_name(&msg.target_name) {
        let whisper = s::ChatMessage {
            sender_id: char.id(),
            sender_name: char.name().to_string(),
            channel_type: 2, // Whisper
            message: msg.message.clone(),
            timestamp: current_timestamp(),
        };
        messages.push_direct(target_client_id, ServerUpdate::new(
            s::Message::ChatMessage(whisper)
        ));
    } else {
        // Emitir SM_SYSTEM_MESSAGE "jogador offline ou inexistente"
        messages.push_direct(update.client_id(), ServerUpdate::new(
            s::Message::MessageCode(s::MessageCode { code: 900010, param: 0 })
        ));
    }
}
```

### 5. Implementar anti-flood

```rust
// No struct State:
chat_timestamps: HashMap<u32, VecDeque<Instant>>, // char_id -> últimas mensagens

fn check_flood(&mut self, char_id: u32) -> bool {
    let timestamps = self.chat_timestamps.entry(char_id).or_default();
    let now = Instant::now();
    // Remover timestamps mais antigos que 5 segundos
    timestamps.retain(|t| now.duration_since(*t) < Duration::from_secs(5));
    if timestamps.len() >= 5 { return false; } // flood detectado
    timestamps.push_back(now);
    true
}
```

### 6. Comandos GM no chat (.spawn, .teleport, .goto, .additem)

O `social.rs` já tem `GmCommand::parse()`. Conectar no handler de ChatMessagePublic:

```rust
if let Some(cmd) = GmCommand::parse(&msg.message) {
    // Verificar se o jogador tem permissão de GM
    if char.access_level() >= 100 {
        self.execute_gm_command(cmd, char.id(), update.client_id(), &mut messages);
    }
}
```

---

## Arquivos a Modificar

| Arquivo | Ação |
|---------|------|
| `game-server/src/game/message/server.rs` | Separar SM_MESSAGE (0x18) de SM_SYSTEM_MESSAGE (0x19), adicionar `ChatMessage` |
| `game-server/src/game/message/client.rs` | Adicionar `ChatMessageWhisper` (0x1C) |
| `game-server/src/game/state.rs` | Roteamento de chat por canal, whisper, anti-flood, GM commands |
| `game-server/src/game/social.rs` | Integrar GmCommand executor |
| `chat-server/src/main.rs` | Conectar canais globais (LFG, Trade) ao game-server via channel ou shared state |

---

## Verificação

- Mensagem normal → só jogadores no raio recebem.
- Shout → raio maior.
- World/Trade → todos os online.
- Whisper → só o alvo recebe.
- Flood → mensagem bloqueada após 5 em 5 segundos.
- Comando GM (.teleport) → funcional para acesso_level >= 100.

---

**Commit:** `git add -A && git commit -m "PLAN-12: Chat — SM_MESSAGE corrigido 0x18, whisper, roteamento por canal, anti-flood, GM commands"`
