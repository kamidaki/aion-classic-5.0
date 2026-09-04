# MIGRATION_SERVICES.md — Fase 12: Módulo `services`

## Resumo

Modernização arquitetural e eliminação integral de Javolution (`FastMap`, `FastList`, `FastSet`) no módulo central de lógica de negócios do emulador (`services` e 24 subpacotes), migrando todas as coleções legadas para as estruturas concorrentes e nativas do Java 25 LTS (`ConcurrentHashMap`, `CopyOnWriteArrayList`, `ArrayList`, `ConcurrentHashMap.newKeySet()`). Foram preservados integralmente todos os sistemas exclusivos do Classic 5.0 (Battle Pass, Daeva Pass, Telos, Revenant, Tiak Research Base, Shugo Sweep, novos formatos de pacote S_*, entre outros).  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Sub-domínios Modernizados (37 arquivos alterados)

### Sub-domínio A: Serviços de Jogador, Social e Recompensas
1. `services.player.BattlePassService`: Substituição de `FastList` e `FastMap` por `CopyOnWriteArrayList`, `ArrayList` e `ConcurrentHashMap` para armazenamento concorrente das temporadas, recompensas e dados de Battle Pass/Daeva Pass.
2. `services.player.EventWindowService`: `FastList<Player>` substituído por `CopyOnWriteArrayList<Player>`.
3. `services.player.ShugoSweepService`: `FastList<PlayerSweep>` substituído por `ArrayList<PlayerSweep>`.
4. `services.player.PlayerLimitService`: `FastMap` substituído por `ConcurrentHashMap` e remoção de `putEntry`.
5. `services.reward.RewardService`: `FastList` substituído por `List` / `ArrayList`.
6. `dao.RewardServiceDAO`: Assinatura abstrata migrada de `FastList` para `List<RewardEntryItem>`.
7. `services.FindGroupService`: `FastMap` substituído por `ConcurrentHashMap`.
8. `services.DuelService`: `FastMap` substituído por `ConcurrentHashMap`.
9. `services.AdminService`: `FastList` substituído por `CopyOnWriteArrayList`.
10. `services.AnnouncementService`: `FastSet` substituído por `ConcurrentHashMap.newKeySet()`.
11. `services.legion.LegionService`: Expurgo de import não utilizado de `FastList`.

### Sub-domínio B: Serviços de Economia, Mercado e Itens
12. `services.BrokerService`: 5 mapas concorrentes `FastMap` substituídos por `ConcurrentHashMap`.
13. `services.WebshopService`: `FastList` substituído por `ArrayList` e remoção de chamadas legadas `.recycle()`.
14. `dao.WebShopDAO`: Assinatura abstrata migrada de `FastList` para `List<WebShopPackageItem>`.
15. `database.mysql5.MySQL5WebShopDAO`: Implementação JDBC migrada de `FastList` para `ArrayList`.
16. `services.LimitedItemTradeService`: `FastMap` substituído por `ConcurrentHashMap`.
17. `services.drop.DropRegistrationService`: `FastMap` e `FastList` substituídos por `ConcurrentHashMap` e `ArrayList`.
18. `services.PeriodicSaveService`: Expurgo de import legado de `FastList`.

### Sub-domínio C: Serviços de Instâncias, Grupos e Combate PvP
19. `services.instance.InstanceService`: `FastList` substituído por `CopyOnWriteArrayList`.
20. `services.AutoGroupService`: `FastMap` e `FastList` substituídos por `ConcurrentHashMap` e `CopyOnWriteArrayList`.
21. `services.instance.DredgionService`: `FastList` substituído por `CopyOnWriteArrayList`.
22. `services.instance.TiakResearchBaseService`: `FastList` substituído por `CopyOnWriteArrayList`.
23. `services.PvpService`: `FastMap` substituído por `ConcurrentHashMap`.
24. `services.KiskService`: `FastMap` substituído por `ConcurrentHashMap`.
25. `services.CuringZoneService`: `FastList` substituído por `CopyOnWriteArrayList`.
26. `services.MotionLoggingService`: `FastMap` substituído por `ConcurrentHashMap`.

### Sub-domínio D: Serviços de Rifts, Cerco e Abyss
27. `services.RiftService`: `FastMap` substituído por `ConcurrentHashMap` e chamada `activeRifts.putEntry` migrada para `put`.
28. `services.rift.RiftInformer`: `FastMap` substituído por `Map`/`HashMap` e chamadas `putEntry` migradas para `put`.
29. `network.aion.serverpackets.S_WORLD_INFO`: Assinatura do construtor e campo interno migrados de `FastMap` para `Map<Integer, Integer>`.
30. `services.InstanceRiftService`: `FastMap` substituído por `ConcurrentHashMap`.
31. `services.SiegeService`: Expurgo de `javolution.util.*`, mapas ativos migrados para `ConcurrentHashMap`, mapas locais para `HashMap` e lista `assembledParts` para `ArrayList`.
32. `services.siegeservice.SiegeRaceCounter`: `FastMap` substituído por `ConcurrentHashMap`.
33. `services.siegeservice.BalaurAssaultService`: `FastMap` substituído por `ConcurrentHashMap`.
34. `services.ShieldService`: `sphereShields` e `registeredShields` migrados de `FastMap` para `ConcurrentHashMap`.
35. `services.SerialKillerService`: `serialKillers`, `worldKillers` e `handledWorlds` migrados para `ConcurrentHashMap`; `getWorldKillers` reescrito com `computeIfAbsent` thread-safe.
36. `services.SurveyService`: `activeItems` migrado para `ConcurrentHashMap`, `players` para `ArrayList` e imports de logger configurados.
37. `services.abyss.AbyssRankingCache`: `FastMap` substituído por `ConcurrentHashMap`.

---

## Estatísticas da Fase 12

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos modificados no módulo `services` e acoplados | 37 | **37** |
| Referências a `javolution` no pacote `services` | ~60 (em 33 classes) | **0 (Zero)** |
| Estruturas de dados concorrentes integradas | 0 | **`ConcurrentHashMap`, `CopyOnWriteArrayList`, `ConcurrentHashMap.newKeySet()`** |
| Compilação Maven (Oracle JDK 25.0.2) | - | **BUILD SUCCESS** (6/6 módulos em 19.390s) |
| Compatibilidade Classic 5.0 (Revenant, Telos, Battle Pass, Tiak, Opcodes) | Preservada | **100% Preservada** |
