# BrService.dll — Módulo Nativo do Cliente Aion Classic 5.0

A **`BrService.dll`** é uma biblioteca nativa C++ (x64 / MSVC / MT estático) injetada no cliente Aion Classic 5.0 (`bin64/Aion.bin`), responsável por fornecer:
- HUD de latência em tempo real com gráfico Fibonacci de 60 minutos;
- Console gráfico Shugo e Analisador de Combate / DPS Meter;
- Combo UI com partículas, banners de status e Pontos de Participação;
- Integração bidirecional com o emulador Java 25 via WebSocket (RFC 6455);
- Arquitetura 100% isolada, assíncrona e resiliente a falhas (zero memory reading).

---

## 1. Parâmetros de Linha de Comando (.bat)

O comportamento e a visibilidade de todos os recursos da DLL podem ser controlados dinamicamente através dos parâmetros de linha de comando no script de inicialização (`Start x64 - PORTUGUÊS BRASIL.bat` e `Start x64 - INGLÊS.bat`):

| Parâmetro | Valores | Descrição |
|---|---|---|
| `-console:enable/disable` | `enable`, `disable` | Controla o ícone do console e a janela modal/gaveta Shugo (**Shift + F3**). |
| `-freefly:enable/disable` | `enable`, `disable` | Ativa o voo e planeio irrestrito em 100% dos mapas e cenários de Atreia. |
| `-pingUi:enable/disable` | `enable`, `disable` | Exibe o medidor de ping (ms), barras de latência no estilo Aion 2 e gráfico Fibonacci de 60 minutos. |
| `-DpsMeterUI:enable/disable` | `enable`, `disable` | Habilita a aba de combate, classificação de dano/DPS por jogador/skill, histórico e radar de 4 eixos. |
| `-comboUi:enable/disable` | `enable`, `disable` | Ativa o Combo UI idêntico ao LostHunting com partículas, banners de status e Pontos de Participação. |
| `-Model3D:enable/disable` | `enable`, `disable` | Renderiza a prévia 3D rotacionável do personagem ou do NPC selecionado dentro do console. |
| `-fov:enable/disable` | `enable`, `disable` | Permite o ajuste dinâmico do campo de visão panorâmico (FOV) entre 60° e 120°. |
| `-camMax:enable/disable` | `enable`, `disable` | Permite afastar a câmera além do limite oficial (até 45 metros de zoom out). |
| `-fpsUnlock:enable/disable` | `enable`, `disable` | Permite alternar o limitador de framerate entre 60 FPS, 144 FPS ou Ilimitado (MAX). |
| `-lang:BRA/ENG/ENU` | `BRA`, `ENG`, `ENU` | Define o idioma de todos os textos da interface: `ENG`/`ENU` para Inglês, `BRA` para Português. |

---

## 2. Arquitetura e Modelo de Concorrência

### 2.1. Princípios de Segurança e Isolamento
1. **Zero Memory Reading**: O DPS meter e todas as métricas de combate são **100% orientados a eventos via WebSocket**. Não há chamadas a `ReadProcessMemory`, offsets de memória do jogo ou heurísticas frágeis de ponteiro.
2. **Proteção do Loader Lock**: O ciclo de vida da DLL não executa esperas bloqueantes (`WaitForSingleObject`) dentro de `DLL_PROCESS_DETACH`. A inicialização pesada é delegada a uma `BackgroundInitThread` assíncrona, e a finalização é coordenada sem deadlocks.
3. **Comunicação Cross-Thread Segura (PostMessage)**: Threads de rede (`WebSocketClient`) e de medição de latência (`PingEngine`) nunca manipulam janelas diretamente (`ShowWindow`, `UpdateLayeredWindow`, `InvalidateRect`). Em vez disso, usam `PostMessage` assíncrono para a thread dona das janelas (`WatchdogThread`).
4. **Handles Atômicos**: Todos os handles de janela (`g_hPingHudWnd`, `g_hDrawerModalWnd`, `g_hComboWnd`) são armazenados em `std::atomic<HWND>`, garantindo leituras e escritas sem data race.
5. **Cache de Assets sem Bloqueio de I/O**: O `IconManager` realiza leitura de disco e decodificação DDS/PNG fora dos locks de cache (double-checked locking pattern), evitando congelamentos na thread de renderização.

### 2.2. Mapa de Threads

| Thread | Proprietário | Responsabilidade | Modelo de Sincronização |
|---|---|---|---|
| `BackgroundInitThread` | `DllMain.cpp` | Inicialização pesada assíncrona (GDI+, Config, DB, Ícones) | `std::atomic<bool> s_initDone` |
| `WatchdogThread` | `ServiceWorker.cpp` | Message pump Win32, registro de hotkey global (Shift+F3), monitor de ciclo de vida | `MsgWaitForMultipleObjects`, `RegisterHotKey` |
| `ClientThread` | `WebSocketClient.cpp` | Conexão TCP persistente, handshake RFC 6455, parser de frames | `std::mutex s_sendMutex`, `s_hWakeEvent` para shutdown instantâneo |
| `WorkerThread` (Ping) | `PingEngine.cpp` | Medição ICMP a cada 2500ms | `s_hWakeEvent` para cancelamento imediato |
| `WorkerThread` (DB) | `CombatDb.cpp` | Gravação assíncrona no SQLite (WAL mode) em lotes | `std::deque` de eventos + `s_hWakeEvent` |
| `RenderThread` (Combo) | `ComboRenderer.cpp` | Renderização a 60 FPS com GDI+ layered windows | `std::mutex stateMutex` |

