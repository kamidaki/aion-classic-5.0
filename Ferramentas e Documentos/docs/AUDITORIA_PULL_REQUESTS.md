# Auditoria de Pull Requests — Aion Classic 5.0 (Lost Academy Group)

**Data da Auditoria:** 24/11/2026  
**Escopo:** Avaliação integral das 24 referências remotas de Pull Request (`refs/remotes/origin/pr/1` a `origin/pr/24`) contra a baseline Open Source do repositório `https://github.com/kamidaki/aion-classic-5.0`.  
**Referência Única GameForge:** GameServer 1 (`game-server-gameforge` — GSID 1).

---

## 1. Resumo Executivo

| Categoria | Quantidade | PRs Envolvidos | Decisão |
|---|---:|---|---|
| Já incorporados ao `HEAD` | 3 | `#2`, `#3`, `#4` | Mantidos no código-fonte |
| Dependências/CI compatíveis aplicados | 10 | `#10`, `#11`, `#13`, `#14`, `#16`, `#18`, `#19`, `#21`, `#22`, `#23` | Aplicados e alinhados nos POMs/workflows |
| Obsoletos / workflows ou binários removidos | 2 | `#1`, `#12` | Descartados / rejeitados |
| Breaking changes Java parciais ou incompatíveis | 4 | `#15`, `#17`, `#20`, `#24` | Rejeitados na árvore Open Source (documentados abaixo) |
| Breaking changes major Rust (supervisor no `.gitignore`) | 5 | `#5`, `#6`, `#7`, `#8`, `#9` | Rejeitados no merge cego; CVEs transitivos mitigados localmente com `cargo update` |
| **Total auditado** | **24** | **`#1`–`#24`** | **100% inspecionados** |

---

## 2. Tabela Completa dos 24 Pull Requests

