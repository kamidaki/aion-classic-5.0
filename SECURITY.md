# Política de Segurança, Firewall Geográfico e Arquitetura Autoritativa — AION CLASSIC 5.0 EMULADOR

<p align="center">
  <a href="./SECURITY.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_Brasil_(Padr%C3%A3o)-10b981?style=for-the-badge&logo=markdown&logoColor=white" alt="PT-BR Padrão" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-3b82f6?style=for-the-badge&logo=markdown&logoColor=white" alt="CONTEXT.md" /></a>
  <a href="./CONTRIBUTING.md"><img src="https://img.shields.io/badge/Contribui%C3%A7%C3%A3o-CONTRIBUTING.md-0ea5e9?style=for-the-badge&logo=github&logoColor=white" alt="CONTRIBUTING.md" /></a>
</p>

## 1. Filosofia de Segurança — Confiança Zero no Cliente

O ecossistema do **Aion Classic 5.0 — Emulador Oficial** adota uma arquitetura rigorosa de **Confiança Zero no Cliente (*Zero-Trust Client Architecture*)**. O executável de jogo (`Aion.bin`) é tratado estritamente como uma **superfície não confiável de entrada de comandos e renderização gráfica**.

Todas as validações críticas de integridade, inventário, coordenadas mundiais, alcance de habilidades, envelopes de física de voo e solo, cálculo de dano, atributos de combate, taxas de drop, transferências de itens e transações econômicas são calculadas e validadas **exclusiva e autoritativamente pelo backend Java 25 LTS** e persistidas de forma estritamente segregada nos schemas relacionais do MySQL.

---

## 2. Versões e Componentes Suportados para Auditoria de Segurança

| Componente | Tecnologia / Stack | Status de Suporte | Observações de Segurança |
| :--- | :--- | :---: | :--- |
| **Backend Java 25 (`commons`, `login-server`, `chat-server`)** | Java 25 LTS (jdk-25.0.2) / NIO / Virtual Threads | Sim | Núcleo de rede assíncrono, Handshake RSA 1024-bit + Blowfish e Firewall GeoIP. |
| **GameServer GameForge (`game-server-gameforge`)** | Java 25 LTS / DB `aionclassic_gs` (GSID 1) | Sim | Modalidade oficial 5.0 autoritativa, CryEngine Native-Path e combate fiel 1:1. |
| **GameServer Remake (`game-server-remake`)** | Java 25 LTS / DB `aionclassic_gs2` (GSID 2) | Sim | Modalidade isolada, regras de progressão e balanceamento customizado. |
| **GameServer BattleRoyale (`game-server-battleroyale`)** | Java 25 LTS / DB `aionclassic_gs3` (GSID 3) | Sim | Modalidade isolada de sobrevivência PvP e arenas dinâmicas. |
| **Supervisor Nativo e DB Studio (`Aion Classic - EMULADOR.exe`)** | Rust 1.80+ (MSVC x64) / WebView2 | Sim | Interface local vinculada estritamente em `127.0.0.1:18080` (loopback). |
| **Proxy Hook Standalone (`version.dll`)** | C/C++ (MSVC v143 x64/x86) / Detours | Sim | Conector Client-Emulador sem dependências externas e com resolução dinâmica de IPs. |
| **Otimizador de Latência (`Academy NoLag`)** | C# / .NET 9.0 SDK | Sim | Roteamento inteligente local para redução de latência e jitter. |
| **Versões legadas Java 8 / 11 / 17 / 21 ou dependências Javolution** | Legado | Não | Descontinuadas e permanentemente proibidas por riscos de segurança e concorrência. |

---

## 3. Camadas de Proteção e Controles de Segurança Implementados

