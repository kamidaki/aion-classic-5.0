# Visualizador, Editor e Pipeline de Salvamento Direto de Mapas do Aion para o Blender

Um addon e conjunto de ferramentas de nível de produção para o Blender dedicado a mapas e recursos 3D do CryEngine / Aion Classic.

Suporta importação abrangente de mapas de larga escala, reconstrução de shaders PBR com semântica da CryEngine, sombras estáticas de terreno (Lightmaps `cover_low_shadow.dds`), spawning autoritativo de NPCs com modelos 3D (`client_world_*.xml` e `client_npcs.xml`), instanciamento de malhas por hardware (GPU Indirect Draw), animações ambientais em tempo real (vento em vegetação, ondas em água, rolagem UV), edição interativa (transformação, raycast snap ao terreno, escultura de terreno) e um **fluxo de Salvamento Direto com um clique** que grava modificações nos binários originais (`brush.lst`, `objects.lst`, `land_map.h32`, `mission_mission0.xml`) repacotando o `Level.pak` com backups automáticos `.pak.bak`.

---

## Sumário

1. [Instalação e Requisitos](#1-instalação-e-requisitos)
2. [Primeiros Passos](#2-primeiros-passos)
3. [Visualização e Navegação de Mapas](#3-visualização-e-navegação-de-mapas)
4. [Controles Granulares de Importação e LODs](#4-controles-granulares-de-importação-e-lods)
5. [Spawning Autoritativo de NPCs e Monstros](#5-spawning-autoritativo-de-npcs-e-monstros)
6. [Otimização Extrema para Material Preview e Viewport](#6-otimização-extrema-para-material-preview-e-viewport)
7. [Sombras de Terreno e Pipeline de Shaders](#7-sombras-de-terreno-e-pipeline-de-shaders)
8. [Animação Ambiental em Tempo Real](#8-animação-ambiental-em-tempo-real)
9. [Guia de Edição de Mapas](#9-guia-de-edição-de-mapas)
10. [Fluxo de Salvamento Direto (Mapas Prontos para o Cliente)](#10-fluxo-de-salvamento-direto-mapas-prontos-para-o-cliente)
11. [Guia de Resolução de Problemas](#11-guia-de-resolução-de-problemas)
12. [Suíte de Testes Automatizados e Benchmarks](#12-suíte-de-testes-automatizados-e-benchmarks)

---

## 1. Instalação e Requisitos

### Ambientes Suportados
- **Versões do Blender:** Blender 4.0 LTS, 4.1, 4.2 LTS, 5.0, 5.1 e **Blender 5.2 LTS** (Compatibilidade total com o novo pipeline de renderização Eevee Next).
- **Sistema Operacional:** Windows 10 / Windows 11 (64 bits).
- **Cliente Aion:** Aion Classic (Classic 5.0) ou clientes Retail (4.8, 4.6, 7.7, etc.).
- **Dependências Python:** Nenhuma. 100% Python puro sem DLLs externas, extensões em C ou pacotes pip. Utiliza módulos nativos do Blender (`mathutils`, `bpy`) e da biblioteca padrão (`struct`, `zlib`, `pathlib`).

### Requisitos de Sistema (Otimizado para PC Fraco — 60+ FPS)
- **Memória RAM:** 8 GB ou mais (perfil **PC Fraco / 60+ FPS** reduz drasticamente o consumo de RAM e VRAM).
- **Placa de Vídeo (GPU):** Placa dedicada ou vídeo integrado compatível com OpenGL 4.3+ / Vulkan (sem exigir raytracing ou SSS).
- **Armazenamento:** Pelo menos 10 GB de espaço livre na unidade do cliente Aion para caches sob demanda.

### Procedimento de Instalação

O addon suporta **duas formas de instalação equivalentes no Blender**: via arquivo comprimido `.zip` ou selecionando diretamente a pasta do projeto descompactada.

#### Método A: Instalação via Arquivo ZIP (Recomendado e Universal)
1. Localize o arquivo de instalação `.zip` na pasta de plugins do repositório ([`aion-classic-5.0`](https://github.com/kamidaki/aion-classic-5.0/)):
   ```text
   Ferramentas e Documentos/Blender - Plugins/importador-mapas-lostacademy.zip
   ```
2. No Blender, abra o menu superior: **Editar (Edit)** > **Preferências (Preferences)** > aba **Extensões / Add-ons**.
3. No canto superior direito, clique no menu de opções (ícone de seta/três pontos) e selecione **Instalar a partir do disco... (Install from Disk...)** ou **Instalar de Arquivo... (Install from File...)**.
4. Navegue até a pasta de plugins e selecione o arquivo `importador-mapas-lostacademy.zip`.
5. O Blender descompacta e registra o plugin automaticamente em sua pasta de extensões.
6. Na barra de busca de add-ons, digite `Aion Map Toolkit`.
7. Marque a caixa de seleção ao lado de **Import-Export: Aion Map Toolkit - Editor & Importer** para ativá-lo.

#### Método B: Instalação Selecionando a Pasta ou Cópia Direta
1. **Pela Interface do Blender (Blender 4.2+ / 5.x LTS)**:
   * Em `Preferências` > `Add-ons` > **Instalar a partir do disco...**, você também pode selecionar diretamente o diretório descompactado:
     ```text
     Ferramentas e Documentos/Blender - Plugins/importador-mapas-lostacademy
     ```
2. **Por Cópia Direta no Sistema de Arquivos**:
   * Copie a pasta `importador-mapas-lostacademy` diretamente para a pasta de scripts do seu Blender:
     ```text
     %APPDATA%\Blender Foundation\Blender\<versao>\scripts\addons\importador-mapas-lostacademy
     ```
3. Reinicie o Blender e ative o plugin na lista de Add-ons.

---

## 2. Primeiros Passos

### Configurando o Caminho do Cliente Aion
Antes de carregar mapas ou recursos, configure o caminho da instalação do jogo Aion:
1. Abra a Viewport 3D no Blender.
2. Pressione a tecla `N` no teclado para abrir o painel lateral direito (Sidebar).
3. Clique na aba **Aion Map**.
4. Na seção **Level Management & Import**, localize o campo **Client Root**.
5. Aponte para o diretório raiz da instalação do seu Aion (exemplo: `<caminho-do-cliente-aion-classic>`).
   - O plugin detectará automaticamente as pastas essenciais: `levels/`, `Textures/`, `objects/`, `Data/` e `Shaders/`.

```text
[Painel Lateral Aion Map (N-Panel)]
├── Level Management & Import
│   ├── Client Root: [ <caminho-do-cliente-aion-classic>      ]
│   ├── [ Import Level ]      [ Import CGF ]
│   ├── Perfil de Desempenho (PC Fraco 60+ FPS | Equilibrado | Alta Qualidade)
│   ├── [ Otimizar Viewport 60 FPS ]  [ Limpar Drivers ]  [ Limpar RAM ]
│   └── Categorias de Importação (Terreno, Construções, Props, Vegetação, NPCs, Água, Luzes)
├── Direct Save & Export
│   ├── [ Direct Save Map ]
│   └── [ Create Backup (.pak.bak) ]
├── Live Environment & Animation
│   ├── [ Play / Pause Live Environment ]
│   └── Wind Strength, Wind Speed, Water Flow
└── Map Editing Tools
    ├── [ Snap Selected to Terrain ]
    ├── [ Randomize Jitter (Scatter) ]
    └── [ Sync Sculpted Heights to LandMap ]
```

---

## 3. Visualização e Navegação de Mapas

### Importando um Mapa do Aion
1. Na barra lateral **Aion Map** (ou via menu `Arquivo (File)` > `Importar (Import)` > `Aion Level`), clique em **Import Level**.
2. Navegue até o diretório do mapa desejado:
   - Para um mapa já extraído: selecione a pasta (ex.: `levels/login`, `levels/df1`, `levels/lf1`).
   - Para um mapa intacto no cliente: selecione o próprio arquivo `Level.pak` diretamente! O motor PAK integrado descompactará de forma transparente os dados necessários para o `.aion_cache` sem ferramentas externas.
3. Configure o **Terrain LOD** e as opções granulares de importação.
4. Clique em **Import Aion Level**.

### Modos de Renderização da Viewport
Para visualizar a aparência autêntica do jogo:
- Mude a Viewport 3D para o modo **Material Preview** ou **Rendered (Eevee Next)** (pressione `Z` e escolha *Material Preview*).
- O motor exibirá cores difusas com sRGB correto, relevo normal tangencial, brilho especular, mapas de sombra de terreno multiplicados (`cover_low_shadow.dds`) e transparência de folhagens em alta velocidade.

### Dicas de Navegação em Mapas Extensos
- Pressione `.` no teclado numérico (Numpad .) para centralizar e focar a câmera no objeto selecionado.
- Pressione `Shift + ~` (ou Shift + aspas) para entrar no **Modo de Navegação Livre / Voo (Walk/Fly)** (use `W`, `A`, `S`, `D` e o mouse para navegar pelo mapa como em uma câmera de jogo).

---

## 4. Perfil de Desempenho Único e Categorias de Importação

Os controles redundantes de LOD foram unificados em **um único seletor de Perfil de Desempenho** (`config/performance_profiles.py`), com foco padrão em **PC Fraco / 60+ FPS**:

### Perfis de Desempenho
- **PC Fraco / 60+ FPS (Padrão):**
  - Terreno em passo 4 (`257x257`, ~16x menos vértices) com pesos calculados apenas na grade reduzida e até **6 texturas** dominantes no shader + lightmap de sombra (`cover_low_shadow.dds`).
  - Modelos importados preferencialmente em **LOD 2** (`_lod2.cgf` -> `_lod1.cgf` -> base) com **fusão automática de sub-malhas estáticas** (1 objeto instanciado por modelo na cena em vez de múltiplos sub-objetos).
  - Shaders simplificados sem `Normal Map`, `Gloss`, `Subsurface Scattering` (SSS em folhas), `Transmission` (refração em água), modificadores `SUBSURF`/`WAVE` ou drivers Python por frame.
  - Sombra dinâmica desativada em objetos/folhagens/água e Eevee ajustado (`use_raytracing=False`, `use_fast_gi=False`, `use_shadows=False`, `taa_samples=1`, `use_simplify=True`).
- **Equilibrado:** Terreno passo 2 (`513x513`), modelos **LOD 1**, até **8 texturas** de terreno e mapas normais sem SSS/refração.
- **Alta Qualidade:** Terreno passo 2, modelos base **LOD 0**, até **12 texturas** de terreno e mapas PBR completos.

### Categorias de Elementos (Toggles Independentes)
- **Terreno, Construções, Props, Rochas e Água:** Ativos por padrão e carregados em etapas lineares.
- **Vegetação, Colisão, Luzes Estáticas, Skybox, Efeitos, Animações e NPCs:** Opcionais sob demanda (desmarcados por padrão no perfil leve para manter 60+ FPS imediatos).

---

## 5. Spawning Autoritativo de NPCs e Monstros

A versão 0.7.0 resolve completamente o spawning de NPCs através da extração das tabelas oficiais do Aion Classic:

1. **Origem dos Dados no Cliente:**
   - **Posições no Mundo:** Extraídas de `Data/World/world.pak` -> `client_world_<map>.xml` (ou `client_world_<map>.bxml`), contendo todos os blocos `<spawn name="..." npc_id="...">` com nós de localização tridimensional `<spot x="..." y="..." z="...">`, orientação e instâncias.
   - **Metadados dos NPCs:** Extraídos de `Data/NPCs/npcs.pak` -> `client_npcs.xml` (ou `client_npc_infos.xml` / `client_monsters.xml`), indexando mais de 40.000 templates com nomes, títulos, raças, facções e caminhos dos modelos 3D CGF (`mesh_path`).
2. **Parser BXML Auto-Alinhado:**
   - O interpretador detecta assinaturas UTF-16LE (`"npc_client"`, `"npc_infos"`) e realiza o alinhamento de limite de 2 bytes, garantindo 100% de precisão de caracteres sem desalinhamento de cabeçalho.
3. **Instanciamento Leve por Hardware:**
   - O modelo CGF do NPC é carregado uma única vez na coleção oculta `.NPC_Templates`.
   - Cada NPC posicionado no mapa compartilha diretamente a malha do template (`mesh.data`), consumindo zero memória de geometria duplicada e aproveitando as chamadas indiretas de renderização da GPU.
   - Os NPCs são projetados verticalmente sobre a malha do terreno caso o Z de spawn seja ligeiramente suspenso.

---

## 6. Otimização Extrema para Material Preview e Viewport

O modo **Material Preview** no Blender 4.2 e 5.2 LTS utiliza o motor Eevee Next, que pode congelar caso haja sobrecarga de compilação de shaders ou fragmentação de texturas. As seguintes otimizações de nível de engenharia foram aplicadas:

1. **Deduplicação de Texturas em Tempo Constante $O(1)$:**
   - O `TextureLoader` mantém um registro canônico em memória (`_image_cache`). Imagens idênticas referenciadas por dezenas de materiais compartilham o mesmo datablock `bpy.data.images`, reduzindo drasticamente o consumo de VRAM da placa de vídeo.
2. **Inspeção de Cabeçalho DDS de 128 Bytes:**
   - O carregador inspeciona apenas os primeiros 128 bytes de arquivos DDS para determinar canais de cores, FourCC (DXT1, DXT3, DXT5, ATI2) e dimensões antes de carregar o arquivo completo, evitando travamentos de I/O em disco.
3. **Compartilhamento de Nós de Shader (Principled BSDF):**
   - Materiais idênticos (`MaterialManager`) são reaproveitados entre nós e meshes similares.
4. **Instanciamento por Hardware vs Empties de Coleção:**
   - Objetos e vegetação repetidos utilizam instanciamento direto de malhas vinculadas (`obj.data = template.data`). A GPU renderiza milhares de instâncias em uma única chamada de desenho (Indirect Draw Call), elevando os quadros por segundo (FPS) na viewport e eliminando engasgos ao mover a câmera livremente.
5. **Transparência Otimizada (Hashed / Dithered Alpha):**
   - Folhagens e transparências utilizam `HASHED` / `DITHERED`, eliminando o custo de ordenação de profundidade (alpha sorting) que costuma paralisar o viewport.

---

## 7. Sombras de Terreno e Pipeline de Shaders

Mapas do Aion utilizam lightmaps estáticos pré-calculados para projetar as sombras de montanhas, desfiladeiros e relevos:

1. **Resolução de Lightmaps de Sombra (`cover_low_shadow.dds`):**
   - O importador de terreno resolve automaticamente o mapa de sombras a partir da raiz do mapa ou do pacote `terrainlm.pak`.
2. **Mesclagem Multiply RGB:**
   - Na árvore de nós do terreno (`terrain_blend_nodes.py`), um nó `ShaderNodeMix` em modo `MULTIPLY` multiplica o resultado das texturas de detalhe do terreno pelo mapa de sombras, preservando a fidelidade exata de contraste e profundidade visual do jogo original sem custo de cálculo de sombras em tempo real na GPU.

---

## 8. Animação Ambiental em Tempo Real

Os mapas do Aion possuem ecossistemas dinâmicos com balanço de vento, rios em movimento e ondulações oceânicas. O toolkit implementa animações nativas do Blender que rodam continuamente durante a reprodução da timeline.

### Reproduzindo Animações
- Pressione a **Barra de Espaço (Spacebar)** ou clique em **Play Live Environment** na barra lateral **Aion Map**.
- O mapa ganha vida imediatamente:

1. **Balanço da Vegetação pelo Vento:**
   - Folhas, galhos, arbustos e copas de árvores balançam através de drivers harmônicos senoidais duplos.
   - Os troncos e bases das raízes permanecem ancorados ao solo enquanto as copas se deformam com suavidade.
   - Ajuste a intensidade e frequência usando os controles deslizantes **Wind Strength** e **Wind Speed** no painel.

2. **Ondas e Correntes da Água (Lagos, Rios e Cachoeiras):**
   - Superfícies de lagos e oceanos deformam-se em tempo real gerando ondulações fluidas com modificadores procedurais nativos `WAVE` e relevo dinâmico de ondas.
   - Quedas d'água (waterfalls) e leitos de rios fluem com animação contínua de UV scroll integrada.

3. **Rolagem UV de Shaders (UV Scroll):**
   - Águas superficiais, barreiras mágicas e bandeiras rúnicas rolam suas coordenadas UV ao longo do tempo respeitando as velocidades dos vetores `TexShift` originais do CryEngine.

---

## 9. Guia de Edição de Mapas

O toolkit transforma o Blender em um ambiente autêntico de criação e edição para mapas do Aion.

### 1. Movendo, Rotacionando e Escalando Objetos
- Selecione qualquer estrutura, ponte, casa, decoração ou árvore importada.
- Utilize os atalhos de transformação padrão do Blender (`G`, `R`, `S`).
- O sistema de rastreamento (`roundtrip_tracker`) etiqueta cada objeto com metadados de proveniência (`aion_source_type`, `aion_source_index`, `aion_reference`, `aion_orig_matrix`), garantindo que qualquer alteração de coordenadas seja detectada automaticamente ao salvar.

### 2. Alinhando Objetos ao Terreno (Snap to Terrain)
1. Selecione um ou mais objetos na cena.
2. Na barra lateral, em **Map Editing Tools**, clique em **Snap Selected to Terrain**.
3. Um raycast vertical descendente projeta os objetos com precisão milimétrica sobre a malha do terreno.

### 3. Dispersão Natural de Vegetação (Randomize Jitter)
1. Selecione árvores ou tufos de vegetação.
2. Em **Map Editing Tools**, clique em **Randomize Jitter (Scatter)**.
3. O operador aplica pequenas variações aleatórias de escala (0.85x a 1.15x) e rotação livre de 360 graus no eixo Z.

### 4. Escultura do Heightfield do Terreno
1. Selecione a malha `Aion Terrain` na viewport.
2. Mude do *Modo Objeto (Object Mode)* para o **Modo Escultura (Sculpt Mode)** (`Ctrl + Tab`).
3. Use os pincéis de escultura do Blender (**Draw**, **Clay**, **Smooth**, **Flatten**) para modificar a elevação do relevo.
4. Ao concluir, retorne ao *Modo Objeto*.
5. Na barra lateral, em **Terrain Sculpting**, clique em **Sync Sculpted Heights to LandMap**.
6. O operador lê as alturas Z dos vértices esculpidos e as grava de volta no arquivo binário `terrain/land_map.h32`.

---

## 10. Fluxo de Salvamento Direto (Mapas Prontos para o Cliente)

O fluxo de Salvamento Direto elimina completamente etapas manuais de conversão, extração de pacotes ou ferramentas externas.

```text
[ Editar Mapa no Blender ]
           │
           v
[ Clicar em 'Direct Save Map' ]
           │
           ├── 1. Identifica objetos, brushes, vegetação e terreno modificados
           ├── 2. Grava arquivos binários (brush.lst, objects.lst, land_map.h32)
           ├── 3. Cria backup de segurança Level.pak.bak
           └── 4. Criptografa (XOR-32) e comprime (Deflate) em Level.pak
           │
           v
[ Abrir Cliente Aion ]  --->  Alterações visíveis imediatamente no jogo!
```

### Como Salvar
1. Na barra lateral **Aion Map**, em **Direct Save & Export**, clique no botão destacado **Direct Save Map** (ou use `Arquivo` > `Exportar` > `Aion Direct Save Map`).
2. O addon automaticamente localiza elementos modificados, atualiza os arquivos binários correspondentes, gera o backup `.pak.bak` e repacota o `Level.pak` cifrado.
3. Inicie o cliente do Aion — suas alterações estarão imediatamente visíveis dentro do jogo!

---

## 11. Guia de Resolução de Problemas

### P: Objetos ou árvores aparecem em cinza sólido sem textura.
- **Causa:** O caminho do **Client Root** na barra lateral está incorreto ou incompleto.
- **Solução:** Certifique-se de que a pasta configurada contém `levels/common/`, `Textures/`, `Data/` e `Shaders/shaders.pak`. Em seguida, reimporte o mapa.

### P: Folhas de árvores aparecem como quadrados pretos ou somem ao olhar por trás.
- **Causa:** A opção de culling de faces traseiras (Backface Culling) estava ativada.
- **Solução:** O interpretador 0.7.0 desativa o Backface Culling automaticamente para shaders de vegetação e configura o modo alfa para `HASHED` / `DITHERED`.

### P: NPCs não aparecem após a importação.
- **Causa:** A opção *Import NPCs* foi desmarcada ou o arquivo `Data/World/world.pak` não foi encontrado.
- **Solução:** Mantenha *Import NPCs* marcado e certifique-se de que o **Client Root** aponta para a pasta do Aion onde a pasta `Data/` reside.

### P: "Failed to open Level.pak: Access Denied" (Acesso Negado ao salvar).
- **Causa:** O jogo Aion está aberto em execução e bloqueou o arquivo `Level.pak`.
- **Solução:** Feche o cliente do Aion antes de clicar em **Direct Save Map**.

---

## 12. Suíte de Testes Automatizados e Benchmarks

O toolkit inclui validação automatizada em modo headless (sem interface) e benchmarks de desempenho:

### Executando a Suíte de Testes (Validações Automatizadas)
```powershell
$env:AION_CLIENT_ROOT = "<caminho-do-cliente-aion-classic>"
blender -b --python "validation/run_tests.py"
```

A suíte valida automaticamente:
1. **Addon Package Registration & Module Sanity:** Registro formal do módulo e de todos os operadores no Blender.
2. **Core PAK Engine & Catalog Indexing:** Varredura e indexação de mais de 1.800 arquivos PAK em menos de 2 segundos.
3. **CryEngine Shader Semantics Resolution:** Resolução de técnicas `.csl` e includes `.csi` diretamente de `shaders.pak`.
4. **Format Parsers & Round-Trip Lossless Integrity:** Integridade byte a byte para `brush.lst`, `objects.lst` (10.937 instâncias) e `land_map.h32` (1.048.576 amostras).
5. **CryEngine -> Blender Material Translation:** Construção do grafo de nós PBR Principled BSDF.
6. **Live Environmental Animation Setup:** Configuração dos drivers de vento, ondas e fluxo UV.
7. **Direct Save Map & Round-Trip Scene Sync:** Detecção de transformações e repacotamento em `Level.pak` com backup `.pak.bak`.
8. **Authoritative World & NPC Spawns / Template Parser:** Parser BXML auto-alinhado (40.725 templates de NPC e 82 pontos de spawn em `df1`).
9. **Granular Import Classification & Hardware Mesh Instancing:** Roteamento de categorias e instanciamento indireto por hardware.
10. **Baked Terrain Shadow Lightmap Resolution & Multiply RGB Blending:** Resolução de `cover_low_shadow.dds` e nó de multiplicação RGB no shader de terreno.

### Executando o Benchmark de Importação
```powershell
$env:AION_CLIENT_ROOT = "<caminho-do-cliente-aion-classic>"
blender -b --python "validation/benchmark_import.py"
```
Mede tempos de execução, contagem de objetos, malhas, materiais, imagens e instâncias de posicionamento.



---

## 13. Arquitetura Multi-Client & Engenharia de Desempenho 2.0

### Compatibilidade Multi-Client Homologada
O toolkit detecta automaticamente e adapta estruturas de dados para 4 gerações de clientes:
- **Classic 5.0**: 137 mapas, 79.340 strings localizadas, 81.446 arquétipos de NPCs.
- **Retail 4.8**: 184 mapas, 134.453 strings localizadas, 254.372 arquétipos.
- **Retail 4.6**: 154 mapas, 97.764 strings. Suporte transparente com detecção de criptografia proprietária `OADTENC1`.
- **Retail 7.7**: 178 mapas, 189.800 strings localizadas, 186.856 arquétipos.

### Resolução de Congelamentos (Pipeline Linear Não-Bloqueante v2.1.0 em 8 Etapas)
Todo travamento de interface foi eliminado com execução estritamente **linear e não-bloqueante** (uma etapa conclui 100% antes de iniciar a próxima, sem capturar cliques do Blender):
1. **Timers Nativos (`bpy.app.timers` Sem Trava Modal):** A importação não utiliza mais operador modal nem `progress_begin` bloqueante. A viewport, menus e cliques continuam 100% livres durante o carregamento, com barra de progresso ao vivo e botão **Cancelar Importação** no painel `Aion Map`.
2. **Thread Única Segura (`RLock` + Escrita Atômica + LRU de PAKs):** Descompactação de `Level.pak`, indexação `.pak`, parsing de `mission_mission0.xml`, geração de buffers do terreno e extração de CGFs/NPCs rodam em fila única protegida por `threading.RLock`, limite LRU de 16 arquivos abertos, cancelamento cooperativo via `Event` e escrita atômica em cache.
3. **Cache de Shaders $O(1)$ e Construção Fatiada:** Técnicas `.csl` de `shaders.pak` são indexadas em tabela hash $O(1)$, templates CGF multi-parte e nós multi-materiais (`iter_load_cgf`) cedem o frame a cada ~6 ms sem recriar coleções na raiz da cena, e volumes `NoDraw`/colisão invisíveis sem geometria visual são ignorados corretamente sem falsos erros.
4. **Ordem Linear das Etapas:** `[1/8] Level.pak` -> `[2/8] Catálogo` -> `[3/8] Terreno` -> `[4/8] Água & Luzes` -> `[5/8] Modelos CGF (1 por vez + instâncias em lotes de 24)` -> `[6/8] CGA/Dinâmicos` -> `[7/8] NPCs (somente após o mapa terminar, com interpolação bilinear $O(1)$ no heightfield do terreno)` -> `[8/8] Otimização Viewport 60 FPS e fechamento de handles`.
5. **Painéis Zero-I/O & Sem Miniaturas Pesadas:** Os painéis consultam caches em memória, sem varredura de disco em `draw()` nem renderização automática em massa de miniaturas 3D.
6. **Fusão de Sub-Malhas Estáticas (`bmesh` + `batch_remove`):** Modelos compostos por várias partes são unificados no template antes da instanciação GPU com remoção em lote via `bpy.data.batch_remove`, reduzindo em 3x–10x o número de objetos e draw calls sem picos na thread principal.

### Sistema Automático de LOD Companion (`_lod2`, `_lod1`, `_lod0`)
O perfil selecionado em **Perfil de Desempenho** escolhe automaticamente a melhor malha disponível (`_lod2.cgf` no perfil PC Fraco, `_lod1.cgf` no Equilibrado e base `.cgf` na Alta Qualidade), com fallback gracioso.

### Nameplates Tridimensionais de NPCs (Opcional)
Quando **Importar NPCs** e **NPC 3D Nameplates** são marcados manualmente, placas de identificação leves em texto 3D (`NPCLabel_{id}`) são criadas na coleção `NPC_NAMES` (desativadas por padrão para máximo FPS).

### Edição Completa de Mapas (Adicionar, Mover, Deletar, Repacotar)
O pipeline de edição agora suporta operações completas:
- **Mover, Girar e Escalar:** Salva coordenadas diretamente nos nós de `brush.lst` e `objects.lst`.
- **Duplicar / Adicionar (`Shift+D`):** Identifica novos objetos e adiciona novas entradas aos blocos de malhas e nós binários.
- **Deletar (`X`):** Detecta a ausência de objetos originais na cena e remove os registros correspondentes do arquivo binário.
- **Edição de NPCs:** Atualiza posições em `client_world_<map>.xml`.
- **Salvamento Direto:** Repacota o `Level.pak` com backup de segurança `.pak.bak` em menos de 2 segundos.
