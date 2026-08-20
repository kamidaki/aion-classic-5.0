# Aion Classic 4.5 — estado e plano

Alvo: cliente **GameForge Aion Classic 4.5**, `ProductVersion 4526.0820.0706.7137`,
x64, instalado em `G:\GFAion\aionclassic`.

## O que já existe neste repo

| pasta | o que é |
|---|---|
| `server/` | Aion-Lightning (retail 4.x) — base de lógica de jogo, **compila no JDK 21** |
| `tools/` | extrator estático da tabela de opcodes direto do `Game.dll` |
| `docs/protocol/` | mapa de opcodes do Classic 4.5: 340 servidor + 244 cliente |
| `docs/reverse/` | achados de RE do `Game.dll` x64: handshake, `SM_INIT`, `SM_SERVER_LIST` |
| `reference/dotnet-poc/` | POC em C# que **já leva o cliente 4.5 até a lista de servidores** |
| `reference/rust-poc/` | POC em Rust do Classic 2.5: crypto, `pcap-parser`, `pak`, `bxml` |

Os dois POCs em `reference/` não são para rodar — são para consultar. O de C#
tem os layouts de pacote que já funcionam contra este cliente; o de Rust tem a
criptografia e os desempacotadores de arquivo do cliente.

## Fase 0 — base compilando ✅

Aion-Lightning nasceu em Java 6/7 e não compilava no JDK 21. Três correções,
10 arquivos tocados, os quatro módulos agora compilam com zero erros:

* backport JSR-166 (`chmv8`) removido — virou `java.util.concurrent` no Java 8
* `sun.misc.Cleaner` / `sun.nio.ch.DirectBuffer` → `Unsafe.invokeCleaner` por reflexão
* `com.sun.org.apache.xml.internal.serialize` → `javax.xml.transform`

Compilação de referência (o build Ant original ainda pede `source="1.7"`, que o
javac 21 recusa — use `--release 8`):

```bash
javac --release 8 -encoding UTF-8 -cp "<libs>" -d build/classes @sources.txt
```

## Estado: o cliente chega à seleção de personagem

Com o stack em Rust (`reference/rust-poc`), um cliente 4.5 real percorre hoje:

```
launcher (named pipe) → auth 13001 → STS 6600 → game server 7777
→ termos → lista de servidores → seleção → tela de personagem
```

A tela de personagem renderiza nomes, níveis, classes e modelos 3D. O `S_CHARACTER_LIST` ainda é
replay dos bytes capturados (`game-server/src/game/message/capturado.rs`); o resto do caminho é
código.

**Como rodar:**

```bash
cd reference/rust-poc
AION_GAME_IP=<ip da LAN, nao 127.0.0.1> ./target/release/auth-server.exe
./target/release/sts-server.exe
AION_DATA_DIR=<xml extraido> ./target/release/game-server.exe
./target/release/launcher.exe --auto durak
```

O `gfclient.exe` oficial precisa estar **fechado** — ele cria o mesmo named pipe e sequestra a
conexão. E o IP anunciado não pode ser loopback, senão o cliente descarta a entrada da lista.
Detalhes em `docs/protocol/auth-server.md`.

### Onde a investigação parou

O `S_CHARACTER_LIST` foi reescrito para o layout 4.5 (`game/message/lista_personagens.rs`), mas
**derruba o cliente**. A versão capturada continua sendo o padrão; a construída fica atrás de
`AION_LISTA_CONSTRUIDA=1`.

O que já foi eliminado como causa, para ninguém refazer:

* **o formato** — rodando o serializador com os valores do personagem capturado, o registro sai
  byte a byte idêntico ao real, cabeçalho e rodapé inclusive
* **os dados** — mandar id, nome e nível exatos do personagem capturado, pelo nosso código,
  também derruba
