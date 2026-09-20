# Atualização dos templates de skills Classic 5.0

Fonte: `5 - Documentação e Referências/3 - Client 5.0 - Dados Extraidos/data/skills/client_skills.xml`.

A revisão abrange os templates completos, além das skills que os geradores anteriores preenchiam como stubs. Em relação ao estado anterior, 10.017 templates foram alterados; 3.053 receberam alterações nos efeitos.

## Correções

- 139 cooldowns: o cliente expressa `delay_time` em milissegundos; o servidor usa décimos de segundo. O divisor correto é 100. O gerador de skills de jogadores usava 1.000, inclusive nas cópias de graus anteriores.
- 662 subtipos, 319 taxas de cancelamento, 79 relações de dano PvP, seis relações de duração PvP e 54 probabilidades de corrente.
- Custos e condições de consumo atualizados conjuntamente, inclusive remoção de custo explicitamente zero no cliente.
- Alcance, relação e tipo de alvo atualizados quando os enums possuem correspondência no servidor.
- Dano físico usa a dupla R1/R2 ou R3/R4, mantendo valor e crescimento da mesma dupla, inclusive quando o crescimento é zero.
- Dano e cura periódicos usam R8/R9 e `checktime` em milissegundos.
- Duração, identificador e nível básico dos efeitos, resistência, crítico, pré-efeitos e parâmetros de escudo revisados pelos campos oficiais.
- Ordem e posições dos efeitos alinhadas apenas quando todos os efeitos oficiais têm correspondência confirmada; efeitos antigos ausentes no cliente são removidos nesses casos.
- Stats antigos substituídos quando todos os tokens oficiais possuem tradução conhecida. Modificadores e condições específicas continuam preservados.
- Nomes traduzidos e templates sem definição no cliente permanecem preservados.

Exemplos conferidos:

| Skill | Antes | Depois |
|---|---|---|
| 151 — `WA_ArmorBreak_G1` | Dano base 11 | Dano base 22, crescimento 1 |
| 234 — `FI_Burserklance_G1` | Dano 2.356, crescimento 42 | Dano 1.649, crescimento 29 |
| 2570 — `WI_Hibernation_UP_G1` | Cooldown 60 | Cooldown 600 = 60 segundos |
| 2703 — `TH_ReturnShadow_new_G1` | Cooldown 12, deslocamento 100 | Cooldown 120 = 12 segundos, deslocamento 15 |

## Limites da atualização

O relatório `relatorio_refresh_skills_50.txt` identifica 169 casos sem correspondência estrutural segura, incluindo NPCs, itens, testes e enums especiais do cliente. Esses casos afetam 62 skills presentes na árvore de jogadores. Efeitos especiais incluem Blending de Soul Reaper, StatSynergy, transformações de modelo de personagem, RadarAngle, FlyBoost e gatilhos de esquiva. Não foram considerados corrigidos: os efeitos existentes sem tradução confirmada permanecem para revisão específica do motor e do protocolo oficial.

Esse levantamento estrutural não é uma auditoria completa de comportamento. A auditoria ampliada em `auditoria_legado_skills_50.md` também verifica restrições, funções de atributos, identificação de textos e implementações Java; portanto, as 62 skills acima não representam todas as pendências da migração.

Uma reconstrução parcial não reordena os demais efeitos nem aplica números de um tipo em outro tipo de efeito.

## Validação e distribuição

- XML completo válido em `skills.xsd`.
- Dez testes de regressão do gerador aprovados.
- Atualização idempotente verificada nos 12.139 templates existentes.
- XMLs da fonte e do produto final idênticos.
- Build Maven concluído com Java 25; JARs de game-server e commons sincronizados com o produto.
- Sem validação interativa no jogo; reiniciar o GameServer para carregar os novos dados.

Para auditar ou aplicar novamente, executar a partir da raiz `Classic`:

```text
python "6 - Ferramentas/parsersXML/refresh_50_skills.py"
python "6 - Ferramentas/parsersXML/refresh_50_skills.py" --aplicar
python "6 - Ferramentas/tests/test_refresh_50_skills.py"
```
