# MIGRATION_QUESTENGINE.md — Fase 5: Módulo `questEngine`

## Resumo

Modernização estrutural do motor de missões (`QuestEngine`), eliminação de 100% dos resíduos de Javolution (`FastMap`) e transição para coleções nativas do Java 25 LTS (`ConcurrentHashMap`, `HashMap`, `Map`), assegurando integridade absoluta com os 13 tipos JAXB estáticos e as centenas de scripts de missões do Classic 5.0 EU (`data/scripts/system/handlers/quest`).  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Estratégia Adotada

1. **Preservação dos Contratos de Scripts 5.0**:
   - No Classic 5.0 EU, os manipuladores de quests estendem `QuestHandler`, que herda de `AbstractQuestHandler`. Toda a hierarquia de métodos auxiliares (`sendUpdatePacket`, `changeQuestStep`, manipulação de diálogos e flags de missão) foi mantida intacta.
2. **Eliminação de Javolution**:
   - 9 arquivos do subdiretório `questEngine` dependiam de `javolution.util.FastMap`. Todos foram migrados para `ConcurrentHashMap` (para gerenciamento concorrente global em tempo de execução) ou `HashMap` (para mapeamentos locais durante a fase de parsing JAXB / registro de templates).
3. **Limpeza e Coerência de Memória**:
   - O método `QuestEngine.clear()` foi atualizado para liberar adicionalmente referências de `dialogMap`, `questOnKillInWorld` e `questOnBonusApply` durante reloads ou paradas do servidor.

---

## Arquivos Modificados (9 arquivos)

| Pacote / Arquivo | Alteração Realizada |
|---|---|
| `questEngine.QuestEngine.java` | Substituição de 8 instâncias de `FastMap` por `ConcurrentHashMap` (`questHandlers`, `questOnEnterZone`, `questOnLeaveZone`, `questOnPassFlyingRings`, `questOnKillRanked`, `questOnKillInWorld`, `dialogMap`, `questOnBonusApply`). Inclusão de limpezas adicionais no método `clear()`. Remoção do import `javolution.*`. |
| `handlers.template.ReportToMany.java` | Campo `npcInfos` e parâmetro do construtor migrados de `FastMap<Integer, NpcInfos>` para `Map<Integer, NpcInfos>`. Remoção do import `javolution.*`. |
| `handlers.models.ReportToManyData.java` | Mapeamento instanciado como `Map<Integer, NpcInfos> = new HashMap<>()`. Remoção do import `javolution.*`. |
| `handlers.template.MonsterHunt.java` | Campo `monsters` e parâmetro do construtor migrados de `FastMap<Monster, Set<Integer>>` para `Map<Monster, Set<Integer>>`. Remoção do import `javolution.*`. |
| `handlers.models.MonsterHuntData.java` | Mapeamento instanciado como `Map<Monster, Set<Integer>> = new HashMap<>()`. Remoção do import `javolution.*`. |
| `handlers.template.MentorMonsterHunt.java` | Parâmetro do construtor migrado de `FastMap<Monster, Set<Integer>>` para `Map<Monster, Set<Integer>>`. Remoção do import `javolution.*`. |
| `handlers.models.MentorMonsterHuntData.java` | Mapeamento instanciado como `Map<Monster, Set<Integer>> = new HashMap<>()`. Remoção do import `javolution.*`. |
| `handlers.template.KillSpawned.java` | Campo `spawnedMonsters` e parâmetro do construtor migrados de `FastMap<List<Integer>, SpawnedMonster>` para `Map<List<Integer>, SpawnedMonster>`. Remoção do import `javolution.*`. |
| `handlers.models.KillSpawnedData.java` | Mapeamento instanciado como `Map<List<Integer>, SpawnedMonster> = new HashMap<>()`. Remoção do import `javolution.*`. |

---

## Estatísticas da Fase 5

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `questEngine` | 53 | **53** |
| Referências a `javolution` no pacote `questEngine` | 9 arquivos | **0 (Zero)** |
| Tipos XML suportados (`XMLQuests.java`) | 13 | **13** (100% preservados) |
| Compatibilidade de scripts existentes | 100% | **100%** |