### 3.1 Proteção Contra Força Bruta (Brute-Force) e Criptografia de Credenciais
* **Bloqueio Automático no LoginServer (`loginserver.server.bruteforceprotector=true`):** O `LoginServer` rastreia tentativas consecutivas de autenticação falha por endereço IP. Atingido o limite configurado (`loginserver.network.client.logintrybeforeban=5`), o IP é automaticamente bloqueado por `loginserver.network.client.bantimeforbruteforcing` minutos.
* **Handshake Criptográfico Híbrido (RSA 1024-bit + Blowfish):** O cliente recebe a chave pública RSA no pacote `SM_INIT` para criptografar as credenciais em trânsito. A comunicação subsequente é cifrada via Blowfish com semente dinâmica de 8 bytes derivada do pacote `S_KEY`.
* **Criptografia e Hashing Seguro no Banco:** Hashes de senhas são armazenados com algoritmos seguros no schema `aionclassic_ls.account_data`. Acesso a dados administrativos é segregado por níveis estritos de privilégio (0=Jogador, 1=VIP, 2=GM, 3=Admin).

### 3.2 Proteção Contra Flood TCP, DDoS e Esgotamento de Recursos no Socket NIO
* **Filtragem Pré-Alocação:** Pacotes com formato inválido, cabeçalhos corrompidos ou tamanho de enquadramento anômalo são descartados no despachante NIO antes de qualquer alocação de heap de sessão.
* **Limitação de Sessões Simultâneas por IP:** Proteção contra esgotamento de descritores de arquivo e soquetes na camada de transporte TCP (Portas `2106`, `7777`, `7778`, `7779`, `10241`).
* **Checksum Dinâmico de Pacote:** Todo frame decifrado valida a integridade do opcode contra o campo de verificação binária (`~opcode`), encerrando conexões adulteradas imediatamente.

### 3.3 Firewall Geográfico por País (`GeoIPFilterService` e `geo_firewall.properties`)
* **Tabelas Globais de Prefixos CIDR em Memória:** Carrega os blocos IPv4 e IPv6 autorizados diretamente na inicialização do servidor com busca binária de altíssima velocidade.
* **Rejeição Imediata no Socket TCP:** Conexões provenientes de regiões geográficas não autorizadas são encerradas diretamente no nível do socket TCP, consumindo zero processamento de criptografia ou processamento de pacotes.
* **Políticas Configuráveis em Tempo Real:** Suporte a listas de países autorizados (`geo.firewall.allowed_countries=BR,PT`), listas de bloqueio e liberação de IPs específicos via whitelist manual (`geo.firewall.manual_whitelist_ips`).

### 3.4 Isolamento Estrito de Bancos de Dados e Prevenção de SQL Injection
* **Isolamento de Schemas por Serviço:**
  - LoginServer: `aionclassic_ls`
  - ChatServer: `aionclassic_cs`
  - GameServer GameForge: `aionclassic_gs`
  - GameServer Remake: `aionclassic_gs2`
  - GameServer BattleRoyale: `aionclassic_gs3`
* **Zero SQL Injection:** Todas as operações de persistência e consulta utilizam estritamente `PreparedStatement` parametrizado. É expressamente proibida a concatenação manual de strings em comandos SQL.
* **Proteção de Credenciais de Banco:** Os arquivos `database.properties` contendo credenciais são protegidos pelo `.gitignore` e nunca devem ser versionados.

### 3.5 Superfície Administrativa e Supervisor Nativo em Rust
* **Bind Estrito em Loopback (`127.0.0.1:18080`):** O painel gráfico administrativo, telemetria de processos e o Database Studio operam exclusivamente em interface de loopback local, sem exposição para a rede pública.
* **Isolamento de Processos via Windows Job Objects:** O supervisor gerencia o ciclo de vida dos processos Java como um grupo estritamente controlado, garantindo o encerramento gracioso e a persistência de integridade sem deixar processos órfãos.
* **Higienização Automática de Cache WebView2:** O diretório de runtime em `%LOCALAPPDATA%\AionClassicEmulador\WebView2` é higienizado e isolado a cada inicialização para evitar persistência de dados de navegação obsoletos.

### 3.6 Física Autoritativa, Anti-Cheat e Validação Tridimensional (CryEngine Native-Path)
* **Prevenção de Atravessamento de Paredes (No-Clip):** Toda movimentação de jogadores e NPCs é validada pelo motor tridimensional `com.lostacademy.nativepath` a partir das malhas CryEngine compiladas (`*-path.dat`, resolução de 0.5m).
* **Validação Cinemática de Movimento e Velocidade:** Entradas que violem a velocidade máxima permitida de corrida, planar ou natação, ou que tentem deslocamentos instantâneos anômalos (teleporte não autorizado), são bloqueadas e corrigidas pelo servidor.
* **Anti-Corner-Cutting e Validação de Linha de Visão:** Checagens físicas de oclusão impedem conjuração de habilidades ou desferimento de ataques através de portas, paredes ou relevos montanhosos.

