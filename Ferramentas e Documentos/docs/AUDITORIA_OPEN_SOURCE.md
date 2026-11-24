# Auditoria Prévia para Publicação Open Source — Aion Classic 5.0 (Lost Academy Group)

**Data da Auditoria Inicial:** 24/11/2026  
**Escopo:** Repositório `https://github.com/kamidaki/aion-classic-5.0` (baseline anterior às modificações de higienização e reestruturação).  
**Idioma Padrão:** Português (PT-BR).

---

## 1. Situação Encontrada

### 1.1 Estrutura Atual do Workspace
O repositório encontra-se dividido em três grandes blocos na raiz, além dos documentos de governança e da pasta `.github/`:

- **Raiz:** `.gitignore`, `CODE_OF_CONDUCT.md`, `CONTEXT.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `SECURITY.md`, `SUPPORT.md`.
- **`.github/`:** `CODEOWNERS`, `ISSUE_TEMPLATE/` (`bug_report.yml`, `config.yml`, `feature_request.yml`, `security_vulnerability.yml`), `pull_request_template.md`, `dependabot.yml`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md` e `workflows/` (`ci-backend.yml`, `ci-dotnet.yml`, `ci-rust.yml`, `commitlint.yml`, `release.yml`, `security-scan.yml`).
- **`Código Fonte - Emulador/`:** projeto multi-módulo Apache Maven (`com.aionemu:aion-server:4.8-SNAPSHOT`) contendo:
  - `commons`
  - `login-server`
  - `chat-server`
  - `game-server-gameforge` (GameServer 1 — GSID 1)
  - `game-server-remake` (GameServer 2 — GSID 2)
  - `game-server-battleroyale` (GameServer 3 — GSID 3)
- **`Emulador - Produto Final/`:** distribuição compilada para execução via launcher Rust (`Aion Classic - EMULADOR.exe`) contendo `Config/`, `LoginServer/`, `ChatServer/`, `GameServer-GameForge/`, `GameServer-Remake/`, `GameServer-BattleRoyale/`, `logs/` e `desktop.ini`.
- **`Ferramentas e Documentos/`:**
  - `Auditorias e Relatórios/`
  - `Client e Coletas/` (alto volume de capturas/arquivos do cliente atualmente rastreados no Git)
  - `Códigos bin64/` (fontes/auditorias CryEngine, `Código Fonte - Game.dll`, `Código Fonte - Version.dll`)
  - `Ferramentas Python e PowerShell/` (scripts auxiliares e `Código Fonte - Executável Rust do Emulador`)
  - `Geo and Nav Builder - Official Client/` (projeto Maven auxiliar `aion-geo-nav-builder` para geração de mapas `.geo` e `.nav`)
  - `Opcodes Oficiais - Classic 5.0/`
  - `Patch final - Client 5.0/` (pacote de cliente x64/x86, shaders, localização PT-BR/EN e scripts `.bat`)

### 1.2 Estado Pendente no Git (Alterações do Proprietário)
No momento da auditoria inicial (`HEAD` em `98af37a1eabae570a34f1579cd350a42aba48f52`), o working tree já continha **422 alterações não commitadas** realizadas pelo proprietário, que **devem ser estritamente preservadas**:
- **419 remoções:**
  - `Ferramentas e Documentos/Blender - Aion Plugins/` (207 arquivos)
  - `Ferramentas e Documentos/Códigos bin64/Código Fonte - BrService.dll/` (34 arquivos)
  - `Ferramentas e Documentos/Ferramentas Java/` (20 arquivos)
  - `Ferramentas e Documentos/Ferramentas Python e PowerShell/Código Fonte - Academy NoLag/` (158 arquivos)
- **3 modificações:** `shader_fix.cpp`, `version.cpp` e `Ferramentas e Documentos/Patch final - Client 5.0/bin64/version.dll`.

