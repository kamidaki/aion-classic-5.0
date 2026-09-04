# MIGRATION_SKILLENGINE.md — Fase 7: Módulo `skillengine`

## Resumo

Modernização estrutural e eliminação integral de Javolution (`FastMap`, `FastList`) no motor de habilidades (`skillengine`), preservando 100% dos efeitos, ações e mecânicas exclusivos do Classic 5.0 EU (Siel Energy/SP System, Classic XP/SP Heal, Idun Drop Boost, Enchant Option Boost, Authorize Boost, etc.) e garantindo 0 erros e compilação limpa no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise Comparativa: Classic 5.0 vs 4.8 Retail

- **Base Classic 5.0 EU (285 arquivos Java)**:
  - Contém todos os novos efeitos e ações do Classic:
    - SP System: `SpUseAction.java`, `SpCondition.java`, `SPHealInstantEffect.java`, `ProcSPHealInstantEffect.java`
    - Classic Experience & Boosts: `XPHealInstantEffect.java`, `ProcXPHealInstantEffect.java`, `IdunDropBoostEffect.java`, `EnchantBoostEffect.java`, `EnchantOptionBoostEffect.java`, `AuthorizeBoostEffect.java`
    - Controles de Penalidade e Deslocamento: `DeathPenaltyReduceEffect.java`, `NoDeathPenaltyReduceEffect.java`, `OdellaRecoverIncreaseEffect.java`, `ReturnCoolReduceEffect.java`, `SprintFpReduceEffect.java`, `ShadowMoveEffect.java`, `TimeFreezingEffect.java`, `SummonKiskEffect.java`
    - Condições de Combate: `ArrowCheckCondition.java`, `ShieldCondition.java`, `ArmorCondition.java`
    - Tarefas e Tipos: `BonusChargeType.java`, `SkillMoveType.java`, `MorphingTask.java`
- **Referência 4.8 Retail (292 arquivos Java)**:
  - Continha sistemas específicos de 4.8 descontinuados no Classic (ex: robôs de Aethertech/Mecha como `RideRobotEffect.java`, `RideRobotCondition.java`, `ChargeArmorCondition.java`; housing de 4.8 como `SummonHouseGateEffect.java`).
- **Decisão Técnica**:
  - A base do Classic 5.0 é integralmente preservada por conter os sistemas exclusivos do Classic. O foco foi a eliminação completa de dependências de Javolution e adequação à concorrência nativa do Java 25.

---

## Alterações Realizadas (3 arquivos)

| Arquivo / Pacote | Alteração Realizada |
|---|---|
| `skillengine.model.Effect.java` | Substituição de `new FastMap<Integer,EffectTemplate>().shared()` por `new ConcurrentHashMap<Integer,EffectTemplate>()`. Remoção do import `javolution.util.FastMap` e adição de `java.util.concurrent.ConcurrentHashMap`. |
| `skillengine.model.ChainSkills.java` | Substituição de `new FastMap<String, ChainSkill>()` por `new ConcurrentHashMap<String, ChainSkill>()`. Remoção do import `javolution.util.FastMap` e adição de `java.util.concurrent.ConcurrentHashMap`. |
| `skillengine.effect.EffectTemplate.java` | Substituição de `FastList<Integer>` no método `getPreEffects()` e chamador `positions` por `List<Integer>` e `ArrayList<Integer>`. Remoção do import `javolution.util.FastList`. |

---

## Estatísticas da Fase 7

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no módulo `skillengine` | 285 | **285** |
| Referências a `javolution` no pacote `skillengine` | 3 arquivos | **0 (Zero)** |
| Efeitos exclusivos Classic 5.0 preservados | 29 | **29 (100%)** |
| Compilação Maven (Java 25) | - | **BUILD SUCCESS** (6/6 módulos) |
