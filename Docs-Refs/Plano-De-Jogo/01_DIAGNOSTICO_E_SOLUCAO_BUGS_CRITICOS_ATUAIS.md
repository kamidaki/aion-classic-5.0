# Plano de Jogo - Diagnóstico e Solução dos Bugs Críticos Atuais

Este documento disseca cada um dos problemas detectados durante os testes reais no cliente de jogo e fornece a solução técnica detalhada com estruturas de pacotes, offsets, opcodes e código Rust compatível.

---

## 1. Problema: Personagem Invisível e Textura Crashada (Corpo Vermelho)

### Causa Raiz:
No AION 4.5/Classic, quando o personagem entra no mundo via `SM_ENTER_WORLD_CHECK` (0x00D) e é spawnado via `SM_PLAYER_SPAWN` / `SM_PLAYER_INFO` (0x040) ou `SM_PUT_USER` (0x041), o cliente espera uma estrutura binária de **Aparência de 140 bytes** (`PlayerAppearance`) perfeitamente formatada.
Se o tamanho ou os offsets dos meshes de cabeça, pele, cor dos olhos, formato do rosto e proporções corporais contiverem valores fora da faixa válida (como bytes nulos ou desalinhados), o motor gráfico CryEngine não consegue instanciar o modelo 3D e renderiza o shader padrão de fallback (o modelo vermelho/invisível).

### Formato Exato do Bloco de 140 Bytes de Aparência:

```
Offset  Tamanho   Tipo       Campo
-------------------------------------------------------------
00..03  4 bytes   u32 (LE)   voice_id (Voz do personagem)
04..07  4 bytes   u32 (LE)   skin_color (RGB packed: 0x00RRGGBB)
08..11  4 bytes   u32 (LE)   hair_color (RGB packed)
12..15  4 bytes   u32 (LE)   eye_color (RGB packed)
16..19  4 bytes   u32 (LE)   lip_color (RGB packed)
20..23  4 bytes   u32 (LE)   face_shape (Índice da malha do rosto)
24..27  4 bytes   u32 (LE)   hair_shape (Índice do modelo de cabelo)
28..31  4 bytes   u32 (LE)   decoration (Tatuagem / Pintura)
32..35  4 bytes   u32 (LE)   tattoo (Tatuagem de corpo)
36..39  4 bytes   u32 (LE)   face_contour (Contorno facial)
40..43  4 bytes   u32 (LE)   expression (Expressão facial)
44..47  4 bytes   u32 (LE)   pupil_shape (Formato da pupila)
48..51  4 bytes   u32 (LE)   pupil_color (Cor da pupila)
52..55  4 bytes   u32 (LE)   eye_color2 (Cor do olho esquerdo)
56..59  4 bytes   u32 (LE)   race_id (0 = Elyos, 1 = Asmodian)
60..63  4 bytes   u32 (LE)   class_id (1 = Warrior, 2 = Scout, ..., 11 = Luminess)
64..67  4 bytes   u32 (LE)   gender_id (0 = Male, 1 = Female)
68..139 72 bytes  [f32/u8]   sliders de proporção corporal (altura, ombros, torso, pernas, etc.)
```

### Solução em Rust (`game-server/src/game/message/lista_personagens.rs` e `character.rs`):
1. Ao receber o pacote `CM_CREATE_CHARACTER` (0x027), extrair os 140 bytes de aparência enviados diretamente pelo cliente e gravá-los no banco na coluna `aparencia BLOB` de `characters`.
2. Ao emitir `SM_PLAYER_INFO` e `SM_ENTER_WORLD_CHECK`, injetar este array exato de 140 bytes no payload de spawn.
3. Se o personagem foi criado sem aparência, usar o molde base da raça/classe extraído da captura oficial Wireshark.

---

## 2. Problema: Câmera Atolada no Chão e Coordenadas Iniciais / Altitude Z

### Causa Raiz:
1. Ao nascer pela primeira vez (mapa de academia ou tutorial), a coordenada Z estava com valor incorreto (ex: `Z = 177.05` em locais onde o piso verdadeiro é `Z = 127.04`).
2. O cliente precisa receber o pacote `SM_REQUEST_TELEPORT` (Opcode 0x014) ou `SM_ENTER_WORLD_CHECK` (Opcode 0x00D) que trava a câmera no player e atualiza a altura do terreno.
3. Como demonstrado na captura oficial de Wireshark (`Some informations about packets.txt`):
   * O pacote `SM_REQUEST_TELEPORT` possui **22 bytes**:
     `[u8 tipo_teleporte][u32 map_id][u32 instance_id][f32 X][f32 Y][f32 Z][u8 heading]`
   * **Teleporte Oficial Kaisinel Academy (110070000)**: `X = 457.0, Y = 251.0, Z = 127.04, Heading = 0`
   * **Teleporte Oficial Sanctum (110010000)**: `X = 1352.14, Y = 1514.12, Z = 569.04, Heading = 0`
   * **Teleporte Oficial Pandaemonium (120010000)**: `X = 1649.59, Y = 1399.40, Z = 194.40, Heading = 0`

