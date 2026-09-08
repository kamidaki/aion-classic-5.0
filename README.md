# Aion Classic 5.0 EU — Emulador Java (Java 25 LTS)

O **melhor e único emulador Aion Classic 5.0 do mundo**, totalmente construído e operando em **Java 25 (LTS)**. Desenvolvido com foco obsessivo em desempenho, estabilidade inabalável e fidelidade máxima ao cliente oficial **Aion Classic 5.0 (EU - Gameforge)**. Conta com compatibilização completa no protocolo de rede, criptografia Blowfish/RSA, sistema de combate fluido, dados estáticos 5.0 extraídos diretamente do cliente oficial e subsistema nativo de **Firewall GeoIP**.

---

## Destaques da Arquitetura 5.0

- **100% Java 25 (LTS)**: Compilado nativamente com javac release 25, aproveitando as mais modernas otimizações da JVM.
- **Purga Total do Javolution**: Substituição integral por coleções nativas de alta performance (`java.util` e `java.util.concurrent`), reduzindo overhead e consumo de heap.
- **Firewall GeoIP Integrado**: Filtro geográfico nativo no socket NIO que bloqueia imediatamente conexões não autorizadas de países não permitidos antes de alocar memória ou processar pacotes.
- **Validação e Integridade Estática Completa**: Tabelas XML de skills, itens, NPCs, quests e motions 100% alinhadas com os esquemas XSD oficiais e dados extraídos do cliente 5.0.

---

## Estrutura de Diretórios do Projeto

```text
├── 1 - Código Fonte [Emulador]/          # Código-fonte Java multi-módulo em Java 25 (LTS)
│   ├── commons/                          # Núcleo de rede (NIO), criptografia Blowfish/RSA, GeoIP e threads
│   ├── chat-server/                      # Servidor de chat e comunicação em tempo real
│   ├── game-server/                      # Motor de jogo, física, IA, combate, entidades, skills, itens
│   ├── login-server/                     # Autenticação RSA/Blowfish, seleção de servidores e sessões
│   └── pom.xml                           # POM Maven agregador multi-módulo (Java 25)
├── 2 - Emulador [Produto Final]/         # Distribuição de produção executável e pronta para uso imediato
│   ├── Aion Classic - EMU.exe            # Executável do Inicializador e Supervisor visual nativo
│   ├── config.json                       # Configurações do inicializador, JVM e parâmetros de boot
│   ├── ChatServer/                       # Binários, libs e configurações do ChatServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   └── LoginServer/                      # Binários e configs do LoginServer em produção
├── 2.5 - Executável Rust [Emulador]/     # Código-fonte Rust do inicializador e painel supervisório nativo
├── 3 - Código Fonte [Version.dll]/       # Código C++/C# do hook No-IP e bypass de launcher oficial
├── 4 - Patch para o Client 5.0/          # Patch pronto para o cliente (bin32, bin64, Start x64.bat)
├── 5 - Documentação e Referências/       # Documentações, PCAPs oficiais e dados canônicos
│   ├── 1 - Version.dll - NoIP/           # Backups e referências do wrapper DLL
│   ├── 2 - Wireshark - Oficial Classic 5.0/ # Capturas reais de tráfego de rede do cliente 5.0
│   ├── 3 - Client 5.0 - Dados Extraidos/ # Dados oficiais extraídos do cliente (skills, itens, npcs)
│   └── 100 - Outros/                     # Ícones e referências complementares
└── 6 - Ferramentas/                      # Suíte de scripts Python, decodificadores BXML e utilitários
    ├── aion_bxml.py                      # Decodificador de XMLs binários (BXML) do cliente
    ├── aion_pak.py / aion_unpak.py       # Manipulação e extração de arquivos .pak oficiais
    └── parsersXML/                       # Parsers dedicados para geração e sincronização de static_data
```

---

## Firewall GeoIP & Proteção Contra Países Não Autorizados

