# GameServer GameForge (GSID 1) — Aion Classic 5.0 EU

Este diretório contém o código-fonte Java 25 LTS do **GameServer GameForge**, responsável pela modalidade que reproduz com fidelidade 1:1 a **experiência oficial do Aion Classic 5.0 europeu (Gameforge)**.

---

## 1. Identificação e Parâmetros de Execução

| Parâmetro | Valor Configurado |
| :--- | :--- |
| **Identificador (GSID)** | `1` |
| **Porta de Jogo (TCP)** | `7777` |
| **Porta de Telemetria / Gestão** | `2130` |
| **Schema de Banco de Dados** | `aionclassic_gs` (86 tabelas) |
| **Diretório de Distribuição** | `Emulador - Produto Final/GameServer-GameForge` |
| **Alocação de Memória JVM** | `-Xms1G -Xmx4G` |

---

## 2. Regras Inegociáveis de Isolamento Arquitetural

> [!CAUTION]
> **REGRAS OBRIGATÓRIAS E INEGOCIÁVEIS:**
> 1. **Isolamento Absoluto:** Este GameServer é um servidor 100% autônomo e independente do `game-server-remake` e do `game-server-battleroyale`.
> 2. **Validação Prévia Obrigatória:** Antes de qualquer alteração ou leitura de código neste diretório, deve-se validar explicitamente se a intervenção solicitada é para o servidor GameForge.
> 3. **Proibição de Consulta Cruzada:** NUNCA tente resolver um problema neste GameServer consultando arquivos de outros GameServers, exceto quando solicitado expressamente pelo usuário.
> 4. **Consulta ao Usuário:** Se houver dúvida ou se o usuário não tiver especificado o servidor alvo, pergunte SEMPRE antes de ler ou alterar qualquer arquivo.
> 5. **Auditoria de Conclusão:** Ao finalizar uma tarefa, confirme se não alterou ou excluiu arquivos de outros GameServers sem autorização.
> 6. **Fidelidade 1:1 ao Oficial:** Toda correção ou implementação nesta instância deve ser validada contra o **servidor oficial Gameforge**, trazendo comprovação via **Ghidra** (binários x64 em `bin64`), **Wireshark** (capturas oficiais `.pcap`) e capturas de tela in-game.
