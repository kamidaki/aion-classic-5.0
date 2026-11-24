# Relatório Final de Validação — Aion Classic 5.0 (Lost Academy Group)

**Data de Validação:** 24/11/2026  
**Escopo:** Verificação técnica completa de compilação, testes automatizados, empacotamento em `Emulador - Produto Final`, integridade binária, higienização de segredos e preparação pré-publicação Open Source.

---

## 1. Resumo de Compilação e Testes (Pós-Edição Final)

Todas as builds Java foram executadas com **JDK `25.0.2`** (`C:\Program Files\Java\jdk-25.0.2`, alinhado ao JDK embarcado em `Emulador - Produto Final/Config/java-deployment` — build `25.0.2+10-LTS-69`) e **Apache Maven `3.9.9`**.

### 1.1 Perfil Padrão (`mvn clean package "-Dmaven.javadoc.skip=true"`)

| Módulo | Versão / Artefato | Compilação | Testes Executados | Falhas / Erros | Skips (Justificados) | Resultado |
|---|---|---|---:|---:|---:|---|
| **`aion-server` (POM Pai)** | `5.0.0` | OK | — | — | — | **SUCCESS** |
| **`commons`** | `commons-LostAcademyGroup.jar` | OK (85 + 2 classes) | **1** (`ScriptManagerTest`) | **0 / 0** | **0** | **SUCCESS** |
| **`chat-server`** | `chat-server-LostAcademyGroup.jar` + `chat-server.zip` | OK | **0** (sem testes no módulo) | **0 / 0** | **0** | **SUCCESS** |
| **`game-server-gameforge` (GSID 1)** | `game-server-LostAcademyGroup.jar` + `game-server-gameforge.zip` | OK | **195** total (**191** executados) | **0 / 0** | **4** (ver §1.3) | **SUCCESS** |
| **`login-server`** | `login-server-LostAcademyGroup.jar` + `login-server.zip` | OK (88 classes) | **0** (sem testes no módulo) | **0 / 0** | **0** | **SUCCESS** |

**Tempo total do reactor padrão:** `01:11 min` — **Exit Code `0`**.

### 1.2 Módulos Opcionais e Ferramentas Auxiliares
- **GameServers secundários (perfil `-Pall-servers`, `mvn package -Pall-servers -pl game-server-remake,game-server-battleroyale -am -U -DskipTests=true`):**
  - `game-server-remake-LostAcademyGroup.jar` e `game-server-remake.zip`: **SUCCESS**.
  - `game-server-battleroyale-LostAcademyGroup.jar` e `game-server-battleroyale.zip`: **SUCCESS**.
  - Nota: mantidos fora dos módulos padrão do POM pai e **desabilitados por padrão** no launcher (`Config/config.json` e `src/config.rs`), em cumprimento às regras de escopo exclusivo GameForge GSID 1.
- **Geo and Nav Builder (`Ferramentas e Documentos/Geo and Nav Builder - Official Client`):**
  - `mvn clean package`: compilação de 43 fontes em **SUCCESS** (`target/geobuilder.jar`, `0` testes no módulo).
- **Supervisor Rust (`Aion Classic - EMULADOR.exe`):**
  - `cargo build --release` após `cargo update` e higienização de `src/config.rs`, `src/db_manager.rs` e `src/ui.rs`: **Finished (`exit code 0`)**.

### 1.3 Correções e Detalhamento dos 4 Skips em `game-server-gameforge`
- **3 falhas da baseline inicial corrigidas:**
  1. `SkillStaticDataAuditTest.sourceAndProductSkillTemplatesAreByteIdentical`: ajustado o caminho alvo de `Emulador - Produto Final/GameServer/...` para `Emulador - Produto Final/GameServer-GameForge/...` e sincronizado `skill_templates.xml` em bytes exatos (`Files.mismatch == -1`).
  2. `ItemUpdateTypeTest.reasonIsTheCapturedOneOrZero`: registrado `DEC_KINAH_RANKING_BUFF` (`0x10E`, definido em `ItemPacketService.java:57`) no mapa `CAPTURED`.
  3. `ClassicItemSystemsTest.everyGameplayMaskUsesOnlyFlagsBackedByClassicClientData`: atualizado o total esperado de `79664` para `79671` refletindo os 7 templates Songweaver presentes no catálogo (`100599901`, `110199549`, `111199417`, `112199376`, `113199435`, `114199465`, `125101451`), mantendo integralmente a validação de máscara em todos os 79.671 itens.
  4. Adicionalmente, `MorosPassiveSkillTest.productDataMatchesTheSource` foi corrigido de `GameServer` para `GameServer-GameForge`, passando a executar e aprovar ativamente (reduzindo os skips de 5 para 4).
