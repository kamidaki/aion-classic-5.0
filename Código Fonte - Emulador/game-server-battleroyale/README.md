# GameServer BattleRoyale (GSID 3) — Aion Classic 5.0 EU

Este diretório contém o código-fonte Java 25 LTS do **GameServer BattleRoyale**, responsável pela modalidade competitiva de sobrevivência, zonas seguras dinâmicas, tempestades de éter e combate em arenas.

---

## 1. Identificação e Parâmetros de Execução

| Parâmetro | Valor Configurado |
| :--- | :--- |
| **Identificador (GSID)** | `3` |
| **Porta de Jogo (TCP)** | `7779` |
| **Porta de Telemetria / Gestão** | `2132` |
| **Schema de Banco de Dados** | `aionclassic_gs3` (86 tabelas) |
| **Diretório de Distribuição** | `Emulador - Produto Final/GameServer-BattleRoyale` |
| **Alocação de Memória JVM** | `-Xms1G -Xmx4G` |

---

## 2. Regras Inegociáveis de Isolamento Arquitetural

> [!CAUTION]
> **REGRAS OBRIGATÓRIAS E INEGOCIÁVEIS:**
> 1. **Isolamento Absoluto:** Este GameServer é um servidor 100% autônomo e independente do `game-server-gameforge` e do `game-server-remake`.
> 2. **Validação Prévia Obrigatória:** Antes de qualquer alteração ou leitura de código neste diretório, deve-se validar explicitamente se a intervenção solicitada é para o servidor BattleRoyale.
> 3. **Proibição de Consulta Cruzada:** NUNCA tente resolver um problema neste GameServer consultando arquivos de outros GameServers, exceto quando solicitado expressamente pelo usuário.
> 4. **Consulta ao Usuário:** Se houver dúvida ou se o usuário não tiver especificado o servidor alvo, pergunte SEMPRE antes de ler ou alterar qualquer arquivo.
> 5. **Auditoria de Conclusão:** Ao finalizar uma tarefa, confirme se não alterou ou excluiu arquivos de outros GameServers sem autorização.
> 6. **Fidelidade de Protocolo e Evidências:** Toda mecânica deste servidor deve ser testada em execução real com imagens comprobatórias, respeitando os padrões de rede oficiais (Ghidra e Wireshark) na camada de comunicação.