Adicionalmente, o banco de objetos do Git possui 4 tags (`v2.0.0`, `v2.0.1`, `v2.0.2`, `v3.0.0`), branch auxiliar `pre-java25-migration` e **24 Pull Requests remotos** (`#1` a `#24`, majoritariamente Dependabot + `#1` obsoleto e `#2`–`#4` já incorporados no `HEAD`).

### 1.3 Stack, Bibliotecas e Ferramentas Verificadas
- **Java:** POMs configurados com `<maven.compiler.release>25</maven.compiler.release>` (JDK `25.0.2` disponível em máquina; `JAVA_HOME` de sistema apontava para JDK 21).
- **Dependências Maven principais:** `logback-classic:1.5.21` (e `logback-core:1.5.21`), `fastjson2:2.0.60`, `HikariCP:7.0.2`, `mysql-connector-j:9.5.0`, `io.netty:netty-all:4.1.138.Final` (chat-server), `quartz:2.5.1`, `commons-lang3:3.20.0`, `jaxb-impl:2.3.9`, `jakarta.xml.bind-api:2.3.3`, `protobuf-java:4.31.1`, `guava`, `junit-jupiter:6.0.1`, `mockito`, `assertj-core`, `slf4j-api:2.0.17` (`chat-server`/`login-server`) e `2.0.16` (game-servers).
- **Rust (Supervisor `Aion Classic - EMULADOR.exe`):** Cargo / `rustc 1.95.0` em `Ferramentas e Documentos/Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador/Cargo.toml` (`425` pacotes resolvidos em `Cargo.lock`).
- **Arquivos de Inicialização:**
  - `Emulador - Produto Final/Aion Classic - EMULADOR.exe` (orquestrador principal) + `Emulador - Produto Final/Config/config.json`.
  - `Código Fonte - Emulador/login-server/dist/{start.bat,start.sh}` e `chat-server/dist/{start.bat,start.sh}`.
  - `Ferramentas e Documentos/Patch final - Client 5.0/Start x64 - PORTUGUÊS BRASIL.bat` e `Start x64 - INGLÊS.bat`.
- **Inspeção Nativa via REA (`inspect_pe_imports`, `inspect_native_exports`, `inspect_rust_binary`):**
  - `Patch final - Client 5.0/bin64/version.dll` e `bin32/version.dll`: **0** importações/exportações apontando para `BrService.dll`.
  - `Emulador - Produto Final/Aion Classic - EMULADOR.exe`: sem seção `.dep-v0`; precisa ser recompilado após higienização de `src/config.rs` e `src/db_manager.rs` porque carrega defaults internos no binário.

---

## 2. Análise Individual dos Módulos