- **4 skips remanescentes (por `Assumptions.assumeTrue`, sem relaxamento de asserções):**
  - `MorosPassiveSkillTest` (1 skip): depende de `client_skills.xml` extraído em texto XML na pasta local `Client e Coletas` (ausente em texto plano neste checkout).
  - `SkillStaticDataAuditTest` (3 skips): dependem dos XMLs de texto do cliente (`client_skills.xml` / `client_strings_skill.xml`) ausentes em texto plano.

---

## 2. Checksums SHA-256 dos Artefatos Finais Entregues

| Artefato | SHA-256 |
|---|---|
| `Emulador - Produto Final/ChatServer/libs/commons-LostAcademyGroup.jar` | `BDE979E02E3EC1210848FF5A80133082B1D971B8354B3915E691B6495927B708` |
| `Emulador - Produto Final/ChatServer/libs/chat-server-LostAcademyGroup.jar` | `7C5BF68167F98BCEA0BD3B61FA907BE51B7AAC7A6416FEF3AF95DCD602FEB7DE` |
| `Emulador - Produto Final/LoginServer/libs/login-server-LostAcademyGroup.jar` | `B93A4FAA0A5620AC3A2673742B95D81E211C63B0B88B56651C83525A54977980` |
| `Emulador - Produto Final/GameServer-GameForge/libs/game-server-LostAcademyGroup.jar` | `1B201D761D85C230D13542A267E939118FB7DE97783A481FD715227E94B6FF3F` |
| `Emulador - Produto Final/GameServer-Remake/libs/game-server-remake-LostAcademyGroup.jar` | `C30A9936C1871194D0E3B17A037042A50623711F86F1883170DA40D239D0BA03` |
| `Emulador - Produto Final/GameServer-BattleRoyale/libs/game-server-battleroyale-LostAcademyGroup.jar` | `339F92315DDB5DE93D022613F4479CA5E06B9E8831E05C9FC5D84772BD722707` |
| `Emulador - Produto Final/Aion Classic - EMULADOR.exe` | `F5487B121FB74558ED6014157D1E7164A81995CD179B1D2D118EC83E17700501` |
| `Ferramentas e Documentos/Patch final - Client 5.0/bin64/version.dll` | `1325A5FAFCCCD1E470B6B18C0CF18DFD70B310464B121EA403192CE757834DA2` |
| `Ferramentas e Documentos/Geo and Nav Builder - Official Client/target/geobuilder.jar` | `F8B43AB6EE3056AF6B5001F8119842922D63D1A8236C60C17F0365A5ABE9FEBE` |

---

## 3. Verificação de Higienização, Dependências e Escopo

1. **Remoção de `BrService.dll` / `[BrSocket]`:**
   - **0** referências encontradas via `git grep` em código Java, `.properties`, documentação operacional e binários inspecionados (`version.dll` x86/x64 via REA `inspect_pe_imports`/`inspect_native_exports` e `Aion Classic - EMULADOR.exe` via análise de strings ASCII/UTF-16).
2. **Higienização de Segredos, IPs Privados e Caminhos Locais:**
   - **0** ocorrências de IPs internos (`192.168.3.*`), senhas reais, usuários privados ou emails internos nos arquivos rastreados e na pasta `Ferramentas e Documentos/docs/`.
   - Todos os 10 `database.properties`, 8 `network.properties`, `Emulador - Produto Final/Config/config.json` e `Emulador - Produto Final/LoginServer/sql/aion_ls.sql` padronizados com credenciais de exemplo local: **`127.0.0.1:3306`**, usuário **`LostAcademyGroup`**, senha **`LostAcademyGroup`**.
   - Todos os logs antigos em `Emulador - Produto Final/*/log/` e `Emulador - Produto Final/logs/` e arquivos `.bak` foram limpos.
