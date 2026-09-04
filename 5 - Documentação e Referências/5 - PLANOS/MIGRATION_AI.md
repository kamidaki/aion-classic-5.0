# MIGRATION: AI & AI HANDLERS (AION 4.8 RETAIL → AION CLASSIC 5.0 EU)

> **Módulo Principal**: `src/com/aionemu/gameserver/ai`  
> **Módulo de Scripts**: `data/scripts/system/handlers/ai`  
> **Status**: `CONCLUÍDO (CORE & SCRIPTS VALIDADOS)`  
> **Data de Conclusão**: 2026-09-04  
> **Fonte (4.8 Retail)**:  
> - Core: `5 - Documentação e Referências/3 - JAVA EMU - 4.8 RETAIL/game-server/src/com/aionemu/gameserver/ai`  
> - Scripts: `5 - Documentação e Referências/3 - JAVA EMU - 4.8 RETAIL/game-server/data/handlers/ai`  
> **Destino (Classic 5.0)**:  
> - Core: `1 - Código Fonte [Emulador]/GameServer/src/com/aionemu/gameserver/ai`  
> - Scripts: `1 - Código Fonte [Emulador]/GameServer/data/scripts/system/handlers/ai`  
> **Capturas de Referência**: `5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0`  

---

## 1. Objetivo

Migrar e aperfeiçoar todo o ecossistema de Inteligência Artificial do AION 4.8 Retail para o AION Classic 5.0 EU (Java 25 LTS). O objetivo é incorporar a máquina de estados refinada, concorrência aprimorada, guardas de recursão em eventos (`DEPTH` check com `ThreadLocal`), gerenciamento de combate e rotinas de movimento e patrulha do 4.8, preservando integralmente o protocolo, o ciclo de vida e os mais de 7.000 scripts de AI do Classic 5.0.

---

## 2. Regras Críticas e Diretrizes de Compatibilidade

1. **Separação em Duas Etapas**:
   - **Etapa 1 (Core AI)**: `src/com/aionemu/gameserver/ai` migrado primeiro via "Replace, DO NOT merge" e adaptado para compilar 100% no Java 25.
   - **Etapa 2 (Handlers AI)**: `data/scripts/system/handlers/ai` processado **após** a conclusão da Etapa 1.
2. **Preservação Absoluta das AIs Exclusivas do Classic 5.0**:
   - Total de scripts auditados: **7.102 scripts** no Classic 5.0 e **461 scripts** no 4.8 Retail.
   - Apenas os **29 scripts comuns** foram atualizados e enriquecidos com recursos do 4.8.
   - Todos os **7.073 scripts exclusivos** do Classic 5.0 foram preservados intactos.
3. **Compatibilidade Dupla de Construtores (No-Arg + Owner-Arg)**:
   - `AbstractAI`, `AITemplate` e `NpcAI` implementam suporte a ambos os construtores:
     - `public AbstractAI() {}` com `setOwner(Creature owner)`
     - `public AbstractAI(T owner) { this.owner = owner; }`
   - O `AIEngine.setupAI(...)` foi adaptado para inspecionar e suportar ambos os modos de instanciação por reflexão.
4. **Métodos Exigidos pelo Classic 5.0**:
   - `AI.java` e `AbstractAI.java` mantiveram:
     - `int modifyDamage(int damage)`
     - `int modifySensoryRange(int value)`
     - `int modifyHealValue(int value)`
     - `int modifyMaccuracy(int value)`
     - `long getRemainigTime()`
     - `void onIndividualNpcEvent(Creature npc)`
     - `boolean poll(AIQuestion question)`
5. **Classes Pontes Requeridas por Outros Módulos**:
   - `ai.eventcallback`: `OnDieEventListener`, `OnDieEventCallback`, `OnHandleAIGeneralEvent`.
   - `AISummon.java` (adaptado com tipos genéricos ajustados).
   - `StateEvents.java`.
   - `AiNames.java` e `handler.SimpleAbyssGuardHandler.java`.
   - `ai.poll`: `AIAnswer.java`, `AIAnswers.java`, `NpcAIPolls.java`, `SimpleAIAnswer.java`.
   - `ai.scenario`: `AIScenario.java`, `AIScenarios.java`, `ScenarioTemplate.java`, `WalkScenario.java`.
