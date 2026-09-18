# Sistemas de itens Classic 5.0 — 18/09/2026

## Alterações

- Enchant com essência 166300500: regras de custo, quantidade de pedras, probabilidade por diferença de nível e transições importadas do client. Revalidação de posse, materiais e nível após a animação, cancelamento de uso e resposta de animação Classic.
- Descarte: bit DELETABLE usa `breakable`, não `item_drop_permitted`. Preserva proteção de Kinah, itens equipados e não destrutíveis. O registro antigo de CM_DELETE_ITEM sobrescrevia CM_VIEW_PLAYER_DETAILS.
- Expansão: ligação do pedido com o serviço de NPC; revalidação de alcance, estágio e capacidade antes de cobrar; cabeçalho inicial mantém capacidade mesmo no inventário vazio e inclui expansões por item.
- Arcamant: os 12 itens `seed` usam grupo ARCAMANT, slot próprio e regras `seed_enchant`.
- Power Talent: substituição das estimativas antigas por contribuições oficiais de itens, qualidade, nível do item, enchant, manastones, fusão e skills. Ainda não constitui implementação completa do sistema: título, recompensas de experiência, additional_option e moros não estão conectados, e o transporte para a ficha requer confirmação.

## Evidência

Dados: `3 - Client 5.0 - Dados Extraidos/data/items/client_items.xml`, `client_enchant_count_prob.xml`, `client_enchant_gap_level_prob.xml` e `data/gamedata/client_combat_power_rule.xml`.

A captura `06_Sistemas_Novos_5.0/*Enchantando*` contém pedido C 0x005A de 38 bytes e resposta S 0x01C3 de 20 bytes, com duração 5000 no início e duração 0 no fim.

A captura indicada `Outros/subida-1-60-2026-08-28.pcapng` foi analisada; não foi isolado nela um descarte nem uma expansão paga que confirme os novos registros. O opcode de descarte 0x0108 (decodificado 0x007A), o tipo 0 de CM_CUBE_EXPAND e o campo de expansão por item do cabeçalho inicial precisam de validação de integração no client 5.0.

Atribuir Power Talent aos offsets 252/388 de S_STATUS não foi confirmado: há valores pareados nos captures que não correspondem a uma pontuação total. O transporte existente foi preservado nesta alteração; não se considera a exibição na ficha resolvida.

## Verificação

- Maven package Java 25: BUILD SUCCESS.
- ClassicItemSystemsTest: 4 testes, 0 falhas, 0 erros. Carrega os XMLs reais com JAXB e verifica essência, custos/transições, 12 Arcamants, descarte e pontos de enchant.
- item_templates.xml e classic_item_systems.xml: schemas XSD válidos; schema principal compilado.
- Gerador repetido: 0 templates alterados, 3637 regras oficiais. Agora valida schemas antes de escrever.
- XMLs, schemas e JAR sincronizados no Produto Final. A ativação requer reinício do GameServer; não houve teste visual no client.

Gerar novamente: `python "6 - Ferramentas/parsersXML/parse_classic_item_systems.py" --aplicar` (Python com lxml).

Testar: `mvn -f "1 - Código Fonte [Emulador]/pom.xml" -pl game-server -am package -Dmaven.test.skip=false -Dtest=ClassicItemSystemsTest -Dsurefire.failIfNoSpecifiedTests=false -Dassembly.skipAssembly=true`.

## Correções após teste no client — enchant e Arcamant

- `client_mask` é gerado a partir do XML oficial e separado do ItemMask interno. GENERAL_INFO agora envia essa máscara: essência 166300500 = 0x6128; Arcamant 130000011 = 0x402C; torso épico 110601334 = 0x8028. O bit de breakable interno anteriormente era interpretado como requisito de soul bind no client.
- Verificação com 213 itens nas capturas de Inventário, Enchant e Stigma: 210 máscaras coincidem integralmente. As três divergências são itens de assembly de quest cujo bit de venda é removido pelo servidor oficial; essa diferença de estado não foi inferida como mudança global de template.
- 3.483 templates com enchant_group tiveram o bit interno NO_ENCHANT corrigido segundo o client, permitindo os equipamentos oficialmente encantáveis além dos Novice.
- Os dois IDs 166300000 e 166300500 têm enchant_essence=true e usam o mesmo serviço de custos, quantidade de pedras e probabilidades oficiais.
- A mensagem de sucesso usa STR_ENCHANT_ITEM_SUCCEED (1300455). O código anterior 1401681 não existe com esse nome no XML de mensagens 5.0 e exibiu a solicitação de grupo interservidor.
- S_SERVER_ENV estava truncado em 37 bytes, com valores diferentes dos oficiais. Agora envia o corpo completo de 60 bytes medido na captura de Enchant, preservando a configuração de reentrada e usando timestamp atual. Esta correção fornece os campos de configuração que faltavam às interfaces novas; a aparição da porcentagem na janela ainda requer verificação visual. Não se atribuiu um nome sem evidência a cada campo desconhecido.
- A busca nos inventários das capturas disponíveis não encontrou um blob de Arcamant para confirmar se seu layout de slots exige uma entrada distinta de SLOTS_WING. O slot próprio e a máscara foram corrigidos; o layout existente foi preservado enquanto essa evidência falta.
- Maven package: BUILD SUCCESS; ClassicItemSystemsTest: 7 testes, 0 falhas, 0 erros. Testes verificam ambos os IDs, Arcamants, permissão de enchant de armadura épica, máscara serializada, mensagem Classic e corpo completo de configuração.
- XMLs e schema validados e sincronizados; JAR atualizado no Produto Final. Gerador repetido sem alterações. Reiniciar GameServer e entrar novamente no personagem para recarregar a configuração e os blobs.

