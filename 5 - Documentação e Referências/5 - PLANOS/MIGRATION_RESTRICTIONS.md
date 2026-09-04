# MIGRATION_RESTRICTIONS.md — Fase 6: Módulo `restrictions`

## Resumo

Validação, modernização e fortalecimento das regras de restrição de jogador e ambiente (`restrictions`), mantendo o padrão de pipeline baseado em `RestrictionsManager` do Classic 5.0 EU, integrando verificações anti-exploit de loja pessoal (`CreatureState.PRIVATE_SHOP`) e garantindo 0 erros e 0 dependências legadas no Java 25 LTS.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven no Java 25.

---

## Análise Comparativa: Classic 5.0 vs 4.8 Retail

- **Arquitetura Classic 5.0**:
  - Implementa um pipeline extensível baseado em anotações e reflexão ordenada por prioridade: `RestrictionsManager` gerencia instâncias de `Restrictions` (`PlayerRestrictions`, `PrisonRestrictions`, `ShutdownRestrictions`).
  - Utiliza os pacotes e opcodes nativos da versão Classic 5.0 (`S_MESSAGE_CODE`, `PlayerMode.WINDSTREAM`, `TransformType.AVATAR`, arenas PvP).
- **Referência 4.8 Retail**:
  - No 4.8, `PlayerRestrictions` havia sido transformado em uma classe de métodos utilitários estáticos acoplada aos pacotes legados do 4.8 (`SM_SYSTEM_MESSAGE`, `SM_ATTACK_RESPONSE`).
- **Decisão Técnica**:
  - Conforme o **Princípio 1** ("Prioridade Absoluta do Classic 5.0"), a arquitetura modular e orientada a objetos de `RestrictionsManager` do 5.0 foi mantida e fortalecida com as checagens anti-exploit identificadas na lógica do 4.8.

---

## Alterações Realizadas

### `PlayerRestrictions.java`
- Adicionada verificação estrita de `CreatureState.PRIVATE_SHOP` nos métodos `canUseSkill` e `canAttack`, impedindo que jogadores executem habilidades ou inflijam dano enquanto operam lojas pessoais.
- Preservação total dos 100% de contratos de arena PvP, voo/windstream e estados anormais (`CANT_ATTACK_STATE`, `SILENCE`, `BIND`).

---

## Estatísticas da Fase 6

| Métrica | Status |
|---|---|
| Arquivos no módulo `restrictions` | 8 arquivos |
| Dependências de `javolution` | **0 (Zero)** |
| Compatibilidade de rede Classic 5.0 | **100%** |
| Compilação Maven | **BUILD SUCCESS** (6/6 módulos) |
