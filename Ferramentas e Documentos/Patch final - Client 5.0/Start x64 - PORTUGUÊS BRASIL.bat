@echo off
cd /d "%~dp0"

REM =========================================================================================
REM  AION CLASSIC 5.0 - SCRIPT DE INICIALIZACAO (Start x64 - PORTUGUÊS BRASIL)
REM =========================================================================================
REM
REM  CONFIGURACOES DE RECURSOS DO BRSERVICE.DLL:
REM  Altere o valor para 'enable' para ativar ou 'disable' para desativar e ocultar.
REM  Por padrao, todas as funcoes vem ativadas (enable).
REM
REM  - HUD de Ping e Barras de Latencia em Tempo Real (Canto inferior direito):
set "PARAM_PINGUI=enable"
REM  - Medidor de DPS, Ranking de Dano e Grafico de Combate (Shift + F3):
set "PARAM_DPSMETERUI=enable"
REM  - Combo UI, Animacoes de Golpes e Pontos de Participacao:
set "PARAM_COMBOUI=enable"
REM
REM =========================================================================================
REM  DESCRICAO DETALHADA DOS PARAMETROS DO BRSERVICE.DLL:
REM
REM  -pingUi:enable/disable
REM     Exibe o medidor de MS e barras de sinal de conexao no estilo Aion 2.
REM     Se desativado, oculta os indicadores visuais de ping.
REM
REM  -DpsMeterUI:enable/disable
REM     Habilita a analise de combate em tempo real, curva Fibonacci de dano, radar de combate
REM     e classificacao de DPS por jogador/skill (Shift + F3). Se desativado, remove o painel.
REM
REM  -comboUi:enable/disable
REM     Ativa o Combo UI identico ao LostHunting com contador de hits, animacoes de particulas,
REM     efeitos visuais de combo e sistema de Pontos de Participacao (1 pt a cada 1000 hits).
REM =========================================================================================

start bin64\Aion.bin -token:#@br!classic50_token_2026# -ip:127.0.0.1 -port:2106 -lang:BRA -cc:2 -dss -dce -probability -pingUi:%PARAM_PINGUI% -DpsMeterUI:%PARAM_DPSMETERUI% -comboUi:%PARAM_COMBOUI%
