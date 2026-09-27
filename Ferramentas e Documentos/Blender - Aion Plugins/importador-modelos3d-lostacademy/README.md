# Lost Academy - Importador de Modelos 3D (Aion Model Library)

A production-quality visual asset library, 3D model viewer, animation player, and full-featured CryEngine CGF / CAL / CAF asset editor built natively for Blender 4.0 - 5.2+ LTS.

---

## 🌟 Overview: The Complete Aion Asset Pipeline

The **Lost Academy - Importador de Modelos 3D (Aion Model Library)** turns Blender into an authoritative editing environment for Aion 3D assets, operating seamlessly on the complete cycle:

$$\mathbf{CLIENT} \longrightarrow \mathbf{INDEX} \longrightarrow \mathbf{VIEW} \longrightarrow \mathbf{EDIT} \longrightarrow \mathbf{SAVE} \longrightarrow \mathbf{CLIENT}$$

Whether modifying official characters, monsters, weapons, wings, and armor, or creating brand-new assets from scratch, the addon provides instant visual inspection, skeletal animation playback, and non-destructive transactional saving back into live client files or safe export packages.

---

## 🚀 Key Features

### 1. 🔍 High-Performance Asset Indexer & Search
- **Recursive Fast Scanner**: Discovers all models (`.cgf`, `.cga`), skeletons, animation lists (`.cal`), and keyframe sequences (`.caf`) across loose directories and encrypted/compressed `.pak` archives without loading full meshes into memory.
- **Categorization Engine**: Classifies assets into 12 authoritative categories: `NPC`, `MONSTER`, `CHARACTER`, `WEAPON`, `ARMOR`, `WINGS`, `PET_MOUNT`, `BUILDING`, `PROP`, `VEGETATION`, `OBJECT`, and `EFFECT`.
- **Sub-Millisecond Search**: Multi-predicate query matching by name, template ID, file path, bone count, or animation tag.
- **Automated Thumbnail Generator**: Renders and caches high-definition PNG icons with studio lighting in `.aion_model_thumbs/`.
- **Persistent Disk Caching**: Saves index metadata to `.aion_model_index.json` for instantaneous startup.

### 2. 🎮 Universal Multi-Client Support
Auto-detects and seamlessly parses all Aion client generations:
- **GameForge Classic (EU)**: BXML templates, XOR-32 obfuscated PAK archives.
- **Aion Live Clássico (América do Sul)**: UTF-8/16 XML, custom NPC tables (`Npcs_LostAcademy.pak`), Standard Zip PAKs.
- **Aion 3.9 Legacy (This Aion Brasil)**: UTF-16LE XML with BOM, legacy CryEngine structures.
- **Aion Classic 5.0 Emulator**: Hybrid loose and archive structures.

### 3. 🎬 Dedicated 3D Viewer & Animation Transport
- **Isolated Staging Collection**: Automatically creates and manages the `Aion_Model_Viewer` scene collection.
- **3-Point Studio Lighting**: Calibrated Key, Fill, and Rim sun lighting for optimal Material Preview.
- **Viewport Presets & Controls**: One-click Front, Side, Top, Perspective/Orthographic toggle, and Auto-Framing.
- **CAL Animation Sequencer**: Lists all animation sequences bound to the model's `.cal` definition.
- **Live Timeline Transport**: Play, pause, stop, step forward/backward, and adjust frame ranges directly from the N-Panel.

### 4. 🛠️ Comprehensive Asset Editors
- **Mesh & Geometry Editor**: Edit Mode, Sculpt Mode, and outward normals recalculation.
- **UV Coordinate Editor**: Angle-based unwrapping and margin-controlled island packing.
- **Skeleton & Armature Editor**: Add bones, reparent, rename, and automatically synchronize vertex groups on skinned meshes.
- **Material & Texture Editor**: Principled BSDF roughness, emission, backface culling, and texture slot reassignments.
- **Model Creator**: Convert arbitrary Blender meshes into authoritative CryEngine `.cgf` models with UVs, materials, and skin weights.
- **Model Cloner**: Duplicate existing client assets into independent new entries with custom IDs and paths.

### 5. 🛡️ Transactional Safe Save Pipeline (Zero Client Corruption)
- **Safety Switch (`allow_client_write`)**: Read-only safety guard enabled by default. Modifications are routed safely to the `Safe Export Directory`.
- **Pre-Write Validation**: Verifies binary headers, vertex counts, and chunk tables before disk write.
- **Atomic Staging**: Prepares all updates in a temporary staging directory before swapping files.
- **Automatic Backups**: Generates `.bak` (loose files) and `.pak.bak` (PAK archives) before applying any changes.
- **In-Place PAK Updates**: Deflate/Stored compression with XOR-32 encryption preservation.
- **One-Click Rollback**: Restore previous file versions from `.bak` directly from the interface.

