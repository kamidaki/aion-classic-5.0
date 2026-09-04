# MIGRATION: CONTROLLERS (AION 4.8 RETAIL → AION CLASSIC 5.0 EU)

> **Módulo**: `src/com/aionemu/gameserver/controllers`  
> **Status**: `CONCLUÍDO (BUILD SUCCESS - JAVA 25 LTS)`  
> **Data de Início**: 2026-09-04  
> **Data de Conclusão**: 2026-09-04  
> **Fonte (4.8 Retail)**: `5 - Documentação e Referências/3 - JAVA EMU - 4.8 RETAIL/game-server/src/com/aionemu/gameserver/controllers`  
> **Destino (Classic 5.0)**: `1 - Código Fonte [Emulador]/GameServer/src/com/aionemu/gameserver/controllers`  
> **Capturas de Referência**: `5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0`  

---

## 1. Objetivo

Migrar toda a arquitetura de controllers de entidades (criaturas, jogadores, NPCs, invocações, objetos visíveis, combate, observadores, movimento e efeitos) da referência madura do AION 4.8 Retail para o emulador AION Classic 5.0 EU executando nativamente em **Java 25 LTS**.

A concorrência robusta (`ConcurrentHashMap`, `StampedLock`, `AtomicBoolean`), o ciclo de vida aperfeiçoado de invocações e IA do 4.8 foram integrados, respeitando com fidelidade absoluta de 100% o protocolo, opcodes, pacotes `S_*`, identificadores de status unsigned e subsistemas específicos do Classic 5.0.

---

## 2. Regras de Compatibilidade e Decisões Críticas

1. **Protocolo Classic 5.0 / Pacotes Prevalecem**:
   - Pacotes de rede usam o padrão oficial `S_` (`S_ATTACK`, `S_MOVE_NEW`, `S_EMOTION`, `S_ABNORMAL_STATUS`, `S_HIT_POINT_OTHER`, `S_GATHER`, `S_FUNCTIONAL_PET`, `S_CHANGE_PET_STATUS`, `S_MESSAGE_CODE`).
   - `CreatureMoveController`: Emissão de `S_MOVE_NEW` via `PacketSendUtility.broadcastPacket`.
2. **AttackStatus Unsigned IDs**:
   - No 4.8 Retail, o enum `AttackStatus` utilizava bytes assinados negativos (`-64`, `-62`, etc.). No Classic 5.0, o serializador `S_ATTACK` realiza `switch(status.getId())` esperando inteiros positivos sem sinal (192, 194, 196, 202, 209, 211, 213, 215, 219). Os IDs canônicos do Classic 5.0 foram preservados.
3. **Substituição Total ("Replace, DO NOT merge")**:
   - O diretório `controllers` original foi completamente apagado antes da cópia da estrutura 4.8.
4. **Purga de Subsistemas Específicos do 4.8 (Inexistentes no 5.0)**:
   - Removidas classes de Housing (`HouseController`, `PlaceableObjectController`), pois o sistema de moradias do 4.8 não existe no Classic 5.0.
   - Removidas classes de instâncias/mecânicas 4.8 (`PvpMapService`, `StarterKitService`, `InstanceScaler`, `VortexService`).
   - Removidas classes órfãs ou sem suporte no 5.0 (`TrapController`, `AbstractMaterialSkillActor`, `ZoneCollisionMaterialActor`, `TerrainZoneCollisionMaterialActor`, `CumulativeResist`, `CumulativeResistType`, `GlideFlag`, `AbstractQuestZoneObserver`, `DeathObserver`, `StanceObserver`, `DamageInfo`, `DamageList`, `AggroTarget`, `KillCounter`, `TeamDamageList`).
   - Removidos artefatos não referenciados (`CounterSkillStatus`, `EffectsContainer`, `SeenCreatureList`).
