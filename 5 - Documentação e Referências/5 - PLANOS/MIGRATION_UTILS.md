# MIGRATION_UTILS.md — Fase 11: Módulo `utils`

## Resumo

Modernização estrutural e eliminação integral de Javolution (`FastMap`, `FastList`) no módulo de utilitários centrais (`utils`), alinhando processamento de comandos de chat administrativo e de jogadores (`ChatProcessor`), serviço de auditoria e monitoramento de Game Masters (`GMService`) e funções utilitárias do sistema (`Util`) para as coleções concorrentes e nativas do Java 25 LTS (`ConcurrentHashMap`, `ArrayList`), garantindo zero erros e compilação limpa no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise do Pacote `utils`

O pacote `com.aionemu.gameserver.utils` e seus 12 subpacotes fornecem serviços transversais essenciais:
1. **Chat & Comandos**: `ChatProcessor`, `ChatUtil`, processamento dinâmico de comandos `//` (admin) e `.` (player).
2. **Auditoria & GMs**: `GMService`, alertas de entrada de GM e transmissão global de avisos.
3. **Cálculos Matemáticos & Geometria**: `MathUtil`, `PositionUtil`, `SafeMath`, `Point2D`, `Point3D`, ângulos 3D e detecção espacial de alvos.
4. **Concorrência & Tarefas**: `ThreadPoolManager`, pools de execução instantânea, agendada e de longa duração.
5. **Caching & Coleções**: Subpacote `collections` com caches fracos/suaves (`AbstractCacheMap`, `CacheMapFactory`, `LastUsedCache`).
6. **Tempo de Jogo & Ranks**: Subpacotes `gametime`, `rates`, `stats` (AP, XP, Abyss Rank, XP loss).
7. **Segurança & Rede**: `PacketSendUtility`, `IdUtils`, `IDFactory`, `CAPTCHAUtil`, `DDSConverter`.

Todos os sistemas e comportamentos exclusivos do Classic 5.0 foram rigorosamente preservados.

---

## Alterações Realizadas (3 arquivos modernizados)

| Arquivo / Pacote | Alteração Realizada |
|---|---|
| `utils.Util.java` | Substituição de `FastList<Integer>` no método `stringToIntList` por `ArrayList<Integer>`. Expurgo total de `javolution.util.FastList`. |
| `utils.chathandlers.ChatProcessor.java` | Substituição de `FastMap<String, ChatCommand>` e `FastMap<String, Byte>` por `ConcurrentHashMap`. Substituição de `new FastMap<String, ChatCommand>(commands)` em `reload()` por `new ConcurrentHashMap<>(commands)`. Expurgo total de `javolution.util.FastMap`. |
| `utils.audit.GMService.java` | Substituição de `FastMap<Integer, Player> gms` por `ConcurrentHashMap<Integer, Player>`. Expurgo total de `javolution.util.FastMap`. |

---

## Estatísticas da Fase 11

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `utils` e subpacotes | 49 | **49** |
| Referências a `javolution` no pacote `utils` | 7 (em 3 arquivos) | **0 (Zero)** |
| Coleções nativas e concorrentes integradas | 0 | **4 (`ConcurrentHashMap`, `ArrayList`)** |
| Compilação Maven (Java 25) | - | **BUILD SUCCESS** (6/6 módulos) |
