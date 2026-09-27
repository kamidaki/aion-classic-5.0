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