5. **Pontes de Compatibilidade com Módulos Não-Migrados**:
   - Como os módulos `ai`, `geoEngine`, `model`, `questEngine`, `skillengine`, `spawnengine`, `world` serão migrados nas fases seguintes, foram mantidas/restauradas pontes de compatibilidade downstream para garantir integridade total da compilação:
     - `MoveController` interface (implementada por `CreatureMoveController`).
     - `PetMoveController`, `ShieldController`, `KillList`, `AddDamageEvent`, `AddDamageEventListener`, `CollisionMaterialActor`, `IActor`.
     - `AggroInfo`, `AggroList`, `PlayerAggroList` (compatibilidade com `Creature`, `AionObject`, `AggroList` de `model` e scripts de IA).
     - `EffectController` e `PlayerEffectController` (compatibilidade com o estado atual de `skillengine`).
     - `ActionObserver`: métodos de sobrecarga com retrocompatibilidade (`attack(Creature)`, `attacked(Creature)`, `skilluse(Skill)`, etc.).
     - `AttackResult`: métodos esperados pelo pipeline de combate Classic 5.0 (`getDamageType()`, `setShieldMp()`).

---

## 3. Inventário de Arquivos do Módulo `controllers`

### Raiz: `com/aionemu/gameserver/controllers/`
- [x] `CreatureController.java` — Ciclo de vida de criaturas, eventos de IA, ataque, aggro e morte.
- [x] `FlyController.java` — Controle de voo, transições de estado e stamina.
- [x] `FlyRingController.java` — Anéis de voo e aceleração.
- [x] `GatherableController.java` — Coleta de materiais, interação e pacotes `S_GATHER`.
- [x] `NpcController.java` — Controle de NPCs, dialogos, respawn e aggro.
- [x] `ObserveController.java` — Gerenciamento thread-safe de observadores (`ActionObserver`, `AttackCalcObserver`).
- [x] `PetController.java` — Ações, comida, loot e estado de pets funcionais.
- [x] `PlayerController.java` — Controller central do jogador, teleporte, duel, pvp e interações.
- [x] `RoadController.java` — Controle de estradas e caminhos de velocidade.
- [x] `RVController.java` — Controle de rifts e fendas espaciais com Daeva Pass (`BattlePassService`).
- [x] `ShieldController.java` — Controle de escudos protetores de zonas.
- [x] `SiegeWeaponController.java` — Armas de cerco com validação geográfica `GeoService.canSee` e alvos por raça.
- [x] `StaticObjectController.java` — Controle de objetos estáticos no mundo.
- [x] `SummonController.java` — Invocações de espíritos / elementais e comandos de combate.
- [x] `VisibleObjectController.java` — Classe base genérica de todos os objetos visíveis.

### Subdiretório: `controllers/attack/`
- [x] `AddDamageEvent.java` — Eventos de incremento de dano em chefes de cerco.
- [x] `AddDamageEventListener.java` — Listener para eventos de dano adicional.
- [x] `AggroInfo.java` — Informações individuais de ódio/aggro por atacante.
- [x] `AggroList.java` — Tabela de ódio thread-safe com agregação de dano.
- [x] `AttackResult.java` — Resultados de dano físico e mágico com penetração de escudo.
- [x] `AttackStatus.java` — Enum de status de ataque (esquiva, bloqueio, crítico) com opcodes unsigned Classic 5.0.
- [x] `AttackUtil.java` — Utilitários de cálculo de combate corpo-a-corpo e distância.
- [x] `KillList.java` — Registro de eliminações PvP e ranking.
- [x] `PlayerAggroList.java` — Lista de ódio especializada para combate de jogadores.

### Subdiretório: `controllers/effect/`
- [x] `EffectController.java` — Gerenciamento de buffs, debuffs e estados anormais em criaturas.
- [x] `PlayerEffectController.java` — Especialização para jogadores com broadcast de ícones e persistência.

### Subdiretório: `controllers/movement/`
- [x] `CreatureMoveController.java` — Motor de movimento de criaturas com suporte a saltos, máscaras e `S_MOVE_NEW`.
- [x] `MoveController.java` — Interface padrão de movimentação.
- [x] `MovementMask.java` — Constantes de máscara de movimento do cliente AION Classic.
- [x] `NpcMoveController.java` — Movimento de NPCs com percurso, perseguição e retorno ao spawn.
- [x] `PetMoveController.java` — Movimento e acompanhamento de pets ao lado do dono.
- [x] `PlayableMoveController.java` — Controle de movimento para entidades jogáveis (jogadores e invocações).
- [x] `PlayerMoveController.java` — Movimentação de jogadores com validação de velocidade e anti-hack.
- [x] `SiegeWeaponMoveController.java` — Movimentação lenta e pesada de armas de cerco.
- [x] `SummonMoveController.java` — Movimento e seguimento de invocações.

