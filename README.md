# Aion Classic 5.0 EU — Emulador Java

Emulador completo e de alta performance para o cliente oficial **Aion Classic 5.0 (EU - Gameforge)** desenvolvido em Java, com compatibilização no protocolo de rede, handshake de criptografia Blowfish/RSA, sistema de combate 5.0, dados estáticos oficiais extraídos do cliente e pipelines automatizados de compilação e deploy.

---

## 🏛 Visão Geral da Arquitetura

O projeto é organizado nos seguintes módulos e diretórios de primeiro nível:

```text
├── 1 - Código Fonte [Emulador]/          # Código-fonte Java do Emulador (Login, Game, Chat)
│   ├── LoginServer/                      # Autenticação e seleção de servidor
│   ├── GameServer/                       # Motor do mundo, física, combate, entidades, skills, itens
│   ├── ChatServer/                       # Servidor de chat e comunicação em tempo real
│   ├── pom.xml                           # POM Maven multi-módulo agregador
│   └── build-server.bat                  # Script de automação de compilação e deploy
├── 2 - Emulador [Produto Final]/         # Distribuição executável e pronta para execução imediata
│   ├── LoginServer/                      # Binários e configs do LoginServer em produção
│   ├── GameServer/                       # Binários, static_data e configs do GameServer em produção
│   ├── ChatServer/                       # Binários e configs do ChatServer em produção
│   ├── StartAll.bat                      # Inicializador unificado de todos os serviços
│   └── StopAll.bat                       # Finalizador gracioso de todos os serviços
├── 2.5 - Executável Rust [Emulador]/     # Launcher/wrapper auxiliar em Rust
├── 3 - Código Fonte [Version.dll]/       # Hook C++/C# para o cliente (No-IP, bypass do launcher Gameforge)
├── 4 - Patch para o Client 5.0/          # Patch pronto para o cliente (bin32, bin64, Start x64.bat)
├── 5 - Documentação e Referências/       # Documentações, PCAPs oficiais e dados de referência
│   ├── 1 - Backup Original do Version.dll (No-IP)
│   ├── 2 - Wireshark - Oficial Classic 5.0
│   ├── 3 - JAVA EMU - 4.8 RETAIL
│   ├── 4 - Client 5.0 - Dados Extraidos
│   └── 5 - PLANOS
└── 6 - Ferramentas/                      # Scripts de geodata, PCAP, análise de memória e parsers XML
    └── parsersXML/                       # Suíte completa de parsers XML 5.0 sincronizada com o client
```

---

## 🎯 A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador seguem rigorosamente a cadeia causal de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

### Princípios Inegociáveis de Engenharia:
1. **Não implementar pacotes isoladamente**: Cada pacote recebido do cliente deve alimentar um evento de domínio, atualizar o estado persistente/em memória e acionar o sistema correspondente, que por sua vez gera as respostas e broadcasts necessários.
2. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais (`5 - Documentação e Referências/2 - Wireshark - Oficial Classic 5.0/`) ou da memória do processo do cliente em execução (`Aion.bin` / `game.dll`).
3. **Comparação e Encadeamento Limpo**: Comparar o comportamento identificado com a especificação canônica do cliente, implementar apenas o necessário dentro da arquitetura desacoplada e garantir que não existam handlers duplicados, lógica espalhada ou soluções temporárias.

---

## 📝 Padrão Obrigatório de Commits

Para manter o histórico do repositório organizado, rastreável e padronizado entre os desenvolvedores:

- **Idioma Estritamente em Português**: Mensagens de commit nunca devem ser escritas em inglês.
- **Formato de Uma Linha por Alteração**: Cada modificação relevante deve ser descrita em uma linha individual, de forma concisa, técnica e objetiva.
- **Estrutura Recomendada**:
  ```text
  Título resumido da entrega em português

  - modulo-modificado: descrição objetiva da primeira mudança
  - outro-modulo: descrição objetiva da segunda mudança
  - ui/docs: descrição objetiva da terceira mudança
  ```

---

## 📡 Arquitetura e Mapeamento Oficial de Opcodes (Classic 5.0)

