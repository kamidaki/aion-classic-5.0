# Plano de correção das skills Classic 5.0

Fonte canônica: `client_skills.xml`, `client_skill_learns.xml`, demais XMLs extraídos do cliente Classic 5.0 e capturas oficiais quando o comportamento não está descrito nos dados. Não serão usados valores substitutos nem estruturas herdadas apenas por semelhança com a 4.8.

## Fase 1 — Segurança dos geradores e campos determinísticos

Status: **concluída em 2026-09-18**.

- Efeitos desconhecidos não viram mais `PHYSICAL_ATTACK/ADD/10`.
- O gerador não usa mais NPC `200000`, duração ou valor genérico para completar stubs.
- Clones de graus anteriores só são aceitos quando todos os efeitos oficiais possuem tradução confirmada.
- `StatBoost` distingue contribuição fixa em R2 e percentual em R4.
- `StatUp` e `StatDown` tratam R13/R6 e R14/R7 separadamente.
- `ShapeChange` deixou de ser considerado equivalente a `Polymorph`.
- Quatro efeitos `DispelDebuffPhysical` oficiais foram restaurados.
- Restrições de arma, mão esquerda e movimento foram sincronizadas para as skills de jogadores, incluindo `GAUNTLET`, `DIMENSIONSWORD` e `RUNESWORD`.

Critério de conclusão: XML válido, execução idempotente, fonte e produto sincronizados e testes de regressão aprovados.

## Fase 2 — Efeitos existentes no motor

Status: **concluída em 2026-09-18 para os campos com tradução confirmada**.

- Foram completados `AlwaysResist`, `Dispel`, `StatUp`, `Reflector` e `DeboostHealAmount` com os campos explícitos do cliente.
- Target slot, categoria de dispel, nível do target slot e `nameId` foram sincronizados a partir dos XMLs oficiais.
- `TargetLock` foi implementado como mecânica própria para `RB_Isolation_G1`: mantém o vínculo caster/alvo, aplica os três modificadores oficiais de dano, encerra fora do alcance oficial e ativa/remove a skill visual 9638 no caster.
- O normalizador ficou idempotente, com XSD válido e testes de regressão.

## Fase 3 — Mecânicas especiais 5.0

Status: **em andamento**.

- `StatSynergy` foi implementado no motor e aplicado às sete passivas do Soul Reaper presentes na árvore de jogadores.
- O `Blending` de aprendizado do Soul Reaper foi separado do efeito musical da Luminess: seis passivas combinadas são concedidas/removidas conforme as combinações oficiais de pré-requisitos.
- O `Blending` por `stack_level` foi implementado a partir da tabela oficial: as cinco graduações de `Blade Assault` compartilham o contador e disparam a skill 9639 no segundo acúmulo. Cinco templates internos com marcador legado também foram convertidos para suas combinações oficiais.
- Validar em jogo o acúmulo de `Blade Assault` e executar uma regressão do Blending musical da Luminess.
- `FlyBoost`, `RadarAngle` e `Control` foram registrados como tipos próprios. O `FlyBoost` agora apenas habilita o Quick Glide já medido no oficial, `RadarAngle` preserva seus 180/240/300/360 graus, e `Control` substitui o falso `Deform` com modelo 200000 antes do `Deform` visual oficial.
- Validar em jogo Quick Glide, expansão do radar e as três skills de Frenzy (`Control`).
- Os 453 efeitos `ShapeChange` com modelo oficial confirmado foram separados dos antigos aliases `Polymorph`/`Deform`, preservando os modelos e restrições existentes.
- `Provoker` passou a receber o resultado defensivo real do ataque. `Boost evasivo I`, sua versão superior e `Defesa confiante I` agora disparam somente em `DodgeHit`/`ParryHit`, conforme o cliente.
- `Sleep I` usa o `Deform` oficial sem modelo: aplica apenas o estado anormal e não encerra uma transformação visual que já esteja ativa.
- Validar em jogo o `TargetLock`: dano contra o alvo marcado, proteção contra terceiros, penalidade contra outros alvos e término acima de 30 m.
- Implementar `Utility` ou substituir o tipo somente quando sua semântica oficial estiver demonstrada.
- Continuar a revisão dos `Polymorph` de conteúdo interno/NPC, que não pertencem à árvore de jogadores.

## Fase 4 — Árvore, motions e validação funcional

Status: **pendente**.

- Revisar as 33 skills com política de aprendizado divergente sem assumir que o gerador atual traduz corretamente todas as classes.
- Importar motions existentes e identificar assets realmente ausentes.
- Validar em jogo por classe: custo, arma, movimento, dano, duração, dispel, cadeia, passivas e efeitos especiais.
- Comparar comportamentos ambíguos com PCAPs e Game.dll, documentando a evidência usada.

## Ordem por impacto

1. Efeitos ausentes já suportados pelo motor.
2. `StatSynergy` das passivas do Soul Reaper.
3. Validação do `Blending` por acúmulo de `Blade Assault` e regressão do Blending musical da Luminess.
4. Tipos sem registro JAXB e classes Java vazias (`FlyBoost`, `Control`, `RadarAngle` e `Utility`).
5. Árvore de aprendizado e motions.
