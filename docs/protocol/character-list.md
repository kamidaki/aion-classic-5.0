# S_CHARACTER_LIST (0x0C7) no layout 4.5

Derivado da captura `build/capture/gf-login.pcapng`, com o `writePlayerInfo()` do Aion-Lightning
(`server/AL-Game/src/com/aionemu/gameserver/network/aion/PlayerInfo.java`) como mapa de campos.

---

## São dois pacotes

O servidor real manda **uma lista vazia primeiro** e a lista de verdade logo depois. Mandando só a
segunda, o cliente fecha a conexão.

```
S_BUILDER_LEVEL   (0x0EE, 29 bytes de payload, tudo zero)
S_CHARACTER_LIST  (0x0C7, 11 bytes de payload  -> contagem 0)
S_CHARACTER_LIST  (0x0C7, 1527 bytes           -> contagem 2, na captura)
```

## Cabeçalho — 11 bytes

| offset | tam | campo |
|---:|---:|---|
| 0 | 1 | contagem de personagens |
| 1 | 4 | chave de sessão (a mesma do `C_HQ_LOGIN`) |
| 5 | 5 | zeros |
| 10 | 1 | **contagem de personagens, de novo** |

Depois vêm `contagem` registros de 758 bytes, e nada mais: o último byte do payload é o último byte
do último registro, não um rodapé.

### A contagem repetida foi o que travou tudo

Na captura os dois bytes valem 2, e 0 na lista vazia — então uma leitura anterior tomou o byte do
offset 10 como o primeiro byte do registro, um "slot" que valeria `0x02` no personagem do último
login. Com 2 personagens os dois layouts produzem exatamente os mesmos bytes. A diferença só
aparece com contagem 1: o cabeçalho dizia 1, o byte do offset 10 continuava dizendo 2, e o cliente
lia um registro a mais do que existia no pacote.

Qual dos dois bytes o cliente usa para dimensionar a lista continua em aberto — na captura eles
nunca discordam. O servidor escreve a contagem nos dois.

## Registro — 758 bytes

Confirmado nos dois personagens da captura (Durak, elyos nível 60; Kimmie, asmodiana nível 3).

| offset | tam | campo | Durak | Kimmie |
|---:|---:|---|---|---|
| 0 | 4 | id do personagem | `0x2E0F3384` | `0x2E4627F1` |
| 4 | 52 | nome, UTF-16LE, terminado em nulo | `Durak` | `Kimmie` |
| 56 | 4 | gênero | 1 | 1 |
| 60 | 4 | raça (0 elyos, 1 asmodiano) | 0 | 1 |
| 64 | 4 | classe | 1 | 11 |
| 68 | 4 | voz | 2 | 0 |
| 72 | 4 | cor da pele | `009DB6DD` | `00D6DBD9` |
| 76 | 4 | cor do cabelo | `001C1C1C` | `001C1C1C` |
| 80 | 4 | cor dos olhos | `00BDA362` | `002C110C` |
| 84 | 4 | cor dos lábios | `008E92EA` | `006A6AFF` |
| 88 | 52 | aparência: 52 valores de 1 byte (rosto, cabelo, nariz, altura de cada traço…) | — | — |
| 140 | 4 | altura, float | 0.650 | 0.650 |
| 144 | 4 | **`100000 + raça * 2 + gênero`** | 100001 | 100003 |
| 148 | 4 | mapa, para o cliente pré-carregar | 800040000 | 120010000 |
| 152 | 12 | posição x, y, z (3 floats) | 1536.5, 320.3, 411.9 | 1295.8, 1416.3, 208.1 |
| 164 | 4 | direção | 99 | 109 |
| 168 | 2 | nível (u16, **não** u32) | 60 | 3 |
| 170 | 2 | zeros (no Java 3.x, `0` e `64`) | 0 | 0 |
| 172 | 4 | título (`0xFFFFFFFF` = sem título) | 24 | sem título |
| 176 | 86 | legião: id + nome em 82 bytes; zerado fora de legião | zerado | zerado |
| 262 | 2 | está em legião? | 0 | 0 |
| 264 | 4 | último login, unix | 2026‑08‑20 07:32 | 2026‑08‑20 07:40 |
| 268 | 272 | equipamento: 16 entradas de 17 bytes, empacotadas no início | 13 itens | 10 itens |
| 540 | 68 | zerado nos dois | | |
| 608 | 4 | data de criação, unix | 2025‑02‑07 | 2026‑08‑20 07:35 |
| 612 | 4 | zerado nos dois | | |
| 616 | 4 | desconhecido | `04 00 01 00` | zerado |
| 620 | 4 | desconhecido | `0F 00 00 00` | zerado |
| 624 | 116 | zerado nos dois | | |
| 740 | 4 | desconhecido | `04 00 00 00` | zerado |
| 744 | 14 | zerado nos dois | | |

A ordem dos 52 bytes de aparência (88..140) vem do `writePlayerInfo()`; ela não foi conferida
campo a campo, porque isolar cada traço exige criar personagens diferentes e capturar de novo.

### Entrada de equipamento — 17 bytes

| offset | tam | campo |
|---:|---:|---|
| 0 | 1 | 1, ou 2 nos slots de arma (no Java: `slot == 2 \|\| 64 \|\| 256`) |
| 1 | 4 | id do template de aparência do item |
| 5 | 4 | godstone |
| 9 | 4 | cor |
| 13 | 4 | acrescentado na 4.5, sempre zero na captura |

Na captura só o flag e o id aparecem diferentes de zero, então a divisão dos 12 bytes restantes é a
do Java e ainda não foi confirmada. No Java 3.x a entrada tem 13 bytes; aqui o passo medido entre
duas entradas é 17.

## Como o layout foi validado

1. **O nome cai em 4..56.** No `writePlayerInfo()` o registro começa com o id e o nome vem logo
   depois, em 52 bytes. Só bate se o registro começar no offset 11 do payload.
2. **`100000 + raça * 2 + gênero` fecha nos dois personagens.** É uma redundância dentro do próprio
   registro: três campos independentes que têm que concordar. Um layout deslocado não passaria nos
   dois.
3. **Os valores são plausíveis campo a campo.** Mapa 120010000 é Ishalgen, onde um asmodiano de
   nível 3 estaria; os ids de item caem nas faixas do jogo; as datas de criação são anteriores às de
   último login.
4. **O serializador reproduz o pacote capturado byte a byte** — teste
   `reproduz_o_pacote_capturado` em `lista_personagens.rs`.

## O que o servidor escreve hoje

Só id, nome e nível. O resto sai de um molde tirado do registro do Durak
(`game-server/src/game/message/molde.rs`), então todo personagem aparece com a aparência, o
equipamento, a classe, a raça e a posição dele. Preencher os outros campos é agora só escrever nos
offsets desta tabela.