### 1. Fio de Rede (Wire Protocol) e Transformação Matemática

- **Cliente $\to$ Servidor**:
  $$\text{decOp} = ((\text{wireOp} \oplus 0x36) - 0xC4) \pmod{0x10000}$$
  $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0x36$$
- **Servidor $\to$ Cliente**:
  $$\text{decOp} = ((\text{wireOp} \oplus 0xD4) - 0xC4) \pmod{0x10000}$$
  $$\text{wireOp} = ((\text{decOp} + 0xC4) \pmod{0x10000}) \oplus 0xD4$$

---

### 2. Login Server — Opcodes Canônicos

| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x07` | `CM_AUTH_GG` | Handshake de integridade do GameGuard |
| C $\to$ S | `0x0B` | `CM_LOGIN` | Envio de credenciais criptografadas via RSA (Usuário/Senha) |
| C $\to$ S | `0x05` | `CM_SERVER_LIST` | Requisição da lista de servidores |
| C $\to$ S | `0x02` | `CM_PLAY` | Seleção do servidor de jogo e solicitação de token |
| C $\to$ S | `0x08` | `CM_UPDATE_SESSION` | Atualização de sessão ativa |
| C $\to$ S | `0x0E` | `CM_NP_LOGIN` | Autenticação via launcher oficial |
| S $\to$ C | `0x00` | `SM_INIT` | Handshake inicial (Chave RSA + Chave Blowfish) |
| S $\to$ C | `0x01` | `SM_LOGIN_FAIL` | Resposta de falha de login |
| S $\to$ C | `0x02` | `SM_LOGIN_OK` | Confirmação de login e credenciais |
| S $\to$ C | `0x04` | `SM_SERVER_LIST` | Lista oficial de servidores e status |
| S $\to$ C | `0x06` | `SM_PLAY_FAIL` | Falha ao ingressar no servidor selecionado |
| S $\to$ C | `0x07` | `SM_PLAY_OK` | Token de autorização para o GameServer |
| S $\to$ C | `0x0B` | `SM_AUTH_GG` | Resposta de validação GameGuard |
| S $\to$ C | `0x0C` | `SM_UPDATE_SESSION` | Confirmação de sessão |

---

### 3. Chat Server — Opcodes Canônicos

| Direção | Opcode Fio | Nome do Pacote | Descrição Técnica |
| :--- | :---: | :--- | :--- |
| C $\to$ S | `0x00` | `CM_CHAT_INI` | Inicialização da conexão de chat |
| C $\to$ S | `0x05` | `CM_PLAYER_AUTH` | Autenticação com token do jogador |
| C $\to$ S | `0x10` | `CM_CHANNEL_REQUEST` | Requisição de ingresso ou saída de canal de chat |
| C $\to$ S | `0x14` | `CM_CHANNEL_MESSAGE` | Envio de mensagem para canal |
| S $\to$ C | `0x00` | `SM_CHAT_INI` | Handshake inicial do chat |
| S $\to$ C | `0x01` | `SM_PLAYER_AUTH_RESPONSE` | Validação de autenticação |
| S $\to$ C | `0x11` | `SM_CHANNEL_RESPONSE` | Confirmação de entrada em canal |
| S $\to$ C | `0x15` | `SM_CHANNEL_MESSAGE` | Broadcast de mensagem para o canal |

---

### 4. Game Server — Pacotes de Cliente e Servidor (Classic 5.0)

#### Principais Pacotes de Cliente (`CM_*`)
| WireOp | DecOp | Nome do Pacote | Descrição |
| :---: | :---: | :--- | :--- |
| `0x00F2` | `0x0000` | `CM_VERSION_CHECK` | Verificação de versão do cliente 5.0 |
| `0x00E0` | `0x0012` | `CM_TIME_CHECK` | Sincronização de horário e ping |
| `0x0182` | `0x00F0` | `CM_L2AUTH_LOGIN_CHECK` | Handshake de login e token |
| `0x0114` | `0x005E` | `CM_CHARACTER_LIST` | Requisição da lista de personagens |
| `0x0115` | `0x005F` | `CM_CREATE_CHARACTER` | Criação de novo personagem e aparência |
| `0x01E9` | `0x011B` | `CM_DELETE_CHARACTER` | Marcação de personagem para exclusão |
| `0x0143` | `0x00B1` | `CM_CHECK_NICKNAME` | Checagem de disponibilidade de nome |
| `0x00EA` | `0x0018` | `CM_ENTER_WORLD` | Entrada no mundo de jogo |
| `0x00EB` | `0x0019` | `CM_LEVEL_READY` | Notificação de carregamento de mapa concluído |
| `0x00E9` | `0x001B` | `CM_CHAT_MESSAGE_PUBLIC` | Chat geral / região / grito |
| `0x00D6` | `0x001C` | `CM_CHAT_MESSAGE_WHISPER`| Sussurro privado entre jogadores |
| `0x00D2` | `0x0020` | `CM_ATTACK` | Ataque básico com arma |
| `0x00D3` | `0x0021` | `CM_CASTSPELL` | Lançamento de magias e skills |
| `0x00C7` | `0x002D` | `CM_USE_ITEM` | Uso de poções, pergaminhos e consumíveis |
| `0x00C4` | `0x002E` | `CM_EQUIP_ITEM` | Equipar / desequipar armaduras e armas |
| `0x00C2` | `0x0030` | `CM_MOVE` | Movimentação tridimensional e coordenadas |
| `0x00CD` | `0x0037` | `CM_TARGET_SELECT` | Seleção de alvo |
| `0x014C` | `0x00B6` | `CM_RECIPE_LIST` | Lista de receitas aprendidas |
| `0x01F3` | `0x0101` | `CM_GLOBAL_TRADE` | Comércio global 5.0 |
| `0x0222` | `0x0150` | `CM_CLIENT_PING_STATE`| Monitoramento de latência em tempo real |

#### Principais Pacotes de Servidor (`SM_*`) e Exclusivos 5.0
| Opcode | Nome da Classe | Descrição |
| :---: | :--- | :--- |
| `0x0001` | `S_STATUS` | Atributos e estatísticas vitais do jogador |
| `0x0003` | `S_HIT_POINT` | Atualização instantânea de vida (HP) |
| `0x0004` | `S_MANA_POINT` | Atualização instantânea de mana (MP) |
| `0x0008` | `S_EXP` | Atualização de pontos de experiência e nível |
| `0x000D` | `S_TUTORIAL_HINT` | Dicas contextuais do novo tutorial 5.0 |
| `0x000E` | `S_PUT_NPC` | Aparição de NPC no mundo de jogo |
| `0x001A` | `S_LOAD_INVENTORY` | Carga completa de slots e inventário |
| `0x0020` | `S_PUT_USER` | Aparição de outros jogadores no campo visual |
| `0x0025` | `S_ACTION` | Ações de combate, danos, críticos e bloqueios |
| `0x0031` | `S_ABNORMAL_STATUS` | Aplicação de buffs, debuffs e efeitos de controle |
| `0x0047` | `S_KEY` | Handshake com chave criptográfica Blowfish |
| `0x005F` | `S_ZONE_MAP_INFO` | Geometria de zonas e mapas do Classic 5.0 |
| `0x0102` | `S_SECURITY_TOKEN` | Token de segurança secundário 5.0 |
| `0x0105` | `S_ACCOUNT_REPUTATION` | Reputação de conta e pontuações do servidor |
| `0x0110` | `S_SEASON_PASS_INFO` | Sistema do Season Pass / Daeva Pass |
| `0x0114` | `S_ACHIEVEMENT_REWARD_NOTI`| Recompensas e conquistas do Classic 5.0 |
| `0x0133` | `S_ENTER_WORLD_CHECK` | Confirmação oficial de entrada no mundo 5.0 |
| `0x019F` | `S_DAEVA_PASS_DATA` | Dados e recompensas completas do Daeva Pass |

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
Consulte sempre o documento [`CONTEXT.md`](file:///CONTEXT.md) para conhecer as diretrizes obrigatórias de arquitetura, integridade de dados estáticos e fluxo de desenvolvimento canônico.
