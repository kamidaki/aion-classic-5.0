#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Auditoria e Refinamento de Tradução - Round 3 (Deep Lexicographical & Residual Clean-up)
Aion Classic 5.0 PT-BR Localization

Escopo:
1. Eliminação cirúrgica de resíduos e dumps lexicográficos de dicionário:
   - Dumps completos inseridos automaticamente no texto:
     * 'n interior: 1 parte interna. 2 parte interior de um país...' -> 'interior'
     * 'n coral: 1 espécie de pólipo. 2 rochedos formados pelos esqueletos desse pólipo...' -> 'coral'
     * 'saída: a) ato ou efeito de sair. b) lugar por onde se sai. 2 morte...' -> 'Saída'
     * 'n efetivo: soldado ou marujo da ativa...' -> 'Eficaz para demolir...' / 'Eficaz em...'
     * 'n máximo: o ponto mais alto a que pode chegar...' -> 'MP Máximo' / 'Máximo de'
     * 'n volume: 1 tomo' -> 'Volume'
     * 'capital: a) sede de governo' -> 'capital'
     * '1 bonito: a) lindo' -> 'Lindo'
     * '1 fraco: a) débil. b) frágil' -> 'Fraco'
     * '1 precioso: a) valioso' -> 'precioso'
     * '1 orgulhoso: a) vaidoso' -> 'orgulhoso'
     * 'fatal: 1 determinado pelo destino' -> 'Fatal'
     * 'n centro: 1 meio. 2 núcleo' -> 'Centro'
     * 'n radar:...', 'n extrato: 1 resumo', 'n plano: 1 planta', 'n familiar: 1 íntimo'
     * 'n funeral: 1 pompas fúnebres', 'n proletário: membro da classe operária'
     * 'face: a) cara', 'fim: a) termo', 'passeio: a) caminhada...', 'passagem: a) ação...'
     * 'partícula: a) pequena...', 'proteger: a) defender', 'valor: a) preço', 'altitude: a) altura'
     * 'companhia: a) convivência', 'trabalho: a) labor', 'união: a) associação', 'condição: a) estado'
     * 'propósito: a) desígnio', 'processo: a) progresso.', 'n frontal: a) osso frontal'
     * 'Spriit/Sprit: 1 de base Bônus', 'vt provocar: 1 desafiar...', 'urbano: de ou relativo à cidade.'
     * 'puro: a) genuíno Malek', '1 posterior: a) ulterior...', 'Fantástico: 1 muito bom'
2. Correção de acordos de gênero em artigos masculinos:
   - 'A/a Fragmento' -> 'Um/um Fragmento'
   - 'A/a Baú' -> 'Um/um Baú'
   - 'A/a Pacote' -> 'Um/um Pacote'
   - 'A/a Pergaminho' -> 'Um/um Pergaminho'
   - 'A/a Chapéu' -> 'Um/um Chapéu'
   - 'A/a Escudo' -> 'Um/um Escudo'
   - 'A/a Livro' -> 'Um/um Livro'
   - 'A/a recibo' -> 'Um/um recibo'
   - 'A/a Cristal' -> 'Um/um Cristal'
   - 'A/a prisma' -> 'Um/um prisma'
   - 'A/a Bilhete' -> 'Um/um Bilhete'
   - 'a capacete' -> 'o capacete'
   - 'Habilidade a Livro' -> 'Livro de Habilidade'
   - '\\nós [substantivo]' -> '\\nOs [substantivo]'
3. Extirpação de falsos cognatos de 'for' em trocas e recompensas:
   - 'Você pode trocar eles(as) for vários itens de/em [NPC]' -> 'Você pode trocá-los por vários itens com/em [NPC]'
   - 'trocar eles(as) for mais valioso itens' -> 'trocá-los por itens mais valiosos'
   - 'for abertura (a) Baú' -> 'por abrir o Baú'
   - 'for invocação' -> 'para invocar'
   - 'for mulheres' -> 'feminino' / 'for homens' -> 'masculino'
4. Normalização completa de 'parao(à)' e 'parao(a)':
   - Pergaminhos de entrada para instâncias, fendas, câmaras, NPCs
   - Fallback geral para 'para o(a)'
5. Harmonização de 'espaço-andamento' e 'Restante/Agora Asa Câmara':
   - 'Fendas do Espaço-Andamento' -> 'Fendas do Espaço-Tempo'
   - 'espaço-andamento fenda' -> 'fenda espaço-temporal'
   - 'Restante Asa Câmara' -> 'Câmara da Asa Esquerda'
   - 'Agora Asa Câmara' -> 'Câmara da Asa Direita'
6. Mapas do tesouro e cognatos residuais:
   - 'Ele(a) shows [Local]... use o(a) Tesouro mapa.' -> 'Mostra [Local]. Vá até lá e use o Mapa do Tesouro.'
   - 'mentiras dormente' -> 'jaz adormecido'
   - 'Shugopinerk’s Fantoche mostra' -> 'Teatro de Fantoches de Shugopinerk'
7. Verbos e construções literais em inglês:
   - 'Makes Você invencível...', 'gives compliments', 'gives Você...', 'Inflicts pesado dano...'
   - 'deals X água/terra dano...', 'receives todos os o dano...', 'carrying o bomba'
   - 'handing...', 'disassembling...', 'upgrade eles(as)...', 'pancada eles(as) abaixo e então disappears'
   - 'pulsação arterial com Energia...', 'Eles não inspiram confiança...', 'adornam casais felizes...'
   - 'Você ganho X% XP adicional...', 'éestiver ativo'
   - 'posterior. • mais tarde. on later mais tarde. veja você later até logo.' -> 'futuramente'
   - 'higher-nível habilidades' -> 'habilidades de nível superior'
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

