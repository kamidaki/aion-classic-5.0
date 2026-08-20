# Game server do Aion Classic 4.5 — porta 7777

Tudo aqui foi decifrado de uma captura real (login completo até entrar no mundo), não deduzido.

## Enquadramento

```
[u16 tamanho][u16 opcode cifrado][u8 0x65][u16 checksum = !opcode][payload]
```

O tamanho inclui os 2 bytes do próprio campo. O `checksum` é o complemento de 1 do opcode
cifrado — o que dá um **teste de sanidade gratuito**: se ele não bater, a decriptação está errada.
Foi esse teste que validou tudo abaixo.

`SERVER_BYTE` é `0x65` na 4.5. O POC usava `0x40`, que era da 2.5.

## Cifra do corpo

Cadeia XOR com chave de 8 bytes, chave estática de 64 bytes e encadeamento com o byte anterior.
O algoritmo e as constantes de derivação do POC **já estavam corretos** para a 4.5:

```
STATIC_KEY = "nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"
chave = ((seed - 0x3FF2CC87) ^ 0xCD92E451) ^ 0x87546CA100000000
```

O `seed` chega em texto claro no primeiro pacote (`S_KEY`), que é o único não cifrado — é o que
torna possível decifrar a sessão inteira a partir de uma captura. Cliente e servidor começam com a
mesma chave e a avançam de forma independente, somando o tamanho de cada pacote. **A chave não
avança no `S_KEY`.**

Validação: 435 pacotes de servidor e 48 de cliente decifrados, checksum conferido em todos, zero
falhas.

## Cifra do opcode — servidor: mapa fixo, confirmado

```
cifrar:    (opcode + 0xC4) ^ 0xD4
decifrar:  (opcode ^ 0xD4) - 0xC4
```

Ancorado no `S_KEY` (`0x047`), que chega em claro como `0x01DF`. Aplicado aos 435 pacotes:
**424 reconhecidos, 11 desconhecidos (2%)**.

O POC usava `(opcode + 0xC0) ^ 0xCF`, da versão 2.5.

A sequência decifrada é uma sessão de Aion legível de ponta a ponta:

```
S_KEY → S_VERSION_CHECK → S_SERVER_ENV → S_SYNC_TIME
→ S_REPLY_NP_LOGIN_GAMESVR ×2 → S_NPSHOP_GOODS_COUNT → S_READY_ENTER_WORLD
→ S_L2AUTH_LOGIN_CHECK (1300 bytes) → S_REPLY_NP_AUTH_TOKEN → S_BUILDER_LEVEL
→ S_CHARACTER_LIST (18 bytes) → ... → S_CHARACTER_LIST (1534 bytes)
→ S_ALIVE → S_2ND_PASSWORD → S_ADD_SKILL (332) → S_LOAD_ACHIEVEMENT
→ S_LOAD_FINISHEDQUEST → S_LOAD_WORKINGQUEST → S_BATTLEPASS_LIST
→ S_USER_CLASSIC_WARDROBE_LOAD → S_RANKING_BADGE → S_USER_STORY_BOOK_*
```

Durante o jogo, o volume vem de `S_PUT_NPC` (157 dos 435), `S_ABNORMAL_STATUS_OTHER`,
`S_MOVE_NEW`, `S_SYNC_TIME`.

## Cifra do opcode — cliente

```
cifrar:    (opcode + 0xC4) ^ 0x36
decifrar:  (opcode ^ 0x36) - 0xC4
```

Confirmado contra o cliente real: a sessão decodifica na ordem certa, com os campos parseando.

```
C_VERSION            aion_version C4, os 6.2
C_SYNC_TIME          ticks, sequence
C_HQ_LOGIN           id 0x0262CAB6, key 0x0AD6, authn_token (100 chars, base64)
C_READY_ENTER_WORLD_ACK
```

`C_HQ_LOGIN` fecha o circuito do auth server: o `id` é a chave entregue no `LOGIN_OK` e o `key` é
o campo de 4 bytes no fim do `SESSION_KEY` cujo propósito estava em aberto
(`docs/protocol/auth-server.md`). O cliente carrega os dois do auth para o game server.

### Uma correção que vale registrar

Uma versão anterior deste documento afirmava que o mapa do cliente "derivava" depois do quinto
pacote, porque a partir dali os nomes deixavam de fazer sentido — apareciam `C_GET_OFF_VEHICLE` e
`C_SA_CONFIRMGOODS` no meio de um login. **Era conclusão errada, tirada dos nomes.**

Olhando o conteúdo dos mesmos pacotes no servidor rodando:

```
opcode 0x5E   [B6 CA 62 02]                    -> 0x0262CAB6, a chave do LOGIN_OK
opcode 0xD6   ... "3C-7C-3F-7C-38-77" ...      -> MAC, id de hardware, IP do cliente
              ... "BAA80100" ... C0 A8 64 4D
```

Os dois são perfeitamente coerentes com um login: devolver a chave de sessão e identificar a
máquina. A cifra estava certa o tempo todo; o que está errado é o **nome** que a tabela extraída dá
a esses opcodes.

Lição: julgar uma hipótese de cifra pelos nomes decodificados é frágil nos dois sentidos — a
contagem de "opcodes válidos" acerta por acidente (os válidos são densos, de 0 a 0x147), e os nomes
podem estar errados mesmo com o valor certo. O que sustenta a conclusão é o **conteúdo dos campos
parseando** e a **ordem** batendo com um login real.

### O que falta

A tabela de nomes precisa de revisão para uma parte dos opcodes. O pareamento nome↔número foi feito
por heurística sobre o `Game.dll` (ver `docs/protocol/README.md`), e casos como `0x5E` e `0xD6`
mostram que ela erra em alguns pontos. O conteúdo dos pacotes, que agora conseguimos ler, é a
referência para corrigir.
