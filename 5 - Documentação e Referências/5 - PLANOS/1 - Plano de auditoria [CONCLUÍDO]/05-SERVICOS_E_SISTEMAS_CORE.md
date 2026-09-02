# 05 - Serviços e Sistemas Core: Aion Classic 5.0 EU

## 1. Auditoria dos Serviços Existentes

### 1.1 Limpeza de Código Morto
- **Remoção de Arquivos Residuais**:
  - Excluir `1 - Código Fonte [Emulador]\GameServer\src\com\aionemu\gameserver\services\ClassChangeService.java.bak`.
- **Eliminação de Soluções Temporárias (Workarounds)**:
  - Verificar métodos com `// TODO workaround` ou fallbacks fictícios que ignoram templates XML.

### 1.2 Serviço de Criação e Inicialização de Personagens (`PlayerService`)
- Garantir suporte a todas as 13 classes oficiais da versão 5.0:
  1. `WARRIOR` (`GLADIATOR`, `TEMPLAR`)
  2. `SCOUT` (`ASSASSIN`, `RANGER`)
  3. `MAGE` (`SORCERER`, `SPIRIT_MASTER`)
  4. `PRIEST` (`CLERIC`, `CHANTER`)
  5. `MONK` (`THUNDERER`)
  6. `MARTIAL_ARTIST` (`BATTLE_MASTER`)
  7. `LUMINESS` (`PHOENIX`)
  8. `REAPER` (`SOUL_REAPER`)
- Validação estrita dos kits de equipamentos iniciais: Cada classe deve receber itens cadastrados em `player_initial_data.xml` que tenham templates válidos em `items.xml`.

### 1.3 Gerenciamento de Identificadores Únicos (`IDFactory`)
- A geração de `ObjectId` para entidades (jogadores, itens, npcs, legiões, correios) deve ser estritamente atômica e consistente com a persistência no banco MySQL/MariaDB.
- Prevenção contra estouro de limites ou colisões de ID entre entidades voláteis e persistentes.

### 1.4 Serviços de Batalha, Habilidades e Efeitos
- `SkillEngine` e `SkillLearnService`:
  - Carregamento correto das árvores de habilidades 5.0 para as novas classes.
  - Verificação de cooldowns em `S_LOAD_SKILL_COOLTIME` e `S_LOAD_ITEM_COOLTIME`.
- `DropService` e `DropDistributionService`:
  - Distribuição em grupo e loot individual sincronizado com os eventos de loot capturados nos PCAPs.