| Módulo | Caminho | Estado Atual | Achados Principais |
|---|---|---|---|
| **POM Pai** | `Código Fonte - Emulador/pom.xml` | Ativo | Usa versão `4.8-SNAPSHOT`, compiler release 25, inclui os 6 submódulos sem perfil opcional para BattleRoyale. |
| **Commons** | `Código Fonte - Emulador/commons` | Compila e passa (1 teste) | Versão `4.8-SNAPSHOT`; declara `logback-classic:1.5.21` (vulnerável via `logback-core`); assemblies dos servidores dependem da versão do artefato `commons`. |
| **Login Server** | `Código Fonte - Emulador/login-server` | Compila (sem suíte `src/test`) | Versão `4.8-SNAPSHOT`; `Config.java` contém token default legado `#@br!...`; `Emulador - Produto Final/LoginServer/sql/aion_ls.sql` contém senha de conexão entre servidores não higienizada nas linhas de `gameservers`. |
| **Chat Server** | `Código Fonte - Emulador/chat-server` | Compila (0 testes) | Versão `4.8-SNAPSHOT`; Netty já em `4.1.138.Final`; `network.properties` contém senha de autenticação GameServer não higienizada. |
| **GameServer GameForge (GSID 1)** | `Código Fonte - Emulador/game-server-gameforge` | Compila; 195 testes: **3 falhas, 5 skips** | Versão `4.8-SNAPSHOT`; módulo alvo oficial GSID 1; `CustomConfig.java`, `GameServer.java`, `DpsService.java`, `WebSocketClientSession.java`, `WebSocketServer.java` e `custom.properties` citam `BrService.dll` / `[BrSocket]` e token `#@br!...`; `database.properties` e `network.properties` têm IP privado, usuário, porta customizada e senha reais; resíduos e créditos 4.8 / Beyond Aion presentes em serviços de recompensa/comentários. |
| **GameServer Remake (GSID 2)** | `Código Fonte - Emulador/game-server-remake` | Compila; 195 testes: **3 falhas, 5 skips** | Projeto secundário; hoje habilitado por padrão no `config.json` e no `config.rs`; apresenta as mesmas exposições de configuração e referências `BrService.dll` do GSID 1; deve permanecer desabilitado por padrão no Open Source. |
| **GameServer BattleRoyale (GSID 3)** | `Código Fonte - Emulador/game-server-battleroyale` | Compila; 195 testes: **3 falhas, 5 skips** | Modo secundário; habilitado no `config.json` atual; `libs/` no Produto Final possui JAR duplicado (`game-server-4.8-SNAPSHOT.jar` + `game-server-battleroyale-4.8-SNAPSHOT.jar`); deve ficar desabilitado por padrão e isolado em `<profile>` Maven opcional. |
| **Geo and Nav Builder** | `Ferramentas e Documentos/Geo and Nav Builder - Official Client` | Auxiliar independente | `README.md` cita caminho local de máquina para o cliente. |
| **Módulos Nativos (`Códigos bin64`)** | `Ferramentas e Documentos/Códigos bin64` | C++ / Python / Docs | `Código Fonte - BrService.dll` já removido pelo proprietário; `Cry3DEngine.dll/Release64/` possui ~385 arquivos intermediários `.obj`/`.lib`/`.exp` versionados no Git; scripts Python/BAT e `README.md`/`CONTEXT.md` citam caminhos locais de disco e IP privado de desenvolvimento. |
| **Supervisor Rust** | `Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador` | Cargo (Rust 1.95) | `src/config.rs` embute credenciais/IP privado reais e defaults ligando `Remake` em vez de `GameForge`; `src/db_manager.rs` injeta senha legada em `gameservers`; `Cargo.lock` possui 5 crates com advisories de segurança. Nota: pasta pai entrará no `.gitignore`. |
| **Produto Final** | `Emulador - Produto Final` | Binários desatualizados/expostos | JARs `*-4.8-SNAPSHOT.jar` antigos; `Config/config.json` e todos os `database.properties` / `network.properties` com dados privados; `Remake` e `BattleRoyale` ativos; arquivos temporários em `log/` contendo IPs locais e caminhos do host. |

---

## 3. Problemas Identificados

1. **Referências residuais à `BrService.dll`:** comentários, logs `[BrSocket]`, strings `BrService Telemetry Connected` e avisos extensos na documentação principal (`README.md`, `CONTEXT.md`, `Códigos bin64/README.md`, `Código Fonte - Version.dll/README.md`) e nas 3 instâncias Java.
2. **Nomenclatura e versionamento inconsistentes no Maven:** uso de `4.8-SNAPSHOT` nos `pom.xml`, divergente dos nomes alvo `*-LostAcademyGroup.jar` e incompatível com um projeto Aion Classic 5.0.
3. **Configuração padrão invertida:** `GameForge (GSID 1)` desabilitado e `Remake` + `BattleRoyale` habilitados no `Emulador - Produto Final/Config/config.json` e no código Rust (`src/config.rs`).
4. **Falhas nos testes Maven (baseline observado em 24/11/2026 com JDK 25):**
   - `SkillStaticDataAuditTest.sourceAndProductSkillTemplatesAreByteIdentical`: procura pasta obsoleta `Emulador - Produto Final\GameServer\data\static_data\skills\skill_templates.xml` em vez de `GameServer-GameForge`, além de divergência de hash SHA-256 entre `game-server-gameforge/data` e `Emulador - Produto Final/GameServer-GameForge/data`.
   - `ItemUpdateTypeTest.reasonIsTheCapturedOneOrZero`: `DEC_KINAH_RANKING_BUFF` retornou `270` (`0x10E`), enquanto o teste esperava `0`.
   - `ClassicItemSystemsTest.everyGameplayMaskUsesOnlyFlagsBackedByClassicClientData`: esperado `79664`, obtido `79671`.
