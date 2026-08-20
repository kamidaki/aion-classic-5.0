# Aion Classic 4.5 — estado e plano

Escrito para ser lido frio, sem contexto de conversa anterior.

---

## 1. O que é este projeto

Servidor privado para o cliente **Aion Classic 4.5 da GameForge**, build
`4526.0820.0706.7137`, x64, instalado em `G:\GFAion\aionclassic`.

A base é o **POC em Rust** em `reference/rust-poc` — originalmente escrito para o Classic 2.5 e
corrigido aqui para a 4.5. A pasta `server/` tem o Aion-Lightning (Java), que foi a base anterior
e hoje é **só referência de lógica de jogo**; nada dela está em uso.

Tudo que se sabe do protocolo saiu de **uma captura de sessão real** contra os servidores da
GameForge, não de tentativa e erro. A captura fica em `build/capture/gf-login.pcapng`, fora do git
porque contém o token de autenticação da conta.

---

## 2. Estado atual

O cliente percorre este caminho, contra servidor local:

```
launcher (named pipe) → auth 13001 → STS 6600 → game server 7777
→ termos → lista de servidores → seleção → tela de personagem → mundo
```

A tela de personagem renderiza nome, nível, classe e modelo 3D. A entrada no mundo carrega a HUD
completa — minimapa, barra de skills, DP.

**O que ainda não funciona:** o mundo carrega sem posição e sem mapa, sobre o cenário da tela de
seleção. A causa é conhecida e está na seção 5.

---

## 3. Como rodar

Quatro processos. O cliente é aberto pelo próprio launcher — não abra o `Aion.exe` na mão.

```bash
cd reference/rust-poc

AION_GAME_IP=192.168.100.77 ./target/release/auth-server.exe
./target/release/sts-server.exe
AION_DATA_DIR="G:/CodexHELPER/ClaudeAion/extracted_xml" ./target/release/game-server.exe
./target/release/launcher.exe --auto durak
```

### Duas condições que não são óbvias

Cada uma produz um sintoma **indistinguível de servidor quebrado**. Juntas explicam boa parte dos
testes que "não funcionavam sem motivo".

**1. O `gfclient.exe` oficial precisa estar fechado.** Ele cria o mesmo named pipe
(`\\.\pipe\GameforgeClientJSONRPC`) e o cliente Aion conecta na instância dele. O nosso launcher
fica em "waiting for client..." para sempre, e o cliente cai no formulário de login manual.

**2. `AION_GAME_IP` não pode ser `127.0.0.1`.** O cliente descarta entradas de loopback na lista de
servidores **antes de tentar conectar** — nenhum SYN, para lugar nenhum. Use o IP da máquina na
LAN. O game server escuta em `0.0.0.0`, então aceita nos dois; o que muda é só o texto que o
cliente lê na lista.

### Variáveis de ambiente

| variável | efeito |
|---|---|
| `AION_GAME_IP` | IP anunciado na lista de servidores. **Não pode ser loopback.** |
| `AION_GAME_PORT` | porta do game server (padrão 7777) |
| `AION_DATA_DIR` | pasta com `npcs/client_npcs.xml` e `items/client_items.xml` |
| `AION_REPLAY` | arquivo de replay (padrão `replay.bin`) |
| `AION_LISTA_CONSTRUIDA` | usa a lista de personagens construída em vez da capturada — **derruba o cliente hoje**, ver seção 5 |
| `AION_PERSONAGEM_CAPTURADO` | manda os valores exatos do personagem capturado; teste de bissecção |

### Gerar o `replay.bin`

Não vai para o git (deriva da captura). Regenerar com:

```bash
python tools/export_replay.py build/capture/gf-login.pcapng reference/rust-poc/replay.bin
```

---

## 4. Mapa do repositório

```
reference/rust-poc/          A BASE. Workspace Rust, 7 crates, compila limpo.
  auth-server/               porta 13001 e 2106. Texto claro, 6 pacotes.
  sts-server/                porta 6600. Identidade federada, RC4/AES/RSA. Funciona.
  game-server/               porta 7777. Onde está o trabalho.
    src/game/message/
      client.rs              pacotes do cliente e seus handlers
      server.rs              pacotes do servidor
      lista_personagens.rs   S_CHARACTER_LIST no layout 4.5 (ver seção 5)
      molde.rs               registro de personagem capturado, gerado
      capturado.rs           pacotes capturados usados como andaime
      replay.rs              motor de replay, indexado por opcode
  launcher/                  named pipe da GameForge + abre o cliente
  krypt/                     cripto do game server e do STS
  pak/ bxml/                 desempacotadores de arquivo do cliente
  pcap-parser/               fora do workspace, não usado

docs/protocol/               O QUE SE SABE DO PROTOCOLO
  README.md                  tabela de opcodes: como foi extraída, limites
  auth-server.md             protocolo do auth completo, 6 pacotes
  game-server.md             cripto, constantes, sequência real decifrada
  opcodes_server.csv         340 opcodes
  opcodes_client.csv         244 opcodes

docs/reverse/                achados de engenharia reversa
tools/                       ferramentas de análise (seção 7)
server/                      Aion-Lightning (Java). Só referência.
build/capture/               capturas. Fora do git: contêm token de conta.
```

