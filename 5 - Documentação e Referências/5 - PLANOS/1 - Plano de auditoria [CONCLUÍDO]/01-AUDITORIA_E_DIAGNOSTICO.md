# 01 - Auditoria e Diagnóstico Completo: Aion Classic 5.0 EU

## 1. Visão Geral da Auditoria
Esta auditoria avaliou a conformidade técnica, integridade do protocolo de rede, fidelidade das estruturas de dados e arquitetura de execução do emulador Java multi-módulo (`LoginServer`, `GameServer`, `ChatServer`) frente às capturas oficiais de tráfego de rede (Wireshark PCAPs) e aos binários oficiais do cliente Aion Classic 5.0 EU (`D:\GameForge\aionclassic`).

---

## 2. Diagnóstico Módulo por Módulo

### 2.1 GameServer: Camada de Rede e Protocolo
- **Opcodes de Cliente com Desalinhamento Crítico**:
  - `CM_LEVEL_READY`: Existência do opcode incorreto `0x0E2` (decOp `0x0010`) marcado como principal, enquanto o cliente oficial 5.0 envia exclusivamente `0xEB` (decOp `0x0019`, C_LEVEL_READY, 0 bytes).
  - `CM_READ_EXPRESS_MAIL`: Registrado com opcode de fio `0x150` (decOp `0x00A2`), mas o cliente oficial envia decOp `0x0150` (opcode de fio `0x0222`) mais de 1.400 vezes como parte do ciclo de atualização de estado contínuo.
  - **Opcodes de Cliente Faltantes**:
    - `0x0002` (Fio `0x00F0`, len 1)
    - `0x00A3` (Fio `0x0151`, len 1)
    - `0x00B5` (Fio `0x014F`, len 20)
    - `0x00B6` (Fio `0x014C`, len 0) - `CM_RECIPE_LIST`
    - `0x00F3` (Fio `0x0181`, len 5)
    - `0x0101` (Fio `0x01F3`, len 6) - `CM_GLOBAL_TRADE_SALESLOG`
    - `0x0150` (Fio `0x0222`, len 5) - heartbeat / motion state
    - `0x0225` (Fio `0x02DF`, len 1)
    - `0x0326` (Fio `0x03DC`, len 7)
    - `0xFFFC` (Fio `0x00F6`, len 4)
    - `0xFFFD` (Fio `0x00F7`, len 4)
  - **Poluição de Aliases e Código Legado**:
    - Diversos pacotes possuem até 3 registros redundantes de épocas legadas (ex: 2.8, 4.8) com opcodes não decodificados que podem colidir com pacotes legítimos da 5.0.

### 2.2 GameServer: Pacotes do Servidor (ServerPacketsOpcodes)
- **38 Opcodes Oficiais Faltantes no Enum do Servidor**:
  - `0x000D`, `0x005F`, `0x00A4` (`S_LOAD_GATHERCOMBINE_COOLTIME`), `0x00BC` (`S_LOAD_PVP_ENV`), `0x00D7` (`S_SKILL_PENALTY_STATUS`), `0x00D8` (`S_SKILL_PENALTY_STATUS_OTHER`), `0x0102`, `0x0105`, `0x0110`, `0x0114`, `0x0135`, `0x0148`, `0x0170`, `0x0173`, `0x0177`, `0x017F`, `0x0181`, `0x0182`, `0x0183`, `0x018C`, `0x0191`, `0x0197`, `0x019D` (Variáveis de Ambiente / PvP World), `0x019F` (Pass/Storybook), `0x01A8`, `0x01AA`, `0x01AB`, `0x01AC`, `0x01AF`, `0x01B3`, `0x01B5`, `0x01BA`, `0x01BD`, `0x01C0`, `0x01C2`, `0x01C5`.
- **Inversão de Pacote em `CM_LEVEL_READY`**:
  - `S_INVISIBLE_LEVEL` (`0x0043`, 7 bytes) foi confundido com `S_CUSTOM_ANIM` (`0x0093`, 19 bytes). No código atual, `CM_LEVEL_READY` dispara `S_CUSTOM_ANIM` achando que seu opcode era `0x43`, enviando uma estrutura divergente para o cliente.

### 2.3 Camada de Serviços e Lógica de Domínio
- Arquivos órfãos e lixo de build (`ClassChangeService.java.bak`).
- Logging síncrono e intensivo no hot path de rede: `AionPacketHandler` e `AionServerPacket` executam `log.info` formatado com string formatting em cada pacote de entrada e saída. Sob carga real, isso estrangula a performance e satura o subsistema de I/O em disco.

### 2.4 Dados Estáticos XML e Compatibilidade 5.0
- Templates das 13 classes do Aion 5.0 (Warrior, Scout, Mage, Priest, Monk/Thunderer, Martial Artist/Battle Master, Luminess/Phoenix, Reaper/Soul Reaper).
- Necessidade de conferir se todos os itens iniciais de criação de personagem existem nos XMLs sem fallback hardcoded.
