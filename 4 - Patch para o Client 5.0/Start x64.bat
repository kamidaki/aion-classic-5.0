@echo off

REM =========================================================================================
REM  Aion Classic EU - Script de Inicializacao (Start_Classic.bat)
REM =========================================================================================
REM
REM  PARAMETROS MANDATORIOS DE LINHA DE COMANDO:
REM  -ip:127.0.0.1   - IP de destino da conexao com o Login Server (Porta TCP 2106).
REM  -port:2106      - Porta TCP oficial de autenticacao do Login Server.
REM  -lang:ENG       - Idioma do cliente (Ingles).
REM  -cc:2           - Country Code / Regiao (Classic EU / Gameforge).
REM  -dss            - Desativa checagens de seguranca secundarias do client engine.
REM  -dce            - Desativa verificacoes redundantes de ambiente do launcher oficial.
REM
REM  -----------------------------------------------------------------------------------------
REM  PARAMETROS AUXILIARES (INJETADOS / BYPASSADOS DE FORMA TRANSPARENTE VIA VERSION.DLL):
REM  Abaixo estao listados os parametros oficiais bypassados automaticamente pela version.dll
REM  para garantir inicializacao limpa, desativar conexoes oficiais da Gameforge e menus web:
REM
REM  -noweb               - Desabilita paginas Web de login do launcher, forcando a tela nativa do jogo.
REM  -classic             - Ativa o modo de regras, menus e interface grafica do Aion Classic.
REM  -nowebshop           - Desativa o carregamento da loja in-game via browser web embutido.
REM  -dnpshop             - Desativa integracoes e verificacoes da loja de DNP oficial (moeda cash).
REM  -st                  - Desativa envio de telemetria e estatisticas para os servidores da Gameforge.
REM  -dpetition           - Desativa o sistema de suporte / abertura de tickets da distribuidora.
REM  -hidepromo           - Oculta janelas, banners e ofertas promocionais na tela de selecao.
REM  -nosatab             - Remove abas de sub-contas e vinculos do launcher oficial da Gameforge.
REM  -nosarefund          - Desativa as verificacoes do sistema de reembolso de itens oficial.
REM  -disabletempbanner   - Desativa banners temporarios de anuncios na inicializacao.
REM  -disabledevaschedule - Desativa o calendario/agenda do evento Deva in-game oficial.
REM  -old_charInstance    - Habilita o motor classic de customizacao visual de personagens.
REM  -charnamemenu        - Permite a exibicao e funcionamento correto dos menus de criacao/renomear.
REM  -dwsm                - Desativa verificacoes de seguranca do Web Service Manager oficial.
REM  -probability         - Desativa requisicoes remotas de probabilidades de loot da Gameforge.
REM  -nospamcheck         - Desativa filtros remotos de spam de chat dos servidores oficiais.
REM =========================================================================================

start bin64\Aion.bin -ip:127.0.0.1 -port:2106 -lang:ENG -cc:2 -dss -dce