---

## 5. O bloqueio atual

O `S_CHARACTER_LIST` foi reescrito para o layout 4.5 em `lista_personagens.rs`, mas **derruba o
cliente**. Por isso o padrão continua sendo a lista capturada; a construída fica em
`AION_LISTA_CONSTRUIDA=1`.

### Por que isso importa

Enquanto a lista for replay da captura, os ids de personagem vêm de outra sessão. O cliente escolhe
um personagem que o servidor não tem no estado, e a entrada no mundo fica sem posição e sem mapa.
**Construir a lista é o que destrava o mundo.**

### O layout, derivado da captura

```
[u8  contagem]
[u32 chave de sessão]
[5 bytes zero]
[registro de 758 bytes] × contagem
[u8 rodapé]
```

São **dois pacotes**, não um: primeiro uma lista vazia (11 bytes de payload), depois a real.
Mandando só a segunda, o cliente fecha a conexão.

Campos conhecidos dentro do registro de 758 bytes:

| offset | campo | como foi confirmado |
|---|---|---|
| 0 | slot | `0x02` no personagem do último login, `0x00` nos demais |
| 1..5 | id do personagem | bate com o que o cliente devolve depois |
| 5..57 | nome, UTF-16LE | "Durak" / "Kimmie" |
| 169 | nível, u32 | deu exatamente 60 e 3 nos dois personagens reais |

Os outros **607 dos 758 bytes são idênticos entre dois personagens diferentes** da mesma captura —
aparência, equipamento e campos ainda não decodificados. Por isso o registro sai de um molde
capturado (`molde.rs`) com os campos conhecidos escritos por cima.

### O que já foi eliminado como causa do crash

Não refaça estes caminhos:

- **Não é o formato.** Rodando o serializador com os valores do personagem capturado, o registro
  sai **byte a byte idêntico** ao real — cabeçalho e rodapé inclusive. Verificado offline.
- **Não são os dados.** Mandar id, nome e nível exatos do personagem capturado, pelo nosso código
  (`AION_PERSONAGEM_CAPTURADO=1`), também derruba.
- **Não é o fio.** Capturando o nosso próprio servidor e decodificando com `tools/decode_game.py`,
  o framing, a cifra e os opcodes saem limpos, e os tamanhos batem: `S_BUILDER_LEVEL` 36 bytes,
  lista vazia 18 bytes.
- **Não é o `S_BUILDER_LEVEL`.** O do POC e o capturado são ambos 29 bytes de zeros.

### O próximo experimento

Comparar **duas capturas do nosso próprio servidor**, pacote a pacote:

```bash
# 1. capturar o caso que funciona
"C:\Program Files\Wireshark\tshark.exe" -i "\Device\NPF_Loopback" \
    -w build/capture/funciona.pcapng -f "tcp port 7777"
# subir o stack SEM AION_LISTA_CONSTRUIDA, rodar o cliente até a tela de personagem

# 2. capturar o caso que quebra
"C:\Program Files\Wireshark\tshark.exe" -i "\Device\NPF_Loopback" \
    -w build/capture/quebra.pcapng -f "tcp port 7777"
# subir com AION_LISTA_CONSTRUIDA=1

# 3. comparar
python tools/decode_game.py build/capture/funciona.pcapng --ate 30
python tools/decode_game.py build/capture/quebra.pcapng   --ate 30
```

O índice da interface do tshark muda entre reinícios — use o nome
(`\Device\NPF_Loopback`), não o número.

Hipóteses que sobraram, em ordem de probabilidade:

1. **Algum outro pacote da sessão difere.** Os nossos `S_VERSION_CHECK` (59 bytes),
   `S_SERVER_ENV` (40) e `S_L2AUTH_LOGIN_CHECK` (1192) são **menores** que os reais (61, 67, 1300).
   São implementações do POC, herdadas da 2.5. Pode ser que uma delas só quebre quando combinada
   com a lista construída.
2. **A diferença entre 1 personagem e 2.** A captura tem 2; nós mandamos 1. Testar mandando 2.
3. **Algo no molde que ainda está errado** e só aparece com contagem 1.

