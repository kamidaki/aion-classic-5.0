# Alterações de arquitetura e dados — auditoria de itens Classic 5.0 EU

## Escopo desta etapa

- Catálogo canônico definido como `data/europe/Items/client_items.xml`; as cinco outras variantes foram inventariadas separadamente e não foram mescladas.
- Auditor anterior corrigido para localizar `data/Strings`; a execução passou de 0 para 248.529 strings carregadas.
- Gerador protegido para preservar nomes localizados por padrão. A troca do texto exibido agora exige `--atualizar-nomes` explícito.
- Auditor individual novo, por streaming, sem caminhos absolutos e sem alterar o emulador.
- 58 referências `desc` ausentes foram preenchidas pelos IDs oficiais da camada Europe. Nenhum comportamento Java foi usado para contornar dados XML.

## Arquivos afetados

- `Código Fonte - Emulador/game-server/data/static_data/items/item_templates.xml`: 58 atributos `desc` corrigidos.
- `Emulador - Produto Final/GameServer/data/static_data/items/item_templates.xml`: cópia idêntica à fonte.
- `Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/rebuild_50_item_templates.py`: seleção EU, descoberta correta de strings e proteção de localização.
- `Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/audit_50_items_complete.py`: geração da matriz por ID, inventário arquitetural, comparação de variantes e matriz de testes.

## Java, pacotes e banco de dados

Nenhum serviço Java, handler, serializer, opcode ou schema SQL foi alterado nesta etapa. Eles foram apenas inventariados. A matriz contém 433 arquivos Java relacionados, 51 arquivos de dados e 68 PCAPs oficiais disponíveis. Alterações nessas camadas dependem da análise específica de cada divergência e de evidência oficial.

## Indicadores após a correção

| Indicador | Resultado |
| --- | ---: |
| Itens oficiais Europe | 79.664 |
| Itens no emulador | 79.664 |
| Compatíveis nos campos auditados | 22.560 |
| Divergentes comprovados | 55.798 |
| Pendentes de relação/protocolo | 1.306 |
| Itens corrigidos nesta etapa | 58 |
| Itens implementados nesta etapa | 0 |
| Descrições ainda divergentes | 0 |
| Testes Java executados | 19/19 aprovados |
| Grupos end-to-end concluídos | 0/15 |

Os números de compatibilidade não equivalem a funcionamento integral: um item só pode ser declarado validado após dados, comportamento, protocolo, persistência e teste no cliente estarem comprovados.

## Etapa 2 — máscaras e permissões

- As máscaras internas dos 79.664 itens foram reconstruídas exclusivamente com `lore`, troca, venda, warehouses, `breakable`, vínculo, remoção no logout, encantamento, fusão, remodelagem, divisão e tingimento da camada Europe.
- 52.455 templates foram alterados. Flags herdadas sem campo oficial no Classic (`CAN_AP_EXTRACT`, `CAN_POLISH` e `LEGION_TRADEABLE`) foram removidas.
- `DELETABLE` continua derivado de `breakable`, conforme a captura oficial de descarte já documentada, e não de `item_drop_permitted`.
- A `client_mask` de wire foi recalculada separadamente. Oito itens mudaram em relação à camada genérica, refletindo os deltas Europe.
- Resultado do verificador: `mask` 100% idêntica nos 79.664 itens; `client_mask` 100% idêntica na matriz integral; XML XSD válido.
- Foi corrigido também o predicado de missão da máscara de wire: 1.422 registros com `<quest>0</quest>` deixaram de receber indevidamente o bit de quest. Os 298 registros com `<quest>1</quest>` permanecem marcados.
- Indicadores após esta etapa: 42.656 compatíveis nos campos diretos, 28.907 divergentes comprovados e 8.101 pendentes de relações que exigem validação adicional.

## Etapa 3 — campos diretos de utilização e tempo

- Foram sincronizados `activate_target`, `activate_count`, `casting_delay`, `expire_time`, `return_world` e `return_alias` em 9.583 templates.
- Alvo, contagem, expiração e retorno agora têm 100% de igualdade com a camada Europe; delays representáveis também foram sincronizados.
- Oito itens permanecem pendentes porque o cliente informa `casting_delay=4000000000`, valor fora de `xs:int` e `Java int`. O valor não foi truncado nem convertido sem prova do significado do sentinel unsigned.
- Indicadores após esta etapa: 49.500 compatíveis nos campos diretos, 20.673 divergentes comprovados e 9.491 pendentes de relações/valores que exigem validação adicional.

