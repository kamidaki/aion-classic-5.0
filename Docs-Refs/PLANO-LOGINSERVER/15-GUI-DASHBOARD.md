# 15 - GUI E DASHBOARD MODERNO (ESTILO MACOS/IOS/GRAFANA)

## OBJETIVO
Desenvolver a interface gráfica moderna para o `Auto-Start EmuRust.exe`, inspirada nas diretrizes de design do macOS, iOS e dashboards do Grafana, oferecendo 3 cards de controle independentes, gráficos de CPU/Memória em tempo real e um Log Center central de alta legibilidade.

## PROBLEMA
Interfaces de emuladores tradicionais são arcaicas, cheias de poluição visual, formulários rígidos do Windows Forms ou dependentes de terminais pretos sem ergonomia.

## CAUSA
Falta de investimento em UX moderna e design system profissional em projetos de emulação.

## ANÁLISE
A interface deve possuir:
1. **Design System & Estética Visual**:
   * Paleta escura elegante (Dark Mode sofisticado com tons de `#0f172a`, `#1e293b`, `#334155`).
   * Tipografia moderna e limpa (Inter / System UI).
   * Efeitos sutis de glassmorphism, cantos arredondados (border-radius suave de 12px a 16px) e sombras suaves.
   * Transições suaves em hover e micro-animações de status (indicadores pulsantes em verde para Online, vermelho para Offline/Crashed, amarelo para Starting/Stopping).
2. **Dashboard com 3 Cards Independentes**:
   * **Card 1: Login-Server**
     * Indicador de Status (ONLINE / OFFLINE / CRASHED).
     * Uptime do processo (ex: `02h 14m 33s`).
     * Barras/Gauges de CPU (%) e Memória (MB).
     * Métricas de conexões ativas e sessões emitidas.
     * Botões de ação: `[LIGAR]` (Verde), `[PARAR]` (Vermelho), `[REINICIAR]` (Azul).
   * **Card 2: Game-Server**
     * Indicador de Status, Uptime, CPU (%), Memória (MB/GB).
     * Jogadores online no mundo e entidades ativas (NPCs: 39.747 carregados).
     * Botões de ação: `[LIGAR]`, `[PARAR]`, `[REINICIAR]`.
   * **Card 3: Chat-Server**
     * Indicador de Status, Uptime, CPU (%), Memória (MB).
     * Canais ativos e contagem de mensagens por minuto.
     * Botões de ação: `[LIGAR]`, `[PARAR]`, `[REINICIAR]`.
3. **Log Center Central Unificado**:
   * Console estilizado com auto-scroll inteligente.
   * **Identificação Visual por Cores**:
     * **Login-Server**: Mensagens identificadas em **Branco / Prata**.
     * **Game-Server**: Mensagens identificadas em **Verde Esmeralda** (`#10b981`).
     * **Chat-Server**: Mensagens identificadas em **Ciano / Azul Claro** (`#06b6d4`).
   * Barra de Ferramentas do Log Center:
     * Filtros por Servidor (`Todos`, `Login`, `Game`, `Chat`).
     * Filtros por Nível (`INFO`, `WARN`, `ERROR`, `DEBUG`).
     * Campo de busca textual em tempo real.
     * Botão `Limpar Visualização` e Botão `Pausar/Resumir Stream`.

## SOLUÇÃO
Implementar a interface gráfica nativa em Rust no crate `auto-start` utilizando um servidor local HTTP/WebSocket assíncrono embutido no binário com frontend renderizado via Webview nativo (Windows WebView2) ou GUI Iced/Egui customizada, garantindo consumo mínimo de memória (< 40 MB) e renderização a 60 FPS com aceleração por hardware.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/auto-start/src/ui/mod.rs`
* `Emulador-Rust/auto-start/src/ui/dashboard.rs`
* `Emulador-Rust/auto-start/src/ui/assets/index.html`
* `Emulador-Rust/auto-start/src/ui/assets/style.css`
* `Emulador-Rust/auto-start/src/ui/assets/app.js`

## IMPLEMENTAÇÃO
* Criação dos componentes visuais e tokens de estilo CSS.
* Integração de WebSocket bidirecional para streaming de métricas e logs em tempo real (100ms de latência máxima sem polling agressivo).

## TESTES
* Teste de responsividade da interface.
* Teste de cliques nos botões de controle de cada servidor.
* Teste de visualização e filtragem de logs sob alto volume.

## VALIDAÇÃO
* Interface abre instantaneamente ao executar `Auto-Start EmuRust.exe`.
* Controles respondem imediatamente e os gráficos refletem o uso real de recursos do sistema.

## RISCOS
* Dependência de runtime do WebView2 no Windows.
* Mitigação: O WebView2 já vem pré-instalado em todos os Windows 10 e Windows 11 modernos.

## DEPENDÊNCIAS
* `tokio`, `warp` / `axum` / `wry`, `serde`, `serde_json`.

## TO-DO
- [x] Desenhar layout e design system dos 3 cards.
- [x] Implementar Log Center com colorização por servidor.
- [x] Integrar gráficos e métricas em tempo real.
- [x] Testar fluidez e controles da GUI.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
