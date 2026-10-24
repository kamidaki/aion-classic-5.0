# Aion Classic 5.0 — Código Fonte Reconstruído (Game.dll x64)

> [!CAUTION]
> ### DIRETRIZ MANDATÓRIA: ESTA DLL NÃO ESTÁ COMPLETA E NUNCA DEVE SER USADA NO CLIENTE
> 1. **STATUS ATUAL**: O código-fonte presente neste repositório é fruto de engenharia reversa avançada com **Ghidra** e **REA MCP**. Embora o catálogo de 1.977 classes RTTI, 1.833 VTables e as assinaturas de exportação tenham sido mapeados, **a `Game.dll` NÃO está completa** em suas rotinas internas e lógica operacional.
> 2. **PROIBIÇÃO ABSOLUTA DE DEPLOY/USO**: Esta DLL **NUNCA DEVE SER USADA** ou colocada no cliente operacional de jogo (`bin64\Game.dll`) **até que esteja comprovadamente 100% IDÊNTICA à original** (em todo o conteúdo de seus ~31.8 MB).
> 3. **CLIENTE OPERACIONAL**: O cliente oficial de jogo (`D:\GameForge\aionclassic`) deve utilizar **estritamente a `Game.dll` original** fornecida pela distribuidora (NCSoft / Gameforge).
> 4. O comando `Build64.bat deploy` **NÃO DEVE** ser executado no ambiente de jogo real, sob pena de corromper a execução do cliente `Aion.bin`.

---

## 1. Visão Geral da Arquitetura & Fonte da Verdade

- **Binário Canônico Original (Única Fonte da Verdade)**: `D:\GameForge\aionclassic\bin64\Game.dll`
- **Tamanho Oficial do Binário**: `31.805.208 bytes` (~30.3 MB)
- **Timestamp do Cabeçalho PE**: `2026-09-16 11:50:39 UTC` (Epoch: 1789559439)
- **Arquitetura**: AMD64 (x64 nativo de 64 bits)
- **Total de Classes RTTI Canônicas**: `1.977 classes` (catalogadas via Ghidra/REA em `rtti_classes.txt`)
- **Total de VTables Mapeadas**: `1.833 VTables` (com até 252 métodos virtuais por diálogo)
- **Funções Registradas em .pdata**: `47.623 funções` de máquina nativas
- **Padrão C++**: C++17 Nativo (`/std:c++17 /GR /EHsc /MD /O2`)
- **Exportações Canônicas PE**:
  1. `CreateGameInstance` (Ordinal 1, RVA `0x00757E30`) - Ponto de entrada chamado por `CrySystem.dll` / `Aion.bin` para instanciar a interface `IGame`.
  2. `CryModuleGetMemoryInfo` (Ordinal 2, RVA `0x0085BC60`) - Relatório de alocação de memória do subsistema CryEngine.
- **Status da Pesquisa**: Mapeamento estrutural de classes e interfaces concluído; implementação de rotinas de baixo nível em andamento. **Não homologada para execução real**.

---

## 2. Princípio Fundamental: Paridade Rigorosa & Zero Mock Data

O projeto de pesquisa sobre a `Game.dll` do Aion Classic 5.0 tem como diretriz técnica a fidelidade total aos sistemas canônicos:
1. **Rede (GameServer & LoginServer)**: Conexões de sockets TCP diretas com o GameServer (`Porta 7777`) e LoginServer (`Porta 2106`). Pacotes reais como `0x0000 S_VERSION_CHECK`, `0x0001 S_STATUS`, `0x000E S_PUT_NPC`, `0x001A S_LOAD_INVENTORY`, `0x0021 S_USE_SKILL`, `0x0036 S_ATTACK`, `0x0037 S_MOVE_NEW`, etc., com criptografia de fluxo (Blowfish/XOR).
2. **Arquivos Locais do Cliente**: Leitura direta das tabelas compiladas em `Data/` (`.pak`), arquivos de malha e mapas de navegação 3D em `Data/Strings/` e `Data/Mesh/` (`.path` sectors).

> **Aviso de Integridade**: Qualquer tentativa de rodar uma `Game.dll` experimental sem 100% de paridade com o binário original de 31.8 MB causará falhas de alocação de memória na CryEngine, crashes no CryMemoryManager e desconexões de protocolo.

---

## 3. Metodologia de Engenharia Reversa (Ghidra & REA MCP)

A estrutura deste código-fonte foi obtida através de um pipeline sistemático de análise estática e dinâmica:

### Ferramentas Utilizadas:
1. **REA MCP + Ghidra 12.1.4 (NSA Research Suite)**: Descompilação estática x64, análise de chamadas de funções, recuperação de 1.833 vtables e fluxo de controle de despacho.
2. **MSVC Dumpbin & PE Parser**: Mapeamento do cabeçalho PE, tabela de seções (`IMAGE_SECTION_HEADER`), tabela de exportações (`IMAGE_EXPORT_DIRECTORY`) e dependências dinâmicas.
3. **RTTI Type Descriptor Extractor**: Extração direta de todos os 1.977 símbolos polimórficos de C++ (`.?AV...@@` e `.?AU...@@`) presentes na seção `.rdata` do binário original.
4. **Capturas de Tráfego de Rede (PCAP/Wire Opcodes)**: Análise dos pacotes reais do Classic 5.0 catalogados em `Ferramentas e Documentos\Wireshark - Oficial Classic 5.0\`.

---

## 4. Estrutura de Diretórios do Código Fonte

```text
Código Fonte - Game.dll/
|-- core/                  # GameGlobals, GameLog, Game (IGame), DllMain
|-- exports/               # Exportações PE: CreateGameInstance, CryModuleGetMemoryInfo
|-- framework/             # Interfaces CryEngine: ISystem, IGame, ILog, IConsole, IRenderer, etc.
|-- net/                   # Protocolo oficial, routers (ClientToServerRouter, etc.)
|-- ai/                    # Máquinas de estado canônicas, AIObject, AIToyPet, bandos de criaturas
|-- tables/                # 453 tabelas oficiais de dados do Classic 5.0 e motor TableLib
|-- path/                  # Navegação 3D, CPathFileReader, setores simples e complexos
|-- game/                  # Player, Items, Quests, Combat, Skills, Inventory, BattlePass
|-- ui/                    # 538 diálogos Dlg*, widgets Addon* e subsistema CEF
|-- resources/             # Informações de versão Win32 e recursos (.rc)
|-- Build64.bat            # Script de compilação para ambiente de laboratório MSVC 2022 x64
|-- Game.def               # Definição canônica de exportações PE
|-- ROADMAP.md             # Roadmap de Reconstrução Integral
|-- rtti_classes.txt       # Lista completa das 1.977 classes canônicas extraídas do binário
|-- CONTEXT.md             # Guia técnico e arquitetural aprofundado
\-- README.md              # Este documento
```

---

## 5. Compilação (Apenas para Fins de Laboratório e Pesquisa)

> [!WARNING]
> **A compilação local gera uma DLL experimental incompleta. Não a utilize para jogar ou no cliente principal.**

### Pré-requisitos:
- **Compilador**: Microsoft Visual Studio 2022 (MSVC v143 x64).

### Comando de Compilação:
Abra o prompt de comando ou PowerShell na pasta do código-fonte e execute:

```bat
Build64.bat
```

O script irá compilar os módulos em modo laboratório para a pasta local `Release64\`.