6. **Inicialização do `AIEngine`**:
   - Implementa `GameEngine` com `load(CountDownLatch progressLatch)` e `shutdown()`.
   - Lê `./data/scripts/system/aihandlers.xml`.

---

## 3. Inventário de Classes do Módulo `src/com/aionemu/gameserver/ai`

### Classes Principais
- [x] `AI.java` — Interface central de Inteligência Artificial.
- [x] `AbstractAI.java` — Classe base com concorrência, `ThreadLocal DEPTH` e ciclo de eventos.
- [x] `AIActions.java` — Ações utilitárias de IA.
- [x] `AIEngine.java` — Motor de carregamento e instanciação de AIs.
- [x] `AIHandlerClassListener.java` — Listener de carregamento de classes de script de IA.
- [x] `AILogger.java` — Logger de depuração de eventos de IA.
- [x] `AIName.java` — Anotação de identificação de IA para NPCs.
- [x] `AiNames.java` — Enum de nomes padrão de IA do Classic 5.0.
- [x] `AIRequest.java` — Solicitações de estado e transição de IA.
- [x] `AIState.java` — Estados da máquina de IA (com `canHandle` e novos estados 4.8).
- [x] `AISubState.java` — Subestados operacionais de IA.
- [x] `AISummon.java` — Template especializado para invocações de cerco.
- [x] `AITemplate.java` — Template base para criação de scripts de IA.
- [x] `AttackIntention.java` — Intenção de ataque (simples, skill, combo).
- [x] `GeneralAIEvent.java` — Eventos genéricos para listeners.
- [x] `HpPhases.java` — Gerenciador de fases de HP para chefes (incorporado do 4.8).
- [x] `NpcAI.java` — IA padrão para entidades NPC.
- [x] `StateEvents.java` — Conjuntos canônicos de eventos por estado do Classic 5.0.

### Subdiretório: `ai/event/`
- [x] `AIEventLog.java` — Buffer circular de registro de eventos recentes.
- [x] `AIEventType.java` — Enum de tipos de eventos despachados para IA.
- [x] `AIListenable.java` — Interface para AIs que suportam ouvintes de eventos.

### Subdiretório: `ai/eventcallback/`
- [x] `OnDieEventCallback.java` — Callback acionado na morte de criatura.
- [x] `OnDieEventListener.java` — Ouvinte de evento de morte (usado por `SiegeBossDeathListener`).
- [x] `OnHandleAIGeneralEvent.java` — Ouvinte de eventos genéricos.

### Subdiretório: `ai/follow/`
- [x] `FollowStartService.java` — Serviço de seguimento de alvo com verificação de alcance.
- [x] `FollowSummonTaskAI.java` — Tarefa agendada para acompanhamento de invocações.

### Subdiretório: `ai/handler/`
- [x] `ActivateEventHandler.java` — Manipulador de evento de ativação.
- [x] `AggroEventHandler.java` — Manipulador de aggro, auxílio e ódio.
- [x] `AttackEventHandler.java` — Manipulador de ataques recebidos e deferidos.
- [x] `CreatureEventHandler.java` — Manipulador de eventos de criaturas próximas.
- [x] `DiedEventHandler.java` — Manipulador de morte e limpeza de estado.
- [x] `FollowEventHandler.java` — Manipulador de seguimento de alvos.
- [x] `FreezeEventHandler.java` — Manipulador de congelamento / pausa de IA.
- [x] `MoveEventHandler.java` — Manipulador de percursos e validação de movimento.
- [x] `ReturningEventHandler.java` — Manipulador de retorno ao ponto de spawn/origem.
- [x] `ShoutEventHandler.java` — Manipulador de gritos e falas de NPCs.
- [x] `SimpleAbyssGuardHandler.java` — Manipulador de guardas de fortaleza e abismo.
- [x] `SpawnEventHandler.java` — Manipulador de pós-spawn de NPCs.
- [x] `TalkEventHandler.java` — Manipulador de diálogos de jogadores.
- [x] `TargetEventHandler.java` — Manipulador de troca e perda de alvo.
- [x] `ThinkEventHandler.java` — Ciclo de processamento e tomada de decisão de IA.

