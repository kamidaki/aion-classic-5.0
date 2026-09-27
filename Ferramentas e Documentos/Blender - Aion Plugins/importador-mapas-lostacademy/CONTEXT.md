# Aion Blender Toolkit: Referência Técnica de Arquitetura e Desenvolvimento (CONTEXT.md)

**Versão do Documento:** 1.1.0 (Versão do Toolkit: 0.7.0)  
**Ambiente Alvo:** Blender 4.0 - 5.2+ LTS, Python 3.10 - 3.11  
**Localização Canônica do Projeto:** `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins\importador-mapas-lostacademy`  
**Pacote Instalável (.ZIP):** `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins\importador-mapas-lostacademy.zip`  
**Modalidades de Instalação Suportadas:** Instalação via arquivo comprimido `.zip` ou seleção direta da pasta fonte no Blender.

---

## 1. Objetivo e Escopo do Projeto

O **Aion Blender Toolkit (Lost Academy Importer)** é um addon modular em Python de nível profissional para o Blender, fornecendo ferramentas completas de ponta a ponta para recursos 3D e mapas mundiais da CryEngine 1 / Aion Classic:
1. **Importador de Recursos (Assets):** Importa malhas estáticas `.cgf` e entidades animadas `.cga` com fidelidade total de materiais e texturas.
2. **Importador de Mapas (Levels):** Carrega mapas de múltiplos quilômetros quadrados diretamente de arquivos oficiais `Level.pak` ou de estruturas de pastas já extraídas.
3. **Interpretador de Shaders e Materiais PBR:** Converte técnicas de shaders fixos e programáveis da CryEngine em árvores de nós modernas `Principled BSDF` do Blender 4.0 - 5.2, incluindo mapas de relevo normal, brilho especular, emissão de brilho e recorte de transparência alfa bifacial.
4. **Sombras de Terreno (Baked Lightmaps):** Integração automática de `cover_low_shadow.dds` (ou de `terrainlm.pak`) via nós `ShaderNodeMix` em modo `MULTIPLY` na mesclagem multicamada do relevo.
5. **Spawning Autoritativo de NPCs e Monstros:** Extração e posicionamento tridimensional de criaturas e NPCs a partir de `world.pak` (`client_world_*.xml`) e `npcs.pak` (`client_npcs.xml`) com instanciamento leve por hardware (GPU Indirect Draw).
6. **Controles Granulares de Importação:** Toggles independentes para Terreno, Prédios, Props, Vegetação, Água, Efeitos, Luzes, Sombras, Colisão e NPCs, além de filtragem de LOD 0 a 3.
7. **Animação Ambiental em Tempo Real:** Anima o balanço da vegetação pelo vento, deslocamento de ondas em corpos d'água e fluxo de coordenadas UV em tempo real na reprodução da timeline da viewport.
8. **Ambiente Interativo de Autoria de Mapas:** Permite editar estruturas do mundo, dispersar vegetação com rotação/escala naturais e esculpir o relevo do terreno diretamente no Modo Escultura do Blender.
9. **Exportador com Salvamento Direto (Pronto para o Jogo):** Serializa objetos de cena modificados de volta para os formatos binários oficiais (`brush.lst`, `objects.lst`, `land_map.h32`, `mission_mission0.xml`) e repacota o arquivo `Level.pak` do cliente com criação automática de backups `.pak.bak`.

---

## 2. Arquitetura de Diretórios e Módulos

