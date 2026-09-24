# Subsistema Native-Path CryEngine (`com.lostacademy.nativepath`)

## 1. Visão Geral e Autoridade Exclusiva

O subsistema `native-path` é o motor primário e **autoritativo exclusivo** de navegação e pathfinding 3D do emulador Lost Academy. Ele consome diretamente os arquivos nativos de navegação compilados da CryEngine (`*-path.dat`) extraídos das pastas `Levels/` do cliente oficial Aion Classic.

Ao contrário de aproximações ou malhas genéricas trianguladas (`.nav` Recast) ou motores legados (Eleanor):
- **Fonte Única da Verdade:** Os arquivos `*-path.dat` são a fonte canônica de tráfego, nós e camadas transitáveis do cliente.
- **Zero Fallbacks em Execução:** Eliminação total de fallbacks em tempo de execução para Eleanor ou NavMesh genérico. Se um caminho não existe na malha nativa, a falha é tratada deterministicamente pela IA (abortar movimento ou recuar) sem atravessar obstáculos ou teleportar silenciosamente.
- **Precisão Geométrica Real:** Resolução de 0.5m por célula de grade espacial, com mapeamento tridimensional exato de camadas sobrepostas (pontes, túneis, estruturas multiníveis e rampas).

---

## 2. Arquitetura do Sistema

```
                        ┌───────────────────────────────────────────────┐
                        │   Requisição de Movimento (NpcMoveController) │
                        └───────────────────────┬───────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │    NativePathService (Fachada de Alto Nível)  │
                        └───────────────────────┬───────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
      ┌─────────────────────────────┐                       ┌─────────────────────────────┐
      │     NativePathData          │                       │     NativePathAStar         │
      │  - Cache Bounded LRU (25)   │                       │  - ThreadLocal SearchContext│
      │  - Rastreamento de Jogadores│                       │  - Heap Binário Primitivo   │
      │  - Pré-carregamento Assínc. │                       │  - Hash Table Primitiva     │
      │  - Limpeza Periódica        │                       │  - Zero Alocação de Heap    │
      └──────────────┬──────────────┘                       └──────────────┬──────────────┘
                     │                                                     │
                     ▼                                                     ▼
      ┌─────────────────────────────┐                       ┌─────────────────────────────┐
      │     NativePathMap           │                       │  Validações Cinemáticas 3D  │
      │  - Parsing Binário .dat     │                       │  - Subida Máx: 0.8m         │
      │  - Setores 16x16 e Camadas  │                       │  - Queda Máx: 1.8m          │
      │  - Integração GeoService 3D │                       │  - Anti-Corner-Cutting      │
      │  - DDA Raycasting 3D        │                       │  - Alisamento String-Pulling│
      └─────────────────────────────┘                       └─────────────────────────────┘
```

---

## 3. Resolução Crítica de Bugs e Desempenho

### 3.1. Correção de Afundamento e Flutuação no Terreno (Elevação 3D Real)
- **Problema:** Anteriormente, `findBestLayer` e `Layer.getZ` retornavam `currentZ` (a coordenada Z informada pelo chamador) para camadas de terreno natural (tipos 2 e 3). Como `GeoService` nunca era consultado, o servidor assumia elevação plana e constante para qualquer agente, fazendo com que NPCs flutuassem no ar ou afundassem no relevo ao se mover.
- **Solução:** `NativePathMap.getSurfaceZ` e `NativePathSector.Layer.getZ` foram integrados à elevação 3D canônica do `GeoService.getInstance().getZ(worldId, x, y)`. Valores `Float.NaN` e desníveis são tratados de forma segura, garantindo ancoragem exata na superfície do relevo.

### 3.2. Eliminação de Atravessamento de Paredes e Obstáculos
- **Problema:** Quando o A* falhava em calcular uma rota até alvos inalcançáveis, o `NpcMoveController` não atualizava o temporizador de repath e caía no fallback direto `moveToLocation(targetX, targetY, targetZ)`, ordenando que o NPC andasse em linha reta através de paredes e despenhadeiros.
- **Solução:**
  - Implementado backoff determinístico de 1000ms para requisições de repath com falha.
  - Verificação estrita de linha de visão física com `NativePathService.canWalkDirectly` antes de permitir qualquer movimento direto.
  - Se não houver caminho transitável, a movimentação é cancelada (`abortMove()`), prevenindo atravessamento de geometria.

### 3.3. Eliminação do Vazamento de Memória (>2 GB) com Cache Bounded LRU
- **Problema:** O método `loadAllMaps()` mantinha pré-carregados todos os 118 mapas no arranque, alocando mais de 4.3 milhões de setores e 452.000 camadas com matrizes `short[1024]` permanentemente no heap, consumindo >2.5 GB de RAM em repouso.
- **Solução:**
  - `NativePathData` foi reformulado com cache LRU estritamente limitado (`max_cached_maps = 25`).
  - Pré-carregamento assíncrono restrito aos 4 mapas iniciais essenciais (Poeta, Ishalgen, Sanctum, Pandaemonium).
  - Rastreamento dinâmico de presença de jogadores (`onPlayerEnterMap` / `onPlayerLeaveMap`) e tarefa agendada a cada 3 minutos para expulsação de mapas sem jogadores ativos por mais de 5 minutos.
  - Redução drástica do consumo de RAM em repouso de >2.5 GB para menos de 150 MB.