| PR | Commit Base | Título / Descrição | Escopo Afetado | Status no Repositório | Decisão e Justificativa Técnica |
|---:|---|---|---|---|---|
| **#1** | `378644be5` | `chore(deploy): auto-start.exe e chat-server.exe recompilados do codigo pos-merge` | `Produto Final/auto-start.exe`, `chat-server.exe` | Não incorporado | **Rejeitado (obsoleto):** binários de layout legado já removido; substituído por `Aion Classic - EMULADOR.exe` e launcher Java. |
| **#2** | `4cb78936c` | `feat(flyloot,nativepath): integrar fly-loot sem montarias e correcao cryengine com updates oficiais 5.0` | `game-server`, spawns, AI, `NativePathService` | **Já no `HEAD`** | **Mantido:** já integrado à base atual e migrado para `game-server-gameforge`. |
| **#3** | `49123c315` | `fix(client,version): corrigir crashes no boot e adicionar otimizacao CryPak PathRedirect` | `version.dll` / `PathRedirect` | **Já no `HEAD`** | **Mantido:** funcionalidade base já presente na árvore atual e preservada nas edições do proprietário. |
| **#4** | `12405a68f` | `fix(version,client): versao de producao sem vulkan e sem mousefix, com argumentos oficiais e suporte a BRA` | `version.cpp` / `version.dll` | **Já no `HEAD`** | **Mantido:** base de suporte oficial 5.0 e região BRA preservada. |
| **#5** | `9ca281cfa` | `build(deps): bump wry` (`0.47.2` → `0.57.1`) | Supervisor Rust (`Cargo.toml` / `Cargo.lock`) | Não incorporado | **Adiado / não aplicado:** diretório do supervisor Rust está no `.gitignore` público; `wry 0.57` exige migração de API incompatível na inicialização WebView2. `cookie`/`url` transitivos atualizados sem quebrar API. |
| **#6** | `a2b40c11c` | `build(deps): bump warp` (`0.3.7` → `0.4.3`) | Supervisor Rust (`Cargo.toml` / `Cargo.lock`) | Não incorporado | **Adiado / não aplicado:** `warp 0.4` quebra rotas baseadas em `hyper 0.14` no `src/main.rs`; diretório ignorado na árvore pública. |
| **#7** | `6624c4f9a` | `build(deps): bump tao` (`0.31.1` → `0.37.2`) | Supervisor Rust (`Cargo.toml` / `Cargo.lock`) | Não incorporado | **Adiado / não aplicado:** atualização major acoplada ao ciclo `wry 0.57`; quebraria integração atual de janela e bandeja. |
| **#8** | `442cdd5f3` | `build(deps): bump parking_lot` (`0.12.5` → `0.13.0`) | Supervisor Rust (`Cargo.toml` / `Cargo.lock`) | Não incorporado | **Não aplicado:** diretório Rust excluído pelo `.gitignore`; nenhuma vulnerabilidade em `0.12.5`. |
| **#9** | `4b279f488` | `build(deps): bump sysinfo` (`0.30.13` → `0.40.1`) | Supervisor Rust (`Cargo.toml` / `Cargo.lock`) | Não incorporado | **Adiado / não aplicado:** `sysinfo 0.40` remove traits/APIs usadas em `src/supervisor.rs`; atualização futura isolada. |
| **#10** | `96adc3308` | `build(deps): bump com.mysql:mysql-connector-j` (`9.5.0` → `26.10.0`) | `Código Fonte - Emulador/commons/pom.xml` | **Aplicado** | **Aceito:** atualização direta aplicada em `commons/pom.xml` com compilação e resolução Maven validadas. |
| **#11** | `e52708f15` | `build(deps): bump actions/checkout from 4 to 7` | `.github/workflows/*.yml` | **Aplicado** | **Aceito:** aplicado aos workflows ativos `ci-backend.yml` e `release.yml`. |
| **#12** | `7749bd454` | `build(deps): bump actions/setup-dotnet from 4 to 6` | `.github/workflows/ci-dotnet.yml` | Descartado | **Rejeitado (obsoleto):** `ci-dotnet.yml` compilava `AcademyNoLag.sln`, já excluído pelo proprietário, tendo sido removido da árvore. |
| **#13** | `7e5168a29` | `build(deps-dev): bump org.apache.maven.plugins:maven-jar-plugin` (`3.5.0` → `3.5.1`) | `Código Fonte - Emulador/pom.xml` | **Aplicado** | **Aceito:** aplicado no POM pai em `pluginManagement`. |
| **#14** | `3ffba3dc9` | `build(deps): bump softprops/action-gh-release from 2 to 3` | `.github/workflows/release.yml` | **Aplicado** | **Aceito:** aplicado na etapa de publicação de releases. |
| **#15** | `f0942c8f1` | `build(deps): bump io.netty:netty-transport` (`4.1.138.Final` → `4.2.20.Final`) | `Código Fonte - Emulador/chat-server/pom.xml` | Não aplicado | **Rejeitado (mantido `4.1.138.Final`):** o Dependabot propôs atualizar `netty-transport`, `netty-common` (#17) e `netty-handler` (#20) separadamente para `4.2.20.Final`, deixando `netty-buffer`, `netty-codec` e `netty-resolver` em `4.1.138.Final` — combinação binariamente incompatível em runtime. A linha `4.1.138.Final` possui **0 CVEs** no scan OSV atual. |
| **#16** | `a8c7e95ca` | `build(deps): bump actions/setup-java from 4 to 5` | `.github/workflows/ci-backend.yml`, `release.yml` | **Aplicado** | **Aceito:** aplicado aos workflows Java ativos com JDK 25 (`temurin`). |
| **#17** | `4a4424b6f` | `build(deps): bump io.netty:netty-common` (`4.1.138.Final` → `4.2.20.Final`) | `Código Fonte - Emulador/chat-server/pom.xml` | Não aplicado | **Rejeitado:** mesmo desalinhamento parcial Netty 4.1/4.2 detalhado no PR `#15`. |
| **#18** | `cc0fb792b` | `build(deps): bump amannn/action-semantic-pull-request from 5 to 6` | `.github/workflows/commitlint.yml` | **Aplicado** | **Aceito:** atualizado na validação semântica de PRs. |
| **#19** | `74d2f2056` | `build(deps): bump org.apache.commons:commons-lang3` (`3.20.0` → `3.22.0`) | `game-server-{gameforge,remake,battleroyale}/pom.xml` | **Aplicado** | **Aceito:** alinhado em todos os GameServers para manter o reactor Maven uniforme sem versões conflitantes em `libs/`. |
| **#20** | `d9f9c3dcb` | `build(deps): bump io.netty:netty-handler` (`4.1.138.Final` → `4.2.20.Final`) | `Código Fonte - Emulador/chat-server/pom.xml` | Não aplicado | **Rejeitado:** mesmo desalinhamento parcial Netty 4.1/4.2 detalhado no PR `#15`. |
| **#21** | `dc123b7b0` | `build(deps-dev): bump io.github.git-commit-id:git-commit-id-maven-plugin` (`9.0.2` → `10.0.1`) | `Código Fonte - Emulador/pom.xml` | **Aplicado** | **Aceito:** plugin atualizado sem conflitos no build com JDK 25. |
| **#22** | `4c48b2c81` | `build(deps): bump org.quartz-scheduler:quartz` (`2.5.1` → `2.5.2`) | `game-server-{gameforge,remake,battleroyale}/pom.xml` | **Aplicado** | **Aceito:** patch compatível alinhado nos GameServers. |
| **#23** | `f6a5d6447` | `build(deps): bump com.alibaba.fastjson2:fastjson2` (`2.0.60` → `2.0.66`) | `Código Fonte - Emulador/commons/pom.xml` | **Aplicado** | **Aceito:** patch compatível aplicado e validado em `commons`. |
| **#24** | `e80e88d49` | `build(deps): bump com.sun.xml.bind:jaxb-impl` (`2.3.9` → `4.0.9`) | `game-server-{gameforge,remake,battleroyale}/pom.xml` | Não aplicado | **Rejeitado (mantido `2.3.9`):** `jaxb-impl 4.x` exige migração completa do namespace `javax.xml.bind.*` para `jakarta.xml.bind.*` nos dataholders/templates JAXB; mantido em `2.3.9` com `jakarta.xml.bind-api:2.3.3` para preservar 100% de compatibilidade. |

---

## 3. Atualizações Adicionais Fora dos PRs Abertos

Além dos 24 PRs analisados, a auditoria de vulnerabilidades (ver [AUDITORIA_VULNERABILIDADES.md](AUDITORIA_VULNERABILIDADES.md)) identificou e aplicou:
1. **`ch.qos.logback:logback-classic` (`1.5.21` → `1.5.38`)** em `Código Fonte - Emulador/commons/pom.xml` (eliminando 3 CVEs do `logback-core`).
2. **`org.slf4j:slf4j-api` (`2.0.16` → `2.0.17`)** via `dependencyManagement` em `Código Fonte - Emulador/pom.xml`, unificando os artefatos `libs/` de GameServer, ChatServer e LoginServer.
3. **`cargo update` no supervisor Rust** (`cookie` `0.18.2 → 0.18.3`, `url` `2.5.8 → 2.5.9`), mitigando as 2 únicas vulnerabilidades Rust corrigíveis sem quebra de API major.
