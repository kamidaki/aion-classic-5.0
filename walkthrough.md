# Walkthrough — Transformação do Inicializador Rust em Aion Classic - EMU.exe e Padronização dos JARs

O executável em Rust foi completamente refatorado e transformado no inicializador e painel supervisor do **Emulador Java (Aion Classic 5.0 EU)**. Além disso, os JARs dos servidores foram renomeados e padronizados, e a documentação técnica foi atualizada.

---

## 1. O Que Foi Realizado

### 1.1 Padronização dos JARs dos Servidores
Os nomes dos JARs foram oficialmente renomeados em todos os `pom.xml`, scripts de build e no inicializador:
- `AL-Chat.jar` $\to$ **`ChatServer-ClassicEmu-Brasil.jar`**
- `Encom-Login-1.8.jar` $\to$ **`LoginServer-ClassicEmu-Brasil.jar`**
- `Encom-Game-1.8.jar` $\to$ **`GameServer-ClassicEmu-Brasil.jar`**

### 1.2 Atualização do Pipeline de Build e Deploy
- **`1 - Código Fonte [Emulador]/build-server.bat`**:
  - Atualizado para compilar os servidores e copiar os JARs canônicos diretamente para `2 - Emulador [Produto Final]/<Server>/` e `2 - Emulador [Produto Final]/<Server>/libs/`.
  - Expurgo da criação de scripts legados `StartAll.bat` e `StopAll.bat`.
- **`2.5 - Executável Rust [Emulador]/src/config.rs`** e **`2 - Emulador [Produto Final]/config.json`**:
  - Classpath atualizado para referenciar os novos nomes dos JARs.
  - Recompilado e publicado o binário `Aion Classic - EMU.exe`.

### 1.3 Atualização Completa da Documentação (`README.md`, `CONTEXT.md`, Plano 09)
Adicionadas seções completas e detalhadas explicando:
1. **Compilação**: Como compilar os servidores Java via Maven (`build-server.bat` ou `mvn clean package -DskipTests=true`) e o inicializador Rust (`Build.bat` ou `cargo build --release`).
2. **Deploy**: Procedimento de cópia e disponibilização dos binários e bibliotecas na pasta `2 - Emulador [Produto Final]`.
3. **Inicialização**: Execução pelo executável único `Aion Classic - EMU.exe` com boot sequencial e interface gráfica WebView2.
4. **Configuração (`config.json`)**: Explicação de todos os campos (`jvm_args`, `start_sequence_delay_seconds`, `database`, `gui`).
5. **Arquitetura WebSocket e Gerenciamento**:
   - `ManagementService.java` na porta `18091`: Shutdown gracioso de 60 segundos com anúncio in-game (`STR_SERVER_SHUTDOWN`) e salvamento de dados.
   - `WebSocketServer` na porta `18099`: Conexão full-duplex RFC 6455 para telemetria em tempo real e broadcast externo.

---

## 2. Validação e Testes

- **Compilação Java**:
  - `ChatServer`: `mvn package` concluído com sucesso (`ChatServer-ClassicEmu-Brasil.jar`).
  - `LoginServer`: `mvn package` concluído com sucesso (`LoginServer-ClassicEmu-Brasil.jar`).
  - `GameServer`: `mvn package` concluído com sucesso (`GameServer-ClassicEmu-Brasil.jar`).
  - `WebSocketServer`: Compilado com sucesso via Maven.
- **Compilação Rust**:
  - `Build.bat` executado com sucesso gerando o executável final `Aion Classic - EMU.exe`.
- **Deploy**:
  - Novos JARs copiados para as pastas de produção de `2 - Emulador [Produto Final]`.
  - JARs legados (`chat-server-5.0-SNAPSHOT.jar`, etc.) removidos.
- **Sincronização com GitHub**:
  - Commit no padrão obrigatório em português enviado para `origin/main`.
