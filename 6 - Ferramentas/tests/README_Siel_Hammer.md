# Martelo de Siel — Classic 5.0

Fluxo: `CM_SIEL_HAMMER` → `SielHammerService` → tarefa de interação → inventário persistente → evento e resultado do Hammer. Não exige NPC ou profissão de fabricação.

## Evidência oficial

Captura: `5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/06_Sistemas_Novos_5.0/06_Sistemas_Novos_Siel_Hammer_5.0_2026-09-11_17-56-12_00001_20260911175612.pcapng`.

51 pacotes de cliente e 694 de servidor decifrados, com checksums válidos. A captura contém uma desmontagem: objeto `0xC03FB271`, item `166001095` (pedra de encantamento de evento L95), quantidade 1. A tabela oficial 322 não cobra Kinah e entrega uma essência de evento `166300500`.

| Etapa | Opcode decodificado | Payload |
|---|---|---|
| Pedido | C `0x00FF`, wire `0x01F5` | `010071b23fc00100000000000000` |
| Início | S `0x01C4` | `01d0070000` |
| Consumo | S `0x001C` | `71b23fc010010000` |
| Resultado | S `0x01A2` | `000000000100548be909010000000000000000` |
| Fechamento do cliente | C `0x0152`, wire `0x0220` | vazio |

Pedido: tamanho `H`, pares `(D objectId, Q quantidade)`. O limite de 20 seleções é confirmado pelo cliente (`Game.dll`, RVA `0x23E7B0`); o serializador do pedido é `0x89A060`. Object IDs são unsigned no protocolo; o bit alto do objeto capturado não pode causar rejeição de um `int` Java negativo.

Evento: `C evento`, `D duração`. O cliente (`0x23F000`) trata 1 como início da barra e 2 como fechamento. A duração capturada é 2.000 ms.

Resultado: `D status` (0 para sucesso), tamanho `H`, pares `(D itemId, Q quantidade, C bônus)`. O último byte pertence a cada entrada; não existe um vetor separado de bônus. Confirmado no parser `0x8D73C0` e no handler `0x8AF230`.

O consumo de uma pilha inteira usa o motivo `0x110` de `S_REMOVE_INVENTORY`. A adição de resultados usa o cabeçalho oficial de seis bytes `120100000001`, seguido do tamanho `H` e dos itens. As demais adições de inventário conservam seu cabeçalho existente.

## Dados e comportamento

`parsersXML/parse_siel_hammer.py` exporta as 441 tabelas de `client_item_crush.xml` e 4.446 associações de itens do `client_items.xml`, usando `can_crush` e `crush_name`. Os nomes de resultados são resolvidos pelos templates canônicos do servidor; item ou tabela ausente provoca erro de geração. A flecha inicial `163000006` tem a marca oficial `can_not_record`, sem tabela, e permanece inelegível. Não foi inventada uma receita para essa marca.

Custos em Kinah, faixas inclusivas de encantamento, quantidades, probabilidades dos resultados e bônus vêm integralmente dos dados oficiais. O denominador é 1.000; cada unidade selecionada recebe um resultado normal e uma rolagem independente de bônus quando previsto. O pacote soma quantidades repetidas, mantendo resultados normais e bônus identificados separadamente.

A tarefa não debita na abertura. Após dois segundos, revalida estado do jogador, objetos, quantidades, encantamento, Kinah e espaço. Itens equipados, expirados, inexistentes ou sem tabela, quantidades inválidas, pacotes truncados, IDs duplicados e seleções acima do limite não produzem resultados. Quantidades são limitadas pela pilha oficial e pela quantidade possuída.

Cancelamento, movimento e logout usam a tarefa de interação normal. Stop fecha a barra antes do consumo; uma conclusão atrasada não pode debitar ou entregar itens. O cancelamento do Hammer não cancela tarefas de outros sistemas. O fechamento enviado pelo cliente depois do sucesso é idempotente.

A reserva de espaço inclui resultados normais, bônus, capacidade restante das pilhas e espaços liberados pelo consumo completo dos materiais. Para resultados aleatórios diferentes, considera limites máximos por tipo antes de sortear, de forma conservadora; pode exigir mais espaço que o resultado efetivamente sorteado. Não permite obter novas rolagens gratuitas por falta de espaço. Consumo, alteração de Kinah e entrega usam o serviço padrão de itens e sua persistência; não exigem tabela SQL nova.

Mensagens oficiais de rejeição: `1403923` para Kinah insuficiente, `1403924` para inventário sem espaço e `1404452` para cancelamento ou seleção alterada. O log `Siel Hammer rejected` informa jogador, motivo e objetos selecionados.

## Verificação reproduzível