```text
importador-mapas-lostacademy/
├── __init__.py                 # Ponto de entrada do addon; registra propriedades, operadores, UI e menus
├── README.md                   # Tutorial de uso, guia de fluxo de trabalho e manual de resolução de problemas
├── CONTEXT.md                  # Especificação técnica para desenvolvedores e agentes de IA (este documento)
│
├── config/                     # Configurações do toolkit, caminhos padrão e constantes
│   ├── __init__.py
│   └── settings.py             # Caminhos padrão do cliente, grades de LOD, constantes de vento e escalas
│
├── core/                       # Motor central de arquivos PAK e resolução de recursos em baixo nível
│   ├── __init__.py
│   ├── pak_engine.py           # AionPakArchive, desofuscação XOR-32, AionCatalogIndex, Descompactador e Repacotador
│   └── resource_resolver.py    # Resolvedor multi-nível de CGF (arquivos soltos -> cache do mapa -> common -> PAKs)
│
├── formats/                    # Parsers e serializadores binários e XML puros (sem dependências do Blender)
│   ├── __init__.py
│   ├── cgf/                    # Formato binário CGF/CGA da CryEngine
│   │   ├── __init__.py
│   │   ├── parser.py           # Leitor da tabela de chunks (Nós, Geometrias, Materiais, Controladores, Hitboxes)
│   │   ├── diagnostics.py      # Diagnósticos de cobertura de chunks do formato
│   │   ├── shader_semantics.py # Parser de técnicas .csl e includes .csi direto do shaders.pak
│   │   └── texture_sequences.py# Decodifica sequências de quadros de texturas difusas
│   └── level/                  # Parsers e serializadores dos formatos de mapa do Aion / CryEngine
│       ├── __init__.py
│       ├── brush.py            # Leitor e gravador binário de brush.lst (estruturas, edifícios, pontes, props)
│       ├── objects.py          # Leitor e gravador binário de objects.lst (posicionamento de vegetação e folhagens)
│       ├── terrain.py          # Leitor e gravador binário de land_map.h32 (heightfield de 16 bits do terreno)
│       ├── leveldata.py        # Parser de leveldata.xml (dimensões, nível da água, lista de materiais)
│       ├── npc_spawns.py       # Parser BXML auto-alinhado de client_world_*.xml e client_npcs.xml
│       ├── mission_placeables.py # Parser e serializador de atualizações do mission_mission0.xml
│       └── ...
│
├── materials/                  # Gerenciamento de materiais e construção de grafos de shaders
│   ├── __init__.py
│   ├── texture_loader.py       # Carregador DDS com inspeção de cabeçalho (128 bytes) e deduplicação O(1)
│   ├── shader_interpreter.py   # Gerador de nós CryEngine -> Principled BSDF (difuso, relevo, especular, alfa)
│   ├── material_manager.py     # Desduplicação, cache de materiais e atribuição de slots CGF
│   ├── terrain_materials.py    # Shaders de mesclagem multi-camada para o terreno
│   └── water_materials.py      # Shaders de superfícies líquidas (água e lava)
│
├── animations/                 # Sistemas de animação ambiental em tempo real
│   ├── __init__.py
│   ├── wind_system.py          # Deformação harmônica senoidal dupla para vegetação com troncos fixos
│   ├── water_animation.py      # Modificadores de deslocamento procedural WAVE para corpos d'água
│   ├── uv_scroll.py            # Drivers scriptados para rolagem de coordenadas UV baseadas em TexShift
│   ├── cga_animator.py         # Extrapolação de quadros-chave para controladores rotacionais CGA
│   └── environment_animation.py# Coordenador mestre de animação da cena
│
├── editing/                    # Ferramentas de autoria, rastreamento de metadados e serialização de cena
│   ├── __init__.py
│   ├── roundtrip_tracker.py    # Rastreia procedência, índices e matrizes dos objetos (collect_scene_changes)
│   ├── terrain_editor.py       # Sincroniza elevações Z esculpidas no Blender de volta para o land_map.h32
│   ├── object_editor.py        # Alinhamento vertical por raycast no terreno e dispersão com jitter aleatório
│   └── level_serializer.py     # Serializa alterações da cena do Blender de volta para os arquivos do mapa
│
├── exporters/                  # Pipeline de empacotamento e exportação para o cliente
│   ├── __init__.py
│   └── level_exporter.py       # Salvamento Direto em um clique: serializa cena -> empacota Level.pak -> backup
│
├── importers/                  # Construtores de cena de alto nível no Blender
│   ├── __init__.py
│   ├── cgf_importer.py         # Construtor de malha CGF, mapeador UV e atribuidor de materiais
│   ├── level_importer.py       # Orquestrador do mapa (terreno, brushes, objetos, água, iluminação, NPCs)
│   ├── level_instances.py      # Instanciamento de malhas por hardware (GPU Indirect Draw)
│   ├── level_jobs.py           # Classificação e desduplicação de tarefas por categoria (Buildings, FX, Props, etc.)
│   ├── level_templates.py      # Agrupamento e gestão de templates CGF na coleção oculta .Level_Templates
│   ├── npc_importer.py         # Instanciador de NPCs com carregamento de CGF e raycast snap ao terreno
│   ├── terrain_blend_nodes.py  # Árvore de nós de mesclagem do terreno com lightmap de sombra (Multiply RGB)
│   └── level_summary.py        # Relatório de execução e estatísticas de importação
│
├── properties/                 # Propriedades customizadas do Blender e configurações da cena
│   ├── __init__.py
│   └── scene_properties.py     # bpy.types.Scene.aion_settings (toggles granulares, LODs, caminhos)
│
├── operators/                  # Operadores do Blender (ações de interface e importação/exportação)
│   ├── __init__.py
│   ├── import_cgf.py           # AION_OT_import_cgf
│   ├── import_level.py         # AION_OT_import_level_folder
│   ├── export_level.py         # AION_OT_direct_save, AION_OT_export_level, AION_OT_repack_level
│   └── editing_operators.py    # AION_OT_snap_to_terrain, AION_OT_randomize_transforms, AION_OT_sync_terrain
│
├── ui/                         # Interface da barra lateral na Viewport 3D (N-panel)
│   ├── __init__.py
│   └── panels.py               # AION_PT_main_panel, level_io, granular_options, direct_save, live_environment
│
└── validation/                 # Suíte de testes automatizados e scripts de benchmark
    ├── __init__.py
    ├── run_tests.py            # Executor automatizado com 10 validações em modo headless
    └── benchmark_import.py     # Script de benchmark para medição de carregamento e contagem de datablocks
```

