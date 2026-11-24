# Auditoria e Preservação de Origem: Retail 4.8 (Beyond Aion) vs. Classic 5.0

**Data:** 24/11/2026  
**Módulo Alvo Principal:** `Código Fonte - Emulador/game-server-gameforge` (GSID 1 — Referência Gameforge EU)  
**Repositório de Origem:** Beyond Aion (`https://github.com/beyond-aion/aion-server`)

---

## 1. Linhagem Arquitetural e Preservação de Créditos

Este projeto nasceu a partir da base **Retail 4.8 da Beyond Aion** e passou por reestruturação e adaptações de protocolo, pacotes, classes, dados estáticos e persistência para operar como o emulador **Aion Classic 5.0 — Lost Academy Group**:

```text
Retail 4.8 da Beyond Aion
↓
Modificação pesada e reestruturação
↓
Aion Classic 5.0 — Lost Academy Group
```

Em conformidade com as diretrizes de preservação e licenciamento (`LICENSE` e `README.md`):
- Os avisos de autoria e licença originais permanecem preservados no repositório;
- Não há afiliação oficial à Beyond Aion, Gameforge 4D GmbH ou NCSOFT Corporation;
- Heranças da versão 4.8 devem ser avaliadas e tratadas **individualmente, código por código, com evidências do Aion Classic 5.0 EU**, nunca por substituições genéricas em massa.

---

## 2. Classificação das Heranças Retail 4.8 no Código Atual

Durante a auditoria estática de `game-server-gameforge`, `commons`, `login-server` e `chat-server`, as referências à base 4.8 e à Beyond Aion dividem-se em três grupos técnicos distintos:

### 2.1 Resíduos Retail 4.8 Desativados ou Removidos para Classic 5.0 (Já Adaptados)
Serviços e opcodes exclusivos da era Retail 4.x/4.8 que não pertencem ao Aion Classic 5.0 e foram explicitamente neutralizados com justificativa técnica no código:

| Arquivo / Símbolo | Situação no Classic 5.0 | Evidência Observada |
|---|---|---|
| `GameServer.java` (`L109-124, L141-146`) | Serviços comentados como `// 4.8 retail residue` | `BaseService`, `WorldRaidService`, `VortexService`, `HousingService`, `HousingBidService`, `AuctionEndTask`, `AuctionAutoFillTask`, `MaintenanceTask`, `TownService` mantidos desativados; `CampWarService` 5.0 assume as torres de Tiamaranta Mesa (`L143-144`). |
| `SpawnEngine.java` (`L246-248`) | Housing desativado no spawn | `Game.dll` do Classic 5.0 não possui pacotes de Housing; `HOUSE_DATA` herdado da 4.8 provocaria erro `"There is no opcode"` caso spawnado no knownlist. |
| `ServerPacketsOpcodes.java` (`L252`) | Opcode `299 SM_ATREIAN_PASSPORT` removido | Documentado no código como `4.8 retail residue not present in Classic 5.0`. |
| `CM_NPSHOP_GOODS_COUNT.java` (`L11-13`) | Substituído do `CM_PING_REQUEST` 4.8 para `C_REQUEST_NPSHOP_GOODS_COUNT` (`0xAA`) | Atualizado para responder `S_NPSHOP_GOODS_COUNT` (`0x10A`) conforme capturas oficiais 5.0. |
| `AionPacketHandlerFactory.java` (`L203-205`) | Opcode `0x0005` reatribuído de `CM_REVIVE` (4.8) para `CM_LEGION` | `C_DEAD_RESTART` no Classic 5.0 utiliza `dec 0x000D` (`0xE7`). |
| `DialogAction.java` (`L118-119`) | `TRADE_SELL_LIST` ajustado de `103` (4.8) para `10256` (5.0) | Validado com captura oficial (`Frigga 799949 -> S_STORE_PURCHASE_INFO`). |
| `SM_LEGION_INFO.java` (`L22-23`) e `SM_LEGION_MEMBERLIST.java` (`L51-53`) | Serialização adaptada para Classic 5.0 | Substituídos os blocos de contribuição/dissolução/Legion Dominion da 4.8 pelos blocos medidos no cliente 5.0. |
| `SM_MAIL_SERVICE.java` (`L138, L151`) | Leitura com destinatário zero e remoção do `nameId` da 4.8 em anexos | Atualizado conforme layout capturado do Classic 5.0 quando há item anexo. |
| `ItemPacketService.java` (`L35`) | `DEC_STIGMA_USE` ajustado de `0x17` (4.8) para `0` (5.0) | Comprovado nas capturas oficiais de uso/troca de página de estigma. |
| `Stigma.java` (`L14-16`) | Reestruturação de estigmas Classic 5.0 | No Classic 5.0, pedras de estigma concedem apenas suas skills configuradas e estigmas superiores validam skills requeridas ativas, diferindo do modelo 4.8. |
| `SummonGameStats.java` (`L109-112`) | Compatibilização Lava Spirit (4.8) / Magma Spirit (5.0) | Mantido suporte a ambos os nomes (`isSpirit("magma") || isSpirit("lava")`) devido à base XML originária da 4.8. |