---

## 6. Depois que o mundo carregar

Em ordem. Cada item destrava o seguinte.

### 6.1 Trocar o andaime por implementação

O `replay.rs` serve pacotes capturados para todo opcode sem implementação. Cada um que for
implementado sai do replay naturalmente. A ordem sensata é a da própria captura — use
`tools/decode_game.py` para ver qual vem primeiro.

O tipo `Bruto` em `server.rs` existe para essa transição: monta o prelude normalmente e usa payload
pronto, então dá para trocar um pacote de cada vez sem parar o fluxo.

### 6.2 Corrigir a tabela nome↔opcode

O pareamento nome↔número foi feito por heurística sobre o `Game.dll` e **erra em alguns pontos**.
Dois casos comprovados:

- `0x5E`, que a tabela chama de `C_GET_OFF_VEHICLE`, na verdade devolve a chave de sessão
- `0xD6`, que a tabela chama de `C_SA_CONFIRMGOODS`, carrega MAC, id de hardware e IP

Agora que o conteúdo dos pacotes é legível, a tabela é corrigível. `docs/protocol/README.md` explica
como a extração funciona.

### 6.3 Decodificar o resto do registro de personagem

Os 607 bytes estáticos incluem aparência e equipamento. Enquanto não forem decodificados, todo
personagem criado no servidor aparece com a aparência do personagem capturado.

Método: criar personagens diferentes no cliente oficial, capturar, e comparar os registros. Cada
campo que variar isola um atributo.

### 6.4 Dados do cliente 4.5

`AION_DATA_DIR` aponta hoje para XML extraído em `G:\CodexHELPER\ClaudeAion\extracted_xml`, de
proveniência não confirmada. O certo é regenerar do cliente 4.5 com os crates `pak` e `bxml`, que
já existem no workspace.

---

## 7. Ferramentas

Todas em `tools/`, todas em Python, todas independentes do servidor.

| ferramenta | o que faz |
|---|---|
| `extract_opcodes.py` | extrai a tabela de opcodes do `Game.dll`. Rode a cada patch do cliente. |
| `decode_auth.py` | decodifica a conversa do auth server a partir de um pcap. Oculta o token por padrão. |
| `decode_game.py` | decifra a sessão do game server e imprime os pacotes em ordem. `--dump NOME` imprime o payload de um pacote. |
| `export_replay.py` | exporta uma sessão capturada para o formato do motor de replay. |
| `probe_login.py` | sonda passiva: aceita a conexão e não envia nada. Serve para descobrir quem fala primeiro. |
| `pe.py` | parser de PE, usado pelo extrator de opcodes. |

---

## 8. Armadilhas conhecidas

Cada uma destas custou tempo real.

**"Igual nos dois personagens" não significa "vazio".** Significa estático — e estático pode ser
obrigatório. Zerei quatro bytes de dados reais por deduzir a fronteira do campo de nome em vez de
medi-la, e o cliente crashou. Meça toda fronteira nos dois registros.

**Contagem de opcodes válidos não valida hipótese de cifra.** Os opcodes válidos são densos
(0 a 0x147), então muitas fórmulas afins acertam quase tudo por acidente — uma tentativa errada deu
48 de 48. O sinal confiável é a **ordem**: uma sessão precisa começar em `C_VERSION`.

**Julgar decodificação pelos nomes é frágil nos dois sentidos.** O nome pode estar errado com o
valor certo. O que sustenta uma conclusão é o **conteúdo dos campos parseando** e a ordem batendo
com uma sessão real.

**O sintoma quase nunca aponta para a causa.** O cliente para sem mensagem, sem código, e o mesmo
sintoma serve para porta errada, offset errado, IP recusado, pipe sequestrado e cripto errada. A
saída é sempre comparar com a captura, nunca deduzir do sintoma.

**Índices de interface do tshark mudam entre reinícios.** Use o nome do dispositivo.

**O binário trava o arquivo.** `cargo build` falha com "failed to remove file" se o servidor estiver
rodando. Pare antes de compilar.

---

## 9. O que existe e não está em uso

- **`server/`** — Aion-Lightning em Java, base anterior. Compila no JDK 21 (correções em
  `scripts/build_login.sh`), tem banco criado no MariaDB local. Vale como **referência de lógica de
  jogo**: quests, skills, IA, instâncias. A camada de rede dele é retail e não serve.
- **`reference/dotnet-poc/`** — POC em C#. O `walkthrough.md` dele descreve um protocolo de login
  que este cliente **não usa**; ver `docs/reverse/login-protocol-findings.md`.
- **`scripts/`** — scripts da era Java (build, banco, verificação de pacotes de login).
