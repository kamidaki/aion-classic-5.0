# FASE 01: BASELINE AND ENVIRONMENT AUDIT
## Aion Classic 5.0 EU — Java 25 Migration

> **Fase**: 01 de 22  
> **Status**: `[CONCLUÍDO]`  
> **Data de Execução**: 2026-09-04  
> **Tag de Rollback**: `pre-java25-migration` (commit `83bca04fe76cf19b74ccb6b3daca74ac858a57b8`)

---

## 1. Auditoria de Ambiente e Toolchain

| Ferramenta | Versão Detectada | Requisito Java 25 | Status |
| :--- | :--- | :--- | :--- |
| **Java Runtime (JRE)** | Java(TM) SE Runtime Environment (build 25.0.2+10-LTS-69) | JDK 25 (LTS) | **CONFORME** |
| **Java Compiler (javac)** | javac 25.0.2 | javac 25+ | **CONFORME** |
| **Apache Maven** | 3.9.9 (rodando sob Java 25.0.2) | Maven 3.8.x+ / 3.9.x | **CONFORME** |
| **Python** | 3.13.0 64-bit | Python 3.8+ para automações | **CONFORME** |
| **Sistema Operacional** | Windows 10 Pro 64-bit (10.0.19045) | Multiplataforma | **CONFORME** |
| **Controle de Versão** | Git 2.45+ (Working tree clean no branch `main`) | Tag imutável criada | **CONFORME** |

---

## 2. Inventário de Arquivos do Emulador Classic 5.0

Varredura estrita realizada no diretório `1 - Código Fonte [Emulador]`:

| Módulo | Arquivos Java (.java) | Linhas de Código | Classes / Tipos | Papel na Arquitetura |
| :--- | :--- | :--- | :--- | :--- |
| **LoginServer** | 111 | 9.925 | ~140 | Autenticação RSA/Blowfish, Seleção de Servidor |
| **GameServer (Core)** | 2.382 | ~310.000 | ~2.900 | Lógica do Mundo, Entidades, Rede, Services |
| **GameServer (Scripts)** | 7.976 | ~181.155 | ~8.100 | Quests, AI2, Spawns, Instâncias, Habilidades |
| **ChatServer** | 62 | 4.696 | ~75 | Servidor de Canais de Chat e Mensageria |
| **WebSocketServer** | 1 | 246 | 2 | Servidor RFC 6455 de Gerenciamento Local |
| **TOTAL GERAL** | **10.532** | **506.022** | **~11.217** | **Aion Classic 5.0 EU Emulator** |

---

## 3. Baseline de Compilação com Maven (JDK 25)

Execução do comando:
```bash
mvn -f "D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]\pom.xml" clean compile -DskipTests
```

### Resultados da Baseline Inicial:
- `aion-server` (root): SUCCESS [0.219s]
- `login-server`: SUCCESS [3.024s] (111 arquivos compilados com javac `release 8`)
- `game-server`: SUCCESS [19.573s] (2.382 arquivos compilados com javac `release 8`)
- `chat-server`: SUCCESS [0.732s] (62 arquivos compilados com javac `release 8`)
- `websocket-server`: SUCCESS [0.254s] (1 arquivo compilado com javac `release 8`)
- **Tempo Total**: 23.977 segundos
- **Diagnóstico**: O projeto compila com sucesso no ambiente JDK 25, porém travado em `--release 8`, com avisos severos de dependências `systemPath` apontando para JARs obsoletos locais (`libs/`) e aviso de que a opção `-source 8` / `-target 8` está obsoleta e será removida em versões futuras da JVM.

---

## 4. Checkpoint e Segurança
- Tag Git criada: `pre-java25-migration`.
- Nenhuma modificação destrutiva sem histórico rastreável.
- FASE 01 FINALIZADA COM SUCESSO.
