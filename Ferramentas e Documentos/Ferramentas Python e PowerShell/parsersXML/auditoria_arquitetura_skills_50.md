# Auditoria arquitetural inicial — Skills Aion Classic 5.0 EU

## Escopo e estado

Esta é a auditoria geral exigida antes de alterar regras de jogo. Ela cobre o fluxo de execução, aprendizado, estigmas, itens, NPCs, pacotes, persistência, testes e fontes oficiais disponíveis.

Nenhuma compatibilidade funcional de 100% é declarada. O inventário reproduzível está em `matriz_rastreabilidade_skills_50.csv`; os detalhes por ID e por fonte estão em `auditoria_skills_50_completa.json`.

## Fontes verificadas

- Cliente extraído: `data/skills/client_skills.xml`, overlays `special` e `special2`, arquivos de aprendizado e itens.
- Emulador: templates, árvore de aprendizado, itens, NPC skills, serviços Java, efeitos, propriedades, pacotes e DAOs.
- Capturas autorizadas: 68 PCAPs oficiais existentes no projeto; 66 sessões de jogo com `S_KEY` foram decodificadas em 53 arquivos.
- Histórico Git: migrações e correções de Skills de 14 a 24 de setembro de 2026 foram localizadas. O histórico contém correções relevantes, mas não substitui prova oficial nem teste de regressão.

Limite material da fonte: nenhuma captura contém tráfego da porta 2106. Portanto, as PCAPs não permitem ler o `SM_SERVER_LIST` oficial e provar se o servidor Classic EU seleciona a base, `special` ou `special2`.

## Inventário consolidado

| Medida | Total |
|---|---:|
| IDs na união cliente/emulador | 12.140 |
| IDs no cliente base | 12.114 |
| Templates no emulador | 12.139 |
| IDs oficiais ausentes no emulador | 1 (`50068`) |
| Templates sem definição no cliente base | 26 |
| Skills na árvore de jogador | 3.969 |
| Skills referenciadas por NPCs | 2.769 |
| Skills observadas em casts do cliente nas PCAPs | 184 |
| Skills observadas em casts do servidor nas PCAPs | 347 |
| Skills com diferença entre variantes do cliente | 241 |
| Skills alteradas especificamente por `special2` | 234 |
| Referências de itens ainda sem resolução no namespace principal | 218 |

As categorias se sobrepõem. A matriz marca ativas, passivas, buffs, debuffs, transformações, estigmas, Skills de item/equipamento, NPC/boss e especiais.

## Bloqueio de variante do cliente

O relatório legado usava apenas `data/skills/client_skills.xml`. Isso é insuficiente para o Classic 5.0 extraído:

- `special2/client_skills.xml` altera 234 Skills e 864 campos;
- 222 dessas Skills aparecem na árvore de jogadores;
- há 111 mudanças de `pve_damage_ratio` e 38 de `pvp_damage_ratio`;
- o modelo do servidor representa `pvp_damage`, mas não possui campo equivalente para `pve_damage_ratio`;
- todas as 38 razões PvP divergentes hoje coincidem com a base, não com `special2`.

O arquivo `SM_SERVER_LIST.java` do emulador envia `0x00000401` (Classic + visible), mas a relação desse bit com os diretórios de overlay ainda não está comprovada por captura oficial nem por análise suficiente do binário. Até essa prova, nenhuma das 234 Skills deve ser corrigida automaticamente para `special2`.

## Fluxo completo de execução

1. `CM_CASTSPELL` lê ID, nível, tipo de alvo, objeto/coordenadas e tempo de impacto.
2. `PlayerController.useSkill` valida conhecimento/contexto e cria a execução.
3. `Skill.canUseSkill` valida estado, recursos, alvo, alcance e condições.
4. `Skill.useSkill` calcula cast/animação, muda estado e envia `SM_CASTSPELL`.
5. `Skill.endCast` revalida alvo/alcance, consome recursos, cria efeitos, calcula resistência/conflito, aplica cooldown e dispara cadeias.
6. `Effect.applyEffect` e `EffectController` aplicam dano, cura, estado anormal, stacking, substituição e término.
7. `SM_CASTSPELL_RESULT`, `SM_ABNORMAL_EFFECT` e pacotes relacionados sincronizam o cliente.
8. `PlayerSkillListDAO`, `PlayerEffectsDAO` e `PlayerCooldownsDAO` persistem aprendizado, efeitos elegíveis e cooldowns longos.

