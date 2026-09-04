# MIGRATION_TASKMANAGER.md — Fase 9: Módulo `taskmanager`

## Resumo

Modernização estrutural e eliminação integral de Javolution (`FastMap`, `FastList`, `FastSet`) no motor de tarefas periódicas e agendamento (`taskmanager`), alinhando as estruturas do agendador iterativo, filas FIFO de executáveis e tarefas de movimento/expiração para as coleções concorrentes nativas do Java 25 LTS (`ConcurrentHashMap`, `LinkedList`, `ConcurrentHashMap.newKeySet()`), garantindo zero erros e compilação limpa no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise do Pacote `taskmanager`

O pacote `com.aionemu.gameserver.taskmanager` é responsável por gerenciar tarefas assíncronas, ciclos de atualização física de entidades em movimento, difusão concorrente de pacotes de rede, expiração de itens com restrição temporal de troca e timers de shutdown/restart do servidor.

- **Estrutura do Módulo (20 classes Java)**:
  - `AbstractCronTask.java`: Agendador baseado em expressões Quartz/Cron integrado ao banco de dados (`ServerVariablesDAO`).
  - `AbstractFIFOPeriodicTaskManager.java`: Gerenciador FIFO periódico utilizando `AEFastSet` (`LinkedHashSet` SequencedSet do Java 25).
  - `AbstractIterativePeriodicTaskManager.java`: Gerenciador periódico iterativo com conjuntos concorrentes de ativação/pausa.
  - `AbstractPeriodicTaskManager.java`: Base periódica com hooks de inicialização (`GameServer.StartupHook`) e locks de leitura/escrita.
  - `FIFOExecutableQueue.java`: Fila FIFO executável reentrante ligada ao `ThreadPoolManager`.
  - `FIFORunnableQueue.java`: Fila FIFO de Runnables.
  - `FIFOSimpleExecutableQueue.java`: Fila simples executável com deque encadeado thread-safe.
  - `TaskManagerFromDB.java`: Carregamento e despacho de tarefas configuradas dinamicamente no banco MySQL.
  - `parallel/ForEach.java`: Processador de iteração paralela de entidades.
  - `tasks/ExpireTimerTask.java`: Monitor de expiração de timers de entidades (`IExpirable`).
  - `tasks/MoveTaskManager.java`: Atualização de movimento de criaturas e validação de chegada ao destino via polling de IA (`AIQuestion.DESTINATION_REACHED`).
  - `tasks/MovementNotifyTask.java`: Notificação periódica de movimentação para a KnownList e IA de NPCs ao redor.
  - `tasks/PacketBroadcaster.java`: Difusão agregada de pacotes de status, velocidade, HP/MP/FP e ícones de efeitos.
  - `tasks/PlayerBlackcloudTask.java`: Verificação periódica de compras pendentes na loja Webshop Black Cloud.
  - `tasks/PlayerMoveTaskManager.java`: Atualização física de destino de jogadores.
  - `tasks/RestartTask.java`: Contagem regressiva e reinicialização programada do GameServer.
  - `tasks/ShutdownTask.java`: Notificação com mensagens globais amarelas e desligamento seguro do servidor.
  - `tasks/TeamEffectUpdater.java`: Atualização periódica de ícones de efeitos entre membros de grupo/aliança.
  - `tasks/TeamMoveUpdater.java`: Atualização periódica de posições de membros no radar de grupo/aliança.
  - `tasks/TemporaryTradeTimeTask.java`: Controle de tempo limite para trocas temporárias de itens após drops (`S_MESSAGE_CODE`).

---

## Alterações Realizadas (6 arquivos)

| Arquivo / Pacote | Alteração Realizada |
|---|---|
| `taskmanager.AbstractIterativePeriodicTaskManager.java` | Substituição de `FastSet<T>` por `ConcurrentHashMap.newKeySet()` em `startList`, `stopList` e `activeTasks`. Modernização do loop de execução em `run()` substituindo a iteração manual de nós `FastSet.Record` por loop foreach `for (final T task : activeTasks)`. Expurgo total de `javolution.util.FastSet`. |
| `taskmanager.FIFOSimpleExecutableQueue.java` | Substituição de `FastList<T>` por `LinkedList<T>` sincronizada, preservando os métodos `addLast`, `addAll`, `remove(T)`, `isEmpty` e `removeFirst`. Expurgo total de `javolution.util.FastList`. |
| `taskmanager.tasks.ExpireTimerTask.java` | Substituição de `FastMap<IExpirable, Player>` por `ConcurrentHashMap<IExpirable, Player>`. Otimização funcional de `removePlayer` via `expirables.values().removeIf(p -> p == player)`. Expurgo total de `javolution.util.FastMap`. |
| `taskmanager.tasks.MoveTaskManager.java` | Substituição de `FastMap<Integer, Creature>` por `ConcurrentHashMap<Integer, Creature>`. Substituição de `FastList<Creature>` por `ArrayList<Creature>` em `arrivedCreatures` e `followingCreatures`. Remoção do ciclo de reciclagem obsoleto `FastList.recycle()`. Expurgo total de `javolution.util.FastList` e `javolution.util.FastMap`. |
| `taskmanager.tasks.PlayerMoveTaskManager.java` | Substituição de `FastMap` raw compartilhado por `Map<Integer, Creature> movingPlayers = new ConcurrentHashMap<>()`. Modernização de `run()` utilizando `for (Creature player : this.movingPlayers.values())`. Expurgo total de `javolution.util.FastMap`. |
| `taskmanager.tasks.TemporaryTradeTimeTask.java` | Substituição de `FastMap<Item, Collection<Integer>>` e `FastMap<Integer, Item>` por `ConcurrentHashMap`. Utilização de `Iterator` seguro com `it.remove()` na exclusão de itens expirados durante `run()`. Preservação integral dos pacotes de rede Classic 5.0 `S_MESSAGE_CODE`. Expurgo total de `javolution.util.FastMap`. |

---

## Estatísticas da Fase 9

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `taskmanager` | 20 | **20** |
| Referências a `javolution` no pacote `taskmanager` | 7 (em 6 arquivos) | **0 (Zero)** |
| Coleções concorrentes Java 25 integradas | 0 | **7 (`ConcurrentHashMap`, `LinkedList`, `newKeySet`)** |
| Compilação Maven (Java 25) | - | **BUILD SUCCESS** (6/6 módulos) |