### 3.4. A* Tridimensional com Alocação Zero (Zero-GC Heap Churn)
- **Problema:** Cada busca A* alocava instâncias de `PriorityQueue`, `HashMap(4096)`, `HashSet(4096)` e milhares de objetos empacotados (`java.lang.Long`, `java.lang.Float`), gerando centenas de MB por segundo de pressão sobre o Garbage Collector sob múltiplos NPCs em combate.
- **Solução:**
  - Criação do `ThreadLocal<AStarSearchContext>` contendo buffers planos e primitivos reutilizáveis.
  - Min-Heap binário primitivo com indexação em arrays `long[]` e `float[]`.
  - Tabela hash aberta de endereçamento primitivo com array de timestamps generacionais (`int generation`), permitindo reset completo do estado em $O(1)$ sem zerar arrays grandes.
  - **Zero alocações de objetos no heap por busca de caminho**.
  - Validação estrita de inclinação e desnível vertical (`MAX_STEP_UP = 0.8f`, `MAX_DROP_DOWN = 1.8f`), prevenindo escaladas impossíveis de penhascos e quedas abruptas.
  - Verificação geométrica de quinas (*anti-corner-cutting*) e alisamento de rota (*string-pulling*) com DDA 3D rápido.

---

## 4. Estrutura de Arquivos e Resolução Dinâmica

Todos os 118 arquivos `.dat` estão organizados na pasta:
`game-server/data/native-path/{worldId}_{nome_do_mapa}/xxxx-path.dat`

Exemplos:
- `data/native-path/210010000_lf1/LF1-path.dat` (Poeta)
- `data/native-path/210020000_lf2/LF2-path.dat` (Verteron)
- `data/native-path/210040000_lf3/LF3-path.dat` (Eltnen)
- `data/native-path/220010000_df1/DF1-path.dat` (Ishalgen)
- `data/native-path/220020000_df2/DF2-path.dat` (Altgard)
- `data/native-path/600040000_tiamat_down/tiamat_down-path.dat` (Tiamaranta Eye)

A classe `NativePathData` mapeia dinamicamente o prefixo `{worldId}` ao inicializar o servidor, eliminando dependência de nomes ou caminhos fixos.

---

## 5. Classes do Subsistema

| Classe | Responsabilidade Técnica |
|---|---|
| `NativePathConfig` | Central de propriedades e constantes cinemáticas (passo máx, queda máx, timeout A*, limites do cache). |
| `NativePathNode` | Representação imutável de nó 3D da malha com coordenadas $(x, y, z)$, índice de grade e propriedades de superfície. |
| `NativePathSector` | Estrutura de setor $16\text{m} \times 16\text{m}$ contendo camadas sobrepostas (*layers*), seleção da melhor camada por proximidade vertical e integração com a elevação natural do terreno via `GeoService`. |
| `NativePathMap` | Parser binário do formato CryEngine 0x80 bytes, grade espacial $O(1)$, elevação de superfície 3D, verificação de transitabilidade e raycasting DDA 3D com linha de visão. |
| `NativePathAStar` | Motor A* heurístico 3D de alta performance com contexto `ThreadLocal`, zero alocações por query, heurística Euclidiana ponderada e string pulling. |
| `NativePathData` | Repositório central de dados com cache LRU concorrente limitado a 25 mapas, pré-carregamento assíncrono e limpeza automática de inatividade. |
| `NativePathService` | Fachada de serviço (*singleton*) com telemetria atômica, verificação de linha de puxão (*pull*), localização de pontos transitáveis e cálculo de rotas para NPCs. |

---

## 6. Configuração (`geodata.properties`)

```properties
# =========================================================================
# CRYENGINE NATIVE PATHFINDING SUBSYSTEM (NATIVE-PATH)
# =========================================================================
# Ativa o subsistema de navegação nativa da CryEngine (*-path.dat)
gameserver.nativepath.enable = true

# Diretório raiz contendo os mapas nativos {ID_MAP}_nome/xxxx-path.dat
gameserver.nativepath.dir = data/native-path/

# Número máximo de mapas mantidos simultaneamente na memória RAM (Cache LRU limitado)
gameserver.nativepath.cache.max_maps = 25

# Tempo de inatividade em milissegundos para expulsação de mapas sem jogadores (padrão: 5 min)
gameserver.nativepath.cache.inactive_timeout_ms = 300000

# Intervalo em milissegundos para verificação e limpeza de mapas inativos (padrão: 3 min)
gameserver.nativepath.cache.cleanup_interval_ms = 180000

# Timeout máximo em milissegundos para busca A*
gameserver.nativepath.astar.timeout = 25

# Ativa logs de depuração detalhados do Native-Path
gameserver.nativepath.debug = false
```
