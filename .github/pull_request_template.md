## Resumo das Alterações

<!-- Descreva de forma concisa e objetiva a alteração implementada neste Pull Request e qual problema ela resolve. -->

Fixes #(issue)

---

## GameServer ou Componente Específico Afetado

<!-- Selecione OBRIGATORIAMENTE apenas um GameServer ou o componente de infraestrutura correspondente. -->
<!-- NUNCA suba alterações para múltiplos GameServers no mesmo Pull Request. -->

- [ ] `GameServer GameForge` (`game-server-gameforge` - GSID 1 | Porta 7777)
- [ ] `GameServer Remake` (`game-server-remake` - GSID 2 | Porta 7778)
- [ ] `GameServer BattleRoyale` (`game-server-battleroyale` - GSID 3 | Porta 7779)
- [ ] `ChatServer` (`chat-server` - Componente compartilhado / apenas conectividade)
- [ ] `LoginServer` (`login-server` - Componente compartilhado / apenas conectividade)
- [ ] `Client Hook` (`version.dll` - Proxy hook e No-IP)
- [ ] `Supervisor Nativo` (`Aion Classic - EMULADOR.exe` - Rust)
- [ ] `Academy NoLag` (.NET 9 / C#)
- [ ] `Parsers e Ferramentas` (Python / PowerShell)

---

## Tipo de Mudança

- [ ] Correção de Bug (*bug fix*)
- [ ] Nova Funcionalidade (*new feature*)
- [ ] Refatoração de Código (*refactor*)
- [ ] Otimização de Performance (*perf*)
- [ ] Melhoria de Segurança (*security*)
- [ ] Documentação (*docs*)

---

## Lista de Verificação de Fidelidade, Evidências e Qualidade

- [ ] **Escopo Pequeno, Mínimo e Atômico:** Este PR foca exclusivamente em um único sistema ou problema bem delimitado, sem misturar múltiplos sistemas ou mecânicas.
- [ ] **Isolamento Absoluto de GameServers:** Confirmo que este PR NÃO alterou nem excluiu arquivos de outros GameServers sem autorização prévia.
- [ ] **Testes e Imagens Comprobatórias:** Anexei abaixo capturas de tela e/ou gravações demonstrando o funcionamento real in-game e os logs de execução sem erros.
- [ ] **Validação com o Servidor Oficial Gameforge:** O comportamento, fórmulas e valores foram comparados e validados diretamente contra o servidor oficial Aion Classic Gameforge.
- [ ] **Confirmação via Ghidra:** Incluí trecho de descompilação/disassembly do binário oficial de 64 bits (`bin64`) comprovando structs, constantes e lógica oficial.
- [ ] **Confirmação via Wireshark:** Incluí dissecção de pacote oficial (`.pcap`) comprovando paridade byte a byte de opcodes e payload.
- [ ] **Zero Bypass de XML:** Nenhuma gambiarra ou fallback hardcoded foi introduzido em Java para suprir falta de dados estáticos; dados ausentes foram corrigidos diretamente nos templates XML.
- [ ] **Compilação 100% Limpa e Sincronizada:**
  - `mvn clean package` aprovado sem erros.
  - Sincronização realizada entre `Código Fonte - Emulador` e `Emulador - Produto Final` (e `Patch final - Client 5.0`, se aplicável).
- [ ] **Portabilidade Absoluta:** Nenhum caminho absoluto ou fixo de disco (`C:\`, `D:\`) foi inserido.
- [ ] **Padrão de Commits:** Commits em Português do Brasil, formato de uma linha técnica por alteração e sem emojis.
- [ ] **Discord-User Informado:** `Discord-User: @seu_usuario` incluído para liberação de permissão no Discord oficial após o merge.

---

## Evidências Anexadas (Capturas de Tela, Ghidra e Wireshark)

<!-- ANEXE AQUI: -->
<!-- 1. Prints in-game demonstrando o teste real. -->
<!-- 2. Evidência do Ghidra (offsets / pseudo-código C++ de bin64). -->
<!-- 3. Evidência do Wireshark (frame / pacote oficial capturado). -->
