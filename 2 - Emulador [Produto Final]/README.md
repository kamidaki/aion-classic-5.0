# Aion Classic 5.0 EU — Manual de Operacao e Configuracao do Emulador

Este diretorio contem a distribuicao executavel do emulador Aion Classic 5.0 (EU - Gameforge), pronta para execucao imediata em ambiente de producao ou desenvolvimento.

---

## 1. Como Inicializar o Emulador

A execucao de todos os servicos do emulador (ChatServer, LoginServer e GameServer) e centralizada em um unico executavel com interface grafica:

```text
Aion Classic - EMU.exe
```

### Procedimento de Inicializacao:
1. De um duplo clique em `Aion Classic - EMU.exe` (ou execute via terminal).
2. O aplicativo verifica se ja existe outra instancia em execucao atraves de um Named Mutex nativo do Windows, impedindo conflitos de portas.
3. O painel supervisor visual sera exibido automaticamente.
4. Caso a opcao `auto_start_servers_on_launch` esteja ativada no `config.json`, os servidores serao iniciados de forma sequencial automatica:
   - **1. ChatServer**: Sobe primeiro e aguarda conexoes.
   - **2. LoginServer**: Sobe em seguida com o intervalo configurado em `start_sequence_delay_seconds`.
   - **3. GameServer**: Sobe por ultimo, carregando os dados estaticos de mapas, NPCs e tabelas do jogo.
5. Todos os processos rodam em segundo plano (sem janelas pretas de console).
6. O icone do emulador e adicionado a **Bandeja do Sistema (System Tray)**. Fechar a janela principal oculta o painel para a bandeja. Clicar com o botao direito no icone da bandeja permite reabrir o painel ou encerrar todos os servidores com seguranca.

---

## 2. Como Configurar o Emulador (`config.json`)

O arquivo `config.json`, localizado na raiz deste diretorio, controla todos os parametros do inicializador e da JVM.

Se o arquivo for removido, o `Aion Classic - EMU.exe` recriara automaticamente uma copia com os valores padrao na primeira inicializacao.

### Estrutura Completa do `config.json`:

```json
{
  "launcher": {
    "start_with_windows": false,
    "auto_start_servers_on_launch": true,
    "start_sequence_delay_seconds": 3,
    "clean_archived_logs_days": 7
  },
  "paths": {
    "base_dir": ".",
    "chat_server_dir": "ChatServer",
    "login_server_dir": "LoginServer",
    "game_server_dir": "GameServer",
    "chat_server_log_dir": "ChatServer/log",
    "login_server_log_dir": "LoginServer/log",
    "game_server_log_dir": "GameServer/log"
  },
  "gui": {
    "theme": "dark",
    "window_width": 1440,
    "window_height": 900,
    "http_port": 18080
  },
  "database": {
    "auto_read_properties": true,
    "host": "",
    "port": 3306,
    "user": "",
    "password": "",
    "database": "aiondbls_gs"
  },
  "servers": {
    "chat": {
      "java_exe": "java",
      "jvm_args": [
        "-Xms128m",
        "-Xmx256m",
        "-Dfile.encoding=UTF-8",
        "-DconsoleEncoding=UTF-8"
      ],
      "main_class": "com.aionemu.chatserver.ChatServer",
      "classpath": "./libs/*;ChatServer-ClassicEmu-Brasil.jar;./libs/ChatServer-ClassicEmu-Brasil.jar",
      "working_dir": "ChatServer",
      "label": "Chat Server",
      "tag": "CS",
      "enabled": true,
      "color": "#00CED1",
      "management_port": null,
      "shutdown_delay_seconds": 5
    },
    "login": {
      "java_exe": "java",
      "jvm_args": [
        "-Xms64m",
        "-Xmx128m",
        "-server",
        "-Dfile.encoding=UTF-8",
        "-DconsoleEncoding=UTF-8"
      ],
      "main_class": "com.aionemu.loginserver.LoginServer",
      "classpath": "./libs/*;LoginServer-ClassicEmu-Brasil.jar;./libs/LoginServer-ClassicEmu-Brasil.jar",
      "working_dir": "LoginServer",
      "label": "Login Server",
      "tag": "LS",
      "enabled": true,
      "color": "#FFD700",
      "management_port": null,
      "shutdown_delay_seconds": 5
    },
    "game": {
      "java_exe": "java",
      "jvm_args": [
        "-Xms1280m",
        "-Xmx3192m",
        "-XX:MaxHeapSize=3192m",
        "-ea",
        "-Dfile.encoding=UTF-8",
        "-DconsoleEncoding=UTF-8"
      ],
      "main_class": "com.aionemu.gameserver.GameServer",
      "classpath": "./libs/*;GameServer-ClassicEmu-Brasil.jar;./libs/GameServer-ClassicEmu-Brasil.jar",
      "working_dir": "GameServer",
      "label": "Game Server",
      "tag": "GS",
      "enabled": true,
      "color": "#32CD32",
      "management_port": 18091,
      "shutdown_delay_seconds": 60
    }
  }
}
```

