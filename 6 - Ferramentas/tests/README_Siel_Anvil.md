# Bigorna de Siel — Classic 5.0

Implementação: `CM_SIEL_ANVIL` → `SielAnvilService` → tarefa de interação → inventário persistente → `SM_SIEL_ANVIL_START` / `SM_SIEL_ANVIL_RESULT`.

## Evidência

Captura: `5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/06_Sistemas_Novos_5.0/06_Sistemas_Novos_Siel_Anvil_5.0_2026-09-11_18-20-22_00001_20260911182022.pcapng`.

53 pacotes de cliente e 620 de servidor decifrados, todos com checksum válido. A captura contém uma fabricação, receita 170, sem interação com NPC.

| Etapa | Opcode decodificado | Payload |
|---|---|---|
| Pedido | C `0x0108` (wire `0x01FA`) | `aa00000000000000000002006089e909040000000134df0a801a060001` |
| Início | S `0x01A3` | `aa00000001b80b0000` |
| Resultado | S `0x01A4` | `aa000000010100020000` |

Pedido: receita `D`, grupo de materiais (índice a partir de zero) `D`, tamanho `H` do vetor de equipamentos selecionados seguido de seus object IDs `D`, tamanho `H` da lista de materiais comuns, pares `(D itemId, D quantidade por tentativa)`, quantidade de tentativas `C` (1–255). Os custos são conferidos contra o grupo exato do XML e multiplicados no servidor. O cliente limita receitas com seleção de equipamento a uma tentativa.

Início: receita `D`, evento `C` (0 rejeição, 1 início, 2 Stop), duração `D = 3000 ms`. Resultado: receita `D`, flag `C = 1`, tamanho `H`, vetor de resultados `C` (1 produto normal, 2 segundo produto, 3 falha), progresso garantido `H`. O valor 2 da captura corresponde ao segundo produto, item `174000001`. Para uma tentativa sem progresso, o payload anterior é idêntico ao confirmado na PCAP.

Complemento de análise em 17/09/2026: rotinas do Game.dll do cliente Classic 5.0: serializador do pedido RVA `0x89AF80`, envio `0x78AA10`, construção do grupo comum `0x2D44C0`, identificação dos materiais selecionáveis `0x201B00`, comando Stop `0x2D1E00`, transformação do opcode `0x1D32D0`, recepção de evento `0x8CEE40`, recepção do resultado `0x8CEF00`, vetor de resultados e progresso `0x8D8C90`, enum visual de resultados `0x21B770`. O Stop usa enum interno `0x139`, convertido para wire `0x1FB`. Essas variantes foram verificadas no código do cliente; a captura fornecida continua contendo apenas uma fabricação única.

SHA-256 do Game.dll analisado: `BE18B7EC8C4480ADF7B0F5184BB0D446DC09FF99F734B8046CC705F19CAA213C`. O cliente foi somente lido.

A captura usa timestamps em nanossegundos; o intervalo entre início e resultado é aproximadamente 3,046 s. O helper antigo `aion_pcap.py` devolve os valores brutos da interface, não segundos.

Receita 170: `166300000 × 4` + `182400001 × 400000` (Kinah). A variante principal `data/items/client_item_special_craft.xml` corresponde à captura; as variantes `special`/`special2` têm custos diferentes e não são sobrepostas. Produtos: 80% primeiro, 20% segundo, conforme probabilidades de base 10000 no XML.

## Dados e limites atuais

`parsersXML/parse_siel_anvil.py` converte as 388 receitas, resolve os nomes canônicos pelos templates do servidor e falha se faltar algum item. O carregamento usa JAXB, XSD e o fluxo normal de `StaticData`/`DataManager`.

97 receitas visíveis estão habilitadas, incluindo as receitas com garantia 102, 118, 145 e 177. Ganho mínimo/máximo e teto vêm do XML oficial. O progresso fica em `player_siel_anvil`, é restaurado no login pelo pacote `S_SPECIAL_COMBINE_RECIPE_INFO` (`0x1AB`: tamanho `H`, pares receita `D` / pontos `H`, modo `C`) e atualizado no resultado. Ao alcançar o teto, a próxima tentativa produz o primeiro produto; sucesso zera o progresso. Se a gravação falhar, o serviço devolve os custos e rejeita a tentativa.

Instalações existentes devem aplicar `2 - Emulador [Produto Final]/GameServer/sql/update_2026-09-17_siel_anvil.sql`. A tabela também está no SQL completo para instalações novas. A migração foi aplicada e a estrutura conferida no banco local desta execução. As receitas ocultas e com limites temporais/por conta/servidor permanecem desabilitadas com motivo no XML.

A fabricação revalida estado do jogador, custos e espaço após três segundos; não desconta antes da conclusão. Requisições duplicadas durante a tarefa, receitas desconhecidas, materiais repetidos, quantidades adulteradas, pacotes truncados, comércio/loja, morte e logout não produzem itens. Equipamentos devem pertencer ao inventário e estar desequipados; o serviço consome os objetos selecionados pelo cliente. Os custos aceitos devem corresponder exatamente ao grupo solicitado. A escolha do produto ocorre somente depois da validação e do débito. Falhas usam todos os retornos definidos no XML; para equipamento retornado do mesmo tipo, `ItemService` copia os atributos do material selecionado. O Stop cancela a tarefa sem débito e ignora uma conclusão atrasada. A entrega usa o fluxo normal de atualizações e persistência do inventário.

