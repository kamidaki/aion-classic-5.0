# Política de Segurança e Arquitetura de Proteção — AION CLASSIC 5.0 EMULADOR

<p align="center">
  <a href="./SECURITY.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_Brasil_(Padr%C3%A3o)-10b981?style=for-the-badge&logo=markdown&logoColor=white" alt="PT-BR Padrão" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-3b82f6?style=for-the-badge&logo=markdown&logoColor=white" alt="CONTEXT.md" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Supervisor_Dashboard-Loopback_Only_(127.0.0.1)-10b981?style=flat-square" alt="Loopback Only" />
  <img src="https://img.shields.io/badge/GeoIP_Firewall-Bloqueio_no_Socket_NIO-0ea5e9?style=flat-square" alt="GeoIP Firewall" />
  <img src="https://img.shields.io/badge/Criptografia-RSA_1024_%2B_Blowfish-6366f1?style=flat-square" alt="RSA + Blowfish" />
  <img src="https://img.shields.io/badge/Runtime-Java_25_LTS_Embarcado-181717?style=flat-square&logo=openjdk&logoColor=white" alt="Java 25 LTS" />
</p>

> [!IMPORTANT]
> **ISOLAMENTO DE SUPERFÍCIE ADMINISTRATIVA E PROTEÇÃO DE REDE:**  
> O painel web administrativo e o Database Studio do supervisor nativo em Rust (`Aion Classic - EMULADOR.exe`) fazem *bind* exclusivamente em `127.0.0.1` (*loopback*). Além disso, os servidores Java contam com o subsistema nativo `GeoIPFilterService`, que rejeita conexões não autorizadas diretamente no nível do socket TCP NIO antes de qualquer alocação de sessão ou handshake criptográfico.

---

## 1. Versões e Componentes Suportados para Auditoria de Segurança

| Componente / Módulo | Tecnologia / Versão | Status de Auditoria de Segurança |
| :--- | :---: | :---: |
| **Backend Multimodular (`commons`, `login-server`, `game-server`, `chat-server`)** | `Java 25 LTS (jdk-25.0.2)` | ![Ativo](https://img.shields.io/badge/AUDITADO-10b981?style=flat-square) |
| **Supervisor Nativo e Database Studio (`Aion Classic - EMULADOR.exe`)** | `Rust 1.80+ (MSVC x64)` | ![Ativo](https://img.shields.io/badge/AUDITADO-10b981?style=flat-square) |
| **Proxy Hook do Cliente (`version.dll` Standalone)** | `C/C++ (MSVC v143 x64/x86)` | ![Ativo](https://img.shields.io/badge/AUDITADO-10b981?style=flat-square) |
| **Versões legadas abaixo do Java 25 ou com dependências `javolution`** | `Java 8 / 11 / 17 / 21` | ![Bloqueado](https://img.shields.io/badge/DESCONTINUADO_POR_SEGURAN%C3%87A-ef4444?style=flat-square) |

---

## 2. Camadas de Segurança e Filtragem de Conexões

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#0f172a', 'primaryTextColor': '#f8fafc', 'primaryBorderColor': '#10b981', 'lineColor': '#38bdf8'}}}%%
flowchart TD
    Conn["Conexão TCP Recebida (2106 / 7777 / 10241)"] --> GeoIP{"GeoIPFilterService<br/>IP na Whitelist ou País Permitido?"}
    GeoIP -->|"Não (ou Fail-Safe Ativo)"| Drop["Rejeição Imediata no Socket NIO<br/>Zero Alocação de Heap"]
    GeoIP -->|"Sim"| Crypto["Handshake Criptográfico<br/>S_KEY (Blowfish) + SM_INIT (RSA 1024-bit)"]
    Crypto --> Opcode["Validação de Frame, Checksum (~opcode)<br/>e Transformação Canônica 5.0"]
    Opcode -->|"Pacote Inválido / Adulterado"| Disconnect["Encerramento Imediato da Sessão<br/>+ Registro de Auditoria"]
    Opcode -->|"Pacote Íntegro"| World["Processamento Autoritativo no Servidor<br/>(Validação Física CryEngine Native-Path)"]
```

---

## 3. Matriz de Controles de Segurança Implementados

| Domínio de Segurança | Mecanismo Implementado | Localização no Repositório |
| :--- | :--- | :--- |
| **Firewall Geográfico no Socket NIO** | Bloqueio pré-handshake por país (IPv4/IPv6 em memória) com política *fail-safe* estrita | `Código Fonte - Emulador/commons` (`GeoIPFilterService`) |
| **Isolamento do Painel Supervisor e DB Studio** | Bind estrito em `127.0.0.1:18080` e controle de ciclo de vida via Windows Job Objects | `Ferramentas e Documentos/Ferramentas Python e PowerShell/Código Fonte - Executável Rust do Emulador` |
| **Higienização Automática de Cache WebView2** | Diretório de dados isolado em `%LOCALAPPDATA%\AionClassicEmulador\WebView2`, limpo e recriado a cada inicialização | `Código Fonte - Executável Rust do Emulador/src/webview.rs` |
| **Runtime Java 25 Determinístico Embarcado** | Distribuição isolada em `Emulador - Produto Final/Config/java-deployment` evitando execução acidental em JVMs vulneráveis do sistema | `Emulador - Produto Final/Config/config.json` |
| **Prevenção de Atravessamento de Paredes (No-Clip)** | Validação física tridimensional autoritativa via `com.lostacademy.nativepath` (`*-path.dat` 0.5m) | `Código Fonte - Emulador/game-server` |
| **Proteção de Credenciais de Banco de Dados** | Exclusão de `database.properties` no `.gitignore` e geração segura com validação contra injeção de quebras de linha | `.gitignore` / `src/config.rs` |

---

## 4. Como Reportar Vulnerabilidades Reais

Caso identifique uma vulnerabilidade técnica real no núcleo NIO (`commons`), na lógica de validação autoritativa (`game-server`, `login-server`, `chat-server`) ou no supervisor nativo (`Rust`), submeta um Pull Request corretivo seguindo rigorosamente as regras de validação descritas em [`CONTRIBUTING.md`](./CONTRIBUTING.md).
