# Plano de Jogo - Motor de Mundo, Grid Espacial & Instâncias

Este documento descreve a arquitetura do **World Engine**, do sistema de particionamento espacial em **Grid 3D / Quadtree**, do gerenciamento de visibilidade entre entidades e do sistema de **Masmorras Instanciadas** (Java 4.8 `world/` e `instance/` $\rightarrow$ Rust).

---

## 1. Mapeamento de Classes Java 4.8 $\rightarrow$ Rust

| Classe Java 4.8 | Módulo em Rust | Responsabilidade |
| :--- | :--- | :--- |
| `world.World` | `world::world_map.rs` | Gerenciador central de todos os mapas e instâncias ativas no servidor |
| `world.WorldMap` | `world::map_instance.rs` | Representação de um mapa específico (ex: Poeta `210010000`, Sanctum `110010000`) |
| `world.WorldMapInstance` | `world::instance.rs` | Instância viva de um mapa (canal aberto ou masmorra privada de grupo) |
| `world.WorldPosition` | `world::position.rs` | Coordenada 3D `(x, y, z, h)` atrelada ao `map_id` e `instance_id` |
| `world.zone.ZoneInstance` | `world::zone.rs` | Polígonos de zonas especiais (Safe Zone, Fly Zone, PvP Area, Drown Zone) |
| `world.MapRegion` | `world::region_grid.rs` | Bloco do Grid 3D de $100\text{m} \times 100\text{m}$ para particionamento espacial |
| `instance.InstanceEngine` | `instance::instance_engine.rs` | Criador, gerenciador de tempo e destruidor de masmorras instanciadas |
| `instance.handlers.InstanceHandler` | `instance::handlers/` | Lógica customizada de masmorras (boss spawns, gates, timers de rank S/A/B) |

---

## 2. Sistema de Particionamento Espacial em Grid 3D

Para evitar que a busca de vizinhança seja $O(N^2)$, o mundo é particionado em um Grid de Regiões de tamanho fixo:

```
+-----------+-----------+-----------+
| Region    | Region    | Region    |
| (x-1,y+1) | (x, y+1)  | (x+1,y+1) |
+-----------+-----------+-----------+
| Region    | Region    | Region    |   <-- A entidade em (x,y) enxerga apenas
| (x-1, y)  | (x, y)    | (x+1, y)  |       as 9 regiões adjacentes (3x3 grid)
+-----------+-----------+-----------+
| Region    | Region    | Region    |
| (x-1,y-1) | (x, y-1)  | (x+1,y-1) |
+-----------+-----------+-----------+
```

### Regras de Visibilidade:
* **Raio de Visão de Jogadores**: $100\text{ metros}$ (Distância máxima na qual o cliente desenha outros jogadores).
* **Raio de Visão de NPCs/Monstros**: $60\text{ metros}$ (Otimização para economizar pacotes de broadcast).
* **Atualização de Região**: Quando uma entidade se move e cruza a fronteira de uma região de $100\text{m}$, o servidor:
  1. Calcula as novas regiões que entraram no campo de visão e envia `SM_PLAYER_INFO` / `SM_NPC_INFO` para os novos vizinhos.
  2. Calcula as regiões que saíram do campo de visão e envia `SM_DELETE_OBJECT` (0x0049) para remover as entidades fora do alcance.

---

## 3. Gestão de Instâncias (Masmorras e Canais)

### Tipos de Mapas:
1. **Mundo Aberto (Persistent Worlds)**:
   * Possuem canais dinâmicos (`channel_id = 1, 2, ...`).
   * Ex: Ishalgen (`220010000`), Poeta (`210010000`), Heiron (`210040000`), Beluslan (`220040000`), Abyss Core (`400010000`).
2. **Masmorras Instanciadas (Private Instances)**:
   * Criadas dinamicamente sob demanda por um jogador ou grupo.
   * `instance_id` único gerado em tempo de execução.
   * Ex: Fire Temple (`300040000`), Nochsana Training Camp (`300030000`), Dark Poeta (`300080000`), Dredgion (`300110000`).

### Ciclo de Vida da Instância em Rust:
```rust
pub struct MapInstance {
    pub instance_id: u32,
    pub map_id: u32,
    pub created_at: Instant,
    pub expire_at: Option<Instant>,
    pub grid: RegionGrid,
    pub players: HashMap<u32, Arc<RwLock<Player>>>,
    pub npcs: HashMap<u32, Arc<RwLock<Npc>>>,
    pub doors: HashMap<u32, StaticDoor>,
}
```

* **Criação**: Ao entrar no portal da masmorra, o `InstanceEngine` aloca uma nova `MapInstance`, carrega os spawns da masmorra do cache estático e vincula o grupo ao `instance_id`.
* **Destruição**: Quando todos os jogadores saem ou o timer expira (ex: 2 horas), a instância e todas as suas entidades são desalocadas da memória RAM automaticamente.