## Etapa 4 — campos básicos do catálogo e qualidade Divinity

- Foram sincronizados `level`, `price`, `max_stack_count`, `quality`, `race` e `attack_type` em 20.681 templates, sempre a partir da camada Europe.
- O servidor e o XSD passaram a reconhecer `DIVINITY(7)`. A posição 7 é comprovada pelas interfaces oficiais `search_quality7`; o catálogo Europe contém 11 itens dessa qualidade e as regras oficiais de Combat Power possuem a entrada `item_quality_divinity`.
- Tipos de ataque elementais `MAGICAL_FIRE` e `MAGICAL_WATER` foram preservados sem redução para `MAGICAL`; 368 templates divergentes foram corrigidos.
- Cinco registros oficiais com `max_stack_count=0` (`gold`, `testball`, `arcanium`, `QUNA` e `FREE_QUNA`) ficaram pendentes. O zero não foi aplicado onde alteraria a operação do inventário sem evidência do significado especial.
- Resultado do verificador: nível, qualidade, raça, tipo de item e tipo de ataque com 100% de igualdade; XML XSD válido. Não restam divergências comprovadas nos campos diretos atualmente auditados.
- Indicadores após esta etapa: 66.805 compatíveis nos campos diretos, 0 divergentes comprovados e 12.859 pendentes de relações/valores que exigem validação adicional.

## Etapa 5 — atributos diretos de armas e escudos

- Foram sincronizados os onze atributos diretos de `weapon_stats` em 3.974 templates: dano mínimo/máximo, velocidade, crítico, precisão física, aparo, precisão mágica, poder mágico, alcance, número de golpes e bloqueio máximo.
- Atributos ausentes no XML agora são comparados pelo auditor com o valor efetivo `0` usado pelo Java, eliminando falsos positivos sem materializar zeros desnecessários nos templates.
- Foram corrigidas 314 diferenças de dano mínimo, 314 de dano máximo, 284 de crítico, 2.550 de precisão física, 613 de aparo, 2.985 de precisão mágica, 412 de poder mágico e 68 de bloqueio máximo. Velocidade, alcance e número de golpes já estavam corretos.
- O auditor não registra mais divergências nem pendências em `weapon_stats`; o XML permanece válido contra o XSD e fonte/produto final continuam idênticos.
- Indicadores após esta etapa: 71.465 compatíveis nos campos diretos, 0 divergentes comprovados e 8.199 pendentes de relações/valores que exigem validação adicional.

## Etapa 6 — restrições de classe e faixa de nível

- Foram sincronizadas as matrizes `restrict` e `restrict_max` em 4.866 templates: 4.787 restrições mínimas e 141 restrições máximas alteradas.
- O mapeamento usa a ordem real dos 25 ordinais de `PlayerClass`; 24 posições possuem fonte oficial. A posição `PlayerClass.ALL`, sem campo correspondente no cliente, preserva seu valor efetivo anterior e não é inventada.
- O parser passou a carregar também os campos oficiais `*_max`, anteriormente descartados, e o auditor agora compara as matrizes após aplicar exatamente a expansão usada pelo JAXB/Java.
- Foi removido o bypass legado que considerava qualquer arma ou armadura válida para qualquer classe. Também foi removida a cópia indevida de nível mínimo/máximo de outras classes quando a classe consultada possui valor zero.
- Resultado do verificador: 100% de igualdade nas 24 posições oficialmente mapeadas; zero divergências de `restrict` ou `restrict_max`; XML XSD válido.
- Os indicadores gerais permanecem em 71.465 compatíveis, 0 divergentes comprovados e 8.199 pendentes, pois essas matrizes ainda não faziam parte das pendências contabilizadas antes desta etapa.

## Etapa 7 — modificadores diretos de atributos