O espaço considera os resultados mutuamente exclusivos e todas as combinações possíveis do lote, incluindo pilhas já existentes e itens retornados do mesmo tipo. Assim, 50 tentativas que geram um equipamento cada exigem até 50 espaços, mesmo que existam dois produtos possíveis. A validação é conservadora quanto aos espaços que serão liberados ao consumir materiais.

## Verificação reproduzível

Execute a partir da pasta `Classic`:

```powershell
python '6 - Ferramentas/parsersXML/parse_siel_anvil.py'
mvn -f '1 - Código Fonte [Emulador]/pom.xml' -pl game-server -am package '-DskipTests' '-Dassembly.skipAssembly=true'
java -cp '1 - Código Fonte [Emulador]/game-server/target/classes;2 - Emulador [Produto Final]/GameServer/libs/*' '6 - Ferramentas/tests/SielAnvilChecks.java' '1 - Código Fonte [Emulador]/game-server/data/static_data'
```

O teste independente passou em 116 verificações. Verifica os payloads oficiais byte a byte, leitura completa do pedido, truncamentos, duplicação de materiais, custos alterados, quantidade em lote, grupos alternativos, objetos selecionados, pedidos de asa e dos dois grupos do anel 102 passando do parser à resolução de custos (incluindo dois equipamentos do mesmo tipo), rejeição de equipamento ausente/equipado, probabilidades exatas, retornos de falha, limites de progresso, cancelamento e conclusão atrasada, XSD e integração JAXB. Verifica também o carregamento das classes `TemporarySpawnEngine`, `PlayerRestrictions` e `PlayerLeaveWorldService` em uma JVM nova. Não inicia o servidor nem altera o banco de dados. O teste ponta a ponta no cliente deve confirmar:

1. Reiniciar o GameServer com o JAR e XMLs atualizados.
2. Fabricar a receita 170 tendo quatro essências, 400.000 Kinah e espaço livre.
3. Observar barra de três segundos, débito único e recebimento de um dos dois produtos.
4. Repetir sem recursos e com inventário cheio: nenhum débito.
5. Sair durante a barra: nenhum débito nem entrega; relogar e conferir inventário.
6. Validar apresentação de falha/devolução numa receita com chance inferior a 100%.
7. Solicitar várias tentativas e conferir custo total e cada resultado.
8. Usar o segundo grupo da receita 2 e conferir o custo alternativo.
9. Selecionar equipamentos em duas receitas, fabricar e conferir que o objeto escolhido foi consumido.
10. Pressionar Stop durante a barra e conferir que não houve débito ou entrega.
11. Fabricar a receita 102 até uma falha, relogar e conferir o progresso; no teto, conferir o sucesso garantido.

O usuário identificou `123001247` como **Zikel's Apostle Belt**. O item existe no cliente com o nome interno `belt_n_e3_zikel_agent_70a`, mas não aparece como material, produto ou retorno em nenhuma das três variantes do XML de receitas. Os arquivos `client_item_special_craft.xml` dos pacotes `items.pak`, `special/special.pak` e `special2/special2.pak` do cliente em uso foram extraídos em modo de leitura e comparados com os dados canônicos: as árvores XML são equivalentes e todas contêm 388 receitas. As receitas de cinto 132/133 usam `belt_n_e2_zikel_70a`, um item distinto. Esse caso permanece pendente de uma captura oficial que mostre o pedido da receita correspondente ou de dados oficiais que a definam; não foi criada uma receita com custos ou probabilidades presumidos.

Nenhum teste automatizado aqui substitui essa confirmação visual no cliente.

## Atualização do JAR e diagnóstico de rejeições

Pare o GameServer antes de substituir o JAR e só volte a iniciá-lo depois da cópia e da conferência do hash. Não sobrescreva o JAR usado por uma JVM em execução: o carregador mantém informações do arquivo anterior e pode deixar de carregar classes que existem no arquivo novo. No incidente de 17/09/2026, o servidor iniciou às 18:22 e o JAR foi substituído às 18:25; surgiram erros `NoClassDefFoundError` em uso de itens, equipamentos, mudança de hora e logout. As três classes citadas existiam no JAR distribuído.

Uma rejeição inicial da Bigorna agora registra `Siel Anvil rejected` com jogador, receita, grupo, quantidade, motivo, materiais comuns e IDs dos objetos selecionados. Isso permite distinguir problemas de estado do jogador, receita indisponível, seleção/custos divergentes, materiais insuficientes e espaço insuficiente sem alterar os custos oficiais.

Se o parser rejeitar o pedido, a linha anterior `Siel Anvil invalid request` preserva os materiais e IDs realmente lidos, o motivo da invalidade e o número de bytes restantes. As listas vazias na linha do serviço, nesse caso, são resultado do descarte de um pedido inválido e não provam que o cliente enviou listas vazias. O teste cobre um pedido com o mesmo anel selecionado duas vezes: ele é rejeitado e seus valores continuam disponíveis para diagnóstico. A receita 102 exige dois objetos distintos do item `122001590` no grupo normal, ou um objeto no grupo alternativo.
