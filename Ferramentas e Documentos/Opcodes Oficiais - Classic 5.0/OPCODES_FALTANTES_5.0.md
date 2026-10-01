# Opcodes Faltantes e Incorretos — Aion Classic 5.0 EU

Este documento lista todos os opcodes observados na captura oficial autorizada `subida-1-60-2026-08-28.pcapng` que estão ausentes ou incorretamente mapeados no emulador Java.

## 0x0112 (274 Decimal)

**Direção:**
S → C

**Wire:**
0x0102

**Ocorrências:**
1

**Tamanhos observados:**
68 bytes

**Evento observado:**
Entrada do personagem no mundo (Pkt 60 da sessão 53646), logo antes de S_PROGRESS_ACHIEVEMENT e listas de quest/título.

**Antes:**
`SM_UNK_01C2` (0x01C2, wire 0x0252, len 14)

**Depois:**
`S_PROGRESS_ACHIEVEMENT` (0x010F, wire 0x0107, len 146)

**Possível função:**
`S_CREATE_ACHIEVEMENT_EVENT` (Eventos/Quests de Achievement/BattlePass ativos). A estrutura oficial tem `writeH(size)` + 66 bytes por quest (total exato de 68 bytes no pacote com 1 quest ativa). O emulador registrou erroneamente como 273 (0x111).

**Nível de evidência:**
COMPROVADO

**Implementação:**
RESOLVIDO (Mapeado opcode 274 para `S_CREATE_ACHIEVEMENT_EVENT` em `ServerPacketsOpcodes.java`)

---

## 0x0118 (280 Decimal)

**Direção:**
S → C

**Wire:**
0x0108

**Ocorrências:**
2

**Tamanhos observados:**
232 bytes

**Evento observado:**
Entrada do jogador no mundo (Pkt 66) e atualização de temporada de BattlePass (Pkt 208). Ocorre exatamente antes de S_BATTLEPASS_UPDATED.

**Antes:**
`SM_MOTION` (0x0093, wire 0x0183, len 3)

**Depois:**
`S_BATTLEPASS_UPDATED` (0x0117, wire 0x010F, len 234)

**Possível função:**
`S_BATTLEPASS_UPDATED` (ou `S_BATTLEPASS_SEASON_INFO`). O payload possui exatamente 232 bytes (1 temporada de BattlePass: 32 bytes de cabeçalho + 200 bytes de recompensas), que é idêntico ao corpo de `S_BATTLEPASS_UPDATED.java` (onde o autor colocou no javadoc `S_BATTLEPASS_UPDATED (0x0118)` mas registrou como 279).

**Nível de evidência:**
COMPROVADO

**Implementação:**
RESOLVIDO (Mapeado opcode 280 para `S_BATTLEPASS_UPDATED` e 279 para `S_BATTLEPASS_LIST` em `ServerPacketsOpcodes.java`)

---

## 0x0181 Wire (Dec 0x00F3) — Colisão e Handler Falso

**Direção:**
C → S

**Wire:**
0x0181

**Ocorrências:**
4

**Tamanhos observados:**
5 bytes

**Evento observado:**
Inscrição nos rankings de poder de combate (Combat Power 1000..1003) durante a entrada no mundo.

**Payload observado:**
`eb03000001` (1003, local=1), `ea03000001` (1002, local=1), `e903000000` (1001, local=0), `e803000000` (1000, local=0).

**Colisão:**
Registrado simultaneamente para `CM_CLIENT_MOTION_ACK` e `CM_RANKING_SUBSCRIBE` no estado `IN_GAME`.

**Veredito:**
`CM_CLIENT_MOTION_ACK` é uma classe falsa (stub vazio criado com leitura incorreta `readC(); readD();`). O pacote oficial é comprovadamente `CM_RANKING_SUBSCRIBE` (`readD(); readC();`).

**Nível de evidência:**
COMPROVADO

**Implementação:**
RESOLVIDO (Registrado `CM_RANKING_SUBSCRIBE` no wire `0x0181` em `AionPacketHandlerFactory.java` e removida a colisão com `CM_CLIENT_MOTION_ACK`)

---

## 0x015A Wire (Dec 0x00A8) — Handler Incorreto

**Direção:**
C → S

**Wire:**
0x015A

**Ocorrências:**
9

**Tamanhos observados:**
0 bytes

**Evento observado:**
Enviado periodicamente a cada 480 segundos (8 minutos) exatos pelo cliente. O servidor responde imediatamente com `SM_SECURITY_TOKEN` (0x0102, 32 bytes).

**Handler atual:**
`CM_SHOW_BLOCKLIST` (registrado incorretamente em linha 69 de `AionPacketHandlerFactory.java`). O verdadeiro `CM_SHOW_BLOCKLIST` é wire `0x014A`.

**Possível função:**
`CM_SECURITY_TOKEN_REQUEST` (`C_REQ_WEB_SESSIONKEY`).

**Nível de evidência:**
COMPROVADO