## Achados arquiteturais prioritários

### P0 — identidade da fonte oficial

- A seleção do overlay não está provada.
- Os 661 `pve_damage_ratio` não neutros encontrados na base não têm representação explícita no `SkillTemplate`/XSD. Não foi demonstrado se foram incorporados a coeficientes dos efeitos.
- O cliente tem grafias e caixas inconsistentes em enums e efeitos; normalização precisa preservar semântica e não apenas comparar texto.

### P0 — cobertura e qualidade dos templates

- 1 ID oficial não possui template: `50068` (`action_pet_pc_doping3`). Nas três variantes oficiais, essa entrada possui somente ID, nome, textos e ícone; não declara ativação, tipo, subtipo, alvo, custo, tempo ou efeitos. A busca integral pelo nome não encontrou outra definição oficial nem ocorrência no código. Ela foi classificada como ação de cliente não executável sem template, justificadamente pendente; criar um template exigiria inventar campos.
- 26 templates não existem na base oficial: `418`, `459`, `460`, `854`, `993`, `1120`, `1129`, `1264`, `1266`, `1514`, `2075`, `2381`–`2388`, `8397`, `21922`–`21927`.
- 31 Skills usam tipos oficiais sem correspondência registrada no motor; 3 ainda usam tipos cuja classe Java está vazia (`Activate_Enslave` e `Dummy`). As 3 Skills de coleta `2521`–`2523` deixaram essa lista após `UtilityEffect` passar a aplicar o ciclo de buff e os modificadores já declarados no XML.
- Os campos oficiais de alcance e seleção foram sincronizados em 8.349 templates; permanecem diferenças de slot, efeitos e outros subsistemas que a matriz não chama de erro sem prova.

### P0 — ausência de testes de Skills

- A auditoria encontrou `maven.test.skip=true`; nesta etapa o padrão foi alterado para `false`, de modo que `mvn test` execute a suíte sem flags especiais.
- Executando `mvn test` com a configuração corrigida, 113 testes passam com Java 25.
- Seis testes estruturais de Skills foram adicionados nesta etapa: unicidade/cobertura de IDs, referências de jogador/NPC, tags de efeito no XSD, sincronização byte a byte entre fonte/produto, garantia de que `UtilityEffect` use o ciclo de buffs e proibição de mensagens inexistentes no motor de Skills.
- Ainda não existe teste comportamental de Skill/efeito/estigma. O sucesso atual não valida combate.

### P1 — seleção de alvo e protocolo

- `CM_CASTSPELL` lê `targetObjectId`, mas não o repassa a `PlayerController.useSkill`; a execução usa o alvo atualmente selecionado no estado do jogador.
- Isso pode ser correto para o protocolo, mas precisa ser comparado com trocas rápidas de alvo, alvo fora de visão e tipos 3/4 nas PCAPs antes de ser preservado.
- Pacotes de cast/result já contêm várias adaptações 5.0 comprovadas, mas ainda há campos desconhecidos e regras hardcoded.
- O aviso de distância usava o ID legado inexistente `1402920`, causa direta do texto `???`; foi substituído pelo ID oficial Classic `1300022` (`STR_SKILL_TOO_FAR`). Após a correção, nenhuma chamada direta do motor de Skills referencia mensagem ausente no cliente oficial.
- A validação de `add_wpn_range` substituía incorretamente distâncias-base maiores pelo alcance da arma (por exemplo, 15 m viravam aproximadamente 2 m). A regra voltou a somar alcance-base e alcance da arma, e os campos de distância/alvo/forma de área foram reconstruídos a partir do cliente 5.0.

### P1 — defesa e resistência

- O caminho comum testa evasão ou resistência mágica em `EffectTemplate`, reduz dano por defesa física/mágica e elemental em `AttackUtil`/`StatFunctions`, aplica ratios defensivos PvP/PvE e, por fim, escudos.
- A auditoria específica enumerou 38 Skills com dano `NoReduce`, 3 stacks de proc com dano fixo hardcoded, 31 Skills de dano atrasado que ignoram escudos e 287 Skills mágicas com efeito sem elemento que exigem revisão individual da conversão.
- Foram encontradas 83 divergências nas quais o servidor declara ou força `noresist` enquanto o campo oficial do efeito é `0`; 46 atingem alvo `Enemy`. Elas não foram alteradas automaticamente porque efeitos secundários podem herdar o acerto do primeiro efeito e isso depende de lógica do servidor não comprovada pelo XML isolado.
- A matriz detalhada de bypasses está em `auditoria_mensagens_defesa_skills_50.json`; nenhum caso foi tratado como erro apenas pelo nome do efeito.

