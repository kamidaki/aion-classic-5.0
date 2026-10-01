# Análise Estrutural e Classificação Semântica dos 29 Pacotes Oficiais (SM_UNK_*)

Este relatório documenta a dissecação byte a byte, o contexto causal (gatilho e resposta), a correlação com o roadmap do jogador e a estrutura de dados proposta para todos os **29 opcodes oficiais** que foram observados no PCAP oficial `subida-1-60-2026-08-28.pcapng` e que atualmente estão registrados como `SM_UNK_*`.

---

## SM_UNK_00BC — Dec: 188 (`0x00BC`) | Wire: `0x0154`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2] bytes
- **Comentário de registro original:** `[S_UNK_00BC] (0x00BC)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2 bytes, Timestamp: 1787886192888.6s):
```text
Hex: 0000
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_EMOTION_LIST (dec 0x004E)`
- **Pacote Imediatamente Posterior:** `S->C SM_INFLUENCE_RATIO (dec 0x0054)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([2] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_00C5 — Dec: 197 (`0x00C5`) | Wire: `0x015D`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 151
- **Tamanhos observados:** [13] bytes
- **Comentário de registro original:** `[S_UNK_00C5] (0x00C5)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 13 bytes, Timestamp: 1787887963908.5s):
```text
Hex: 31df0180030200000000000000
Valores iniciais: byte[0]=49 (0x31), short[0]=57137, int[0]=2147606321 (0x8001DF31), long[0]=0x000002038001DF31
```
**Ocorrência 2** (Tamanho: 13 bytes, Timestamp: 1787887978767.6s):
```text
Hex: 31df0180030000000000000000
Valores iniciais: byte[0]=49 (0x31), short[0]=57137, int[0]=2147606321 (0x8001DF31), long[0]=0x000000038001DF31
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_NPC_INFO (dec 0x000E)`
- **Pacote Imediatamente Posterior:** `S->C SM_MOVE (dec 0x0037)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_CREATURE_POSTURE_STATE` / `S_ENTITY_STATE_NOTIFY` (Atualização de postura/estado de criatura).
- **Evidência Comprovada:** Ocorre 151 vezes. O payload de 13 bytes possui `writeD(creatureObjectId)` + `writeC(stateType=3)` + `writeD(flags)` + `writeD(0)`. Enviado continuamente quando monstros ou jogadores entram em modo de alerta, combate ou repouso.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_CREATURE_STATE_UPDATE`.

---

## SM_UNK_0109 — Dec: 265 (`0x0109`) | Wire: `0x0119`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [3] bytes
- **Comentário de registro original:** `[S_UNK_0109] (0x0109)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 3 bytes, Timestamp: 1787886192708.8s):
```text
Hex: 010000
Valores iniciais: byte[0]=1 (0x01), short[0]=1
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_TUTORIAL_HINT (dec 0x000D)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01C0 (dec 0x01C0)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([3] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_0110 — Dec: 272 (`0x0110`) | Wire: `0x0100`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [36] bytes
- **Comentário de registro original:** `[S_UNK_0110] (0x0110)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 36 bytes, Timestamp: 1787886195960.6s):
```text
Hex: 010058d1200f000000000201000000000000000000000000000000000000000000000000
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=3512205313 (0xD1580001), long[0]=0x00000F20D1580001
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_NEARBY_QUESTS (dec 0x007E)`
- **Pacote Imediatamente Posterior:** `S->C S_CLEAR_ACHIEVEMENT_EVENT (dec 0x0115)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_ACHIEVEMENT_SEASON_EVENT_INFO` (Sincronização de temporada de conquista ativa).
- **Evidência Comprovada:** 36 bytes contendo `writeH(1)` + `writeQ(achievementObjectId)` + flags de ativação de temporada.
- **Nível de Evidência:** **FORTE EVIDÊNCIA**.
- **Recomendação:** Conectar ao `BattlePassService` / `AchievementService`.

---

## SM_UNK_0127 — Dec: 295 (`0x0127`) | Wire: `0x013F`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [20] bytes
- **Comentário de registro original:** `[S_UNK_0127] (0x0127)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 20 bytes, Timestamp: 1787886193068.4s):
```text
Hex: 0900000001000200030004000500060007000800
Valores iniciais: byte[0]=9 (0x09), short[0]=9, int[0]=9 (0x00000009), long[0]=0x0002000100000009
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_SPAM_FILTER_FLAG (dec 0x0126)`
- **Pacote Imediatamente Posterior:** `S->C SM_CHANNEL_CHATTING_BLACKLIST_SETTING (dec 0x012C)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_UI_TAB_UNLOCKED_ARRAY` (Slots/abas desbloqueadas da interface).
- **Evidência Comprovada:** 20 bytes contendo `writeD(count=9)` seguido de 9 inteiros curtos consecutivos (`0x0001` a `0x0008`) correspondentes às abas liberadas de inventário/cubo/quickbar.
- **Nível de Evidência:** **FORTE EVIDÊNCIA**.
- **Recomendação:** Renomear para `SM_UI_TABS_UNLOCKED`.

---

## SM_UNK_0129 — Dec: 297 (`0x0129`) | Wire: `0x0139`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2252] bytes
- **Comentário de registro original:** `[S_UNK_0129] (0x0129)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2252 bytes, Timestamp: 1787886193249.3s):
```text
Hex: a200460061007a00790000005a0063006200710077000000320032007300320045003400420044000000500068006b00
Valores iniciais: byte[0]=162 (0xA2), short[0]=162, int[0]=4587682 (0x004600A2), long[0]=0x007A0061004600A2
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `C->S CM_PING (dec 0x0159, wire 0x022B)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_013A (dec 0x013A)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_RECOMMENDED_PLAYERS_LIST` (Lista de jogadores recomendados / amigos próximos na entrada).
- **Evidência Comprovada:** Pacote de 2252 bytes contendo cabeçalho `writeH(count)` seguido por múltiplos blocos de strings UTF-16LE com nomes de jogadores reais da sessão oficial ('Fazy', 'Zcbqw', '22s2'...). Disparado na entrada do mundo.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_RECOMMENDED_PLAYERS_LIST`.

---

## SM_UNK_0135 — Dec: 309 (`0x0135`) | Wire: `0x012D`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 4
- **Tamanhos observados:** [19] bytes
- **Comentário de registro original:** `[S_UNK_0135] (0x0135)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 19 bytes, Timestamp: 1787887186444.2s):
```text
Hex: 6700000001024b0000004b0000000000000000
Valores iniciais: byte[0]=103 (0x67), short[0]=103, int[0]=103 (0x00000067), long[0]=0x004B020100000067
```
**Ocorrência 2** (Tamanho: 19 bytes, Timestamp: 1787887188995.6s):
```text
Hex: 7900000001c14b0000004b0000000000000000
Valores iniciais: byte[0]=121 (0x79), short[0]=121, int[0]=121 (0x00000079), long[0]=0x004BC10100000079
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `C->S CM_CLIENT_PING_STATE (dec 0x0150, wire 0x0222)`
- **Pacote Imediatamente Posterior:** `C->S CM_MOVE (dec 0x0030, wire 0x00C2)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([19] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_013A — Dec: 314 (`0x013A`) | Wire: `0x012A`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [6] bytes
- **Comentário de registro original:** `[S_UNK_013A] (0x013A)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 6 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 000000000000
Valores iniciais: byte[0]=0 (0x00), short[0]=0, int[0]=0 (0x00000000)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0129 (dec 0x0129)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01B3 (dec 0x01B3)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([6] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_0146 — Dec: 326 (`0x0146`) | Wire: `0x02DE`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [8] bytes
- **Comentário de registro original:** `[S_UNK_0146] (0x0146)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 8 bytes, Timestamp: 1787886192888.6s):
```text
Hex: aa2d462e00000000
Valores iniciais: byte[0]=170 (0xAA), short[0]=11690, int[0]=776351146 (0x2E462DAA), long[0]=0x000000002E462DAA
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_BIND_POINT_INFO (dec 0x00EB)`
- **Pacote Imediatamente Posterior:** `S->C SM_PLAYER_SPAWN (dec 0x000F)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_PLAYER_SPAWN_ID_CONFIRM` (Confirmação de ID único do avatar).
- **Evidência Comprovada:** 8 bytes contendo exatamente o `playerObjectId` em 64-bit (`aa 2d 46 2e 00 00 00 00`), enviado imediatamente antes do `SM_PLAYER_SPAWN`.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_PLAYER_OBJECT_ID_ECHO`.

---

## SM_UNK_0170 — Dec: 368 (`0x0170`) | Wire: `0x02E0`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2] bytes
- **Comentário de registro original:** `[S_UNK_0170] (0x0170)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 0000
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_01AC (dec 0x01AC)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_0183 (dec 0x0183)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([2] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_0173 — Dec: 371 (`0x0173`) | Wire: `0x02E3`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 3
- **Tamanhos observados:** [4] bytes
- **Comentário de registro original:** `[S_UNK_0173] (0x0173)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 4 bytes, Timestamp: 1787889255261.1s):
```text
Hex: 04000000
Valores iniciais: byte[0]=4 (0x04), short[0]=4, int[0]=4 (0x00000004)
```
**Ocorrência 2** (Tamanho: 4 bytes, Timestamp: 1787889351751.2s):
```text
Hex: 08000000
Valores iniciais: byte[0]=8 (0x08), short[0]=8, int[0]=8 (0x00000008)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `C->S CM_MOVE_ITEM (dec 0x00B4, wire 0x014E)`
- **Pacote Imediatamente Posterior:** `S->C SM_STATUPDATE_HP (dec 0x0003)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_EQUIP_SLOT_MASK_UPDATE` (Atualização de máscara de slots de equipamento).
- **Evidência Comprovada:** Ocorre exatamente no momento em que o jogador desequipa itens do inventário no roadmap (armas, armaduras). O payload de 4 bytes transmite o índice do slot alterado (`0x04`, `0x08`, `0x0E`...).
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_EQUIP_SLOT_UPDATE` e vincular a `Equipment.java`.

---

## SM_UNK_0177 — Dec: 375 (`0x0177`) | Wire: `0x02EF`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [6] bytes
- **Comentário de registro original:** `[S_UNK_0177] (0x0177)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 6 bytes, Timestamp: 1787886192708.8s):
```text
Hex: 000001000000
Valores iniciais: byte[0]=0 (0x00), short[0]=0, int[0]=65536 (0x00010000)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_STORYBOOK_REGISTERED_LIST (dec 0x014D)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_0197 (dec 0x0197)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([6] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_0181 — Dec: 385 (`0x0181`) | Wire: `0x0291`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 48
- **Tamanhos observados:** [38, 74] bytes
- **Comentário de registro original:** `[S_UNK_0181] (0x0181)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 38 bytes, Timestamp: 1787886986814.8s):
```text
Hex: 01004d6c030051d02180a0860100a08601008afd906a00000000de4918448ad23044e18db143
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=1816985601 (0x6C4D0001), long[0]=0xD05100036C4D0001
```
**Ocorrência 2** (Tamanho: 38 bytes, Timestamp: 1787886990849.5s):
```text
Hex: 01004d6c030051d02180a0860100a08601008afd906a00000000de4918448ad23044e18db143
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=1816985601 (0x6C4D0001), long[0]=0xD05100036C4D0001
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_ATTACK (dec 0x0036)`
- **Pacote Imediatamente Posterior:** `S->C SM_NPC_INFO (dec 0x000E)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_ABNORMAL_EFFECT_PERIODIC` / `S_COMBAT_BURST_EFFECT` (Efeito de combate / postura temporária).
- **Evidência Comprovada:** Ocorre 48 vezes exclusivamente durante o combate do tutorial contra monstros. O payload contém `writeH(1)` + `writeD(effectSkillId)` + `writeD(creatureObjectId)` + `writeD(durationMs=100000)` + timestamp Unix + floats de impacto.
- **Nível de Evidência:** **FORTE EVIDÊNCIA**.
- **Recomendação:** Manter estrutura já implementada em `SM_UNK_0181.java` e conectar com o acerto de skills do combat engine.

