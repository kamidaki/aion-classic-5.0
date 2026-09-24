# Subsistema Native-Path CryEngine (`com.lostacademy.nativepath`)

## 1. Visão Geral

O subsistema `native-path` é o motor primário de navegação e pathfinding do emulador Lost Academy. Ele consome diretamente os arquivos nativos de navegação compilados da CryEngine (`*-path.dat`) extraídos das pastas `Levels/` do cliente oficial Aion Classic.

Ao contrário de aproximações ou malhas genéricas trianguladas (`.nav` Recast), o formato nativo da CryEngine possui:
- Precisão de 0.5m por unidade de célula de grade espacial.
- Mapeamento tridimensional exato com suporte a camadas sobrepostas (pontes, túneis, desníveis verticais).
- Conexões de adjacência pré-calculadas entre células transitáveis.
- Atributos de tráfego, inclinação máxima e flags de superfície nativas da engine do cliente.

---

## 2. Hierarquia de 4 Camadas de Fallback

O sistema implementa uma cadeia estrita de 4 camadas:

```
[Camada 1: Native-Path (CryEngine .dat)]
         │
         ▼ (falha / sem arquivo / desativado)
[Camada 2: NavMesh (.nav Recast)]
         │
         ▼ (falha / sem malha / desativado)
[Camada 3: Eleanor (Geometria / Raycast LoS)]
         │
         ▼ (falha / sem rota transitável)
[Camada 4: Vanilla / Comportamento Normal (GeoService direto)]
```

### Comportamento dos Gatilhos:
- Se `gameserver.nativepath.enable = true` e `gameserver.geodata.nav.enable = false`:
  O fluxo percorre: `Native-Path` -> `Eleanor` -> `Vanilla`.
- Se `gameserver.nativepath.enable = false` e `gameserver.geodata.nav.enable = true`:
  O fluxo percorre diretamente: `NavMesh (.nav)` -> `Eleanor` -> `Vanilla`.
- Se ambos estiverem ativos:
  O fluxo percorre a hierarquia completa de 4 camadas.

---

## 3. Estrutura de Arquivos e Resolução Dinâmica

Todos os 185 arquivos `.dat` foram indexados e distribuídos na pasta:
`data/native-path/{worldId}_{nome_do_mapa}/xxxx.dat`

Exemplos:
- `data/native-path/210010000_lf1/LF1-path.dat` (Poeta)
- `data/native-path/210020000_lf2/LF2-path.dat` (Verteron)
- `data/native-path/210040000_lf3/LF3-path.dat` (Eltnen)
- `data/native-path/220020000_df2/DF2-path.dat` (Altgard)
- `data/native-path/600040000_tiamat_down/tiamat_down-path.dat` (Tiamaranta Eye)

### Resolução Automática:
A classe `NativePathData` escaneia os subdiretórios de `data/native-path/` ao inicializar e mapeia o prefixo numérico `{worldId}` para o respectivo arquivo `.dat`, eliminando qualquer necessidade de caminhos fixos (*hardcoded*) no código.

---

## 4. Arquitetura dos Componentes

| Classe | Responsabilidade |
|---|---|
| `NativePathConfig` | Mapeamento das propriedades do arquivo `geodata.properties` e `LostAcademy.properties`. |
| `NativePathNode` | Representação imutável de nós 3D transitáveis com coordenadas $(x, y, z)$, índices de grade e flags. |
| `NativePathMap` | Parser binário do cabeçalho CryEngine (0x80 bytes, versão 0x00060005, blocos de 147 bytes). Grade espacial $16\text{m}\times 16\text{m}$ ($O(1)$) para localização de nós vizinhos e line-of-sight raycasting. |
| `NativePathAStar` | Algoritmo A* heurístico tridimensional com fila de prioridade (`PriorityQueue`) e alisamento de rota via *string-pulling raycasting*. |
| `NativePathData` | Singleton para indexação de diretórios, carregamento sob demanda, cache LRU thread-safe e pré-carregamento assíncrono. |
| `NativePathService` | Fachada de alto nível que expõe APIs: `navigateToTarget`, `navigateToLocation`, `canPullTarget`, `getSurfaceZ`, `isWalkable`. |

---

## 5. Integração com o Servidor

O subsistema está profundamente integrado aos principais subsistemas de controle do jogo:

1. **`NpcMoveController`**:
   - `moveToDestination(TARGET_OBJECT)`: Perseguição de alvos de combate.
   - `moveToDestination(POINT)`: Movimentação a ponto arbitrário no espaço.
   - `fleeFromFlyingTarget()`: Fuga inteligente de NPCs contra alvos voando fora de alcance.
   - `returnToLastStepOrSpawn()`: Retorno seguro ao ponto inicial / spawn.
2. **`ForcedMovementSafety`**:
   - `resolveSafeDestination()`: Validação e teleporte seguro em puxões, empurrões, medo (fear) e knockbacks.
   - `isInsideNavReach()`: Validação de alcance e paredes de colisão.
3. **`WhipSkillService`**:
   - `canPullTarget()`: Checagem de linha de puxão de skills de gancho/chicote antes do efeito ser disparado.
4. **`WalkManager`**:
   - `navigateToLocation()`: Rotas de patrulha e rotina de NPCs pelas cidades e estradas.
5. **Ciclo de Vida do Jogador**:
   - `PlayerEnterWorldService` & `TeleportService`: Notificam `NativePathData.onPlayerEnterMap(worldId)`, acionando pré-carregamento assíncrono do mapa.
   - `PlayerLeaveWorldService`: Notifica `NativePathData.onPlayerLeaveMap(worldId)` para contagem de atividade e desalocação do cache LRU quando inativo.
6. **Interface e Notificações**:
   - `CM_LEVEL_READY`: Informa o status de navegação do mapa ao jogador (`CryEngine Nativo`, `NavMesh (.nav)`, ou `Sem dados`).

---

## 6. Configuração (`geodata.properties`)

```properties
# =========================================================================
# CRYENGINE NATIVE PATHFINDING SUBSYSTEM (NATIVE-PATH)
# =========================================================================
# Ativa o subsistema de navegação nativa da CryEngine (*-path.dat)
gameserver.nativepath.enable = true

# Diretório raiz contendo os mapas nativos {ID_MAP}_nome/xxxx.dat
gameserver.nativepath.dir = data/native-path/

# Número máximo de mapas mantidos simultaneamente na memória RAM (Cache LRU)
gameserver.nativepath.cache.max_maps = 20

# Timeout máximo em milissegundos para busca A*
gameserver.nativepath.astar.timeout = 25

# Intervalo em minutos para verificação e limpeza de mapas inativos da memória
gameserver.nativepath.cleanup.interval = 10

# Ativa logs de depuração detalhados do Native-Path
gameserver.nativepath.debug = false
```
