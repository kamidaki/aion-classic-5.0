# Ferramentas e Parsers XML - Aion Classic 5.0

Este diretório contém os scripts utilitários e pipelines de extração, sincronização e conversão de dados entre os arquivos brutos do cliente oficial Aion Classic 5.0 e o emulador Java (`game-server` e `EMULADOR FINAL`).

---

## 1. `parse_quests_50.py` - Pipeline de Extração e Integração de Missões 5.0

### Visão Geral
Script automatizado responsável por extrair 100% das missões do cliente Aion Classic 5.0, gerar/atualizar o banco de dados estático de missões (`quest_data.xml`), criar os scripts de missões por mapa (`quest_script_data/*.xml`), implementar os Handlers Java para todas as Missões de Campanha (`category="MISSION"`), validar contra os esquemas XSD oficiais e sincronizar automaticamente entre as duas instâncias do servidor.

### Arquivos de Origem (Client 5.0)
- `Data/Quest/quest.xml`: Definição de todas as 6.124 missões do cliente (nível, raça, classe, recompensas, itens requeridos, etc.).
- `Strings/strings/client_strings_quest.xml` e correlatos: Títulos e descrições das missões em texto legível.
- `Data/Items/client_items.xml`: Mapeamento de nomes de itens para seus respectivos `item_id`.
- `Data/Npc/client_npcs.xml`: Mapeamento de nomes de NPCs e monstros para seus respectivos `npc_id` e nomes reais.
- `quest_monster.csv` e `quest_script_monster.csv`: Mapeamento de drops vinculados e monstros de caça.

### Arquivos de Destino Gerados / Atualizados
1. **`quest_data.xml`**:
   - Localização: `data/static_data/quest_data/quest_data.xml`
   - Contém 9.465 missões (6.124 oficiais 5.0 atualizadas/adicionadas + 3.341 missões do servidor preservadas).
   - Segue 100% a sequência de tags exigida por `quest_data.xsd`:
     `collect_items` -> `inventory_items` -> `rewards` -> `bonus` -> `extended_rewards` -> `quest_drop` -> `quest_kill` -> `start_conditions` -> `class_permitted` -> `gender_permitted` -> `quest_work_items` -> `[class]_selectable_reward`.
   - Conversão de `combineskill` de texto para `xs:int` conforme `QuestService.java` (`any` -> `-1`, `weaponsmith` -> `40002`, `armorsmith` -> `40003`, etc.).
   - Conversão de strings de título (`light_title45`, `dark_title27`) para `xs:int`.

2. **Scripts de Zona (`quest_script_data/*.xml`)**:
   - `telos.xml`: 18 missões (Telos / Início do Revenant)
   - `tiamaranta_mesa.xml`: 146 missões (Tiamaranta's Eye / Mesa)
   - `laphsaran.xml`: 131 missões (Laphsaran)
   - `teva.xml`: 58 missões (Teva)
   - `apheta_beluslan.xml`: 16 missões (Apheta Beluslan)
   - `dranium_battlefield.xml`: 10 missões (Dranium Battlefield)
   - `dokkaebi_realm.xml`: 10 missões (Dokkaebi Realm)
   - `balic_treasury.xml`: 36 missões (Balic Treasury)
   - Validados 100% contra `quest_script_data.xsd`.

3. **Handlers Java de Missões de Campanha (`data/handlers/quest/**/*.java`)**:
   - 190 classes Java geradas no formato `_<id><CamelCaseName>.java` estendendo `AbstractQuestHandler`.
   - Comentários para cada NPC registrado indicando ID e Nome Real (`// <id>: <nome_npc>`).
   - Sobrescrita de métodos `register()`, `onDialogEvent()`, `onKillEvent()`, `onEnterWorldEvent()`, `onLevelChangedEvent()`.
   - Compilação 100% validada via `javac` com zero erros.

### Como Executar
```bash
python parse_quests_50.py
```

---

## 2. `extract_50_spawns_and_walkers.py` - Extração de Spawns e Rotas (Walkers) 5.0

### Visão Geral
Extrai dados de posicionamento de NPCs e monstros (spawns fixos e rotas de patrulha/walkers) dos dados brutos dos mapas do cliente 5.0 e converte para a arquitetura estática do emulador.

### Arquivos de Origem (Client 5.0)
- Níveis/Mapas em `Levels/`: Arquivos de colocação de entidades, missões e rotas (`Mission.xml`, `mission.xml`, `Objects.xml`, waypoints de rotas de IA).

### Arquivos de Destino Gerados / Atualizados
1. **Spawns de NPCs e Instâncias**:
   - `data/static_data/spawns/Npcs/...`: Spawns organizados por zonas de mundo aberto (ex: `telos`, `laphsaran`, `tiamaranta_mesa`).
   - `data/static_data/spawns/Instances/...`: Spawns de instâncias e campos de batalha.
   - Cada spawn inclui comentários com o nome real do NPC (`<!-- <nome_npc> -->`).
2. **Rotas de Patrulha (`npc_walker/walker_data.xml`)**:
   - Contém todos os nós (`routes` -> `route` -> `points` -> `point`) com coordenadas `x`, `y`, `z`, tempo de espera (`rest_time`) e velocidade.
   - Referenciados nos spawns correspondentes através do atributo `walker_id`.

### Como Executar
```bash
python extract_50_spawns_and_walkers.py
```

---

## 3. Sincronização Automática

Ambos os scripts realizam a sincronização bidirecional/espelhamento automático entre:
- Código Fonte do Emulador: `Código Fonte - Emulador/game-server`
- Servidor Final: `Emulador - Produto Final/GameServer`

Garantindo que qualquer alteração ou reexecução dos parsers mantenha as duas instâncias em perfeita paridade.