---

## 3. Formatos de Dados Suportados do Aion

| Formato | Função no Jogo | Módulo Leitor (Parser) | Módulo Serializador / Exportador |
| :--- | :--- | :--- | :--- |
| **`Level.pak`** | Pacote compactado do mapa | `core.pak_engine.AionPakArchive` | `core.pak_engine.pack_level_directory` |
| **`brush.lst`** | Estruturas fixas, pontes, prédios | `formats.level.brush.parse_brush_lst` | `formats.level.brush.write_brush_lst` |
| **`objects.lst`** | Instâncias de folhagem/vegetação | `formats.level.objects.parse_objects_lst`| `formats.level.objects.write_objects_lst`|
| **`land_map.h32`** | Heightfield de 16 bits do relevo | `formats.level.terrain.parse_land_map_h32` | `formats.level.terrain.write_land_map_h32` |
| **`leveldata.xml`**| Limites do mapa, água, materiais | `formats.level.leveldata.parse_leveldata` | Preservação direta sem modificação |
| **`mission_mission0.xml`** | Entidades de missão posicionadas | `formats.level.mission_placeables` | `update_mission_placeables_xml` |
| **`staticdeferredlights.lst`** | Luzes pontuais e marcadores | `formats.level.static_lights` | Preservação direta sem modificação |
| **`client_world_*.xml`** | Spawns tridimensionais de NPCs | `formats.level.npc_spawns.parse_world_spawns_bxml` | Consulta somente leitura |
| **`client_npcs.xml`** | Metadados e modelos de NPCs | `formats.level.npc_spawns.parse_npc_templates_bxml` | Consulta somente leitura |
| **`cover_low_shadow.dds`** | Lightmap de sombras do terreno | `importers.terrain_blend_nodes` | Nó Multiply RGB |
| **`.cgf`** | Geometria e materiais CryEngine | `formats.cgf.parser.get_cgf` | Construção de malhas na cena |
| **`.cga`** | Entidade animada e controladores | `formats.cgf.parser.get_cgf` | `animations.cga_animator` |
| **`.csl` / `.csi`**| Definições de shaders do cliente | `formats.cgf.shader_semantics` | `materials.shader_interpreter` |
| **`.dds`** | Texturas DirectDraw Surface | `materials.texture_loader` | `bpy.data.images.load` |

---

## 4. Funcionamento dos Subsistemas

### 4.1. Motor PAK e Desofuscação XOR
Os arquivos `.pak` do Aion utilizam uma variante do formato ZIP com:
- Assinaturas customizadas de 4 bytes: Cabeçalho Local (`0xafb4fcfb`), Diretório Central (`0xafb4fefd`), Fim do Diretório Central / EOCD (`0xafb4faf9`).
- Criptografia de fluxo: Os dados são comprimidos em Deflate cru (Método 8, `wbits=-15`) ou armazenados sem compressão (Método 0) e em seguida sofrem operação XOR contra uma janela cíclica de 32 bytes gerada a partir de uma tabela mestra estática de 1056 bytes (`AION_XOR_TABLE`).
- O método `deobfuscate_stream(data)` no módulo `core.pak_engine` utiliza laços rápidos desempacotando inteiros de 64 bits (`struct.unpack_from("<Q")`), processando mais de 100 MB/s por núcleo em Python puro.

### 4.2. Indexador Global de Catálogo (`AionCatalogIndex`)
No cliente do Aion, os recursos são distribuídos em centenas de arquivos PAK distintos:
- `levels/common/Mesh_Textures_000.pak` até `106.pak`
- `Textures/*.pak`
- `objects/*.pak`
- `Data/World/world.pak` e `Data/NPCs/npcs.pak`
- `Shaders/shaders.pak`

