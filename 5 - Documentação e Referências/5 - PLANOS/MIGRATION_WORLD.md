# MIGRATION_WORLD.md — Fase 10: Módulo `world`

## Resumo

Modernização estrutural e eliminação integral de Javolution (`FastMap`, `FastList`) no motor de particionamento espacial, visibilidade e gerenciamento de mundo (`world`), alinhando containers de entidades (`PlayerContainer`, `LegionMemberContainer`, `LegionContainer`), malhas e regiões espaciais (`MapRegion`, `World`, `WorldMap`, `WorldMapInstance`), sistema de visibilidade e proximidade (`KnownList`) e subsistema de zonas (`ZoneService`, `ZoneInstance`, `SiegeZoneInstance`, `ZoneName`, `MaterialZoneHandler`) para as coleções concorrentes nativas do Java 25 LTS (`ConcurrentHashMap`, `CopyOnWriteArrayList`, `ConcurrentHashMap.newKeySet()`), garantindo zero erros e compilação limpa no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise do Pacote `world`

O pacote `com.aionemu.gameserver.world` é o coração do servidor de jogo, responsável por:
1. Armazenar e indexar todos os objetos vivos e estáticos do jogo (`World`, `MapRegion`).
2. Rastreamento e particionamento espacial de entidades em células geográficas vizinhas (`MapRegion.neighbours`).
3. Detecção e notificação contínua de objetos no campo de visão (`KnownList`).
4. Gerenciamento de canais e instâncias dinâmicas de mapas (`WorldMap`, `WorldMapInstance`).
5. Gerenciamento de zonas de combate, colisão, material e cercos (`zone`).
6. Containers globais de jogadores e legiões (`PlayerContainer`, `LegionContainer`, `LegionMemberContainer`).

Todos os sistemas e comportamentos exclusivos do Classic 5.0 (como o suporte à nova classe Revenant e pontos de spawn em Telos em `World.java`, além dos handlers de instâncias dinâmicas `WorldEngine`) foram rigorosamente preservados.

---

## Alterações Realizadas (13 arquivos no módulo + 2 externos)

| Arquivo / Pacote | Alteração Realizada |
|---|---|
| `world.container.PlayerContainer.java` | Substituição de `FastMap<Integer, Player>` e `FastMap<String, Player>` por `ConcurrentHashMap`. Modernização de `doOnAllPlayers` para iterar diretamente sobre `playersById.values()`. Expurgo total de `javolution.util.FastMap`. |
| `world.container.LegionMemberContainer.java` | Substituição de `FastMap` em `legionMemberById`, `legionMemberExById` e `legionMemberExByName` por `ConcurrentHashMap`. Expurgo total de `javolution.util.FastMap`. |
| `world.container.LegionContainer.java` | Substituição de `FastMap` por `ConcurrentHashMap`. Alteração do retorno de `getAllLegions()` de `FastList<Legion>` para `List<Legion>` (`ArrayList`). Expurgo total de `javolution.util.FastList` e `javolution.util.FastMap`. |
| `network.aion.serverpackets.S_GUILD_LIST.java` | Substituição do tipo de parâmetro e campo de `FastList<Legion>` para `List<Legion>`. Expurgo total de `javolution.util.FastList`. |
| `services.legion.GuildSearchService.java` | Substituição de `FastList<Legion>` por `List<Legion>` (`ArrayList<Legion>`). Expurgo total de `javolution.util.FastList`. |
| `world.knownlist.KnownList.java` | Substituição de `knownObjects`, `knownPlayers`, `visualObjects` e `visualPlayers` por `ConcurrentHashMap`. Modernização de `findVisibleObjects`, `doOnAllNpcs`, `doOnAllNpcsWithOwner`, `doOnAllPlayers` e `doOnAllObjects` para iteração nativa sobre `.values()`. Expurgo total de `javolution.util.FastMap`. |
| `world.MapRegion.java` | Substituição de `objects` e `zoneMap` por `ConcurrentHashMap`. Modernização dos loops de zona (`revalidateZones`, `getZones`, `onDie`, `isInsideZone`, `isInsideItemUseZone`) para iterar sobre `.values()` e `.entrySet()`. Otimização de `createZoneMap` com `computeIfAbsent`. Expurgo total de `javolution.util.FastMap`. |
| `world.World.java` | Substituição de `allObjects` e `allNpcs` por `ConcurrentHashMap`. Substituição de `FastList<SiegeNpc>` em `localSiegeNpcs` por `ConcurrentLinkedQueue<SiegeNpc>`. Modernização de `doOnAllObjects` para iterar sobre `allObjects.values()`. Expurgo total de `javolution.util.FastList` e `javolution.util.FastMap`. |
| `world.WorldMap.java` | Substituição do mapa de `instances` por `ConcurrentHashMap`. Expurgo total de `javolution.util.FastMap`. |
| `world.WorldMapInstance.java` | Substituição de `worldMapObjects` e `worldMapPlayers` por `ConcurrentHashMap`. Substituição de `registeredObjects` por `ConcurrentHashMap.newKeySet()`. Substituição de `questIds` por `CopyOnWriteArrayList<Integer>` e retorno de `List<Integer>` em `getQuestIds()`. Expurgo total de `javolution.util.FastList` e `javolution.util.FastMap`. |
| `world.zone.handler.MaterialZoneHandler.java` | Substituição de `FastMap<Integer, IActor> observed` por `ConcurrentHashMap<Integer, IActor>`. Expurgo total de `javolution.util.FastMap`. |
| `world.zone.SiegeZoneInstance.java` | Substituição de `FastMap<Integer, Player> players` por `ConcurrentHashMap<Integer, Player>`. Modernização de `doOnAllPlayers` iterando sobre `players.values()`. Expurgo total de `javolution.util.FastMap`. |
| `world.zone.ZoneInstance.java` | Substituição de `Map<Integer, Creature> creatures = new FastMap<>()` por `ConcurrentHashMap`. Expurgo total de `javolution.util.FastMap`. |
| `world.zone.ZoneName.java` | Substituição de `FastMap<String, ZoneName> zoneNames` por `ConcurrentHashMap<String, ZoneName>`. Otimização atômica de `createOrGet` com `computeIfAbsent`. Expurgo total de `javolution.util.FastMap`. |
| `world.zone.ZoneService.java` | Substituição de `FastMap<ZoneName, ZoneHandler> collidableHandlers` por `ConcurrentHashMap<ZoneName, ZoneHandler>`. Expurgo total de `javolution.util.FastMap`. |

---

## Estatísticas da Fase 10

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `world` | 21 | **21** |
| Referências a `javolution` no pacote `world` | 17 (em 13 arquivos) | **0 (Zero)** |
| Coleções concorrentes Java 25 integradas | 0 | **17 (`ConcurrentHashMap`, `ConcurrentLinkedQueue`, `newKeySet`, `CopyOnWriteArrayList`)** |
| Compilação Maven (Java 25) | - | **BUILD SUCCESS** (6/6 módulos) |