5. **Documentação desalinhada com a diretriz Open Source:**
   - `README.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `.github/SUPPORT.md`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml` ainda citam suporte individual, GSID 2/3 no fluxo de contribuição, caminhos `D:\GameForge\...` e a versão antiga do projeto.
   - `README.md` não apresenta o status `PvE: 60%`, `Full PvP: 100%`, `Classe Bard: 70%`, a política estrita de PR para GSID 1, a seção do site `Aion Remake` e a árvore de origem/créditos da Beyond Aion conforme exigido.
6. **Workflows e `.github/` quebrados após exclusões do proprietário:**
   - `.github/workflows/ci-dotnet.yml` referencia solução `AcademyNoLag.sln` já removida pelo proprietário.
   - `.github/workflows/ci-rust.yml` e `.github/release.yml` dependem de diretórios que entrarão no `.gitignore` (`Ferramentas Python e PowerShell/`) ou de caminhos obsoletos (`game-server/target/*.jar`).
   - `.github/workflows/security-scan.yml` contém exclusivamente os checks `CodeQL Static Security Analysis` e `Verificacao de Segredos (Gitleaks)` que precisam ser removidos.
   - `CODEOWNERS` ainda referencia `Academy NoLag`, `BrService.dll`, `Remake`, `BattleRoyale` e pastas obsoletas.
7. **Dependências duplicadas/desalinhadas em `Emulador - Produto Final/*/libs/`:**
   - `GameServer-BattleRoyale/libs` contém simultaneamente `game-server-4.8-SNAPSHOT.jar` e `game-server-battleroyale-4.8-SNAPSHOT.jar`.
   - `GameServer-*/libs` usa `slf4j-api-2.0.16.jar`, enquanto `ChatServer/libs` e `LoginServer/libs` usam `slf4j-api-2.0.17.jar`.
8. **Rastreamento indevido no Git:** `Ferramentas e Documentos/Client e Coletas/` (115.761 arquivos), `Ferramentas e Documentos/Ferramentas Python e PowerShell/` (503 arquivos), `desktop.ini` (4 arquivos) e artefatos de build `.obj`/`.lib`/`.exp` em `Cry3DEngine.dll/Release64/` estão versionados no índice Git.

---

## 4. Riscos de Segurança

1. **Exposição de Credenciais e IPs Privados no Working Tree e no Histórico Git (CRÍTICO):**
   - Credenciais reais de banco de dados (usuário privado, senha administrativa, IP interno e porta não padrão) encontradas em:
     - `Emulador - Produto Final/Config/config.json`
     - `Código Fonte - Emulador/{game-server-gameforge,game-server-remake,game-server-battleroyale}/config/network/database.properties`
     - `Emulador - Produto Final/{LoginServer,ChatServer,GameServer-GameForge,GameServer-Remake,GameServer-BattleRoyale}/config/network/database.properties`
     - `Ferramentas e Documentos/Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador/src/config.rs` (e compiladas no binário `Aion Classic - EMULADOR.exe`)
     - `CONTEXT.md` (menção direta ao IP e porta de banco).
   - Senha compartilhada de comunicação entre servidores (`gameserver.network.*.password`, `chatserver.network.gameserver.password` e `Emulador - Produto Final/LoginServer/sql/aion_ls.sql` + `src/db_manager.rs`).
   - Token legado WebSocket/LoginServer (`#@br!...`) em `CustomConfig.java`, `custom.properties` (origem e produto final) e `login-server/.../Config.java`.
   - IP privado adicional encontrado em diagrama de `Ferramentas e Documentos/Códigos bin64/Código Fonte - Game.dll/CONTEXT.md`.
   - Logs temporários locais em `Emulador - Produto Final/*/log/` contendo IP LAN do host e caminhos completos da máquina (atualmente ignorados pelo `.gitignore`, mas precisam ser limpos do pacote final).
   - **Histórico Git comprometido:** commits antigos (como `96e154dc4` e anteriores) carregam essas credenciais e IPs privados, além de binários e exclusões antigas — tornando obrigatório o backup privado externo + reconstrução de histórico limpo (`orphan branch`) antes de qualquer publicação pública.
