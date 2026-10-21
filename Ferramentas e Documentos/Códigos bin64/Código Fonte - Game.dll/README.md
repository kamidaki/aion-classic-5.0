# Aion Classic 5.0 - Código Fonte Oficial Reconstruído (Game.dll x64)

Este repositório contém a reconstrução integral, modular e canônica do código fonte em C++17 x64 da biblioteca central **`Game.dll`** do cliente **Aion Classic 5.0** (GameForge / NCSoft).

---

## 1. Visão Geral da Arquitetura & Fonte da Verdade

- **Binário Canônico Original (Única Fonte da Verdade)**: `D:\GameForge\aionclassic\bin64\Game.dll`
- **Tamanho Oficial do Binário**: `31.805.208 bytes` (~30.3 MB)
- **Timestamp do Cabeçalho PE**: `2026-09-16 11:50:39 UTC` (Epoch: 1789559439)
- **Arquitetura**: AMD64 (x64 nativo de 64 bits)
- **Total de Classes RTTI Canônicas**: `1.977 classes` (descritas integralmente em `rtti_classes.txt`)
- **Total de VTables Mapeadas**: `1.833 VTables` (com até 252 métodos virtuais por diálogo)
- **Funções Registradas em .pdata**: `47.623 funções` de máquina nativas
- **Padrão C++**: C++17 Nativo (`/std:c++17 /GR /EHsc /MD /O2`)
- **Exportações Canônicas PE**:
  1. `CreateGameInstance` (Ordinal 1, RVA `0x00757E30`) - Ponto de entrada chamado por `CrySystem.dll` / `Aion.bin` para instanciar a interface `IGame`.
  2. `CryModuleGetMemoryInfo` (Ordinal 2, RVA `0x0085BC60`) - Relatório de alocação de memória do subsistema CryEngine.

---

## 2. Princípio Fundamental: ZERO Mock Data & Zero Fake Classes

O `Game.dll` oficial do Aion Classic 5.0 **não utiliza dados estáticos ou falsificados (mock data)** nem classes fictícias inventadas. Toda a lógica de jogo é alimentada por duas fontes primárias reais:
1. **Rede (GameServer & LoginServer)**: Conexões de sockets TCP diretas com o GameServer (`192.168.3.16:7787`) e LoginServer (`192.168.3.16:2120`). Pacotes reais como `0x0000 S_VERSION_CHECK`, `0x0001 S_STATUS`, `0x000E S_PUT_NPC`, `0x001A S_LOAD_INVENTORY`, `0x0021 S_USE_SKILL`, `0x0036 S_ATTACK`, `0x0037 S_MOVE_NEW`, etc., com criptografia de fluxo (Blowfish/XOR).
2. **Arquivos Locais do Cliente**: Leitura direta das tabelas compiladas em `Data/` (`.pak`), arquivos de malha e mapas de navegação 3D em `Data/Strings/` e `Data/Mesh/` (`.path` sectors).

> **Atenção**: O emulador Java em `D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador` está aproximadamente 80% completo. Portanto, em caso de qualquer divergência em pacotes ou estruturas, a **única fonte da verdade absoluta** é o binário oficial `D:\GameForge\aionclassic\bin64\Game.dll`.

---

## 3. Como Foi Feita a Montagem (Metodologia de Engenharia Reversa)

A montagem e reconstrução do código fonte foi executada através de um pipeline sistemático de engenharia reversa com as seguintes ferramentas:

