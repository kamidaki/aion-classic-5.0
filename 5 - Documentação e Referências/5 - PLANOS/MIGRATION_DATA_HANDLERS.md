# Relatório de Migração - Fase 13: Data Handlers, Zone/Instance Handlers e Database DAOs

## Visão Geral
- **Objetivo**: Concluir a modernização do ecossistema de scripts e acesso a dados (`data/scripts/system/handlers` e `data/scripts/system/database`) para compatibilidade integral com **Java 25 LTS (Oracle JDK 25.0.2)**, eliminando por completo todas as dependências herdadas do **Javolution** (`FastMap`, `FastList`, nós intrusivos e `.recycle()`).
- **Data de Conclusão**: 04/09/2026
- **Status**: **100% CONCLUÍDO E VALIDADO COM BUILD SUCCESS**

---

## Escopo e Sub-domínios Modernizados

### 1. Sub-domínio A: World Handlers (18 arquivos)
Substituição de `FastList<Npc>` por `ArrayList<Npc>` nativo e expurgo de imports não utilizados em todos os mapas principais do Aion Classic:
- `Poeta.java`
- `Ishalgen.java`
- `Sanctum.java`
- `Pandaemonium.java`
- `Verteron.java`
- `Altgard.java`
- `Eltnen.java`
- `Morheim.java`
- `Heiron.java`
- `Beluslan.java`
- `Brusthonin.java`
- `Theobomos.java`
- `Inggison.java`
- `Gelkmaros.java`
- `Silentera_Canyon.java`
- `Reshanta.java`
- `Telos_Elyos.java` (Zona Classic 5.0 / Revenant)
- `Telos_Asmodians.java` (Zona Classic 5.0 / Revenant)

### 2. Sub-domínio B: Instance & Zone Handlers (14 arquivos)
Substituição de nós intrusivos `FastList.Node<Future<?>>` e coleções legadas por `CopyOnWriteArrayList<Future<?>>` thread-safe, com iteração direta e cancelamento seguro de tasks:
- `Tiak_Research_Base.java` (Instância PvP Classic 5.0)
- `Chantra_Dredgion.java`
- `Baranath_Dredgion.java`
- `Dark_Poeta.java`
- `Beshmundir_Temple.java`
- `Tempus.java`
- `TempusQ.java`
- `Raksang.java`
- `Abyssal_Splinter.java`
- `Telos_Of_The_Forgotten.java`
- `Talocs_Hollow.java`
- `Steel_Rake.java`
- `Fire_Temple.java`
- `AbyssCore.java`: migração de `FastMap` para `ConcurrentHashMap` no observer.

### 3. Sub-domínio C: Admin Commands (2 arquivos)
- `SpawnAssembledNpc.java`: migração de `FastList` para `ArrayList<AssembledNpcPart>`.
- `LegionCommand.java`: migração de `FastList` para `ArrayList<String>` com remoção do método legado `.recycle()`.

### 4. Sub-domínio D: Database Script DAOs & Interfaces (15 arquivos)
Modernização das interfaces em `com.aionemu.gameserver.dao` e implementações MySQL5 em `data/scripts/system/database/mysql5`:
- `InGameShopDAO.java` & `MySQL5inGameShopDAO.java`: `FastMap` -> `Map<Byte, List<IGItem>>` / `ConcurrentHashMap`.
- `InventoryDAO.java` & `MySQL5InventoryDAO.java`: `FastList` -> `Collections.singletonList` / `ArrayList<Item>`.
- `LegionDAO.java` & `MySQL5LegionDAO.java`: `FastList` -> `List<LegionJoinRequest>` / `ArrayList`.
- `SurveyControllerDAO.java` & `MySQL5SurveyControllerDAO.java`: `FastList` -> `List<SurveyItem>` / `ArrayList`.
- `MySQL5CraftCooldownsDAO.java`: `FastMap` -> `Map<Integer, Long>` / `HashMap`.
- `MySQL5PlayerBattlePassDAO.java`: `FastMap` -> `HashMap` para temporadas, recompensas e quests de Battle Pass Classic 5.0.
- `MySQL5PlayerDAO.java`: `FastMap` compartilhado -> `ConcurrentHashMap` para caches de `PlayerCommonData` (id e nome), corrigindo chamadas `putEntry` para `put`.
- `MySQL5PlayerVarsDAO.java`: `FastMap.newInstance()` -> `new HashMap<String, Object>()`.
- `MySQL5PortalCooldownsDAO.java`: `FastMap` -> `ConcurrentHashMap` sincronizado com `PortalCooldownList`.
- `MySQL5PlayerEventsWindowDAO.java`: `FastMap` -> `HashMap` para janelas de eventos.
- `MySQL5AccountBlackCloudDAO.java`: `FastMap`/`FastList` -> `HashMap`/`ArrayList` para cartas e itens do Black Cloud.

---

## Validação e Verificação
- **Varredura de Resíduos**: Busca recursiva em `data/scripts` confirmou **0** ocorrências residuais de `javolution`.
- **Compilação Maven**:
  ```
  Reactor Summary for Aion Classic 5.0 EU Server 5.0-SNAPSHOT:
  Aion Classic 5.0 EU Server ......................... SUCCESS [  0.004 s]
  Aion Commons ....................................... SUCCESS [  1.545 s]
  Aion Classic 5.0 Login Server ...................... SUCCESS [  0.289 s]
  Aion Classic 5.0 Game Server ....................... SUCCESS [ 25.500 s]
  Aion Classic 5.0 Chat Server ....................... SUCCESS [  0.098 s]
  Aion Classic 5.0 - WebSocket Server ................ SUCCESS [  0.077 s]
  BUILD SUCCESS (27.734 s no Oracle JDK 25.0.2)
  ```
