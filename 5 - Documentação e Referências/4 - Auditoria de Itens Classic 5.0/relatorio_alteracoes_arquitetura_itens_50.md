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

- Correção probatória: o campo `cash_title` dos cartões antigos é legado e não comprova que o título continue utilizável. A string oficial `STR_OLD_TITLE_NOTICE_DESC` declara: “cartão de título que não pode mais ser usado; ao desmontá-lo com o Siel's Hammer, obtêm-se emblemas de título”. O catálogo atual `data/PC/client_titles.xml`, e não o campo residual do item, é a autoridade de existência.
- O Classic 5.0 EU disponível contém exatamente 74 títulos, IDs 408–481. Dos 411 itens com `cash_title`, 337 apontam para IDs fora desse catálogo; 336 deles estão comprovadamente registrados no `siel_hammer.xml`. O item 169611050/ID 279 é o único caso fora do catálogo sem `can_crush` e permanece pendente.
- Foram removidas as 230 ações `titleadd` legadas: 163 já herdadas do Live e 67 inseridas na primeira leitura desta etapa. Nenhum dos cartões antigos agora pode conceder título por duplo clique. Os 74 cartões atuais permanecem sem ação até que seus templates oficiais 408–481 sejam reconstruídos.
- Todos os 74 cartões atuais também possuem `can_crush=TRUE`; isso não conflita com seu uso normal, apenas os torna elegíveis para desmontagem. O sincronizador usa `client_titles.xml` para decidir se um ID é atual e `can_crush`/`crush_name` para classificar os cartões antigos.
- O `player_titles.xml` ainda contém 300 templates legados e não foi substituído nesta correção: naquele ponto, `quest_data.xml` ainda possuía 85 concessões de 67 IDs antigos, e a persistência carrega títulos antigos estritamente. As concessões de quest foram tratadas na Etapa 14; a retirada do catálogo legado continua condicionada à migração dos registros existentes dos jogadores.
- O auditor agora indexa separadamente 74 títulos oficiais, 300 templates legados do servidor e 4.446 itens elegíveis no Siel's Hammer. `cash_available_minute`, `titleadd.titleid` e `titleadd.minutes` só são avaliados como título para IDs presentes no catálogo oficial atual.
- Os 23 testes de `ClassicItemSystemsTest` foram aprovados em Java 25. A regressão confirma que cartões antigos representativos não possuem `TitleAddAction` e resolvem para suas tabelas oficiais do Siel's Hammer.
- Fonte e produto final estão sincronizados: `item_templates.xml` SHA-256 `cb54ecaec4863cdd581a971e38af631af97b44a63239114ee1d7758c39702f9f`; JAR do GameServer permanece `f40839b581bd711e79fe6403822c514cb761176dd2fcf60b928b521d377ce844`.
- Indicadores após a correção: 73.560 compatíveis nos campos auditados, 0 divergências comprovadas e 6.104 pendentes. Os 15 grupos end-to-end continuam em 0/15.

## Etapa 13 — reconstrução dos 74 títulos atuais

- Os 74 títulos oficiais, IDs 408–481, foram reconstruídos diretamente de `data/PC/client_titles.xml`. Nome localizado, raça universal e todos os 253 atributos declarados são rastreáveis ao cliente; nenhum atributo ficou sem mapeamento.
- Os cartões 169611175–169611248 receberam suas ações `titleadd` permanentes. Os 336 cartões antigos comprovados pelo Siel's Hammer continuam sem ação de título e o caso 169611050/ID 279 permanece pendente.
- Atributos `speedratio`, `AttackDelayratio`, `boostCastingTimeratio` e `flyspeedratio` usam décimos de percentual no catálogo atual. Foi introduzido `StatPermilleFunction` para preservar valores como 58 = 5,8%, sem arredondá-los para os inteiros aceitos pela função `rate` legada.
- `CriticalDamageBoost` ganhou um `StatEnum` próprio e integração nos cálculos de crítico de ataques normais e skills, separado das estatísticas defensivas de fortitude. Os valores oficiais 2 e 8 são aplicados como pontos percentuais no multiplicador crítico.
- `AllAttackRatio` e `AllDefendRatio` continuam expandidos para PvP e PvE, conforme a mesma conversão comprovada usada nos itens e skills. Atributos percentuais antigos que incluem `%` continuam usando `rate`.
- Os 300 templates antigos foram preservados como camada interna de compatibilidade para registros persistidos. Eles não voltaram aos cartões atuais; após a Etapa 14, sua retirada definitiva ainda depende de uma migração explícita e segura dos registros existentes no banco e da aposentadoria conjunta das seis condições legadas descritas abaixo.
- Fonte e produto final permanecem sincronizados: `player_titles.xml` SHA-256 `bb00244eca3ccd5be193bf2e2e7af5aab70c81af6d343c91c09d7bda3595f3f8`, `item_templates.xml` SHA-256 `10d15a080e1920084b8eac6b7e6c1ef2160f251e750afcffe9a91f0432d71d1f` e `modifiers.xsd` SHA-256 `b3581b488f1dd273d27ec930112503b726770c1c201402757c510008fc1e0013`. O auditor agora indexa 74 títulos oficiais e 374 templates totais, distinguindo a camada atual da camada legada.
- A regressão automatizada executou os 25 testes de `ClassicItemSystemsTest` e a suíte completa de 136 testes do GameServer em Java 25, sem falhas. A cobertura inclui os extremos 408/481, concessão do cartão atual, exclusão dos cartões legados, precisão de 5,8%/3,5%, bônus crítico e expansão PvP/PvE. O JAR foi produzido em checkout limpo do commit desta etapa e sincronizado no produto final com SHA-256 `bb3f71240b0f147366159fc257d0673268140c8264adef8f6100be71ff333a21`.
- Indicadores após esta etapa: 73.634 compatíveis nos campos auditados, 0 divergências comprovadas e 6.030 pendentes. Os 15 grupos end-to-end continuam em 0/15.