- O auditor passou a comparar, por item e por tupla completa, operação, `StatEnum`, valor e flag `bonus` dos atributos base, `bonus_attrN` e `stat_enchant` oficiais. A presença genérica de um bloco `<modifiers>` não é mais aceita como comprovação.
- Foram adicionados 4.010 modificadores oficiais ausentes em 1.585 templates, sem remover modificadores existentes e sem sobrescrever colisões de valor. Fonte e produto final permanecem idênticos.
- Foram comprovados os mapeamentos adicionais de resistências `ar*`, `magical_resist` e `questexpboost`; o XML e o enum Java já possuem os `StatEnum` correspondentes. O caso representativo `101301113` recebeu `BOOST_QUEST_XP_RATE=10%` e o manastone `167000524` recebeu `MAGICAL_RESIST=300`.
- Permanecem preservados para investigação 1.853 conflitos de valor/semântica e 461 itens com campos sem mapeamento comprovado: 389 `alldefendratio`, 66 `bleedreduceratio`, quatro `elementaldefendall` e dois manastones `elementaldefendall`.
- `alldefendratio` não foi convertido para `PVP_DEFEND_RATIO`: o item oficial `110100842` informa 30, enquanto o template legado possui 50, evidenciando que a equivalência direta seria incorreta. Os demais campos ambíguos também não foram inferidos.
- A matriz integral agora registra 1.660 itens com pendência específica de modificador, sendo 461 com nome ainda não mapeado e 1.204 com ao menos uma tupla oficial ausente; há sobreposição entre os grupos.
- A regressão automatizada executou 25 testes em Java 25, todos aprovados, incluindo a carga real de `BOOST_QUEST_XP_RATE=10` e `MAGICAL_RESIST=300` a partir dos templates sincronizados.
- Indicadores após esta etapa: 71.316 compatíveis nos campos auditados, 0 divergências comprovadas e 8.348 pendentes. A queda nominal de compatíveis decorre da auditoria mais rigorosa, não de regressão: diferenças antes ocultas por um bloco `<modifiers>` não vazio passaram a ser explicitadas.

## Etapa 8 — conflitos e modificadores compostos

- Foram corrigidos 2.785 valores legados em 1.191 templates quando havia correspondência inequívoca um-para-um de operação, `StatEnum` e flag `bonus`; outros 384 modificadores oficiais do mesmo grupo foram adicionados.
- A leitura de modificadores passou a separar bônus diretos dos efeitos condicionais. Treze templates ainda tinham tuplas diretas ausentes dentro de blocos com condições: foram adicionadas 13 tuplas e corrigidos oito valores de `MAXHP`, preservando integralmente os bônus condicionados por `charge`.
- `AllAttackRatio` e `AllDefendRatio` foram alinhados à conversão já comprovada no reconstrutor oficial de skills: cada valor gera simultaneamente os modificadores PvP e PvE correspondentes. Foram adicionadas 1.160 tuplas `PVE_ATTACK_RATIO`, 389 `PVE_DEFEND_RATIO` e 239 `PVP_DEFEND_RATIO`; 144 valores legados de defesa PvP foram corrigidos.
- `ElementalDefendAll` foi expandido para água, vento, fogo e terra, como já definido nos conversores oficiais de skills e consumíveis. Os quatro acessórios e os dois manastones aplicáveis receberam as quatro resistências, totalizando 24 tuplas.
- `BleedReduceRatio` permaneceu pendente em 66 armaduras. A string oficial o descreve como redução de dano de sangramento; o `BLEED_RESISTANCE` atual representa resistência à aplicação do efeito e, portanto, não é uma equivalência segura. Será necessária uma representação de stat e integração específica com o cálculo de dano periódico.
- O sincronizador terminou idempotente, sem conflitos diretos preservados. O verificador chegou a 96,9% de igualdade integral dos blocos existentes e 100% das manastones comparáveis; diferenças integrais restantes podem incluir modificadores adicionais não originados nos campos diretos auditados.
- A regressão automatizada executou 26 testes em Java 25, todos aprovados, incluindo expansão PvP/PvE e as quatro resistências elementais. O XML permanece válido contra o XSD.
- Indicadores após esta etapa: 72.900 compatíveis nos campos auditados, 0 divergências comprovadas e 6.764 pendentes. Somente 66 itens ainda têm pendência de modificador direto.

## Etapa 9 — redução de dano de sangramento

