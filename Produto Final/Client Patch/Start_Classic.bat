@echo off

set "ENABLE_DXVK=1"
REM =========================================================================================
REM  Aion Classic EU - Script de Inicializacao Simplificado (Start_Classic.bat)
REM =========================================================================================
REM
REM  PARAMETROS MANDATORIOS DE REDE:
REM  -ip:127.0.0.1   - IP de destino da conexao de Login (Porta 2106).
REM  -port:2106      - Porta TCP oficial do Login Server.
REM  -lang:ENG       - Idioma do cliente (Ingles).
REM  -cc:2           - Country Code / Bracket para a regiao Classic EU.
REM
REM  -----------------------------------------------------------------------------------------
REM  PARAMETROS AUXILIARES (OCULTOS / BYPASSADOS VIA VERSION.DLL):
REM  Abaixo estao descritos os parametros opcionais oficiais que foram descartados deste .BAT
REM  e que agora sao injetados de forma transparente via version.dll. Quem os processa e a
REM  propria binaria do jogo (Aion.bin / game.dll):
REM
REM  -noweb               - Desabilita carregamento de paginas Web de login e abas do launcher,
REM                         forcando o cliente a exibir a tela de login nativa do jogo.
REM  -classic             - Define a interface e regras de comportamento para a versao Classic
REM                         do Aion, modificando menus e botoes para o layout correto.
REM  -nowebshop           - Desativa o carregamento da loja in-game via browser web embutido.
REM  -dnpshop             - Desativa integracoes e verificacoes da loja de DNP (moeda cash).
REM  -st                  - Desativa telemetrias e estatisticas que seriam enviadas a Gameforge.
REM  -dpetition           - Desativa o sistema de peticoes/suporte via ticket da desenvolvedora.
REM  -hidepromo           - Oculta janelas e banners promocionais na tela de selecao.
REM  -nosatab             - Remove abas extras de contas associadas ao launcher.
REM  -nosarefund          - Desativa as verificacoes do sistema de reembolso de itens.
REM  -disabletempbanner   - Desativa banners temporarios de anuncios.
REM  -disabledevaschedule - Desativa o calendario/agenda do evento Deva in-game.
REM  -old_charInstance    - Habilita o motor classic antigo de customizacao de personagens.
REM  -charnamemenu        - Permite a exibicao e interacao correta com menus de renomear chars.
REM =========================================================================================

start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2