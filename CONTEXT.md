# CONTEXTO GLOBAL DO PROJETO - EMULADOR AION CLASSIC 4.5 EM RUST

> **Documento Central de Rastreamento e Estado do Projeto**  
> *Este arquivo DEVE ser atualizado continuamente a cada marco alcançado, nova funcionalidade implementada, pacote mapeado ou bug corrigido no emulador Rust.*

---

## 1. Visão Geral do Projeto

O objetivo deste projeto é o desenvolvimento de um **Emulador de Alta Performance em Rust para Aion Classic versão 4.5 (Client GameForge)**. O emulador visa substituir e superar as implementações tradicionais em Java, oferecendo:
- **Segurança de Memória e Concorrência Real** (sem paradas de Garbage Collector).
- **Consumo Mínimo de Recursos** com processamento assíncrono via `tokio` e canais `crossbeam`.
- **Arquitetura Resiliente Anti-Crash**: mapeamento sistemático de todos os pacotes Client $\leftrightarrow$ Server (CM / SM) e fallbacks seguros para evitar crashes do cliente 4.5.
- **Suporte aos Novos Recursos do Classic 4.5**: Daeva Pass, Roupeiro (Wardrobe), novos pacotes de segurança, sistemas modernos de instâncias e balanceamento.

---

## 2. Diretórios e Recursos do Ecossistema

| **Repositório GitHub** | `https://github.com/kamidaki/aion-classic-rust` | Repositório oficial do emulador para versionamento e controle de versão contínuo. |
| **Pasta de Deploy Limpa** | `D:\AION RUST\AionEMU\AionEMU\deploy` | Pasta de produção limpa com executáveis e inicializador de 1 clique (`INICIAR_SERVIDOR.bat`). |
| **Emulador Rust (Principal)** | `D:\AION RUST\AionEMU\AionEMU\Emulador-Rust` | Código-fonte do servidor Rust (`game-server`, `auth-server`, `sts-server`, `launcher`, `krypt`, `pak`, `bxml`, `pcap-parser`). |
| **Cliente Aion Classic 4.5** | `D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic` | Binários do cliente oficial (`bin64/AION.bin`, `aion.exe`, `.pak`, dados XML). Usado para testes e capturas reais. |
| **Emulador Java 4.8 Retail** | `D:\AION RUST\AionEMU\AionEMU\JAVA EMU - 4.8 RETAIL` | **Referência Completa e Estável (Java 25)**. Base estrutural de CM/SM, controllers, services, managers, regras de combate e banco de dados. |
| **Wireshark** | `E:\Programas instalados - Leves\Wireshark` | Captura e inspeção de tráfego de rede TCP/UDP para análise de pacotes e payloads. |
| **GeoBuilder** | `F:\Servidor Aion\SERVIDOR RETAIL 7.7\GeoBuilder` | Gerador e extrator de GeoData, malhas de colisão (NavMesh) e mapas de altura para Line of Sight (LoS) e física. |
| **Projeto Valkyrie 2.8 Classic** | `F:\Servidor Aion\Aion 2.8 Classic Projeto VALKYRIE\Aion 2.8 Classic Projeto VALKYRIE\aionsdo-master` | Servidor Classic 2.8 em Java para conferência complementar de particularidades Classic. |
| **Plano de Desenvolvimento** | `D:\AION RUST\AionEMU\AionEMU\PLANO-DESENVOLVIMENTO` | Guia mestre de execução sequencial (Etapas 00 a 21). |

---

## 3. Estado Atual do Emulador Rust (`Emulador-Rust`)

### Conquistas Recentes:
- **Independência do Replay**: O cliente conecta, cria personagens e entra no mundo em Pandaemonium sem depender de pacotes gravados estáticos.
- **Autenticação STS e Launcher**: Integração via Named Pipe (`\\.\pipe\aion_launch`) e Handshake STS com criptografia AES/RSA/RC4 e tokens estáveis.
- **Criação e Lista de Personagens**:
  - Mapeamento do deslocamento do pedido de criação (bytes 22..162 mapeados para 4..144 do registro da lista).
  - Cálculo de redundância de mesh (`100000 + raca*2 + genero`).
  - Persistência básica de contas e personagens no banco SQLite (`aion.db`).
- **Extração de NPCs e Streaming**:
  - Extração de 1.054 NPCs reais de Pandaemonium via PCAP e catalogo de nomes do cliente.
  - Implementação de streaming por alcance de visão (~20m) e despawn dinâmico (`S_PUT_NPC` / `S_REMOVE_OBJECT`).
- **Correção Crítica de I/O**:
  - Substituição de `write` parcial por `write_all`, resolvendo telas de carregamento travadas e erros de "Packet Checksum Failed".
