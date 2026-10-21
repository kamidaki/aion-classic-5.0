# Contexto Técnico e Arquitetural - Aion Classic 5.0 (Game.dll x64)

## 1. Introdução e Contexto Operacional

O binário `Game.dll` é o componente mais volumoso e crítico da arquitetura do cliente Aion Classic 5.0, compreendendo mais de 31,8 MB de lógica executável de 64 bits compilada nativamente. Ele atua como o **módulo mestre de gameplay** do CryEngine customizado da NCSoft, conectando o núcleo do motor gráfico (`CrySystem.dll`, `Cry3DEngine.dll`, `CryAnimation.dll`, `XRenderD3D9.dll`), o subsistema de rede TCP/IP, o sistema de arquivos comprimidos (`.pak`), o banco de dados em memória e a interface gráfica do usuário.

---

## 2. A Fonte da Verdade: Binário Original vs. Emulador

| Atributo | Binário Original (`D:\GameForge\aionclassic\bin64\Game.dll`) | Emulador Java (`D:\AION CLASSIC 5.0 - EMULADOR\Código Fonte - Emulador`) |
|:---|:---|:---|
| **Status** | 100% Canônico / Oficial | ~80% Completo (Em desenvolvimento) |
| **Arquitetura** | x64 C++ Nativo | Java 21 / Netty / Spring |
| **Opcodes** | 345 Opcodes Server / 212 Client | Opcodes parcialmente implementados |
| **Prioridade de Decisão** | **Prioridade Máxima (Fonte da Verdade)** | Referência de apoio para fluxos de dados |

### Diretriz Estrita de Desenvolvimento:
Se houver qualquer divergência estrutural, semântica ou de layout entre uma classe do emulador Java e o binário oficial x64, a implementação do `Game.dll` **deve seguir rigorosamente o binário oficial x64**.

---

## 3. Metodologia de Reconstrução & Ferramental

### 3.1. Extração de Símbolos RTTI & VTables
O binário de produção do Aion Classic foi compilado com a opção de Run-Time Type Information (`/GR`) ativa, necessária para os operadores `dynamic_cast` e `typeid` utilizados internamente pelo subsistema de diálogos e árvores de IA.

Utilizando o analisador de RTTI sobre as seções `.rdata` e executáveis, foram extraídos os 1.977 descritores canônicos (`.?AV...@@` e `.?AU...@@`) e 1.833 VTables completas, revelando:
- A hierarquia completa de classes base e derivadas com 1.833 tabelas virtuais.
- Todas as 538 classes de interface com usuário (`Dlg*`, `Addon*`, `Cef*`).
- Todas as 453 tabelas de dados binárias e motor de templates `TableLib` (`*Table*`, `TableIndex`, `Array`, `Node`).
- As 43 classes de inteligência artificial canônicas (`AIObject`, `AIToyPet`, `AiCharState*`, bandos de criaturas).
- Os setores de navegação 3D (`CPathFileReader`, `SimplePathSector`, `ComplexPathSector`).

### 3.2. Análise de Descompilação com Ghidra 12.1.4 & REA MCP
A auditoria e descompilação combinada permitiu identificar:
1. **O Ponto de Criação da Instância (`CreateGameInstance`)**:
   - RVA canônica: `0x00757E30`.
   - Assinatura: `extern "C" __declspec(dllexport) IGame* CreateGameInstance();`
   - Função: Aloca e retorna a interface canônica `IGame` e registra os ponteiros de subsistemas (`ISystem`, `ILog`, `IConsole`, `IRenderer`, `IEntitySystem`).
2. **O Inspetor de Memória (`CryModuleGetMemoryInfo`)**:
   - RVA canônica: `0x0085BC60`.
   - Assinatura: `extern "C" __declspec(dllexport) void CryModuleGetMemoryInfo(CryModuleMemoryInfo* pMemInfo);`
   - Função: Retorna o consumo acumulado de memória de heap e buffers do módulo para o CryEngine.

---

## 4. O Subsistema de Rede Sem Mock Data (Zero Mock Data)

O `Game.dll` opera sem nenhum dado simulado (mock data). Toda informação exibida em tela é originada de pacotes de rede ou arquivos de dados locais:

### 4.1. Fluxo de Vida do Pacote de Rede
```
[ GameServer (192.168.3.16:7787) ]
               │  TCP Socket Stream
               ▼
   [ AionCryptEngine ] (Decriptografia XOR/Blowfish dinâmica)
               │  Buffer Limpo descompactado
               ▼
   [ ClientToServerRouter / BaseReceiveRouter ] (Despacho por Opcode)
               │
   ┌───────────┼───────────┬───────────┬───────────┐
   ▼           ▼           ▼           ▼           ▼
S_VERSION   S_STATUS    S_PUT_NPC   S_INVENTORY  S_USE_SKILL
 (0x0000)    (0x0001)    (0x000E)    (0x001A)    (0x0021)
   │           │           │           │           │
   ▼           ▼           ▼           ▼           ▼
[Handshake] [Player]   [WorldMgr]  [InvManager] [SkillEngine]
```

---

## 5. Novidades Arquiteturais do Classic 5.0

Em relação às versões anteriores (como 4.8), o Classic 5.0 introduziu sistemas canônicos que aumentaram o binário de 26 MB para 31,8 MB:

1. **CEF (Chromium Embedded Framework)**:
   - Classes `AionCefApp`, `CEFClientHandler`, `CefBaseRefCounted`, `CefClient`, `CefDisplayHandler`, etc.
   - Permite a renderização de páginas web modernas integradas dentro do jogo (como lojas de moedas, guias interativos e rankings).
2. **Sistema de Wardrobe / AionLook**:
   - Classes `AionLookShop_ApparelPage`, `AionLookShop_CardPage`, `AionLookDyeColorTable`.
   - Guarda-roupa visual desvinculado dos atributos de armadura de combate.
3. **Passe de Batalha (BattlePass)**:
   - Classes `nsDlgBattlePass`, `BattlePassGridItemData`, `BattlePassPathMap`, `BattlePassRewardMap`.
   - Trilha de recompensas periódicas e missões sazonais.
4. **Encantamento Acumulado (Accumulated Enchantment)**:
   - Classes `AccumulatedEnchantManager`, `AccumulatedEnchantTable`.
   - Sistema de progressão acumulativa de probabilidade de encantamento de itens míticos.

---

## 6. Procedimento de Teste e Validação

1. **Compilação**: Executar `Build64.bat` e verificar código de saída `0` com zero erros.
2. **Auditoria de Cobertura**: Executar `python audit_coverage.py` garantindo que as 1.127 classes de `rtti_classes.txt` possuem representação de tipo canônica.
3. **Teste de Carregamento Dinâmico**: Executar script Python com `ctypes.WinDLL` chamando `CreateGameInstance` e validando o ponteiro da interface `IGame`.
4. **Integração com Servidor**: Iniciar o cliente apontando para o servidor e inspecionar a troca de pacotes de autenticação e seleção de personagens.