### Ferramentas Utilizadas:
1. **REA MCP + Ghidra 12.1.4 (NSA Research Suite)**: Descompilação estática x64, análise de chamadas de funções, recuperação de 1.833 vtables e fluxo de controle de despacho.
2. **MSVC Dumpbin & PE Parser**: Mapeamento do cabeçalho PE, tabela de seções (`IMAGE_SECTION_HEADER`), tabela de exportações (`IMAGE_EXPORT_DIRECTORY`) e dependências dinâmicas.
3. **RTTI Type Descriptor Extractor**: Extração direta de todos os 1.977 símbolos polimórficos de C++ (`.?AV...@@` e `.?AU...@@`) presentes na seção `.rdata` / código principal do binário original.
4. **Capturas de Tráfego de Rede (PCAP/Wire Opcodes)**: Análise dos pacotes reais do Classic 5.0 catalogados em `Ferramentas e Documentos\Opcodes Oficiais - Classic 5.0\`.

### Etapas da Reconstrução:
1. **Despejo e Catalogação RTTI**: 1.977 classes identificadas e salvas em `rtti_classes.txt`.
2. **Mapeamento Modular em 10 Fases**: Agrupamento lógico por subsistemas (`net`, `combat`, `skills`, `ai`, `quests`, `inventory`, `world`, `path`, `ui`, `framework`, `tables`, `exports`).
3. **Reconstrução das Interfaces CryEngine**: Criação das abstrações virtuais puras canônicas (`IGame`, `ISystem`, `ILog`, `IConsole`, `IRenderer`, `IEntitySystem`).
4. **Implementação dos 538 Diálogos e Widgets de UI**: Modelagem completa de todas as classes `Dlg*`, botões, containers, browsers e o subsistema **CEF (Chromium Embedded Framework)** para janelas web integradas (`AionCefApp`, `CEFClientHandler`).
5. **Implementação das 453 Tabelas de Dados TableLib**: Modelagem de carregamento das tabelas binárias do Classic 5.0 (incluindo `AccumulatedEnchantTable`, `MorosTable`, `ConfirmedEnchantTable`, `GuildGrowthTable`, `FlyPathTable`, etc.).
6. **Compilação e Linkedição Canônica**: Geração de `Game.dll` x64 nativo com arquivo de definição `Game.def` para paridade ordinal 1 e 2.

---

## 4. Estrutura de Diretórios do Código Fonte

```
Código Fonte - Game.dll/
├── core/                  # GameGlobals, GameLog, Game (IGame), DllMain
├── exports/               # Exportações PE: CreateGameInstance, CryModuleGetMemoryInfo
├── framework/             # Interfaces CryEngine: ISystem, IGame, ILog, IConsole, IRenderer, etc.
├── net/                   # Protocolo oficial, routers (ClientToServerRouter, etc.)
├── ai/                    # Máquinas de estado canônicas, AIObject, AIToyPet, bandos de criaturas
├── tables/                # 453 tabelas oficiais de dados do Classic 5.0 e motor TableLib
├── path/                  # Navegação 3D, CPathFileReader, setores simples e complexos
├── game/                  # Player, Items, Quests, Combat, Skills, Inventory, BattlePass
├── ui/                    # 538 diálogos Dlg*, widgets Addon* e subsistema CEF
├── resources/             # Informações de versão Win32 e recursos (.rc)
├── Build64.bat            # Script de compilação automatizado via MSVC 2022 x64
├── Game.def               # Definição canônica de exportações PE
├── ROADMAP.md             # Novo Roadmap Canônico de Reconstrução Integral
├── rtti_classes.txt       # Lista completa das 1.977 classes canônicas extraídas do binário
├── CONTEXT.md             # Guia técnico e arquitetural aprofundado
└── README.md              # Este documento
```

---

## 5. Como Compilar

### Pré-requisitos:
- **Sistema Operacional**: Windows 10/11 x64 ou Windows Server.
- **Compilador**: Microsoft Visual Studio 2022 (Community, Professional ou Enterprise) com o componente **"Desktop development with C++"** (MSVC v143 x64).
- O script localiza automaticamente o inicializador do ambiente:
  `C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat`

### Comando de Compilação:
Abra o prompt de comando ou PowerShell na pasta do código fonte e execute:

```bat
Build64.bat
```

O script irá:
1. Inicializar o ambiente MSVC x64 de 64 bits.
2. Compilar os recursos Win32 (`resources\Game.rc`) gerando `Release64\Game.res`.
3. Compilar todas as unidades modulares em C++17 com flags otimizadas (`/O2 /W3 /std:c++17 /EHsc /MD /LD /GR`).
4. Linkar a biblioteca com `Game.def`, produzindo `Release64\Game.dll`, `Release64\Game.lib` e `Release64\Game.pdb`.
5. Executar `dumpbin /exports` para validar a presença exata de `CreateGameInstance` (Ordinal 1) e `CryModuleGetMemoryInfo` (Ordinal 2).

---

## 6. Como Fazer Deploy e Testar

Para compilar e automaticamente aplicar a DLL no cliente do jogo com criação de backup de segurança:

```bat
Build64.bat deploy
```

O script fará o deploy diretamente para `D:\GameForge\aionclassic\bin64\Game.dll`, criando preventivamente uma cópia de segurança em `Game.dll.original.bak`.