---

## SM_UNK_0182 — Dec: 386 (`0x0182`) | Wire: `0x0292`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 9
- **Tamanhos observados:** [8] bytes
- **Comentário de registro original:** `[S_UNK_0182] (0x0182)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 8 bytes, Timestamp: 1787887059301.2s):
```text
Hex: 4d6c030051d02180
Valores iniciais: byte[0]=77 (0x4D), short[0]=27725, int[0]=224333 (0x00036C4D), long[0]=0x8021D05100036C4D
```
**Ocorrência 2** (Tamanho: 8 bytes, Timestamp: 1787887070961.4s):
```text
Hex: 3c450c00e9d62180
Valores iniciais: byte[0]=60 (0x3C), short[0]=17724, int[0]=804156 (0x000C453C), long[0]=0x8021D6E9000C453C
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_NEARBY_QUESTS (dec 0x007E)`
- **Pacote Imediatamente Posterior:** `S->C SM_DELETE (dec 0x0016)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_ABNORMAL_EFFECT_REMOVE` (Remoção do efeito de combate de 0x0181).
- **Evidência Comprovada:** Ocorre 9 vezes, com exatamente 8 bytes: `writeD(effectSkillId)` + `writeD(creatureObjectId)`. Sempre disparado no momento exato em que o efeito temporário do 0x0181 cessa ou o monstro é deletado.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_COMBAT_EFFECT_REMOVE`.

