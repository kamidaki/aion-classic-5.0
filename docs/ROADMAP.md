# Aion Classic 4.5 — estado e plano

Escrito para ser lido frio, sem contexto de conversa anterior.

---

## 1. O que é este projeto

Servidor privado para o cliente **Aion Classic 4.5 da GameForge**, build
`4526.0820.0706.7137`, x64, instalado em `G:\GFAion\aionclassic`.

A base é o **POC em Rust** em `EmuRustDurak` — originalmente escrito para o Classic 2.5 e
corrigido aqui para a 4.5. A pasta `reference/aion-lightning/` tem o Aion-Lightning (Java), que foi a base anterior
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

A lista de personagens sai do banco e o cliente devolve o id do banco quando você seleciona — a
tela de personagem é implementação, não replay (seção 5). O mundo carrega em Pandaemonium com
cenário, NPCs e minimapa; o personagem anda e a UI responde (seção 6).

**O que ainda é andaime:** o corpo no mundo e boa parte da sessão são bytes da captura com o id
trocado — o personagem aparece com a cara e o nome do capturado. Trocar isso por implementação é o
trabalho da seção 6.

---

## 3. Como rodar

Quatro processos. O cliente é aberto pelo próprio launcher — não abra o `Aion.exe` na mão.

```bash
cd EmuRustDurak

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
| `AION_CABECALHO` | escreve à mão os dois bytes do cabeçalho da lista, ex. `"2,1"`; para perguntar ao cliente sem recompilar |
| `AION_PACOTES_25` | manda também os pacotes da 2.5 na entrada no mundo. **Derruba o cliente**; ver seção 6 |
| `AION_CLIENT` | caminho do `aion.bin`. É a única coisa que muda de máquina para máquina |

### Para outra pessoa rodar

```bash
powershell -ExecutionPolicy Bypass -File pacote/empacotar.ps1
```

Compila, junta os quatro executáveis com o `replay.bin` e os scripts, e gera `dist/aion-emulador/`
mais um zip de ~2,6 MB. Quem receber preenche o caminho do cliente no `config.txt` e clica no
`INICIAR.bat`; o `LEIA-ME.txt` que vai junto explica o resto, inclusive as duas condições acima.

O `INICIAR.bat` fecha o `gfclient.exe`, detecta o IP da rede, recusa loopback e espera as portas
abrirem antes de chamar o cliente — cada uma dessas falhas produz o mesmo sintoma de "servidor
quebrado", e nenhuma é adivinhável de dentro do jogo.

Não vai nada do repositório: nem código, nem captura, nem ferramenta de análise. O `AION_DATA_DIR` é
opcional — sem ele o servidor roda igual, só não resolve nome de NPC e item nos logs.

### Gerar o `replay.bin`

Não vai para o git (deriva da captura). Regenerar com:

```bash
python tools/export_replay.py build/capture/gf-login.pcapng EmuRustDurak/replay.bin
```

---

## 4. Mapa do repositório

```
EmuRustDurak/          A BASE. Workspace Rust, 7 crates, compila limpo.
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
    mundo.rs                 mapa, posição e direção do ponto de entrada
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

pacote/                      o que vira o pacote para outra pessoa (seção 3)
docs/reverse/                achados de engenharia reversa
tools/                       ferramentas de análise (seção 8)
dist/                        pacote gerado. Fora do git.
build/capture/               capturas. Fora do git: contêm token de conta.

reference/                   NADA AQUI EXECUTA. É material de consulta.
  aion-lightning/            servidor Aion em Java. Foi de onde saiu o layout do registro
                             de personagem — é referência de protocolo tanto quanto de
                             lógica de jogo.
  dotnet-poc/                POC em C#. O protocolo de login dele não é o deste cliente.