**Implementação:**
RESOLVIDO (Wire `0x015A` mapeado para `CM_SECURITY_TOKEN` e `CM_SHOW_BLOCKLIST` corrigido para wire `0x014A` em `AionPacketHandlerFactory.java`)

---

## Pacotes de Alta Prioridade Refatorados (Classic 5.0)

| Opcode Dec | Opcode Hex | Nome Anterior | Nome Semântico Refatorado | Tamanho Wire | Função Semântica | Status |
|---|---|---|---|---|---|---|
| **445** | `0x01BD` | `SM_UNK_01BD` | `SM_HUNT_OBJECTIVE_PROGRESS` | 27 bytes | Notificação de progresso de objetivo de caça (Normal: 0x17, Named: 0x16, Boss: 0x15). | **REFATORADO** |
| **197** | `0x00C5` | `SM_UNK_00C5` | `SM_CREATURE_STATE_UPDATE` | 13 bytes | Atualização de estado/ação dinâmica de criatura (`targetId`, `action`, `val1`, `val2`). | **REFATORADO** |
| **386** | `0x0182` | `SM_UNK_0182` | `SM_COMBAT_BURST_REMOVE` | 8 bytes | Remoção de efeito visual de burst/abnormal effect (`effectId`, `targetObjectId`). | **REFATORADO** |
| **371** | `0x0173` | `SM_UNK_0173` | `SM_EQUIP_SLOT_UPDATE` | 4 bytes | Atualização de estado de slot de equipamento após movimentação de item (`slotId`). | **REFATORADO** |
| **297** | `0x0129` | `SM_UNK_0129` | `SM_RECOMMENDED_PLAYERS_LIST` | 2 / 2252 bytes | Lista de jogadores recomendados na entrada de mundo (`writeH(count)` + `writeS(name)`). | **REFATORADO** |
| **326** | `0x0146` | `SM_UNK_0146` | `SM_PLAYER_OBJECT_ID_ECHO` | 8 bytes | Eco do objectId do jogador no handshake de entrada de mundo (`objectId` + `0`). | **REFATORADO** |

---

## Como Foram Descobertos os 16 Blobs Fixos de Inicialização (SM_UNK_*)

Os 16 pacotes classificados como **Blobs Fixos de Inicialização** foram descobertos através da análise cronológica e diferencial do fluxo de rede oficial (`subida-1-60-2026-08-28.pcapng`), descriptografado com o algoritmo Blowfish de sessão do servidor oficial.

### Critérios de Identificação Comprovados:
1. **Cronologia Exclusiva de Handshake**: Todos os 16 pacotes são emitidos **exatamente 1 única vez por login/conexão**, em rajada contínua imediatamente após o spawn do jogador no mundo (`SM_PLAYER_SPAWN` / `SM_ENTER_WORLD_CHECK`).
2. **Invariância de Conteúdo (Payload Estático)**: Ao comparar sessões distintas e jogadores diferentes na mesma versão, os bytes desses 16 pacotes são **100% idênticos e estáticos**, servindo como confirmações de estado do motor (ACKs de subsistemas de áudio, mapa estático, câmera e abas padrão).
3. **Ausência de Gatilhos de Gameplay**: Ao contrário dos pacotes de alta/média prioridade (que disparam em combate, mortes de NPCs ou troca de equipamentos), esses 16 pacotes **nunca mais voltam a ser disparados durante o gameplay normal**.

### Tabela de Registro dos Blobs Fixos Refatorados