* **o fio** — capturando o nosso próprio servidor e decodificando com `tools/decode_game.py`,
  framing, cifra e opcodes saem limpos, e os tamanhos batem (`S_BUILDER_LEVEL` 36, lista vazia 18)

Sobra o **contexto**: algum outro pacote da sessão, ou a diferença entre mandar 1 personagem e os
2 da captura. O caminho para fechar isso é comparar duas capturas do nosso próprio servidor —
uma com `AION_LISTA_CONSTRUIDA=1` e outra sem — pacote a pacote.

**Próximo passo:** o botão Start manda `C_ENTER_WORLD`. A captura tem a sequência inteira de
entrada no mundo em `docs/protocol/game-server.md`, e `tools/decode_game.py` imprime qualquer
pacote dela com `--dump`.

**Dívida deliberada:** trocar cada pacote capturado por um construído, um de cada vez. O tipo
`Bruto` existe para isso — dá para substituir sem parar o fluxo.

## Fase 1 — camada de rede (o trabalho de verdade)

O que o confronto de tabelas mostrou (detalhes em `docs/protocol/README.md`):

* **opcodes de cliente**: numeração do AL é 100% incompatível. Tabela descartada
  e reconstruída a partir do dump — os 244 opcodes já estão em CSV.
* **opcodes de servidor**: ~parecida, com deslocamentos de −1 e algumas
  realocações reais (`SM_GROUP_INFO` 0x5a → 0xf7). Auditar pacote a pacote.
* **corpo dos pacotes**: muda entre retail e Classic. É aqui que entra captura.

Ordem sugerida, do que destrava mais para o que destrava menos:

1. ~~Login server: portar do POC em C# o handshake que já passa.~~ **Feito** —
   `SM_INIT`, `SM_LOGIN_OK` e `SM_SERVER_LIST` adaptados, constantes em
   `ClassicProtocol.java`, offsets verificados por
   `scripts/verify_login_packets.sh`. Falta testar contra o cliente de verdade
   (precisa do banco `al_server_ls` criado).
2. Handshake do game server: `S_KEY` (`0x047`) e o XOR de opcode.
3. Seleção de personagem: `C_CHARACTER_LIST` (`0x096`) → `S_CHARACTER_LIST` (`0x0c7`).
4. Entrada no mundo: `C_ENTER_WORLD` (`0x008`) → `S_ENTER_WORLD_CHECK` (`0x00d`)
   → `S_WORLD` (`0x00f`) → `C_LEVEL_READY` (`0x009`) → `S_PUT_USER` (`0x020`).
5. Movimento, chat, ataque — a partir daí o AL já tem a lógica pronta.

## Fase 2 — dados estáticos do cliente 4.5

`server/AL-Game/data/static_data/` são 195 MB de XML do **retail** 4.x: IDs de
item, npc e skill em boa parte não valem para o Classic. A fonte correta é o
próprio cliente, via `pak` + `bxml` (ambos em `reference/rust-poc/`).

Já existe extração pronta em `G:\CodexHELPER\ClaudeAion\extracted_xml`
(`client_items.xml` com 189 MB, npcs, skills) — falta conferir de qual build veio
antes de confiar.

## Sobre sniffer / Wireshark

Para **opcodes**, captura não é mais necessária: a tabela sai do binário, é
completa e é autoritativa. Wireshark serve para o que sobrou:

1. **Loopback do seu próprio servidor** — o Npcap captura em `127.0.0.1`. É o
   jeito de ver o que você mandou quando o cliente reage errado.
2. **Proxy MITM** (`reference/dotnet-poc` tem um `Sniffer`) — mais útil que
   Wireshark puro, porque decripta Blowfish/XOR na hora, em vez de mostrar bytes
   embaralhados.
3. **`pcap-parser`** do POC em Rust já implementa a decriptação de pacote e
   opcode a partir de um `.pcap`.

Capturar o servidor oficial só faz sentido para descobrir *layout de campo* — e
exige conta ativa na GameForge.
