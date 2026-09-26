# Aion-Version-Dll — Módulo Standalone de Compatibilidade e Conexão (x64 & x86)

DLL nativa (`version.dll`) desenvolvida como proxy DLL de sistema para o cliente **Aion Classic 5.0 (Gameforge / Oficial)**. Opera de maneira 100% autônoma e independente, sem qualquer dependência de bibliotecas externas de serviço (como `BrService.dll`) e sem necessidade de infraestrutura WebSocket.

---

## Recursos e Funcionalidades

### 1. Conexão No-IP Oficial & Bypass de Validação de Servidor
* Permite que o cliente oficial conecte-se a servidores locais (`127.0.0.1`) ou privados sem erros de autorização (`No game server is available to the authorization server (6)`).
* **Hooks de Rede (WinSock)**:
  * `zzinet_ntoa`: Registra os endereços IP candidatos recebidos na lista de servidores (`SM_SERVER_LIST`).
  * `zzlstrcpynA`: Substitui dinamicamente o IP para `"70.5.0.18"` durante a validação interna do cliente no `game.dll`, mantendo a integridade do fluxo sem alterar arquivos `hosts`.
  * `zzconnect`: Conecta diretamente ao IP e porta requisitados, interceptando portas 80/443 para redirecionamento ao webshop local (`127.0.0.1:8080`).
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

### 5. Correções de Gameplay no Cliente 5.0
* **Quna Balance Fix (`quna_fix.h`)**: Intercepta pacotes de saldo de Quna recebidos do emulador e atualiza os ponteiros em memória do `game.dll` para exibição correta no inventário, armazém e Quna Market.
* **Siel Hammer Fix (`siel_hammer_fix.h`)**: Evita o travamento do diálogo de desmonte e cancelamento de progresso de quebra de itens (`DlgItemCrushResult`).

---

## Arquitetura e Independência Modular

* **100% Standalone**: Não carrega nem depende de `BrService.dll` ou de qualquer outro módulo externo complementar.
* **Zero WebSocket**: Não contém sockets WebSocket nem código de telemetria externa; utiliza apenas chamadas nativas WinSock para hooks de conexão de jogo.
* **Sem Exigência de Token**: Inicializa imediatamente sem travas artificiais de token de linha de comando.

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
* Pasta de desenvolvimento do cliente (`bin64` e `bin32`).