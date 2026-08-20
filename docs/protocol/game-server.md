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

## Cifra do opcode — cliente: NÃO é um mapa fixo

```
(opcode ^ 0x36) - 0xC4
```

Isto decodifica corretamente o começo da sessão:

```
C_VERSION → C_SYNC_TIME → C_SYNC_TIME → C_HQ_LOGIN → C_READY_ENTER_WORLD_ACK
```

`C_HQ_LOGIN` é o pacote que leva os dois ids de 4 bytes e o token do STS, exatamente como
`reference/rust-poc/docs/AUTH.md` descreve. `C_READY_ENTER_WORLD_ACK` responde ao
`S_READY_ENTER_WORLD` do servidor.

**A partir do sexto pacote o resultado deixa de fazer sentido** — aparecem `C_GET_OFF_VEHICLE`,
`C_TOGGLE_CHEST`, `C_READY_TO_QUIT` no meio de um login. Não é erro de decriptação: o checksum
interno confere nos 48 pacotes. A ofuscação do opcode de cliente depende de algum estado que
avança durante a sessão.

> Cuidado ao avaliar candidatos a constante por "quantos opcodes caem na tabela": os opcodes
> válidos de cliente são densos (0 a 0x147), então muitas fórmulas afins acertam quase tudo por
> acidente. Foi assim que uma primeira tentativa deu 48/48 com constantes erradas. **A ordem dos
> pacotes é o sinal confiável** — uma sessão tem que começar em `C_VERSION`.

### O que falta

Descobrir como esse estado evolui. Duas fontes: o handler no `Game.dll` (a região da tabela de
opcodes está em texto claro, ver `docs/protocol/README.md`) e a própria captura, comparando
pacotes repetidos — `C_SYNC_TIME` aparece 12 vezes e deve dar o padrão.

Para o handshake inicial, que é o que o servidor precisa agora, a constante acima basta.