---

## 4. Como Reportar Vulnerabilidades de Segurança

Se você identificar uma vulnerabilidade técnica real no núcleo NIO (`commons`), nos protocolos do `login-server`, `chat-server`, em qualquer um dos três `game-server`, na `version.dll` ou no supervisor em `Rust`:

1. **NÃO abra uma issue pública** contendo códigos ou etapas de exploração ativa.
2. Reporte a vulnerabilidade de forma privada através dos [**Avisos de Segurança do GitHub (GitHub Security Advisories)**](https://github.com/kamidaki/aion-classic-5.0/security/advisories/new) neste repositório.
3. A equipe técnica responderá em até **48 horas** confirmando o recebimento e definindo o plano de mitigação.
4. Após a correção e auditoria do patch, a correção será mesclada na branch `main` com o devido crédito técnico ao pesquisador no histórico de commits.

---

## 5. Security Vulnerabilities Fixed

Em conformidade com as políticas contínuas de segurança e auditoria do GitHub Dependabot, todas as bibliotecas de terceiros integradas ao ecossistema Aion Classic passam por revisões periódicas.

Abaixo está o registro formal completo das 8 vulnerabilidades identificadas e mitigadas na pilha de rede assíncrona do `chat-server` (`io.netty` atualizado para `4.1.138.Final`):

| CVE / GHSA | Dependência | Versão vulnerável | Versão corrigida | Severidade | Data da correção | Descrição | Impacto | Correção aplicada | Fonte oficial |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| **CVE-2025-58057** / `GHSA-3p8m-j85q-pgmj` | `io.netty:netty-codec` | $\le$ `4.1.124.Final` | `4.1.138.Final` | Medium (6.9) | 2025-08-14 | Negação de Serviço (*DoS*) via descompressão irrestrita (*zip-bomb*) em `BrotliDecoder.decompress()`, alocando buffers repetidos de 64KB sem teto máximo. | Risco de exaustão de Heap da JVM (`OutOfMemoryError`) no ChatServer por pacotes comprimidos manipulados. | Atualização do `netty-codec` para `4.1.138.Final` e imposição de limite no acumulador de descompressão. | [GitHub Advisory GHSA-3p8m-j85q-pgmj](https://github.com/netty/netty/security/advisories/GHSA-3p8m-j85q-pgmj) |
| **CVE-2026-42578** / `GHSA-45q3-82m4-75jr` | `io.netty:netty-handler-proxy` | $\le$ `4.1.132.Final` | `4.1.138.Final` | High (7.5) | 2026-02-12 | Injeção de cabeçalhos HTTP e quebra de sequência CRLF em `HttpProxyHandler` devido à desativação explícita de validação (`withValidation(false)`) em conexões CONNECT. | Risco de injeção de requisições intermediárias ou adulteração de túneis em proxies upstream. | Atualização do Netty para `4.1.138.Final` restaurando validação obrigatória de delimitadores CRLF. | [GitHub Advisory GHSA-45q3-82m4-75jr](https://github.com/netty/netty/security/advisories/GHSA-45q3-82m4-75jr) |
| **CVE-2026-75595** / `GHSA-c4c3-7fpv-j4q5` | `io.netty:netty-handler` | $\le$ `4.1.136.Final` | `4.1.138.Final` | Critical (9.1) | 2026-03-20 | Bypass de roteamento SNI e mTLS em `SslClientHelloHandler#decode` decorrente de cálculo incorreto de offset ignorando cabeçalho de registro TLS de 5 bytes. | Risco de fallback inadvertido para o `SslContext` padrão em listeners TLS com múltiplos certificados de domínio. | Atualização para `4.1.138.Final` com parsing rigoroso de múltiplos records e prevenção de fallback não autorizado. | [GitHub Advisory GHSA-c4c3-7fpv-j4q5](https://github.com/netty/netty/security/advisories/GHSA-c4c3-7fpv-j4q5) |
| **CVE-2026-75596** / `GHSA-2g37-3h88-55hc` | `io.netty:netty-handler` | $\le$ `4.1.136.Final` | `4.1.138.Final` | High (8.7) | 2026-03-20 | Complexidade algorítmica quadrática e consumo desproporcional de CPU no event loop em `SniHandler` ao processar mensagens TLS fragmentadas em pequenos pacotes. | Degradação severa e travamento temporário do processamento de eventos de rede em conexões concorrentes. | Atualização para `4.1.138.Final` substituindo cópia quadrática cumulativa por buffer linear contínuo. | [Netty Security Advisory CVE-2026-75596](https://github.com/netty/netty/security/advisories/CVE-2026-75596) |
| **CVE-2026-100655** / `GHSA-rmcw-9fcq-wjq7` | `io.netty:netty-codec-http` | $\le$ `4.1.137.Final` | `4.1.138.Final` | High (7.5) | 2026-04-10 | Aceitação irrestrita de streams remotos concorrentes em `SpdySessionHandler`, permitindo esgotamento de recursos por rajadas de quadros `SYN_STREAM`. | Risco de exaustão de memória direta e heap da JVM por alocação excessiva de fluxos paralelos. | Atualização para `4.1.138.Final` impondo limites estritos de streams concorrentes por conexão. | [GitHub Advisory GHSA-rmcw-9fcq-wjq7](https://github.com/netty/netty/security/advisories/GHSA-rmcw-9fcq-wjq7) |
| **CVE-2026-93491** / `GHSA-m8gf-w8j2-r2hh` | `io.netty:netty-codec-http` | $\le$ `4.1.137.Final` | `4.1.138.Final` | High (7.5) | 2026-04-10 | Esgotamento de memória Heap via acúmulo irrestrito na fila `methodOverflowQueue` de `HttpServerCodec` sob pipelining HTTP/1.1 sem leitura pelo cliente. | Risco de vazamento de memória e queda do processo por acúmulo contínuo de requisições retidas. | Atualização para `4.1.138.Final` aplicando limites de retenção e aplicação de backpressure. | [Netty Security Advisory CVE-2026-93491](https://github.com/netty/netty/security/advisories/CVE-2026-93491) |
| **CVE-2026-59903** / `GHSA-8c42-7qj2-3j46` | `io.netty:netty-codec-http` | $\le$ `4.1.136.Final` | `4.1.138.Final` | Medium (6.5) | 2026-03-05 | Sobrescrita indevida do cabeçalho HTTP `Vary` em `CorsHandler#setVaryHeader`, descartando configurações prévias como `Vary: Authorization`. | Risco de envenenamento de cache (cache poisoning) e vazamento de respostas privadas em caches HTTP intermediários. | Atualização para `4.1.138.Final` garantindo união apropriada dos valores existentes no cabeçalho `Vary`. | [GitHub Advisory GHSA-8c42-7qj2-3j46](https://github.com/netty/netty/security/advisories/GHSA-8c42-7qj2-3j46) |
| **CVE-2026-59900** / `GHSA-c69g-56f8-xwqj` | `io.netty:netty-codec-http2` | $\le$ `4.1.135.Final` | `4.1.138.Final` | Medium (6.5) | 2026-02-28 | Falha de deduplicação e validação quando o pseudo-cabeçalho `:authority` e o cabeçalho literal `Host` coexistem na tradução de HTTP/2 para HTTP/1.x. | Risco de discrepância de interpretação de rotas e bypass de filtros de autorização baseados em host. | Atualização para `4.1.138.Final` garantindo conformidade estrita com RFC 9113 e consistência de autoridade. | [GitHub Advisory GHSA-c69g-56f8-xwqj](https://github.com/netty/netty/security/advisories/GHSA-c69g-56f8-xwqj) |

> **Nota de Implementação:** As dependências do `chat-server` foram unificadas na versão **`4.1.138.Final`** e os binários de distribuição final sincronizados em `Emulador - Produto Final/ChatServer/libs`, eliminando a presença de quaisquer artefatos Netty desatualizados no runtime.
