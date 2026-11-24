# Auditoria de Segurança e Vulnerabilidades — Aion Classic 5.0 (Lost Academy Group)

**Data da Auditoria:** 24/11/2026  
**Escopo:** Dependências Maven do emulador Java (`Código Fonte - Emulador`), bibliotecas distribuídas em `Emulador - Produto Final/*/libs/` e árvore Cargo do supervisor Rust (`Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador/Cargo.lock`).  
**Metodologia de Verificação:**  
- A interface web privada do GitHub (`Security > Dependabot alerts`) retornou HTTP 404 na sessão sem autenticação; portanto, a auditoria combinou a análise direta de todas as 24 branches/PRs (`origin/pr/1` a `origin/pr/24`) com consultas diretas em lote à API oficial **OSV.dev** sobre o grafo completo de dependências resolvidas pelo Maven (`mvn dependency:tree`) e sobre os 424 pacotes do `Cargo.lock`.

---

## 1. Resumo Executivo Pós-Correções

| Ecossistema | Pacotes Analisados | Vulnerabilidades Encontradas (Baseline) | Corrigidas | Remanescentes no Alvo | Status |
|---|---:|---:|---:|---:|---|
| **Java / Apache Maven (`Código Fonte - Emulador`)** | Grafo completo dos 4 módulos padrão + perfis opcionais | **3 CVEs críticos/altos** em `ch.qos.logback:logback-core:1.5.21` | **3** (`logback-classic` → `1.5.38`) | **0** | **100% limpo no scan OSV** |
| **Java (`Emulador - Produto Final/*/libs/`)** | Bibliotecas empacotadas em runtime | Mesmos JARs legados (`logback-*-1.5.21.jar`, `slf4j-api-2.0.16.jar`, `fastjson2-2.0.60.jar`, `mysql-connector-j-9.5.0.jar`, `quartz-2.5.1.jar`, `commons-lang3-3.20.0.jar`) + JAR duplicado em `GameServer-BattleRoyale` | **Sincronizadas com build 5.0.0** | **0** | **Alinhado após rebuild** |
| **Rust / Cargo (`Cargo.lock` — no `.gitignore`)** | 424 pacotes no lockfile | **2 advisories corrigíveis** (`cookie`, `url`) + **3 advisories acoplados a major bumps** (`h2`, `glib`, `rand`) + **3 avisos de manutenção** (`chrono`, `fxhash`, `proc-macro-error`) | **2** (`cookie 0.18.3`, `url 2.5.9`) | **1 em Windows** (`h2 0.3.27` loopback); **`glib`/`rand`/`fxhash`/`proc-macro-error` só em alvos Linux** | **Documentado e mitigado** |

---

## 2. Vulnerabilidades Java (Maven) Corrigidas

| Pacote | Versão Anterior | Versão Aplicada | Identificadores CVE / GHSA | Impacto Original | Ação Realizada e Validação |
|---|---|---|---|---|---|
| `ch.qos.logback:logback-classic` (transitivo `logback-core`) | `1.5.21` | **`1.5.38`** | `CVE-2026-10532` (`GHSA-jhq6-gfmj-v8fx`), `CVE-2026-9828` (`GHSA-p47f-322f-whfh`), `CVE-2026-1225` (`GHSA-qqpg-mvqg-649v`) | Desserialização não confiável e injeção de objetos/instanciação de classes via `logback-core` | Atualizado em `Código Fonte - Emulador/commons/pom.xml`; verificado via `mvn dependency:tree` e scan OSV posterior com **0 vulnerabilidades**. |
| `org.slf4j:slf4j-api` | `2.0.16` (GameServers) / `2.0.17` (Login/Chat) | **`2.0.17`** (unificado) | Consistência de classpath | Divergência de versão entre `commons`, `login-server`, `chat-server` e `game-server-*` | Gerenciado centralmente via `<dependencyManagement>` em `Código Fonte - Emulador/pom.xml`. |
| `com.mysql:mysql-connector-j` | `9.5.0` | **`26.10.0`** | — (PR `#10`) | Driver desatualizado | Atualizado em `commons/pom.xml` e validado com `mvn clean package`. |
| `com.alibaba.fastjson2:fastjson2` | `2.0.60` | **`2.0.66`** | — (PR `#23`) | Biblioteca JSON desatualizada | Atualizado em `commons/pom.xml`. |
| `org.quartz-scheduler:quartz` | `2.5.1` | **`2.5.2`** | — (PR `#22`) | Agendador desatualizado | Alinhado nos três módulos `game-server-*`. |
| `org.apache.commons:commons-lang3` | `3.20.0` | **`3.22.0`** | — (PR `#19`) | Utilitários Apache desatualizados | Alinhado nos três módulos `game-server-*`. |

### Itens Maven Avaliados e Mantidos Intencionalmente
- **`io.netty:netty-*` (`4.1.138.Final`):** Os PRs `#15`, `#17` e `#20` tentavam atualizar apenas 3 dos 6 artefatos Netty do `chat-server` para `4.2.20.Final`, causando incompatibilidade binária entre submódulos `4.1` e `4.2`. O scan OSV confirmou **0 CVEs** em `4.1.138.Final`.
- **`com.sun.xml.bind:jaxb-impl` (`2.3.9`):** O PR `#24` propunha migrar para `4.0.9`, o que altera o pacote base de `javax.xml.bind.*` para `jakarta.xml.bind.*` em todo o backend e quebra a compilação sem refatoração ampla. Mantido `2.3.9` em conjunto com `jakarta.xml.bind-api:2.3.3` (**0 CVEs** no scan OSV).