### Detalhamento dos Campos:

#### Bloco `launcher`:
- `start_with_windows` (booleano): Define se o executavel sera adicionado a inicializacao automatica do Windows.
- `auto_start_servers_on_launch` (booleano): Se `true`, inicia os 3 servidores sequencialmente assim que o executavel for aberto.
- `start_sequence_delay_seconds` (inteiro): Tempo em segundos de espera entre a subida de cada servidor na sequencia (recomendado: `3`).
- `clean_archived_logs_days` (inteiro): Apaga automaticamente logs compactados antigos apos N dias (padrao: `7`).

#### Bloco `gui`:
- `theme` (string): Tema visual do painel (`"dark"` ou `"light"`).
- `window_width` e `window_height` (inteiros): Resolucao inicial da janela do painel.
- `http_port` (inteiro): Porta TCP local para o servidor web do painel (padrao: `18080`). Acesso local via navegador: `http://127.0.0.1:18080/`.

#### Bloco `database`:
- `auto_read_properties` (booleano): Quando `true`, o inicializador le automaticamente os parametros de conexao (host, porta, usuario e senha) dos arquivos:
  - `GameServer/config/network/database.properties`
  - `LoginServer/config/network/database.properties`
  Caso queira forcar credenciais customizadas pelo JSON, defina `auto_read_properties: false` e preencha os campos `host`, `port`, `user`, `password` e `database`.

#### Bloco `servers` (`chat`, `login`, `game`):
- `java_exe` (string): Caminho do binario do Java. Por padrao utiliza `"java"`, buscando dinamicamente na variavel de ambiente `JAVA_HOME` ou no caminho padrao de instalacao do JDK 8 (`C:\Program Files\Java\jdk1.8.0_431\bin\java.exe`). Caso use um Java em local especifico, informe o caminho absoluto.
- `jvm_args` (array de strings): Argumentos de memoria e flags da JVM.
  - `-Xms`: Memoria inicial alocada.
  - `-Xmx`: Memoria maxima permitida para o processo.
  - `-XX:MaxHeapSize`: Tamanho maximo do heap.
  - `-Dfile.encoding=UTF-8`: Garante que todos os logs e leituras de XML utilizem encoding UTF-8.
- `classpath` (string): Caminho para as bibliotecas e o JAR principal do servidor.
- `working_dir` (string): Pasta de trabalho do servidor (`ChatServer`, `LoginServer` ou `GameServer`).
- `management_port` (inteiro ou null): Porta do listener HTTP de controle local do servidor (padrao: `18091` para o GameServer).
- `shutdown_delay_seconds` (inteiro): Contagem regressiva oficial de encerramento seguro (padrao: `60` segundos para o GameServer).

---

## 3. Desligamento Seguro e Prevencao de Rollback

Ao solicitar a parada ou reinicializacao do GameServer pelo painel supervisor:
1. O inicializador envia um comando seguro para a porta de gerenciamento do GameServer (`127.0.0.1:18091`).
2. O GameServer inicia uma contagem regressiva de **60 segundos** com aviso oficial na tela de todos os jogadores no jogo (`STR_SERVER_SHUTDOWN`).
3. O servidor ativa a protecao contra novas conexoes e salva os dados de todos os personagens conectados no banco de dados (`PlayerLeaveWorldService.startLeaveWorld`).
4. Somente apos o processo Java encerrar completamente, o supervisor atualiza o status para Offline ou reinicia o servico (caso seja uma reinicializacao).
5. Isso garante total integridade do inventario, itens, quests e niveis dos jogadores, eliminando rollbacks.

---

## 4. Conexao com o Banco de Dados (MySQL / MariaDB)

As configuracoes principais de conexao com o banco estao em:
- `GameServer/config/network/database.properties`
- `LoginServer/config/network/database.properties`

Exemplo de configuracao padrao:
```properties
database.url = jdbc:mysql://127.0.0.1:3306/aiondbls_gs?useUnicode=true&characterEncoding=UTF-8&allowPublicKeyRetrieval=true&useSSL=false&serverTimezone=UTC
database.user = root
database.password = sua_senha
```

O script inicial para criacao e importacao do banco de dados esta disponivel em:
```text
GameServer/sql/aiondbls_gs.sql
```
