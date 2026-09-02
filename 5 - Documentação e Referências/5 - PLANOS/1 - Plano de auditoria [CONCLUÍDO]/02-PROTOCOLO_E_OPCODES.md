# 02 - Protocolo e Opcodes Canônicos: Aion Classic 5.0 EU

## 1. Matemática do Protocolo e Enquadramento Criptográfico

### 1.1 Fio de Rede (Wire Protocol)
- **Cabeçalho de Enquadramento**: `[u16 length (inclusive)][corpo cifrado]`
- **Corpo Cifrado**: `[u16 opcode_fio][1 byte staticServerPacketCode = 0x65][u16 checksum = ~opcode_fio][payload]`
- **Handshake Inicial**:
  - Primeiro pacote do servidor: `S_KEY` (11 bytes em claro).
  - Últimos 4 bytes trazem o seed para cálculo da chave Blowfish/XOR de 8 bytes.
  - Constantes criptográficas:
    - `SUB_SEED = 0x3FF2CC87`
    - `XOR_SEED_32 = 0xCD92E451`
    - `XOR_SEED_64 = 0x87546CA100000000`

### 1.2 Transformação de Opcodes
- **Cliente -> Servidor**:
  $$\text{decOp} = ((\text{wireOp} \oplus 0x36) - 0xC4) \pmod{0x10000}$$
  $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0x36$$
- **Servidor -> Cliente**:
  $$\text{decOp} = ((\text{wireOp} \oplus 0xD4) - 0xC4) \pmod{0x10000}$$
  $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0xD4$$

---

## 2. Correções Obrigatórias na Tabela de Cliente (`AionPacketHandlerFactory.java`)

| Nome do Pacote | decOp (PCAP) | wireOp Canônico | Problema Identificado | Ação Corretiva |
|---|---|---|---|---|
| `CM_LEVEL_READY` | `0x0019` | `0x00EB` | Opcode principal estava como `0x0E2` (decOp `0x0010`) | Remover `0x0E2`, fixar `0x00EB` como canônico |
| `CM_READ_EXPRESS_MAIL` | `0x00A2` | `0x0150` | Confusão entre fio `0x150` e decOp `0x0150` (fio `0x0222`) | Separar e criar handler para `0x0222` (motion/heartbeat) |
| `CM_RECIPE_LIST` | `0x00B6` | `0x014C` | Faltando registro no factory | Adicionar `new CM_RECIPE_LIST(0x14C, State.IN_GAME)` |
| `CM_GLOBAL_TRADE` | `0x0101` | `0x01F3` | Faltando registro no factory | Adicionar `new CM_GLOBAL_TRADE(0x1F3, State.IN_GAME)` |
| `CM_CLIENT_PING_STATE` | `0x0150` | `0x0222` | Faltando registro (1404 ocorrências em PCAP) | Implementar e registrar para State.IN_GAME |
| `CM_SERVER_PVP_ACK` | `0x0326` | `0x03DC` | Faltando registro (len 7) | Implementar e registrar para State.IN_GAME |
| `CM_CUSTOM_SETTING_ACK`| `0xFFFC` | `0x00F6` | Faltando registro (len 4) | Registrar para State.IN_GAME |
| `CM_CUSTOM_SETTING_ACK2`| `0xFFFD` | `0x00F7` | Faltando registro (len 4) | Registrar para State.IN_GAME |

---

## 3. Correções Obrigatórias na Tabela de Servidor (`ServerPacketsOpcodes.java`)

1. **Descomentar e Ativar Opcodes Válidos**:
   - `0x00A4` -> `S_LOAD_GATHERCOMBINE_COOLTIME`
   - `0x00BC` -> `S_LOAD_PVP_ENV`
   - `0x00D7` -> `S_SKILL_PENALTY_STATUS`
   - `0x00D8` -> `S_SKILL_PENALTY_STATUS_OTHER`

2. **Corrigir Opcodes Conflitantes**:
   - `0x0043` -> `S_INVISIBLE_LEVEL` (7 bytes)
   - `0x0093` -> `S_CUSTOM_ANIM` (19 bytes)

3. **Registrar Novos Pacotes Oficiais 5.0**:
   - `0x000D` -> `S_TUTORIAL_HINT` (3 bytes)
   - `0x005F` -> `S_ZONE_MAP_INFO` (134 bytes)
   - `0x0102` -> `S_SECURITY_TOKEN` (32 bytes)
   - `0x0105` -> `S_ACCOUNT_REPUTATION` (9 bytes)
   - `0x0110` -> `S_SEASON_PASS_INFO` (36 bytes)
   - `0x0114` -> `S_ACHIEVEMENT_REWARD_NOTI` (68 bytes)
   - `0x0181` -> `S_SERVER_TIME_EXP` (38/74 bytes)
   - `0x019D` -> `S_WORLD_ENV_FLAGS` (Strings UTF-16)
   - `0x019F` -> `S_DAEVA_PASS_DATA` (793 bytes)
   - `0x01C2` -> `S_WARMUP_REPUTATION` (14 bytes)
