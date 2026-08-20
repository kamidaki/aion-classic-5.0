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

## Fase 1 — camada de rede (o trabalho de verdade)

O que o confronto de tabelas mostrou (detalhes em `docs/protocol/README.md`):

* **opcodes de cliente**: numeração do AL é 100% incompatível. Tabela descartada
  e reconstruída a partir do dump — os 244 opcodes já estão em CSV.
* **opcodes de servidor**: ~parecida, com deslocamentos de −1 e algumas
  realocações reais (`SM_GROUP_INFO` 0x5a → 0xf7). Auditar pacote a pacote.
* **corpo dos pacotes**: muda entre retail e Classic. É aqui que entra captura.

Ordem sugerida, do que destrava mais para o que destrava menos:

1. Login server: portar do POC em C# o handshake que já passa
   (`SM_INIT` com o byte `0xFD` em `0xA8`, flags `0x3F` + assinatura `0xFF FE`,
   entradas de 21 bytes com `ServerBits 0x401` e o byte de bracket do `-cc:2`).
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