3. **Configuração Padrão de Servidores:**
   - **GameForge (GSID 1):** habilitado (`enabled: true`).
   - **Remake (GSID 2) e BattleRoyale (GSID 3):** desabilitados (`enabled: false`) em `config.json` e nos defaults compilados do launcher `Aion Classic - EMULADOR.exe`.
4. **Limpeza do Índice Git e Preservação de Trabalho do Proprietário:**
   - `Ferramentas e Documentos/Client e Coletas/`, `Ferramentas e Documentos/Ferramentas Python e PowerShell/`, `desktop.ini` e artefatos de build `Release64` (`.obj`, `.pch`, `.idb`, `.exp`, `.lib`, `.res`) devidamente ignorados no `.gitignore` e removidos do índice (`0` rastreados).
   - Todas as 419 exclusões e 3 modificações originais do proprietário (`shader_fix.cpp`, `version.cpp`, `Patch final - Client 5.0/bin64/version.dll`) permaneceram preservadas sem restauração indevida.
5. **Segurança e Execução Local em Banco:**
   - Scan OSV pós-atualização no backend Java (`logback-classic 1.5.38`, `fastjson2 2.0.66`, `mysql-connector-j 26.10.0`, `protobuf-java 4.36.1`, `quartz 2.5.2`, `commons-lang3 3.22.0`, `slf4j-api 2.0.17`): **0 vulnerabilidades**.
   - Supervisor Rust atualizado com `cargo update` (`cookie 0.18.3`, `url 2.5.9`), deixando apenas `h2 0.3.27` em loopback `127.0.0.1` no alvo Windows e 4 crates exclusivos de targets Linux sem impacto no `.exe`.
   - **Nota sobre boot ao vivo de banco de dados:** o serviço MySQL/MariaDB local não está em execução nesta máquina na etapa final (`MySQL_SLAVE` parado), e as credenciais atuais configuradas (`LostAcademyGroup` / `LostAcademyGroup` em `127.0.0.1:3306`) destinam-se ao exemplo Open Source de desenvolvimento; portanto, a inicialização completa do launcher contra instância MariaDB ao vivo não foi executada após a substituição para evitar poluição de logs e alteração de serviços do host.

---

## 4. Documentação Gerada / Atualizada na Raiz e `Ferramentas e Documentos/docs/`

- Raiz: [README.md](../../README.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [SUPPORT.md](../../SUPPORT.md), [SECURITY.md](../../SECURITY.md), [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md), [CONTEXT.md](../../CONTEXT.md), [.gitignore](../../.gitignore).
- Governança GitHub: `.github/{CODEOWNERS,SUPPORT.md,SECURITY.md,CODE_OF_CONDUCT.md,pull_request_template.md,dependabot.yml}`, `.github/ISSUE_TEMPLATE/*`, `.github/workflows/{ci-backend.yml,commitlint.yml,release.yml}` (removidos `security-scan.yml`, `ci-dotnet.yml` e `ci-rust.yml`).
- Patch do Cliente: [Ferramentas e Documentos/Patch final - Client 5.0/README.md](../Patch%20final%20-%20Client%205.0/README.md).
- Relatórios de Auditoria:
  - [AUDITORIA_OPEN_SOURCE.md](AUDITORIA_OPEN_SOURCE.md)
  - [AUDITORIA_PULL_REQUESTS.md](AUDITORIA_PULL_REQUESTS.md)
  - [AUDITORIA_VULNERABILIDADES.md](AUDITORIA_VULNERABILIDADES.md)
  - [AUDITORIA_HERANCAS_RETAIL_4.8.md](AUDITORIA_HERANCAS_RETAIL_4.8.md)
  - [RELATORIO_FINAL_VALIDACAO.md](RELATORIO_FINAL_VALIDACAO.md)
