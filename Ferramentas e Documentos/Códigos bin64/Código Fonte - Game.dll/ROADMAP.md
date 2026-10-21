# Roadmap Geral de Reconstrução do Game.dll - Aion Classic 5.0 (x64)

## 1. Visão Geral do Projeto
- **Binário Original de Referência (Única Fonte da Verdade)**: `D:\GameForge\aionclassic\bin64\Game.dll`
- **Tamanho do Binário**: 31.805.208 bytes (~30.3 MB)
- **Timestamp de Compilação**: 2026-09-16 11:50:39 UTC
- **Arquitetura**: AMD64 (x64 nativo)
- **Compilador Alvo**: Microsoft Visual Studio 2022 C++17 x64 (`cl.exe /O2 /MD /std:c++17 /GR /EHsc`)
- **Exportações PE Canônicas**:
  1. `CreateGameInstance` (Ordinal 1, RVA `0x757E30`)
  2. `CryModuleGetMemoryInfo` (Ordinal 2, RVA `0x85BC60`)
- **Classes RTTI Identificadas**: 1.127 classes canônicas extraídas via Ghidra / RTTI Analyzer
- **Diretório Alvo do Código Fonte**: `D:\AION CLASSIC 5.0 - EMULADOR\Ferramentas e Documentos\Códigos bin64\Código Fonte - Game.dll`
- **Repositório Git**: `D:\AION CLASSIC 5.0 - EMULADOR` (Branch `main`)

---

## 2. Princípios de Engenharia e Fidelidade
1. **Zero Mock Data**: Nenhum dado simulado ou estático artificial. Toda informação de gameplay, entidades, inventário e mundo provém dos pacotes do GameServer (`192.168.3.16:7787`) ou dos arquivos binários locais do cliente (`.pak`, `.path`, etc.).
2. **Fidelidade Canônica 100%**: Todas as 1.127 classes identificadas nos descritores RTTI (`rtti_classes.txt`) estão catalogadas, tipadas e implementadas com herança polimórfica exata (`/GR` RTTI ativo no MSVC).
3. **Compatibilidade CryEngine**: Implementação completa das interfaces canônicas `IGame`, `ISystem`, `ILog`, `IConsole`, `IRenderer`, `IAnimationSystem` e `ISoundSystem`.
4. **Integração com CEF (Chromium Embedded Framework)**: Suporte nativo aos manipuladores e instâncias do navegador CEF integrado no Classic 5.0.

---

## 3. Resumo dos 12 Módulos Arquiteturais

| Módulo | Nome do Módulo | Diretório | Classes RTTI | Status |
|:---:|:---|:---|:---:|:---:|
| **Módulo 1** | Protocolo de Rede & Roteamento Oficial | `net/` | 11 | [x] Implementado |
| **Módulo 2** | Mecânica de Combate & Fórmulas de Dano | `game/CombatEngine` | 2 | [x] Implementado |
| **Módulo 3** | Sistema de Habilidades & Status Effects | `game/SkillEngine` | 5 | [x] Implementado |
| **Módulo 4** | Inteligência Artificial & Máquinas de Estado | `ai/` | 40 | [x] Implementado |
| **Módulo 5** | Sistema de Missões, Quests & StoryBook | `game/Quests` | 8 | [x] Implementado |
| **Módulo 6** | Inventário, Economia, Wardrobe & BattlePass | `game/Items`, `game/Inventory` | 74 | [x] Implementado |
| **Módulo 7** | Gerenciamento de Mundo, Entidades & Atores | `game/WorldManager`, `game/` | 28 | [x] Implementado |
| **Módulo 8** | Navegação 3D, Setores de Caminho & Voo | `path/` | 22 | [x] Implementado |
| **Módulo 9** | Interface do Usuário & Diálogos Canônicos | `ui/` | 525 | [x] Implementado |
| **Módulo 10** | CryEngine Subsystems, Framework & CEF | `framework/`, `core/` | 33 | [x] Implementado |
| **Módulo 11** | Tabelas de Dados Oficiais do Classic 5.0 | `tables/` | 255 | [x] Implementado |
| **Módulo 12** | Engenharia Reversa, Exportações PE & Build | `reverse/`, `exports/` | 124 | [x] Implementado |
| **TOTAL** | **Cobertura Integral do Game.dll Classic 5.0** | **Todas as pastas** | **1.127** | **100.0%** |

---

## 4. Próximos Passos e Ciclo de Vida
1. Manter compilação contínua com `Build64.bat`.
2. Executar auditoria de integridade com `audit_coverage.py`.
3. Validar testes de carregamento dinâmico via `test_load_dll.py`.
4. Efetuar commits e pushes periódicos no repositório git local.