### P1 — Skills temporárias e persistentes

- `PlayerSkillList` mantém Skills permanentes e temporárias no mesmo mapa por ID.
- Uma Skill temporária pode elevar uma entrada permanente existente sem registrar a origem temporária.
- A remoção sempre marca a entrada como `DELETED`; isso exige testes de equipar/desequipar estigma ou item quando o mesmo ID já foi aprendido por outra origem.
- A origem de concessão deve ser rastreável para impedir que remover uma fonte apague outra fonte ainda válida.

### P1 — stacking, conflito e buffs independentes

- `EffectController` indexa efeitos pelo `stack` do template. Dois efeitos independentes com stack igual colidem por construção.
- Há exceções por `conflict_id`, `effectId`, categorias de dispel e IDs hardcoded.
- A exigência de não unir buffs distintos depende tanto da correção do XML quanto de testes de coexistência no controlador.
- Os testes devem cobrir aplicação simultânea, renovação, substituição por nível, dispel parcial, toggle/chant, morte e relog.

### P1 — persistência

- Efeitos e cooldowns com 28 segundos ou menos restantes não são persistidos.
- A regra pode ser correta, mas não está vinculada a evidência Classic 5.0 no código e precisa de teste de fronteira (27.999/28.000/28.001 ms).
- O carregamento de efeitos restaura skill, nível, tempo e `force_type`; a auditoria ainda precisa provar interação com morte, troca de personagem e limpeza de efeitos expirados.

### P1 — NPCs e bosses

- A auditoria encontrou `NpcSkillList` removendo do próprio `List` carregado em `DataManager` qualquer Skill sem template durante a construção de uma instância. A mutação global foi eliminada nesta etapa; uma referência inválida agora é apenas ignorada para a instância e registrada no log.
- As definições de NPC/boss são predominantemente server-side; `client_npcs.xml` não fornece uma lista completa de Skills de combate.
- Fases, prioridades, probabilidade, cooldown, alvo e spawns acionados precisam ser validados por PCAP e scripts de IA, não apenas por `client_skills.xml`.

### P2 — legado 4.8 e hardcodes

- A regra de charge/cast contém comentário e fonte web de 4.8; isso não é evidência definitiva para Classic 5.0 EU.
- O controlador de efeitos contém IDs específicos para conflitos/cooldowns, remoção e Avatar.
- Existem TODOs em resistência, controle, transformação, movimento, hate, alcance, voo e efeitos especiais.
- O nome Maven/JAR ainda usa `4.8-SNAPSHOT`; isso não prova comportamento 4.8, mas dificulta rastreabilidade de artefato e deve ser tratado separadamente da regra de jogo.

## Classificação de componentes legados

| Classificação | Tratamento nesta reconstrução |
|---|---|
| Compatível com Classic 5.0 | Preservar somente após teste e fonte registrada |
| Parcialmente compatível | Isolar a diferença, adaptar XML/Java e testar dependências |
| Exclusivo do Live 4.8 | Remover apenas com prova e análise de consumidores |
| Inexistente no emulador | Implementar somente com parâmetros oficiais suficientes |
| Sem evidência suficiente | Manter pendente e visível na matriz |

## Alterações implementadas e verificadas nesta etapa