### Solução em Rust:
* Ajustar a tabela de nascimento inicial (`initial_spawns.csv`) para as coordenadas exatas capturadas no Wireshark.
* No handler de `EnterWorld`, enviar o `SM_REQUEST_TELEPORT` com a coordenada correta de piso caso a coordenada atual do banco esteja abaixo da malha.

---

## 3. Problema: Botão "Check Name" (Verificar Nickname) Não Responde

### Causa Raiz:
Na tela de criação de personagem, ao clicar em "Check Name", o cliente envia o pacote `CM_CHECK_NICKNAME` (Opcode 0x028 na 4.5 / 0x01E no Java 4.8).
Como o GameServer não estava tratando esse pacote no roteador de mensagens de rede, o pacote era descartado silenciosamente e o cliente ficava aguardando a resposta infinitamente com o botão inativo.

### Estrutura do Pacote `CM_CHECK_NICKNAME`:
```
Offset  Tamanho   Tipo       Campo
-------------------------------------------------------------
00..01  2 bytes   u16 (LE)   tamanho_do_pacote
02..03  2 bytes   u16 (LE)   opcode (0x0028)
04..05  2 bytes   u16 (LE)   tamanho_da_string_nome
06..NN  NN bytes  UTF-16LE   nome_do_personagem
```

### Estrutura da Resposta `SM_NICKNAME_CHECK_RESPONSE` (Opcode 0x0029):
```
Offset  Tamanho   Tipo       Campo
-------------------------------------------------------------
00..01  2 bytes   u16 (LE)   tamanho_do_pacote (ex: 7 bytes)
02..03  2 bytes   u16 (LE)   opcode (0x0029)
04      1 byte    u8         resultado (0 = Nome Disponível, 1 = Nome em Uso, 2 = Caracteres Inválidos, 3 = Nome Proibido)
05..06  2 bytes   u16 (LE)   codigo_de_erro_adicional (0x0000)
```

### Implementação em Rust:
```rust
pub fn handle_check_nickname(db: &Database, name: &str) -> Vec<u8> {
    let exists = db.verificar_nome_em_uso(name).unwrap_or(false);
    let mut packet = Vec::with_capacity(7);
    packet.extend_from_slice(&7u16.to_le_bytes());
    packet.extend_from_slice(&0x0029u16.to_le_bytes());
    let code: u8 = if exists { 1 } else { 0 };
    packet.push(code);
    packet.extend_from_slice(&0u16.to_le_bytes());
    packet
}
```

---

## 4. Problema: Botões de "Voltar / Character Select" e "Quit Game" Não Funcionam

### Causa Raiz:
1. **Voltar para Seleção de Personagens**: O cliente envia `CM_RECONNECT` (0x004A) solicitando um token de reconexão para retornar ao lobby de personagens sem fechar a conexão de socket. O servidor precisa responder com `SM_RECONNECT_KEY` (0x004B).
2. **Sair do Jogo (Quit)**: O cliente envia `CM_QUIT` (0x0048). O servidor precisa responder com `SM_QUIT_RESPONSE` (0x0049), confirmando o encerramento da sessão em 0 segundos (se em área segura) ou 10 segundos (se em área de combate).

### Formato de `SM_QUIT_RESPONSE` (Opcode 0x0049):
```
[u16 tamanho][u16 opcode 0x0049][u8 quit_type][u32 countdown_seconds]
quit_type: 1 = Sair para Área de Trabalho, 2 = Voltar para Seleção de Personagens
```

---

## 5. Problema: Mensagem "Usage Fee / Conta Reportada por Não Pagar Taxa de Uso"

### Causa Raiz:
No AION Classic Oficial (Gameforge), o sistema de **Siel's Energy (Energia de Siel)** exige que o servidor envie o status de assinatura da conta logo após a entrada no mundo via pacote `SM_ACCOUNT_PROPERTIES` (0x015A) ou `SM_SIEGE_LOCATION_INFO` (0x003A).
Quando o servidor não envia ou envia com valor `0` (Free Trial sem Siel), o cliente ativa o aviso de "não pagamento de taxa de uso" e bloqueia o gliding/coleta após alguns minutos.

### Solução em Rust:
No handshake de entrada no mundo, emitir `SM_ACCOUNT_PROPERTIES`:
* `membership_type = 1` (Siel's Aura Ativa / VIP Status)
* `toll_coins = 0`
* `siel_expiration_timestamp = 0x7FFFFFFF` (Permanente / Vitalício)
Isso desativa imediatamente a mensagem amarela e vermelha de restrição de uso.
