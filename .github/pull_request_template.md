## Resumo das Alterações

<!-- Descreva objetivamente o que este Pull Request corrige, adiciona ou documenta. -->

Fixes #(issue)

---

> [!TIP]
> **Contribuição apenas de Documentação (`.md` / imagens / `README` / guias)?**
> Você está na **Via Rápida (`docs-only`)**! **NÃO** é necessário compilar Maven/JDK 25, gerar capturas de Wireshark/Ghidra nem preencher itens de código Java — o bot rotula, revisa e aprova automaticamente assim que as verificações leves passarem.

---

## Componente Afetado

- [ ] **Documentação (`.md` / Guias / Diagramas — Via Rápida `docs-only`)**
- [ ] `GameServer GameForge` (`game-server-gameforge` — GSID 1 | Referência Oficial EU)
- [ ] `LoginServer` (`login-server`) / `ChatServer` (`chat-server`) / `Commons` (`commons`)
- [ ] `Client Hook` (`version.dll` — conectividade e fixes de cliente)
- [ ] `Plugins Blender` (`Ferramentas e Documentos/Blender - Plugins/`)
- [ ] `Geo & Nav Builder / Ferramentas` (`Ferramentas e Documentos/`)
- [ ] `Sistema Multilínguas (l10n)` (preservando Português PT-BR como padrão)
- [ ] `Build / CI` (`.github/`, Maven)

---

## Checklist Proporcional ao Tipo de Mudança

### Obrigatório para qualquer PR
- [ ] Nenhuma credencial real, token privado, IP interno ou caminho local do PC (`C:\Users\<seu_usuario>\...`, `D:\AionCliente\...`) foi incluído.
- [ ] O idioma padrão do projeto (**Português / PT-BR**) foi preservado (exceto quando o recurso implementa seletor multilíngue).

### Aplicável apenas se você alterou código Java / C++ / Ferramentas *(contribuidores de `.md` podem ignorar)*
- [ ] **Escopo GameForge GSID 1:** Alterações de código respeitam o servidor oficial EU (`game-server-gameforge`), sem modificar servidores auxiliares desabilitados (`game-server-remake` / `game-server-battleroyale`).
- [ ] **Compilação / Validação:** Compilado com sucesso via `mvn clean package --file "Código Fonte - Emulador/pom.xml"` (se alterou Java) ou validado no Blender/ferramenta correspondente.
- [ ] **Qualidade de Implementação:** Sem gambiarras em Java para mascarar falhas em XMLs canônicos; comportamentos PvE alinhados à referência oficial quando aplicável.

---

## Evidências e Registros de Teste *(opcional para PRs de documentação)*

<!-- Para código: logs de build/testes ou prints. Para docs: um breve resumo já basta! -->