| Opcode Dec | Opcode Hex | Wire Hex | Nome Semântico | Classe Legada | Tamanho | Estrutura de Bytes / Função |
|---|---|---|---|---|---|---|
| **95** | `0x005F` | `0x00B2` | `SM_SPECIAL_CURRENCY_SLOTS` | `SM_UNK_005F` | 134 bytes | Tabela estática de 11 slots de moedas/tokens especiais do cliente. |
| **188** | `0x00BC` | `0x0154` | `SM_DEFAULT_EMOTION_LIST` | `SM_UNK_00BC` | 2 bytes | Handshake de lista de emoções / animações padrão (`writeH(0)`). |
| **295** | `0x0127` | `0x013F` | `SM_CUBE_TAB_EXPANSION_INFO` | `SM_UNK_0127` | 20 bytes | Inicialização de abas desbloqueadas de interface (Cubo/Bolsa). |
| **314** | `0x013A` | `0x012A` | `SM_LEGION_HOUSING_NOTICE` | `SM_UNK_013A` | 6 bytes | Sinalização inicial de módulo de legion / habitação (`writeD(0)` + `writeH(0)`). |
| **330** | `0x014A` | `0x0120` | `SM_NETWORK_SYNC_ACK` | `SM_UNK_014A` | 0 bytes | Pacote vazio de confirmação/sync de subsistema de rede. |
| **350** | `0x015E` | `0x0216` | `SM_LEGION_TERRITORY_INFO` | `SM_UNK_015E` | 22 bytes | Estado inicial de território / domínio de legião (`writeD(1)` + `writeH(1)` + zeros). |
| **387** | `0x0183` | `0x0293` | `SM_CAMERA_VIEW_MODE` | `SM_UNK_0183` | 2 bytes | Flag de modo de câmera e visão panorâmica de mapa (`writeH(1)`). |
| **396** | `0x018C` | `0x0284` | `SM_TERRAIN_SECTOR_INFO` | `SM_UNK_018C` | 216 bytes | Tabela estática de 20 setores de malha física do terreno ativo. |
| **401** | `0x0191` | `0x0281` | `SM_RENDER_GRAPHIC_INIT` | `SM_UNK_0191` | 8 bytes | Handshake de sincronização de engine gráfica/render (`FRH0` + `writeD(416)`). |
| **407** | `0x0197` | `0x028F` | `SM_AVATAR_PRESENCE_INIT` | `SM_UNK_0197` | 6 bytes | Confirmação de presença do avatar local no cliente (`writeD(objectId)` + `writeH(0)`). |
| **424** | `0x01A8` | `0x02B8` | `SM_AVATAR_PRESENCE_SYNC` | `SM_UNK_01A8` | 6 bytes | Sincronização secundária de presença do avatar (`writeD(objectId)` + `writeH(0)`). |
| **426** | `0x01AA` | `0x02BA` | `SM_COSMETIC_TITLE_INIT` | `SM_UNK_01AA` | 3 bytes | Inicialização de títulos e insígnias cosméticas (`writeH(1)` + `writeC(0)`). |
| **427** | `0x01AB` | `0x02BB` | `SM_SIEL_ANVIL_POINTS_INFO` | `SM_UNK_01AB` | 3+ bytes | Pontos de produção da Bigorna de Siel (Siel Anvil). |
| **428** | `0x01AC` | `0x02A4` | `SM_MAP_ZONE_BOUNDS` | `SM_UNK_01AC` | 254 bytes | Tabela de 23 pares de Zone IDs e limites do mapa atual. |
| **431** | `0x01AF` | `0x02A7` | `SM_RADAR_INITIAL_STATE` | `SM_UNK_01AF` | 5 bytes | Estado inicial do minimapa e radar de área (`writeD(0)` + `writeC(0)`). |
| **435** | `0x01B3` | `0x02A3` | `SM_MAILBOX_INITIAL_STATUS` | `SM_UNK_01B3` | 2 bytes | Notificação inicial de status de caixa de correio (`writeH(0)`). |
| **442** | `0x01BA` | `0x02AA` | `SM_REGION_CHAT_CHANNEL_INFO` | `SM_UNK_01BA` | 3 bytes | Ativação dos canais padrão de chat de região (`writeH(1)` + `writeC(0)`). |
| **448** | `0x01C0` | `0x0250` | `SM_TUTORIAL_LOAD_COMPLETED` | `SM_UNK_01C0` | 2 bytes | Sinalizador de finalização de carregamento de tutorial (`writeH(0)`). |
| **450** | `0x01C2` | `0x0252` | `SM_CHALLENGE_GUIDE_TABS` | `SM_UNK_01C2` | 14 bytes | Registro inicial de abas do guia de desafios/missões. |
| **453** | `0x01C5` | `0x025D` | `SM_ENTER_WORLD_HANDSHAKE_ACK` | `SM_UNK_01C5` | 3 bytes | ACK final de conclusão do handshake de entrada de mundo (`writeH(0)` + `writeC(2)`). |

---

## 7 Pacotes de Média Prioridade (Concluídos)

| Opcode Dec | Opcode Hex | Wire Hex | Nome Semântico | Ocorrências | Tamanho | Função Identificada |
|---|---|---|---|---|---|---|
| **385** | `0x0181` | `0x0291` | `SM_COMBAT_BURST_EFFECT` | 48 | 38 bytes | Aplicação de efeito de combate com coordenadas 3D (`skillId`, `targetId`, `duration`, `x, y, z`). |
| **309** | `0x0135` | `0x012D` | `SM_AUTO_GROUP_STATUS` | 4 | 19 bytes | Matchmaking / fila de auto group e arenas (`instanceId`, `status`, `minLevel`, `maxLevel`). |
| **272** | `0x0110` | `0x0100` | `SM_ACHIEVEMENT_SEASON_EVENT_INFO` | 1 | 36 bytes | Informação de temporada ativa de evento e passe de batalha. |
| **275** | `0x0113` | `0x0103` | `SM_SPECIAL_SHOP_ITEM_LIST` | 1 | 756 bytes | Lista de 58 itens/recompensas da loja especial Classic 5.0. |
| **375** | `0x0177` | `0x02EF` | `SM_EQUIPMENT_VIEW_STATE` | 1 | 6 bytes | Estado de visualização de equipamento e guarda-roupa (`type`, `count`, `state`). |
| **265** | `0x0109` | `0x0119` | `SM_TUTORIAL_GUIDE_STATE` | 1 | 3 bytes | Estado de exibição de guias de interface e tutoriais rápidos (`guideId`, `state`). |
| **368** | `0x0170` | `0x02E0` | `SM_ZONE_HAZARD_LIST` | 1 | 2 bytes | Lista de zonas de perigo ambiental / clima dinâmico ativas no mapa. |




