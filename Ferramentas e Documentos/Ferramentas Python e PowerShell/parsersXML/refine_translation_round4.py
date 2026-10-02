#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Auditoria e Refinamento de Tradução - Round 4 (Comprehensive Global Polish)
Aion Classic 5.0 PT-BR Localization

Escopo:
1. Normalização massiva de 'Andamento' significando 'Tempo' (892 ocorrências):
   - Casos compostos: 'andamento frio' -> 'tempo de recarga', 'atraso de andamento' -> 'tempo de ataque',
     'tempo de voo do andamento' -> 'tempo de voo', 'Redefinição de andamento' -> 'Redefinição de Tempo de Recarga',
     'Cápsula de andamento' -> 'Cápsula do Tempo', 'Relíquia do andamento' -> 'Relíquia do Tempo',
     'portal do Andamento' -> 'Portal do Tempo', 'Congelado no andamento' -> 'Congelado no Tempo',
     'Senhor(a) do Andamento' -> 'Senhor(a) do Tempo', 'Daeva do andamento' -> 'Daeva do Tempo',
     'espaço e do andamento' -> 'espaço e do tempo', 'andamento de conjuração' -> 'tempo de conjuração',
     'andamento de uso' -> 'tempo de uso', 'não há andamento a perder' -> 'não há tempo a perder', etc.
   - Substituição geral de 'andamento' por 'tempo', preservando estritamente 'em andamento'.
2. Correção de 'Zagueiro' (futebol) para 'Defensor' (99 ocorrências):
   - Itens ('Cristal do Defensor', 'Núcleo do Defensor'), monstros ('Defensor Lepharist', 'Klaw Defensor',
     'Defensor Desertor'), NPCs ('Comandante dos Defensores', 'Centurião Defensor') e habilidades.
3. Padronização de 'Cadinho' -> 'Crisol' e 'Empírio' -> 'Empíreo' (69 ocorrências):
   - 'Coliseu cadinho' -> 'Coliseu do Crisol', 'desafio empírio cadinho' -> 'Desafio do Crisol Empíreo',
     'Insígnias cadinhas' -> 'Insígnias do Crisol', 'Marca cadinho' -> 'Marca do Crisol',
     'Remédio/Poção do cadinho' -> 'Remédio/Poção do Crisol', 'Senhor Empírio' -> 'Senhor Empíreo'.
4. Extirpação de Dumps Lexicais e Resíduos Gramaticais (280 ocorrências):
   - 'Big: .sint. grande' -> 'Grande'
   - '1 legal. 2 legítimo. 3 lícito. 4 válido.' -> 'Gentil / Válido / Legítimo'
   - 'cabeça da cabeça' (headwear) -> 'Adereço de Cabeça'
   - 'massa alimentícia' (folder/pasta) em diálogos e quests -> 'pasta' / 'ração' / 'reduzir a pó'
   - 'ps e pp de encontrar. fundar' -> 'encontrado'
   - 'vt (ps e pp freed) 1 livrar queda' -> 'Queda Livre'
   - '[Título] vt (ps e pp freed) 1 livrar Espírito' -> '[Título] Espírito Liberto'
   - 'goleiro da tocha / do farol' -> 'Guardião da Tocha / do Farol'
   - 'motorista de escravos' -> 'feitor de escravos'
   - 'n poeta cair da noite' (even) -> 'mesmo / até mesmo'
   - 'n joão-ninguém. • pron ninguém.' -> 'Nobody'
   - 'I Am pron possessivo sg' -> 'I Am Yours'
   - 'pron meu n = gracinha.' -> 'Minha Gracinha'
   - 'pron qualquer pessoa indiscriminadamente' -> 'qualquer pessoa'
   - 'são vi elaborar' -> 'tão elaborado'
   - 'para vi Alimentar' -> 'para alimentar'
   - 'Tiamat bestowed ao pron lhe underlings' -> 'que Tiamat concedeu aos seus servos'
   - '[Cartão de Movimento] Manter posto, ele(a)’s Ringing!' -> '[Cartão de Movimento] Aguenta Aí, Está Tocando!'
