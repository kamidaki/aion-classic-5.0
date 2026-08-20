# Auth server do Aion Classic (GameForge) — porta 13001

Decodificado de uma captura real (conta ativa, login completo até entrar no mundo).
Regenerar com:

```bash
python tools/decode_auth.py build/capture/gf-login.pcapng
```

## O cliente nunca usa a porta 2106

A captura mostra a ordem real das conexões:

| ordem | servidor | porta | papel |
|---|---|---|---|
| 1 | 79.110.83.156 | **13001** | auth |
| 2 | 79.110.83.118 | **6600** | STS (identidade federada) |
| 3 | 79.110.83.115 | **7777** | game server |
| 4 | 79.110.83.159 | 10241 | — |

Nada na 2106. Toda a tentativa de falar o protocolo legado da NCSoft ali foi contra uma porta que
este cliente não usa.

## Framing

Texto claro, sem cifra nenhuma:

```
[u16 tamanho][u8 opcode][3 bytes zero][payload]
```

O tamanho inclui o cabeçalho de 6 bytes.

## A conversa completa

```
S -> C   0x05  GREETING        92 bytes
C -> S   0x01  CREDENTIALS    107 bytes
S -> C   0x01  LOGIN_OK        14 bytes
S -> C   0x02  SERVER_LIST    201 bytes
C -> S   0x02  SERVER_SELECT   10 bytes
S -> C   0x04  SESSION_KEY     22 bytes
```

### 0x05 GREETING (servidor fala primeiro)

Três strings terminadas em nulo, seguidas de 4 bytes de trailer:

```
"5B4503FA-8521-4608-BB60-5CFAC87BD63A"   <- chave 1
"7282405F-79E5-49C2-9872-D4F3CC961FF3"   <- chave 2
"aiongfc"                                <- nome do serviço
14 0c 00 00                              <- trailer
```

As duas UUIDs são **constantes do servidor**, não valores de sessão: batem byte a byte com as que o
POC em Rust trazia fixas no código, capturadas em outra época e outra máquina.

### 0x01 CREDENTIALS (cliente)

Uma string base64 terminada em nulo. Decodificada, é `<uuid>:<uuid>` — o par de identificadores que
o launcher da GameForge entrega ao cliente pelo named pipe `\.\pipe\GameforgeClientJSONRPC`.

**É o segredo da conta.** O `decode_auth.py` oculta por padrão; use `--mostrar-token` só se souber
por quê.

### 0x01 LOGIN_OK (servidor)

```
[u32 accountId][u32 chave]
```

Na captura: `accountId = 0x00000000`, `chave = 0x026edf39`. A chave reaparece no `SESSION_KEY` e é
o que o cliente leva para o game server.

### 0x02 SERVER_LIST (servidor)

```
[u16 quantidade][entrada × quantidade][4 bytes]
```

Cada entrada tem **63 bytes**:

| offset | tamanho | conteúdo |
|---|---|---|
| 0 | 1 | sempre `0x01` |
| 1 | 1 | tipo: `4` = mundo, `5` = instância |
| 4 | 1 | online (0/1) |
| 5 | 1 | id do servidor |
| 9 | 1 | quantidade de personagens da conta nesse servidor |
| 13 | var | **IP em ASCII**, terminado em nulo (`"79.110.83.115"`) |
| 53 | 2 | porta, u16 little-endian (`0x1e61` = 7777) |

Da captura:

```
[0] id=0x67 tipo=5 online=0 personagens=0  79.110.83.114:7777
[1] id=0x17 tipo=4 online=1 personagens=2  79.110.83.115:7777
[2] id=0x79 tipo=5 online=0 personagens=0  79.110.83.116:7777
```

> **O POC em Rust erra esta entrada.** Ele escreve o IP como 4 octetos binários em `[13..17]` e a
> porta big-endian em `[17..19]`, com um comentário afirmando que o cliente lê bytes crus e *não*
> uma string ASCII. A captura mostra o contrário: IP em ASCII no offset 13 e porta little-endian no
> offset 53. Quem for portar a partir daquele código vai herdar o erro.

### 0x02 SERVER_SELECT (cliente)

```
[u32 id do servidor]
```

### 0x04 SESSION_KEY (servidor)

```
[u32 id do servidor][u32 chave][u32 erro][u32 extra]
```

Na captura: `0x17`, `0x026edf39`, `0x00000000`, `0x00000ad6`.

O campo de erro **tem que ser zero**; qualquer outro valor o cliente exibe como
"Authorization Error (código)" e desconecta antes de chegar ao game server.

## O que falta

A mesma captura ainda contém, não analisados:

* **STS na 6600** — 11 kB. Identidade federada, com troca de chaves e RC4 (ver
  `reference/rust-poc/docs/AUTH.md`). O cliente conecta logo depois do auth.
* **Game server na 7777** — 98 kB, incluindo a entrada no mundo. É a fonte para os layouts de
  pacote que a tabela de opcodes sozinha não dá.