---

## 3. Auditoria do Supervisor Rust (`Aion Classic - EMULADOR.exe`)

> **Observação estrutural:** O código-fonte do supervisor Rust reside em `Ferramentas e Documentos/Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador/`, diretório excluído do repositório Open Source público pelo `.gitignore`. Mesmo assim, o lockfile foi atualizado, auditado e o executável compilado em release (`SHA-256: F5487B121FB74558ED6014157D1E7164A81995CD179B1D2D118EC83E17700501`) antes da distribuição final.

### 3.1 Advisories Corrigidos via `cargo update`
| Crate | Anterior | Atualizada | Advisory / GHSA | Descrição |
|---|---:|---:|---|---|
| `cookie` | `0.18.2` | **`0.18.3`** | `RUSTSEC-2026-0594` (`GHSA-8wcq-xq25-7fhm`) | Repetição potencial de nonces privados após `fork()` |
| `url` | `2.5.8` | **`2.5.9`** | `RUSTSEC-2026-0592` (`GHSA-hrj5-67jp-wqp9`) | Stack overflow em `Url::origin()` para URLs `blob:` aninhadas |

### 3.2 Advisories Remanescentes no `Cargo.lock` e Análise de Alcance Real no Alvo Windows (`x86_64-pc-windows-msvc`)

Verificado explicitamente via `cargo tree --target x86_64-pc-windows-msvc` e `cargo tree --target all`:

| Crate / Versão | Advisory / Severidade | Cadeia em `cargo tree` | Compilado no `.exe` Windows? | Mitigação / Análise |
|---|---|---|---|---|
| `h2 0.3.27` | `RUSTSEC-2026-0258` (`GHSA-q83h-524g-xf6h`) — fix `0.4.16` | `aion-classic-emu -> warp 0.3.7 -> hyper 0.14.32 -> h2 0.3.27` | **Sim** | O servidor HTTP embutido (`warp`) escuta exclusivamente em loopback local `127.0.0.1` (`src/main.rs:612`) para interface administrativa local, sem exposição pública à rede. A correção exige migração breaking de `warp 0.3` para `warp 0.4` / `hyper 1.0` (PR `#6`, adiado). |
| `glib 0.18.5` | `RUSTSEC-2024-0429` (`GHSA-wrw7-89jp-8q8g`, Moderada) — fix `0.20.0` | `wry 0.47.2 / tao 0.31.1 -> gtk/webkit2gtk/atk/gdk/gio/soup3 -> glib 0.18.5` | **Não** (`cargo tree --target x86_64-pc-windows-msvc` vazio) | Dependência exclusiva de backend Linux GTK/WebKitGTK registrada no `Cargo.lock` multiplataforma. Ausente do binário Windows PE compilado. Atualização definitiva exige migração major `wry 0.57` / `tao 0.37` (PRs `#5` e `#7`). |
| `rand 0.7.3` | `RUSTSEC-2026-0097` (`GHSA-cq8v-f236-94qc`, Baixa) — fix `0.8.6` | `wry 0.47.2 -> kuchikiki 0.8.2 -> selectors 0.22.0 / phf_macros -> phf_generator 0.8.0 -> rand 0.7.3` | **Não** (`cargo tree --target x86_64-pc-windows-msvc` vazio) | Só aparece na árvore Linux (`kuchikiki` do `wry` sem target Windows) e não utiliza logger customizado com `rand::rng()`. |
| `fxhash 0.2.1` | `RUSTSEC-2025-0057` (Sem manutenção; sem CVE) | `wry 0.47.2 -> kuchikiki 0.8.2 -> selectors 0.22.0 -> fxhash 0.2.1` | **Não** | Somente presente fora do target Windows. |
| `proc-macro-error 1.0.4` | `RUSTSEC-2024-0370` (Sem manutenção; sem CVE) | `glib-macros 0.18.5 / gtk3-macros 0.18.2 -> proc-macro-error 1.0.4` | **Não** | Macro de compilação exclusiva de `glib`/`gtk3` no Linux. |
| `chrono 0.4.45` | `RUSTSEC-2026-0543` (Aviso de manutenção; sem CVE) | `aion-classic-emu -> chrono 0.4.45` | Sim (API utilitária de data/hora) | Sem vulnerabilidade explorável reportada; apenas aviso de status de manutenção no advisory DB. |

---

## 4. Limpeza de Logs e Configurações Sensíveis Associadas

- Todos os arquivos `.properties`, `.json`, `.sql` e código-fonte Java/Rust foram auditados e higienizados para credenciais locais de exemplo (`127.0.0.1:3306`, usuário `LostAcademyGroup`, senha `LostAcademyGroup`, token inter-servidor `LostAcademyGroup`).
- Logs de execuções anteriores em `Emulador - Produto Final/*/log/` e `Emulador - Produto Final/logs/` (que continham endereços IP internos e caminhos locais de host de execuções antigas) foram removidos na preparação do pacote limpo.
