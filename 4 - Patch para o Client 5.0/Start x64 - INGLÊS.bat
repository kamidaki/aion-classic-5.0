@echo off
cd /d "%~dp0"

REM =========================================================================================
REM  AION CLASSIC 5.0 - SCRIPT DE INICIALIZACAO (Start x64 - INGLÊS)
REM =========================================================================================
REM
REM  CONFIGURACOES DE RECURSOS DO BRSERVICE.DLL:
REM  Altere o valor para 'enable' para ativar ou 'disable' para desativar e ocultar.
REM  Por padrao, todas as funcoes vem ativadas (enable).
REM
REM  - Console Shugo / Gaveta Lateral de Ajustes e Combate (Ctrl + X):
set "PARAM_CONSOLE=enable"
REM  - Voo Livre e Planeio em 100%% dos Mapas (g_freefly):
set "PARAM_FREEFLY=enable"
REM  - HUD de Ping e Barras de Latencia em Tempo Real (Canto inferior direito):
set "PARAM_PINGUI=enable"
REM  - Medidor de DPS, Ranking de Dano e Grafico de Combate (Dentro do Console):
set "PARAM_DPSMETERUI=enable"
REM  - Miniatura e Rotacao do Modelo 3D do Personagem (Dentro do Console):
set "PARAM_MODEL3D=enable"
REM  - Ajuste de Campo de Visao Panoramico / FOV (60 a 120 graus):
set "PARAM_FOV=enable"
REM  - Ajuste de Distancia Maxima da Camera / Zoom Out (ate 45 metros):
set "PARAM_CAMMAX=enable"
REM  - Desbloqueio e Limitador de FPS (60, 144, MAX):
set "PARAM_FPSUNLOCK=enable"
REM
REM =========================================================================================
REM  DESCRICAO DETALHADA DOS PARAMETROS DO BRSERVICE.DLL:
REM
REM  -console:enable/disable
REM     Controla o icone do console (>_) no canto inferior direito e a janela modal (gaveta)
REM     de ferramentas Shugo (Ctrl + X). Se desativado, o icone e a gaveta ficam ocultos.
REM
REM  -freefly:enable/disable
REM     Ativa voo e planeio (glide) livre irrestrito em 100%% dos mapas e cenarios de Atreia.
REM     Se desativado, segue as regras padroes de restricao de voo do motor CryEngine original.
REM
REM  -pingUi:enable/disable
REM     Exibe o medidor de MS e barras de sinal de conexao no estilo Aion 2.
REM     Se desativado, oculta os indicadores visuais de ping.
REM
REM  -DpsMeterUI:enable/disable
REM     Habilita a analise de combate em tempo real, curva Fibonacci de dano, radar de combate
REM     e classificacao de DPS por jogador/skill. Se desativado, remove esses graficos.
REM
REM  -Model3D:enable/disable
REM     Renderiza a miniatura 3D do personagem com rotacao e esqueleto dentro do console.
REM     Se desativado, a viewport 3D fica desativada e oculta para economia de processamento.
REM
REM  -fov:enable/disable
REM     Permite controlar o campo de visao panoramico (FOV) de 60 a 120 graus.
REM
REM  -camMax:enable/disable
REM     Permite distanciar a camera alem do limite padrao (ate 45 metros de zoom out).
REM
REM  -fpsUnlock:enable/disable
REM     Permite alternar a taxa de quadros entre 60 FPS, 144 FPS ou Ilimitado (MAX).
REM =========================================================================================

start bin64\Aion.bin -token:#@br!classic50_token_2026# -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -dss -dce -probability -console:%PARAM_CONSOLE% -freefly:%PARAM_FREEFLY% -pingUi:%PARAM_PINGUI% -DpsMeterUI:%PARAM_DPSMETERUI% -Model3D:%PARAM_MODEL3D% -fov:%PARAM_FOV% -camMax:%PARAM_CAMMAX% -fpsUnlock:%PARAM_FPSUNLOCK%
