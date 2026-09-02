# 09 - Compilação, Deploy e Publicação em Produto Final

## 1. Fluxo de Compilação
- **Maven Multi-Módulo**:
  ```bash
  mvn clean package -DskipTests
  ```
- O build deve gerar os artefatos nos targets:
  - `LoginServer/target/login-server-5.0-SNAPSHOT.jar`
  - `GameServer/target/game-server-5.0-SNAPSHOT.jar`
  - `ChatServer/target/chat-server-5.0-SNAPSHOT.jar`

---

## 2. Publicação e Distribuição em `PRODUTO FINAL`
- O destino final mandatado para a distribuição é:
  - `2 - Emulador [Produto Final]`
- Atualizar exclusivamente as JARs e arquivos alterados:
  - `PRODUTO FINAL/LoginServer/login-server.jar` (e libs alteradas, se houver)
  - `PRODUTO FINAL/GameServer/game-server.jar` (e data/libs alteradas)
  - `PRODUTO FINAL/ChatServer/chat-server.jar`
- Validar a integridade das pastas de scripts de execução:
  - `StartAll.bat`, `StopAll.bat`, `StartGS.bat`, `StartLS.bat`, `StartCS.bat`.

---

## 3. Versionamento Git e Entrega
- Após compilação e teste bem-sucedido de todos os módulos:
  1. `git status` para conferir a árvore de trabalho limpa e precisa.
  2. `git add .`
  3. `git commit -m "feat(5.0): finalizacao completa da auditoria, protocolo, opcodes e deploy do emulador Aion Classic 5.0"`
  4. `git push origin main`
