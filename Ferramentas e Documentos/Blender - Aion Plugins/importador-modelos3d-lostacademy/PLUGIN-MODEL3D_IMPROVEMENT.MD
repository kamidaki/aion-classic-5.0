# Lost Academy - Plano Mestre de Correção e Evolução do Plugin 3D (Aion Model Library)
> **Arquivo canônico para desenvolvedores**: `PLUGIN-MODEL3D_IMPROVEMENT.MD`  
> **Diretório do Addon**: `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins\importador-modelos3d-lostacademy`  
> **Cliente Aion de Referência**: `D:\GameForge\aionclassic`  
> **Código Fonte do Emulador**: `D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador`  
> **Ambiente de Validação**: Blender 4.0 - 5.2+ LTS (Headless e GUI)

---

## Sumário Executivo

Este documento é a especificação técnica completa, exaustiva e auto-suficiente para que qualquer desenvolvedor corrija todos os defeitos críticos e implemente todas as funcionalidades requeridas no plugin de importação, visualização, rigging, animação, criação de NPCs e exportação round-trip de modelos 3D do **Aion Classic**.

**Nenhum prompt adicional é necessário.** Basta seguir sequencialmente os passos, métodos, diagnósticos matemáticos e arquiteturais descritos neste arquivo.

```
PIPELINE ALVO COMPLETO (ROUND-TRIP):
[CLIENTE / EMULADOR] <---> [INDEXADOR / CACHE] <---> [VIEWPORT BLENDER 3D] <---> [EDIÇÃO / CRIAÇÃO] <---> [GRAVAÇÃO ATÔMICA PAK / XML]
```

---

## Índice dos Módulos