---

## 3. Principais Funcionalidades

### 3.1. Atalhos de Teclado
- **Shift + F3**: Abre / fecha a janela do Console Shugo e Analisador de Combate (registrado via `RegisterHotKey`, sem polling de CPU).
- **Ctrl + X**: Inicia / reseta a sessão atual de combate e medição de DPS.

### 3.2. Combo UI & Pontos de Participação
- Renderização transparente em camadas (`GDI+` / `WS_EX_LAYERED`) com suporte a pop-scale de dano, partículas gif (`hit1.gif`, `flash-effect_*.gif`), banners de título (`combo_matador`, `combo_rei`, `combo_aniquilador`, etc.) e notificações de estados anormais (`state_atordoamento`, `state_silenciamento`, etc.).
- **Pontos de Participação**: A cada 1.000 golpes cumulativos registrados contra NPCs agressivos, o jogador é premiado com 1 Ponto de Participação, persistido de forma atômica no banco de dados (`player_participation_points` e `player_hits`).
- **Novo Recorde**: Notificação animada na tela ao bater recorde pessoal de golpes consecutivos.

### 3.3. Configurações de Combo UI no Console
Na seção de configurações do Console (**Shift + F3**), o jogador pode:
1. **Opacidade**: Slider linear de 10% a 100%.
2. **Tamanho / Escala**: Predefinições (70%, 100%, 130%) ou ajuste fino (+/-) entre 0.55x e 1.60x.
3. **Exibir / Ocultar**: Toggle rápido. **Regra de Negócio**: Quando ocultado pelo jogador, o sistema não contabiliza nem credita Pontos de Participação, mesmo que objetivos de combate sejam alcançados.

### 3.4. Radar de Combate de 4 Eixos
O radar de combate exibe estritamente as métricas canônicas de mitigação e sobrevivência, populadas de forma autoritativa pelo emulador via evento `RADAR_METRICS`:
- **Topo**: Crítico (`CRIT` / `CRÍTICO`) — derivado de dados reais de combate
- **Direita**: Bloqueio (`BLOCK` / `BLOQUEIO`) — atributos de jogo reais do personagem
- **Base**: Esquiva (`DODGE` / `ESQUIVA`) — atributos de jogo reais do personagem
- **Esquerda**: Resistência (`RESIST` / `RESISTÊNCIA`) — atributos de jogo reais do personagem

### 3.5. Gráfico Fibonacci de Latência (60 Minutos)
- Desenhado logo abaixo do texto de latência (`XXms`) no HUD inferior direito.
- Linha ultra-fina (1px) em branco puro, sem fundo opaco, representando a evolução da latência nos últimos 60 minutos (buffer `std::deque` circular com pop_front O(1)).

### 3.6. Disco / Emblema do Alvo (NPCs & Mobs)
- Renderiza na faixa de cabeçalho do alvo o disco ornamental com anéis metálicos concêntricos, chanfros cardeais e runa central estilizada.
- Cores e insígnias adaptadas automaticamente à classificação do NPC (`LEGENDARY`, `HERO`, `ELITE`, `NORMAL`) ou facção do jogador (`ELYOS`, `ASMODIANS`).

### 3.7. Ocultação Automática dos Overlays (Foco & Minimização)
- Todos os elementos visuais da DLL (HUD de Ping, janela do Console e janela de Combo UI) ocultam-se **imediatamente e sem delay** quando:
  - O jogo é minimizado (`IsIconic`).
  - O jogo perde o foco da janela (`WM_KILLFOCUS` ou `WA_INACTIVE`).
  - Outra janela é colocada em primeiro plano (`GetForegroundWindow` não pertence ao processo do Aion).
- Ao restaurar o foco no jogo, a interface reaparece instantaneamente no estado anterior.

### 3.8. Internacionalização (I18n) e Persistência
- Seleção de idioma entre **Português (BR)** e **English (US)** diretamente na aba **Advanced** do Console.
- Persistência automática em `br_settings.ini` sob `[General] Language`.
- Consultas thread-safe em tempo de renderização via flag atômica `g_isEnglish`.

---

## 4. Instruções de Compilação e Publicação

Para compilar a DLL de 64 bits e publicá-la automaticamente para o patch do cliente e o diretório de jogo real:

```bat
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - BrService.dll"
Build64.bat
```

Requisitos:
- Visual Studio 2022 (Community / Professional / Enterprise) com workload C++ (x64 MSVC)
- Windows SDK 10+
- SQLite3 (incluído no repositório em `database/sqlite3.c`)