### Subdiretório: `ai/manager/`
- [x] `AttackManager.java` — Gerenciador de ciclo de ataque.
- [x] `EmoteManager.java` — Gerenciador de animações e emoções.
- [x] `FollowManager.java` — Gerenciador de proximidade em perseguição.
- [x] `SimpleAttackManager.java` — Gerenciador de ataque básico.
- [x] `SkillAttackManager.java` — Gerenciador de uso de habilidades e cooldowns de IA.
- [x] `WalkManager.java` — Gerenciador de navegação e rotas de patrulha.

### Subdiretórios de Suporte: `ai/poll/` e `ai/scenario/`
- [x] `AIAnswer.java`, `AIAnswers.java`, `AIQuestion.java`, `NpcAIPolls.java`, `SimpleAIAnswer.java`
- [x] `AIScenario.java`, `AIScenarios.java`, `ScenarioTemplate.java`, `WalkScenario.java`

---

## 4. Inventário e Adaptação dos Scripts em `data/scripts/system/handlers/ai`

1. **AIs Existentes em Ambos (29 scripts atualizados com sucesso)**:
   - Raiz: `ActionItemNpcAI`, `AggressiveNpcAI`, `BombAi`, `BookAI`, `ChestAI`, `DeliveryManAI`, `FollowingNpcAI`, `GeneralNpcAI`, `HomingNpcAI`, `KiskAI`, `NoActionAI`, `PostboxAI`, `ResurrectAI`, `ServantNpcAI`, `SkillAreaNpcAI`, `SummonerAI`, `TrapNpcAI`.
   - Instâncias: `AbyssalSplinter` (`EbonsoulAI`, `Kaluva_SpawnerAI`, `Kaluva_The_Fourth_FragmentAI`, `Luminous_WaterwormAI`, `PazuzuAI`, `RukrilAI`, `YamennesAI`), `AdmaStronghold` (`Acid_CloudAI`, `Captain_MundirveAI`, `Lord_LannokAI`, `Princess_KaremiwenAI`, `Suspicious_BoyAI`), `AetherogeneticsLab` (`RM_78CAI`).
2. **AIs Exclusivas do Classic 5.0 (7.073 scripts preservados intactos)**:
   - `AbsoluteAI`, `DummyAI`, `Illusion_GateAI`, `InvisibleNpcAI`, `MercenaryAI`, `OneDmgPerHitAI`, `QuestItemNpcAI`.
   - Todas as centenas de scripts em `portals/`, `siege/`, `walkers/`, `instance/`.
   - Todas as 6.902 AIs em `worlds/`.

---

## 5. Resultados e Validação

- **Compilação do Core AI**: `mvn compile` no Java 25 concluído com sucesso.
- **Compilação dos Scripts Comuns (29/29)**: Compilação via `javac` com zero erros e zero warnings de incompatibilidade.
- **Compilação em Massa de Todos os Scripts (7.102/7.102)**: Script `compile_all_ai.py` executou `javac` nos 7.102 scripts com **ZERO ERROS**.
- **Build Completo do Servidor**: Pipeline Maven empacotou GameServer e LoginServer com sucesso.

---

## 6. Critérios de Aceitação (Definition of Done)

- [x] `src/com/aionemu/gameserver/ai` anterior substituído e 4.8 migrado.
- [x] Compatibilidade de construtor duplo garantida para todos os scripts existentes.
- [x] Dependências de rede, pacotes e métodos Classic 5.0 adaptadas.
- [x] Scripts comuns em `handlers/ai` atualizados da referência 4.8.
- [x] Todos os 7.073 scripts exclusivos do Classic 5.0 preservados intactos.
- [x] Compilação integral com sucesso (`BUILD SUCCESS`) no Java 25.
- [x] Pipeline `build-server.bat` / Maven clean package validado.
- [x] Diff do Git inspecionado e limpo.
- [x] Commit e Push realizados em Português.
- [x] Documentação de rastreamento e Roadmap Mestre atualizados.