O `AionCatalogIndex` lê apenas os cabeçalhos do Diretório Central (64 bytes por entrada) sem descompactar o conteúdo interno, construindo tabelas de dispersão em memória:
1. `_path_to_pak_entry`: Caminho relativo minúsculo completo -> `(pak_path, entry)`.
2. `_basename_to_pak_entry`: Nome base do arquivo (`cliff_01.dds`) -> `(pak_path, entry)`.

Mais de 1.800 arquivos PAK são indexados em menos de 2 segundos, possibilitando consultas imediatas em tempo constante $O(1)$.

### 4.3. Spawning Autoritativo de NPCs e Instanciamento Leve por Hardware
- **Detecção de Limite BXML:** Arquivos BXML da CryEngine possuem cabeçalhos de tamanho variável (6 ou 7 bytes). A função `parse_npc_templates_bxml` e `parse_world_spawns_bxml` utilizam busca de padrão de tokens (`"npc_client".encode("utf-16le")` e `"npc_infos".encode("utf-16le")`) alinhando o cursor na fronteira par de 2 bytes, garantindo 100% de estabilidade na extração de tags UTF-16LE.
- **Instanciamento por Hardware:** Em vez de instanciar coleções inteiras com `bpy.data.objects.new(name, None)` (o que gera sobrecarga no dependency graph e atrasa o Material Preview), cada objeto instanciado é criado como `bpy.data.objects.new(name, template_mesh.data)`. A GPU do Blender agrupa as instâncias sob uma única chamada de desenho indireta (Indirect Draw Call).
- **Ajuste Vertical ao Terreno:** NPCs com Z de posicionamento suspenso são projetados verticalmente sobre a malha do terreno via raycast descendente, garantindo contato visual perfeito com o solo.

### 4.4. Otimizações de Material Preview e Sombras de Terreno
- **Deduplicação de Texturas:** `TextureLoader` mantém `_image_cache` mapeando caminhos canônicos para `bpy.data.images`, evitando carregamento redundante de DDS na memória de vídeo.
- **Inspeção de Cabeçalho DDS (128 Bytes):** Inspeciona apenas a estrutura binária `DDS_HEADER` para extrair dimensões e FourCC sem decodificar desnecessariamente o fluxo completo de mipmaps do disco.
- **Lightmap de Sombra (`cover_low_shadow.dds`):** No terreno, um nó `ShaderNodeMix` em modo `MULTIPLY` multiplica as texturas de detalhe do terreno pelo mapa de sombras estático, reproduzindo as sombras de relevo fiéis do CryEngine com zero impacto de cálculo de luz dinâmica em tempo real.
- **Transparência Otimizada:** Folhagens e elementos transparentes são configurados para `HASHED` / `DITHERED`, eliminando os congelamentos provocados pelo cálculo de ordenação de profundidade no Eevee Next.

---

## 5. Padrões de Código e Diretrizes de Manutenção

Ao dar manutenção ou estender este projeto:
1. **Separação Rígida de Responsabilidades:**
   - Parsers e serializadores binários em `formats/` NUNCA devem importar módulos do Blender (`bpy`). Devem permanecer bibliotecas Python puras e testáveis isoladamente.
   - Construção de objetos na cena pertence a `importers/`.
   - Rastreamento e serialização de cena pertencem a `editing/` e `exporters/`.
   - Menus e painéis visuais pertencem a `ui/`.
2. **Zero Dependências Externas:** Não adicione pacotes pip ou bibliotecas compiladas externas. O addon deve funcionar imediatamente em qualquer instalação padrão do Blender LTS.
3. **Preservação Sem Perdas (Lossless):** Nunca descarte bytes não compreendidos nos arquivos da CryEngine. Todos os parsers devem reter campos de cabeçalho desconhecidos e bytes finais (`trailing_bytes`).
4. **Modificação Mínima (Non-destructive):** O exportador só deve reescrever os registros que o usuário alterou ativamente no Blender, preservando a identidade binária dos elementos não modificados.
5. **Validação Contínua (10/10 Testes):** Após alterar qualquer parser, serializador ou interpretador de shaders, execute sempre a suíte de testes automatizada:
   ```powershell
   & "E:\Programas instalados - Leves\Blender\blender.exe" -b --python "validation/run_tests.py"
   ```
   Certifique-se de que todos os 10 testes passem antes de entregar alterações.