- Os 66 usos oficiais de `BleedReduceRatio` foram classificados nos valores 100, 140, 205 e 275. A escala por mil segue a convenção dos demais atributos `Ratio`, correspondendo a 10%, 14%, 20,5% e 27,5% de redução.
- Foi criado o stat `BLEED_DAMAGE_REDUCE_RATIO`, separado de `BLEED_RESISTANCE`. O primeiro reduz o dano periódico já calculado; o segundo continua sendo usado exclusivamente na chance de aplicação/resistência do estado de sangramento.
- `BleedEffect` passou a aplicar a redução ao dano final reservado para cada pulso, com intervalo defensivo de 0 a 1000 e dano mínimo de um ponto.
- Os 66 templates receberam o modificador oficial, e os XSDs da fonte e do produto final foram sincronizados com o novo enum.
- O sincronizador terminou idempotente com zero modificadores ausentes, zero nomes sem mapeamento e zero conflitos. A matriz integral não possui mais pendências de modificadores diretos.
- A regressão automatizada executou 29 testes em Java 25, todos aprovados. Foram cobertos os quatro valores oficiais, limites inferior/superior, dano mínimo, carga do template e separação de `BLEED_RESISTANCE`.
- O produto final foi recompilado e sincronizado: JAR `b507257dcf58a5774b72e336c091603aa8a6419edb826d307aa504cdf6bbb136` e ZIP `c91f4a94b6899fcd3b98b8653f2d714528915acfd907515a8c7557141f6c8667` coincidem com os artefatos gerados pelo Maven.
- Indicadores após esta etapa: 72.961 compatíveis nos campos auditados, 0 divergências comprovadas e 6.703 pendentes. Cinco dos 66 itens continuam pendentes por relações não ligadas aos modificadores.

## Etapa 10 — ações oficiais de ativação de skills

- O sincronizador `fix_50_item_activation_skill.py` passou a usar como catálogo canônico `data/europe/Items/client_items.xml`, resolver nomes pelo `data/skills/client_skills.xml` oficial e exigir que o ID exista no `skill_templates.xml` do servidor antes de alterar um item.
- Foram inseridas 198 ações `skilluse` ausentes. Entre os casos recuperados estão consumíveis, pergaminhos, itens de missão, invocações e itens de transformação; nenhuma skill ou efeito foi inventado.
- Quatro ações existentes de itens de missão tinham `level="0"`; os IDs 182202194, 182205692, 182206724 e 182206726 foram alinhados ao `activation_level=1` oficial.
- O verificador cobre individualmente os 2.508 registros com `activation_skill`: 2.388 nomes oficiais estão resolvidos para o mesmo `skillid` e `level` carregado pelo servidor. Os 120 valores numéricos pequenos (5, 6, 8, 9 e 11), todos em equipamentos, não foram tratados como IDs de skill e permanecem pendentes de um dicionário oficial de semântica.
- O fluxo Java existente foi preservado: `SkillUseAction` valida pelo `SkillEngine`, inicia a skill com o template do item, e a remoção/cooldown ocorre no pagamento dos custos do cast. Esta etapa não declara validação end-to-end desse fluxo no cliente.
- Fonte e produto final permanecem idênticos e válidos contra o XSD, com SHA-256 `cc6f409ac280112dbc9160fc9e12caf795d2f9faafb7435b06a81f7c437130b8`. Uma segunda execução terminou idempotente, com zero inserções e zero correções.
- A regressão automatizada executou os 21 testes de `ClassicItemSystemsTest` em Java 25, todos aprovados. A nova cobertura verifica ação/alvo, níveis 1 e 5 e garante que um código numérico de equipamento não seja convertido em `skilluse`.
- Indicadores após esta etapa: 73.158 compatíveis nos campos auditados, 0 divergências comprovadas e 6.506 pendentes. Os 15 grupos de testes end-to-end continuam em 0/15.

## Etapa 11 — combinações oficiais de itens