```

**`EmuRustDurak/` é o servidor de verdade** — o que compila e roda, e de onde saem os quatro
executáveis do pacote. A pasta se chamava `reference/rust-poc`, o que sugeria o contrário: nem era
referência, nem era mais um POC.

---

## 5. A lista de personagens — resolvida

O `S_CHARACTER_LIST` é montado do banco, no layout 4.5 (`lista_personagens.rs`), e o cliente
aceita: desenha o personagem do banco na tela de personagem e devolve **o id do banco** quando você
seleciona. Confirmado contra o cliente em 20/08/2026.

O layout campo a campo está em `docs/protocol/character-list.md`. Duas coisas valem repetir aqui:

**O byte 0 do cabeçalho não é contagem.** Ele precisa valer `0x02`; a contagem fica no byte 10. Na
captura os dois valem 2, o que escondia a diferença — com 1 personagem elas se separam, e mandar a
contagem no byte 0 fazia o cliente parar na tela de servidor sem mensagem nenhuma. O significado do
byte 0 continua desconhecido.

**O registro sai de um molde do Durak.** O servidor escreve id, nome e nível; aparência,
equipamento, classe, raça, posição e mapa são os dele, iguais para todo personagem.

### Como isso foi isolado

Vale como método, porque o sintoma não apontava para nada. Comparando duas capturas do nosso próprio
servidor pacote a pacote, os 18 primeiros saíam **idênticos byte a byte**, e o pacote 19 quebrado
era o pacote 19 que funciona, truncado, com um byte trocado. Isso reduziu a causa a quatro bytes
possíveis, e três rodadas do cliente separaram qual deles era.

Nenhuma etapa dessa dependeu de adivinhar o que o cliente estava pensando.

---

## 6. A entrada no mundo

O cliente entra em Pandaemonium com cenário, NPCs e minimapa; o personagem aparece, anda, e a UI
responde. Vida, barra de skills e inventário vêm preenchidos. Confirmado contra o cliente em
21/08/2026.

Boa parte disso ainda é andaime — ver "o que é reprodução", abaixo.

### O que estava faltando

**Os opcodes da 2.5 estão deslocados em `0x10`.** A seleção de personagem é `0x18` (era `0x08`) e o
"terminei de carregar" é `0x19` (era `0x09`). Os dois handlers já existiam no POC, registrados nos
números velhos — nunca eram chamados. Sem tratar a seleção, a sessão ficava com personagem `0` e a
entrada no mundo saía sem mapa nem posição.

**O mapa precisa concordar em dois lugares.** O cliente pré-carrega o cenário pelo mapa que está no
registro do personagem, dentro do `S_CHARACTER_LIST`, e depois entra pelo mapa do `S_WORLD`. Os dois
leem de `game::mundo` — Pandaemonium, com a posição e a direção exatas da captura. É o ponto de
nascimento da 4.5: a Kimmie da captura tinha cinco minutos de criada.

**O id da captura aparece espalhado pelos pacotes replayados.** O replay já trocava a chave de
sessão; faltava o id do personagem. Sem isso o cliente recebe dois "eus", e os buffs, a animação e o
estado falam do outro. Foi a troca que fez a Siel's Aura cair no personagem certo.

**O replay só atendia opcode sem implementação** — e os lotes que faltavam estavam justamente sob
opcodes que têm handler: o burst de entrada no mundo está indexado sob o
`C_REQUEST_SERIAL_KILLER_LIST`, o bloco que vem logo antes de o cliente andar está sob o
`C_SYNC_TIME`, e skills e inventário estão sob o `C_2ND_PASSWORD`. Depois da seleção de personagem o
replay passa a atender também quem tem implementação.

Ação do jogador nunca é atendida pelo replay. A resposta gravada fala de outro movimento e para o
personagem no meio do passo — foi o que aconteceu com o `C_MOVE_NEW`.

### O que é reprodução, e não implementação

| o quê | de onde vem |
|---|---|
| lista de personagens | **implementação**: id, nome e nível saem do banco |
| mapa, posição e direção | **implementação**: `game::mundo`, nos dois lugares |
| `S_STATUS` (396 bytes) e `S_PUT_USER` (481) | captura, com o id trocado — por isso o corpo no mundo é o da Kimmie |
| o lote de entrada no mundo (8 pacotes) | captura, em `capturado.rs` |
| NPCs, buffs, abyss, chat, mail, LFG (~190 pacotes) | captura, pelo motor de replay |

### Os pacotes 2.5 que crasham

`S_STATUS` sai com 312 bytes contra 396 da captura, `S_ADD_SKILL` 376 contra 325,
`S_LOAD_INVENTORY` 1907 contra 3363. Com eles ligados o cliente carrega Pandaemonium e crasha logo
depois. Ficam atrás de `AION_PACOTES_25=1`.

Dois do mesmo grupo **batem** com a captura e estão ligados: o `S_WORLD_INFO`, que sai byte a byte
igual, e o `S_CUR_STATUS`, de 1 byte.

### As skills não disparam, e a captura não ajuda

Apertar uma skill não produz **nenhum pacote**: o cliente recusa do lado dele. O que chega enquanto
se aperta é `0x3B` (1 byte, `01`) e `0x86` (o id do personagem), que são outra coisa.

E a captura não tem resposta: a sessão gravada só logou, andou um pouco e terminou. Ela não usa
skill, não ataca, não abre janela nenhuma. Não dá para saber nem qual é o opcode de uso de skill na
4.5 — a tabela do `Game.dll` chama `0x21` de `C_USE_SKILL`, e essa tabela já errou em cinco pontos
conhecidos.

**O desbloqueio é uma captura nova**, contra o servidor oficial, cobrindo o que falta: usar skill,
atacar um mob, pegar loot, abrir inventário e loja, falar no chat, trocar de mapa. Foi assim que a
captura de login destravou tudo o que existe aqui hoje — cada bloqueio virou comparação byte a
byte, em vez de tentativa e erro.

Sem ela, o caminho é engenharia reversa do `Game.dll` para achar o opcode e a condição que o
cliente checa antes de liberar o botão. Muito mais caro.

### O próximo passo

Decodificar o `S_STATUS` e o `S_PUT_USER`, nessa ordem. São os dois que fazem o personagem ser o do
banco em vez do capturado, e o método é o que já funcionou duas vezes: pegar o `writeImpl` do
pacote correspondente no Aion-Lightning como mapa de campos, conferir contra os bytes da captura, e
procurar uma redundância interna que valide o alinhamento — no registro da lista foi
`100000 + raça * 2 + gênero`.

Depois deles, trocar os pacotes replayados um a um, na ordem em que aparecem na captura. Cada um que
sair do replay é um a menos de sessão emprestada.

---

## 7. Depois que o mundo carregar

Em ordem. Cada item destrava o seguinte.

### 7.1 Trocar o andaime por implementação

O `replay.rs` serve pacotes capturados para todo opcode sem implementação. Cada um que for
implementado sai do replay naturalmente. A ordem sensata é a da própria captura — use
`tools/decode_game.py` para ver qual vem primeiro.

O tipo `Bruto` em `server.rs` existe para essa transição: monta o prelude normalmente e usa payload
pronto, então dá para trocar um pacote de cada vez sem parar o fluxo.

### 7.2 Corrigir a tabela nome↔opcode

O pareamento nome↔número foi feito por heurística sobre o `Game.dll` e **erra em alguns pontos**.
Dois casos comprovados:

- `0x5E`, que a tabela chama de `C_GET_OFF_VEHICLE`, na verdade devolve a chave de sessão
- `0xD6`, que a tabela chama de `C_SA_CONFIRMGOODS`, carrega MAC, id de hardware e IP
- `0x18`, que a tabela chama de `C_TOGGLE_CHEST`, é a **seleção de personagem**
- `0x19`, que a tabela chama de `C_GIVE_ITEM`, é o **"terminei de carregar o mapa"**
- `0x56`, que a tabela chama de `C_QUERY_NUMBER_RESULT`, é um canal de log do cliente: foi por ele
  que chegou `[INIT][1] SCANNER : LOADING LIST FAILED.`

Agora que o conteúdo dos pacotes é legível, a tabela é corrigível. `docs/protocol/README.md` explica
como a extração funciona.

### 7.3 Preencher o registro de personagem

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

### 7.4 Dados do cliente 4.5

`AION_DATA_DIR` aponta hoje para XML extraído em `G:\CodexHELPER\ClaudeAion\extracted_xml`, de
proveniência não confirmada. O certo é regenerar do cliente 4.5 com os crates `pak` e `bxml`, que
já existem no workspace.

---

## 8. Ferramentas

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

## 9. Armadilhas conhecidas

Cada uma destas custou tempo real.

**"Igual nos dois personagens" não significa "vazio".** Significa estático — e estático pode ser
obrigatório. Zerei quatro bytes de dados reais por deduzir a fronteira do campo de nome em vez de
medi-la, e o cliente crashou. Eram o gênero, que vale 1 nos dois personagens da captura. Meça toda
fronteira nos dois registros.

**Opcode que "não existe" pode ser o mesmo, deslocado.** Entre a 2.5 e a 4.5, a seleção de
personagem foi de `0x08` para `0x18` e o "terminei de carregar" foi de `0x09` para `0x19` — os dois
somaram `0x10`. Os handlers já estavam escritos e corretos; só o número estava velho, e o sintoma
era o servidor ignorar um pacote que o cliente mandava. Antes de escrever handler novo para um
opcode desconhecido, vale procurar o handler existente que faz exatamente aquilo.

**Um campo que sempre teve o mesmo valor pode ser dois campos.** No cabeçalho da lista de
personagens, o byte 0 e o byte 10 valem os dois 2 na captura, e valem os dois 0 na lista vazia.
Parecem o mesmo dado repetido, e não são: um é contagem, o outro é uma marca que precisa valer
`0x02`. Só uma contagem diferente de 2 separa os dois — e a captura não tinha nenhuma.

**Reproduzir a captura não prova que o layout está certo.** O `S_CHARACTER_LIST` construído saía
byte a byte igual ao capturado e mesmo assim estava deslocado em um byte: a captura tem 2
personagens, e as duas leituras do cabeçalho só divergem com contagem diferente de 2. O que
desempata um layout é ele parsear em **dois casos diferentes**, ou fechar uma conta interna ao
pacote — no registro de personagem, `100000 + raça * 2 + gênero`.

**A base Java em `reference/aion-lightning/` é referência de protocolo, não só de lógica de jogo.** O layout do
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

## 10. O que existe e não está em uso

- **`reference/aion-lightning/`** — Aion-Lightning em Java, base anterior. Compila no JDK 21 (correções em
  `scripts/build_login.sh`), tem banco criado no MariaDB local. Vale como **referência de lógica de
  jogo**: quests, skills, IA, instâncias. A camada de rede dele é retail e não serve.
- **`reference/dotnet-poc/`** — POC em C#. O `walkthrough.md` dele descreve um protocolo de login
  que este cliente **não usa**; ver `docs/reverse/login-protocol-findings.md`.
- **`scripts/`** — scripts da era Java (build, banco, verificação de pacotes de login).