A partir da pasta `Classic`:

```powershell
python '6 - Ferramentas/parsersXML/parse_siel_hammer.py'
mvn -f '1 - Código Fonte [Emulador]/pom.xml' -pl game-server -am package '-DskipTests' '-Dassembly.skipAssembly=true'
java -cp '1 - Código Fonte [Emulador]/game-server/target/classes;2 - Emulador [Produto Final]/GameServer/libs/*' '6 - Ferramentas/tests/SielHammerChecks.java' '1 - Código Fonte [Emulador]/game-server/data/static_data'
java -cp '1 - Código Fonte [Emulador]/game-server/target/classes;2 - Emulador [Produto Final]/GameServer/libs/*' '6 - Ferramentas/tests/SielAnvilChecks.java' '1 - Código Fonte [Emulador]/game-server/data/static_data'
```

O Hammer passou em 4.928 verificações, incluindo todos os limites das probabilidades normais e dos bônus, faixas de encantamento, XSD/JAXB, associação capturada, payloads oficiais byte a byte, cabeçalhos de inventário, leitura completa e inválida, lote, custo oficial, espaço liberado, pilhas existentes, snapshot de encantamento, cancelamento, callback atrasado e registro final dos opcodes. Também verifica a fila real de pacotes: consumo → resultado → recompensa → atualização do cubo, preservando as atualizações imediatas dos demais usos de inventário. A regressão da Bigorna passou nas 116 verificações existentes.

### Inventário do personagem fecha quando um item entra ou sai

`SM_CUBE_UPDATE` (`S_EVENT`, opcode interno `0x81`, ação zero) enviava apenas
9 bytes. O cliente 5.0 x64 lê também os offsets 9, 10 e 11
(`Game.dll`, handler RVA `0x8B6EA0`). O byte 11 alimenta o estado de modo
do inventário; uma mudança desse estado fecha suas janelas
(RVA `0x77A050`). Com o payload truncado, esses bytes vinham de fora do pacote.

A captura oficial do Hammer contém o payload completo de 12 bytes
`000047000000050101000000`, com esses três campos zerados. O servidor agora
envia os três bytes em todas as atualizações de capacidade, mantendo a ação
de stigma (`06 06`) em dois bytes. Os testes conferem a captura byte a byte e
os pacotes reais enfileirados nos fluxos comuns de adição e remoção de itens.
Essa correção é feita no servidor e não exige outra alteração de `version.dll`.

### Aviso de cancelamento depois de uma desmontagem concluída

O cliente emite `1404452` localmente quando fecha a janela do Hammer com a barra ativa (`Game.dll`, RVA `0x23F640`). Esse aviso não depende de um `SM_SYSTEM_MESSAGE` enviado pelo servidor. Na captura, a atualização de cubo `S_EVENT` (`0x81`, evento 649) ocorre depois do resultado e da recompensa, inclusive depois do fechamento automático enviado pelo cliente. O fluxo genérico do emulador enviava atualizações de cubo entre o consumo e o resultado, e a cada recompensa adicionada.

As remoções `CRUSH` e adições `CRUSH_RESULT` agora adiam essas atualizações. O Hammer envia uma atualização de cubo ao final da entrega; em caso de reversão de débito, atualiza o cubo também. Stop mantém o evento de fechamento e as proteções contra conclusão atrasada. A alteração da ordem está coberta pelo teste de fila, mas o teste visual confirmou que ela sozinha não remove o aviso local.

O patch `bin64/version.dll` distingue o fechamento dentro do resultado bem-sucedido do botão Stop. A análise e os testes nativos estão documentados em [README_Siel_Hammer.md](../../3%20-%20C%C3%B3digo%20Fonte%20%5BVersion.dll%5D/tests/README_Siel_Hammer.md). A DLL passou em 27 verificações; suas assinaturas e o RTTI foram conferidos no cliente 5.0 x64. O usuário confirmou o funcionamento com a nova DLL e com a correção do pacote de inventário aplicada ao servidor.

Antes de substituir o JAR de produção, pare o GameServer e confira que não há clientes conectados. Substitua o JAR somente com a JVM parada; sincronize `siel_hammer.xml`, `siel_hammer.xsd`, `static_data.xml` e `static_data.xsd`, confira os hashes e inicie novamente.

Os testes não substituem a confirmação no cliente. Validação visual pendente: desmontar o item capturado, desmontar várias pilhas, usar equipamento nas três faixas de encantamento, conferir bônus e Kinah, pressionar Stop e sair durante a barra, relogar para conferir o inventário. A captura fornecida confirma um resultado normal gratuito; não contém amostras de lote, bônus ou consumo de Kinah.
