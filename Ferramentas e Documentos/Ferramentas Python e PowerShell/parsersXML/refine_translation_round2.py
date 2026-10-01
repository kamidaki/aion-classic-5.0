#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Auditoria e Refinamento de Traducao - Round 2 (Deep Quality & Clean-up)
Aion Classic 5.0 PT-BR Localization

Escopo:
1. Eliminacao de palavras duplicadas residuais ('de de Elite' -> 'de Elite', 'de de' -> 'de', 'do Dragao Dragao Garras' -> 'Garras do Dragao', etc.)
2. Correcao de insercoes anomalas com apostrofo ingles no meio de substantivos:
   - '[Entidade]’Colar s' -> 'Colar de [Entidade]' / 'Colar do [Entidade]'
   - '[Entidade]’Brinco s' -> 'Brinco de [Entidade]' / 'Brinco do [Entidade]'
   - '[Entidade]’Anel s' -> 'Anel de [Entidade]' / 'Anel do [Entidade]'
   - '[Entidade]’[Recipiente] de s [Item]' -> '[Recipiente] de [Item] de [Entidade]'
3. Normalizacao de nomes e titulos com genitivo ingles ('Owner’s Item' -> 'Item de Owner' / 'Item do Owner'):
   - General de Brigada, Comodoro, Batalha, Yasba, Vidar, Fasimedes, Mastarius, Veille, Triniel, Valetta, Sunayaka, Lodas, etc.
4. Extirpacao de falsos cognatos grotescos:
   - 'palito de fosforo' / 'partidas' quando referente a 'match' -> 'correspondente a' / 'combina com'
   - 'resultado ou ponto final Engrenagem' -> 'Equipamento Final'
   - 'suicidio esquadrao' -> 'Esquadrao Suicida'
   - 'funcionarios' (Staff) -> 'Cajado'
   - 'deputado' (MP / Deputy) -> 'MP' / 'Subcomandante'
   - 'cardapio' (Menu) -> 'menu'
   - 'Ministro' (Lesser/Minor) -> 'Pergaminho Menor'
   - 'area em forma de ventilador' -> 'area em leque'