- **Skills Básicas**:
  - Parser de `client_skill_learns.xml` com 18.644 regras lidas e envio de `S_ADD_SKILL` autolearn no login.

---

## 4. Tabela de Progresso do Plano de Desenvolvimento

> **Regra**: As etapas devem ser seguidas rigorosamente na ordem de numeração (00 a 21).

| Etapa | Arquivo do Plano | Status | Descrição Resumida |
| :---: | :--- | :---: | :--- |
| **00** | [00_VISAO_GERAL_E_METODOLOGIA.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/00_VISAO_GERAL_E_METODOLOGIA.md) | **Concluída** | Arquitetura, metodologia, protocolo de testes autônomos e ferramentas. |
| **01** | [01_INFRAESTRUTURA_REDE_SEGURANCA_PROTOCOLOS.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/01_INFRAESTRUTURA_REDE_SEGURANCA_PROTOCOLOS.md) | **Concluída** | Framework unificado de pacotes CM/SM, encriptação e tratamento de opcodes anti-crash. |
| **02** | [02_AUTENTICACAO_STS_LOGIN_PERSONAGEM.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/02_AUTENTICACAO_STS_LOGIN_PERSONAGEM.md) | **Concluída** | Pipeline de autenticação STS/Auth, lobby, criação completa de personagens e SQLite. |
| **03** | [03_MOTOR_MUNDO_SPATIAL_ENTIDADES.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/03_MOTOR_MUNDO_SPATIAL_ENTIDADES.md) | **Concluída** | World Engine, Grid espacial 2D/3D, KnownList/Streaming de entidades e Game Loop. |
| **04** | [04_SISTEMA_MOVIMENTACAO_FISICA_GEOENGINE.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/04_SISTEMA_MOVIMENTACAO_FISICA_GEOENGINE.md) | **Concluída** | Movimentação (`CM_MOVE`/`SM_MOVE`), voo, gliding, GeoEngine, colisão e Line of Sight. |
| **05** | [05_STATUS_ATRIBUTOS_SISTEMA_VIDA.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/05_STATUS_ATRIBUTOS_SISTEMA_VIDA.md) | **Concluída** | Motor de atributos, modificadores dinâmicos, regeneração (HP/MP/DP/FP) e sincronização. |
| **06** | [06_ITENS_INVENTARIO_EQUIPAMENTOS_ECONOMIA.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/06_ITENS_INVENTARIO_EQUIPAMENTOS_ECONOMIA.md) | **Concluída** | Cube, Warehouse, Equipamentos, Stigmas, Manastones, Encantamento, Trade e Broker. |
| **07** | [07_SISTEMA_DE_COMBATE_E_HABILIDADES_SKILLENGINE.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/07_SISTEMA_DE_COMBATE_E_HABILIDADES_SKILLENGINE.md) | **Concluída** | SkillEngine completo, fórmulas de combate, EffectEngine (buffs/debuffs/CCs) e combos. |
| **08** | [08_IA_DE_NPCS_MONSTROS_E_SPAWNENGINE.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/08_IA_DE_NPCS_MONSTROS_E_SPAWNENGINE.md) | **Concluída** | SpawnEngine (população mundial), Máquinas de Estado de IA, Aggro/Threat e Drop System. |
| **09** | [09_DIALOGOS_MISSOES_QUESTENGINE.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/09_DIALOGOS_MISSOES_QUESTENGINE.md) | **Concluída** | QuestEngine (Campanhas, Quests, Work Orders), Diálogos HTML, Gatilhos e Persistência. |
| **10** | [10_SISTEMAS_SOCIAIS_GUILDAS_ABYSS_PVP.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/10_SISTEMAS_SOCIAIS_GUILDAS_ABYSS_PVP.md) | **Concluída** | Chat Server, Party/Alliance, Legiões, Sistema de Abyss (AP, Ranks, PvP) e Duelos. |
| **11** | [11_INSTANCIAS_MASMORRAS_E_EVENTOS.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/11_INSTANCIAS_MASMORRAS_E_EVENTOS.md) | **Concluída** | Instâncias dinâmicas (`WorldMapInstance`) e Masmorras PvE clássicas. |
| **12** | [12_COLETA_ARTESANATO_E_CRAFTING.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/12_COLETA_ARTESANATO_E_CRAFTING.md) | **Pendente** | Coleta (Vitalidade e Éter), 7 Profissões de Artesanato, Procs de Craft e Work Orders. |
| **13** | [13_PETS_MINIONS_SUMMONS_E_TRAPS.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/13_PETS_MINIONS_SUMMONS_E_TRAPS.md) | **Pendente** | Mascotes funcionais (Loot/Bag/Buff/Feed), Espíritos de Spiritmaster e Armadilhas. |
| **14** | [14_HABITACOES_HOUSING_E_DECORACAO.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/14_HABITACOES_HOUSING_E_DECORACAO.md) | **Pendente** | Estúdios, Casas no Mundo Aberto, Leilões Semanais, Decorações e Mobílias Funcionais. |
| **15** | [15_OBJETOS_INTERATIVOS_CLIMA_E_AMBIENTE.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/15_OBJETOS_INTERATIVOS_CLIMA_E_AMBIENTE.md) | **Pendente** | Kisks (Individuais e de Legião), Portas Estáticas, Vento (Windstreams), FlyRings e Clima. |
| **16** | [16_SERVICOS_WEB_LOJA_INGAME_E_PASSE_BATALHA.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/16_SERVICOS_WEB_LOJA_INGAME_E_PASSE_BATALHA.md) | **Pendente** | Loja Web (Black Cloud Market), Daeva Pass (4.5), Roupeiro (Wardrobe) e Presença Diária. |
| **17** | [17_AGENDAMENTOS_CRON_EVENTOS_E_SIEGE_GUERRA.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/17_AGENDAMENTOS_CRON_EVENTOS_E_SIEGE_GUERRA.md) | **Pendente** | Agendador Cron, Sieges de Fortalezas, Assalto Balaur, Bases, Vórtices e Raides Mundiais. |
| **18** | [18_ARENAS_CAMPOS_BATALHA_E_AUTOGROUP.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/18_ARENAS_CAMPOS_BATALHA_E_AUTOGROUP.md) | **Pendente** | Matchmaking AutoGroup, Arenas (Discipline 1v1, Chaos FFA, Glory), Dreadgion e Tiarkh. |
| **19** | [19_SISTEMAS_ADMIN_ANTIHACK_E_MONITORAMENTO.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/19_SISTEMAS_ADMIN_ANTIHACK_E_MONITORAMENTO.md) | **Pendente** | Toolkit de GM, Punições (Prisão, Mute, Ban), Anti-Hack nativo e Monitoramento de Carga. |
| **20** | [20_MAPEAMENTO_COMPLETO_PACOTES_CM_SM_4_5.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/20_MAPEAMENTO_COMPLETO_PACOTES_CM_SM_4_5.md) | **Pendente** | Dicionário Exaustivo de Opcodes e Payloads de TODOS os pacotes CM (189+) e SM (239+). |
| **21** | [21_VALIDACAO_AUTONOMA_TESTES_E_DEPLOY.md](file:///d:/AION%20RUST/AionEMU/AionEMU/PLANO-DESENVOLVIMENTO/21_VALIDACAO_AUTONOMA_TESTES_E_DEPLOY.md) | **Pendente** | Protocolo Autônomo de Testes do Agente: Execução do cliente, Wireshark, debug e deploy. |


---

## 5. Como o Agente de IA Deve Operar
 
1. **Consulta Obrigatória**: Antes de iniciar qualquer tarefa ou alteração de código, o agente deve consultar este `CONTEXT.md` e a etapa correspondente em `PLANO-DESENVOLVIMENTO/`.
2. **Referência Cruzada com Java 4.8**: Sempre inspecionar a implementação correspondente no `JAVA EMU - 4.8 RETAIL` para obter os nomes de variáveis, pacotes, sequências de chamadas e lógicas de negócios consagradas.
3. **Validação Autônoma**: O agente tem a obrigação de testar suas alterações:
   - Rodar `cargo check` e `cargo test`.
   - Iniciar os serviços do emulador Rust.
   - Executar o cliente ou simular conexões com scripts/bots.
   - Analisar logs e capturas de pacotes.
   - Corrigir falhas até que o fluxo funcione de ponta a ponta.
4. **Atualização da Pasta de Deploy**: Ao validar o funcionamento de novas features, rodar `scripts\publicar_deploy.ps1` para sincronizar os executáveis e dados na pasta `deploy/`.
5. **Versionamento Contínuo Obrigatório no GitHub**:
   - **Regra Mandatória**: O agente NUNCA deve esquecer de versionar no GitHub após cada progresso ou correção bem-sucedida.
   - Realizar `git add .`, gerar um commit descritivo e detalhado (`git commit -m "feat/fix: detalhes da mudança"`) e enviar com `git push` para o repositório oficial [https://github.com/kamidaki/aion-classic-rust](https://github.com/kamidaki/aion-classic-rust).
   - Isso garante rastreabilidade total e histórico seguro para rollbacks imediatos a qualquer momento.
6. **Atualização do Contexto**: Ao concluir uma etapa ou solucionar um bug significativo, o agente deve atualizar a tabela de status deste `CONTEXT.md` e documentar as lições aprendidas.