## Retorno de validação — Arcamant, falha e interfaces

- Arcamant: havia slot próprio, mas ItemGroup ainda retornava EquipType.NONE e ItemInfoBlob serializava SLOTS_WING. Agora a classificação é ARMOR/ACCESSORY e o blob fornece slot próprio em SLOTS_ACCESSORY. O teste valida o tipo de equipamento, ausência de entrada de asas e os 16 bytes de slots. Esta é uma correção da inconsistência do modelo; o layout específico ainda requer confirmação no client, pois as capturas disponíveis não contêm Arcamant.
- Falha: conforme solicitação do usuário, a tabela gerada do emulador agora usa `max(0, before - 1)`. A tabela original do client mantém o nível e foi preservada. A adaptação fica no gerador, sem constante de perda de nível no serviço Java.
- Version.dll: o parâmetro -probability agora é adicionado também quando o launcher já fornece -classic. Antes, a presença de -classic pulava todo o bloco que adicionava o parâmetro. Compilação MSBuild x64 e x86 concluída; DLLs sincronizadas em `4 - Patch para o Client 5.0/bin64` e `bin32`. Ainda não instaladas no client de jogo: falta seu caminho.
- Porcentagem e Combat Talent: ainda não considerados resolvidos. A configuração oficial de 60 bytes não bastou no teste do usuário. É necessário conferir o Game.dll do client utilizado e uma resposta com pontuação/probabilidade ativa. Não foram inventados novos opcodes de UI nem transferida a pontuação para outro offset sem evidência.
- A varredura adicional de S_STATUS encontrou inclusive texto ASCII e valores residuais em campos desconhecidos (34..39 e outros), reforçando que um campo não zero, sozinho, não identifica Combat Talent.
- Verificação: Maven BUILD SUCCESS; 8 testes, 0 falhas, 0 erros. JAR e classic_item_systems.xml sincronizados no Produto Final, com hashes iguais entre fonte e produto. O teste visual após reinício ainda é necessário.

## Confirmação pelo binário do client — 18/09/2026

- Combat Talent: o handler S_STATUS em Game.dll, RVA 0x8A8880, copia 256 bytes a partir do byte 8 do payload para o bloco atual de atributos. A ficha obtém esse bloco em 0x7A4140 e lê a pontuação em atributos + 0xCC, em 0x606790. Portanto o campo correto é o DWORD no byte 212. SM_STATS_INFO foi corrigido; as injeções nos bytes 252 e 388 foram removidas. A captura oficial de Enchant confirma pontuações 644 e 5337 nesse campo, além de zero. O pacote continua com 412 bytes.
- Arcamant: a tabela de equipamento em 0xD59E18 confirma equip_seed após equip_rhand2/equip_lhand2. O decoder de blobs em 0x80ABB0 lê dois uint64 para as entradas 0x04 e 0x0D (assim como 0x01 e 0x05). A entrada de acessórios de 16 bytes corrigida é compatível com esse leitor. A entrada de asas também foi corrigida de 8 para 16 bytes para preservar o enquadramento da entrada seguinte. Os bônus oficiais STR/VIT/AGI/DEX/KNO/WIL, antes ignorados pelo parser, foram mapeados e os 12 seeds regenerados.
- Porcentagem: Game.dll, RVA 0x4EE810, testa o bit 82 antes de calcular e formatar a taxa localmente. Aion.bin registra -probability com uma função que ativa exatamente esse bit (0x2C510); -probability2 ativa o bit 102 e não substitui essa opção. O fluxo de inicialização recebe a linha guardada pelo CRT (0xB84A0 -> 0x91CC -> 0x9EAC -> 0xA9E8), em vez de consultar necessariamente o GetCommandLine interceptado nesse ponto. Por isso o parâmetro agora consta na linha real dos dois BATs do patch e no Start_Classic.bat do client informado. O log do hook sozinho não prova que o parser recebeu a opção. Não se alterou Game.dll nem se inventou um pacote de taxa.
- Os dois IDs 166300000 e 166300500 pertencem à faixa reconhecida pelo classificador em 0x260FB0 e continuam suportados pelo serviço. A redução de um nível em falha permanece conforme pedido do usuário.
- Ainda é necessária validação visual após fechar/reabrir o client pelo BAT atualizado e reiniciar o GameServer. A análise estática confirma o protocolo; não houve teste de interação com personagem nesta etapa.
- Verificação final: Maven BUILD SUCCESS; 10 testes, zero falhas/erros. JAR e item_templates.xml sincronizados no Produto Final. O BAT anterior do client foi preservado em scratch/Start_Classic.before_enchant_probability.bat; as opções de rede e idioma foram mantidas.