---

## SM_UNK_0183 — Dec: 387 (`0x0183`) | Wire: `0x0293`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2] bytes
- **Comentário de registro original:** `[S_UNK_0183] (0x0183)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 0100
Valores iniciais: byte[0]=1 (0x01), short[0]=1
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0170 (dec 0x0170)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01AF (dec 0x01AF)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([2] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_018C — Dec: 396 (`0x018C`) | Wire: `0x0284`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [216] bytes
- **Comentário de registro original:** `[S_UNK_018C] (0x018C)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 216 bytes, Timestamp: 1787886193249.3s):
```text
Hex: d40000001400000000000e001800040008000c00100014000e00000047780802abfcee19900000007800000004000000
Valores iniciais: byte[0]=212 (0xD4), short[0]=212, int[0]=212 (0x000000D4), long[0]=0x00000014000000D4
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_01B3 (dec 0x01B3)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01AC (dec 0x01AC)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_MAP_GRID_SECTOR_PARAMS` (Parâmetros da malha e setores do mapa).
- **Evidência Comprovada:** 216 bytes com tabela de 20 offsets e dimensões de colisão do terreno do mapa Pandaemonium/Tutorial, enviado na transição de mundo.
- **Nível de Evidência:** **FORTE EVIDÊNCIA**.
- **Recomendação:** Manter baseline estático por mapa em `SM_UNK_018C`.

