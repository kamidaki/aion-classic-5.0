# MIGRATION_SPAWNENGINE.md — Fase 8: Módulo `spawnengine`

## Resumo

Modernização estrutural e eliminação integral de Javolution (`FastMap`, `FastList`) no motor de spawn (`spawnengine`), alinhando as coleções de spawns temporários (`TemporarySpawnEngine`) à concorrência nativa do Java 25 LTS (`CopyOnWriteArrayList`, `ConcurrentHashMap`) e garantindo zero erros e compilação limpa no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise do Pacote `spawnengine`

- **Estrutura do Módulo (14 arquivos Java)**:
  - `ClusteredNpc.java`: Agrupamento de NPCs com distância e detecção.
  - `InstanceWalkerFormations.java`: Formações de patrulha para instâncias dinâmicas.
  - `SpawnEngine.java`: Gerenciamento central de spawn (instâncias, rifts, sieges, handlers).
  - `SpawnHandlerType.java`: Enum de tipos de handler (`RIFT`, `STATIC`).
  - `StaticDoorSpawnManager.java`: Gerenciamento de portas estáticas e estados de portas em instâncias.
  - `StaticObjectSpawnManager.java`: Gerenciamento de objetos estáticos e caixas de suprimentos/pontos interativos.
  - `TemporarySpawnEngine.java`: Spawns temporários baseados em horários de jogo (`GameTime.onHourChange()`) e inicialização (`GameServer.spawnAll()`).
  - `VisibleObjectSpawner.java`: Instanciação e spawn de entidades visíveis (`Npc`, `Gatherable`, `Trap`, `Portal`, etc.).
  - `WalkerFormationsCache.java`: Cache thread-safe de formações de rota.
  - `WalkerFormator.java`: Cálculo geométrico e posicionamento de membros em formação de patrulha.
  - `WalkerGroup.java`: Gerenciamento dinâmico de grupos de patrulha, velocidades sincronizadas e pontos de destino.
  - `WalkerGroupShift.java`: Deslocamento angular e offsets de formação.
  - `WalkerGroupType.java`: Tipos de formação de patrulha (`SQUARE`, `CIRCLE`, `LINE`, etc.).
  - `WorldWalkerFormations.java`: Formações de rota de mundo aberto persistentes.

---

## Alterações Realizadas

| Arquivo / Pacote | Alteração Realizada |
|---|---|
| `spawnengine.TemporarySpawnEngine.java` | Substituição de `FastList<SpawnGroup>` por `CopyOnWriteArrayList<SpawnGroup>`. Substituição de `FastMap<SpawnGroup, HashSet<Integer>>` por `ConcurrentHashMap<SpawnGroup, Set<Integer>>`. Otimização de `addSpawnGroup` utilizando `addIfAbsent` e `computeIfAbsent(spawn, _ -> ConcurrentHashMap.newKeySet()).add(instanceId)`. Expurgo total dos imports `javolution.util.FastList` e `javolution.util.FastMap`. |

---

## Estatísticas da Fase 8

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `spawnengine` | 14 | **14** |
| Referências a `javolution` no pacote `spawnengine` | 2 (em 1 arquivo) | **0 (Zero)** |
| Coleções concorrentes modernizadas | 0 | **2 (`CopyOnWriteArrayList`, `ConcurrentHashMap`)** |
| Compilação Maven (Java 25) | - | **BUILD SUCCESS** (6/6 módulos) |
