# Aion Classic 5.0 EU — Java Emulator

Emulador Java de alta performance para o cliente **Aion Classic 5.0 (EU - Gameforge)**, compatibilizado no protocolo de rede, handshake de criptografia, opcodes, classes 5.0, tabelas estáticas de dados XML e arquitetura de compilação multi-módulo com Apache Maven.

---

> [!CAUTION]
> # 🚨 DIRETRIZES MANDATÓRIAS E REGRAS INEGOCIÁVEIS DE DESENVOLVIMENTO
> **ESTAS REGRAS SÃO ESTRITAMENTE OBRIGATÓRIAS PARA TODOS OS DESENVOLVEDORES E AGENTES DE IA NESTE PROJETO.**
> **QUALQUER VIOLAÇÃO OU WORKAROUND QUEBRA A ARQUITETURA E NÃO SERÁ TOLERADA.**

### 1. Novo Root e Proibições Absolutas de Referências Obsoletas
* **Raiz Oficial e Definitiva do Projeto**:
  `D:\AION CLASSIC 5.0 - EMULADOR`
* O diretório antigo `D:\AION CLASSIC 5.0 - EMULADOR` é **obsoleto** e deve ser completamente ignorado. Nunca ler, referenciar ou depender de arquivos do diretório antigo.
* **O PROJETO É UM EMULADOR JAVA (Aion Classic 5.0)**, não mais um emulador em Rust.
* **NUNCA FAZER WORKAROUND (GAMBIARRAS OU ATALHOS TEMPORÁRIOS).**
* **NUNCA consulte os emuladores legados (2.5, 2.8 ou 4.8) do workspace sem autorização e orientação prévia.** Use apenas `5 - Documentação e Referências\3 - JAVA EMU - 4.8 RETAIL` como referência arquitetural quando expressamente solicitado.
* **NUNCA consulte coletas de rede (Wireshark / PCAPs) que estejam fora deste projeto.** Use exclusivamente as capturas de:
  `D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\2 - Wireshark - Oficial Classic 5.0\`

---

### 2. Regra Rígida de Dados XML — NUNCA Fazer Bypass de Código por Dados Faltantes
> [!WARNING]
> **É TERMINANTEMENTE PROIBIDO CRIAR BYPASS NO JAVA PARA SUPRIR FALTA DE DADOS ESTÁTICOS!**
> Quando não houver definição de item, NPC, monstros, magias, skills ou atributos nos XMLs:
> - **NÃO crie fallbacks hardcoded, valores mágicos fictícios ou pontes que ignoram os templates.**
> - **A ÚNICA abordagem correta e obrigatória é CORRIGIR OS XMLs.**
> - Todas as correções de XML devem ser feitas utilizando os scripts em:
>   `D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\parsersXML`
> - Caso algum script Python da pasta de parsers esteja incompleto, **atualize o parser Python** para cobrir o que falta e gere novamente os dados.
> - A fonte de verdade dos dados oficiais do cliente 5.0 está localizada em:
>   `D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\4 - Client 5.0 - Dados Extraidos\data`
>   É dessa pasta que os parsers extraem os dados oficiais e montam/comparam os XMLs de templates do Java em:
>   `D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\GameServer\data\static_data`
>   e sincronizam com:
>   `D:\AION CLASSIC 5.0 - EMULADOR\2 - Emulador [Produto Final]\GameServer\data\static_data`

---

### 3. Integridade de Gameplay — Sem Pontes ou Atalhos
* **NUNCA faça bypass de sistemas de gameplay.** Você deve desenvolver ou corrigir as classes reais dos serviços (`services/`), entidades (`model/`) e controladores (`controllers/`) que tratam aquela funcionalidade no motor do jogo.
* **Nunca crie uma "ponte" ou atalho** que passe por cima das camadas do emulador para forçar um resultado artificial na tela.

---

### 4. Arquitetura e Fluxo Canônico

Siga sempre a **Regra Principal de Arquitetura**:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`5 - Documentação e Referências\2 - Wireshark - Oficial Classic 5.0\`) ou da memória do processo do cliente em execução (`Aion.bin` / `game.dll`).
3. **Encadeamento Canônico**: Garantir que não existam handlers duplicados, pacotes espúrios injetados ou lógicas espalhadas fora da arquitetura.

---

## 🏛 Estrutura de Diretórios do Projeto

```text
D:\AION CLASSIC 5.0 - EMULADOR\
├── 1 - Código Fonte [Emulador]\          # Código-fonte Java do Emulador (Login, Game, Chat)
│   ├── LoginServer/                      # Autenticação RSA/Blowfish, seleção de servidor e contas
│   ├── GameServer/                       # Mundo do jogo, física, entidades, skills, itens, dados estáticos
│   ├── ChatServer/                       # Canais de chat global, grupos e comunicação em tempo real
│   ├── pom.xml                           # POM Maven multi-módulo agregador
│   └── build-server.bat                  # Script de automação de compilação e deploy
├── 2 - Emulador [Produto Final]\         # Distribuição executável e pronta para execução imediata
│   ├── LoginServer/                      # Binários e configs do LoginServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   ├── ChatServer/                       # Binários e configs do ChatServer em produção
│   ├── StartAll.bat                      # Inicializador unificado de todos os serviços
│   └── StopAll.bat                       # Finalizador gracioso de todos os serviços
├── 2.5 - Executável Rust [Emulador]\     # Launcher/wrapper auxiliar de inicialização rápida
├── 3 - Código Fonte [Version.dll]\       # Hook C++/C# para o cliente (No-IP, bypass launcher oficial)
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
  - Otimizações com Virtual Threads (Project Loom), Records, Foreign Function & Memory API e melhorias massivas de throughput.

---

## 🛠 Workflow de Desenvolvimento

$$\mathbf{Código\ Fonte\ [1]} \xrightarrow{\text{mvn clean package / build-server.bat}} \mathbf{Build\ &amp;\ Deploy} \xrightarrow{\text{Sincronização}} \mathbf{Produto\ Final\ [2]} \xrightarrow{\text{StartAll.bat}} \mathbf{Servidor\ Ativo}$$

1. **Alterações de Código**: Feitas exclusivamente em `1 - Código Fonte [Emulador]`.
2. **Compilação**: Executada via `build-server.bat` ou `mvn clean package -DskipTests=true`.
3. **Deploy**: O `build-server.bat` publica e atualiza automaticamente os artefatos em `2 - Emulador [Produto Final]`.
4. **Execução**: Realizada através do `StartAll.bat` dentro de `2 - Emulador [Produto Final]`.