5. Refinamento de descricoes de itens de quebra-cabeca (Puzzles/Obras de Arte).
6. Ajuste de termos militares Balaur: 'Guilda Indratu/Bakarma/Anuhart' -> 'Legiao Indratu/Bakarma/Anuhart'.
7. Correcao de verbos de acao em ingles vazados ('Deals pesado dano' -> 'Causa dano pesado').
"""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')

def read_xml_utf16(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data.startswith(b'\xff\xfe'):
        return data[2:].decode('utf-16le', errors='replace')
    elif data.startswith(b'\xfe\xff'):
        return data[2:].decode('utf-16be', errors='replace')
    elif data.startswith(b'\xef\xbb\xbf'):
        return data[3:].decode('utf-8', errors='replace')
    return data.decode('utf-8', errors='replace')

def write_xml_utf16(filepath, content):
    with open(filepath, 'wb') as f:
        f.write(b'\xff\xfe')
        f.write(content.encode('utf-16le'))

def apply_refinements(text, fname):
    mod_count = 0
    stats = {}

    def track(cat, n):
        nonlocal mod_count
        if n > 0:
            mod_count += n
            stats[cat] = stats.get(cat, 0) + n

    # -------------------------------------------------------------
    # 1. Broken inserted apostrophes (Colar, Brinco, Anel, Bolsa, Pacote)
    # -------------------------------------------------------------
    def fix_inserted_apostrophe(m):
        prefix = m.group(1).strip()
        item_type = m.group(2).strip()
        low = prefix.lower()
        if low in ['batalha']:
            return f'{item_type} de {prefix}'
        elif low in ['centurião', 'tribuno', 'legado', 'comandante', 'comodoro', 'general de brigada', 'primus pilus', 'devourer']:
            if low == 'devourer':
                return f'{item_type} do Devorador'
            return f'{item_type} do {prefix}'
        elif low in ['guardião', 'arconte']:
            return f'{item_type} do {prefix}'
        return f'{item_type} de {prefix}'

    p_ins_jewel = re.compile(r'([A-Za-zÀ-ÿ\s]+)[’\'](Colar|Brinco|Anel)\s*s\b')
    text, n = p_ins_jewel.subn(fix_inserted_apostrophe, text)
    track("Joias com apóstrofo invertido", n)

    # Containers: [Owner]’[Container] de s [Item]
    def fix_inserted_container(m):
        owner = m.group(1).strip()
        container = m.group(2).strip()
        item = m.group(3).strip()
        low_owner = owner.lower()
        if low_owner in ['recruta', 'aprendiz', 'intendente', 'aventureiro', 'general de brigada', 'brigada']:
            art = 'do'
            if low_owner == 'brigada': owner = 'General de Brigada'
        elif low_owner in ['guarda']:
            art = 'da'
        else:
            art = 'de'
        return f'{container} de {item} {art} {owner}'

    p_ins_cont = re.compile(r'([A-Za-zÀ-ÿ]+)[’\']([A-Za-zÀ-ÿ]+)\s+de\s+s\s+([A-Za-zÀ-ÿ]+)', re.I)
    text, n = p_ins_cont.subn(fix_inserted_container, text)
    track("Recipientes com apóstrofo invertido", n)

    # -------------------------------------------------------------
    # 2. Duplicate Words
    # -------------------------------------------------------------
    p_de_elite = re.compile(r'\bde\s+de\s+elite\b', re.I)
    text, n = p_de_elite.subn('de Elite', text)
    track("Duplicação 'de de Elite'", n)

    p_de_guard = re.compile(r'\bde\s+de\s+Guardião\b', re.I)
    text, n = p_de_guard.subn('do Guardião', text)
    track("Duplicação 'de de Guardião'", n)

    p_de_arc = re.compile(r'\bde\s+de\s+Arconte\b', re.I)
    text, n = p_de_arc.subn('do Arconte', text)
    track("Duplicação 'de de Arconte'", n)

    p_dede = re.compile(r'\bde\s+de\b', re.I)
    text, n = p_dede.subn('de', text)
    track("Duplicação geral 'de de'", n)

    dragon_map = [
        (re.compile(r'Verdadeiro\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Real'),
        (re.compile(r'Nobre\s+Verdadeiro\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Real'),
        (re.compile(r'Branco\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Branco'),
        (re.compile(r'Nobre\s+Branco\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Branco'),
        (re.compile(r'Sábio\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Sábio'),
        (re.compile(r'Nobre\s+Sábio\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Sábio'),
        (re.compile(r'Celeste\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Imperador Dragão Celeste'),
        (re.compile(r'Nobre\s+Celeste\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Imperador Dragão Celeste'),
        (re.compile(r'Estrela\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Estelar'),
        (re.compile(r'Nobre\s+Estrela\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Estelar'),
        (re.compile(r'Preto\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Negro'),
        (re.compile(r'Nobre\s+Preto\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Negro'),
        (re.compile(r'Sombrio\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Sombrio'),
        (re.compile(r'Nobre\s+Sombrio\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Sombrio'),
        (re.compile(r'Chifrudo\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão Chifrudo'),
        (re.compile(r'Nobre\s+Chifrudo\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras Nobres do Dragão Chifrudo'),
        (re.compile(r'Sunstorm\s+do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras da Tempestade Solar do Dragão'),
        (re.compile(r'Cinto\s+do\s+Dragão\s+Dragão', re.I), 'Cinto do Dragão'),
        (re.compile(r'do\s+Dragão\s+Dragão\s+Garras', re.I), 'Garras do Dragão'),
        (re.compile(r'engrenagem\s+de\s+engrenagem\s+de\s+engrenagem', re.I), 'Equipamento Final'),
        (re.compile(r'Ministro\s+de\s+vento\s+furioso\s+de\s+vento\s+furioso', re.I), 'Pergaminho Menor do Vento Furioso'),
    ]
    for reg, repl in dragon_map:
        text, n = reg.subn(repl, text)
        track("Duplicações 'Dragão Dragão' e afins", n)

    # -------------------------------------------------------------
    # 3. Match / Matches False Friends ('palito de fósforo', 'partidas')
    # -------------------------------------------------------------
    match_map = [
        (re.compile(r'palito\s+de\s+fósforo\s+Seu\(Sua\)\s+Facção', re.I), 'correspondente à sua Facção'),
        (re.compile(r'palito\s+de\s+fósforo\s+Seu\(Sua\)\s+classe', re.I), 'correspondente à sua classe'),
        (re.compile(r'que\s+palito\s+de\s+fósforo\s+Seu\(Sua\)\s+Facção', re.I), 'correspondente à sua Facção'),
        (re.compile(r'para\s+palito\s+de\s+fósforo\s+Seu\(Sua\)\s+classe', re.I), 'correspondente à sua classe'),
        (re.compile(r'Eles\(as\)’re\s+quadril\s+e\s+palito\s+de\s+fósforo\s+o\(a\)\s+Dragão\s+Manto\.', re.I), 'São estilosas e combinam com o Manto do Dragão.'),
        (re.compile(r'a\s+boxe\s+palito\s+de', re.I), 'uma luta de boxe'),
        (re.compile(r'que\s+partidas\s+Seu\(Sua\)\s+Facção', re.I), 'correspondente à sua Facção'),
        (re.compile(r'que\s+partidas\s+Seu\(Sua\)\s+classe', re.I), 'correspondente à sua classe'),
        (re.compile(r'que\s+partidas\s+o\(a\)\s+escola\s+uniforme', re.I), 'que combina com o uniforme escolar'),
    ]
    for reg, repl in match_map:
        text, n = reg.subn(repl, text)
        track("Falso cognato 'match' (palito de fósforo / partidas)", n)

    # -------------------------------------------------------------
    # 4. 'resultado ou ponto final' (End-game Gear / UI End)
    # -------------------------------------------------------------
    end_gear_map = [
        (re.compile(r'Projeto:\s*resultado\s+ou\s+ponto\s+final\s+Engrenagem\s+Névoa\s+Detector', re.I), 'Projeto: Detector de Névoa de Equipamento Final'),
        (re.compile(r'Luz\s+de\s+Resultado\s+ou\s+ponto\s+final\s+Engrenagem', re.I), 'Luz de Equipamento Final'),
        (re.compile(r'n\s+poeta\s+esplendor\s+Luz\s+de\s+Resultado\s+ou\s+ponto\s+final\s+Engrenagem', re.I), 'Luz Resplandecente de Poeta do Equipamento Final'),
        (re.compile(r'Item\s+da\s+Missão\s+de\s+Engrenagem\s+resultado\s+ou\s+ponto\s+final', re.I), 'Item da Missão de Equipamento Final'),
        (re.compile(r'Teste\s+resultado\s+ou\s+ponto\s+final\s+Engrenagem\s+Lendable\s+Classe\s+Espada', re.I), 'Espada de Teste de Equipamento Final'),
        (re.compile(r'Teste\s+resultado\s+ou\s+ponto\s+final\s+Engrenagem\s+mito\s+Classe\s+Espada', re.I), 'Espada Mítica de Teste de Equipamento Final'),
        (re.compile(r'PNJ\s+Elyos\s+resultado\s+ou\s+ponto\s+final\s+Engrenagem\s+Orbe\s+02', re.I), 'Orbe 02 de NPC Elyos de Equipamento Final'),
        (re.compile(r'resultado\s+ou\s+ponto\s+final\s+Engrenagem\s+Mármore\s+Edifício', re.I), 'Edifício Residencial de Mármore Superior'),
        (re.compile(r'Perímetro\s+de\s+segurança\s+de\s+fúria\s+de\s+Antriksha\s+resultado\s+ou\s+ponto\s+final', re.I), 'Perímetro de Segurança da Fúria de Antriksha Final'),
        (re.compile(r'Cerimônia\s+de\s+engrenagem\s+a\s+etapa', re.I), 'Cerimônia de Equipamento Daevanion'),
        (re.compile(r'armadura\s+de\s+engrenagem\s+a\s+etapa', re.I), 'armadura de equipamento Daevanion'),
        (re.compile(r'arma\s+de\s+engrenagem\s+definitiva', re.I), 'arma de equipamento definitivo'),
        (re.compile(r'itens\s+de\s+engrenagem\s+a\s+etapa', re.I), 'itens de equipamento Daevanion'),
        (re.compile(r'Fazendo\s+a\s+melhor\s+arma\s+de\s+engrenagem', re.I), 'Criando a Melhor Arma Daevanion'),
    ]
    for reg, repl in end_gear_map:
        text, n = reg.subn(repl, text)
        track("Tradução errônea 'resultado ou ponto final Engrenagem'", n)

    if fname == 'stringtable_dialog.xml':
        dialog_btn_map = [
            (re.compile(r'(<name>STR_DLG_START_MENU_DEVA_PASS</name>\s*<body>)resultado ou ponto final(</body>)'), r'\1Encerrar\2'),
            (re.compile(r'(<name>STR_DLG_START_MENU_AION_LOOK</name>\s*<body>)Detalhes RESULTADO OU PONTO FINAL(</body>)'), r'\1Encerrar Detalhes\2'),
            (re.compile(r'(<name>STR_DLG_START_MENU_N_SHOP</name>\s*<body>)Informações sobre ingressos RESULTADO OU PONTO FINAL(</body>)'), r'\1Encerrar Informações de Ingressos\2'),
            (re.compile(r'(<name>STR_DLG_START_MENU_QUNA_MARKET</name>\s*<body>)Você pode comprar ingressos RESULTADO OU PONTO FINAL na loja da Aion\.(</body>)'), r'\1Você pode comprar ingressos na Loja Aion.\2'),
            (re.compile(r'(<name>STR_DLG_START_MENU_CHARACTER_SETECTION</name>\s*<body>)Detalhes RESULTADO OU PONTO FINAL(</body>)'), r'\1Encerrar Detalhes\2'),
            (re.compile(r'(<name>STR_DLG_START_MENU_ACCESS_REWARD</name>\s*<body>)Níveis RESULTADO OU PONTO FINAL(</body>)'), r'\1Encerrar Níveis\2'),
            (re.compile(r'(<name>STR_GUILD_AUTH_DIALOG__SUBMASTER</name>\s*<body>)Deputado(</body>)'), r'\1Subcomandante\2'),
        ]
        for reg, repl in dialog_btn_map:
            text, n = reg.subn(repl, text)
            track("Botões de Menu Inicial 'Encerrar'", n)

    if fname == 'client_strings_ui.xml':
        ui_rank_map = [
            (re.compile(r'(<name>STR_GUILD_RANK_NAME_SUBMASTER</name>\s*<body>)Deputado(</body>)'), r'\1Subcomandante\2'),
        ]
        for reg, repl in ui_rank_map:
            text, n = reg.subn(repl, text)
            track("Cargo de Legião Subcomandante", n)

    # -------------------------------------------------------------
    # 5. Suicídio Esquadrão -> Esquadrão Suicida
    # -------------------------------------------------------------
    p_suicide = re.compile(r'suicídio\s+esquadrão', re.I)
    text, n = p_suicide.subn('Esquadrão Suicida', text)
    track("'Suicídio esquadrão' -> 'Esquadrão Suicida'", n)

    p_suicide_wings = re.compile(r'Asas\s+de\s+(?:De\s+)?Elite\s+(Guardião|Arconte)\s+Esquadrão\s+Suicida', re.I)
    text, n = p_suicide_wings.subn(r'Asas do Esquadrão Suicida do \1 de Elite', text)
    track("Sintaxe Asas do Esquadrão Suicida", n)

    p_suicide_tunic = re.compile(r'Túnica\s+de\s+(?:De\s+)?Elite\s+(Guardião|Arconte)\s+Esquadrão\s+Suicida', re.I)
    text, n = p_suicide_tunic.subn(r'Túnica do Esquadrão Suicida do \1 de Elite', text)
    track("Sintaxe Túnica do Esquadrão Suicida", n)

    # -------------------------------------------------------------
    # 6. 'funcionários' (Staff / Cajado)
    # -------------------------------------------------------------
    staff_map = [
        (re.compile(r'%Dos\s+funcionários\s+da\s+Nanyu\s+de\s+%0', re.I), '%Do Cajado de Nanyu de %0'),
        (re.compile(r'Projeto:\s*funcionários\s+dignos\s+de\s+koa', re.I), 'Projeto: Cajado Nobre de Koa'),
        (re.compile(r'Projeto:\s*funcionários\s+dignos\s+de\s+EGRASI', re.I), 'Projeto: Cajado Nobre de Egrasi'),
        (re.compile(r'Projeto\s+Balic:\s*funcionários\s+do\s+dragão\s+sábio', re.I), 'Projeto Balaur: Cajado do Dragão Sábio'),
        (re.compile(r'Projeto\s+Balic:\s*funcionários\s+do\s+Dragão\s+Sábio', re.I), 'Projeto Balaur: Cajado do Dragão Sábio'),
        (re.compile(r'Ensina\s+como\s+criar\s+funcionários\s+de\s+Betua\.', re.I), 'Ensina como criar Cajado de Betua.'),
        (re.compile(r'(<name>STR_VENDOR_DIALOG__VENDOR_TAB_FRAME_WIDGET2_WEAPON_EXT_WEAPON_LIST_WIDGET1_ITEM15</name>\s*<body>)Funcionários(</body>)'), r'\1Cajado\2'),
    ]
    for reg, repl in staff_map:
        text, n = reg.subn(repl, text)
        track("Falso cognato 'funcionários' -> 'Cajado'", n)

    # -------------------------------------------------------------
    # 7. 'deputado' / 'deputados' (MP / Subcomandante)
    # -------------------------------------------------------------
    deputado_map = [
        (re.compile(r'Digno\s+Durável\s+e\s+Deputados', re.I), 'Ombreiras de Couro Duráveis e Dignas'),
        (re.compile(r'e\s+seu\s+deputado\s+por', re.I), 'e seu MP por'),
        (re.compile(r'aumenta\s+seu\s+deputado', re.I), 'aumenta seu DP'),
        (re.compile(r'deputado\s+Comandante', re.I), 'Vice-comandante'),
        (re.compile(r'Deputado\s+Lohan', re.I), 'Subcomandante Lohan'),
        (re.compile(r'Deputado\s+Lagel', re.I), 'Subcomandante Lagel'),
        (re.compile(r'Deputado\s+Hanuman', re.I), 'Subcomandante Hanuman'),
        (re.compile(r'deputado\s+Hanuman', re.I), 'Subcomandante Hanuman'),
        (re.compile(r'Deputado\s+Lamipedon', re.I), 'Subcomandante Lamipedon'),
        (re.compile(r'Bubu\s+DEPUTADO', re.I), 'Bubu Mep'),
        (re.compile(r'Budu\s+DEPUTADO', re.I), 'Bubu Mep'),
        (re.compile(r'Roooo-M-DEPUTADO', re.I), 'Roooo-M-MP'),
        (re.compile(r'Dano\s+adicional\s+ao\s+deputado', re.I), 'Dano adicional ao MP'),
        (re.compile(r'As\s+habilidades\s+não\s+custam\s+que\s+não\s+seja\s+deputado\s+para\s+usar\.', re.I), 'As habilidades não consomem MP ao serem usadas.'),
    ]
    for reg, repl in deputado_map:
        text, n = reg.subn(repl, text)
        track("Falso cognato 'deputado' -> 'MP' / 'Subcomandante'", n)

    # -------------------------------------------------------------
    # 8. 'Ministro' (Lesser/Minor)
    # -------------------------------------------------------------
    ministro_map = [
        (re.compile(r'Ministro\s+de\s+rolagem\s+à\s+prova\s+de\s+terra', re.I), 'Pergaminho Menor de Resistência à Terra'),
        (re.compile(r'Ministro\s+anti-choque\s+físico', re.I), 'Pergaminho Menor Anti-Choque Físico'),
        (re.compile(r'Projeto:\s*Ministro\s+de\s+Rolagem\s+Anti-choque\s+física', re.I), 'Projeto: Pergaminho Menor Anti-Choque Físico'),
        (re.compile(r'Projeto:\s*Ministro\s+Mágico\s+Anti-Choque\s+Rolagem', re.I), 'Projeto: Pergaminho Menor Anti-Choque Mágico'),
        (re.compile(r'\[Recompensa\s+da\s+Guilda\]\s*Ministro\s+de\s+vento\s+furioso', re.I), '[Recompensa da Legião] Pergaminho Menor do Vento Furioso'),
        (re.compile(r'\[Conteúdo\s+especial\]\s*Ministro\s+de\s+vento\s+furioso\s+com\s+raiva', re.I), '[Evento] Pergaminho Menor do Vento Furioso'),
        (re.compile(r'\[Conteúdo\s+especial\]\s*Ministro\s+anti-choque\s+de\s+pergaminho', re.I), '[Evento] Pergaminho Menor Anti-Choque'),
        (re.compile(r'Ministro\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I), 'Traje de Banho Elegante'),
    ]
    for reg, repl in ministro_map:
        text, n = reg.subn(repl, text)
        track("Falso cognato 'Ministro' -> 'Pergaminho Menor'", n)

    # -------------------------------------------------------------
    # 9. 'cardápio' -> 'menu'
    # -------------------------------------------------------------
    p_cardapio = re.compile(r'\bcardápio\b', re.I)
    def fix_cardapio(m):
        w = m.group(0)
        return 'Menu' if w[0].isupper() else 'menu'
    text, n = p_cardapio.subn(fix_cardapio, text)
    track("Falso cognato 'cardápio' -> 'menu'", n)

    # -------------------------------------------------------------
    # 10. Ventilador -> Em leque / Atiçar
    # -------------------------------------------------------------
    fan_map = [
        (re.compile(r'área\s+em\s+forma\s+de\s+ventilador', re.I), 'área em leque'),
        (re.compile(r'se\s+espalha\s+em\s+forma\s+de\s+ventilador', re.I), 'se espalha em leque'),
        (re.compile(r'Ventilador\s+Chamas\s+da\s+Vingança', re.I), 'Atiçar as Chamas da Vingança'),
        (re.compile(r'Ventilador\s+Fome\s+de\s+Chamas', re.I), 'Atiçar a Fome de Chamas'),
        (re.compile(r'Conjunto\s+de\s+ventiladores\s+definitivo', re.I), 'Pacote de Torcedor Definitivo'),
    ]
    for reg, repl in fan_map:
        text, n = reg.subn(repl, text)
        track("Correção 'ventilador' -> 'leque' / 'atiçar'", n)

    # -------------------------------------------------------------
    # 11. Entidades Nominais com Apóstrofo Inglês ('s)
    # -------------------------------------------------------------
    apostrophe_titles = [
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Mão/pé/Ombreiras\s+Armadura\s+Caixa\s+de\s+Seleção', re.I), 'Caixa de Seleção de Armadura de Mão/Pé/Ombro do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Mão,\s*pé\s+e\s+armadura\s+de\s+ombro\s+seleção\s+Caixas', re.I), 'Caixas de Seleção de Armadura de Mão, Pé e Ombro do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Armadura\s+Caixa\s+de\s+Seleção', re.I), 'Caixa de Seleção de Armadura do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Armadura\s+Caixa', re.I), 'Caixa de Armadura do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Arma\s+Caixa\s+de\s+Seleção', re.I), 'Caixa de Seleção de Armas do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Arma\s+Caixa', re.I), 'Caixa de Armas do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Armadura', re.I), 'Armadura do General de Brigada'),
        (re.compile(r'General\s+de\s+Brigada[’\']s\s+Arma', re.I), 'Arma do General de Brigada'),
        (re.compile(r'Comodoro[’\']s\s+Armadura\s+Caixa', re.I), 'Caixa de Armadura do Comodoro'),
        (re.compile(r'Comodoro[’\']s\s+acessório\s+Caixa', re.I), 'Caixa de Acessórios do Comodoro'),
        (re.compile(r'Batalha[’\']s\s+armadura\s+de\s+ombro', re.I), 'Ombreiras de Batalha'),
        (re.compile(r'Batalha[’\']s\s+Manter', re.I), 'Prisão da Batalha'),
        (re.compile(r'Guarda[’\']s\s+Aurora\s+Cerimonial', re.I), 'Traje Cerimonial da Aurora da Guarda'),
        (re.compile(r'Guarda[’\']s\s+congelado\s+Cerimonial', re.I), 'Traje Cerimonial Congelado da Guarda'),
        (re.compile(r'Yasba[’\']s\s+Graça', re.I), 'Graça de Yasba'),
        (re.compile(r'Sunayaka[’\']s\s+Tesouro\s+Câmara', re.I), 'Câmara do Tesouro de Sunayaka'),
        (re.compile(r'Sunayaka[’\']s\s+Treasure\s+Chamber', re.I), 'Câmara do Tesouro de Sunayaka'),
        (re.compile(r'Lodas[’\']\s+Amuleto[s]?\s+III', re.I), 'Amuleto de Lodas III'),
        (re.compile(r'Vidar[’\']s\s+Dignidade', re.I), 'Dignidade de Vidar'),
        (re.compile(r'Bollvig[’\']s\s+Tragédia', re.I), 'Tragédia de Bollvig'),
        (re.compile(r'Fasimedes[’\']\s+Majestade', re.I), 'Majestade de Fasimedes'),
        (re.compile(r'Sigyn[’\']s\s+Inteligência', re.I), 'Inteligência de Sigyn'),
        (re.compile(r'Bóreas[’\']s\s+Encorajamento', re.I), 'Encorajamento de Boreas'),
        (re.compile(r'Thrasymedes[’\']\s+Esperteza', re.I), 'Esperteza de Thrasymedes'),
        (re.compile(r'Khrudgelmir[’\']s\s+Tacitância', re.I), 'Taciturnidade de Khrudgelmir'),
        (re.compile(r'Marchutan[’\']s\s+Ascensão\s+Assistente', re.I), 'Assistente de Ascensão de Marchutan'),
        (re.compile(r'Marchutan[’\']s\s+Amuletos\s+I', re.I), 'Amuletos de Marchutan I'),
        (re.compile(r'imperador[’\']s\s+Lâminas\s+em\s+Corrente', re.I), 'Lâminas em Corrente do Imperador'),
        (re.compile(r'Atreia[’\']s\s+Campeão', re.I), 'Campeão de Atreia'),
        (re.compile(r'Bruxa[’\']s\s+Manto', re.I), 'Manto da Bruxa'),
        (re.compile(r'Phaestos[’\']\s+disco', re.I), 'Disco de Phaestos'),
        (re.compile(r'Phaestos[’\']\s+Disc', re.I), 'Disco de Phaestos'),
        (re.compile(r'Fortuneers[’\']\s+Stigma\s+Caixa\s+de', re.I), 'Caixa de Estigmas dos Fortuneers'),
        (re.compile(r'Comerciantes[’\']\s+Armadura\s+Baú\s+de', re.I), 'Baú de Armadura dos Comerciantes'),
        (re.compile(r'Dragão\s+Negro[’\']s\b', re.I), 'do Dragão Negro'),
        (re.compile(r'Dragão\s+Branco[’\']s\b', re.I), 'do Dragão Branco'),
        (re.compile(r'Apsu[’\']s\s+Assassino', re.I), 'Assassino de Apsu'),
        (re.compile(r'Apsu[’\']s\s+Guerreiro', re.I), 'Guerreiro de Apsu'),
        (re.compile(r'Apsu[’\']s\s+Laphsaran\s+Guerreiro', re.I), 'Guerreiro de Laphsaran de Apsu'),
        (re.compile(r'Apsu[’\']s\s+Recon\s+esquadrão', re.I), 'Esquadrão de Reconhecimento de Apsu'),
        (re.compile(r'Tiamat[’\']s\s+Sombra', re.I), 'Sombra de Tiamat'),
        (re.compile(r'Tiamat[’\']s\s+Guerreiro', re.I), 'Guerreiro de Tiamat'),
        (re.compile(r'Tiamat[’\']s\s+Santuário\s+teste\s+mensagem', re.I), 'Mensagem de Teste do Santuário de Tiamat'),
        (re.compile(r'Senhor\s+dos\s+Dragões[’\']s\s+servo', re.I), 'Servo do Senhor dos Dragões'),
        (re.compile(r'Rukibuki[’\']s\s+Ilusão', re.I), 'Ilusão de Rukibuki'),
        (re.compile(r'Lisandro[’\']s\s+Treinamento\s+Grounds', re.I), 'Campo de Treinamento de Lisandro'),
        (re.compile(r'Granir[’\']s\s+Treinamento\s+Lounds', re.I), 'Campo de Treinamento de Granir'),
        (re.compile(r'Kard[’\']s\s+Acampamento', re.I), 'Acampamento de Kard'),
        (re.compile(r'Manir[’\']s\s+Acampamento', re.I), 'Acampamento de Manir'),
        (re.compile(r'Metamor[’\']s\s+aperto', re.I), 'Aperto de Metamor'),
        (re.compile(r'Raksha[’\']s\s+Cripta', re.I), 'Cripta de Raksha'),
        (re.compile(r'Mahisha[’\']s\s+Ninho', re.I), 'Ninho de Mahisha'),
        (re.compile(r'Beluslan[’\']s\s+Telhado', re.I), 'Telhado de Beluslan'),
        (re.compile(r'Alukina[’\']s\s+Palácio', re.I), 'Palácio de Alukina'),
        (re.compile(r'Notícias\s+do\s+Arbolu[’\']s\s+Refúgio', re.I), 'Notícias do Refúgio de Arbolu'),
        (re.compile(r'\[coleta\]\s*Sora[’\']s\s+Energia\s+Reforço', re.I), '[Coleta] Reforço de Energia de Sora'),
        (re.compile(r'\[Experto\]\s*Armousmith[’\']s\s+a\s+etapa\s+Exame', re.I), '[Especialista] Teste Final de Armeiro'),
        (re.compile(r'Feira[’\']s\s+Pesca\s+Haste', re.I), 'Vara de Pesca de Feira'),
        (re.compile(r'Stephano[’\']s\s+Espada', re.I), 'Espada de Stephano'),
        (re.compile(r'\[Diário\]\s*Skafir[’\']s\s+Ordem', re.I), '[Diário] Ordens de Skafir'),
        (re.compile(r'\[Diário\]\s*Retinoa[’\']s\s+Pedido', re.I), '[Diário] Pedido de Retinoa'),
        (re.compile(r'\[Diário\]\s*Thiamin[’\']s\s+Pedido', re.I), '[Diário] Pedido de Thiamin'),
        (re.compile(r'Derrote\s+Inggison[’\']s\s+Balaur', re.I), 'Derrote os Balaur de Inggison'),
        (re.compile(r'Grendal[’\']s\s+Gountlets', re.I), 'Manoplas de Grendal'),
        (re.compile(r'Kaisinel[’\']s\s+Adjuntante', re.I), 'Ajudante de Kaisinel'),
        (re.compile(r'Éter[’\']s\s+Manter', re.I), 'Prisão de Éter'),
        (re.compile(r'Assistindo\s+olho[’\']s\s+Aperto', re.I), 'Aperto do Olho Vigilante'),
        (re.compile(r'Morati[’\']s\s+fera\s+de\s+estimação\s+Porgus', re.I), 'o porgus de estimação de Morati'),
        (re.compile(r'Beshmundir\s+templo[’\']s', re.I), 'Templo de Beshmundir'),
        (re.compile(r'Tobu[’\']s\s+fera\s+de\s+estimação', re.I), 'animal de estimação de Tobu'),
        (re.compile(r'Vigia[’\']s\s+Colina', re.I), 'Colina do Vigia'),
        (re.compile(r'Dragão[’\']s\s+Brasa', re.I), 'Brasa do Dragão'),
        (re.compile(r'Taloc[’\']s\s+concavidade', re.I), 'Cavidade de Taloc'),
        (re.compile(r'Pixiebelle[’\']s\s+Lingote', re.I), 'Lingote de Pixiebelle'),
        (re.compile(r'Gellmar[’\']s\s+Wardstone', re.I), 'Pedra de Proteção de Gellmar'),
        (re.compile(r'Pauno[’\']s\s+Lanterna\s+comemorativa', re.I), 'Lanterna Comemorativa de Pauno'),
        (re.compile(r'norte\s+de\s+Elim[’\']s\s+Campos', re.I), 'norte dos Campos dos Elims'),
        (re.compile(r'Shugo[’\']s\s+Bits\s+e\s+Bobs', re.I), 'Bugigangas de Shugo'),
        (re.compile(r'Don[’\']t\s+machucar\s+me!', re.I), 'Não me machuque!'),
        (re.compile(r'C[’\']Mooooon\.\s*Vámos!', re.I), 'Vamos lá!'),
        (re.compile(r'você[’\']tenho\s+recebido\s+ajudar\s+do\s+GM', re.I), 'Você recebeu ajuda do GM'),
        (re.compile(r'i[’\']irá\s+ajuda\s+você', re.I), 'eu o ajudarei'),
        (re.compile(r'se\s+você[’\']re\s+ser\s+atacado', re.I), 'se você for atacado'),
        (re.compile(r'lá[’\']s\s+a\s+Alto\s+chance', re.I), 'Há uma alta chance'),
        (re.compile(r'lá[’\']s\s+a\s+magro\s+chance', re.I), 'Há uma pequena chance'),
        (re.compile(r'Lá[’\']s\s+a\s+alto\s+chance', re.I), 'Há uma alta chance'),
        (re.compile(r'Lá[’\']s\s+a\s+magro\s+chance', re.I), 'Há uma pequena chance'),
        (re.compile(r'Você[’\']irá\s+receber\s+a\s+Especial', re.I), 'Você receberá um item especial'),
        (re.compile(r'Você[’\']irá\s+receber', re.I), 'Você receberá'),
    ]
    for reg, repl in apostrophe_titles:
        text, n = reg.subn(repl, text)
        track("Títulos e nomes com genitivo saxão ('s)", n)

    # Specific named entities owner-item reordering:
    # e.g. 'Mastarius’ Arma' -> 'Arma de Mastarius'
    def fix_owner_item(m):
        owner = m.group(1)
        item = m.group(2)
        return f'{item} de {owner}'

    p_owners = re.compile(r'\b(Mastarius|Veille|Triniel|Valetta|Votan|Bakarma|Charna|Yustiel|Sunayaka|Vidar|Fasimedes|Sigyn|Bóreas|Thrasymedes|Khrudgelmir)[’\']s?\s+([A-Za-zÀ-ÿ]+)', re.I)
    text, n = p_owners.subn(fix_owner_item, text)
    track("Inversão de posse 'Owner's Item' -> 'Item de Owner'", n)

    # -------------------------------------------------------------
    # 12. Receitas de Manufatura com Apóstrofo ('s)
    # -------------------------------------------------------------
    recipe_apostrophes = [
        (re.compile(r'Basilisco[’\']s\s+Concha\s+Osso\s+Montantes', re.I), 'Espadões de Osso de Basilisco'),
        (re.compile(r'Fera[’\']s\s+Montantes', re.I), 'Espadões da Fera'),
        (re.compile(r'Lenda[’\']s\s+Espadas', re.I), 'Espadas Lendárias'),
        (re.compile(r'Akairun[’\']s\s+Lanças', re.I), 'Lanças de Akairun'),
        (re.compile(r'Devourer[’\']s\s+Espadas', re.I), 'Espadas do Devorador'),
        (re.compile(r'Dragão\s+Branco[’\']s\s+Adagas', re.I), 'Adagas do Dragão Branco'),
        (re.compile(r'Dragão\s+Branco[’\']s\s+Espadas', re.I), 'Espadas do Dragão Branco'),
        (re.compile(r'Dragão\s+Branco[’\']s\s+Maces', re.I), 'Maças do Dragão Branco'),
        (re.compile(r'Dragão\s+Branco[’\']s\s+Montantes', re.I), 'Espadões do Dragão Branco'),
        (re.compile(r'Dragão\s+Branco[’\']s\s+Lanças', re.I), 'Lanças do Dragão Branco'),
        (re.compile(r'Basilisco[’\']s\s+Concha\s+Osso\s+Calções\s+de\s+Malha', re.I), 'Calções de Malha de Osso de Basilisco'),
        (re.compile(r'Basilisco[’\']s\s+Concha\s+Osso\s+de\s+Grevas\s+de\s+Placa', re.I), 'Grevas de Placa de Osso de Basilisco'),
        (re.compile(r'Eracus[’\']s\s+Ombreiras\s+de\s+Malha', re.I), 'Ombreiras de Malha de Eracus'),
        (re.compile(r'Eracus[’\']s\s+Shoulderplates', re.I), 'Ombreiras de Placa de Eracus'),
        (re.compile(r'Carmesim\s+Guerreiro[’\']s\s+Manoplas\s+de\s+Malha', re.I), 'Manoplas de Malha do Guerreiro Carmesim'),
        (re.compile(r'Carmesim\s+Guerreiro[’\']s\s+de\s+Placas\s+Manoplas', re.I), 'Manoplas de Placa do Guerreiro Carmesim'),
        (re.compile(r'gigantesco\s+Klaw[’\']s\s+Cota\s+de\s+Malha', re.I), 'Cota de Malha do Klaw Gigante'),
        (re.compile(r'gigantesco\s+Klaw[’\']s\s+Peitorais', re.I), 'Peitorais do Klaw Gigante'),
        (re.compile(r'Unfest[’\']s\s+Ombreiras\s+de\s+Malha', re.I), 'Ombreiras de Malha de Unfest'),
        (re.compile(r'Unfest[’\']s\s+Shoulderplates', re.I), 'Ombreiras de Placa de Unfest'),
        (re.compile(r'Akairun[’\']s\s+de\s+Placas\s+Helms', re.I), 'Elmos de Placa de Akairun'),
    ]
    for reg, repl in recipe_apostrophes:
        text, n = reg.subn(repl, text)
        track("Receitas de manufatura com apóstrofo", n)

    # -------------------------------------------------------------
    # 13. Nomes de Legiões Balaur ('Guilda' -> 'Legião')
    # -------------------------------------------------------------
    legion_fixes = [
        (re.compile(r'\bGuilda\s+Indratu\b', re.I), 'Legião Indratu'),
        (re.compile(r'\bGuilda\s+Bakarma\b', re.I), 'Legião Bakarma'),
        (re.compile(r'\bGuilda\s+de\s+Anuhart\b', re.I), 'Legião de Anuhart'),
        (re.compile(r'\bGuilda\s+Anuhart\b', re.I), 'Legião de Anuhart'),
        (re.compile(r'\bGuilda\s+de\s+Bollvig\b', re.I), 'Legião de Bollvig'),
        (re.compile(r'\bGuilda\s+do\s+Céu\s+Vermelho\b', re.I), 'Legião do Céu Vermelho'),
    ]
    for reg, repl in legion_fixes:
        text, n = reg.subn(repl, text)
        track("Legiões Balaur ('Guilda' -> 'Legião')", n)

    # -------------------------------------------------------------
    # 14. Descrições de Quebra-cabeças / Pinturas
    # -------------------------------------------------------------
    puzzle_pattern = re.compile(
        r'(<string>\s*<id>(\d+)</id>\s*<name>STR_CLASSIC_PUZZLE([A-J])_PIECE_DESC</name>\s*<body>)'
        r'(?:A|Um\(a\))\s+([^<]+?)\s+Fragmento\s+de\s+Pintura\.\s*o\(a\)\s+adquirido\s+obra\s+de\s+arte\s+Fragmento\s+pode\s+ser\s+adicionado\s+inferior\.\s*•\s*1\s+inferiormente\.\s*2\s+embaixo\s+Menu\s+Inicial\s*→\s*Livro\s+de\s+Lenda\.\s*\\nClique\s+duas\s+vezes\s+unneeded\s+pintura\s+Fragmentos\s+ou\s+use\s+(?:o\(a\)\s+)?(?:cardápio|menu)\s+no\(a\)\s+Livro\s+de\s+Lenda\s+para\s+desmontar\s+eles\(as\)\s+em\s+Pintura\s+poeira\.'
        r'(</body>)',
        re.DOTALL
    )
    def fix_puzzle_desc(m):
        header = m.group(1)
        name_target = m.group(4).strip()
        footer = m.group(5)
        if 'Tiamat' in name_target:
            pname = 'da Pintura de Tiamat'
        elif 'Brohum' in name_target:
            pname = 'da Pintura de Brohum'
        elif 'Dramata' in name_target:
            pname = 'da Pintura de Dramata'
        elif 'Eltar' in name_target:
            pname = 'da Pintura do Daeva de Eltar'
        elif 'Apheta' in name_target:
            pname = 'da Pintura de Apheta'
        elif 'Laphsaran' in name_target:
            pname = 'da Pintura de Laphsaran'
        elif 'Lumiel' in name_target:
            pname = 'da Pintura de Lumiel'
        elif 'Dokkaebi' in name_target:
            pname = 'da Pintura do Reino Dokkaebi'
        elif 'Tiamaranta' in name_target:
            pname = 'da Pintura de Tiamaranta'
        elif 'Balic' in name_target:
            pname = 'da Pintura do Tesouro Balaur'
        else:
            pname = f'da Pintura de {name_target}'
        
        body = (f'Um Fragmento {pname}. O fragmento de obra de arte obtido pode ser adicionado ao Livro de Lendas '
                f'(Menu Inicial → Livro de Lendas).\\nClique duas vezes em fragmentos de pintura sobressalentes '
                f'ou use o menu no Livro de Lendas para desmontá-los em Poeira de Pintura.')
        return f'{header}{body}{footer}'

    text, n = puzzle_pattern.subn(fix_puzzle_desc, text)
    track("Descrições de Peças de Pintura (Livro de Lendas)", n)

    # -------------------------------------------------------------
    # 15. Verbos e Construções Residuais em Inglês
    # -------------------------------------------------------------
    leaked_english = [
        (re.compile(r'Deals\s+pesado\s+dano\s+para\s+inimigos\s+no\(a\)\s+n\s+vizinhança\s+e\s+paralisa\s+eles\(as\)\.\\nSó\s+pode\s+ser\s+usado\s+no\s+Coliseu\s+do\s+Crisol\.', re.I),
         'Causa dano pesado a inimigos nos arredores e os paralisa.\\nSó pode ser usado no Coliseu do Crisol.'),
        (re.compile(r'De\s+Tahabata\s+habilidade\s+dano\s+decreases\s+por\s+\[%e1\.StatUp\.RemainTime\]\.', re.I),
         'O dano das habilidades de Tahabata diminui por [%e1.StatUp.RemainTime].'),
        (re.compile(r'Adiciona\s+a\s+Arma\s+efeito\s+que\s+deals\s+(\d+)\s+fogo\s+dano\s+para\s+a\s+alvo\s+com\s+5%%?\s+probabilidade\.', re.I),
         r'Adiciona à arma um efeito que causa \1 de dano de fogo ao alvo com 5%% de probabilidade.'),
        (re.compile(r'Você\s+ganho\s+50%%?\s+adicional\s+XP\s+de\s+coleta,\s+Artesanato,\s+e\s+caça\s+criaturas\s+enquanto\s+Verdin[’\']s\s+Amuleto\s+II\s+é?estiver\s+ativo\.', re.I),
         'Você ganha 50%% a mais de EXP por coleta, artesanato e caça enquanto o Amuleto de Verdin II estiver ativo.'),
        (re.compile(r'Você\s+ganho\s+100%%?\s+adicional\s+XP\s+de\s+coleta,\s+Artesanato,\s+e\s+caça\s+criaturas\s+enquanto\s+Verdin[’\']s\s+Amuleto\s+III\s+é?estiver\s+ativo\.', re.I),
         'Você ganha 100%% a mais de EXP por coleta, artesanato e caça enquanto o Amuleto de Verdin III estiver ativo.'),
        (re.compile(r'Você\s+recebe\s+30%%?\s+mais\s+XP\s+de\s+caça,\s+coleta\s+e\s+Artesanato\s+enquanto\s+este\(a\)\s+amuleto[’\']s\s+efeitos\s+último\.', re.I),
         'Você recebe 30%% mais EXP por caça, coleta e artesanato enquanto os efeitos deste amuleto durarem.'),
        (re.compile(r'Você\s+pode\s+trocar\s+eles\(as\)\s+for\s+mais\s+valioso\s+itens\.', re.I),
         'Você pode trocá-los por itens mais valiosos.'),
    ]
    for reg, repl in leaked_english:
        text, n = reg.subn(repl, text)
        track("Frases residuais em inglês nos itens", n)

    return text, mod_count, stats

def main():
    print("=" * 75)
    print("INICIANDO AUDITORIA E REFINAMENTO ROUND 2 — AION CLASSIC 5.0 PT-BR")
    print("=" * 75)

    xml_files = sorted(glob.glob(os.path.join(STRINGS_DIR, "*.xml")))
    print(f"Total de arquivos XML encontrados na pasta strings: {len(xml_files)}\n")

    grand_total = 0
    all_category_stats = {}
    modified_files = []

    for fpath in xml_files:
        fname = os.path.basename(fpath)
        content = read_xml_utf16(fpath)
        new_content, count, file_stats = apply_refinements(content, fname)

        if count > 0:
            # Validate XML parse
            try:
                # Encode matching declaration utf-16
                ET.fromstring(b'\xff\xfe' + new_content.encode('utf-16le'))
            except ET.ParseError as pe:
                print(f"[ERRO DE SINTAXE XML] {fname}: {pe}")
                sys.exit(1)

            # Write updated UTF-16 LE
            write_xml_utf16(fpath, new_content)
            grand_total += count
            modified_files.append((fname, count))
            print(f"✔ [{fname}] -> {count} refinamentos aplicados com sucesso.")
            for cat, c in file_stats.items():
                all_category_stats[cat] = all_category_stats.get(cat, 0) + c
        else:
            print(f"• [{fname}] -> 0 pendências (arquivo já 100% limpo).")

    print("\n" + "=" * 75)
    print("RELATÓRIO CONSOLIDADO DO REFINAMENTO ROUND 2:")
    print("=" * 75)
    print(f"Total geral de strings refinadas: {grand_total}")
    print(f"Total de arquivos aprimorados: {len(modified_files)} de {len(xml_files)}\n")

    print("Estatísticas por Categoria:")
    for cat, c in sorted(all_category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {c}")

    print("\nDetalhamento por Arquivo:")
    for fname, cnt in modified_files:
        print(f"  - {fname}: {cnt}")
    print("=" * 75)

if __name__ == "__main__":
    main()
