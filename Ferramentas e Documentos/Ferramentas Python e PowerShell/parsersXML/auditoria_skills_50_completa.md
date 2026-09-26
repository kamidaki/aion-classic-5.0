# Auditoria rastreável das Skills — Aion Classic 5.0 EU

## Resultado desta etapa

O inventário contém **12140 IDs** na união das fontes: 12114 no cliente base e 12139 no emulador.
Há **1 ID oficial ausente no emulador**, **26 templates sem definição na base do cliente** e **241 Skills com divergência entre variantes do mesmo cliente**.
Nenhuma dessas categorias autoriza remoção ou correção automática. O relatório registra evidência e mantém lacunas como pendências.

### Lacunas de definição por ID

- Oficial sem template: `50068`.
- Entrada oficial sem dados executáveis e sem template: `50068`.
- Template sem definição na base oficial: `418`, `459`, `460`, `854`, `993`, `1120`, `1129`, `1264`, `1266`, `1514`, `2075`, `2381`, `2382`, `2383`, `2384`, `2385`, `2386`, `2387`, `2388`, `8397`, `21922`, `21923`, `21924`, `21925`, `21926`, `21927`.
A classificação de entrada não executável exige ausência simultânea de ativação, tipo, subtipo e efeitos no cliente. Ela documenta a lacuna, mas não autoriza inventar um template.

## Bloqueio de fonte identificado

O overlay `special2` diverge da base em 234 Skills. As capturas disponíveis contêm **0 pacotes na porta 2106**, portanto não comprovam qual overlay foi selecionado pela lista oficial de servidores.
O emulador anuncia o bit Classic, mas isso não demonstra sozinho se o cliente usa `base`, `special` ou `special2`. Até essa seleção ser comprovada, os valores divergentes ficam classificados como `PENDENTE_VARIANTE_CLIENTE`.

## Cobertura verificável

Foram lidos 68 PCAPs, com 66 sessões de jogo decodificadas. Há 184 IDs lançados pelo cliente e 347 IDs anunciados pelo servidor nas capturas.
A presença no PCAP comprova que o ID foi usado; não comprova por si só dano, duração, prioridade, persistência ou todas as transições internas.
Há 218 referências de itens não resolvidas no namespace principal de Skills; elas permanecem enumeradas no JSON e não foram descartadas.
Existem 12136 templates sem referência direta ou indireta encontrada nos testes Java atuais.

## Estado por classificação

| Classificação | Skills |
|---|---:|
| ALINHADO_ESTATICAMENTE_NAO_VALIDADO | 4336 |
| AUSENTE_EMULADOR | 1 |
| DIVERGENTE_ESTRUTURAL | 7718 |
| EFEITO_JAVA_STUB | 3 |
| EFEITO_SEM_REGISTRO_JAVA | 31 |
| ENTRADA_CLIENTE_NAO_EXECUTAVEL_SEM_TEMPLATE | 1 |
| OBSERVADA_EM_PCAP | 349 |
| PENDENTE_VARIANTE_CLIENTE | 241 |
| SEM_DEFINICAO_CLIENTE_BASE | 26 |

## Divergências estruturais por campo

| Campo | Skills |
|---|---:|
| properties.first_target_range | 6384 |
| effect1 | 1197 |
| properties.first_target | 897 |
| tslot | 709 |
| properties.target_maxcount | 672 |
| pve_damage_ratio | 661 |
| skillsubtype | 620 |
| effect2 | 442 |
| properties.target_distance | 418 |
| effect3 | 160 |
| cooldown | 120 |
| pvp_damage | 79 |
| effect4 | 56 |
| effect0 | 2 |
| template_ausente | 1 |

## Categorias (sobrepostas)

| Categoria | Skills |
|---|---:|
| acao_cliente | 1 |
| ativa | 10765 |
| buff | 3267 |
| debuff | 1685 |
| especial | 1091 |
| especial_ou_interna | 103 |
| item_equipamento | 3852 |
| jogador | 3969 |
| npc_boss | 2769 |
| passiva | 1268 |
| stigma | 1953 |
| transformacao | 574 |

## Critério de conclusão

`ALINHADO_ESTATICAMENTE_NAO_VALIDADO` não significa compatibilidade funcional. Uma Skill só poderá ser promovida a validada após teste de execução e, quando aplicável, comparação com PCAP oficial. Nenhuma Skill sem evidência foi contada como correta.

## Artefatos

- `auditoria_skills_50_completa.json`: evidência completa, inclusive diferenças de overlays.
- `matriz_rastreabilidade_skills_50.csv`: matriz por ID para triagem e acompanhamento.
- `audit_50_skills_complete.py`: gerador reproduzível e somente-leitura sobre as fontes.