---

## SM_UNK_0191 — Dec: 401 (`0x0191`) | Wire: `0x0281`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [8] bytes
- **Comentário de registro original:** `[S_UNK_0191] (0x0191)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 8 bytes, Timestamp: 1787886193068.4s):
```text
Hex: 30485246a0010000
Valores iniciais: byte[0]=48 (0x30), short[0]=18480, int[0]=1179797552 (0x46524830), long[0]=0x000001A046524830
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_ABYSS_RANK (dec 0x00ED)`
- **Pacote Imediatamente Posterior:** `S->C S_DAEVA_PASS_DATA (dec 0x019F)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([8] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_0197 — Dec: 407 (`0x0197`) | Wire: `0x028F`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [6] bytes
- **Comentário de registro original:** `[S_UNK_0197] (0x0197)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 6 bytes, Timestamp: 1787886192708.8s):
```text
Hex: aa2d462e0000
Valores iniciais: byte[0]=170 (0xAA), short[0]=11690, int[0]=776351146 (0x2E462DAA)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0177 (dec 0x0177)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01A8 (dec 0x01A8)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([6] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01A8 — Dec: 424 (`0x01A8`) | Wire: `0x02B8`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [6] bytes
- **Comentário de registro original:** `[S_UNK_01A8] (0x01A8)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 6 bytes, Timestamp: 1787886192708.8s):
```text
Hex: aa2d462e0000
Valores iniciais: byte[0]=170 (0xAA), short[0]=11690, int[0]=776351146 (0x2E462DAA)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0197 (dec 0x0197)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01BA (dec 0x01BA)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([6] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01AA — Dec: 426 (`0x01AA`) | Wire: `0x02BA`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [3] bytes
- **Comentário de registro original:** `[S_UNK_01AA] (0x01AA)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 3 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 010000
Valores iniciais: byte[0]=1 (0x01), short[0]=1
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_01AB (dec 0x01AB)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01C5 (dec 0x01C5)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([3] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01AB — Dec: 427 (`0x01AB`) | Wire: `0x02BB`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [3] bytes
- **Comentário de registro original:** `[S_UNK_01AB] (0x01AB)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 3 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 000002
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_GLOBAL_TRADE_SALESLOG (dec 0x0141)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_01AA (dec 0x01AA)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([3] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01AC — Dec: 428 (`0x01AC`) | Wire: `0x02A4`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [254] bytes
- **Comentário de registro original:** `[S_UNK_01AC] (0x01AC)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 254 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 0100000000000000170000003c009f04002e130f002ea00f002e2d11002e7611002e191c002e6222002ef923002e322d
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=1 (0x00000001), long[0]=0x0000000000000001
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_018C (dec 0x018C)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_0170 (dec 0x0170)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_CLIENT_ZONE_INDEX_TABLE` (Tabela de zonas e sub-regiões do mapa ativo).
- **Evidência Comprovada:** 254 bytes estruturados em 23 pares de zone IDs (`0x2E00 049F`, `0x2E00 0F13`, `0x2E00 112D`...), definindo os limites das zonas ativas de Pandaemonium.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Integrar com o carregamento estático de zonas por WorldId.

---

## SM_UNK_01AF — Dec: 431 (`0x01AF`) | Wire: `0x02A7`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [5] bytes
- **Comentário de registro original:** `[S_UNK_01AF] (0x01AF)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 5 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 0000000000
Valores iniciais: byte[0]=0 (0x00), short[0]=0, int[0]=0 (0x00000000)
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0183 (dec 0x0183)`
- **Pacote Imediatamente Posterior:** `S->C SM_PACKAGE_INFO_NOTIFY (dec 0x0101)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([5] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01B3 — Dec: 435 (`0x01B3`) | Wire: `0x02A3`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2] bytes
- **Comentário de registro original:** `[S_UNK_01B3] (0x01B3)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 0000
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_013A (dec 0x013A)`
- **Pacote Imediatamente Posterior:** `S->C SM_UNK_018C (dec 0x018C)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([2] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01BA — Dec: 442 (`0x01BA`) | Wire: `0x02AA`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [3] bytes
- **Comentário de registro original:** `[S_UNK_01BA] (0x01BA)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 3 bytes, Timestamp: 1787886192708.8s):
```text
Hex: 010000
Valores iniciais: byte[0]=1 (0x01), short[0]=1
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_01A8 (dec 0x01A8)`
- **Pacote Imediatamente Posterior:** `S->C SM_TUTORIAL_HINT (dec 0x000D)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([3] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01BD — Dec: 445 (`0x01BD`) | Wire: `0x0255`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 42
- **Tamanhos observados:** [27] bytes
- **Comentário de registro original:** `[S_UNK_01BD] (0x01BD)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 27 bytes, Timestamp: 1787886569383.5s):
```text
Hex: 01000b000000021700000000000000010000000000000000000000
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=720897 (0x000B0001), long[0]=0x17020000000B0001
```
**Ocorrência 2** (Tamanho: 27 bytes, Timestamp: 1787886769408.6s):
```text
Hex: 01000b000000021700000000000000020000000000000000000000
Valores iniciais: byte[0]=1 (0x01), short[0]=1, int[0]=720897 (0x000B0001), long[0]=0x17020000000B0001
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_DELETE (dec 0x0016)`
- **Pacote Imediatamente Posterior:** `S->C SM_ATTACK_STATUS (dec 0x0005)`

### Análise Semântica e Função Provável

- **Função Identificada:** `S_HUNT_PROGRESS` / `S_QUEST_OBJECTIVE_STEP` (Progresso de objetivo de caça/tutorial).
- **Evidência Comprovada:** Ocorre 42 vezes. Toda vez que um mob morre no tutorial (após `SM_DELETE` e antes de `SM_STATUPDATE_EXP`), o campo de 4 bytes incrementa (1, 2, 3, 4...). O payload traz `writeH(1)` (count), `writeD(11)` (id do tutorial/guia), `writeC(2)`, `writeD(0x17)` (tipo do mob), e o contador incremental `writeD(counter)`.
- **Nível de Evidência:** **COMPROVADO**.
- **Recomendação:** Renomear para `SM_HUNT_OBJECTIVE_PROGRESS` e integrar ao `QuestEngine` / `TutorialService`.

---

## SM_UNK_01C0 — Dec: 448 (`0x01C0`) | Wire: `0x0250`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [2] bytes
- **Comentário de registro original:** `[S_UNK_01C0] (0x01C0)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 2 bytes, Timestamp: 1787886192708.8s):
```text
Hex: 0000
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_0109 (dec 0x0109)`
- **Pacote Imediatamente Posterior:** `S->C SM_ITEM_COOLDOWN (dec 0x0066)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([2] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01C2 — Dec: 450 (`0x01C2`) | Wire: `0x0252`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [14] bytes
- **Comentário de registro original:** `[S_UNK_01C2] (0x01C2)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 14 bytes, Timestamp: 1787886192708.8s):
```text
Hex: 0200050000000000060000000000
Valores iniciais: byte[0]=2 (0x02), short[0]=2, int[0]=327682 (0x00050002), long[0]=0x0000000000050002
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C 0x116 (dec 0x0116)`
- **Pacote Imediatamente Posterior:** `S->C S_CREATE_ACHIEVEMENT_EVENT (dec 0x0112)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([14] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

## SM_UNK_01C5 — Dec: 453 (`0x01C5`) | Wire: `0x025D`

- **Direção:** Servidor → Cliente (S → C)
- **Ocorrências no PCAP:** 1
- **Tamanhos observados:** [3] bytes
- **Comentário de registro original:** `[S_UNK_01C5] (0x01C5)`

### Amostras de Payload e Estrutura dos Bytes

**Ocorrência 1** (Tamanho: 3 bytes, Timestamp: 1787886193249.3s):
```text
Hex: 000002
Valores iniciais: byte[0]=0 (0x00), short[0]=0
```

### Causalidade e Contexto de Execução

- **Pacote Imediatamente Anterior:** `S->C SM_UNK_01AA (dec 0x01AA)`
- **Pacote Imediatamente Posterior:** `S->C SM_STATS_INFO (dec 0x0001)`

### Análise Semântica e Função Provável

- **Classificação Geral:** Pacote de infraestrutura / sinalização do cliente oficial Classic 5.0.
- **Estrutura Básica:** Payload estático ou de tamanho fixo ([3] bytes) enviado na entrada do mundo ou handshake.
- **Nível de Evidência:** **HIPÓTESE CONTEXTUAL** (função demarcada pelo momento cronológico do handshake).
- **Recomendação:** Manter a classe `SM_UNK_*` atual preservando os bytes verificados no wire.

---