### Subdiretório: `controllers/observer/`
- [x] `AbstractCollisionObserver.java` — Observador abstrato para detecção de colisão.
- [x] `ActionObserver.java` — Observador polimórfico de ações (ataque, movimento, habilidades, itens, morte).
- [x] `AttackCalcObserver.java` — Interceptor de cálculos de ataque e defesa.
- [x] `AttackShieldObserver.java` — Absorção de dano por escudos protetores.
- [x] `AttackStatusObserver.java` — Modificação de probabilidades de status crítico/bloqueio.
- [x] `AttackerCriticalStatus.java` — Estado de crítico do atacante com contadores.
- [x] `AttackerCriticalStatusObserver.java` — Observador de acertos críticos com redução de contagem.
- [x] `CollisionDieActor.java` — Ações desencadeadas por colisão fatal.
- [x] `CollisionMaterialActor.java` — Ações em superfícies de materiais colidíveis.
- [x] `DialogObserver.java` — Observador de abertura e fechamento de diálogos com NPCs.
- [x] `FlyRingObserver.java` — Detecção de passagem por anéis de voo.
- [x] `IActor.java` — Interface de atuadores de colisão e gatilhos.
- [x] `ItemUseObserver.java` — Observador de cancelamento e progresso do uso de itens.
- [x] `ObserverType.java` — Máscara de bits de categorias de eventos observáveis.
- [x] `RoadObserver.java` — Observador de entrada e saída em estradas de aceleração.
- [x] `ShieldObserver.java` — Observador de barreira de cerco.
- [x] `StartMovingListener.java` — Listener de início de movimento.

---

## 4. Resoluções de Compilação no Java 25

| Categoria | Causa Raiz | Resolução Aplicada |
| :--- | :--- | :--- |
| **Opcode / Serialização** | `AttackStatus` usava IDs signed (-64) no 4.8, quebrando o switch case de `S_ATTACK`. | Restaurados os IDs canônicos inteiros positivos (192, 194, etc.) do Classic 5.0. |
| **Nomenclatura de Pacotes** | 4.8 utilizava `SM_MOVE` e `SM_ATTACK`. | Adaptado para `S_MOVE_NEW` e `S_ATTACK` com envio via `PacketSendUtility`. |
| **Interfaces Downstream** | Classes em `model` e `ai` exigiam `MoveController`, `ShieldController`, etc. | Interface `MoveController` implementada por `CreatureMoveController` e classes pontes preservadas. |
| **Parâmetros de Observer** | Handlers de `data/handlers` chamavam `attack(Creature)` sem `skillId`. | Adicionadas sobrecargas delegando para as novas assinaturas preservando total retrocompatibilidade. |
| **GeoService / Cerco** | `SiegeWeaponController` chamava métodos inexistentes no 5.0. | Adaptado para `GeoService.getInstance().canSee(...)` e `FollowStartService`. |
| **Classes 4.8 Órfãs** | Classes de Housing e Vortex não têm modelos correspondentes no 5.0. | Removidas completamente sem prejuízo funcional ao Classic 5.0. |

---

## 5. Critérios de Aceitação (Definition of Done)

- [x] Pasta de destino anterior completamente removida antes da cópia.
- [x] Implementação de referência do 4.8 migrada.
- [x] Dependências de classes e modelos adaptadas à API 5.0.
- [x] Projeto compila integralmente com sucesso (`BUILD SUCCESS`) em Java 25.0.2 LTS via Maven 3.9.9.
- [x] Sem supressão dummy de métodos ou remoção de lógica essencial.
- [x] Protocolo oficial Classic 5.0 validado contra capturas Wireshark.
- [x] Pipeline de build e deploy (`build-server.bat`) executado com sucesso.
- [x] Git diff revisado e limpo de resíduos.
- [x] Documento de rastreamento da fase e Roadmap Mestre atualizados.