### 2.2 Heranças Parciais da 4.8 Ainda Pendentes de Comprovação 5.0 (Tratar Caso a Caso)
Trechos onde o próprio código registra explicitamente que parte dos casos segue o comportamento herdado da 4.8 por ausência de captura oficial específica no Classic 5.0:

| Arquivo | Trecho / Comportamento Herdado | Ação Recomendada para Futuras Contribuições |
|---|---|---|
| `CM_LEGION.java` (`L26`) | Comentário `As demais seguem o layout da 4.8 (PENDENTE_DE_COMPROVACAO)` para sub-ações ainda não capturadas de `C_GUILD` (`0x05`) além de `0x00, 0x01, 0x02, 0x06, 0x08, 0x09, 0x0D, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16`. | Validar sub-ações faltantes contra pacotes reais do GameForge EU (GSID 1) antes de alterar estruturas. |
| `SM_LEGION_LEAVE_MEMBER.java` (`L11`) | Ramo de saída/expulsão (`flag 0`) mantém o layout da 4.8 (`PENDENTE_DE_COMPROVACAO`). | Coletar captura oficial de expulsão/saída voluntária de Legion no 5.0 para substituir o layout 4.8 com segurança. |
| `SM_MAIL_SERVICE.java` (`L155-158`) | Carta sem anexo mantém três leituras/escritas (`writeQ(0)`, `writeQ(0)`, `writeD(0)`) herdadas da 4.8 por falta de captura do caso vazio no 5.0. | Validar em captura oficial de correio sem anexo. |
| `ItemPacketService.java` (`L22-24, L59+`) | Motivos de `ItemUpdateType` além dos 29 tipos já validados nas capturas 5.0 herdam máscaras da 4.8 e enviam trailer `0`. | Registrar cada novo motivo individualmente conforme capturas `S_CHANGE_ITEM_DESC` (`0x1D`) no oficial. |
| `AionPacketHandlerFactory.java` (`L81`) | Alias legado `0x09` mantido em `CM_LEVEL_READY` junto ao opcode Classic `0xEB` (`0x0019`). | Confirmar em sessão real se o alias 4.8 ainda é necessário ou pode ser isolado. |
| `Equipment.java` (`L802`) | Tratamento de fallback para `slot == 0` / bits de slot herdados da 4.8 (ex.: estigmas legados em banco antigo). | Manter proteção defensiva para integridade de personagens migrados. |
| `Race.java`, `TribeClass.java`, `StatEnum.java`, `WorldMapType.java`, `SkillTreeData.java`, `SkillLearnTemplate.java`, `EmotionLearnAction.java`, `SM_ATTACK_STATUS.java` | Comentários, enums, comentários de `since 4.8` e tribos/mapas/estatísticas da geração 4.8 usados como base estrutural. | Revisar item por item em conformidade com os IDs oficiais do `Game.dll` e `data/static_data` Classic 5.0. |

### 2.3 Serviços de Recompensa Originários da Beyond Aion (Mensagens Originais Preservadas)
Os quatro serviços abaixo preservam a implementação e strings de remetente/mensagem herdados da base **Beyond Aion** (`"Beyond Aion"` / `"Enjoy your stay on Beyond Aion!"`):

- `game-server-gameforge/src/com/aionemu/gameserver/services/BonusPackService.java` (`L57-60`)
- `game-server-gameforge/src/com/aionemu/gameserver/services/FactionPackService.java` (`L68-70`)
- `game-server-gameforge/src/com/aionemu/gameserver/services/reward/StarterKitService.java` (`L17, L68-72`)
- `game-server-gameforge/src/com/aionemu/gameserver/services/reward/VeteranRewardService.java` (`L473-476`)

**Decisão de auditoria:** Em estrita observância à regra de **não realizar substituições indiscriminadas** e de **preservar código funcional e créditos históricos**, esses serviços não foram alterados automaticamente nesta higienização. Ajustes de conteúdo/regras nesses sistemas de recompensa devem ser feitos individualmente conforme o alinhamento específico do projeto ao PvE oficial Gameforge GSID 1.

---

## 3. Recomendações de Continuidade para Contribuidores

1. Sempre consultar os opcodes oficiais mapeados em `Ferramentas e Documentos/Opcodes Oficiais - Classic 5.0/` e os relatórios de auditoria antes de modificar pacotes com marcação `PENDENTE_DE_COMPROVACAO` ou `4.8 retail residue`.
2. Evitar limpeza em lote de enums em `TribeClass`, `DialogAction`, `WorldMapType` ou `StatEnum` sem validação completa das referências em `data/static_data/` e testes automatizados.
3. Nunca reabilitar `BaseService`, `VortexService`, `WorldRaidService`, `HousingService` ou `SM_ATREIAN_PASSPORT` sem evidência concreta de existência no cliente **Aion Classic 5.0 Oficial EU**.
