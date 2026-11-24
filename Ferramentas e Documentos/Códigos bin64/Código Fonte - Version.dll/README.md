# Aion-Version-Dll — Módulo Standalone de Conexão com Emulador & Hub de Customs (x64 & x86)

DLL nativa (`version.dll`) desenvolvida como proxy DLL de sistema para o cliente **Aion Classic 5.0 (Gameforge / Oficial)**.

> [!IMPORTANT]
> ### PAPEL ARQUITETURAL FUNDAMENTAL:
> 1. **Responsável pela Conexão Client-Emulador e Multi-GameServer**: A `version.dll` é a responsável exclusiva por conectar o cliente oficial ao emulador. Ela faz o **bypass dos sistemas oficiais de validação e autenticação** (NCSoft / Gameforge) e direciona todas as conexões de rede do cliente para o emulador local/privado (`127.0.0.1:2106`, `127.0.0.1:7777`, `7778`, `7779`).
> 2. **Hub Homologado de Customizações ("Customs")**: A `version.dll` é o componente arquitetural correto, modular e seguro para implementação de funcionalidades personalizadas e ajustes no cliente sem alterar os binários originais da CryEngine.
> 3. **Independência Completa**: Opera de maneira 100% autônoma e independente, sem qualquer dependência de bibliotecas externas de serviço e sem necessidade de infraestrutura WebSocket.
> 4. **Isolamento e Compatibilidade Multi-GameServer**: Toda alteração na `version.dll` deve ser arquitetada pensando sempre no funcionamento em conjunto com cada GameServer isoladamente (`game-server-gameforge`, `game-server-remake`, `game-server-battleroyale`), garantindo que uma alteração não cause mau funcionamento em outros servidores.

---

## Recursos e Funcionalidades

### 1. Conexão No-IP Oficial & Bypass de Validação de Servidor
* Permite que o cliente oficial conecte-se a servidores locais (`127.0.0.1`) ou privados sem erros de autorização (`No game server is available to the authorization server (6)`).
* **Hooks de Rede (WinSock)**:
  * `zzinet_ntoa`: Registra os endereços IP candidatos recebidos na lista de servidores (`SM_SERVER_LIST`) no pool dinâmico thread-safe `s_candidateIps`.
  * `zzlstrcpynA`: Substitui dinamicamente o IP para `"70.5.0.18"` durante a validação interna do cliente no `game.dll`, mantendo a integridade do fluxo sem alterar arquivos `hosts`.
  * **Preservação de Múltiplos GameServers**: O pool de candidatos `s_candidateIps` não é esvaziado prematuramente dentro de `zzlstrcpynA`, permitindo que os 3 GameServers (GameForge, Remake e BattleRoyale) sejam validados simultaneamente.
  * **Proteção de Boot do LoginServer**: A verificação `IsCandidateGameServerIp` é condicionada à presença de candidatos já deserializados de `SM_SERVER_LIST` (`s_candidateIpCount > 0`), impedindo que o argumento de inicialização do cliente (`-ip:127.0.0.1`) seja sequestrado no boot, prevenindo o erro *"Não tem servidor de autenticação disponível"*.
  * `zzconnect`: Conecta diretamente ao IP e porta requisitados, interceptando portas 80/443 para redirecionamento ao webshop local (`127.0.0.1:8080`) e redefinindo o pool de candidatos ao conectar no mundo.
  * `zzgethostbyname`: Redireciona domínios oficiais (`plaync`, `ncsoft`, `gameforge`) para `127.0.0.1`.

### 2. Desbloqueio Gráfico em Alta Resolução (4096×4096)
* Remove as travas de resolução padrão do `crysystem` (1920×1200 e 2560×1600), liberando todas as opções gráficas (sombras, água, efeitos) em resoluções Ultrawide e 4K.
* `shader_fix`: Corrige flickering e artefatos de renderização com placas NVIDIA e AMD sob DirectX 9 / DXVK.