2. **Caminhos Internos de Máquina e Infraestrutura Privada:**
   - Referências frequentes a diretórios locais em READMEs, scripts `.bat`/`.py` e relatórios (`D:\GameForge\...`, `D:\AION CLASSIC 5.0 - EMULADOR\...`, diretório de usuário local e unidades externas).
3. **Vulnerabilidades em Dependências (identificadas via consulta direta ao banco OSV.dev):**
   - **Maven (3 CVEs no `logback-core:1.5.21`, puxado por `logback-classic:1.5.21` em `commons/pom.xml`):**
     - `CVE-2026-10532` (`GHSA-jhq6-gfmj-v8fx`)
     - `CVE-2026-9828` (`GHSA-p47f-322f-whfh`)
     - `CVE-2026-1225` (`GHSA-qqpg-mvqg-649v`)
   - **Cargo / Rust (`Cargo.lock` — 5 crates com advisories + 3 avisos de manutenção):**
     - `cookie 0.18.2` (`RUSTSEC-2026-0594` / `GHSA-8wcq-xq25-7fhm`)
     - `url 2.5.8` (`RUSTSEC-2026-0592` / `GHSA-hrj5-67jp-wqp9`)
     - `h2 0.3.27` (`RUSTSEC-2026-0258` / `GHSA-q83h-524g-xf6h`)
     - `glib 0.18.5` (`RUSTSEC-2024-0429` / `GHSA-wrw7-89jp-8q8g` — Linux GTK only)
     - `rand 0.7.3` (`RUSTSEC-2026-0097` / `GHSA-cq8v-f236-94qc` — Linux GTK/WebKitGTK feature tree)
     - 3 crates marcados como sem manutenção (sem CVE): `chrono 0.4.45` (`RUSTSEC-2026-0543`), `fxhash 0.2.1` (`RUSTSEC-2025-0057`), `proc-macro-error 1.0.4` (`RUSTSEC-2024-0370`).

---

## 5. Incompatibilidades e Dependências Obsoletas

1. **Dependência do JDK 25:** O projeto falha na compilação quando executado com o `JAVA_HOME` padrão do Windows (JDK 21); os workflows e a documentação de build devem explicitar JDK 25.
2. **Pull Requests Dependabot incompatíveis:**
   - bumps parciais para Netty `4.2.x` criam risco de incompatibilidade binária entre `netty-*` caso não estejam alinhados;
   - bump major de `jaxb-impl` (`2.3.9` -> `4.0.9`) quebra imports `javax.xml.bind` usados no projeto sem migração completa para `jakarta.xml.bind` v4;
   - PR `#1` aponta para executáveis e estrutura antiga de agosto/2026.
3. **Remoção dos workflows/checks de segurança e pipelines incompatíveis (Fase 6 — Impacto documentado):**
   - A exclusão de `.github/workflows/security-scan.yml` remove as execuções automáticas de **Gitleaks** e **CodeQL** no GitHub Actions. Como mitigação compensatória obrigatória, a higienização pré-publicação realiza varredura integral de segredos em working tree e histórico antes da criação do branch órfão, mantendo `.github/SECURITY.md` e `SECURITY.md` com política clara de divulgação responsável.