O emulador integra nativamente no pacote `com.aionemu.commons.network.GeoIPFilterService` uma camada de proteção geográfica e anti-intrusão operando no nível de transporte TCP:

1. **Bloqueio no Socket**: Conexões oriundas de faixas IP fora dos países autorizados são rejeitadas instantaneamente antes do handshake de criptografia, poupando CPU e memória do servidor.
2. **Faixas IPv4 e IPv6**: Base de dados de prefixos globais indexada em memória para busca em tempo logarítmico.
3. **Controle por Lista de Países**: Configuração simples por códigos ISO (ex: `BR,PT,US` ou `all` para liberar globalmente).
4. **Whitelist Manual**: Permite adicionar IPs ou sub-redes específicas para administradores e serviços parceiros.
5. **Configuração (`geo_firewall.properties` ou propriedades de sistema)**:
   - `geo.firewall.enable`: Ativa/desativa o firewall (`true` / `false`).
   - `geo.firewall.world_ip_range_dir`: Pasta com as tabelas de ranges IP por país.
   - `geo.firewall.allowed_countries`: Países liberados (ex: `BR,PT`).
   - `geo.firewall.manual_whitelist_ips`: IPs individuais autorizados.

---

## A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador seguem rigorosamente a cadeia causal de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

### Princípios Inegociáveis de Engenharia:
1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/`) ou dos dados extraídos do cliente oficial (`5 - Documentação e Referências/3 - Client 5.0 - Dados Extraidos/`).
3. **Sincronização Rigorosa**: Toda alteração no código-fonte em `1 - Código Fonte [Emulador]` deve ser compilada e os artefatos publicados em `2 - Emulador [Produto Final]`.

---

## Padrão Obrigatório de Commits

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, de forma concisa, técnica e objetiva.

---

## Compilação, Deploy e Inicialização

### 1. Compilação dos Servidores Java (Maven)
```bash
mvn -f "1 - Código Fonte [Emulador]/pom.xml" clean package -DskipTests
```
O build compila os módulos em Java 25 (`commons`, `chat-server`, `game-server`, `login-server`) e gera os `.jar` em cada pasta `target/`.

### 2. Deploy dos Binários no Produto Final
Copiar os artefatos gerados para a pasta de produção:
- `game-server/target/game-server-4.8-SNAPSHOT.jar` $	o$ `2 - Emulador [Produto Final]/GameServer/libs/`
- `commons/target/commons-4.8-SNAPSHOT.jar` $	o$ `2 - Emulador [Produto Final]/<Server>/libs/`
- `login-server/target/login-server-4.8-SNAPSHOT.jar` $	o$ `2 - Emulador [Produto Final]/LoginServer/libs/`
- `chat-server/target/chat-server-4.8-SNAPSHOT.jar` $	o$ `2 - Emulador [Produto Final]/ChatServer/libs/`

### 3. Como Iniciar o Emulador
A inicialização do emulador é realizada através do executável nativo único:
```text
2 - Emulador [Produto Final]\Aion Classic - EMU.exe
```
Ao iniciar:
- Uma única instância do emulador é garantida via Windows Named Mutex.
- Os servidores são inicializados em ordem sequencial: **ChatServer** $\to$ **LoginServer** $\to$ **GameServer**.
- Todos os processos executam em segundo plano, com interface gráfica web integrada, telemetria de CPU/RAM em tempo real e Database Studio.

### 4. Conexão do Cliente Oficial 5.0
1. Tenha o cliente oficial **Aion Classic 5.0 (EU)** instalado.
2. Aplique os arquivos da pasta `4 - Patch para o Client 5.0\` no diretório do seu cliente.
3. Inicie o jogo executando `Start x64.bat`.

---

## Regras de Desenvolvimento e Qualidade
Consulte sempre o documento [`CONTEXT.md`](file:///CONTEXT.md) para conhecer as diretrizes obrigatórias de arquitetura, integridade de dados estáticos e fluxo de desenvolvimento canônico.