5. Normalização de 'Tesouro mapa' -> 'Mapa do Tesouro' (76 ocorrências).
6. Inversão sintática em 'Caixa de Seleção' (801 ocorrências):
   - '[Prefix] [Item] Caixa de Seleção' -> '[Prefix] Caixa de Seleção de [Item]'
   - Normalização interna de 'Mão/pé/Perna/Ombreiras Armadura' -> 'Luvas/Calçados/Perneiras/Ombreiras'.
7. Higienização e sanitização de múltiplos BOMs (ex: triple BOM em client_strings_etc.xml).
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
    while data.startswith(b'\xff\xfe'):
        data = data[2:]
    while data.startswith(b'\xfe\xff'):
        data = data[2:]
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
        return data.decode('utf-8', errors='replace').lstrip('\ufeff')
    return data.decode('utf-16le', errors='replace').lstrip('\ufeff')

def write_xml_utf16(filepath, content):
    with open(filepath, 'wb') as f:
        f.write(b'\xff\xfe')
        f.write(content.encode('utf-16le'))

def apply_round4_refinements(text, fname):
    mod_count = 0
    stats = {}

    def track(cat, n):
        nonlocal mod_count
        if n > 0:
            mod_count += n
            stats[cat] = stats.get(cat, 0) + n

    # -------------------------------------------------------------------------
    # 1. Extirpação de "Andamento" significando "Tempo" (preservando "em andamento")
    # -------------------------------------------------------------------------
    andamento_special = [
        (re.compile(r'\bandamento\s+frio\b', re.I), 'tempo de recarga'),
        (re.compile(r'\batraso\s+de\s+andamento\b', re.I), 'tempo de ataque'),
        (re.compile(r'\b[Tt]empo\s+de\s+voo\s+do\s+andamento\b', re.I), 'tempo de voo'),
        (re.compile(r'\b[Rr]edefinição\s+de\s+andamento\b', re.I), 'Redefinição de Tempo de Recarga'),
        (re.compile(r'\b[Rr]einicialização\s+de\s+andamento\b', re.I), 'Redefinição de Tempo de Recarga'),
        (re.compile(r'\bCápsula\s+de\s+andamento\b', re.I), 'Cápsula do Tempo'),
        (re.compile(r'\bRelíquia\s+do\s+andamento\b', re.I), 'Relíquia do Tempo'),
        (re.compile(r'\b[Pp]ortal\s+do\s+Andamento\b', re.I), 'Portal do Tempo'),
        (re.compile(r'\bCongelado\s+no\s+andamento\b', re.I), 'Congelado no Tempo'),
        (re.compile(r'\bDaeva\s+do\s+andamento\b', re.I), 'Daeva do Tempo'),
        (re.compile(r'\bSenhor[a]?\s+do\s+Andamento\b', re.I), 'Senhora do Tempo'),
        (re.compile(r'\bpoder\s+do\s+Andamento\b', re.I), 'poder do Tempo'),
        (re.compile(r'\bPedra\s+de\s+Ativação\s+do\s+Andamento\b', re.I), 'Pedra de Ativação do Tempo'),
        (re.compile(r'\bespaço\s+e\s+(?:do\s+)?andamento\b', re.I), 'espaço e tempo'),
        (re.compile(r'\bandamento\s+e\s+(?:do\s+)?espaço\b', re.I), 'tempo e espaço'),
        (re.compile(r'\bAndamento\s+foi\s+divertido\b', re.I), 'Esse tempo foi divertido'),
        (re.compile(r'\bAndamento\s+de\s+brincadeira\b', re.I), 'Tempo de brincadeira'),
        (re.compile(r'\bandamento\s+de\s+brincadeira\b', re.I), 'tempo de brincadeira'),
        (re.compile(r'\bAndamento\s+de\s+conjuração\b', re.I), 'Tempo de conjuração'),
        (re.compile(r'\bandamento\s+de\s+conjuração\b', re.I), 'tempo de conjuração'),
        (re.compile(r'\bAndamento\s+de\s+descanso\b', re.I), 'Tempo de descanso'),
        (re.compile(r'\bandamento\s+de\s+descanso\b', re.I), 'tempo de descanso'),
        (re.compile(r'\bandamento\s+máximo\s+de\s+vôo\b', re.I), 'tempo máximo de voo'),
        (re.compile(r'\bandamento\s+de\s+uso\b', re.I), 'tempo de uso'),
        (re.compile(r'\bandamento\s+restante\b', re.I), 'tempo restante'),
        (re.compile(r'\bSem\s+limite\s+de\s+andamento\b', re.I), 'Sem limite de tempo'),
        (re.compile(r'\blimite\s+de\s+andamento\b', re.I), 'limite de tempo'),
        (re.compile(r'\bpor\s+um\s+longo\s+andamento\b', re.I), 'por um longo tempo'),
        (re.compile(r'\bpor\s+um\s+certo\s+andamento\b', re.I), 'por um certo tempo'),
        (re.compile(r'\bao\s+longo\s+do\s+andamento\b', re.I), 'ao longo do tempo'),
        (re.compile(r'\bpassar\s+mais\s+andamento\b', re.I), 'passar mais tempo'),
        (re.compile(r'\bcom\s+algum\s+andamento\s+para\b', re.I), 'com algum tempo para'),
        (re.compile(r'\bjá\s+faz\s+um\s+andamento\b', re.I), 'já faz tempo'),
        (re.compile(r'\bsem\s+andamento\b', re.I), 'sem tempo'),
        (re.compile(r'\bficando\s+sem\s+andamento\b', re.I), 'ficando sem tempo'),
        (re.compile(r'\bnão\s+tenho\s+andamento\b', re.I), 'não tenho tempo'),
        (re.compile(r'\bnão\s+há\s+andamento\s+a\s+(?:desperdiçar|perder)\b', re.I), 'não há tempo a perder'),
    ]
    for reg, repl in andamento_special:
        text, n = reg.subn(repl, text)
        track("Andamento -> Tempo (Expressões compostas)", n)

    # Substituição geral de andamento exceto "em andamento" ou "o andamento da"
    def fix_general_andamento(m):
        w = m.group(0)
        return 'Tempo' if w[0].isupper() else 'tempo'

    p_gen_andamento = re.compile(r'(?<!\b[Ee]m\s)(?<!\b[Oo]\s)\b[Aa]ndamentos?\b(?!\s+da\s+(?:obra|construção|pesquisa|missão|quest|operação))')
    text, n = p_gen_andamento.subn(fix_general_andamento, text)
    track("Andamento -> Tempo (Geral preservando 'em andamento')", n)

    # -------------------------------------------------------------------------
    # 2. Correção de "Zagueiro" -> "Defensor"
    # -------------------------------------------------------------------------
    def fix_zagueiro(m):
        w = m.group(0)
        is_upper = w[0].isupper()
        low = w.lower()
        if low == 'zagueiro':
            return 'Defensor' if is_upper else 'defensor'
        elif low == 'zagueiros':
            return 'Defensores' if is_upper else 'defensores'
        elif low == 'zagueira':
            return 'Defensora' if is_upper else 'defensora'
        elif low == 'zagueiras':
            return 'Defensoras' if is_upper else 'defensoras'
        return w

    p_zag = re.compile(r'\bzagueir[oa]s?\b', re.I)
    text, n = p_zag.subn(fix_zagueiro, text)
    track("Zagueiro -> Defensor", n)

    # -------------------------------------------------------------------------
    # 3. Padronização de "Cadinho" -> "Crisol" e "Empírio" -> "Empíreo"
    # -------------------------------------------------------------------------
    cadinho_rules = [
        (re.compile(r'\bColiseu\s+cadinho\b', re.I), 'Coliseu do Crisol'),
        (re.compile(r'\bdesafio\s+emp[íi]ri[oa]\s+cadinho\s+e\s+cadinho\b', re.I), 'Desafio do Crisol Empíreo'),
        (re.compile(r'\bdesafio\s+cadinho\b', re.I), 'Desafio do Crisol'),
        (re.compile(r'\bInfiltrador\s+cadinho\b', re.I), 'Infiltrador do Crisol'),
        (re.compile(r'\bGuarda\s+cadinho\b', re.I), 'Guarda do Crisol'),
        (re.compile(r'\bárbitro\s+cadinho\b', re.I), 'Árbitro do Crisol'),
        (re.compile(r'\bÁrbitro\s+cadinho\b', re.I), 'Árbitro do Crisol'),
        (re.compile(r'\bPortão\s+do\s+abismo\s+cadinho\b', re.I), 'Portão do Crisol Abissal'),
        (re.compile(r'\bInsígnias\s+cadinhas\b', re.I), 'Insígnias do Crisol'),
        (re.compile(r'\bInsígnia\s+cadinho\b', re.I), 'Insígnia do Crisol'),
        (re.compile(r'\bMarca\s+cadinho\s+cintilante\b', re.I), 'Marca do Crisol Cintilante'),
        (re.compile(r'\bMarca\s+cadinho\b', re.I), 'Marca do Crisol'),
        (re.compile(r'\bRemédio\s+de\s+cura\s+HP\s+cadinho\s+divino\b', re.I), 'Remédio de Cura HP do Crisol Divino'),
        (re.compile(r'\bRemédio\s+de\s+cura\s+HP\s+cadinho\b', re.I), 'Remédio de Cura HP do Crisol'),
        (re.compile(r'\bPoção\s+de\s+recuperação\s+cadinho\s+divina\b', re.I), 'Poção de Recuperação do Crisol Divina'),
        (re.compile(r'\bPoção\s+de\s+recuperação\s+cadinho\b', re.I), 'Poção de Recuperação do Crisol'),
        (re.compile(r'\bno\s+cadinho\b', re.I), 'no Crisol'),
        (re.compile(r'\bdo\s+cadinho\b', re.I), 'do Crisol'),
        (re.compile(r'\bo\s+cadinho\b', re.I), 'o Crisol'),
        (re.compile(r'\bum\s+cadinho\b', re.I), 'um Crisol'),
        (re.compile(r'\bcadinho\s+Empíreo\b', re.I), 'Crisol Empíreo'),
        (re.compile(r'\bSenhor\s+Empírio\b', re.I), 'Senhor Empíreo'),
        (re.compile(r'\bSenhora\s+Empíria\b', re.I), 'Senhora Empírea'),
        (re.compile(r'\bsenhora\s+Empíria\b', re.I), 'senhora Empírea'),
        (re.compile(r'\bSenhores\s+Empírios\b', re.I), 'Senhores Empíreos'),
        (re.compile(r'\bempírio\b', re.I), 'empíreo'),
        (re.compile(r'\bEmpírio\b', re.I), 'Empíreo'),
        (re.compile(r'\bempíria\b', re.I), 'empírea'),
        (re.compile(r'\bEmpíria\b', re.I), 'Empírea'),
    ]
    for reg, repl in cadinho_rules:
        text, n = reg.subn(repl, text)
        track("Cadinho -> Crisol / Empírio -> Empíreo", n)

    # -------------------------------------------------------------------------
    # 4. Remoção de Dumps Lexicais Restantes
    # -------------------------------------------------------------------------
    lexical_rules = [
        # Big: .sint. grande
        (re.compile(r'Big:\s*\.sint\.\s*grande', re.I), 'Grande'),
        (re.compile(r'\.sint\.\s*grande', re.I), 'grande'),

        # 1 legal. 2 legítimo. 3 lícito. 4 válido.
        (re.compile(r'1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+da\s+sua\s+parte\s+dizer', re.I),
         'Gentileza da sua parte dizer'),
        (re.compile(r'Isso\s+é\s+muito\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+da\s+sua\s+parte', re.I),
         'Isso é muito gentil da sua parte'),
        (re.compile(r'é\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+da\s+sua\s+parte', re.I),
         'é gentileza da sua parte'),
        (re.compile(r'Maiô\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+NPC', re.I),
         'NPC de Maiôs'),
        (re.compile(r'Caixa\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+de\s+maiô', re.I),
         'Caixa Válida de Maiô'),
        (re.compile(r'\[Masmorra\s+Instlanced\s+Redefinição\s+de\s+(?:andamento|tempo)\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+Pergaminho\]', re.I),
         '[Pergaminho de Redefinição de Tempo de Recarga de Instância]'),
        (re.compile(r'\[Masmorra\s+Instangeon\s+Redefinir\s+Redefinição\s+de\s+(?:Andamento|Tempo)\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\]', re.I),
         '[Pergaminho de Redefinição de Tempo de Recarga de Instância]'),
        (re.compile(r'redefinição\s+de\s+(?:andamento|tempo)\s+de\s+teste\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I),
         'redefinição de tempo de recarga válida'),
        (re.compile(r'reinicialização\s+de\s+(?:andamento|tempo)\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I),
         'redefinição de tempo de recarga válida'),
        (re.compile(r'\[Aliança\]\s+O\s+julgamento\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+de\s+Moras', re.I),
         '[Aliança] O Julgamento Legítimo de Moras'),
        (re.compile(r'Cupom\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.\s+da\s+cabeça\s+da\s+cabeça', re.I),
         'Cupom Válido de Adereço de Cabeça'),
        (re.compile(r'flecha\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I),
         'flecha certeira'),
        (re.compile(r'Batida\s+1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I),
         'Golpe Certeiro'),
        (re.compile(r'1\s+legal\.\s*2\s+legítimo\.\s*3\s+lícito\.\s*4\s+válido\.', re.I),
         'válido'),

        # Cabeça da cabeça -> Adereço de Cabeça
        (re.compile(r'Dimensional\s+da\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça Dimensional'),
        (re.compile(r'Cabeça\s+da\s+cabeça\s+do\s+mago', re.I), 'Adereço de Cabeça do Mago'),
        (re.compile(r'Vingança\s+da\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça da Vingança'),
        (re.compile(r'Tormento\s+da\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça do Tormento'),
        (re.compile(r'Twisp\s+na\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça de Twisp'),
        (re.compile(r'Ancestral\s+da\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça Ancestral'),
        (re.compile(r'Contramestre\s+na\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça do Contramestre'),
        (re.compile(r'Tulipa\s+na\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça de Tulipa'),
        (re.compile(r'Iniciante\s+Lefarista\s+Vermelho\s+na\s+cabeça\s+da\s+cabeça', re.I), 'Adereço de Cabeça do Iniciante Lepharist Vermelho'),
        (re.compile(r'\[Conteúdo\s+especial\]\s+Coração\s+da\s+cabeça\s+da\s+cabeça', re.I), '[Conteúdo Especial] Adereço de Cabeça de Coração'),
        (re.compile(r'\[Conteúdo\s+especial\]\s+Girassol\s+para\s+a\s+cabeça\s+da\s+cabeça', re.I), '[Conteúdo Especial] Adereço de Cabeça de Girassol'),
        (re.compile(r'Cupom\s+fofo\s+da\s+cabeça\s+da\s+cabeça', re.I), 'Cupom de Adereço de Cabeça Fofo'),
        (re.compile(r'\bcabeça\s+da\s+cabeça\b', re.I), 'Adereço de Cabeça'),

        # Massa alimentícia (em contextos de pasta / ração / redução a pó)
        (re.compile(r'massa\s+alimentícia\s+[\'"]pron\s+meu\s+Documentos[\'"]', re.I), "pasta 'Meus Documentos'"),
        (re.compile(r'massa\s+alimentícia\s+UserPreset\s+na\s+massa\s+alimentícia\s+de\s+instalação\s+do\s+Aion', re.I), 'pasta UserPreset na pasta de instalação do Aion'),
        (re.compile(r'massa\s+alimentícia\s+UserMApinting\s+da\s+massa\s+alimentícia\s+de\s+instalação\s+do\s+Aion', re.I), 'pasta UserMapPainting na pasta de instalação do Aion'),
        (re.compile(r'massa\s+alimentícia\s+de\s+instalação\s+do\s+Aion', re.I), 'pasta de instalação do Aion'),
        (re.compile(r'Uma\s+massa\s+alimentícia\s+grossa\s+e\s+brilhante\s+de\s+arquivos\.', re.I), 'Uma pasta grossa e encadernada de arquivos.'),
        (re.compile(r'Eu\s+vou\s+bater\s+em\s+você\s+em\s+uma\s+massa\s+alimentícia!', re.I), 'Eu vou te reduzir a pó!'),
        (re.compile(r'<Daru\s+da\s+massa\s+alimentícia>', re.I), '<Daru da Pastagem>'),
        (re.compile(r'Massa\s+alimentícia\s+de\s+pastagem', re.I), 'Ração de Pastagem'),
        (re.compile(r'que\s+massa\s+alimentícia\s+na\s+Selva\s+de\s+Marayas', re.I), 'que pasta na Selva de Marayas'),

        # ps e pp (past and past participle)
        (re.compile(r'ps\s+e\s+pp\s+de\s+encontrar\.\s*fundar\b', re.I), 'encontrado'),
        (re.compile(r'Pode\s+ser\s+ps\s+e\s+pp\s+de\s+encontrar\.\s*fundar', re.I), 'Pode ser encontrado'),
        (re.compile(r'foi\s+ps\s+e\s+pp\s+de\s+encontrar\.\s*fundar', re.I), 'foi encontrado'),
        (re.compile(r'vt\s+\(ps\s+e\s+pp\s+freed\)\s+1\s+livrar\s+queda', re.I), 'Queda Livre'),
        (re.compile(r'\[Título\]\s+vt\s+\(ps\s+e\s+pp\s+freed\)\s+1\s+livrar\s+Espírito', re.I), '[Título] Espírito Liberto'),
        (re.compile(r'Terma\.vt\s+\(ps\s+e\s+pp\s+freed\)\s+1\s+livrar\s+Terma', re.I), 'Terma. Libertar Terma'),

        # Goleiro / Motorista
        (re.compile(r'goleiro\s+da\s+tocha', re.I), 'Guardião da Tocha'),
        (re.compile(r'goleiro\s+do\s+farol', re.I), 'Guardião do Farol'),
        (re.compile(r'motorista\s+de\s+escravos', re.I), 'feitor de escravos'),

        # n poeta / cair da noite (even)
        (re.compile(r'Revitalises\s+n\s+poeta\s+cair\s+da\s+noite\s+o\(a\)\s+a\s+maior\s+parte\s+uninspired\s+penteado\.', re.I),
         'Revitaliza até mesmo o penteado mais sem graça.'),
        (re.compile(r'sweetens\s+n\s+poeta\s+cair\s+da\s+noite\s+o\(a\)\s+bitterest\s+coração\.', re.I),
         'adoça até mesmo o coração mais amargo.'),
        (re.compile(r'makes\s+romântico\s+copas\s+batida\s+n\s+poeta\s+cair\s+da\s+noite\s+faster\.', re.I),
         'faz corações românticos baterem ainda mais rápido.'),
        (re.compile(r'n\s+poeta\s+cair\s+da\s+noite\s+se\s+você\s+(?:está|for)\s+atacado\b', re.I),
         'mesmo se você for atacado'),
        (re.compile(r'Tornar-se\s+um\(a\)\s+n\s+poeta\s+cair\s+da\s+noite\s+mais\s+poderoso\s+Daeva', re.I),
         'Torne-se um Daeva ainda mais poderoso'),
        (re.compile(r'A\s+Especial\s+bingsu\s+feito\s+n\s+poeta\s+cair\s+da\s+noite\s+mais\s+Especial\s+por\s+o\(a\)\s+adição', re.I),
         'Um Bingsu especial tornado ainda mais especial pela adição'),
        (re.compile(r'\[Evento\]\s+n\s+poeta\s+esplendor\s+Mármore', re.I), '[Evento] Bolinha de Gude Brilhante'),
        (re.compile(r'n\s+poeta\s+esplendor\s+Luz\s+de\s+Equipamento\s+Final', re.I), 'Luz Resplandecente de Equipamento Final'),
        (re.compile(r'n\s+poeta\s+esplendor\s+Seaswept', re.I), 'Resplendor Marítimo'),
        (re.compile(r'N\s+poeta\.’s\s+Acessório\s+de\s+Cabelo', re.I), 'Acessório de Cabelo do Poeta'),

        # Outros resíduos gramaticais e de verbos
        (re.compile(r'Mude\s+no\s+penteado\s+Virar\s+dos\s+anos\s+60,\s+do\s+vídeo\s+[\'"]\s*n\s+joão-ninguém\.\s*[•~]\s*pron\s+ninguém\.\s*[\'"]\.', re.I),
         "Mude para o penteado retrô dos anos 60, inspirado no clipe de 'Nobody'."),
        (re.compile(r'[\'"]I-Am-\s*pron\s+possessivo\s+sg[\'"]\s+Correspondência\s+T-Camisa', re.I), "Camiseta de Casal 'I Am Yours'"),
        (re.compile(r'[\'"]I\s+Am\s+pron\s+possessivo\s+sg[\'"]\s+par[\'’]s\s+Camisa', re.I), "Camiseta de Casal 'I Am Yours'"),
        (re.compile(r'Você\s+têm\s+para\s+fazer\s+a\s+rápido\s+Fone\s+de\s+Ouvido\.\s*[•~]\s*vi\s+telefonar\.\s*chamar\.', re.I),
         'Você precisa fazer uma ligação rápida.'),
        (re.compile(r'A\s+Deslumbrante\s+vestido\s+obtido\s+reta\s+de\s+n\+pron\s*=\s*alguém\.’s\s+n\s+mus\s+fantasia\.', re.I),
         'Um vestido deslumbrante saído diretamente da fantasia de alguém.'),
        (re.compile(r'Pron\s+meu\s+n\s*=\s*gracinha\.\s*(olhar|jogo)', re.I),
         lambda m: 'Visual Minha Gracinha' if 'olhar' in m.group(1).lower() else 'Conjunto Minha Gracinha'),
        (re.compile(r'Este\(a\)\s+Cajado\s+é\s+são\s+vi\s+elaborar\s+ele\(a\)’s\s+1\s+provável\s+para\s+deslumbrar\s+Seu\(Sua\)\s+inimigos\.', re.I),
         'Este cajado é tão elaborado que certamente deslumbrará seus inimigos.'),
        (re.compile(r'Este\(a\)\s+Cajado’s\s+Poder\s+é\s+evidente\s+para\s+pron\s+qualquer\s+pessoa\s+indiscriminadamente\s+que\s+sees\s+ele\(a\)\.', re.I),
         'O poder deste cajado é evidente para qualquer pessoa que o veja.'),
        (re.compile(r'Você\s+pode\s+jogo\s+a\s+total\s+de\s+3\s+itens\s+para\s+vi\s+Alimentar', re.I),
         'Você pode definir um total de 3 itens para alimentar automaticamente'),
        (re.compile(r'Tiamat\s+bestowed\s+ao\s+pron\s+lhe\s+underlings\.', re.I),
         'que Tiamat concedeu aos seus servos.'),
        (re.compile(r'Use\s+o\(a\)\s+mapa\s+no\(a\)\s+localização\s+este\(a\)\s+mapa\s+indicates!\s*I\s+escondeu\s+pron\s+meu\s+Tesouro\s+posto\s+o\(a\)\s+cabeça\s+do\(a\)\s+tallest\s+Dragão', re.I),
         'Use o mapa na localização que este mapa indica! Escondi meu tesouro na cabeça do dragão mais alto'),
        (re.compile(r'%0\s+usado\s+%1\s+e\s+recebido\s+%2\s+contendo\s+25\s+Major\.\s*3\s+mus\s+a\s+clave\s+maior\.\s*[•~]\s*vi\s+formar-se\s+Antigo\s+Coroas\.', re.I),
         '%0 usou %1 e recebeu %2 contendo 25 Coroas Antigas Maiores.'),
        (re.compile(r'\bpron\s+meu\s+Info\s+Aparência\b', re.I), 'Minhas Informações de Aparência'),
        (re.compile(r'\bvt\s+incitar\s+fúria\b', re.I), 'Incitar Fúria'),
        (re.compile(r'\bGolpe\s+VI\s+enfraquecendo\s+VI\b', re.I), 'Golpe Enfraquecedor VI'),
        (re.compile(r'\bSagrado\s+VI\s+Sagrado\s+VI\b', re.I), 'Golpe Sagrado VI'),
        (re.compile(r'\[Cartão\s+de\s+Movimento\]\s+Manter\s+posto,\s+ele\(a\)’s\s+Ringing!', re.I), '[Cartão de Movimento] Aguenta Aí, Está Tocando!'),
        (re.compile(r'\[cartão\s+de\s+Movimento\]\s+Manter\s+posto,\s+ele\(a\)’s\s+Ringing!', re.I), '[Cartão de Movimento] Aguenta Aí, Está Tocando!'),
        (re.compile(r'Este\(a\)\s+elegante\s+pequeno\s+Adaga\s+looks\s+como\s+ele\(a\)’s\s+brotação\.', re.I), 'Esta pequena e elegante adaga parece estar brotando.'),
        (re.compile(r'\btodos\s+os\s+o\b', re.I), 'todo o'),
        (re.compile(r'\btodas\s+as\s+a\b', re.I), 'toda a'),
    ]
    for reg, repl in lexical_rules:
        text, n = reg.subn(repl, text)
        track("Eliminação de Dumps e Resíduos Gramaticais", n)

    # -------------------------------------------------------------------------
    # 5. Correção de "Tesouro mapa" -> "Mapa do Tesouro"
    # -------------------------------------------------------------------------
    tmap_rules = [
        (re.compile(r'(\[[^\]]+\]\s*)?([A-Za-zÀ-ÿ\s]+?)\s+Tesouro\s+mapa\b', re.I),
         lambda m: f"{m.group(1) or ''}Mapa do Tesouro {m.group(2).strip()}".strip()),
        (re.compile(r'\bTesouro\s+mapa\b', re.I), 'Mapa do Tesouro'),
    ]
    for reg, repl in tmap_rules:
        text, n = reg.subn(repl, text)
        track("Tesouro mapa -> Mapa do Tesouro", n)

    # -------------------------------------------------------------------------
    # 6. Harmonização de "Caixa de Seleção" Invertida
    # -------------------------------------------------------------------------
    def fix_selection_box(m):
        full = m.group(1).strip()
        p_box = re.match(r'^((\[[^\]]+\]\s*)?)(.+?)\s+Caixa\s+de\s+Seleção$', full, re.I)
        if p_box:
            tag = p_box.group(1) or ''
            item = p_box.group(3).strip()
            item = re.sub(r'\bPerna\s+Armadura\b', 'Armadura de Pernas', item, flags=re.I)
            item = re.sub(r'\bpé\s+Armadura\b', 'Calçados', item, flags=re.I)
            item = re.sub(r'\bMão\s+Armadura\b', 'Luvas', item, flags=re.I)
            item = re.sub(r'\bOmbreiras\s+Armadura\b', 'Ombreiras', item, flags=re.I)
            item = re.sub(r'\bOmbreiras/Mão/pé\s+Armadura\b', 'Ombreiras/Luvas/Calçados', item, flags=re.I)
            item = re.sub(r'\bArma\b', 'Armas', item, flags=re.I)
            return f'<body>{tag}Caixa de Seleção de {item}</body>'
        return m.group(0)

    p_sel_box = re.compile(r'<body>([^<\n]+?\s+Caixa\s+de\s+Seleção)</body>', re.I)
    text, n = p_sel_box.subn(fix_selection_box, text)
    track("Caixa de Seleção Invertida", n)

    return text, mod_count, stats

def main():
    print("=" * 80)
    print("AION CLASSIC 5.0 PT-BR - AUDITORIA E REFINAMENTO ROUND 4")
    print("=" * 80)

    xml_files = sorted(glob.glob(os.path.join(STRINGS_DIR, '*.xml')))
    if not xml_files:
        print(f"ERRO: Nenhum arquivo XML encontrado em: {STRINGS_DIR}")
        sys.exit(1)

    print(f"Arquivos XML localizados: {len(xml_files)}")
    print(f"Diretório: {STRINGS_DIR}\n")

    total_modifications = 0
    grand_stats = {}
    files_modified = 0

    for filepath in xml_files:
        fname = os.path.basename(filepath)
        raw_content = read_xml_utf16(filepath)

        refined_content, count, stats = apply_round4_refinements(raw_content, fname)

        if count > 0:
            files_modified += 1
            total_modifications += count
            print(f"[*] {fname}: {count} refinamentos aplicados")
            for cat, c in stats.items():
                grand_stats[cat] = grand_stats.get(cat, 0) + c
                print(f"    - {cat}: {c}")

            # Validação XML com UTF-16LE + BOM
            try:
                test_bytes = b'\xff\xfe' + refined_content.encode('utf-16le')
                ET.fromstring(test_bytes)
            except Exception as e:
                print(f"[!] ERRO CRITICO DE PARSE XML em {fname}: {e}")
                sys.exit(1)

            # Gravação em UTF-16 LE com BOM único
            write_xml_utf16(filepath, refined_content)

    print("\n" + "=" * 80)
    print("RESUMO DA AUDITORIA ROUND 4:")
    print(f"- Total de arquivos analisados: {len(xml_files)}")
    print(f"- Total de arquivos modificados: {files_modified}")
    print(f"- Total de modificações aplicadas: {total_modifications}")
    print("\nDetalhamento por Categoria:")
    for cat, c in sorted(grand_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  * {cat}: {c}")
    print("=" * 80)

if __name__ == '__main__':
    main()
