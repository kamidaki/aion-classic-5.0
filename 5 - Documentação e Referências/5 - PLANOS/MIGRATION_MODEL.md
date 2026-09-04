# MIGRATION_MODEL.md — Fase 4: Módulo `model`

## Resumo

Migração, modernização e substituição integral de Javolution por coleções Java 25 de alta concorrência no módulo `model` (`GameServer/src/com/aionemu/gameserver/model`), integrando componentes estruturais do 4.8 Retail e preservando 100% dos sistemas exclusivos do Classic 5.0.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Estratégia Adotada

O módulo `model` do Classic 5.0 possui 720 arquivos Java com sistemas exclusivos da versão Classic (Battle Pass, Siel's Energy, Luna System, Wardrobe, Instâncias Tiak, InGameShop), enquanto o 4.8 Retail continha sistemas removidos no Classic (como 33 arquivos de Housing studio/palaces e 16 arquivos de Bases de Katalam).

Conforme o **Princípio 1** do Roadmap ("Prioridade Absoluta do Classic 5.0"), a abordagem executada foi:
1. **Preservação Total da Base 5.0**: Nenhuma mecânica, opcode ou entidade do Classic 5.0 foi descontinuada.
2. **Expurgo Total de Javolution**: Todos os 44 arquivos do 5.0 que ainda utilizavam `FastMap`, `FastList`, `FastSet` foram migrados para coleções nativas do Java 25 (`ConcurrentHashMap`, `CopyOnWriteArrayList`, `ArrayList`, `HashSet`).
3. **Integração de 6 Classes Estruturais do 4.8**: Classes matemáticas, probabilísticas e de estado temporal.
4. **Alinhamento de Compatibilidade nos Chamadores**: 5 pacotes/serviços externos foram ajustados para consumir os tipos padronizados (`List`, `Map`).

---

## Classes Estruturais Integradas do 4.8 (6 arquivos)

| Arquivo | Pacote | Descrição |
|---|---|---|
| `Plane3D.java` | `model.geometry` | Interseção raio-plano em espaço 3D para motor de física e colisão. |
| `Chance.java` | `model` | Interface funcional genérica para sorteio probabilístico ponderado com suporte a remoção. |
| `Expirable.java` | `model` | Interface com default methods Java para controle de expiração de itens e estados. |
| `EventTheme.java` | `model` | Enum com anotações JAXB de temas de eventos (Halloween, Natal, etc.), alinhado a `DespawnableNode`. |
| `CreatureType.java` | `model` | Classificação de criaturas (ATTACKABLE, PEACE, AGGRESSIVE, FRIEND, SUPPORT). |
| `AttendType.java` | `model` | Enum JAXB de tipos de presença/atendimento (DAILY, ANNIVERSARY, CUMULATIVE). |

---

## Eliminação de Javolution (44 arquivos modernizados)

### Sub-domínio A: Armazenamento e Itens (Storage & Items)
- `IStorage.java`: assinatura de `getItemsWithKinah()` padronizada para `List<Item>`.
- `Storage.java`: `FastList` removido, retorno `List<Item>`, eliminação de `recycle()`.
- `ItemStorage.java`: mapa de itens migrado para `ConcurrentHashMap<Integer, Item>`, `getItems()` e `getItemsById()` retornando `List<Item>`.
- `LegionStorageProxy.java`: delegador atualizado para `List<Item>`.
- `DecomposeAction.java`: `FastList` substituído por `ArrayList`.
- `CraftGroup.java`: `FastMap` substituído por `Map / ConcurrentHashMap`.

### Sub-domínio B: Entidades Centrais (Player, Creature, Equipment, Spawns)
- `Creature.java`: `skillCoolDowns` e `skillCoolDownsBase` migrados para `ConcurrentHashMap<Integer, Long>`.
- `Player.java`: `vars`, `itemCoolDowns`, `playerEventWindow`, `playerEquipSettingList`, `playerWardrobe`, `blackcloudLetters` migrados para `ConcurrentHashMap`; `getAllItems()` para `List<Item>`.
- `Equipment.java`: `getEquippedItemsWithoutStigma()` e `getEquippedItemsWithoutStigmaOld()` retornando `List<Item>`.
- `CreatureGameStats.java`: mapa de funções estatísticas migrado para `ConcurrentHashMap<StatEnum, TreeSet<IStatFunction>>` com remoção funcional via `removeIf`.
- `AssembledNpc.java`: `FastList` substituído por `List<AssembledNpcPart>`.
- `SpawnTemplate.java`: `visibleObjects` migrado para `CopyOnWriteArrayList<VisibleObject>`.

### Sub-domínio C: Sub-sistemas do Jogador (Player Sub-systems)
- `CraftCooldownList.java`: `craftCooldowns` migrado para `ConcurrentHashMap<Integer, Long>`.
- `PortalCooldownList.java`: `portalCooldowns` migrado para `ConcurrentHashMap<Integer, PortalCooldownItem>`.
- `Mailbox.java`: `mails` e `reserveMail` migrados para `ConcurrentHashMap<Integer, Letter>`.
- `PetList.java`: `pets` migrado para `ConcurrentHashMap<Integer, PetCommonData>`.
- `QuestStateList.java`: `getAllFinishedQuests()` migrado para `List<QuestState>`.
- `MotionList.java`: `motions` e `activeMotions` migrados para `ConcurrentHashMap<Integer, Motion>`.
- `TitleList.java`: `titles` migrado para `ConcurrentHashMap<Integer, Title>`.
- `PlayerSweep.java`: `rewardCell` migrado para `ArrayList<Integer>`.
- `BattlePassSeason.java` & `PlayerBattlePass.java`: coleções migradas para `ConcurrentHashMap`.

### Sub-domínio D: Contas, Lojas e Trocas
- `Account.java`: removido import não utilizado de `FastMap`.
- `InGameShopEn.java`: `items` e `lastUsage` para `ConcurrentHashMap`, `activeRequests` para `CopyOnWriteArrayList`, `getTopSales()` para `List<Integer>`.
- `LimitedTradeNpc.java`: `limitedItems` migrado para `List<LimitedItem>`.
- `GoodsList.java`: `limitedItems` migrado para `List<LimitedItem>`.
- `Exchange.java`: `itemsToUpdate` migrado para `ArrayList<Item>`.
- `BlackcloudLetter.java`: `attachedItem` migrado para `ArrayList<BlackcloudItem>`.
- `Kisk.java`: `kiskMemberIds` para `ConcurrentHashMap.newKeySet()`, `currentMemberList` para `ArrayList<Player>`.

### Sub-domínio E: Grupos, Legiões e Social
- `PlayerGroup.java`: `groupMembers` migrado para `ConcurrentHashMap<Integer, Player>`.
- `PlayerGroupService.java`: `groupMembers` migrado para `ConcurrentHashMap<Integer, PlayerGroup>`.
- `Legion.java`: `joinRequestMap` migrado para `ConcurrentHashMap<Integer, LegionJoinRequest>`.
- `LootGroupRules.java`: `itemsToBeDistributed` migrado para `CopyOnWriteArrayList<DropItem>`.
- `LookingForParty.java`: `searchInstances` retorno migrado para `ArrayList<SearchInstance>`.

### Sub-domínio F: Siege, Rifts, Instâncias e Movimentação
- `SiegeLocation.java`: `creatures` e `players` migrados para `ConcurrentHashMap`, iteração de visitantes via `players.values()`.
- `SiegeShield.java`: `observed` migrado para `ConcurrentHashMap<Integer, IActor>`.
- `InstanceRiftLocation.java`: `players` migrado para `ConcurrentHashMap<Integer, Player>`.
- `StreamLocations.java`: `location` migrado para `ArrayList<Location2D>`.
- `InstanceReward.java`: `instanceRewards` migrado para `CopyOnWriteArrayList<T>`.
- `DredgionReward.java`: `dredgionRooms` migrado para `List<DredgionRooms>`.
- `PvPArenaReward.java`: `zones` migrado para `List<Integer>`.
- `TiakReward.java`: `tiakRooms` migrado para `List<TiakRooms>`.
- `MotionLog.java`: `motionsForWeapons` migrado para `ConcurrentHashMap<WeaponTypeWrapper, List<SkillTime>>`.
- `ExMaterials.java`: `material` migrado para `ArrayList<Material>`.

---

## Estatísticas Finais da Fase 4

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `model` | 720 | **726** (+6 estruturais) |
| Referências a `javolution` no pacote `model` | 44 arquivos | **0 (Zero)** |
| Tempo de compilação limpa (Maven) | 25.6s | **20.8s** |
| Erros de compilação | 0 | **0** |
| Módulos compilados com sucesso | 6/6 | **6/6** |