---

## 📦 Installation

1. Clone or download the repository into Blender's addons directory:
   ```
   D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Blender - Aion Plugins\importador-modelos3d-lostacademy
   ```
2. Open Blender (4.0, 4.1, 4.2, 5.0, 5.2+ LTS).
3. Go to **Edit > Preferences > Add-ons**.
4. In the search bar, type `Lost Academy` or `Aion Model Library`.
5. Enable the checkbox next to **Import-Export: Lost Academy - Importador de Modelos 3D (Aion Model Library)**.
6. The addon panel will appear in the 3D Viewport Sidebar (`N-Panel`) under the **Aion Models** tab.

---

## 🕹️ User Guide: Step-by-Step Workflow

### Step 1: Client Detection & Asset Scanning
1. Open the **Aion Models** tab on the 3D Viewport sidebar (`N`).
2. Under **Aion Client Setup**, click **Detect Client** to auto-detect your game installation, or browse to your client root folder.
3. Click **Scan Client Assets**. The scanner will index models, animations, and textures.

### Step 2: Browsing & Staging Models
1. Select a category from the dropdown (e.g. `NPC`, `MONSTER`, `WEAPON`).
2. Type a search query in the search bar (e.g. `shugo`, `brax`, `sword`).
3. Select an item in the list and click **Load in Viewer**.
4. The model will appear centered with 3-point studio lighting, textured materials, and skeletal armature.

### Step 3: Playing Animations
1. Expand the **Animations** sub-panel.
2. Select an animation from the CAL sequence list (e.g. `idle`, `walk`, `run`, `attack`).
3. Click **Apply Animation**.
4. Use the **Play / Pause** and **Stop** buttons to preview movement in real-time.

### Step 4: Editing Geometry or Bones
- **Edit Mesh**: Click **Edit Mesh** or press `Tab` to tweak vertices, edges, or faces.
- **Sculpting**: Click **Sculpt** for organic modeling and surface detailing.
- **Rigging**: Click **Edit Rig** to reposition bones, or **Add Bone** to create new attachment points.
- **Normals & UVs**: Click **Recalculate Normals** or **Unwrap UV** to adjust texturing coordinates.

### Step 5: Saving & Exporting
1. **Safe Export (Default)**:
   - Keep `Allow Client Write` disabled.
   - Click **SAVE TO SAFE EXPORT FOLDER**.
   - Your modified `.cgf`, `.dds`, and `.caf` files are saved into the export directory ready for mod packaging.
2. **Direct Client Save**:
   - Check **Allow Client Write** (confirm caution dialog).
   - Click **SAVE DIRECTLY TO CLIENT**.
   - The addon creates `.bak` backups and commits the changes atomically to your official client files/PAKs.
3. **Rollback**: If you ever want to revert your edits, click **Rollback .bak** and select the backup file.

---

## 🧪 Automated Verification Suite

The repository includes a 15-test automated verification test suite executed headless via Blender Python:

```powershell
& "E:\Programas instalados - Leves\Blender\blender.exe" -b --python "validation\run_model_tests.py"
```

### Test Coverage Matrix:
1. `test_01_addon_lifecycle`: Addon registration, operators, properties, and UI panels.
2. `test_02_multiclient_discovery`: Multi-client discovery across GameForge, Live SA, and Legacy 3.9.
3. `test_03_scanner_and_catalog`: Category classification and recursive PAK scanning.
4. `test_04_asset_database_and_caching`: Full-text search and JSON disk cache serialization.
5. `test_05_thumbnail_generator`: Studio thumbnail rendering and PNG caching.
6. `test_06_model_loader_and_staging`: Armature, mesh, UVs, Principled BSDF, skin weights, and Action binding.
7. `test_07_viewport_and_camera_presets`: 3-point lighting setup, framing, and shading presets.
8. `test_08_animation_switching_and_transport`: Animation switching and timeline transport controls.
9. `test_09_mesh_editor_and_normals`: Vertex editing, geometry stats, and normals recalculation.
10. `test_10_skeleton_editor_add_bone`: Bone hierarchy addition, parenting, and bone count verification.
11. `test_11_material_editor`: Roughness, emission, and backface culling adjustments.
12. `test_12_transactional_save_safe_mode`: Read-only safe export routing without modifying client.
13. `test_13_transactional_save_live_client`: Live write with atomic staging and automatic `.bak` creation.
14. `test_14_rollback`: Byte-for-byte original file restoration from backup.
15. `test_15_model_creator_and_cloner`: Creating CGFs from arbitrary meshes and cloning existing assets.

---

## 🏛️ Architecture & File Structure

