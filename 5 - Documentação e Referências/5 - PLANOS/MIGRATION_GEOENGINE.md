# MIGRATION_GEOENGINE.md — Fase 3: Módulo `geoEngine`

## Resumo

Migração e modernização do módulo `geoEngine` (motor de colisão geográfica) do AION 4.8 Retail para o Classic 5.0.  
**Status**: `[CONCLUÍDO]` — BUILD SUCCESS, 0 erros, 6/6 módulos Maven.

---

## Estratégia

O 5.0 já possuía uma versão **mais avançada** do geoEngine (43 arquivos vs. 29 no 4.8).  
A abordagem foi:
1. Manter o 5.0 como base (mais completo e adaptado ao protocolo 5.0)
2. Incorporar **7 arquivos exclusivos do 4.8** com as adaptações necessárias para a API 5.0
3. Substituir **javolution** por coleções Java modernas em todos os arquivos afetados
4. Enriquecer `CollisionResults` com `IgnoreProperties` e `shouldInvalidateSlopingSurface()`

---

## Arquivos Adicionados (7 novos — só existiam no 4.8)

| Arquivo | Descrição |
|---|---|
| `collision/IgnoreProperties.java` | Propriedades de colisão por raça (ELYOS, ASMODIANS, BALAUR) e instância estática |
| `utils/TempVars.java` | Pool thread-local de variáveis temporárias (Vector3f, Matrix3f, arrays BIH) sem pressão de GC |
| `models/Terrain.java` | Lógica de heightmap e materiais de terreno com detecção de colisão por ray |
| `scene/DespawnableNode.java` | Nó de cena ativável por tipo: EVENT, SHIELD, HOUSE, PLACEABLE, TOWN_OBJECT, DOOR_STATE |
| `scene/mesh/IndexArray.java` | Interface de acesso unificado ao buffer de índices (pattern-matching Java 21+) |
| `scene/mesh/IndexByteArray.java` | Implementação de IndexArray para índices de 1 byte |
| `scene/mesh/IndexShortArray.java` | Implementação de IndexArray para índices de 2 bytes (short) |

---

## Arquivos Modificados (modernização/adaptação)

### Eliminação de `javolution` (7 arquivos)

| Arquivo | Antes | Depois |
|---|---|---|
| `models/GeoMap.java` | `FastMap<K,V>` | `ConcurrentHashMap<K,V>` |
| `collision/bih/BIHNode.java` | `FastList.newInstance()` / `recycle()` | `ArrayDeque<>` / `removeLast()` |
| `math/Array3f.java` | `ObjectFactory`, `implements Reusable` | `new Array3f()` / no-op recycle |
| `math/Matrix3f.java` | `ObjectFactory`, `implements Reusable` | `new Matrix3f()` / no-op recycle |
| `math/Triangle.java` | `ObjectFactory`, `implements Reusable` | `new Triangle()` / no-op recycle |
| `math/Vector3f.java` | `ObjectFactory`, `implements Reusable` | `new Vector3f()` / no-op recycle |

### Enriquecimento de `CollisionResults.java`

Adicionados à API da classe:
- Campo `IgnoreProperties ignoreProperties` + `getIgnoreProperties()`
- Campo `invalidateSlopingSurface` + `shouldInvalidateSlopingSurface()` + `setInvalidateSlopingSurface()`
- Constante `SLOPING_SURFACE_ANGLE_RAD = 45°`
- Múltiplos construtores com sobrecarga para `IgnoreProperties`
- Mantida compatibilidade retroativa com o construtor 5.0 `(byte, boolean, int)`

---

## Adaptações API 5.0

| Item 4.8 | Substituição 5.0 |
|---|---|
| `services.event.EventService` | `services.EventService` (pacote diferente no 5.0) |
| `EventService.getEventTheme().getId()` | `EventService.getEventType().getId()` |
| `node.collisionIntentions` + `node.materialId` | `node.collisionFlags` (short unificado no 5.0) |
| `FastList.remove(size - 1)` | `ArrayDeque.removeLast()` |

---

## Estatísticas Finais

| Métrica | Antes | Depois |
|---|---|---|
| Arquivos `.java` no geoEngine | 43 | **50** |
| Referências javolution ativas | 6 arquivos | **0** |
| Erros de compilação | 0 (baseline) | **0** |
| Tempo de compilação (total) | 25s | **21s** |
| Módulos compilados | 6/6 | **6/6** |

---

## Commit

> `feat(geoEngine): migracao do modulo geoEngine — 7 arquivos do 4.8 integrados, javolution eliminado, BUILD SUCCESS`
