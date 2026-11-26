# Geo & Nav Builder — Aion Classic 5.0 (Official Client)

Ferramenta oficial do projeto **[Aion Classic 5.0 — Lost Academy Group](https://github.com/kamidaki/aion-classic-5.0/)** para extrair e compilar dados geográficos (**Geodata**) e malhas de navegação 3D (**NavMesh**) diretamente a partir do **Cliente Oficial do Aion Classic 5.0**.

Ao contrário de ferramentas legadas que geravam apenas `.geo`/`.png` ou dependiam de exportação manual e geração de `.nav` via **Blender**, este gerador produz **tanto os arquivos de Geodata (`models.mesh`, `*.geo`, `*.png`) quanto as malhas de navegação (`*.nav`) de forma 100% nativa em Java com Recast4j** — **sem precisar de Blender** e **fundamentalmente mais leve** na geração e no consumo em execução pelo emulador.

---

## Sumário

1. [Diferenciais: Geração Nativa sem Blender e Mais Leve](#diferenciais-geração-nativa-sem-blender-e-mais-leve)
2. [O que a Ferramenta FAZ e O que NÃO FAZ](#o-que-a-ferramenta-faz-e-o-que-não-faz)
3. [Pré-requisitos](#pré-requisitos)
4. [Como Compilar e Gerar os Arquivos](#como-compilar-e-gerar-os-arquivos)
5. [Onde Instalar e Configurar no Emulador](#onde-instalar-e-configurar-no-emulador)
6. [Quais Códigos do Emulador Leem Estes Arquivos](#quais-códigos-do-emulador-leem-estes-arquivos)
7. [Especificação Técnica do `.nav` e Parâmetros Recast4j](#especificação-técnica-do-nav-e-parâmetros-recast4j)
8. [Créditos e Referências Técnicas](#créditos-e-referências-técnicas)

---

## Diferenciais: Geração Nativa sem Blender e Mais Leve

1. **Zero dependência do Blender para gerar `.nav`:**
   - Todo o pipeline roda diretamente na JVM lendo os arquivos `.pak` do cliente oficial e invocando o **Recast4j 1.5.7** (`RecastBuilder`) em Java puro.
   - Não exige exportação intermediária de mapas para `.obj`/`.fbx`/`.blend`, scripts manuais no Blender nem conversão externa de coordenadas.
2. **Mais leve na geração:**
   - **Buffers primitivos sem boxing (`FloatList` / `IntList`):** evita a sobrecarga de memória de coleções `ArrayList<Float>`/`ArrayList<Integer>` em mapas extensos.
   - **Recorte espacial por tile (*spatial binning* $O(N)$):** particiona os triângulos em tiles (`256 × 256` células) antes de rodar o Recast por tile em paralelo, com controle de concorrência (`availableProcessors() / 2` no estágio de `.nav`) para evitar picos excessivos de RAM.
   - **Compactação e deduplicação de malhas e terrenos:** remove vértices/faces redundantes em `models.mesh`, mescla malhas idênticas (`caminho1|caminho2`), deduplica heightmaps/materiais idênticos entre mapas (`id1,id2.png`) e comprime PNGs com `oxipng` embutido.
   - **Execução incremental:** arquivos `.geo`, `.nav` e `.png` já existentes no diretório de saída são preservados e pulados automaticamente.
3. **Mais leve no emulador em produção:**
   - Os arquivos `.nav` utilizam formato binário compacto *little-endian* com buffer único de vértices compartilhados + triângulos e adjacências já pré-calculadas (sem necessidade de reconstrução pesada no servidor).
   - No GameServer (`NavData`), os `.nav` são carregados **sob demanda** apenas quando um jogador entra no mapa, com cache LRU limitado a 15 mapas e limpeza automática após 5 minutos sem jogadores.
   - Na distribuição atual do **GameForge GSID 1**, todo o conjunto em `data/geo/` (210 arquivos, incluindo `models.mesh` com ~62,3 MB) ocupa cerca de **149 MB**, e os **233** arquivos em `data/nav/` somam cerca de **471 MB**.

---

## O que a Ferramenta FAZ e O que NÃO FAZ

### O que ela FAZ

- **Leitura direta dos pacotes do cliente (somente leitura):**
  - Suporta arquivos `.pak` em formato ZIP padrão e PAK ofuscado do Aion, aplicando prioridade automática de patch (`z_Level.pak` / `z_*.pak` sobre `Level.pak`).
  - Lê lista de mapas em `Data/World/World.pak` (`worldid.xml`) ou arquivo XML externo via `-w` (como o `world_maps.xml` do emulador).
  - Lê materiais em `Data/Material/Material.pak` (`materials.xml`) e endereços de casas em `Data/Housing/Housing.pak` (`client_housing_address.xml`, opcional).
  - Lê dados de cada nível em `Levels/<mapa>/`: `leveldata.xml`, `terrain/land_map.h32`, `mission_mission0.xml`, `brush.lst` / `brush.lstd` e `objects.lst`.
  - Lê malhas `.cgf` e `.cga` em `Levels/common/`, `Levels/idabpro/` e `Objects/`.
- **Geração de Geodata (`out/geo/`):**
  - `models.mesh`: geometria das malhas compactada e deduplicada com `materialId` e flags de colisão (`CollisionIntention`). Para portas (`Door`), também extrai a pose aberta no frame `999999` com sufixo `_state2`.
  - `<worldId>.geo`: instâncias posicionadas por mapa (matriz de rotação 3×3, posição, escala, tipo `EntryType` e IDs: `brushes`, vegetação, `PlaceableObject`, `AbyssArtifacts`, `AbyssShield`, `AbyssDoor`, bancadas de craft, `BasicEntity` com `EventType`, `Door` fechado/aberto, `TownObject` e `HousingBuilding`).
  - `<worldId[,...]>.png`: heightmaps de terreno em PNG 16-bit escala de cinza (compartilhados entre mapas de terreno idêntico e otimizados via `oxipng`).
  - `<worldId[,...]>_materials.png`: mapas de materiais de terreno em PNG 8-bit (por padrão, apenas materiais associados a skills e `mat_abyss_castle_shield`, ou todos com `-am`).
- **Geração de NavMesh (`out/nav/`):**
  - `<worldId>.nav`: combina o heightfield do terreno com as malhas de colisão navegável (`PHYSICAL`, `WALK`, `DOOR`, `PHYSICAL_SEE_THROUGH`), constrói a NavMesh *tiled* via Recast4j, filtra centróides fora dos limites lógicos do tile, quantiza vértices, reconstrói adjacências entre tiles e grava diretamente no eixo Aion `(X, Y, Z)` com *winding* CCW.

### O que ela NÃO FAZ

- **Não gera a grade nativa oficial `path.dat` (`data/native-path/`):**
  - Arquivos `*.dat` consumidos por [`PathDatService`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/lostacademy/nativepath/PathDatService.java) são grades nativas extraídas do cliente oficial, não geradas por este builder.
  - **Como os dois sistemas convivem no emulador:** quando `gameserver.geodata.pathdat.enable = true` e o mapa possui arquivo em `data/native-path/`, a perseguição e o retorno de NPCs terrestres usam a grade `path.dat` (apoiada pelo `GeoService` em `getTerrainHeight` e `canSee`). Os arquivos `.nav` gerados aqui atendem **todos os mapas sem `path.dat`**, verificações de superfície/movimento no `NavService` (como `SpawnEngine`, `WalkManager`, `FearEffect`, `DashEffect`, `BackDashEffect`, `PulledEffect`, `StumbleEffect`, `OpenAerialEffect`, `AttackEventHandler`) e assumem todo o pathfinding caso `pathdat.enable` seja `false`.
- **Não modela estados dinâmicos dentro do `.nav`:**
  - A malha `.nav` é estática (terreno + geometria sólida). Portas abertas/fechadas, escudos e objetos spawnáveis em tempo real são resolvidos pelo `GeoService` sobre o `.geo` (por exemplo, `canSee` e `getClosestCollision` em conjunto com `NavService`).
- **Não processa entidades animadas além de portas:**
  - Elevadores, dirigíveis (*airships*), plataformas móveis e `BasicEntity` em formato `.cga` são ignorados na etapa de entidades; animações esqueléticas `.caf`/`.cal` não são processadas.
- **Não utiliza Blender nem exporta `.obj`/`.fbx`/`.blend`:**
  - Para abrir, visualizar ou editar mapas e modelos 3D visualmente no Blender, utilize os plugins em [`../Blender - Plugins/`](../Blender%20-%20Plugins/).
- **Não edita arquivos do cliente nem gera XMLs do emulador:**
  - Opera exclusivamente em modo somente leitura sobre o cliente e não gera `world_maps.xml`, XMLs de spawn, zonas, drops ou missões.

---

## Pré-requisitos

- **Java Development Kit (JDK) 21 ou superior** (recomendado **JDK 25 LTS**, o mesmo utilizado para compilar o emulador).
- **Apache Maven 3.9+** (para compilar o projeto e copiar as dependências em `target/lib/`).
- **Cliente Oficial Aion Classic 5.0** completo em disco local (contendo `Data/`, `Levels/` e `Objects/`).

---

## Como Compilar e Gerar os Arquivos

### 1. Compilar o Projeto

Execute na pasta `Ferramentas e Documentos/Geo and Nav Builder - Official Client` (ou apontando o `-f` para o `pom.xml`):

```powershell
mvn clean package
```

O Maven gerará em `target/`:
- `target/geobuilder.jar`
- `target/lib/` (dependências `recast`, `detour`, `jdom2`, `jcommander`)
- `target/oxipng/` (binários `oxipng.exe` / `oxipng` usados na compressão lossless dos `.png` de terreno)

### 2. Gerar Geodata e NavMesh para Todos os Mapas

```powershell
java -Xmx8G -jar target/geobuilder.jar "<caminho-do-cliente-aion-classic>"
```

Por padrão, a saída será gravada em `./out/geo/` e `./out/nav/`.

### 3. Exemplos Práticos de Execução

**Gerar usando o `world_maps.xml` do GameServer GameForge (`GSID 1`) como filtro de mapas:**

```powershell
java -Xmx8G -jar target/geobuilder.jar "<caminho-do-cliente-aion-classic>" `
  -w "../../Código Fonte - Emulador/game-server-gameforge/data/static_data/world_maps.xml" `
  -o "./out"
```

**Gerar apenas mapas específicos (ex.: Sanctum `110010000` e Pandaemonium `120010000`):**

```powershell
java -Xmx4G -jar target/geobuilder.jar "<caminho-do-cliente-aion-classic>" `
  -lvl 110010000 -lvl 120010000 `
  -o "./out-parcial"
```

> [!WARNING]
> **Cuidado ao usar `-lvl` com `models.mesh`:**
> O arquivo `out/geo/models.mesh` contém apenas as malhas referenciadas pelos mapas processados naquela execução. Se você rodar com `-lvl` para gerar poucos mapas, gere em uma pasta separada (`-o "./out-parcial"`) para **não sobrescrever** um `models.mesh` completo já instalado no servidor.

> [!NOTE]
> **Execução incremental:**
> Se `<worldId>.geo`, `<worldId>.nav` e `<worldId>.png` já existirem na pasta `-o`, a ferramenta pula esses arquivos automaticamente. Para regerar um mapa específico do zero, apague os arquivos antigos daquele mapa na pasta de saída antes de executar novamente.

### Parâmetros de Linha de Comando (`AionLevelsProcessor`)

| Argumento | Obrigatório | Padrão | Descrição |
| :--- | :---: | :--- | :--- |
| `<client path>` | Sim | — | Diretório raiz do Cliente Oficial Aion Classic 5.0. |
| `-lvl` | Não | Todos os mapas | Restringe a geração aos IDs de mapa informados (pode ser repetido, ex.: `-lvl 110010000 -lvl 110020000`). |
| `-w` | Não | `worldid.xml` do cliente | Caminho para `world_maps.xml` do emulador ou `WorldId.xml` customizado. |
| `-o` | Não | `./out` | Pasta de destino (serão criadas as subpastas `geo/` e `nav/`). |
| `-am` | Não | `false` | Gera todos os materiais de terreno em `*_materials.png` (sem `-am`, inclui apenas materiais com skill e `mat_abyss_castle_shield`). |
| `-do` | Não | `false` | Desativa a otimização `oxipng` ao salvar os `.png` de terreno. |
| `-dc` | Não | `false` | Desativa a compactação de malhas (remoção de vértices não usados/duplicados e faces degeneradas/duplicadas). |
| `-ds` | Não | `false` | Desativa a ordenação de vértices/faces das malhas. |
| `-v` | Não | `false` | Ativa logs detalhados (*verbose*). |

---

## Onde Instalar e Configurar no Emulador

Este repositório concentra o desenvolvimento Open Source exclusivamente no **GameServer 1 — GameForge (`GSID 1`)**.

### Destino dos Arquivos Gerados

| Conteúdo Gerado | Destino no Código-Fonte | Destino no Produto Final |
| :--- | :--- | :--- |
| `out/geo/*` (`models.mesh`, `*.geo`, `*.png`) | [`Código Fonte - Emulador/game-server-gameforge/data/geo/`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/data/geo/) | [`Emulador - Produto Final/GameServer-GameForge/data/geo/`](../../Emulador%20-%20Produto%20Final/GameServer-GameForge/data/geo/) |
| `out/nav/*.nav` | [`Código Fonte - Emulador/game-server-gameforge/data/nav/`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/data/nav/) | [`Emulador - Produto Final/GameServer-GameForge/data/nav/`](../../Emulador%20-%20Produto%20Final/GameServer-GameForge/data/nav/) |

### Configuração (`geodata.properties`)

Arquivo de configuração:
- Código-fonte: [`Código Fonte - Emulador/game-server-gameforge/config/main/geodata.properties`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/config/main/geodata.properties)
- Produto Final: [`Emulador - Produto Final/GameServer-GameForge/config/main/geodata.properties`](../../Emulador%20-%20Produto%20Final/GameServer-GameForge/config/main/geodata.properties)

Principais propriedades lidas por [`GeoDataConfig.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/configs/main/GeoDataConfig.java):

```properties
# Geodata (data/geo/)
gameserver.geodata.enable = true
gameserver.geodata.cansee.enable = true
gameserver.geodata.fear.enable = true
gameserver.geodata.npc.move = true
gameserver.geodata.materials.enable = true
gameserver.geodata.materials.showdetails = false
gameserver.geodata.shields.enable = true

# NavMesh (data/nav/)
gameserver.geodata.nav.enable = true
gameserver.geodata.nav.dir = data/nav/
gameserver.geodata.forced_move.nav_fallback = true

# Grade oficial path.dat (opcional; atua em conjunto com Geo/Nav)
gameserver.geodata.pathdat.enable = true
gameserver.geodata.pathdat.dir = data/native-path/
```

---

## Quais Códigos do Emulador Leem Estes Arquivos

### 1. Inicialização e Configuração

| Arquivo no Emulador | Responsabilidade |
| :--- | :--- |
| [`GameServer.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/GameServer.java#L97-L101) | Inicializa `GeoService.getInstance()` em paralelo na subida e chama `NavService.getInstance().initializeNav()`. |
| [`GeoDataConfig.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/configs/main/GeoDataConfig.java) | Mapeia todas as propriedades de `config/main/geodata.properties`. |

### 2. Leitores e Consumidores de `data/geo/` (`models.mesh`, `*.geo`, `*.png`)

| Arquivo no Emulador | Responsabilidade |
| :--- | :--- |
| [`GeoWorldLoader.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/GeoWorldLoader.java) | Carrega heightmaps/materiais `*.png` (`loadTerrains`), abre `data/geo/models.mesh` via `FileChannel` mapeado (`loadMeshes`) e instancia `data/geo/<worldId>.geo` (`loadWorld`), registrando portas, casas, cidades, objetos e zonas de materiais. |
| [`GeoService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/world/geo/GeoService.java) | Fachada pública do GeoEngine: `getZ`, `getValidGroundZ`, `getTerrainHeight`, `canSee`, `canPass`, `canPassPhysical`, `findMovementCollision`, estado de portas (`setDoorState`, `setHouseDoorState`), cidades (`updateTown`) e objetos colocáveis. |
| [`GeoMap.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/models/GeoMap.java) | Estrutura espacial por mapa (particionamento em chunks 256×256, `DespawnableNode` para portas/objetos dinâmicos e raycast contra terreno + BIHTree). |
| [`Terrain.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/models/Terrain.java) | Decodifica heightmap 16-bit (`2048f / 65536.0f`, passo de 2 m) e matriz de materiais de superfície para colisão e verificação de inclinação. |
| [`Mesh.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/scene/Mesh.java) & [`BIHTree.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/collision/bih/BIHTree.java) | Armazena vértices/índices lidos de `models.mesh` e acelera interseção de raios via BIH. |
| [`StaticDoorSpawnManager.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/spawnengine/StaticDoorSpawnManager.java) | Sincroniza o estado aberto/fechado das portas estáticas (`DOOR_STATE1` / `DOOR_STATE2`) no `GeoService`. |
| [`PathDatService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/lostacademy/nativepath/PathDatService.java) | Consulta `GeoService.getTerrainHeight` e `canSee` para complementar a grade `path.dat`. |

### 3. Leitores e Consumidores de `data/nav/` (`*.nav`)

| Arquivo no Emulador | Responsabilidade |
| :--- | :--- |
| [`NavData.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/lostacademy/nav/NavData.java) | Lê `<worldId>.nav` de `gameserver.geodata.nav.dir` em `ByteOrder.LITTLE_ENDIAN`, carrega sob demanda com cache LRU (`MAX_CACHED_MAPS = 15`) e descarrega mapas sem jogadores após 5 min de inatividade. |
| [`NavService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/lostacademy/nav/NavService.java) | Executa `navigateToTarget`, `navigateToLocation`, `canPullTarget` (linha reta + `GeoService.canSee`), `getNavSurfaceZ` (com fallback para `GeoService.getValidGroundZ`) e suavização pelo algoritmo *Funnel*. |
| [`NavHelper.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/lostacademy/nav/NavHelper.java) | Busca A* em heap binário sobre o grafo de triângulos `NavGeometry` (`ARBITRARY_LARGE_VALUE = 2500` iterações). |
| [`NavGeometry.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/geoEngine/scene/NavGeometry.java) | Representa cada triângulo do `.nav` compartilhando `sharedVertexBuffer` e referências diretas `edge1`/`edge2`/`edge3` para seus vizinhos. |
| [`CM_LEVEL_READY.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/network/aion/clientpackets/CM_LEVEL_READY.java), [`PlayerEnterWorldService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/services/player/PlayerEnterWorldService.java), [`PlayerLeaveWorldService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/services/player/PlayerLeaveWorldService.java), [`TeleportService.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/services/teleport/TeleportService.java) | Notificam `NavData` (`onPlayerEnterMap` / `onPlayerLeaveMap`) para pré-carregar assincronamente ou liberar a `.nav` do mapa ativo. |
| [`NpcMoveController.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/controllers/movement/NpcMoveController.java), [`WalkManager.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/ai/manager/WalkManager.java), [`AttackEventHandler.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/ai/handler/AttackEventHandler.java), [`SpawnEngine.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/spawnengine/SpawnEngine.java) | Movimentação de perseguição/retorno, caminhada aleatória, fuga de NPCs e correção vertical de spawns no solo via `NavService` + `GeoService`. |
| [`FearEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/FearEffect.java), [`DashEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/DashEffect.java), [`BackDashEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/BackDashEffect.java), [`PulledEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/PulledEffect.java), [`StumbleEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/StumbleEffect.java), [`OpenAerialEffect.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/src/com/aionemu/gameserver/skillengine/effect/OpenAerialEffect.java) | Efeitos de habilidade que consultam `NavService` para validar puxões (`canPullTarget`), rotas de fear e altura de superfície (`getNavSurfaceZ`). |
| [`GeoNavRegressionTest.java`](../../C%C3%B3digo%20Fonte%20-%20Emulador/game-server-gameforge/test/com/lostacademy/nav/GeoNavRegressionTest.java) | Suíte de testes unitários e de regressão do motor Geo/NavMesh. |

---

## Especificação Técnica do `.nav` e Parâmetros Recast4j

### Parâmetros de Geração (`AionLevelsProcessor.buildTiledNavMesh`)

- **Particionamento:** `PartitionType.MONOTONE` em tiles de `256 × 256` células
- **Resolução de voxel:** `cellSize = 0.4f`, `cellHeight = 0.2f`
- **Agente:** `agentHeight = 2.0f`, `agentRadius = 0.5f`, `agentMaxClimb = 0.9f`, `agentMaxSlope = 50.0f` graus
- **Polígonos:** `maxVertsPerPoly = 3` (somente triângulos), `minRegionArea = 16.0f`, `mergeRegionArea = 20.0f`, `maxEdgeLen = 12.0f`, `maxSimplificationError = 1.3f`

### Estrutura Binária do Arquivo `.nav` (*Little-Endian*)

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `floatCount` | `int32` (LE) | Total de floats no buffer de vértices (`nverts * 3`). |
| `vertices` | `float32[floatCount]` (LE) | Coordenadas em espaço Aion `(X, Y, Z)` convertidas de `(Recast-X, Recast-Z, Recast-Y)`. |
| `triangleCount` | `int32` (LE) | Quantidade de triângulos (`npolys`). |
| `triangles[i]` | `6 × int32` (LE) | Para cada triângulo `i`: `[v0, v1, v2, adj0, adj1, adj2]` com *winding* CCW (`nz > 0`) e `-1` quando a aresta não possui vizinho. |

---

## Créditos e Referências Técnicas

- **Repositório Principal:** [https://github.com/kamidaki/aion-classic-5.0/](https://github.com/kamidaki/aion-classic-5.0/)
- **Bibliotecas utilizadas:** [Recast4j](https://github.com/recast4j/recast4j) (Recast/Detour em Java), [oxipng](https://github.com/shssoichiro/oxipng), JDOM2 e JCommander.
- **Bases técnicas de formato:** [PyFFI](https://github.com/niftools/pyffi), [Cryengine-Converter](https://github.com/Markemp/Cryengine-Converter) e histórico open-source de GeoDataBuilderJ/GeoBuilder.