### 3. Estabilidade e Compatibilidade Windows 10/11 (x64)
* **Fix de Stack 64-bit e VEH**: Estabiliza a execução do binário de 64 bits (`Aion.bin`) sob proteção Themida no Windows 11 (24H2+) através de hooks em `CloseHandle`, `RtlAddVectoredExceptionHandler`, `CreateFileA` e `LoadLibraryA`.
* **Afinidade de CPUs de Alto Desempenho (32+ Threads)**: Limita de forma segura a máscara de afinidade em processadores com 32 ou mais núcleos lógicos, prevenindo travamentos conhecidos da CryEngine legada.

### 4. Injeção Dinâmica de Idioma (PT-BR) e Bypass de Região
* Varre dinamicamente a tabela de idiomas nos módulos carregados (`crysystem`, `cryfont`, `crymovie`, `game.dll`, etc.) e injeta o suporte ao idioma `BRA`.
* Suprime caixas de diálogo de bloqueio de país (`"unavailable in your country"`).
* Normaliza argumentos de linha de comando (`-lang:BRA`, `-cc:2`, `-classic`, `-probability`, etc.).

### 5. Correções de Gameplay no Cliente 5.0 (Customs Homologadas)
* **Quna Balance Fix (`quna_fix.h`)**: Intercepta pacotes de saldo de Quna recebidos do emulador e atualiza os ponteiros em memória do `game.dll` para exibição correta no inventário, armazém e Quna Market.
* **Siel Hammer Fix (`siel_hammer_fix.h`)**: Evita o travamento do diálogo de desmonte e cancelamento de progresso de quebra de itens (`DlgItemCrushResult`).

### 6. Modo Dual e Interoperabilidade WebPort (`-webPort`)
* **Detecção Automática de Modo**: O hook em `GetCommandLineA/W` detecta a presença da flag `-webPort` e expõe a função exportada `IsWebPortClient()` (ordinal 17).
* **Redirecionamento Gráfico Offscreen**: Intercepta `CreateWindowExA/W`, `ShowWindow` e `SetWindowPos` para forçar coordenadas `-32000, -32000` e estilo `SW_HIDE`, viabilizando captura headless sem janela na tela.
* **Preservação de Processo Hospedeiro Compartilhado**: Intercepta chamadas de saída limpa (`ExitProcess(0)` e `TerminateProcess(0)`) originadas por logout web ou timeout de rede, finalizando a thread chamadora (`ExitThread(0)`) sem derrubar o processo hospedeiro `Aion.bin`. Falhas anômalas (código != 0) são repassadas ao SO.
* **Encerramento Administrativo Seguro**: Exporta `RequestHostShutdown(UINT uExitCode)` (ordinal 18) para encerramento gracioso via chamadas RPC do orquestrador Node.js.
* **Preservação do Modo Windows Desktop**: Sem a flag `-webPort`, o cliente opera normalmente em modo janela/tela cheia com encerramento convencional.

---

## Validação Obrigatória com Evidências Oficiais (Ghidra & Wireshark)

> [!CAUTION]
> Toda alteração nesta DLL deve ser estritamente validada e comprovada:
> 1. **Ghidra**: Análise estática das rotinas do `Aion.bin` e `Game.dll` (PE32+ x64).
> 2. **Wireshark**: Análise das capturas de rede oficiais do Aion Classic Gameforge (`.pcap`).
> 3. **Imagens Comprobatórias**: Capturas de tela demonstrando o teste em execução real.
> 4. **Isolamento de Servidores**: Alterações que afetem GameServers são permitidas apenas para conectividade e comunicação de rede, nunca gameplay.

---

## Como Compilar

### Pré-requisitos:
* Visual Studio 2022 Community com as ferramentas de compilação C++ (v143).
* Pacote Microsoft Detours (restaurado automaticamente via NuGet).

### Comando Automatizado:
Execute o script `build.bat` na raiz do diretório do código-fonte:
```cmd
build.bat
```

Os binários compilados são gerados em:
* `src\x64\Release\version.dll` (64-bit)
* `src\Release\version.dll` (32-bit)

E sincronizados automaticamente para:
* `Ferramentas e Documentos\Patch final - Client 5.0\bin64\`
* `Ferramentas e Documentos\Patch final - Client 5.0\bin32\`
* Pasta do cliente Aion Classic (`%AION_CLIENT_DIR%\bin64` e `bin32`, quando definida).
