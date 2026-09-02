# Aion Classic 5.0 EU — Emulador Java

Emulador completo e de alta performance para o cliente oficial **Aion Classic 5.0 (EU - Gameforge)** desenvolvido em Java, com compatibilização no protocolo de rede, handshake de criptografia Blowfish/RSA, sistema de combate 5.0, dados estáticos oficiais extraídos do cliente e pipelines automatizados de compilação e deploy.

---

## 🏛 Visão Geral da Arquitetura

O projeto é organizado nos seguintes módulos e diretórios de primeiro nível:

```text
D:\AION CLASSIC 5.0 - EMULADOR\
├── 1 - Código Fonte [Emulador]\          # Código-fonte Java do Emulador (Login, Game, Chat)
│   ├── LoginServer/                      # Autenticação e seleção de servidor
│   ├── GameServer/                       # Motor do mundo, física, combate, entidades, skills, itens
│   ├── ChatServer/                       # Servidor de chat e comunicação em tempo real
│   ├── pom.xml                           # POM Maven multi-módulo agregador
│   └── build-server.bat                  # Script de automação de compilação e deploy
├── 2 - Emulador [Produto Final]\         # Distribuição executável e pronta para execução imediata
│   ├── LoginServer/                      # Binários e configs do LoginServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   ├── ChatServer/                       # Binários e configs do ChatServer em produção
│   ├── StartAll.bat                      # Inicializador unificado de todos os serviços
│   └── StopAll.bat                       # Finalizador gracioso de todos os serviços
├── 2.5 - Executável Rust [Emulador]\     # Launcher/wrapper auxiliar em Rust
├── 3 - Código Fonte [Version.dll]\       # Hook C++/C# para o cliente (No-IP, bypass do launcher Gameforge)
├── 4 - Patch para o Client 5.0\          # Patch pronto para o cliente (bin32, bin64, Start x64.bat)
├── 5 - Documentação e Referências\       # Documentações, PCAPs oficiais e dados de referência
│   ├── 1 - Backup Original do Version.dll (No-IP)
│   ├── 2 - Wireshark - Oficial Classic 5.0
│   ├── 3 - JAVA EMU - 4.8 RETAIL
│   ├── 4 - Client 5.0 - Dados Extraidos
│   └── 5 - PLANOS
└── 6 - Ferramentas\                      # Scripts de geodata, PCAP, análise de memória e parsers XML
    └── parsersXML\                       # Suíte completa de parsers XML 5.0 sincronizada com o client
```

---

## ⚡ Ambiente de Execução e Roadmap

- **Runtime Atual**: Java 8 (Recomendado: `jdk1.8.0_431` ou superior x64).
- **Build Tool**: Apache Maven 3.8+ (3.9.9 testado).
- **Banco de Dados**: MySQL 5.7+ / MariaDB 10.x / MySQL 8.x.
- **Roadmap Futuro**:
  - Migração planejada para **Java 25 (LTS)**.
  - Otimizações com Virtual Threads (Project Loom), Foreign Function & Memory API e alto throughput de pacotes concorrentes.

---

## 🛠 Como Compilar e Executar

### 1. Compilação e Publicação Automática
Para compilar o código-fonte e atualizar a pasta de produção `2 - Emulador [Produto Final]`, execute na pasta `1 - Código Fonte [Emulador]`:
```bat
build-server.bat
```
Ou via linha de comando com o Maven:
```bash
mvn clean package -DskipTests=true
```

### 2. Inicialização dos Servidores
Para iniciar toda a suite de servidores em janelas dedicadas, acesse `2 - Emulador [Produto Final]` e execute:
```bat
StartAll.bat
```
Para encerrar graciosamente os servidores:
```bat
StopAll.bat
```

### 3. Conexão do Cliente
1. Instale o cliente oficial **Aion Classic 5.0 (EU)**.
2. Aplique o conteúdo da pasta `4 - Patch para o Client 5.0\` no diretório raiz do seu cliente.
3. Inicie o jogo através de `Start x64.bat`.

---

## 📜 Regras de Desenvolvimento e Qualidade
Consulte sempre o documento [`CONTEXT.md`](file:///D:/AION%20CLASSIC%205.0%20-%20EMULADOR/CONTEXT.md) para conhecer as diretrizes obrigatórias de arquitetura, integridade de dados estáticos e fluxo de desenvolvimento canônico.
