# BrService.dll — Módulo Nativo do Cliente Aion Classic 5.0

A **`BrService.dll`** é uma biblioteca nativa C++ (x64 / MSVC / MT estático) injetada no cliente Aion Classic 5.0 (`bin64/Aion.bin`), responsável por fornecer a interface de HUD de latência em tempo real, console gráfico Shugo, analisador de combate / DPS meter, Combo UI e integração bidirecional com o emulador Java 25 via WebSocket (RFC 6455).

---

## 1. Parâmetros de Linha de Comando (.bat)

O comportamento e a visibilidade de todos os recursos da DLL podem ser controlados dinamicamente através dos parâmetros de linha de comando no script de inicialização (`Start x64 - PORTUGUÊS BRASIL.bat` e `Start x64 - INGLÊS.bat`):

| Parâmetro | Valores | Descrição |
|---|---|---|
| `-console:enable/disable` | `enable`, `disable` | Controla o ícone do console (`>_`) e a janela modal/gaveta de ferramentas Shugo (**Shift + F3** ou **Ctrl + X**). |
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

## 2. Principais Funcionalidades

### 2.1. Atalhos de Teclado
- **Shift + F3**: Abre / fecha a janela do Console Shugo e Analisador de Combate.
- **Ctrl + X**: Inicia / reseta a sessão atual de combate e medição de DPS.

### 2.2. Combo UI & Pontos de Participação
- Renderização transparente em camadas (`GDI+` / `WS_EX_LAYERED`) com suporte a pop-scale de dano, partículas gif (`hit1.gif`, `flash-effect_*.gif`), banners de título (`combo_matador`, `combo_rei`, `combo_aniquilador`, etc.) e notificações de estados anormais (`state_atordoamento`, `state_silenciamento`, etc.).
- **Pontos de Participação**: A cada 1.000 golpes cumulativos registrados contra NPCs agressivos, o jogador é premiado com 1 Ponto de Participação, persistido de forma atômica no banco de dados (`player_participation_points` e `player_hits`).
- **Novo Recorde**: Notificação animada na tela ao bater recorde pessoal de golpes consecutivos.

### 2.3. Configurações de Combo UI no Console
Na seção de configurações do Console (**Shift + F3**), o jogador pode:
1. **Opacidade**: Slider linear de 10% a 100%.
2. **Tamanho / Escala**: Predefinições (70%, 100%, 130%) ou ajuste fino (+/-) entre 0.55x e 1.60x.
3. **Exibir / Ocultar**: Toggle rápido. **Regra de Negócio**: Quando ocultado pelo jogador, o sistema não contabiliza nem credita Pontos de Participação, mesmo que objetivos de combate sejam alcançados.

### 2.4. Radar de Combate de 4 Eixos
O radar de combate foi reformulado para exibir estritamente as métricas canônicas de mitigação e sobrevivência:
- **Topo**: Crítico (`CRIT` / `CRÍTICO`)
- **Direita**: Bloqueio (`BLOCK` / `BLOQUEIO`)
- **Base**: Esquiva (`DODGE` / `ESQUIVA`)
- **Esquerda**: Resistência (`RESIST` / `RESISTÊNCIA`)

### 2.5. Gráfico Fibonacci de Latência (60 Minutos)
- Desenhado logo abaixo do texto de latência (`XXms`) no HUD inferior direito.
- Linha ultra-fina (1px) em branco puro, sem fundo opaco, representando a evolução da latência nos últimos 60 minutos (buffer circular em memória com descarte automático de medições expiradas).

### 2.6. Disco / Emblema do Alvo (NPCs & Mobs)
- Renderiza na faixa de cabeçalho do alvo o disco ornamental com anéis metálicos concêntricos, chanfros cardeais e runa central estilizada.
- Cores e insígnias adaptadas automaticamente à classificação do NPC (`LEGENDARY`, `HERO`, `ELITE`, `NORMAL`) ou facção do jogador (`ELYOS`, `ASMODIANS`).

### 2.7. Ocultação Automática dos Overlays (Foco & Minimização)
- Todos os elementos visuais da DLL (HUD de Ping, ícone `>_`, janela do Console e janela de Combo UI) ocultam-se **imediatamente e sem delay** quando:
  - O jogo é minimizado (`IsIconic`).
  - O jogo perde o foco da janela (`WM_KILLFOCUS` ou `WA_INACTIVE`).
  - Outra janela é colocada em primeiro plano (`GetForegroundWindow` não pertence ao processo do Aion).
- Ao restaurar o foco no jogo, a interface reaparece instantaneamente no estado anterior.

### 2.8. Localização de Sprites
- A DLL resolve estritamente a pasta `sprites/effects/` no **mesmo diretório** em que ela reside (`bin64/sprites/effects/`).
- Não realiza buscas retrocedendo diretórios (`../`) nem pesquisa fora da raiz de binários do cliente.
- Apenas os assets efetivamente consumidos pelo motor de renderização são distribuídos no patch.

---

## 3. Instruções de Compilação

Para compilar e publicar a DLL para os diretórios do cliente e patch:

```bat
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - BrService.dll"
Build64.bat
```

Requisitos:
- Visual Studio 2022 (vcvarsall.bat x64)
- Windows SDK 10+