def apply_round3_refinements(text, fname):
    mod_count = 0
    stats = {}

    def track(cat, n):
        nonlocal mod_count
        if n > 0:
            mod_count += n
            stats[cat] = stats.get(cat, 0) + n

    # -------------------------------------------------------------
    # 1. Resíduos de Dicionário e Dumps Lexicográficos
    # -------------------------------------------------------------
    dict_rules = [
        # Dump complexo 'posterior... veja você later até logo'
        (re.compile(r'Se\s+novo\s+Perfeito\s+Habilidades\s+são\s+adicionado\s+posterior\.\s*[•~]\s*mais\s+tarde\.\s*on\s+later\s+mais\s+tarde\.\s*veja\s+você\s+later\s+até\s+logo\.\s*for\s+outro\(a\)\s+classes,\s*o\(a\)\s+novo\s+Perfeito\s+Habilidades\s+será\s+adicionado\s+parao\([aà]\)\s+components\.', re.I),
         'Se novas Habilidades Maiores forem adicionadas futuramente para outras classes, as novas Habilidades Maiores serão adicionadas aos componentes.'),
        (re.compile(r'Se\s+higher-nível\s+habilidades\s+for\s+outro\(a\)\s+classes\s+são\s+adicionado\s+posterior\.\s*[•~]\s*mais\s+tarde\.\s*on\s+later\s+mais\s+tarde\.\s*veja\s+você\s+later\s+até\s+logo\.,\s*eles\(as\)\s+irá\s+também\s+ser\s+incluso\s+no\(a\)\s+conteúdo\.', re.I),
         'Se habilidades de nível superior forem adicionadas futuramente para outras classes, elas também serão incluídas no conteúdo.'),
        (re.compile(r'posterior\.\s*[•~]\s*mais\s+tarde\.\s*on\s+later\s+mais\s+tarde\.\s*veja\s+você\s+later\s+até\s+logo\.', re.I),
         'futuramente'),
        (re.compile(r'higher-nível\s+habilidades', re.I), 'habilidades de nível superior'),

        # Dicionários padrão
        (re.compile(r'n\s+interior:\s*1\s+parte\s+interna\.\s*2\s+parte\s+interior\s+de\s+um\s+pa[íi]s\.\s*3\s+assuntos\s+internos\s+de\s+um\s+pa[íi]s\.\s*[•~]\s*1\s+interior', re.I), 'interior'),
        (re.compile(r'n\s+coral:\s*1\s+esp[ée]cie\s+de\s+p[óo]lipo\.\s*2\s+rochedos\s+formados\s+pelos\s+esqueletos\s+desse\s+p[óo]lipo\.\s*3\s+cor\s+vermelho-coral\.\s*[•~]\s*1\s+feito\s+de\s+coral', re.I), 'coral'),
        (re.compile(r'sa[íi]da:\s*a\)\s+ato\s+ou\s+efeito\s+de\s+sair\.\s*b\)\s+lugar\s+por\s+onde\s+se\s+sai\.\s*2\s+morte\.\s*[•~]\s*sair\.\s*2\s+morrer\.', re.I), 'Saída'),
        (re.compile(r'n\s+efetivo:\s*soldado\s+ou\s+marujo\s+da\s+ativa\.\s*[•~]\s*1\s+efetivo\s+(?:for\s+demolishing|para\s+demolir)\s+fortaleza\s+port[õo]es', re.I), 'Eficaz para demolir os portões da fortaleza'),
        (re.compile(r'n\s+efetivo:\s*soldado\s+ou\s+marujo\s+da\s+ativa\.\s*[•~]\s*1\s+efetivo\s+em\s+escurecido\s+ballrooms', re.I), 'Eficaz em salões de baile escurecidos'),
        (re.compile(r'n\s+m[áa]ximo:\s*o\s+ponto\s+mais\s+alto\s+a\s+que\s+pode\s+chegar\s+uma\s+grandeza\s+vari[áa]vel\.\s*[•~]\s*m[áa]ximo\.\s+MP\s+([IVX]+)', re.I), r'MP Máximo \1'),
        (re.compile(r'n\s+m[áa]ximo:\s*o\s+ponto\s+mais\s+alto\s+a\s+que\s+pode\s+chegar\s+uma\s+grandeza\s+vari[áa]vel\.\s*[•~]\s*m[áa]ximo\.\s+de\s+', re.I), 'Máximo de '),
        (re.compile(r'n\s+solit[áa]rio:\s*quem\s+vive\s+na\s+solid[ãa]o\.\s*[•~]\s*1\s+solit[áa]rio\s+Protetor', re.I), 'Protetor Solitário'),
        (re.compile(r'consumir:\s*1\s+esgotar\(-se\)\.\s*2\s+comer\s+automaticamente', re.I), 'Alimentação automática'),
        (re.compile(r'vista:\s*a\)\s+vis[ãa]o\s+ser[áa]\s+alterado\s+para\s+(\d+)', re.I), r'Campo de visão será alterado para \1'),
        (re.compile(r'vista:\s*a\)\s+vis[ãa]o\s+o\(a\)\s+conte[úu]do\.', re.I), 'Veja o conteúdo.'),
        (re.compile(r'progress[ãa]o:\s*a\)\s+avan[çc]o\.', re.I), 'Progressão.'),
        (re.compile(r'v[áa]lido:\s*1\s+que\s+tem\s+valor\s+legal\s+bem\s+fundamentado\s+ou\s+motivado\s+for\s+o\(a\)\s+atual\s+temporada', re.I), 'Válido apenas para a temporada atual'),
        (re.compile(r'capital:\s*a\)\s+sede\s+de\s+governo', re.I), 'capital'),
        (re.compile(r'1\s+bonito:\s*a\)\s+lindo', re.I), 'Lindo'),
        (re.compile(r'1\s+precioso:\s*a\)\s+valioso', re.I), 'precioso'),
        (re.compile(r'1\s+fraco:\s*a\)\s+d[ée]bil\.\s*b\)\s+fr[áa]gil', re.I), 'Fraco'),
        (re.compile(r'1\s+orgulhoso:\s*a\)\s+vaidoso', re.I), 'orgulhoso'),
        (re.compile(r'n\s+centro:\s*1\s+meio\.\s*2\s+n[úu]cleo', re.I), 'Centro'),
        (re.compile(r'n\s+volume:\s*1\s+tomo', re.I), 'Volume'),
        (re.compile(r'n\s+prolet[áa]rio:\s*membro\s+da\s+classe\s+oper[áa]ria\.\s*Swarms', re.I), 'Enxame de Operários'),
        (re.compile(r'n\s+prolet[áa]rio:\s*membro\s+da\s+classe\s+oper[áa]ria\.\s*de\s+Ar[áa]cnida\s+Marrom', re.I), 'Operário Arácnida Marrom'),
        (re.compile(r'N\s+fama:\s*1\s+renome\.\s*2\s+voz\s+p[úu]blica\s+([A-Za-zÀ-ÿ]+)', re.I), r'\1 da Fama'),
        (re.compile(r'n\s+radar:\s*instrumento\s+para\s+determinar\s+a\s+dist[âa]ncia\s+e\s+a\s+dire[çc][ãa]o\s+de\s+objetos\s+n[ãa]o\s+visto', re.I), 'Radar'),
        (re.compile(r'n\s+extrato:\s*1\s+resumo', re.I), 'Extrato'),
        (re.compile(r'n\s+plano:\s*1\s+planta', re.I), 'Plano'),
        (re.compile(r'n\s+amigo:\s*a\)\s+conhecido', re.I), 'amigo'),
        (re.compile(r'n\s+familiar:\s*1\s+[íi]ntimo', re.I), 'familiar'),
        (re.compile(r'n\s+funeral:\s*1\s+pompas\s+f[úu]nebres', re.I), 'funeral'),
        (re.compile(r'n\s+india\s+sati:\s*1\s+costume\s+hindu\s+de\s+queimar\s+a\s+vi[úu]va\s+com\s+os\s+restos\s+mortais\s+do\s+seu\s+marido\.\s*2\s+a\s+vi[úu]va\s+queimada\.', re.I), 'Sati'),
        (re.compile(r'n\s+alguns\s+n\s+poss[íi]vel:\s*aquilo\s+que\s+[ée]\s+poss[íi]vel\.\s*[•~]\s*1\s+poss[íi]vel:\s*a\)\s+que\s+pode\s+acontecer\.\s*b\)\s+realiz[áa]vel:', re.I), 'alguns itens possíveis:'),
        (re.compile(r'n\s+poss[íi]vel:\s*aquilo\s+que\s+[ée]\s+poss[íi]vel\.\s*[•~]\s*1\s+poss[íi]vel:\s*a\)\s+que\s+pode\s+acontecer\.\s*b\)\s+realiz[áa]vel:', re.I), 'possível:'),
        (re.compile(r'fim:\s*a\)\s+termo', re.I), 'Fim'),
        (re.compile(r'FIM:\s*A\)\s*TERMO', re.I), 'Fim'),
        (re.compile(r'face:\s*a\)\s+cara\s+esmagamento\s+([IVX]+)', re.I), r'Esmagamento Facial \1'),
        (re.compile(r'face:\s*a\)\s+cara\s+o\s+julgamento\s+de\s+Destino!', re.I), 'Enfrente o Julgamento do Destino!'),
        (re.compile(r'A\s+Outra\s+face:\s*a\)\s+cara\s+da\s+Mans[ãa]o', re.I), 'A Outra Face da Mansão'),
        (re.compile(r'face:\s*a\)\s+cara', re.I), 'rosto'),
        (re.compile(r'fatal:\s*1\s+determinado\s+pelo\s+destino', re.I), 'Fatal'),
        (re.compile(r'passeio:\s*a\)\s+caminhada\s+a\s+p[ée]\.\s*b\)\s+lugar\s+em\s+que\s+se\s+passeia\s+habitualmente\.\s*c\)\s+cal[çc]ada\.\s*2\s+o\s+andar\s+a\s+p[ée]\.', re.I), 'Caminhada'),
        (re.compile(r'passagem:\s*a\)\s+a[çc][ãa]o\s+ou\s+efeito\s+de\s+passar\s+ou\s+transpor\.\s*b\)\s+tr[âa]nsito\.\s*c\)\s+passadouro', re.I), 'Passagem'),
        (re.compile(r'part[íi]cula:\s*a\)\s+pequena\s+parte\.\s*b\)\s+gram\s+qualquer\s+palavra\s+invari[áa]vel', re.I), 'Partícula'),
        (re.compile(r'proteger:\s*a\)\s+defender', re.I), 'proteger'),
        (re.compile(r'valor:\s*a\)\s+pre[çc]o', re.I), 'valor'),
        (re.compile(r'altitude:\s*a\)\s+altura', re.I), 'altitude'),
        (re.compile(r'COMPANHIA:\s*A\)\s*CONVIV[ÊE]NCIA', re.I), 'Companhia'),
        (re.compile(r'companhia:\s*a\)\s+conviv[êe]ncia', re.I), 'companhia'),
        (re.compile(r'trabalho:\s*a\)\s+labor', re.I), 'Trabalho'),
        (re.compile(r'uni[ãa]o:\s*a\)\s+associa[çc][ãa]o', re.I), 'União'),
        (re.compile(r'condi[çc][ãa]o:\s*a\)\s+estado', re.I), 'condição'),
        (re.compile(r'prop[óo]sito:\s*a\)\s+des[íi]gnio', re.I), 'Propósito'),
        (re.compile(r'processo:\s*a\)\s+progresso\.', re.I), 'processo.'),
        (re.compile(r'n\s+frontal:\s*a\)\s+osso\s+frontal', re.I), 'frontal'),
        (re.compile(r'Spriit:\s*1\s+de\s+base\s+B[ôo]nus', re.I), 'Bônus de Espírito Básico'),
        (re.compile(r'Sprit:\s*1\s+de\s+base\s+B[ôo]nus', re.I), 'Bônus de Espírito Básico'),
        (re.compile(r'vt\s+provocar:\s*1\s+desafiar\s*[•~]\s*sucessivo\s+Provoca[çc][ãa]o\.', re.I), 'Provocação Sucessiva.'),
        (re.compile(r'urbano:\s*de\s+ou\s+relativo\s+[àa]\s+cidade\.', re.I), 'Urbano'),
        (re.compile(r'pote:\s*a\)\s+panela;\s*', re.I), 'Pote: '),
        (re.compile(r'puro:\s*a\)\s+genu[íi]no\s+Malek;', re.I), 'Malek Puro;'),
        (re.compile(r'1\s+posterior:\s*a\)\s+ulterior\.\s*b\)\s+traseiro\.\s*2\s+caudal\.\s*3\s+dorsal\.\s*4\s+bot\s+superior\.', re.I), 'traseiro'),
        (re.compile(r'Fant[áa]stico:\s*1\s+muito\s+bom\b', re.I), 'Fantástico'),
        (re.compile(r'fant[áa]stico:\s*1\s+muito\s+bom\b', re.I), 'fantástico'),
        (re.compile(r'Transforma[çc][ãa]o:\s*1\s+louco\b', re.I), 'Transformação: Louco'),
        (re.compile(r'pron\s+meu\s+n\s*=\s*gracinha\.\s*Estilo', re.I), 'Estilo Gracinha'),
    ]
    for reg, repl in dict_rules:
        text, n = reg.subn(repl, text)
        track("Eliminação de Dumps e Resíduos de Dicionário", n)

    # -------------------------------------------------------------
    # 2. Artigos e Concordância de Gênero
    # -------------------------------------------------------------
    art_map = [
        (re.compile(r'\bA\s+Fragmento\b'), 'Um Fragmento'),
        (re.compile(r'\ba\s+Fragmento\b'), 'um Fragmento'),
        (re.compile(r'\bA\s+Baú\b'), 'Um Baú'),
        (re.compile(r'\ba\s+Baú\b'), 'um Baú'),
        (re.compile(r'\bA\s+Pacote\b'), 'Um Pacote'),
        (re.compile(r'\ba\s+Pacote\b'), 'um Pacote'),
        (re.compile(r'\bA\s+Pergaminho\b'), 'Um Pergaminho'),
        (re.compile(r'\ba\s+Pergaminho\b'), 'um Pergaminho'),
        (re.compile(r'\bA\s+Chapéu\b'), 'Um Chapéu'),
        (re.compile(r'\ba\s+Chapéu\b'), 'um Chapéu'),
        (re.compile(r'\bA\s+Escudo\b'), 'Um Escudo'),
        (re.compile(r'\ba\s+Escudo\b'), 'um Escudo'),
        (re.compile(r'\bA\s+Livro\b'), 'Um Livro'),
        (re.compile(r'\ba\s+Livro\b'), 'um Livro'),
        (re.compile(r'\bA\s+recibo\b'), 'Um recibo'),
        (re.compile(r'\ba\s+recibo\b'), 'um recibo'),
        (re.compile(r'\bA\s+Cristal\b'), 'Um Cristal'),
        (re.compile(r'\ba\s+Cristal\b'), 'um Cristal'),
        (re.compile(r'\bA\s+Bilhete\b'), 'Um Bilhete'),
        (re.compile(r'\ba\s+Bilhete\b'), 'um Bilhete'),
        (re.compile(r'\bA\s+prisma\b'), 'Um prisma'),
        (re.compile(r'\ba\s+prisma\b'), 'um prisma'),
        (re.compile(r'\ba\s+capacete\b'), 'o capacete'),
        (re.compile(r'Habilidade\s+a\s+Livro\s+Caixa\s+de\s+Seleção', re.I), 'Caixa de Seleção de Livro de Habilidade'),
        (re.compile(r'Habilidade\s+a\s+Livro', re.I), 'Livro de Habilidade'),
        (re.compile(r'\\nós\s+(efeitos|fungos|colecionadores|livros|estigmas|itens|comprovantes|danos)\b', re.I),
         lambda m: r'\nOs ' + m.group(1)),
        (re.compile(r'\\nós\s+Asas\b', re.I), r'\nAs Asas'),
    ]
    for reg, repl in art_map:
        text, n = reg.subn(repl, text)
        track("Artigos e Concordância de Gênero (Um Baú/Pacote/Fragmento)", n)

    # -------------------------------------------------------------
    # 3. Falso Cognato 'for' em Trocas e Recompensas
    # -------------------------------------------------------------
    for_map = [
        (re.compile(r'Você\s+pode\s+trocar\s+eles\(as\)\s+for\s+vários\s+itens\s+de\s+([A-Za-zÀ-ÿ]+)', re.I),
         r'Você pode trocá-los por vários itens com \1'),
        (re.compile(r'Você\s+pode\s+trocar\s+eles\(as\)\s+for\s+vários\s+itens\s+em\s+([A-Za-zÀ-ÿ\s]+)', re.I),
         r'Você pode trocá-los por vários itens em \1'),
        (re.compile(r'trocar\s+eles\(as\)\s+for\s+vários\s+Recompensa\s+de\s+([A-Za-zÀ-ÿ]+)', re.I),
         r'trocá-los por várias recompensas com \1'),
        (re.compile(r'trocar\s+eles\(as\)\s+for\s+mais\s+valioso\s+itens', re.I),
         'trocá-los por itens mais valiosos'),
        (re.compile(r'trocar\s+eles\(as\)\s+com\s+o\(a\)\s+Dourado\s+Vento\s+Shugo', re.I),
         'trocá-los com o Shugo do Vento Dourado'),
        (re.compile(r'for\s+abertura\s+(?:a\s+)?Baú\s+do\s+Tesouro', re.I),
         'por abrir o Baú do Tesouro'),
        (re.compile(r'\bfor\s+abertura\b', re.I), 'por abrir'),
        (re.compile(r'\bfor\s+invocação\b', re.I), 'para invocar'),
        (re.compile(r'for\s+a\s+doce\s+Recompensa', re.I), 'por uma doce recompensa'),
        (re.compile(r'for\s+a\s+bem-sorte\s+presente', re.I), 'por um presente da sorte'),
        (re.compile(r'for\s+a\s+presente\b', re.I), 'por um presente'),
        (re.compile(r'\bfor\s+mulheres\b', re.I), 'feminino'),
        (re.compile(r'\bfor\s+homens\b', re.I), 'masculino'),
        (re.compile(r'\bfor\s+outro\(a\)\s+classes\b', re.I), 'para outras classes'),
    ]
    for reg, repl in for_map:
        text, n = reg.subn(repl, text)
        track("Falso Cognato 'for' em Trocas e Recompensas", n)

    # -------------------------------------------------------------
    # 4. 'parao(à)' e 'parao(a)'
    # -------------------------------------------------------------
    parao_map = [
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Crisol\s+desafio', re.I),
         'Pergaminho de Entrada para o Desafio do Crisol'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Ardente\s+sangue\s+Fortaleza', re.I),
         'Pergaminho de Entrada para a Fortaleza do Sangue Ardente'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+CAMPO\s+DE\s+TREINAMENTO\s+DE\s+NOCHSANA', re.I),
         'Pergaminho de Entrada para o Campo de Treinamento de Nochsana'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Chantra\s+de\s+Dredgion', re.I),
         'Pergaminho de Entrada para o Dredgion de Chantra'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Esoterrace', re.I),
         'Pergaminho de Entrada para Esoterrace'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Templo\s+do\s+Fogo', re.I),
         'Pergaminho de Entrada para o Templo do Fogo'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Caverna\s+Draupnir', re.I),
         'Pergaminho de Entrada para a Caverna Draupnir'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Tiarkh\s+Teste\s+Laboratório', re.I),
         'Pergaminho de Entrada para o Laboratório de Testes de Tiarkh'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Agora\s+Asa\s+Câmara', re.I),
         'Pergaminho de Entrada para a Câmara da Asa Direita'),
        (re.compile(r'Pergaminho\s+de\s+Entrada\s+parao\([aà]\)\s+Restante\s+Asa\s+Câmara', re.I),
         'Pergaminho de Entrada para a Câmara da Asa Esquerda'),
        (re.compile(r'Caixa\s+de\s+Entrada\s+pergaminhos\s+parao\([aà]\)\s+Instância', re.I),
         'Caixa de Pergaminhos de Entrada para Instâncias'),
        (re.compile(r'passadouro\s+conectado\s+parao\([aà]\)\s+([A-Za-zÀ-ÿ\s]+)\s+Câmara', re.I),
         r'passagem conectada à Câmara de \1'),
        (re.compile(r'fenda\s+conectado\s+parao\([aà]\)\s+Enxofre\s+Árvore\s+Câmara', re.I),
         'fenda conectada à Câmara da Árvore de Enxofre'),
        (re.compile(r'fenda\s+conectado\s+parao\([aà]\)\s+Restante\s+Asa\s+Câmara', re.I),
         'fenda conectada à Câmara da Asa Esquerda'),
        (re.compile(r'fenda\s+conectado\s+parao\([aà]\)\s+Agora\s+Asa\s+Câmara', re.I),
         'fenda conectada à Câmara da Asa Direita'),
        (re.compile(r'fenda\s+conectado\s+parao\([aà]\)\s+([A-Za-zÀ-ÿ\s]+)\s+Câmara', re.I),
         r'fenda conectada à Câmara de \1'),
        (re.compile(r'fenda\s+conectado\s+parao\([aà]\)\s+([A-Za-zÀ-ÿ\s]+)', re.I),
         r'fenda conectada a \1'),
        (re.compile(r'Vestido\s+parao\([aà]\)\s+Vermelho\s+Tapete', re.I),
         'Vestido para o Tapete Vermelho'),
        (re.compile(r'as\s+Recompensa\s+parao\([aà]\)\s+IDRaksha\s+Arma\s+Swap\s+Missão', re.I),
         'como recompensa da Missão de Troca de Armas de Raksha'),
        (re.compile(r'parao\([aà]\)\s+Nuvem\s+Negra\s+Comerciantes', re.I),
         'aos Comerciantes da Nuvem Negra'),
        (re.compile(r'parao\([aà]\)\s+evento\s+NPC', re.I),
         'ao NPC do evento'),
        (re.compile(r'parao\([aà]\)\s+poderoso\s+Mago\s+NPC', re.I),
         'ao poderoso NPC Mago'),
        (re.compile(r'parao\([aà]\)\s+Balic\s+tesouraria\s+Exchanger', re.I),
         'ao Trocador do Tesouro Balaur'),
        (re.compile(r'propriedades\s+parao\([aà]\)\s+gato\s+Purra', re.I),
         'propriedades para o gato Purra'),
        (re.compile(r'disponível\s+parao\([aà]\)\s+personagem\s+que\s+usado\s+o', re.I),
         'disponível para o personagem que usou o'),
        (re.compile(r'inativo\s+movimento\s+parao\([aà]\)\s+movimento', re.I),
         'movimento ocioso para o movimento'),
        (re.compile(r'\bparao\([aà]\)\b', re.I), 'para o(a)'),
    ]
    for reg, repl in parao_map:
        text, n = reg.subn(repl, text)
        track("Normalização de 'parao(à)' e 'parao(a)'", n)

    # -------------------------------------------------------------
    # 5. Espaço-Tempo e Câmaras das Asas
    # -------------------------------------------------------------
    space_wing_map = [
        (re.compile(r'Fendas\s+do\s+Espaço-Andamento', re.I), 'Fendas do Espaço-Tempo'),
        (re.compile(r'espaço-andamento\s+fenda', re.I), 'fenda espaço-temporal'),
        (re.compile(r'espaço-andamento', re.I), 'espaço-tempo'),
        (re.compile(r'Restante\s+Asa\s+Câmara', re.I), 'Câmara da Asa Esquerda'),
        (re.compile(r'Agora\s+Asa\s+Câmara', re.I), 'Câmara da Asa Direita'),
        (re.compile(r'A\s+Fragmento\s+permitindo\s+Você\s+para\s+ativar', re.I),
         'Um Fragmento que permite ativar'),
    ]
    for reg, repl in space_wing_map:
        text, n = reg.subn(repl, text)
        track("Espaço-Tempo e Câmaras das Asas Esquerda/Direita", n)

    # -------------------------------------------------------------
    # 6. Mapas do Tesouro, Dormente e Fantoche
    # -------------------------------------------------------------
    def fix_treasure_map(m):
        loc = m.group(1).strip()
        return f'Mostra {loc}. Vá até lá e use o Mapa do Tesouro.'

    p_tmap = re.compile(r'Ele\(a\)\s+shows\s+([^.]+?)\.\s*fazer\s+Seu\(Sua\)\s+caminho\s+lá\s+e\s+use\s+o\(a\)\s+Tesouro\s+mapa\.', re.I)
    text, n = p_tmap.subn(fix_treasure_map, text)
    track("Mapas do Tesouro ('Ele shows' -> 'Mostra')", n)

    p_dormant = re.compile(r'mentiras\s+dormente', re.I)
    text, n = p_dormant.subn('jaz adormecido', text)
    track("'mentiras dormente' -> 'jaz adormecido'", n)

    p_puppet = re.compile(r'Shugopinerk[’\']s\s+Fantoche\s+mostra\s*\(Nível\s*(\d+)\)', re.I)
    text, n = p_puppet.subn(r'Teatro de Fantoches de Shugopinerk (Fase \1)', text)
    track("Teatro de Fantoches de Shugopinerk", n)

    # -------------------------------------------------------------
    # 7. Verbos e Construções Literais em Inglês
    # -------------------------------------------------------------
    eng_verb_map = [
        (re.compile(r'Makes\s+Você\s+invencível\s+por\s+1\s+minutos', re.I),
         'Torna você invencível por 1 minuto'),
        (re.compile(r'Makes\s+Você\s+invencível\s+por\s+(\d+)\s+minutos', re.I),
         r'Torna você invencível por \1 minutos'),
        (re.compile(r'A\s+Chapéu\s+que\s+makes\s+Você\s+tato\s+como\s+a\s+navio\s+capitão\.', re.I),
         'Um chapéu que faz você se sentir como um capitão de navio.'),
        (re.compile(r'A\s+GM\s+Traje\s+que\s+gives\s+compliments\.', re.I),
         'Um Traje de GM que faz elogios.'),
        (re.compile(r'gives\s+Você\s+longo,\s*curley\s+dois-colorido\s+cabelo', re.I),
         'concede a você cabelo longo, ondulado e bicolor'),
        (re.compile(r'gives\s+Você\s+longo,\s*curley\s+ponytails', re.I),
         'concede a você maria-chiquinhas longas e onduladas'),
        (re.compile(r'O\(a\)\s+Oculto\s+Alto\s+secreto\s+Uniforme\s+gives\s+Você\s+a\s+diferente\s+olhar\s+em\s+batalha\.', re.I),
         'O Uniforme Ultrassecreto concede a você um visual diferenciado em batalha.'),
        (re.compile(r'O\(a\)\s+Oculto\s+Alto\s+secreto\s+Adereço\s+de\s+Cabeça\s+gives\s+Você\s+a\s+diferente\s+olhar\s+em\s+batalha\.', re.I),
         'O Adereço de Cabeça Ultrassecreto concede a você um visual diferenciado em batalha.'),
        (re.compile(r'O\(a\)\s+Gótico\s+Lolita\s+Traje\s+gives\s+Você\s+a\s+diferente\s+olhar\s+em\s+batalha\.', re.I),
         'O Traje Lolita Gótica concede a você um visual diferenciado em batalha.'),
        (re.compile(r'O\(a\)\s+Gótico\s+Lolita\s+Adereço\s+de\s+Cabeça\s+gives\s+Você\s+a\s+diferente\s+olhar\s+em\s+batalha\.', re.I),
         'O Adereço de Cabeça Lolita Gótica concede a você um visual diferenciado em batalha.'),
        (re.compile(r'Este\(a\)\s+é\s+a\s+Pacote\s+que\s+gives\s+Você\s+o\(a\)\s+página\s+claridade\s+de\s+Ataque\.', re.I),
         'Este é um Pacote que concede a você a página Claridade de Ataque.'),
        (re.compile(r'Este\(a\)\s+é\s+a\s+Pacote\s+que\s+gives\s+Você\s+o\(a\)\s+página\s+Sopro\s+do\(a\)\s+Vento\.', re.I),
         'Este é um Pacote que concede a você a página Sopro do Vento.'),
        (re.compile(r'A\s+fofo\s+coelhinho\s+escudo\s+que\s+makes\s+Você\s+tato\s+cofre\.', re.I),
         'Um escudo fofo de coelhinho que faz você se sentir seguro.'),
        (re.compile(r'A\s+Baú\s+que\s+gives\s+Você\s+a\s+variável\s+número\s+de\s+\[Runa\]\s+Pedras\s+de\s+Encantamento\s+quando\s+aberto\.', re.I),
         'Um Baú que concede a você uma quantidade variável de [Runa] Pedras de Encantamento quando aberto.'),
        (re.compile(r'A\s+Arma\s+que\s+makes\s+pron\s*=\s*todo\s+mundo\.\s*tremer\.\.\s*frenziedly\.', re.I),
         'Uma arma que faz todo mundo tremer... freneticamente.'),
        (re.compile(r'A\s+Arma\s+que\s+makes\s+Você\s+ação\s+de\s+andar\s+1\s+fraco:\s*a\)\s+débil\.\s*b\)\s+frágil\s+no\(a\)\s+knees\.\.\s*com\s+gargalhada\.', re.I),
         'Uma arma que faz você fraquejar os joelhos... de tanto rir.'),
        (re.compile(r'Este\(a\)\s+Florete\s+poder\s+finalmente\s+makes\s+Seu\(Sua\)\s+mãe\s+1\s+orgulhoso:\s*a\)\s+vaidoso\s+de\s+Você\.', re.I),
         'Este Florete pode finalmente deixar sua mãe orgulhosa de você.'),
        (re.compile(r'Este\(a\)\s+Espada\s+poder\s+finalmente\s+fazer\s+Seu\(Sua\)\s+mãe\s+1\s+orgulhoso:\s*a\)\s+vaidoso\s+de\s+Você\.', re.I),
         'Esta Espada pode finalmente deixar sua mãe orgulhosa de você.'),
        (re.compile(r'Inflicts\s+pesado\s+dano\s+para\s+próximo\s+inimigos\s+e\s+paralisa\s+eles\(as\)', re.I),
         'Inflige dano pesado a inimigos próximos e os paralisa'),
        (re.compile(r'Inflicts\s+1\s+sério\s+dano\s+posto\s+próximo\s+inimigos\s+e\s+paralisa\s+eles\(as\)', re.I),
         'Inflige dano severo a inimigos próximos e os paralisa'),
        (re.compile(r'A\s+Haramel\s+habilidade\.\s*Inflicts\s+f[íi]sico\s+dano\s+posto\s+próximo\s+inimigos\s+e\s+atordoamentos\s+eles\(as\)\.', re.I),
         'Habilidade de Haramel. Inflige dano físico a inimigos próximos e os atordoa.'),
        (re.compile(r'Templo\s+do\s+Fogo\s+habilidade\.\s*Inflicts\s+f[íi]sico\s+dano\s+posto\s+próximo\s+inimigos\s+e\s+atordoamentos\s+eles\(as\)\.', re.I),
         'Habilidade do Templo do Fogo. Inflige dano físico a inimigos próximos e os atordoa.'),
        (re.compile(r'Inflicts\s+(\d+)\s+pontos\s+de\s+(veneno|sangramento|fogo|água|terra|Vento)\s+dano', re.I),
         r'Inflige \1 pontos de dano de \2'),
        (re.compile(r'Inflicts\s+([0-9,]+)\s+fogo\s+dano\s+para\s+inimigos', re.I),
         r'Inflige \1 de dano de fogo a inimigos'),
        (re.compile(r'Inflicts\s+água\s+dano\s+em\s+um\s+alvo\s+1\s+dentro\s+15m\s+e\s+absorve\s+(\d+)%%?\s+do\(a\)\s+dano\s+as\s+HP\s+e\s+MP\.', re.I),
         r'Inflige dano de água a um alvo em um raio de 15m e absorve \1% do dano como HP e MP.'),
        (re.compile(r'Seu\(Sua\)\s+Arma\s+inflicts\s+([0-9,]+)\s+(fogo|água|terra|Vento)\s+dano\s+com\s+(\d+(?:\.\d+)?%%?)\s+probabilidade\.\s*aumenta\s+golpe\s+probabilidade\.', re.I),
         r'Sua arma inflige \1 de dano de \2 com \3 de probabilidade. Aumenta a probabilidade de acerto.'),
        (re.compile(r'Adiciona\s+a\s+Arma\s+efeito\s+que\s+deals\s+(\d+)\s+(água|terra|Vento|fogo)\s+dano\s+para\s+a\s+alvo\s+com\s+a?\s*(\d+(?:\.\d+)?%%?)\s+probabilidade', re.I),
         r'Adiciona à arma um efeito que causa \1 de dano de \2 ao alvo com \3 de probabilidade'),
        (re.compile(r'A\s+prisma\s+contendo\s+a\s+Pluma\s+Pique\.\s*Quando\s+usado,\s*ele\(a\)\s+invoca\s+a\s+Pluma\s+que\s+deals\s+f[íi]sico\s+dano\s+para\s+inimigos\s+1\s+dentro\s+25m\.', re.I),
         'Um prisma contendo uma Pena Perfurante. Quando usado, invoca uma Pena que causa dano físico a inimigos em um raio de 25m.'),
        (re.compile(r'o\s+Espírito\s+receives\s+todos\s+os\s+o\s+dano\s+em\s+lugar\s+do\s+conjurador', re.I),
         'o espírito recebe todo o dano no lugar do conjurador'),
        (re.compile(r'você\s+está\s+carrying\s+o\s+bomba', re.I),
         'você está carregando a bomba'),
        (re.compile(r'handing\s+1\s+excedente\s+a\s+sangue\s+drana\s+produto', re.I),
         'entregar 1 produto excedente de drana de sangue'),
        (re.compile(r'disassembling\s+eles\(as\)\s+com\s+Martelo\s+de\s+Siel', re.I),
         'desmontá-los com o Martelo de Siel'),
        (re.compile(r'Dismantling\s+Fábula\s+Equipamento\s+com\s+Martelo\s+de\s+Siel', re.I),
         'Desmontar Equipamento Mítico com o Martelo de Siel'),
        (re.compile(r'upgrade\s+eles\(as\)\s+para\s+a\s+higher\s+item\s+posto\s+em\s+Bigorna\s+de\s+Siel', re.I),
         'aprimorá-los para um item superior na Bigorna de Siel'),
        (re.compile(r'pancada\s+eles\(as\)\s+abaixo\s+e\s+então\s+disappears', re.I),
         'derruba os inimigos e depois desaparece'),
        (re.compile(r'pulsação\s+arterial\s+com\s+Energia', re.I),
         'pulsam com energia'),
        (re.compile(r'Eles\(as\)\s+don[’\']t\s+inspirar\s+confiança', re.I),
         'Eles não inspiram confiança'),
        (re.compile(r'Eles\(as\)\s+adornar\s+feliz\s+nupcial\s+couples', re.I),
         'Elas adornam casais felizes'),
        (re.compile(r'Tomada\s+ele\(a\)\s+para\s+a\s+fóssil\s+comerciante', re.I),
         'Leve-o ao comerciante de fósseis'),
        (re.compile(r'rotação\s+eles\(as\)\s+em\s+para\s+Choirunerk,\s*Asmodians\s+para\s+Choichoirinerk', re.I),
         'entregam a Choirunerk, Asmodianos a Choichoirinerk'),
        (re.compile(r'libertar\s+a\s+certo\s+número\s+de\s+eles\(as\)\s+parao\([aà]\)\s+Balic\s+tesouraria\s+Exchanger', re.I),
         'entregar uma certa quantidade ao Trocador do Tesouro Balaur'),
        (re.compile(r'Você\s+ganho\s+(\d+)%%?\s+XP\s+adicional\s+de\s+caça,\s+coleta\s+e\s+criação\s+enquanto\s+este\(a\)\s+efeito\s+é?estiver\s+ativo', re.I),
         r'Você ganha \1%% de EXP adicional em caça, coleta e criação enquanto este efeito estiver ativo'),
        (re.compile(r'Você\s+ganho\s+(\d+)%%?\s+XP\s+adicional', re.I),
         r'Você ganha \1%% de EXP adicional'),
        (re.compile(r'éestiver\s+ativo', re.I), 'estiver ativo'),
        (re.compile(r'Ao\s+abrir,\s*você\s+pode\s+receber\s+um\(a\)\s+variável\s+número\s+de\s+pedras\s+de\s+encantamento\.', re.I),
         'Ao abrir, você pode receber uma quantidade variável de pedras de encantamento.'),
        (re.compile(r'It\s+é\s+disse\s+que\s+Vindachinerk[’\']s\s+Fantasma\s+requires\s+este\(a\)\s+Fragmento\.', re.I),
         'Diz-se que o Fantasma de Vindachinerk necessita deste Fragmento.'),
        (re.compile(r'Cleanses\s+você\s+e\s+seu\s+aliados\s+de\s+especial\s+status\s+efeitos\s+e\s+makes\s+você\s+1\s+capaz\s+para\s+n\s+batalha\s+novamente\.\s*remoção\s+abnormal', re.I),
         'Purifica você e seus aliados de efeitos de estado anormais e torna você capaz de batalhar novamente.'),
    ]
    for reg, repl in eng_verb_map:
        text, n = reg.subn(repl, text)
        track("Verbos e Construções Literais em Inglês", n)

    return text, mod_count, stats

def main():
    print("=" * 80)
    print("AION CLASSIC 5.0 PT-BR - AUDITORIA E REFINAMENTO ROUND 3")
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

        refined_content, count, stats = apply_round3_refinements(raw_content, fname)

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

            # Gravação em UTF-16 LE com BOM
            write_xml_utf16(filepath, refined_content)

    print("\n" + "=" * 80)
    print("RESUMO DA AUDITORIA ROUND 3:")
    print(f"- Total de arquivos analisados: {len(xml_files)}")
    print(f"- Total de arquivos modificados: {files_modified}")
    print(f"- Total de modificações aplicadas: {total_modifications}")
    print("\nDetalhamento por Categoria:")
    for cat, c in sorted(grand_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  * {cat}: {c}")
    print("=" * 80)

if __name__ == '__main__':
    main()