```
importador-modelos3d-lostacademy/
├── __init__.py                # Addon registration & bl_info
├── config/
│   ├── settings.py            # Client paths, categories, cache filenames, safety defaults
│   └── __init__.py
├── core/
│   ├── pak_engine.py          # XOR-32 encryption, Zip/Pak extraction & atomic in-place updates
│   ├── client_detector.py     # Multi-client detection & version classification
│   ├── client_provider.py     # Version-independent resource provider & PAK indexer
│   ├── change_tracker.py      # Dirty tracking, SHA-256 baseline hashing & commit audit
│   ├── transaction_manager.py # Atomic staging, validation, .bak backups & rollback
│   └── __init__.py
├── formats/
│   ├── cgf/
│   │   ├── parser.py          # CryEngine CGF chunk table parser (0x744 / 0x745)
│   │   ├── writer.py          # Scratch CGF writer & non-destructive CGF patcher
│   │   ├── cal_parser.py      # CAL animation sequence list reader
│   │   ├── cal_writer.py      # CAL text list writer
│   │   ├── caf_parser.py      # Binary CAF keyframe parser
│   │   ├── caf_writer.py      # Binary CAF keyframe serializer (0xCCCC000D)
│   │   ├── skeleton.py        # Bone hierarchy & CryBoneVertex structures
│   │   └── skeleton_writer.py # Serializer for BoneNameList, BoneInitialPos, BoneAnim
│   └── dds/
│       └── header.py          # 128-byte DDS header inspector (DXT1/3/5, dimensions, mipmaps)
├── indexer/
│   ├── asset_entry.py         # Lightweight asset dataclass
│   ├── dependency_graph.py    # Bidirectional dependency tracker (Model -> Skel -> CAL -> Mats)
│   ├── scanner.py             # High-performance recursive client scanner
│   ├── asset_database.py      # In-memory database with O(1) queries & disk cache
│   └── thumbnail_generator.py # Automated PNG thumbnail generator
├── providers/
│   ├── base_provider.py       # Abstract provider interfaces
│   ├── texture_provider.py    # DDS texture extraction & VRAM deduplication
│   ├── material_provider.py   # Principled BSDF node trees & CryEngine Mtl conversion
│   ├── skeleton_provider.py   # Armature builder (cm -> m) & extractor
│   ├── animation_provider.py  # CAF Action keyframing & Action-to-CAF serializer
│   ├── model_provider.py      # Unified model loader & CGF serializer
│   ├── npc_provider.py        # Archetype template matching
│   └── export_provider.py     # Connects model serialization to TransactionManager
├── viewers/
│   ├── viewer_stage.py        # Aion_Model_Viewer collection & 3-point studio lighting
│   ├── viewport_controls.py   # Front, Side, Top, Ortho/Persp, Focus, Reset
│   ├── display_modes.py       # Wireframe, Solid, Material, Rendered, and bone display
│   └── animation_player.py    # Timeline transport (play, pause, stop, step)
├── editors/
│   ├── mesh_editor.py         # Edit Mode, Sculpt Mode, normals recalculation
│   ├── uv_editor.py           # Unwrapping & island packing
│   ├── skeleton_editor.py     # Add, rename, reparent bones with vertex group sync
│   ├── animation_editor.py    # Action duplication & timeline scaling
│   ├── material_editor.py     # BSDF tweaks & texture slot assignment
│   ├── model_creator.py       # Converts arbitrary Blender meshes to CGF
│   └── model_cloner.py        # Clones existing client assets
├── exporters/
│   ├── direct_saver.py        # Coordinates transactional saves back to client/export
│   └── loose_exporter.py      # Loose directory asset export
├── properties/
│   └── library_properties.py  # Blender Scene & UI collection property definitions
├── operators/
│   ├── library_ops.py         # Detect, scan, filter, load asset, clear stage
│   ├── viewer_ops.py          # Camera presets, shading toggles, bone visibility
│   ├── animation_ops.py       # Play/pause, stop, switch CAL animation
│   ├── editing_ops.py         # Mesh/Rig edit modes, add bone, recalculate normals
│   ├── save_ops.py            # Save asset, export loose, rollback
│   └── creation_ops.py        # Create from mesh, clone asset
├── ui/
│   ├── panels.py              # 3D Viewport sidebar N-Panel layout
│   └── menus.py               # File > Import/Export topbar menu items
└── validation/
    ├── run_model_tests.py     # 15-test automated verification suite
    ├── test_indexer.py        # Standalone indexer test
    └── test_roundtrip.py      # Binary round-trip verification (CAL, CAF, CGF)
```

---

## 📄 License & Credits

- Developed for the **LostAcademy** project.
- Compatible with all official and private Aion CryEngine 1.x / 2.x client files.