## Etapa 14 — recompensas de títulos em quests

- Foram inventariadas individualmente as 85 concessões de títulos antigos presentes em `quest_data.xml`: 80 pertenciam a 73 quests ausentes das três variantes atuais do cliente e 5 pertenciam às quests 1718, 2368, 2718, 3912 e 4933.
- As cinco quests ainda existentes conservam no arquivo oficial os campos residuais `light_title45`, `dark_title27`, `dark_title45`, `light_title39` e `dark_title39`. Nenhum desses nomes existe entre os 74 registros de `data/PC/client_titles.xml`; por isso, os campos não comprovam uma recompensa funcional no cliente atual e não podem ser convertidos para IDs 1–300.
- As 85 propriedades `title` foram removidas das recompensas, sem alterar experiência, Kinah, AP, itens fixos, itens selecionáveis ou condições das quests. Fonte e produto final ficaram sincronizados com SHA-256 `1d0238b4021e4bcfc0d694d64e8621ec13a35c9b4781a6a0475f8783760b28d4`.
- `parse_quests_50.py` agora resolve títulos exclusivamente pelo catálogo oficial atual e remove qualquer recompensa preservada que aponte para um ID inexistente nele. Isso impede que uma nova execução do importador restaure silenciosamente o legado.
- A rastreabilidade completa, incluindo quest, grupo de recompensa, ID antigo, presença no cliente e motivo da remoção, está em `rastreabilidade_recompensas_titulos_quests_50.csv`.
- Os templates 1–300 continuam carregáveis somente para preservar os títulos já existentes no banco dos jogadores. Esta etapa não apaga registros persistidos nem altera o título exibido por personagens antigos.
- Permanecem seis condições `<required_title>278</required_title>` nas quests legadas 13813, 13820, 13821, 23813, 23820 e 23821, todas ausentes do cliente atual. Elas não concedem títulos e não foram removidas isoladamente, pois retirar apenas a condição poderia reabrir conteúdo antigo; devem ser tratadas junto da desativação integral dessas quests.
- Validação concluída: `quest_data.xml` passou no XSD; o teste específico passou com 26/26 e a suíte completa do GameServer passou com 137/137, sem falhas ou erros.

## Etapa 15 — persistência e compatibilidade dos títulos legados

