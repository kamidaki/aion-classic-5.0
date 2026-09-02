# 09 - Compilação, Deploy e Publicação em Produto Final

## 1. Fluxo de Compilação
- **Maven Multi-Módulo**:
  ```bash
  mvn clean package -DskipTests
  ```
- O build gera os artefatos nos targets com a nomenclatura oficial:
  - `ChatServer/target/ChatServer-ClassicEmu-Brasil.jar`
  - `LoginServer/target/LoginServer-ClassicEmu-Brasil.jar`
  - `GameServer/target/GameServer-ClassicEmu-Brasil.jar`
  - `WebSocketServer/target/AL-WebSocket.jar`

- **Inicializador Rust (Aion Classic - EMU)**:
  ```bat
  cd "2.5 - Executável Rust [Emulador]"
  Build.bat
  ```
  Gera o executável `Aion Classic - EMU.exe` otimizado em release.

---

## 2. Publicação e Distribuição em `2 - Emulador [Produto Final]`
- O destino final para a distribuição é:
  - `2 - Emulador [Produto Final]`
- Artefatos publicados:
  - `Aion Classic - EMU.exe` (executável único de inicialização com painel WebView2)
  - `config.json` (configuração do inicializador, parâmetros de memória JVM e portas)
  - `ChatServer/ChatServer-ClassicEmu-Brasil.jar` (e em `ChatServer/libs/`)
  - `LoginServer/LoginServer-ClassicEmu-Brasil.jar` (e em `LoginServer/libs/`)
  - `GameServer/GameServer-ClassicEmu-Brasil.jar` (e em `GameServer/libs/`)
- Os scripts obsoletos BAT/SH foram eliminados em favor do executável supervisor único.

---

## 3. Gerenciamento e Telemetria
- **ManagementService (`127.0.0.1:18091`)**: Endpoint local no GameServer para shutdown gracioso de 60s com anúncio oficial no jogo (`STR_SERVER_SHUTDOWN`) e salvamento de dados.
- **WebSocketServer (`127.0.0.1:18099`)**: Servidor WebSocket nativo (RFC 6455) para broadcast e telemetria externa.

---

## 4. Versionamento Git e Entrega
- Após compilação e teste bem-sucedido de todos os módulos:
  1. `git status` para conferir a árvore de trabalho limpa e precisa.
  2. `git add -A`
  3. `git commit -m "Título em português\n- modulo: descricao..."`
  4. `git push origin main`