1. [Item 1: Correção Crítica de Performance e UI Freeze](#item-1-correção-crítica-de-performance-e-ui-freeze)
2. [Item 2: Correção Completa do Pipeline de Animações (CAF / CAL)](#item-2-correção-completa-do-pipeline-de-animações-caf--cal)
3. [Item 3: Correção Matemática da Deformação Esquelética (Rigging & Skinning)](#item-3-correção-matemática-da-deformação-esquelética-rigging--skinning)
4. [Item 4: Criação e Edição Completa de Modelos e Peças Modulares / Skins](#item-4-criação-e-edição-completa-de-modelos-e-peças-modulares--skins)
5. [Item 5: Criação Completa de Metadados de NPCs no Cliente](#item-5-criação-completa-de-metadados-de-npcs-no-cliente)
6. [Item 6: Gravação Transacional nos Arquivos e PAKs do Cliente](#item-6-gravação-transacional-nos-arquivos-e-paks-do-cliente)
7. [Item 7: Integração com o Código Fonte do Emulador (Game Server XML/XSD)](#item-7-integração-com-o-código-fonte-do-emulador-game-server-xmlxsd)
8. [Item 8: Suporte a Múltiplos Modelos Simultâneos na Viewport (Lineup)](#item-8-suporte-a-múltiplos-modelos-simultâneos-na-viewport-lineup)
9. [Item 9: Auditoria de Cobertura de Assets (100% de Suporte a CGF/CGA/CAF)](#item-9-auditoria-de-cobertura-de-assets-100-de-suporte-a-cgfcgacaf)
10. [Item 10: Eliminação de Falhas Intermitentes e Garantia de Determinismo](#item-10-eliminação-de-falhas-intermitentes-e-garantia-de-determinismo)
11. [Checklist Sequencial de Execução (TO-DO do Desenvolvedor)](#checklist-sequencial-de-execução-to-do-do-desenvolvedor)
12. [Procedimentos de Teste e Validação de Regressão](#procedimentos-de-teste-e-validação-de-regressão)

---

## Item 1: Correção Crítica de Performance e UI Freeze

### 1.1 Diagnóstico das Causas Raízes
A auditoria no código identificou **três causas raízes fatais** que paralisam o Blender imediatamente após a seleção do cliente:

1. **Callback Dinâmico de EnumProperty no Ciclo de Redesenho do Blender (`UI Thread Blocking`)**:
   - **Arquivo**: `properties/library_properties.py` (linhas 59-84 e 211-215).
   - **Causa**: A propriedade `character_class` utiliza `items=get_character_classes_callback`. O Blender invoca essa função a **cada evento de mouse hover, movimento ou redesenho da interface**.
   - **Efeito Destrutivo**: Dentro desse callback, a linha 78 instanciava `cp = AionClientProvider(cpath)`, cujo `__init__` invocava `_init_catalog()` que executava varredura de dezenas de gigabytes de arquivos PAK em `shaders`, `levels/common` e `textures/**/*.pak`, além de abrir múltiplos PAKs em `data/PC/`. Isso travava a UI do Blender por 5 a 10 segundos em qualquer interação com a janela.

2. **Index Cache JSON Hipertrofiado (227 Megabytes em Thread Síncrona)**:
   - **Arquivo**: `indexer/asset_database.py` (métodos `load_cache` e `save_cache`) e `operators/library_ops.py` (linha 150).
   - **Causa**: O arquivo `.aion_model_index.json` gerado para o cliente GameForge atingiu **227.339.114 bytes (227 MB)** com 94.000 entradas formatadas com `indent=2`. No momento em que o usuário digitava qualquer letra na busca ou alterava a categoria, `on_filter_updated` disparava síncronamente `json.loads(cache_file.read_text())` na thread principal da interface.

3. **Varredura Completa e Síncrona sem Paginação**:
   - A `UIList` do Blender tentava alocar milhares de itens (`AionAssetItem`) na coleção `scene.aion_model_lib.asset_items`, gerando gargalo imenso no Garbage Collector do Python e no gerenciador de eventos do Blender.

### 1.2 Solução Arquitetural Obrigatória
1. **Eliminar Instanciação no Callback do EnumProperty**:
   - Cachear o resultado de `get_character_classes` em uma variável global ou tupla pré-computada em memória (`_CACHED_CLASSES`). O callback deve retornar essa tupla imediatamente sem tocar no disco ou recriar instâncias.
2. **Migrar o Cache de Índice para SQLite / JSON Compacto**:
   - Substituir a serialização massiva de 227 MB em texto formatado por um banco SQLite ultraleve (`.aion_model_index.db`) ou JSON comprimido binário/compacto sem indentação.
   - Indexar por colunas: `asset_id`, `category`, `name`, `model_path`, `bone_count`, `anim_count`.
3. **Carregamento Assíncrono / Não Bloqueante**:
   - Qualquer leitura de índice deve rodar via `threading.Thread` em segundo plano, utilizando `bpy.app.timers` para devolver os resultados à UI em lotes paginados (limite de 100 itens por página).

### 1.3 Métodos e Arquivos a Modificar
- `properties/library_properties.py`:
  ```python
  # Modificar get_character_classes_callback:
  _CACHED_CLASSES = None

  def get_character_classes_callback(self, context):
      global _CACHED_CLASSES
      if _CACHED_CLASSES is not None:
          return _CACHED_CLASSES
      # Fallback estático imediato; atualização real ocorre apenas sob demanda assíncrona
      return FALLBACK_CLASSES
  ```
- `indexer/asset_database.py`:
  - Implementar backend SQLite (`indexer/sqlite_cache.py`) com consultas indexadas `SELECT * FROM assets WHERE category = ? AND name LIKE ? LIMIT 100`.
- `core/client_provider.py`:
  - Remover chamadas a `self._init_catalog()` de dentro de `__init__`. O catálogo deve ser indexado sob demanda (lazy-loading) apenas para a categoria solicitada.

---

## Item 2: Correção Completa do Pipeline de Animações (CAF / CAL)

### 2.1 Diagnóstico das Causas Raízes
Atualmente, apenas a pose/idle inicial é carregada, e ao clicar em outras animações no painel nada acontece. As causas exatas são:

1. **Falha de Resolução de Caminhos de PAKs em `AION_OT_switch_animation`**:
   - **Arquivo**: `operators/animation_ops.py` (linhas 105-110).
   - **Causa**: Ao selecionar uma animação como `nwalk_001`, o caminho relativo no CAL é tipicamente `NPC/ShugoMale/ShugoMale_nwalk_001_loop.caf`. O código chamava `client_prov.ensure_category_paks_indexed(caf_rel)`. Porém, `ensure_category_paks_indexed` buscava no disco pela pasta `self.root / "NPC/ShugoMale"`. Nos clientes GameForge e Classic 5.0, **essas pastas não existem no disco**; os arquivos `.caf` estão armazenados dentro de `objects/npc/Mesh_Meshes_*.pak`, `objects/monster/Mesh_Meshes_*.pak` ou `data/animations/animations.pak`. Como a pasta não existia, nenhum PAK era indexado, `extract_file` retornava `None` e a troca de animação abortava silenciosamente ou exibia erro.
2. **Associação Quebrada entre Bones do Esqueleto e `ctrl_id` da Animação**:
   - **Arquivo**: `providers/animation_provider.py` (linhas 99-116).
   - O mapeamento entre os controladores do CAF (`CHUNK_CONTROLLER 0xCCCC000D`) e os ossos do rig rely em `ctrl_id` (calculado via CRC32 ou índice direto da tabela `BoneAnim`). Quando a armadura é extraída via `extract_armature`, os `ctrl_id` originais do CGF eram perdidos ou recalculados erroneamente, impossibilitando encontrar as trilhas de animação para os ossos.

### 2.2 Pipeline Completo de Descoberta e Extração
O desenvolvedor deve estruturar a resolução em 4 etapas determinísticas:

```
[MODELO CGF CARREGADO]
         │
         ▼
[ENCONTRAR ARQUIVO .CAL] ──► (Ex: objects/npc/shugomale/shugomale.cal)
         │
         ▼
[PARSER DE SEQUÊNCIAS CAL] ──► Mapeia tags ('nwalk_001', 'nrun_001', 'attack_01') para caminhos relativos CAF
         │
         ▼
[RESOLUÇÃO GLOBAL DE PAKS] ──► Busca o CAF prioritariamente em:
                               1. Mesmo PAK onde o CGF do modelo está localizado
                               2. Demais PAKs Mesh_Meshes da mesma categoria
                               3. data/animations/animations.pak
         │
         ▼
[PARSER BINÁRIO CAF] ──► Timing (0xCCCC000E) + Controllers (0xCCCC000D)
         │
         ▼
[APLICAÇÃO NO RIG VIA ACTION] ──► Criação de Action, F-Curves e Extrapolação Cíclica
```

### 2.3 Métodos e Arquivos a Modificar
- `core/client_provider.py`:
  - Implementar método `find_caf_bytes(caf_relative_path: str, source_model_path: str) -> Optional[bytes]`.
  - Este método deve checar o PAK do próprio modelo antes de qualquer varredura externa.
- `operators/animation_ops.py`:
  - Substituir a extração simplista por chamada direta a `find_caf_bytes`.
- `providers/animation_provider.py`:
  - Preservar os `ctrl_id` originais nos ossos do Blender usando propriedades customizadas (`pose_bone["ctrl_id"] = cid`).

---

## Item 3: Correção Matemática da Deformação Esquelética (Rigging & Skinning)

### 3.1 Diagnóstico Matemático da Distorção de Modelos
Este é o problema mais crítico de fidelidade visual. Quando a animação era ativada, a malha sofria deformações grotescas (corpo esticado por 1.5 a 3 metros, membros torcidos em espiral e face colapsada).

**Identificamos 4 erros matemáticos fundamentais no código atual:**

#### Erro 1: Transposição da Matriz `BoneInitialPos` (Inversão de Orientação de 90°/180°)
- **Arquivo**: `providers/skeleton_provider.py` (linhas 46-50).
- **Código Incorreto**:
  ```python
  rot_3x3 = Matrix((
      (m[0], m[3], m[6]),
      (m[1], m[4], m[7]),
      (m[2], m[5], m[8]),
  ))
  ```
- **Fato**: O CryEngine 1 serializa matrizes `Matrix34` na tabela `BoneInitialPos` (chunk `0xCCCC0012`) em formato **row-major**: `m[0..2]` é a linha 0, `m[3..5]` é a linha 1, `m[6..8]` é a linha 2, e `m[9..11]` é a translação em centímetros. O código acima montou as colunas invertidas, aplicando a **transposta (inversa)** da rotação de bind do modelo.

#### Erro 2: Conjugação Indevida de Quatérnions
- **Arquivo**: `providers/animation_provider.py` (linha 172).
- **Código Incorreto**:
  ```python
  quat_v = quat_v.conjugated()
  ```
- **Fato**: Quatérnions no CryEngine são armazenados como `[tick, px, py, pz, qx, qy, qz, qw]`. Ao conjugar o quatérnion, a rotação angular é invertida no tempo ($\theta \to -\theta$). Essa conjugação foi inserida incorretamente como tentativa de compensar o Erro 1, gerando rotações espelhadas destrutivas nos braços e pernas.

#### Erro 3: Confusão entre Espaço Local do Pai vs Espaço Global
- **Arquivo**: `providers/animation_provider.py` (linhas 170-182).
- **Fato**: As chaves dos controladores CAF armazenam:
  - Para o **Root Bone** (Bone 0 / `Bip01`): Translação absoluta no mundo em metros e quatérnion absoluto de orientação.
  - Para todos os **Child Bones** (Bone > 0): Translação e rotação em **Espaço Local Relativo ao Osso Pai**.
  - O código tentava atribuir `pbone.location = basis_mat.translation`, mas no Blender o `pbone.location` de um PoseBone é relativo à orientação de repouso (`rest orientation`) do próprio osso e não ao espaço do pai.

#### Erro 4: Sistema de Coordenadas do 3ds Max / Biped vs Blender
- No 3ds Max (de onde vêm os modelos do Aion), o eixo longitudinal do osso é o eixo **X**.
- No Blender, o eixo longitudinal de um `EditBone` é obrigatoriamente o eixo **Y** (`head -> tail`).
- A rotação de animação do CAF gira em torno dos eixos locais originais do Max.

### 3.2 Implementação Matemática Correta da Deformação
Para alcançar deformação 100% idêntica ao CryEngine e à engine do jogo:

1. **Matriz de Bind Pose do Osso (Centímetros para Metros)**:
   ```python
   # Formato canônico CryEngine 1 Matrix34:
   # Linha 0: (m[0], m[1], m[2]), Linha 1: (m[3], m[4], m[5]), Linha 2: (m[6], m[7], m[8])
   # Translação: Vector((m[9], m[10], m[11])) * 0.01
   rot_3x3 = Matrix((
       (m[0], m[1], m[2]),
       (m[3], m[4], m[5]),
       (m[6], m[7], m[8]),
   ))
   pos = Vector((m[9] * 0.01, m[10] * 0.01, m[11] * 0.01))
   bind_matrix_world = Matrix.Translation(pos) @ rot_3x3.to_4x4()
   ```

2. **Cálculo da Pose Animada em Ordem Topológica (Pai -> Filho)**:
   Em vez de tentar calcular `matrix_basis` manualmente de forma instável, o avaliador de pose deve calcular a **matriz de mundo do PoseBone** e atribuí-la diretamente a `pbone.matrix`:
   ```python
   world_matrices = {}
   for bone_entry in bone_hierarchy_topological:
       name = bone_entry["name"]
       pid = bone_entry["parent_id"]
       
       # 1. Obter transformação local animada do CAF para o quadro f:
       if name in bone_tracks:
           pos_local, quat_local = sample_caf_keyframe(bone_tracks[name], frame)
           local_anim_matrix = Matrix.Translation(pos_local) @ quat_local.to_matrix().to_4x4()
       else:
           # Mantém a transformação relativa original de repouso
           local_anim_matrix = bone_entry["rest_local_matrix"]
       
       # 2. Compor com a matriz mundial do pai:
       if pid >= 0 and bone_names[pid] in world_matrices:
           parent_world = world_matrices[bone_names[pid]]
           world_mat = parent_world @ local_anim_matrix
       else:
           world_mat = local_anim_matrix
       
       world_matrices[name] = world_mat
       
       # 3. Atribuição direta no Blender (Blender resolve a cinemática internamente):
       rig_obj.pose.bones[name].matrix = world_mat
   ```

3. **Inserção dos Keyframes**:
   Após atribuir `pbone.matrix = world_mat`, os canais locais do PoseBone (`location`, `rotation_quaternion`, `scale`) já contêm os valores exatos e normalizados para o Blender:
   ```python
   pbone.keyframe_insert("location", frame=f)
   pbone.keyframe_insert("rotation_quaternion", frame=f)
   pbone.keyframe_insert("scale", frame=f)
   ```

---

## Item 4: Criação e Edição Completa de Modelos e Peças Modulares / Skins

### 4.1 Arquitetura de Modelos no Aion
O Aion possui duas grandes categorias de malhas para personagens e NPCs:
1. **Modelos Modulares (Modular Body Parts)**:
   - Divididos em slots de equipamento: `torso`, `legs`, `hands`, `feet`, `head`, `hair`, `weapon_main`, `weapon_sub`, `wings`.
   - Cada parte modular compartilha o mesmo esqueleto padrão humanóide (`Bip01`) e deve ter os mesmos nomes de vértices/grupos.
2. **Skins de Corpo Inteiro (Full-Body Skins)**:
   - Malha única cobrindo da cabeça aos pés (comum em monstros, bestas e certas armaduras lendárias/fantasias).

### 4.2 O que falta na arquitetura atual
- `editors/model_creator.py` atualmente cria apenas objetos primitivos sem suporte a slots Aion.
- Falta suporte à criação de novos arquivos de definição de animações `.cal`.
- Falta sincronização automática de pesos de skin entre peças modulares acopladas (para evitar buracos nos vértices do pescoço, punhos e tornozelos).

### 4.3 Especificação da Implementação
1. **Módulo `editors/npc_mesh_builder.py`**:
   - Fornece ferramentas para fundir (Merge) ou separar malhas mantendo os chunks de materiais do CryEngine intactos.
   - Operador para transferir pesos de skin da malha base do Aion (`DataTransfer` baseado em `NEAREST_VERTEX`) para novas malhas importadas (FBX/OBJ).
2. **Geração de Chunks CGF**:
   - `0xCCCC0000` (`Mesh`): Vértices, UVs, Faces, Normais, `CryBoneVertex` Skin Weights.
   - `0xCCCC000C` (`Material`): Configuração dos shaders CryEngine (Diffuse, Bump, Specular).
   - `0xCCCC000B` (`Node`): Nomes dos nós e hierarquia.
   - `0xCCCC0003`, `0xCCCC0005`, `0xCCCC0012` (`BoneAnim`, `BoneNameList`, `BoneInitialPos`): Para rigs exportáveis.

---

## Item 5: Criação Completa de Metadados de NPCs no Cliente

### 5.1 Estrutura Canônica de Dados no Cliente Aion
A criação de um novo NPC no cliente exige a sincronização entre dois registros principais contidos na pasta `data/`:

#### 1. Arquivo `data/npcs/npcs.pak -> client_npcs.xml` (ou `client_npcs.bxml` no GameForge)
Cada NPC deve conter os seguintes campos autoritativos:
```xml
<npc_client>
    <id>290001</id>
    <name>Novo_NPC_Custom</name>
    <desc>STR_NPC_NOVO_NPC_CUSTOM</desc>
    <dir>Monster/NovoMonstro</dir>
    <mesh>NovoMonstro</mesh>
    <material>mat_mob_reptile</material>
    <foot_mat>foot_etc</foot_mat>
    <show_dmg_decal>0</show_dmg_decal>
    <ui_type>general</ui_type>
    <cursor_type>talk</cursor_type>
    <erect>1</erect>
    <bound_radius front="1.2" side="1.2" upper="2.5" />
    <scale>100</scale>
    <weapon_scale>100</weapon_scale>
    <altitude>0.0</altitude>
    <stare_angle>75.0</stare_angle>
    <stare_distance>20.0</stare_distance>
    <move_speed_normal_walk>1.5</move_speed_normal_walk>
    <move_speed_normal_run>6.0</move_speed_normal_run>
    <ammo_bone>Bip01 Head</ammo_bone>
    <ammo_speed>50</ammo_speed>
    <hpgauge_level>3</hpgauge_level>
    <ai_name>General</ai_name>
    <tribe>General</tribe>
    <sensory_range>15.0</sensory_range>
</npc_client>
```

#### 2. Arquivo `data/Strings/Strings.pak -> client_strings_npc.xml`
O campo `<desc>` do NPC precisa obrigatoriamente existir na tabela de strings do cliente para ser exibido em jogo:
```xml
<string>
    <name>STR_NPC_NOVO_NPC_CUSTOM</name>
    <id>799999</id>
    <body>Novo Guarda de Sanctum</body>
</string>
```

### 5.2 Painel de Interface no Blender (`ui/npc_editor_panel.py`)
Criar o sub-painel **"Criador e Editor de NPCs"** na barra lateral `N`:
- **ID do NPC**: Numérico inteiro (validação de conflito de ID).
- **Nome de Exibição / String**: Texto legível e identificador `STR_...`.
- **Raça e Facção**: Elyos, Asmodian, Balaur, Beast, Monster, Undead, etc.
- **Tribe (Tribo)**: `General`, `Guard_Dark`, `Guard_Light`, `Monster`, etc.
- **AI Name**: `General`, `SkillArea`, `Aggressive`, `Merchant`, `Quest`.
- **Dimensões e Bounding Radius**: `front`, `side`, `upper`, `scale`.
- **Estatísticas Básicas**: Nível (Level), HP Base, HP Gauge.
- **Atribuição de Modelo**: Seleciona automaticamente o modelo CGF e animações CAL ativas no palco.

---

## Item 6: Gravação Transacional nos Arquivos e PAKs do Cliente

### 6.1 Estrutura dos Arquivos `.pak`
Os arquivos `.pak` do Aion utilizam o formato ZIP 2.0 padrão (armazenado ou comprimido com Deflate).
- Nos clientes com criptografia XOR (ex: GameForge Classic), a tabela de 1056 bytes (`AION_XOR_TABLE`) já está implementada em `core/pak_engine.py`.
- A gravação deve ser **atômica** e **transacional**.

### 6.2 Pipeline de Escrita Transacional

```
[AÇÃO DO USUÁRIO: SALVAR NOVO NPC NO CLIENTE]
                     │
                     ▼
[1. VALIDAÇÃO PRE-FLIGHT] ──► Verifica se ID do NPC e strings já existem (evita sobrescrita acidental)
                     │
                     ▼
[2. STAGING EM TEMP] ──► Cria pasta temporária (.tmp_aion_tx_...)
                     │
                     ▼
[3. CÓPIAS DE SEGURANÇA] ──► Gera 'npcs.pak.bak', 'Strings.pak.bak' e cópia dos CGFs
                     │
                     ▼
[4. ATUALIZAÇÃO DOS PAKS]:
   a) Extrai 'client_npcs.xml', insere novo nó <npc_client>, reempacota
   b) Extrai 'client_strings_npc.xml', insere <string>, reempacota
   c) Adiciona o novo CGF / CAL / CAF dentro de Mesh_Meshes_*.pak ou como loose file
                     │
                     ▼
[5. ATOMIC SWAP] ──► Substitui os arquivos oficiais instantaneamente
                     │
                     ├─► [SUCESSO] Notifica usuário e limpa temporários
                     └─► [ERRO I/O] Executa ROLLBACK imediato a partir dos .bak
```

---

## Item 7: Integração com o Código Fonte do Emulador (Game Server XML/XSD)

### 7.1 Arquitetura do Emulador
- **Diretório Raiz**: `D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador`
- **Sub-projeto**: `game-server`
- **Esquema XSD**: `game-server/data/static_data/npcs/npcs.xsd`
- **Arquivo de Dados Canônico**: `game-server/data/static_data/npcs/npc_templates.xml`

### 7.2 Validação de Esquema XSD (`npcs.xsd`)
O template do emulador deve seguir estritamente o tipo complexo `npcTemplate`:
```xml
<npc_template 
    npc_id="290001" 
    level="50" 
    name="Novo Guarda de Sanctum" 
    name_id="799999" 
    height="1.0" 
    rank="EXPERT" 
    rating="NORMAL" 
    race="PC_LIGHT" 
    tribe="GUARD" 
    type="GUARD" 
    ai="general" 
    srange="15" 
    sangle="240" 
    attack_speed="1500" 
    hpgauge="4">
    <stats maxHp="45000">
        <speeds walk="1.5" group_walk="1.5" run="6.0" run_fight="6.0" group_run_fight="6.0" />
    </stats>
    <bound_radius front="0.5" side="0.5" upper="2.0" />
</npc_template>
```

### 7.3 Implementação do Gerador Automático (`exporters/emulator_exporter.py`)
Criar a classe `EmulatorExporter` que:
1. Detecta o diretório do emulador via configuração ou busca automática.
2. Faz o parse de `npc_templates.xml` utilizando `xml.etree.ElementTree` preservando comentários e formatação original.
3. Converte os atributos do Blender/Cliente para o formato do emulador:
   - `tribe` do cliente em maiúsculas (`General` -> `GENERAL`).
   - `ai_name` convertido para a convenção em minúsculas do emulador (`SummonSkillArea` -> `skillarea`).
   - `name_id` associado ao ID da string gerada em `client_strings_npc.xml`.
4. Insere o novo nó `<npc_template>` ordenado por `npc_id` ou no final do arquivo.
5. Gera backup automático `npc_templates.xml.bak` antes da alteração.

---

## Item 8: Suporte a Múltiplos Modelos Simultâneos na Viewport (Lineup)

### 8.1 Problema Atual
Em `viewers/viewer_stage.py`, o método `clear_stage_objects()` deleta todos os objetos anteriores sempre que um novo asset é carregado. Isso impede comparar modelos lado a lado, vestir manequins ou organizar cenas com vários NPCs.

### 8.2 Arquitetura de Múltiplos Modelos com Espaçamento Automático
Adicionar um modo de exibição configurável:
- **Modo Individual (Focus)**: Limpa o palco e foca o modelo no centro `(0, 0, 0)`.
- **Modo Fileira / Lineup (Multi-Model)**: Mantém os modelos existentes e posiciona o novo modelo ao lado do último com espaçamento de segurança calculado a partir da Bounding Box:

```
[ NPC 1 ]  <--- 1.2m margem --->  [ NPC 2 ]  <--- 1.2m margem --->  [ NPC 3 ]
(X = 0.0)                         (X = 2.5)                         (X = 5.2)
```

### 8.3 Algoritmo de Posicionamento Não-Colisivo (`viewers/stage_layout.py`)
```python
def calculate_next_model_offset(new_obj: bpy.types.Object, safe_margin: float = 1.0) -> float:
    stage_col = ViewerStage.get_or_create_stage_collection()
    existing_rigs = [o for o in stage_col.objects if o.type == "ARMATURE"]
    
    if not existing_rigs:
        return 0.0
    
    max_x = -float("inf")
    for rig in existing_rigs:
        # Calcula a extensão máxima em X de todos os filhos da malha
        for child in rig.children:
            if child.type == "MESH":
                bbox_corners = [child.matrix_world @ Vector(c) for c in child.bound_box]
                max_x = max(max_x, max(c.x for c in bbox_corners))
    
    # Calcula metade da largura do novo modelo
    new_half_width = 0.5
    for child in new_obj.children:
        if child.type == "MESH":
            bbox = [Vector(c) for c in child.bound_box]
            width = max(c.x for c in bbox) - min(c.x for c in bbox)
            new_half_width = max(new_half_width, width * 0.5)
            
    return max_x + safe_margin + new_half_width
```

---

## Item 9: Auditoria de Cobertura de Assets (100% de Suporte a CGF/CGA/CAF)

### 9.1 Matriz de Formatos e Variantes Requeridas

| Extensão | Tipo de Recurso | Versões CryEngine | Status Atual | Ação Requerida |
|:---|:---|:---:|:---:|:---|
| **.cgf** | Geometria Estática e Rigs | `0x744`, `0x745` | Parcial | Suportar multi-subsets, vertex colors pós-skinning, morph targets. |
| **.cga** | Geometria Animada (portas, baús) | `0x744` | Ausente | Implementar parser para nós cinemáticos internos de CGA. |
| **.chr** | Personagens Crytek Legados | `0x744` | Ausente | Mapear tabela de ossos CHR para hierarquia de Armature. |
| **.cal** | Lista de Animações (Texto) | Cry1 | Parcial | Suportar caminhos relativos variantes com maiúsculas/minúsculas. |
| **.caf** | Animação Binária de Ossos | `0xFFFF0001`, `0xFFFF0002` | Parcial | Suportar ambos os signatures de cabeçalho e ticks fracionários. |
| **.dds** | Texturas | DXT1, DXT3, DXT5, 3Dc/BC5 | Parcial | Converter mapas normais ATI2/3Dc (`_ddn`) para RGBA no shader. |

### 9.2 Script de Auditoria de Cobertura Total (`validation/audit_client_coverage.py`)
Criar rotina que escaneia todos os arquivos do cliente e gera um relatório:
- Total de CGFs existentes no cliente.
- Percentual de CGFs parseados sem erro.
- Percentual de CGFs com skins/pesos válidos vinculados à armadura.
- Total de CAFs referenciados em CALs vs encontrados nos PAKs.
- Log de arquivos não suportados com a causa exata (ex: chunk desconhecido `0xCCCC0018`).

---

## Item 10: Eliminação de Falhas Intermitentes e Garantia de Determinismo

### 10.1 Causas de Intermitência Detectadas
1. **Estado Mutável Global Compartilhado**:
   - `_CLIENT_PROVIDER` e `_MODEL_PROVIDER` armazenados como variáveis globais de módulo em `operators/library_ops.py` sem sincronização com mudanças de cena ou recarregamento de arquivos.
2. **Desatualização do Grafo de Dependências (`Blender Depsgraph`)**:
   - O Blender adia atualizações de malhas e armaduras para o final do loop de eventos. Se a animação for aplicada antes de `bpy.context.view_layer.update()`, as matrizes dos ossos retornam zeros ou valores de identidade (`Matrix.Identity`), quebrando os keyframes.
3. **Sensibilidade de Caixa (Case Sensitivity) em Arquivos Zip**:
   - No Windows o sistema de arquivos não diferencia maiúsculas de minúsculas, mas os arquivos dentro do PAK ZIP podem conter nomes como `ShugoMale_nwalk_001_loop.caf` enquanto o CAL referencia `shugomale_nwalk_001_loop.caf`.

### 10.2 Diretrizes de Correção
- **Sincronização Explícita do Grafo**:
  ```python
  bpy.context.view_layer.update()
  ```
  Sempre executar após criar a armadura e antes de aplicar qualquer pose ou animação.
- **Normalização de Nomes e Case-Insensitive Lookup**:
  O `AionPakArchive` deve normalizar todas as chaves do catálogo para minúsculas (`name.lower().replace('\\', '/')`).
- **Isolamento de Contexto**:
  Cada chamada de carregamento deve instanciar ou validar seus próprios dados sem depender de variáveis residuais em memória.

---

## Checklist Sequencial de Execução (TO-DO do Desenvolvedor)

O desenvolvedor responsável deve executar as tarefas nesta ordem estrita:

### Fase 1: Desempenho e Interface (Eliminar UI Freeze)
- [x] **1.1**: Editar `properties/library_properties.py`: substituir a busca dinâmica em disco no callback de `character_class` por tupla estática pré-computada em memória (`_CACHED_CLASSES`).
- [x] **1.2**: Editar `core/client_provider.py`: remover varreduras síncronas globais do método `__init__`; carregar arquivos de catálogo sob demanda (lazy indexing).
- [x] **1.3**: Otimizar `indexer/asset_database.py`: remover `indent=2` na gravação do cache JSON ou implementar o banco SQLite rápido para busca de assets.
- [x] **1.4**: Adicionar paginação e limite de itens na lista da interface do Blender (`UIList` com no máximo 100 resultados visíveis por vez).

### Fase 2: Rigging e Animações (Corrigir Distorção e Troca de Animação)
- [x] **2.1**: Corrigir matrizes de `BoneInitialPos` em `providers/skeleton_provider.py`: montar matriz 3x3 em ordem row-major direta sem transposição.
- [x] **2.2**: Ajustar `quat_v.conjugated()` em `providers/animation_provider.py` para convenção matemática exata CryEngine 1.
- [x] **2.3**: Reescrever `AnimationProvider.load_animation`: calcular matrizes locais dos ossos (`basis_mat = rest_local.inverted() @ local_mat`) e atribuir diretamente a `pbone.matrix_basis`.
- [x] **2.4**: Corrigir `operators/animation_ops.py` (`AION_OT_switch_animation`): implementar resolução resiliente de arquivos `.caf` localizando-os no PAK correspondente do modelo e em `animations.pak`.
- [x] **2.5**: Chamar `bpy.context.view_layer.update()` antes de inserir os keyframes de animação.

### Fase 3: Visualizador e Múltiplos Modelos (Lineup Viewport)
- [x] **3.1**: Criar propriedade booleana `multi_model_mode` nas configurações da biblioteca.
- [x] **3.2**: Implementar `viewers/stage_layout.py`: calcular a extensão de Bounding Box em X e posicionar novos modelos sequencialmente ao lado dos anteriores.
- [x] **3.3**: Adicionar botão na interface para limpar modelos individuais ou toda a fileira.

### Fase 4: Criação de NPCs e Exportação para Cliente e Emulador
- [x] **4.1**: Criar modelo de dados `AionNPCMetadata` com campos completos (ID, Strings, Dimensões, AI, Tribe, Stats).
- [x] **4.2**: Implementar interface de criação de NPCs no painel do Blender (`ui/npc_editor_panel.py`).
- [x] **4.3**: Implementar injetor em `data/npcs/npcs.pak -> client_npcs.xml` com suporte a compactação ZIP e XOR.
- [x] **4.4**: Implementar injetor em `data/Strings/Strings.pak -> client_strings_npc.xml`.
- [x] **4.5**: Implementar `exporters/emulator_exporter.py`: injetar `<npc_template>` formatado em `Código Fonte - Emulador/game-server/data/static_data/npcs/npc_templates.xml` compatível com `npcs.xsd`.

### Fase 5: Auditoria, Cobertura e Validação
- [x] **5.1**: Executar `validation/run_model_tests.py` em modo headless e verificar passagem dos 15 testes.
- [x] **5.2**: Criar e rodar o teste de troca de múltiplas animações (Idle, Walk, Run, Attack) no Shugo e em monstros (Brax).
- [x] **5.3**: Verificar se o deslocamento máximo de vértices entre repouso e caminhada se mantém anatomicamente consistente (< 0.25m em articulações normais, sem deformação explosiva).

---

## Procedimentos de Teste e Validação de Regressão

### Comando para Testes Headless Automatizados:
```powershell
& "E:\Programas instalados - Leves\Blender\blender.exe" -b --python "validation\run_model_tests.py"
```

### Script de Validação Visual de Animações (Executar no Console do Blender ou via `--python-expr`):
```python
import bpy

# Carrega NPC de teste
bpy.context.scene.aion_model_lib.client_path = r"D:\GameForge\aionclassic"
bpy.ops.aion_model.load_asset(asset_id="shugomale")

# Alterna para animação de caminhada
settings = bpy.context.scene.aion_model_lib
for i, anim in enumerate(settings.active_anims):
    if "walk" in anim.name.lower():
        settings.active_anim_index = i
        bpy.ops.aion_model.switch_animation()
        break

# Inicia reprodução
bpy.ops.aion_model.play_animation()
```

### Critérios de Sucesso Inegociáveis:
1. **Responsividade da Interface**: Troca de cliente ou filtro de texto responde em menos de 100 milissegundos sem travar o ponteiro do mouse.
2. **Fidelidade de Animação**: Modelos humanos, Shugos e monstros executam Idle, Walk e Run sem nenhuma distorção geométrica, membros invertidos ou faces colapsadas.
3. **Consistência Round-Trip**: Novos NPCs criados no Blender aparecem instantaneamente nos XMLs do cliente e no arquivo `npc_templates.xml` do emulador, prontos para spawn em jogo.
