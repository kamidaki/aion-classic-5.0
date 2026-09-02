# 08 - Concorrência, Performance e Otimização: Aion Classic 5.0 EU

## 1. Eliminação de Gargalos de I/O em Hot Path
- **Logging Excessivo no Pipeline de Pacotes**:
  - `AionPacketHandler.java`: Atualmente executa `log.info` com formatação de strings em cada pacote recebido do cliente.
  - `AionServerPacket.java`: Atualmente executa `log.info` em cada pacote enviado pelo servidor.
  - **Solução**: Converter esses logs para nível `log.debug` condicionado a flags de configuração (`NetworkConfig.DISPLAY_PACKETS`), evitando a saturação da thread de rede e do disco sob carga.

---

## 2. Gerenciamento de Concorrência e Pools de Threads
- **Netty e I/O de Rede**:
  - Garantir que decodificadores e enquadradores liberem ByteBuffers diretamente sem vazamentos de memória (ByteBuf release / DirectBuffer cleanup).
  - Execução de pacotes pesados (`runImpl`) despachada para o pool de workers (`ThreadPoolManager`) para não bloquear a thread do selector do Netty.
- **Estruturas de Coleções Concorrentes**:
  - Acesso ao mapa de protótipos de pacotes (`AionPacketHandler`): deve ser imutável após inicialização ou usar `ConcurrentHashMap`.
  - Gerenciamento de jogadores no `World`: Utilizar particionamento espacial de mapas e zonas para broadcast seletivo, evitando iterações globais em loops de visualização.

---

## 3. Banco de Dados e Pool de Conexões
- Assegurar fechamento de `ResultSet`, `PreparedStatement` e `Connection` em blocos `try-with-resources` em todos os DAOs de `com.aionemu.gameserver.dao`.
- Ajustar pool HikariCP / Commons-DBCP para evitar timeout sob concorrência de múltiplos jogadores salvando inventário e status simultaneamente.