| Escopo | Evidência | Alteração | Verificação |
|---|---|---|---|
| Inventário integral | Cliente base/`special`/`special2`, dados do emulador e 68 PCAPs autorizados | Gerador reproduzível, JSON detalhado e matriz CSV com 12.140 IDs | Regeneração completa sem descarte silencioso de IDs |
| NPC Skills | `NpcSkillList` e lista compartilhada de `DataManager` | Uma referência inválida deixa de remover globalmente a definição carregada; passa a ser ignorada apenas na instância | Compilação Java 25 e suíte Maven |
| Skills `2521`–`2523` | Tipos oficiais `Utility`, árvore de Skills e modificadores já presentes no XML | `UtilityEffect` passou a herdar o ciclo de `BufEffect`, registrando e removendo os três modificadores declarados | Teste estrutural dedicado e suíte Maven |
| Mensagem de Skill fora de alcance | Cliente oficial: `STR_SKILL_TOO_FAR`, ID `1300022`; ID legado `1402920` ausente | Substituição do envio legado em `FirstTargetRangeProperty` | Teste cruza todas as chamadas do motor de Skills com `client_strings_msg.xml` |
| Alcance e seleção de alvo | `first_target_valid_distance`, `add_wpn_range`, `revision_distance`, `target_range` e `target_range_opt1..4` do cliente | 8.349 templates sincronizados; fórmula de alcance da arma corrigida | Auditor idempotente, teste estático de 12.114 Skills e testes unitários da soma de alcance |
| Execução de testes | `maven.test.skip=true` no POM raiz | Testes habilitados por padrão | `mvn test`: 113 testes, 0 falhas, 0 erros, 0 ignorados |
| Produto final | JAR reconstruído a partir do código testado | JAR do GameServer sincronizado | SHA-256 idêntico entre `target` e produto final |

Esta tabela registra apenas o que foi efetivamente alterado. Não promove as demais Skills a compatíveis nem transforma diferenças estáticas em bugs confirmados.

## Plano por dependência e prioridade

### Fase 0 — fundação de evidência

1. Provar a seleção `base`/`special`/`special2` pelo cliente oficial (captura de login autorizada ou análise verificável do loader).
2. Tornar o auditor parte do fluxo de validação e impedir desaparecimento silencioso de IDs.
3. Criar testes de invariantes XML/JAXB: IDs únicos, referências existentes, slots de efeito únicos, classes Java registradas e source/prod sincronizados.

### Fase 1 — motor antes dos valores

1. Testar e corrigir proveniência de Skills temporárias/permanentes.
2. Testar stacking independente, conflito, dispel, toggle/chant e persistência.
3. Resolver os efeitos Java vazios e os tipos sem representação, sem fallback inventado.
4. Definir representação comprovada para PvE ratio ou documentar onde o coeficiente já foi incorporado.

### Fase 2 — Skills de jogador

1. Agrupar por classe e progressão, começando pelas Skills observadas em PCAP.
2. Para cada grupo: template, custo, alvo, alcance, cast, cooldown, cadeia, efeitos, pacotes, morte/relog/interrupção.
3. Auditar passivas e requisitos de arma antes das ativas que dependem desses atributos.

### Fase 3 — buffs, debuffs e transformações

1. Validar duração, stack, prioridade, substituição, dispel, imunidade e persistência.
2. Validar aparência, tribo, atributos, velocidade e restrições de Skills durante transformação.
3. Executar cenários de coexistência de buffs distintos e troca de equipamentos.

### Fase 4 — estigmas, itens e equipamentos

1. Resolver as 218 referências de namespace pendentes.
2. Testar slots, pré-requisitos, shard, encantamento, equipar/desequipar e múltiplas fontes do mesmo ID.
3. Validar procs, godstones, Skills de item e restrições de arma por PCAP existente.

### Fase 5 — NPCs e bosses

1. ~~Eliminar mutação de dados compartilhados no carregamento de NPC Skills.~~ Concluído e coberto pelo invariante que exige referências resolvidas nos dados atuais.
2. Inventariar cada referência de NPC/boss, IA, fase e condição.
3. Priorizar os 347 IDs observados no servidor e manter os demais como estáticos não validados.

### Fase 6 — regressão e produto final

1. Testes de relog, troca de personagem/equipamento, morte, ressurreição, interrupção, concorrência e expiração.
2. Comparação wire-format com PCAP para os casos cobertos.
3. Sincronização source/prod e verificação por hash.
4. Somente então promover Skills individualmente de pendente para validada.

## Critério operacional de conclusão

Uma Skill só é considerada validada quando a matriz contém: fonte oficial, template, caminho de execução Java, efeitos, origem de aprendizado/uso, testes automatizados pertinentes e resultado esperado. Skills sem PCAP podem ser validadas estaticamente apenas nos campos definidos pelo cliente; comportamento exclusivo do servidor permanece pendente.

Enquanto existir qualquer ID sem template, sem representação de efeito, sem teste necessário ou sem evidência suficiente, a compatibilidade de 100% permanece proibida.