- Os 439 registros Europe com `assembly_item` foram resolvidos pelo nome interno do resultado no mesmo catálogo. Todos produziram uma relação única e existente, distribuída em 313 resultados; não houve nome ausente, ambíguo ou peça repetida dentro de um grupo.
- A tabela legada `assembly_items.xml` continha 89 resultados e 253 peças. Apenas um grupo coincidia integralmente com a camada Europe; a tabela foi reconstruída com os 313 resultados e 439 peças oficiais.
- Foram inseridas 434 ações `assemble`; as cinco ações já existentes foram validadas. O auditor agora compara também o atributo `assemble.item`, evitando considerar correta uma ação que apenas possua a tag esperada.
- O sincronizador `sync_50_item_assembly.py` valida os dois XMLs contra seus XSDs, exige fonte/produto final inicialmente sincronizados, registra cada resultado e suas peças e interrompe diante de qualquer relação não comprovada. A segunda execução terminou com 313/313 grupos exatos e 439 ações validadas, sem alteração.
- `AssemblyItemAction` passou a validar quantidades agregadas, inclusive se uma combinação futura exigir mais de uma unidade da mesma peça. A entrega do resultado agora é verificada antes de confirmar a operação; se o inventário recusar o resultado, todas as peças removidas são devolvidas e não há mensagem, cooldown ou animação de sucesso.
- A regressão Java 25 carregou `item_templates.xml` e `assembly_items.xml` reais, validou o grupo histórico de cinco peças, um novo resultado de peça única e a resolução da ação para o resultado. Os 22 testes de `ClassicItemSystemsTest` foram aprovados.
- Fonte e produto final estão sincronizados: `item_templates.xml` SHA-256 `8100302b6328c7a168df6dccb35d968c56a8f42d48d26a0bd60ec3b972ee5a04`; `assembly_items.xml` SHA-256 `204817496acf294473092eb21f98130e0e3f79af906d66b01ab78c63c086d8e2`; JAR do GameServer SHA-256 `b2041d7c4064073b1977bdab7a27be882dbd89ec19fe43e2f8cb2a6b1c867f6e`.
- Indicadores após esta etapa: 73.387 compatíveis nos campos auditados, 0 divergências comprovadas e 6.277 pendentes. A diferença de 229 itens compatíveis decorre de 205 peças que ainda possuem outra relação pendente; a pendência `assemble` foi eliminada dos 439 itens.

## Etapa 12 — cartões de título oficiais

- O catálogo Europe contém 411 itens com `cash_title`, apontando para 335 títulos distintos. As 163 ações `titleadd` preexistentes já tinham ID e duração exatos; 248 cartões não possuíam ação.
- Foram inseridas 67 ações ausentes cujos títulos 228–296 já existem no `player_titles.xml`. O resultado possui 230 ações validadas individualmente, incluindo títulos permanentes (atributo `minutes` omitido) e temporários com os valores oficiais preservados sem normalização.
- Os 181 cartões restantes não foram ativados porque seus 163 títulos distintos ainda não existem no catálogo do servidor. O extrato oficial `data/PC/client_titles.xml` fornece estrutura para 74 deles (IDs 408–481); para outros 89 IDs entre 301 e 407, o conjunto oficial disponível contém apenas referências de itens/strings, sem atributos completos de título. Esses casos permanecem explicitamente pendentes, sem inferência a partir do Live.
- O sincronizador `sync_50_item_titles.py` exige que o título exista no servidor antes de inserir ou corrigir a ação, valida o XML agregado e mantém fonte/produto final sincronizados. A segunda execução terminou idempotente, com zero inserções e zero correções.
- O auditor agora carrega `cash_available_minute`, compara `titleadd.titleid` e `titleadd.minutes` e distingue uma ação ausente de uma dependência ausente em `player_titles.xml`. Isso eliminou um falso diagnóstico intermediário de 173 divergências de duração.
- `TitleAddAction` expõe ID e duração para regressão automatizada. Os 23 testes de `ClassicItemSystemsTest` foram aprovados em Java 25, cobrindo um cartão temporário, um permanente e a ausência deliberada da ação para o título 301 ainda não implementado.
- Fonte e produto final estão sincronizados: `item_templates.xml` SHA-256 `54a84dfd3162673db487f95d129247a6bb9f96fe04352b938d47b328e7521687`; JAR do GameServer SHA-256 `f40839b581bd711e79fe6403822c514cb761176dd2fcf60b928b521d377ce844`.
- Indicadores após esta etapa: 73.454 compatíveis nos campos auditados, 0 divergências comprovadas e 6.210 pendentes. Os 15 grupos end-to-end continuam em 0/15.