- O banco ativo foi consultado somente para leitura: há 1 registro legado em `player_titles`, correspondente ao título 101, nenhum registro atual 408–481 e nenhuma referência legada ou atual ativa em `players.title_id` ou `players.bonus_title_id`. Nenhum dado do jogador foi modificado.
- Os 300 templates 1–300 receberam `available="false"`; os 74 títulos 408–481 permanecem disponíveis por padrão. A camada antiga continua carregável para preservar registros históricos, transferências e rollback, mas deixa de representar conteúdo utilizável do cliente.
- `SM_TITLE_INFO` ação 0 agora informa a contagem e serializa somente títulos disponíveis. `CM_TITLE_SET`, `CM_BONUS_TITLE`, `TitleList.addTitle`, a seleção ativa e a aplicação de atributos rejeitam templates indisponíveis.
- Ao carregar o personagem, referências ativas ou bônus que não pertençam à lista atual adquirida são normalizadas para `-1`. O título bônus atual válido volta a aplicar seus atributos depois que os atributos do equipamento são carregados. No login, a ação 1 do `SM_TITLE_INFO` passou a transportar separadamente o título visual e o título bônus persistido.
- Foram criados `update_2026-09-27_classic_titles.sql` e `rollback_2026-09-27_classic_titles.sql`. A migração cria tabelas de arquivo sem cascata, copia títulos e seleções antigas antes de limpar as referências ativas e possui restauração explícita. Ela foi deliberadamente preparada, mas não executada automaticamente.
- As seis condições do título 278 continuam preservadas porque suas quests também são legadas e ausentes do cliente. A remoção deve ocorrer junto da desativação integral das quests, nunca isoladamente.
- Fonte e produto final de dados estão sincronizados: `player_titles.xml` SHA-256 `801a5dc05f0bc8ddda49fe4719fc7dedeac4fba969d2feaf74ddff96aab2549a`; `player_titles.xsd` SHA-256 `9844831ceb7019102317eebc05543d5769e8bfa4c874746096115a6cfc8e3092`.
- A rastreabilidade por componente está em `inventario_persistencia_titulos_50.csv`. A execução da migração no banco e a validação in-game após relog permanecem pendentes e não alteram o indicador end-to-end de 0/15.
- Validação automatizada concluída em Java 25: 27/27 testes específicos, incluindo o payload binário filtrado do `SM_TITLE_INFO`, e 138/138 testes da suíte completa, sem falhas ou erros. Os XMLs de fonte e produto também passaram em seus XSDs.
- A validação in-game revelou que o JAR ainda instalado no produto era a compilação paralela anterior, SHA-256 `8f58b7460e9ae065c32152ff5c8f0767505f3b2784f5923808d72ef69f591280`. A descompilação confirmou que seu `SM_TITLE_INFO` ainda chamava `TitleList.size()` e `getTitles()`, enviando o registro legado 101 junto dos títulos atuais e fazendo a coleção do cliente permanecer em zero.
- O banco ativo confirmou a aquisição dos cartões mostrados no teste: os títulos 408 e 481 possuem um registro cada em `player_titles`. Portanto, não houve perda dos itens nem falha de persistência; o defeito ficou isolado na versão binária do serializer em execução.
- A captura oficial `outros_2026-09-27_16-39-33_00001_20260927163933.pcapng` confirmou o wire da ação 0: `ação C`, `reservado C`, `quantidade H` e, para cada entrada, `titleId D` e `expiração D`. Uma amostra oficial contém seis títulos (455, 460, 463, 473, 474 e 476) em 58 bytes, exatamente o layout implementado na fonte.
- A árvore de trabalho atual, incluindo as alterações paralelas já presentes, foi recompilada em Java 25 e integrada ao produto. O JAR instalado em `GameServer/libs` possui SHA-256 `e2e5a00107f877023db860d4bd0103d34ed0eaaaee4370ed1b9b9e482c174e05`; a descompilação do artefato implantado confirma `availableSize()` e `getAvailableTitles()`. O binário anterior foi preservado temporariamente como `game-server-4.8-SNAPSHOT.8f58b746.pre-title-fix.jar` para recuperação.
- A regressão foi repetida depois da integração: 27/27 testes específicos e 138/138 testes do GameServer passaram. Após reiniciar o GameServer ou fazer novo login com o JAR atualizado, a lista inicial deve restaurar os títulos 408 e 481 já persistidos; essa confirmação visual permanece como o único passo manual deste incidente.
- O primeiro reteste após o boot mostrou uma segunda causa: `PlayerEnterWorldService` enviava somente a ação 1 do `SM_TITLE_INFO`, sem a ação 0 que restaura a coleção persistida. A captura oficial confirma a sequência ação 1 → ação 0 durante a entrada no mundo. O login agora envia os dois pacotes nessa ordem, de modo que os títulos 408 e 481 existentes no banco reapareçam sem consumir novos cartões.
- A mesma captura oficial registra a ação 1 `01 cf01 cf01 0000 00000000`: quando não há título bônus, o terceiro `H` é zero. O serializer foi corrigido para emitir `0000` em vez de `FFFF`, com regressão binária baseada nesse payload.
- A correção de login foi registrada no commit `5b1f5fcd5`. A suíte passou com 28/28 testes específicos e 139/139 testes totais. O novo JAR foi implantado em `GameServer/libs` com SHA-256 `ec4354383d69bcd1e364d8699e6cfce0eb232071ae2a4d09ed01e1a6ec9b88df`; é necessário reiniciar o processo do GameServer para carregar essa versão.
