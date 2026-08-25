# Plano de Jogo - SkillEngine, Fórmulas de Dano & Sistema de Combate

Este documento define todas as fórmulas matemáticas de combate, cálculo de acertos e bloqueios, execução de habilidades, correntes de skills (Chains), sistema de Stigmas e efeitos de status anormais (migração de `com/aionemu/gameserver/skillengine/` do Java 4.8 para Rust).

---

## 1. Mapeamento de Classes Java 4.8 $\rightarrow$ Rust

| Classe Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `skillengine.SkillEngine` | `skill::skill_engine.rs` | Carregador e executor de habilidades |
| `skillengine.model.Skill` | `skill::skill_instance.rs` | Instância em execução de uma habilidade (caster, target, tempo de cast) |
| `skillengine.model.SkillTemplate` | `skill::template.rs` | Dados estáticos da skill (dano base, custo de MP, alcance, cooldown, chain) |
| `skillengine.effect.Effect` | `skill::effect.rs` | Efeito ativo (buff, debuff, dano contínuo, escudo) |
| `skillengine.action.DamageAction` | `skill::damage_calc.rs` | Motor matemático de cálculo de dano físico e mágico |
| `skillengine.condition.ChainCondition` | `skill::chain.rs` | Verificação e ativação de habilidades em cadeia |

---

## 2. Fórmulas Oficiais de Combate

### A. Dano Físico (Physical Damage)
$$\text{Dano Base} = \max\left(1, \left(\text{Ataque Físico} - \frac{\text{Defesa Física do Alvo}}{10}\right)\right)$$
$$\text{Dano Final} = \text{Dano Base} \times \text{Multiplicador da Skill} \times \text{Modificador de Crítico/Bloqueio}$$

* **Crítico Físico**: Se ocorrer acerto crítico:
  * Espada / Adaga: $\text{Dano} \times 2.3$
  * Greatsword / Polearm / Arco: $\text{Dano} \times 1.8$
  * Mace / Staff: $\text{Dano} \times 2.0$

### B. Dano Mágico (Magic Damage)
$$\text{Dano Mágico} = \left(\text{Dano Base da Skill} \times \left(1 + \frac{\text{Magic Boost}}{1000}\right) - \frac{\text{Magic Supp}}{10}\right) \times \left(1 - \frac{\text{Magic Resist}}{10000}\right)$$

### C. Tabela de Resolução de Golpes Físicos (Hierarquia de Dados)
Quando um ataque físico é desferido, o servidor roda a rolagem de dados na seguinte ordem estrita:
1. **Miss (Erro de Ataque)**:
   $$\text{Chance de Miss} = \max\left(0\%, \min\left(30\%, \frac{\text{Evasion}_{\text{alvo}} - \text{Accuracy}_{\text{atacante}}}{10}\right)\right)$$
2. **Dodge / Evasion (Esquiva)**: Alvo desvia completamente do golpe ($0\text{ de dano}$).
3. **Parry (Aparo com a Arma)**:
   $$\text{Chance de Parry} = \max\left(0\%, \min\left(40\%, \frac{\text{Parry}_{\text{alvo}} - \text{Accuracy}_{\text{atacante}}}{10}\right)\right)$$
   * Se aparar: Reduz o dano recebido em **$40\%$** e pode ativar habilidades de contra-ataque.
4. **Block (Bloqueio com Escudo)**:
   $$\text{Chance de Block} = \max\left(0\%, \min\left(50\%, \frac{\text{Block}_{\text{alvo}} - \text{Accuracy}_{\text{atacante}}}{10}\right)\right)$$
   * Se bloquear: Reduz o dano recebido no valor de mitigação do escudo (normalmente **$70\%$** com escudo equipado).
5. **Critical Hit**:
   $$\text{Chance de Crítico} = \max\left(0\%, \min\left(50\%, \frac{\text{Crit}_{\text{atacante}} - \text{CritStrikeResist}_{\text{alvo}}}{10}\right)\right)$$
6. **Normal Hit**: Dano regular sem modificadores especiais.

---

## 3. Sistema de Efeitos e Status Anormais

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AbnormalState {
    Stun,        // Imóvel e sem poder agir (1 a 3s)
    Stumble,     // Derrubado no chão (alvo recebe mais dano)
    Knockback,   // Empurrado para trás
    Silence,     // Incapaz de conjurar magias
    Blind,       // Precisão física reduzida drasticamente (Miss frequente)
    Sleep,       // Dormindo (acorda se receber dano)
    Fear,        // Correndo em pânico sem controle
    Poison,      // Dano contínuo de veneno a cada 2s
    Bleed,       // Dano contínuo de sangramento a cada 2s
    Root,        // Preso ao chão, mas pode conjurar habilidades
    Hide,        // Invisibilidade (Níveis I a III)
    Paralyze,    // Paralisado completamente por efeito de Godstone
}
```

---

## 4. Correntes de Habilidade (Skill Chains)

Determinadas habilidades só podem ser usadas após o sucesso de uma habilidade anterior (ex: *Ferocious Strike* $\rightarrow$ *Robust Blow* $\rightarrow$ *Wrathful Blow*):
* Ao acertar o primeiro golpe, o servidor envia `SM_SKILL_CHAIN` informando que o próximo estágio da corrente está liberado.
* O jogador tem uma janela de tempo de **$7\text{ segundos}$** para ativar a próxima skill da cadeia antes que o gatilho expire.