4. **Remoção de `ci-dotnet.yml` e `ci-rust.yml`:** Com a exclusão da solução C# pelo proprietário e a inclusão de `Ferramentas e Documentos/Ferramentas Python e PowerShell/` no `.gitignore` (Fase 7), esses workflows apontariam para diretórios inexistentes no checkout Git e falhariam no CI. `ci-backend.yml`, `commitlint.yml` e `release.yml` permanecem ativos e alinhados aos artefatos `*-LostAcademyGroup.jar` e ao escopo **GameForge (GSID 1)**.
5. **Ajuste de `.gitignore` para `database.properties`:** o `.gitignore` anterior ignorava `**/database.properties`, o que impediria a presença dos arquivos de configuração de exemplo local (`127.0.0.1:3306`, `LostAcademyGroup`) em um clone limpo; a regra será ajustada para versionar os exemplos sanitizados enquanto mantém proteção contra `.env` e arquivos `.local.properties`.

---

## 6. Arquivos que Precisam de Correção (Mapa Resumido)

- **Governança & Documentação:** `README.md`, `CONTEXT.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/{SUPPORT,SECURITY,CODE_OF_CONDUCT,CODEOWNERS,pull_request_template}.md`, `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.yml`, `Ferramentas e Documentos/Patch final - Client 5.0/README.md` (novo), `Ferramentas e Documentos/Códigos bin64/README.md`, `Ferramentas e Documentos/Códigos bin64/Código Fonte - Version.dll/{README.md,build.bat,tests/README_MultiServer.md}`, `Ferramentas e Documentos/Códigos bin64/Código Fonte - Game.dll/{CONTEXT.md,README.md,ROADMAP.md,Build64.bat,audit_*.py}`, demais `audit_*.py` / `BuildCrySystem64.bat` em `Códigos bin64/`, `Ferramentas e Documentos/Geo and Nav Builder - Official Client/README.md`, `Ferramentas e Documentos/Auditorias e Relatórios/relatorio_diagnostico_roteamento_multi_gameserver.md`.
- **Git & CI/CD:** `.gitignore`, `.github/dependabot.yml`, `.github/workflows/{ci-backend,commitlint,release}.yml`, remoção de `.github/workflows/{security-scan,ci-dotnet,ci-rust}.yml`.
- **Código Java & POMs:** `Código Fonte - Emulador/pom.xml`, POMs e `assembly.xml` de `commons`, `login-server`, `chat-server`, `game-server-gameforge`, `game-server-remake`, `game-server-battleroyale`; arquivos Java com menções `BrService`/`BrSocket`, token legado, strings `Beyond Aion` em serviços de recompensa e os testes/dados divergentes (`SkillStaticDataAuditTest.java`, `ItemUpdateTypeTest.java`, `ClassicItemSystemsTest.java`, `data/static_data`).
- **Configurações & Banco:** `database.properties`, `network.properties`, `custom.properties` (em `Código Fonte - Emulador/*` e `Emulador - Produto Final/*`), `Emulador - Produto Final/Config/config.json`, `Emulador - Produto Final/LoginServer/sql/aion_ls.sql`.
- **Launcher Rust (build local para `Emulador - Produto Final`):** `src/config.rs`, `src/supervisor.rs`, `src/db_manager.rs`, `Cargo.toml` / `Cargo.lock` e recompilação de `Aion Classic - EMULADOR.exe`.

---

## 7. Plano de Execução

