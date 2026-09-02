# Aion-Version-Dll — Módulo de Conexão, Otimização e Telemetria (x64 & x86)

DLL nativa (`version.dll`) desenvolvida para o cliente do **Aion Classic EU (Gameforge)**, fornecendo spoofing de conexão No-IP, suporte avançado a DXVK / Vulkan, correções de compatibilidade para Windows 10/11 e telemetria detalhada de rede.

---

## Recursos e Funcionalidades

### 1. Conexão No-IP Oficial & Bypass de Validação
* Permite que o cliente oficial conecte-se a servidores locais (`127.0.0.1`) ou privados sem erros de autorização (`No game server is available to the authorization server (6)`).
* **Mecanismo Limpo**:
  * `zzinet_ntoa`: Registra os endereços IP candidatos recebidos na lista de servidores (`SM_SERVER_LIST`).
  * `zzlstrcpynA`: Substitui dinamicamente o IP para `"70.5.0.18"` durante a validação interna do cliente no `game.dll`, mantendo a integridade do fluxo.
  * `zzconnect`: Conecta diretamente ao IP e porta requisitados sem forçar desvios ou modificar o tráfego de loopback.

### 2. Suporte a Vulkan & DXVK (Direct3D 9 Layer)
* **Carregamento Proativo (`PreloadDXVK`)**: Carrega automaticamente `d3d9.dll` (DXVK) ao iniciar o processo.
* **Detecção Automática da Versão do Vulkan**: Inspeciona `vulkan-1.dll`, consulta `vkEnumerateInstanceVersion` e registra a versão da API Vulkan disponível no driver de vídeo.

### 3. Otimizações Gráficas e Desbloqueio de Resolução
* **Desbloqueio High Quality (4096×4096)**: Remove as travas de resolução padrão do `crysystem` (1920×1200 e 2560×1600), liberando todas as opções gráficas (sombras, água, efeitos) em resoluções Ultrawide e 4K.
* **Correção de Flickering**: Elimina oscilações e artefatos pretos em placas NVIDIA e AMD ao rodar com DXVK.

### 4. Estabilidade e Compatibilidade Windows 10/11
* **Fix de Câmera**: Corrige o movimento errático do cursor e da câmera introduzido nas atualizações do Windows 10/11.
* **Fix de Stack 64-bit**: Estabiliza a execução do binário de 64 bits (`Aion.bin`) no Windows 11 24H2 e versões superiores.
* **Afinidade de CPUs de Alto Desempenho (32+ Threads)**: Limita de forma segura a máscara de afinidade em processadores com 32 ou mais núcleos lógicos, prevenindo travamentos conhecidos da CryEngine legada.

### 5. Telemetria e Registro Completo (`version_hook.log`)
Gera logs estruturados e thread-safe com carimbos de data/hora em milissegundos:
* **Processo & Inicialização**: PID, caminho do executável e parâmetros de linha de comando (`GetCommandLineW`).
* **Gráficos & DXVK**: Detecção de módulo, versão do DXVK e versão da API Vulkan.
* **Rede & Conexões**:
  * `connect()`: Socket ID, IP de destino, porta de destino e código de erro WSA / sucesso.
  * `send()` / `WSASend()`: Socket ID, bytes enviados, opcode do pacote e status.
  * `recv()` / `WSARecv()`: Socket ID, bytes recebidos, opcode e status.
  * `closesocket()`: Fechamento de sockets de rede.
  * `inet_ntoa()` / `lstrcpynA()`: Registro de IPs e eventos de spoofing.

---

## Como Compilar

### Pré-requisitos:
* Visual Studio 2022 Community com as ferramentas de compilação C++ (v143).
* Pacote Microsoft Detours (restaurado automaticamente via NuGet).

### Comando Automatizado:
```cmd
call "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
msbuild src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x64 /v:m /nologo
msbuild src\AionVersionDll.sln /p:Configuration=Release /p:Platform=x86 /v:m /nologo
```

Os binários gerados ficam localizados em:
* `src\x64\Release\version.dll` (para `bin64\version.dll` do cliente).
* `src\Release\version.dll` (para `bin32\version.dll` do cliente).