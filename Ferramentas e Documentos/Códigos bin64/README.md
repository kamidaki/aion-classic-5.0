# Códigos-Fonte dos Módulos Nativos bin64 (CryEngine / Crytek & Injetores) — Aion Classic 5.0

Este diretório reúne o código-fonte C/C++ dos módulos nativos de 64 bits (`bin64`) do cliente oficial **Aion Classic 5.0 (Gameforge / NCSoft)**, englobando tanto a reconstrução da suíte CryEngine (Crytek) obtida via engenharia reversa quanto a DLL de conexão e compatibilidade com o emulador.

---

## 1. Visão Geral dos Módulos Presentes

A pasta é composta por três categorias distintas de projetos:

| Módulo / Diretório | Tecnologia / Origem | Finalidade / Papel Arquitetural | Status de Prontidão e Uso |
| :--- | :--- | :--- | :--- |
| **`Código Fonte - Version.dll`** | C++17 (MSVC v143) / Nativo | **Ponte de conexão Client-Emulador**. Bypass de validações oficiais, hooks WinSock, No-IP, suporte dinâmico a múltiplos GameServers e injeção de customs. | **HOMOLOGADA & ATIVA EM PRODUÇÃO** |
| **`Código Fonte - Game.dll`** | C++17 (MSVC v143) / REA + Ghidra | Lógica central do cliente de jogo (1.977 classes RTTI, ~31.8 MB no original). | **INCOMPLETA — NUNCA USAR NO JOGO** |
| **`Código Fonte - Crysystem.dll`** | C++ / REA + Ghidra | Sistema central da CryEngine (memória, console, logs, inicializador). | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - Cry3DEngine.dll`** | C++ / REA + Ghidra | Motor gráfico 3D, rendering de cenários, terreno e iluminação. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryAnimation.dll`** | C++ / REA + Ghidra | Subsistema de animação esqueletal e interpolação de modelos. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryEntitySystem.dll`** | C++ / REA + Ghidra | Gerenciamento de entidades dinâmicas do mundo de jogo. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryFont.dll`** | C++ / REA + Ghidra | Renderização de fontes TrueType e glifos multilíngues. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryInput.dll`** | C++ / REA + Ghidra | Captura de periféricos (teclado, mouse, DirectInput). | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryMovie.dll`** | C++ / REA + Ghidra | Subsistema de cutscenes e sequências cinematográficas in-game. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryPhysics.dll`** | C++ / REA + Ghidra | Motor de física rígida, colisões e gravidade. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CryScriptSystem.dll`**| C++ / REA + Ghidra | Integração com scripts Lua da CryEngine. | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - CrySoundSystem.dll`** | C++ / REA + Ghidra | Subsistema de áudio, efeitos sonoros e ambientação (FMOD). | **Pesquisa / Paridade estrita exigida** |
| **`Código Fonte - BrService.dll`** | C++ / Experimental | DLL experimental de serviço legada. | **DESATIVADA — NUNCA USAR OU CONSIDERAR** |

---

## 2. Metodologia de Reconstrução Crytek (REA MCP + Ghidra)

Os códigos-fonte dos módulos CryEngine e do `Game.dll` foram montados e catalogados através de engenharia reversa sistemática avançada sobre os binários oficiais do Aion Classic 5.0 x64, utilizando:
- **Ghidra 12.1.4 (NSA Research Suite)**: Descompilação de rotinas nativas x64, identificação de blocos lógicos e de controle.
- **REA MCP**: Análise estática, mapeamento de símbolos, correlação de grafos de chamada (*call graphs*) e análise semântica estrutural.
- **RTTI & VTable Extractors**: Mapeamento completo dos símbolos polimórficos de C++ (`.?AV...@@`) e tabelas de despacho virtual no `.rdata`.

---

## 3. Diretriz Mandatória: Regra Estrita para os Módulos Crytek

> [!CAUTION]
> ### REGRA CRÍTICA PARA AS DLLS DA CRYTEK / CRYENGINE:
> 1. Os códigos-fonte reconstruídos da Crytek servem para análise aprofundada, pesquisa arquitetural e busca progressiva por paridade técnica.
> 2. **O desenvolvedor ou agente de automação SÓ DEVE USAR qualquer DLL reconstruída da Crytek quando garantir que 100% de todo o seu conteúdo é IDÊNTICO ao original, sem nenhum problema ou divergência.**
> 3. Na execução prática do cliente oficial (`D:\GameForge\aionclassic`), **DEVEM SER MANTIDAS AS DLLs ORIGINAIS** (`bin64\CrySystem.dll`, `bin64\Cry3DEngine.dll`, etc.) até que haja certificação inequívoca de equivalência perfeita.

---

## 4. Diretriz Mandatória: Situação Crítica da `Game.dll`

> [!WARNING]
> ### A `Game.dll` NÃO ESTÁ COMPLETA E NUNCA DEVE SER USADA NO CLIENTE:
> - O binário canônico oficial `D:\GameForge\aionclassic\bin64\Game.dll` possui **31.805.208 bytes (~30.3 MB)** e contém mais de 47.600 funções compiladas nativas e 1.977 classes de gameplay, rede, IA e interface.
> - Embora o repositório em `Código Fonte - Game.dll` possua a catalogação RTTI e o esqueleto estrutural de interfaces mapeado, **a implementação interna das rotinas NÃO está completa**.
> - **REGRA INVIOLÁVEL**: O arquivo gerado pela compilação deste código **NUNCA DEVE SER USADO** para substituir a DLL do cliente em produção ou desenvolvimento de jogo **até que esteja 100% idêntica à original em todos os seus ~31 MB de conteúdo**.
> - O comando `Build64.bat deploy` **NÃO DEVE SER EXECUTADO** no cliente de jogo operacional, pois substituir a `Game.dll` original por uma versão incompleta quebrará imediatamente a inicialização e o funcionamento do jogo.

---

## 5. Papel Central da `Version.dll` (Conexão Client-Emulador & Customs)

A **`version.dll`** é a única biblioteca nativa de desenvolvimento próprio que atua ativamente no cliente oficial:

1. **Responsável pela Conexão com o Emulador e Múltiplos GameServers**:
   - Atua como uma proxy DLL de sistema (`version.dll`), sendo carregada nativamente pelo processo `Aion.bin` sem a necessidade de launchers invasivos.
   - Faz o **bypass completo dos sistemas oficiais**: neutraliza checagens de autenticação oficial da Gameforge/NCSoft, suprime o erro *"No game server is available to the authorization server (6)"* e redireciona a camada WinSock (`connect`, `inet_ntoa`, `lstrcpynA`, `gethostbyname`).
   - **Resolução Dinâmica Multi-GameServer**: Coleta via `zzinet_ntoa` os IPs dos GameServers entregues no pacote `SM_SERVER_LIST` e aplica o spoofing em `zzlstrcpynA` preservando o conjunto de servidores para suportar simultaneamente o GameForge (GSID 1), Remake (GSID 2) e BattleRoyale (GSID 3), sem sequestrar o handshake inicial de LoginServer no boot (`127.0.0.1:2106`).
2. **Regra Arquitetural de Alteração da `version.dll`**:
   - Toda alteração na `version.dll` deve ser arquitetada pensando sempre no funcionamento conjunto com cada GameServer isoladamente, garantindo que uma alteração não cause mau funcionamento em outros GameServers.
   - Se uma alteração na `version.dll` demandar ajustes nos GameServers, este é o único momento autorizado para alterá-los em lote, desde que a modificação afete estritamente **conectividade e comunicação de rede, NUNCA mecânicas ou gameplay**.
3. **Hub Oficial para Customizações ("Customs")**:
   - Suporte Gráfico Ultra-HD até 4096×4096 no `crysystem`.
   - Compatibilidade e mitigação de stack x64 para Windows 11 24H2+.
   - Injeção de idioma Português (`BRA`) e bypass regional de país.
   - Gameplay Fixes 5.0 (saldo Quna e diálogo de desmonte do Martelo de Siel).

---

## 6. Situação da `BrService.dll` (Desativada)

> [!CAUTION]
> A pasta `Código Fonte - BrService.dll` contém um módulo experimental que foi **completamente desativado, não é utilizado e nunca deve ser considerado**. Toda a comunicação do cliente com o emulador e o ecossistema é tratada via `version.dll` e pelos protocolos padrão de rede.
