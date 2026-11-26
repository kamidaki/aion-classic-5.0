# Lost Academy — Importador de Modelos 3D (Aion Model Library)

Biblioteca visual de ativos, visualizador 3D, reprodutor de animações esqueléticas e editor transacional de modelos CryEngine `.cgf` / `.cga` / `.cal` / `.caf` nativo para **Blender 4.0 a 5.2+ LTS**, integrado ao projeto **[Aion Classic 5.0 — Lost Academy Group](https://github.com/kamidaki/aion-classic-5.0/)**.

---
Alguns prints durante os testes (LEMBRANDO QUE O PLUGIN ESTÁ LONGE DE FICAR PRONTO, estimo que esteja em uns 60%, os outros 40% são animações, estados, efeitos visuais e sonoros, entre outras coisas)
<img width="1907" height="1042" alt="image" src="https://github.com/user-attachments/assets/893abccd-854d-479e-bbc7-4583d3743cbd" />
<img width="3839" height="1041" alt="image" src="https://github.com/user-attachments/assets/2f18896d-2440-49fc-897c-4663063c8c7a" />
<img width="1916" height="1016" alt="image" src="https://github.com/user-attachments/assets/e8918550-e040-448a-9732-6ef76ce8df28" />
<img width="1897" height="963" alt="image" src="https://github.com/user-attachments/assets/84663423-b5b3-443a-b3b7-f2743b3ac377" />

## Visão Geral: Pipeline Bidirecional Completo

O **Importador de Modelos 3D (Aion Model Library)** transforma o Blender em uma estação de trabalho para inspeção visual, rigging, animação e edição transacional de modelos do Aion no ciclo completo:

$$\mathbf{CLIENTE} \longrightarrow \mathbf{INDEXA\c{C}\tilde{A}O} \longrightarrow \mathbf{VISUALIZA\c{C}\tilde{A}O} \longrightarrow \mathbf{EDI\c{C}\tilde{A}O} \longrightarrow \mathbf{SALVAMENTO} \longrightarrow \mathbf{CLIENTE}$$

Seja para inspecionar e ajustar personagens, monstros, armas, armaduras e asas oficiais, ou para criar e exportar novos NPCs e modelos do zero, o add-on oferece visualização com iluminação de estúdio, reprodução de animações em tempo real e gravação segura com backups automáticos `.bak` / `.pak.bak`.

---

## Principais Recursos

### 1. Indexador de Ativos e Busca Rápida
- **Varredura Recursiva (`indexer/scanner.py`):** Descobre modelos (`.cgf`, `.cga`), esqueletos, listas de animação (`.cal`) e sequências de quadros-chave (`.caf`) em pastas soltas e arquivos `.pak` (ZIP padrão e XOR-32), sem carregar as malhas inteiras na memória.
- **Classificação por Categorias:** Organiza ativos em categorias como `NPC`, `MONSTER`, `CHARACTER`, `WEAPON`, `ARMOR`, `WINGS`, `PET_MOUNT`, `BUILDING`, `PROP`, `VEGETATION`, `OBJECT` e `EFFECT`.
- **Busca Instantânea e Cache em Disco:** Suporta filtros por nome, ID, caminho e categoria, salvando metadados em `.aion_model_index.json` e miniaturas PNG em `.aion_model_thumbs/`.

### 2. Suporte Multi-Client
Detecta e adapta automaticamente diferentes gerações de clientes Aion:
- **GameForge Classic (EU) / Classic 5.0:** Templates BXML e pacotes `.pak` com ofuscação XOR-32.
- **Clientes Retail 4.8 / Estruturas Híbridas:** XML UTF-8/UTF-16 e pacotes `.pak` ZIP padrão.
- **Clientes 3.9 Legacy:** XML UTF-16LE com BOM e estruturas CryEngine legadas.

### 3. Visualizador 3D, Áudio, VFX e Reprodutor de Animações
- **Palco Isolado (`Aion_Model_Viewer`):** Gerencia objetos carregados com iluminação de estúdio de 3 pontos (Key, Fill e Rim) e suporte a alinhamento de múltiplos modelos (`stage_layout.py`).
- **Predefinições de Câmera e Viewport:** Atalhos de visão Frontal, Lateral, Topo, Perspectiva/Ortográfica e enquadramento automático.
- **Sequenciador `.cal` e Transporte:** Lista animações associadas ao modelo (`idle`, `walk`, `run`, `attack`, etc.) com controles de reproduzir, pausar, parar e avanço quadro a quadro.
- **Áudio e Efeitos Visuais:** Suporte experimental a descoberta de áudios (`sound_provider.py`) e aplicação de efeitos visuais elementais em cena (`effect_provider.py`).

### 4. Editores Integrados
- **Malha e Geometria (`mesh_editor.py`):** Acesso rápido a *Edit Mode*, *Sculpt Mode* e recálculo de normais externas.
- **Coordenadas UV (`uv_editor.py`):** Abertura de UV por ângulo e empacotamento de ilhas.
- **Esqueleto e Armature (`skeleton_editor.py`):** Adição, renomeação e reparentamento de ossos com sincronização dos grupos de vértices.
- **Materiais e Texturas (`material_editor.py`):** Ajustes de *Principled BSDF* (*roughness*, emissão, *backface culling*) e reatribuição de slots de textura.
- **Criador e Clonador de Modelos (`model_creator.py`, `model_cloner.py`):** Converte malhas do Blender em `.cgf` com UVs, materiais e pesos de skinning ou clona ativos existentes.

### 5. Pipeline de Salvamento Seguro e Integração com o Emulador
- **Modo Seguro por Padrão (`allow_client_write = False`):** Alterações são gravadas em diretório seguro de exportação, protegendo os arquivos do cliente contra gravações acidentais.
- **Staging Atômico e Backups:** Valida cabeçalhos antes de gravar, cria backups `.bak` / `.pak.bak` automaticamente e permite restauração (*rollback*) a partir do backup.
- **Exportador de Metadados de NPC (`emulator_exporter.py` / `client_exporter.py`):** Auxilia na geração de entradas de `npc_templates.xml` para o emulador (`AION_EMULATOR_ROOT` ou árvore local do repositório em `Código Fonte - Emulador/game-server-gameforge/data/static_data/npcs/npc_templates.xml`).

---

## Instalação e Configuração

O add-on suporta **duas formas de instalação no Blender (4.0 a 5.2+ LTS)**:

### Método A: Instalação via Arquivo `.zip` (Recomendado)
1. Localize o pacote distribuível no repositório:
   ```text
   Ferramentas e Documentos/Blender - Plugins/importador-modelos3d-lostacademy.zip
   ```
2. No Blender, acesse **Editar (Edit)** > **Preferências (Preferences)** > **Extensões / Add-ons**.
3. Clique no menu superior direito de opções e escolha **Instalar a partir do disco... (Install from Disk...)**.
4. Selecione o arquivo `importador-modelos3d-lostacademy.zip`.
5. Na busca de add-ons, localize e marque:
   `Import-Export: Lost Academy - Importador de Modelos 3D (Aion Model Library)`

### Método B: Instalação via Pasta Descompactada ou Cópia Direta
1. Copie a pasta `importador-modelos3d-lostacademy` (de `Ferramentas e Documentos/Blender - Plugins/`) para o diretório de add-ons do seu Blender:
   ```text
   %APPDATA%\Blender Foundation\Blender\<versao>\scripts\addons\importador-modelos3d-lostacademy
   ```
2. Ou crie um link simbólico apontando para a pasta do repositório, reinicie o Blender e ative o add-on em **Preferências > Add-ons**.

---

## Guia de Uso Passo a Passo

1. **Detecção e Varredura do Cliente:**
   - Abra a aba **Modelos Aion** na barra lateral direita (`N`) da Viewport 3D.
   - Em **Configuração do Cliente**, selecione a pasta raiz da sua instalação do Aion (ou clique em detectar) e execute **Scan Client Assets**.
2. **Busca e Carregamento:**
   - Selecione uma categoria (`NPC`, `MONSTER`, `WEAPON`, etc.) e filtre pelo nome ou ID.
   - Clique em **Load in Viewer** para carregar o modelo no palco `Aion_Model_Viewer`.
3. **Animações:**
   - Expanda o subpainel de animações, escolha uma sequência `.cal` e utilize **Play / Pause** e **Stop**.
4. **Edição e Salvamento:**
   - Edite malha, ossos, UVs ou materiais normalmente no Blender.
   - Mantenha `Allow Client Write` desmarcado para exportar para a pasta segura, ou habilite-o explicitamente quando desejar gravar com backup automático `.bak` / `.pak.bak`.

---

## Suíte de Testes Automatizados

Os scripts de validação headless devem ser executados com a variável de ambiente `AION_CLIENT_ROOT` apontando para o diretório do cliente Aion:

```powershell
$env:AION_CLIENT_ROOT = "<caminho-do-cliente-aion-classic>"
blender -b --python "validation/run_model_tests.py"
```

### Principais Testes Cobertos em `validation/`
- `run_model_tests.py`: suíte principal cobrindo registro do add-on, descoberta de cliente, scanner, cache/database, miniaturas, carregamento de modelo/rig/animações, controles de câmera, editores de malha/esqueleto/material, salvamento seguro e rollback.
- `test_roundtrip.py`: validação de escrita e leitura binária (`.cal`, `.caf`, `.cgf`).
- `test_npc_export.py`: validação de metadados de NPC, exportação e layout de múltiplos modelos.
- `test_shugo_walk.py`, `test_sound_and_vfx.py`, `test_indexer.py`, `test_fixes.py`, `audit_client_coverage.py`.

---

## Arquitetura de Diretórios

```text
importador-modelos3d-lostacademy/
├── __init__.py                    # Registro do add-on e bl_info
├── README.md                      # Guia de instalação e uso
├── CONTEXT.md                     # Especificação técnica e formatos binários
├── config/
│   ├── __init__.py
│   └── settings.py                # Categorias, caches e configuração via AION_CLIENT_ROOT
├── core/
│   ├── __init__.py
│   ├── change_tracker.py          # Rastreamento de modificações e hashes SHA-256
│   ├── client_detector.py         # Detecção de geração/flavor do cliente
│   ├── client_provider.py         # Camada unificada de acesso a ativos e PAKs
│   ├── pak_engine.py              # Leitura/atualização atômica ZIP e XOR-32
│   └── transaction_manager.py     # Staging temporário, backups .bak/.pak.bak e rollback
├── formats/
│   ├── cgf/                       # Parsers e writers para CGF, CGA, CAL, CAF e esqueleto
│   └── dds/                       # Inspetor de cabeçalho DDS (128 bytes)
├── indexer/                       # Scanner, grafo de dependências, cache e thumbnails
├── providers/                     # Construtores de modelo, rig, animação, shader, som e VFX
├── viewers/                       # Palco de estúdio, lineup, câmera, display e player
├── editors/                       # Editores de malha, UV, rig, animação, material, criador e clonador
├── exporters/                     # Salvamento direto, exportação solta, NPC metadata e emulador
├── properties/                    # Propriedades da cena e listas de UI
├── operators/                     # Operadores do Blender (N-Panel)
├── ui/                            # Painéis e menus da interface
└── validation/                    # Scripts de validação headless no Blender
```

---

## Créditos e Licença

- Desenvolvido pela equipe **Lost Academy Group** no repositório [https://github.com/kamidaki/aion-classic-5.0/](https://github.com/kamidaki/aion-classic-5.0/).
- Dependências Python externas: **nenhuma** (100% biblioteca padrão do Python + `bpy` / `mathutils` nativos do Blender).