1. **Fase 2 — Remoção completa de referências à `BrService.dll`:** limpar comentários, logs `[BrSocket]`, strings de autenticação WebSocket e avisos em Java, `.properties` e Markdown, preservando os recursos de telemetria/combo desacoplados ou desabilitados por padrão sem restaurar a DLL.
2. **Fase 3 — Higienização de credenciais, IPs e caminhos:** padronizar banco local (`127.0.0.1:3306`, usuário `LostAcademyGroup`, senha `LostAcademyGroup`), senhas internas/tokens locais de exemplo e caminhos relativos/portáveis em scripts e docs.
3. **Fases 4 e 5 — Documentação principal e governança:** reestruturar `README.md` (status PvE/PvP/Bard, foco exclusivo em GameForge GSID 1, política estrita de PR, seção Aion Remake + créditos Beyond Aion) e alinhar arquivos de contribuição, templates de issue/PR e suporte.
4. **Fase 6 — Reestruturação `.github/`:** remover `security-scan.yml` e workflows obsoletos, ajustar CI backend e documentar impactos.
5. **Fases 7 e 8 — `.gitignore`, limpeza do índice e Patch 5.0:** ignorar `desktop.ini`, `Client e Coletas/`, `Ferramentas Python e PowerShell/` e artefatos `.obj`/temporários, destracking no Git sem apagar nada do proprietário, e criar `Ferramentas e Documentos/Patch final - Client 5.0/README.md`.
6. **Fases 9, 10 e 11 — Maven, Configurações Padrão e Bibliotecas:** configurar saída `*-LostAcademyGroup.jar`, isolar BattleRoyale em perfil opcional, ativar apenas `GameForge (GSID 1)` por padrão, recompilar o launcher Rust, limpar `libs/` e alinhar dependências.
7. **Fases 12, 13 e 14 — PRs, Vulnerabilidades e Heranças 4.8:** auditar todos os 24 PRs, corrigir `logback-classic` (para versão sem os 3 CVEs) e dependências Rust, e gerar `Ferramentas e Documentos/docs/AUDITORIA_PULL_REQUESTS.md`, `Ferramentas e Documentos/docs/AUDITORIA_VULNERABILIDADES.md` e `Ferramentas e Documentos/docs/AUDITORIA_HERANCAS_RETAIL_4.8.md`.
8. **Fases 16 e 17 — Sincronização do Produto Final, Compilação e Testes:** corrigir os testes falhando sem relaxar asserções, compilar tudo em modo limpo com JDK 25, atualizar `Emulador - Produto Final`, testar execução/serviços disponíveis e gerar `Ferramentas e Documentos/docs/RELATORIO_FINAL_VALIDACAO.md`.
9. **Fases 15, 18, 19 e 20 — Backup Externo, Histórico Limpo e Gate de Publicação:** realizar backup completo e `.bundle` privado fora do repositório, preparar branch órfão limpo com validação integral do checklist da Fase 18 e **aguardar confirmação explícita do proprietário** antes de executar qualquer alteração destrutiva no repositório remoto (`push --force`).

---

## 8. Critérios de Aprovação

- Zero ocorrências de `brservice.dll` / `BrService` no working tree e no futuro branch limpo.
- Zero credenciais reais, tokens de produção, IPs privados de infraestrutura ou caminhos locais de máquina nos arquivos versionados.
- `README.md`, políticas de PR (GSID 1 exclusivo), governança e documentação do Patch 5.0 100% conformes.
- Build Maven limpo (`mvn clean package` com JDK 25) gerando `commons-LostAcademyGroup.jar`, `login-server-LostAcademyGroup.jar`, `chat-server-LostAcademyGroup.jar` e `game-server-LostAcademyGroup.jar`, e compilação validada de todos os perfis/módulos.
- Zero falhas de testes automatizados (todas as execuções registradas após a última edição).
- Por padrão, somente **GameForge (GSID 1)** habilitado; **Remake** e **BattleRoyale** desabilitados em `config.json` e no executável `Aion Classic - EMULADOR.exe`.
- Vulnerabilidades reportadas tratadas/documentadas em `Ferramentas e Documentos/docs/AUDITORIA_VULNERABILIDADES.md`.
- Backup privado + `git bundle` preservados externamente e checklist pré-publicação 100% verificado antes de solicitar aprovação final para rewrite do histórico remoto.
