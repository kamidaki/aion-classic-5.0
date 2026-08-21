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
seleção — sintoma de o personagem escolhido não existir no estado do servidor. A lista de
personagens acabou de passar a ser montada do banco, o que ataca exatamente essa causa, e ainda não
foi testada contra o cliente. Seção 5.

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
| `AION_LISTA_CAPTURADA` | volta a lista de personagens para o replay da captura, em vez da construída do banco; ver seção 5 |
| `AION_PERSONAGEM_CAPTURADO` | monta a lista construída com os valores do personagem capturado; teste de bissecção |

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
      molde.rs               registro capturado, com os campos que o servidor escreve zerados
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
  character-list.md          S_CHARACTER_LIST campo a campo, os 758 bytes do registro
  opcodes_server.csv         340 opcodes
  opcodes_client.csv         244 opcodes

docs/reverse/                achados de engenharia reversa
tools/                       ferramentas de análise (seção 7)
server/                      Aion-Lightning (Java). Só referência.
build/capture/               capturas. Fora do git: contêm token de conta.
```

---

## 5. A lista de personagens

O `S_CHARACTER_LIST` agora é montado a partir do banco, no layout 4.5
(`lista_personagens.rs`), e essa é a lista que o servidor manda por padrão. **Isso ainda não foi
confirmado contra o cliente** — ver "o teste que falta", no fim desta seção.

### Por que isso importa

Enquanto a lista for replay da captura, os ids de personagem vêm de outra sessão. O cliente escolhe
um personagem que o servidor não tem no estado, e a entrada no mundo fica sem posição e sem mapa.
**Construir a lista é o que destrava o mundo.**

### O crash, e o que era

A lista construída derrubava o cliente. A causa era o cabeçalho: **a contagem de personagens
aparece duas vezes**, no offset 0 e no offset 10, e a leitura antiga do layout só conhecia a
primeira — tratava o byte do offset 10 como o primeiro byte do registro, um "slot" que valeria
`0x02` no personagem do último login.

Com os 2 personagens da captura, as duas leituras produzem exatamente os mesmos bytes. A diferença
só aparece com 1 personagem: o cabeçalho dizia 1, o byte do offset 10 continuava dizendo 2, e o
cliente lia um registro a mais do que existia no pacote.

Como o caso quebrado foi isolado: comparando duas capturas do nosso próprio servidor, pacote a
pacote, os 18 primeiros pacotes saem **idênticos** nas duas, e o pacote 19 quebrado é o pacote 19
que funciona, truncado, com um único byte trocado — o do offset 0, de `0x02` para `0x01`. Não
sobrava mais nada para ser a causa.

```bash
python tools/decode_game.py build/capture/funciona.pcapng --ate 20
```

`funciona.pcapng` é a sessão com a lista capturada, que vai até o mundo; `nosso.pcapng` é a que
quebra, e termina no pacote 19.

### O layout

Está inteiro em `docs/protocol/character-list.md`: cabeçalho, os 758 bytes do registro campo a
campo, e as entradas de equipamento. Foi derivado da captura com o `writePlayerInfo()` do
Aion-Lightning (`server/`, a base Java que ficou de referência) como mapa de campos, e validado por
uma redundância dentro do próprio registro: o campo do offset 144 vale `100000 + raça * 2 + gênero`,
e a conta fecha nos dois personagens.

O servidor escreve id, nome e nível. O resto sai de um molde tirado do registro do Durak, então todo
personagem ainda aparece com a aparência, o equipamento, a classe, a raça e a posição dele.

### O teste que falta

Uma rodada do cliente até a tela de personagem. O esperado é ver o personagem do banco, com o nome
do banco, e entrar no mundo com os ids do servidor.

Se derrubar o cliente de novo, capture a sessão e compare com `funciona.pcapng`:

```bash
"C:\Program Files\Wireshark\tshark.exe" -i "\Device\NPF_Loopback" -w build/capture/quebra.pcapng -f "tcp port 7777"
```

```bash
python tools/decode_game.py build/capture/quebra.pcapng --ate 30
```

O índice da interface do tshark muda entre reinícios — use o nome (`\Device\NPF_Loopback`), não o
número.

Duas alavancas para bissecção:

| variável | o que faz |
|---|---|
| `AION_LISTA_CAPTURADA=1` | volta para o replay da captura, o caminho que se sabe que chega no mundo |
| `AION_PERSONAGEM_CAPTURADO=1` | monta a lista construída com os valores do Durak. O pacote sai byte a byte igual ao capturado, exceto pela contagem, que é 1 em vez de 2 |

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

### 6.3 Preencher o registro de personagem

O registro está decodificado — `docs/protocol/character-list.md` tem a tabela — mas o servidor só
escreve id, nome e nível. Aparência, equipamento, classe, raça, posição e mapa continuam vindo do
molde, iguais para todo mundo.

Preencher é escrever nos offsets da tabela. Dois avisos:

- o campo do offset 144 tem que continuar valendo `100000 + raça * 2 + gênero`. É a redundância que
  valida o registro; se ela sair errada, a lista pode passar e a tela de personagem não
- o mapa do offset 148 é o que o cliente pré-carrega. Personagem novo com mapa zero é candidato a
  reproduzir o mundo sem cenário

Os poucos campos que restam sem nome (616, 620, 740, e a ordem dos 52 bytes de aparência) se isolam
criando personagens diferentes no cliente oficial, capturando, e comparando os registros.

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
medi-la, e o cliente crashou. Eram o gênero, que vale 1 nos dois personagens da captura. Meça toda
fronteira nos dois registros.

**Reproduzir a captura não prova que o layout está certo.** O `S_CHARACTER_LIST` construído saía
byte a byte igual ao capturado e mesmo assim estava deslocado em um byte: a captura tem 2
personagens, e as duas leituras do cabeçalho só divergem com contagem diferente de 2. O que
desempata um layout é ele parsear em **dois casos diferentes**, ou fechar uma conta interna ao
pacote — no registro de personagem, `100000 + raça * 2 + gênero`.

**A base Java em `server/` é referência de protocolo, não só de lógica de jogo.** O layout do
registro de personagem saiu do `writePlayerInfo()` dela em minutos, depois de horas de comparação
byte a byte. Ela está algumas versões atrás, então serve como mapa de campos a conferir contra a
captura, não como verdade.

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
