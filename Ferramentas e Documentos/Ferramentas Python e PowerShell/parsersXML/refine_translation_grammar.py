#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refine_translation_grammar.py

Pipeline Integral de Refinamento Gramatical e Eliminação de Incoerências PT-BR (Aion Classic 5.0):
1. Eliminação de palavras duplicadas consecutivas ("de de", "duras duras", "Siel Siel", "escudo escudo", etc.)
2. Correção de falhas de tradução automática ("rio rio meu" -> "meu", "Porta rio rio segura" -> "Porta do Cofre", "O el el santo" -> "em Sanctum")
3. Correção de "cão raivoso nível" -> "cujo nível de personagem", "nós ranques" -> "nos ranques"
4. Correção de patentes e cargos militares ("idéia de Brigada" -> "General de Brigada", "o idéia do guardião" -> "o General Guardião")
5. Correção de armas traduzidas incorretamente:
   - Staff traduzido como "Funcionários" ou "Pessoal" -> "Cajado"
   - Mace traduzida como "Mulher" -> "Maça"
   - Dagger traduzida como "dias" -> "Adaga"
   - Greatsword traduzida como "GRANDESWORD" -> "Espadão"
6. Correção de equipamentos de PvP/Crucible ("Liga Ouro - do Oficial Tático Marca" -> "Marca do Oficial Tático", "Liga Prata - Tático suboficial's" -> "do Suboficial Tático")
7. Inversão possessiva de patentes ("do Comandante de Batalha Guardião Espada Longa" -> "Espada Longa do Comandante de Batalha Guardião")
8. Ajuste de concordância e posição de adjetivos ("Nobre Manoplas de Placas" -> "Manoplas Nobres de Placa", "Digno Durável Adamantio Espada" -> "Espada de Adamântio Digna e Durável")
9. Correção de termos de combate em magias ("Poderoso cobrança" -> "Investida Poderosa", "Parafuso de chama" -> "Dardo de Chamas") e numerais romanos

Uso:
    python refine_translation_grammar.py --verificar
    python refine_translation_grammar.py --aplicar
"""

import os
import sys
import re
import argparse
from typing import Dict, List, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
STRINGS_DIR = os.path.join(REPO_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Tradução - Português Brasil", "strings")
EN_DIR = os.path.join(REPO_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "Idioma em Inglês", "strings")

STRING_PAT = re.compile(r'(<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>\s*<body>)(.*?)(</body>)', re.S)

def read_file(path: str) -> Tuple[str, str]:
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16le', errors='replace'), 'utf-16le'
    return raw.decode('utf-8', errors='replace'), 'utf-8'

# Repetições sonoras / onomatopeias legítimas
VALID_REPETITIONS = {
    'nyerk', 'shugo', 'ha', 'hah', 'haha', 'hahaha', 'he', 'heh', 'hehe', 'hehehe',
    'hi', 'hihi', 'ho', 'hoho', 'hum', 'humm', 'ai', 'ui', 'ou', 'oh', 'la', 'lá',
    'bum', 'pam', 'bang', 'clic', 'tic', 'tac', 'tique', 'taque', 'bla', 'blá',
    'mim', 'não', 'nao', 'já', 'ja', 'bem', 'muito', 'tão', 'tao', 'quase'
}

DUP_PAT = re.compile(r'\b([A-Za-zÀ-ÖØ-öø-ÿ0-9]+)(?:\s+\1\b)+', re.IGNORECASE)

def clean_duplicate_words(text: str) -> str:
    def repl(m):
        w = m.group(1)
        if w.lower() in VALID_REPETITIONS:
            return m.group(0)
        return w
    res = DUP_PAT.sub(repl, text)
    res = DUP_PAT.sub(repl, res)
    return res

COMMON_REPLACEMENTS = [
    # Máquinas de tradução bizarras
    (r'\brio\s+rio\s+meu\b', 'meu'),
    (r'\bRio\s+rio\s+meu\b', 'Meu'),
    (r'\brio\s+rio\s+minha\b', 'minha'),
    (r'\bRio\s+rio\s+minha\b', 'Minha'),
    (r'\bPorta\s+rio\s+rio\s+segura\b', 'Porta do Cofre'),
    (r'\bporta\s+rio\s+rio\s+segura\b', 'porta do cofre'),
    (r'\bChave\s+rio\s+rio\s+segura\b', 'Chave do Cofre'),
    (r'\bchave\s+rio\s+rio\s+segura\b', 'chave do cofre'),
    (r'\bmais\s+rio\s+rio\s+segura\b', 'mais segura'),
    (r'\brio\s+rio\s+segura\b', 'segura'),
    (r'\brio\s+rio\s+seguro\b', 'seguro'),
    (r'\bRio\s+rio\s+[Gg]anges\b', 'Ganges'),
    (r'\brio\s+rio\s+[Gg]anges\b', 'Ganges'),
    (r'\bRio\s+rio\s+meu\s+lefarista\b', 'Lefarista da Mina'),
    (r'\bO\s+el\s+el\s+santo\b', 'em Sanctum'),
    (r'\bo\s+el\s+el\s+santo\b', 'em Sanctum'),
    (r'\bEl\s+el\s+santo\b', 'Sagrado'),
    (r'\bel\s+el\s+santo\b', 'sagrado'),
    (r'\bAurora\s+polar\s+polar\b', 'Aurora'),
    (r'\baurora\s+polar\s+polar\b', 'aurora'),
    (r'\bAço\s+Aço\b', 'Ancinho de Aço'),
    (r'\baço\s+aço\b', 'Ancinho de Aço'),
    (r'\bdiário\s+de\s+bordo\s+de\s+Ancinho\s+de\s+Aço\b', 'diário de bordo do Ancinho de Aço'),
    (r'\bcapitão\s+de\s+Ancinho\s+de\s+Aço\b', 'capitão do Ancinho de Aço'),
    (r'\bnavio\s+Ancinho\s+de\s+Aço\b', 'navio Ancinho de Aço'),
    (r'\bno\s+Ancinho\s+de\s+Aço\b', 'no Ancinho de Aço'),
    (r'\bconcavidade\'s\s+concavidade\b', 'Fenda de Taloc'),
    
    # "cão raivoso" gerado por erro em "whose character"
    (r'\bcão\s+raivoso\s+nível\s+seja\s+mais\s+de\s+10\s+níveis\s+(?:n\s+)?inferior\s+ao\s+seu\b', 'cujo nível de personagem seja mais de 10 níveis inferior ao seu'),
    (r'\bcão\s+raivoso\s+heroísmo\b', 'cujo heroísmo'),
    (r'\bcão\s+raivoso\s+espírito\b', 'cujo espírito'),

    # General traduzido erroneamente como idéia
    (r'\bVício-\s*idéia\s+de\s+Brigada\b', 'Vice-General de Brigada'),
    (r'\bvício-\s*idéia\s+de\s+brigada\b', 'vice-general de brigada'),
    (r'\b(?:a\s+)?brigada\s+idéia\b', 'o General de Brigada'),
    (r'\bBrigada\s+idéia\b', 'General de Brigada'),
    (r'\bdo\s+idéia\s+de\s+Brigada\b', 'do General de Brigada'),
    (r'\bo\s+idéia\s+do\s+guardião\b', 'o General Guardião'),
    (r'\bCapacete\s+do\s+Guardião\s+idéia\b', 'Elmo do General Guardião'),
    (r'\bEspada\s+do\s+Guardião\s+idéia\b', 'Espada do General Guardião'),
    (r'\bCapacete\s+do\s+idéia\s+Guardião\b', 'Elmo do General Guardião'),
    (r'\bEspada\s+do\s+idéia\s+Guardião\b', 'Espada do General Guardião'),
    (r'\bidéia\s+Guardião\b', 'General Guardião'),
    (r'\bIdéia\s+Guardião\b', 'General Guardião'),
    (r'\bidéia\s+Comerciante\b', 'Comerciante Geral'),
    (r'\bIdéia\s+Comerciante\b', 'Comerciante Geral'),
    (r'\bidéia\s+Elyos\b', 'General Elyos'),
    (r'\bIdéia\s+Elyos\b', 'General Elyos'),
    (r'\bidéia\s+Asmodiano\b', 'General Asmodiano'),
    (r'\bIdéia\s+Asmodiano\b', 'General Asmodiano'),
    (r'\bDranium\s+Batalha\s+idéia\b', 'General de Batalha de Dranium'),

    # Correção de nós -> nos
    (r'\bnós\s+ranques\b', 'nos ranques'),
    (r'\bnós\s+níveis\b', 'nos níveis'),
    (r'\bnós\s+arredores\b', 'nos arredores'),
    (r'\bnós\s+campos\b', 'nos campos'),

    # Preposições duplicadas
    (r'\bde\s+de\b', 'de'),
    (r'\bdo\s+do\b', 'do'),
    (r'\bda\s+da\b', 'da'),
    (r'\bdos\s+dos\b', 'dos'),
    (r'\bdas\s+das\b', 'das'),
    (r'\bno\s+no\b', 'no'),
    (r'\bna\s+na\b', 'na'),
    (r'\bnos\s+nos\b', 'nos'),
    (r'\bnas\s+nas\b', 'nas'),
    (r'\bem\s+em\b', 'em'),
    (r'\bcom\s+com\b', 'com'),
    (r'\bpara\s+para\b', 'para'),
    (r'\bpor\s+por\b', 'por'),
    (r'\be\s+e\b', 'e'),
    (r'\bou\s+ou\b', 'ou'),
    (r'\bque\s+que\b', 'que'),
    (r'\bse\s+se\b', 'se'),
    (r'\bum\s+um\b', 'um'),
    (r'\buma\s+uma\b', 'uma'),
    
    # Facção Nuvem Negra
    (r'\bPreto\s+nuvem\s+Chapéu\b', 'Chapéu da Nuvem Negra'),
    (r'\bPreto\s+nuvem\s+Baú\b', 'Baú da Nuvem Negra'),
    (r'\bPreto\s+nuvem\s+Ilha\b', 'Ilha Nuvem Negra'),
    (r'\bPreto\s+nuvem\b', 'Nuvem Negra'),
    (r'\bpreto\s+nuvem\b', 'nuvem negra'),
]

ITEM_REPLACEMENTS = [
    # Armas com traduções bizarras
    (r'^Naga,\s+a\s+mulher$', 'Maça Naga'),
    (r'^Mulher\s+Akarios$', 'Maça de Akarios'),
    (r'^Mulher\s+Mulher$', 'Maça de Morheim'),
    (r'^Mulher\s+resistente\s+antiga$', 'Maça Resistente Antiga'),
    (r'^Minha\s+mulher$', 'Maça Menor'),
    (r'^A\s+mulher\s+de\s+Cheftain\s+Ulagan$', 'Maça do Chefe Ulagan'),
    (r'^Maa\s+do\s+Monstro\s+Espiritual$', 'Maça do Monstro Espiritual'),
    
    (r'^Eltnen\s+dias$', 'Adaga de Eltnen'),
    (r'^Altgard\s+dias$', 'Adaga de Altgard'),
    (r'^Dagaga\s+Dukaki\s+lascada$', 'Adaga Dukaki Lascada'),
    
    (r'^Eltnen\s+GRANDESWORD$', 'Espadão de Eltnen'),
    (r'^Vengence\s+Grandesword$', 'Espadão da Vingança'),
    (r'^GAIA\s+de\s+Gaia$', 'Espadão de Gaia'),

    (r'^Funcionários\s+do\s+Guardião$', 'Cajado do Guardião'),
    (r'^Funcionários\s+do\s+viajante$', 'Cajado do Viajante'),
    (r'^Funcionários\s+de\s+Verteron$', 'Cajado de Verteron'),
    (r'^Funcionários\s+do\s+cultivador$', 'Cajado do Cultivador'),
    (r'^Funcionários\s+do\s+Explorador$', 'Cajado do Explorador'),
    (r'^Funcionários\s+do\s+santuário$', 'Cajado de Sanctum'),
    (r'^Funcionários\s+do\s+Oráculo$', 'Cajado da Profecia'),
    (r'^Funcionários\s+do\s+Arconte$', 'Cajado do Arconte'),
    (r'^Funcionários\s+Altgard$', 'Cajado de Altgard'),
    (r'^Funcionários\s+de\s+Saqueador$', 'Cajado do Saqueador'),
    (r'^Funcionários\s+de\s+Morheim$', 'Cajado de Morheim'),
    (r'^Funcionários\s+do\s+Pandaemonium$', 'Cajado de Pandaemonium'),
    (r'^Funcionários\s+de\s+Telêmaco$', 'Cajado de Telêmaco'),
    (r'^Funcionários\s+de\s+Trajanus$', 'Cajado de Trajano'),
    (r'^Funcionários\s+do\s+Monstro\s+da\s+Alma$', 'Cajado do Monstro da Alma'),
    (r'^Quer\s+funcionários$', 'Cajado Mau'),
    (r'^Funcionários\s+de\s+Athana', 'Cajado de Athana'),
    (r'^Funcionários\s+do\s+santuário\s+reparados$', 'Cajado de Sanctum Reparado'),
    (r'^Reparou\s+a\s+equipe\s+de\s+batalha$', 'Cajado de Batalha Reparado'),

    (r'^Pessoal\s+de\s+Tecoma\s+durável', 'Cajado de Tecoma Durável'),
    (r'^Pessoal\s+da\s+alma$', 'Cajado da Alma'),
    (r'^Pessoal\s+nebuloso$', 'Cajado Nebuloso'),
    (r'^Pessoal\s+avermelhado$', 'Cajado Avermelhado'),
    (r'^Pessoal\s+odioso$', 'Cajado Odioso'),
    (r'^Pessoal\s+oblato$', 'Cajado Oblato'),
    (r'\bpessoal\s+supremo\s+de\s+Siel\b', 'cajado supremo de Siel'),
    (r'\bPessoal\s+supremo\s+de\s+Siel\b', 'Cajado Supremo de Siel'),
    (r'\bum\s+pessoal\s+imbuído\b', 'um cajado imbuído'),
    (r'^Pessoal\s+de\s+região\s+autónoma\s+da\s+madeira\s+acabado$', 'Cajado de Madeira Acabado'),
    (r'^Projeto:\s*Pessoal\s+de\s+região\s+autónoma\s+da\s+madeira\s+acabada$', 'Projeto: Cajado de Madeira Acabado'),

    # Liga Ouro e Prata (Tac Officer / NCO)
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Marca$', 'Marca do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Marca$', 'Marca do Suboficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Espada$', 'Espada do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Clava$', 'Clava do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Maça$', 'Maça do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Punhal$', 'Punhal do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Punhal\s+de\s+Tático\s+suboficial$', 'Punhal do Suboficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Adaga$', 'Adaga do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Globo$', 'Orbe do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Globo$', 'Orbe do Suboficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Orbe$', 'Orbe do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Grimório$', 'Grimório do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Grimório$', 'Grimório do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Claymore$', 'Espadão do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Claymore$', 'Espadão do Suboficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Espada\s+Grande$', 'Espadão do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Glaive$', 'Alabarda do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Glaive\s+do\s+Tático\s+suboficial$', 'Alabarda do Suboficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Alabarda\s+do\s+Tático\s+suboficial$', 'Alabarda do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Cajado$', 'Cajado do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Cajado\s+do\s+Tático\s+suboficial$', 'Cajado do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Arco$', 'Arco do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Arco$', 'Arco do Suboficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+Escudo$', 'Escudo do Oficial Tático'),
    (r'^Liga\s+Prata\s+-\s+Tático\s+suboficial\'s\s+Escudo$', 'Escudo do Suboficial Tático'),
    
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Manoplas$', 'Manoplas Divinas de Placa do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Placas\s+Grevas$', 'Grevas Divinas de Placa do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Placas\s+Botas$', 'Botas Divinas de Placa do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Couro\s+Sapatos$', 'Sapatos Divinos de Couro do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Tecido\s+Sapatos$', 'Sapatos Divinos de Tecido do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Malha\s+Botas$', 'Botas Divinas de Malha do Oficial Tático'),
    (r'^Liga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\s+divino\s+Malha\s+Manoplas$', 'Manoplas Divinas de Malha do Oficial Tático'),
    
    (r'\bLiga\s+Ouro\s+-\s+do\s+Oficial\s+Tático\b', 'do Oficial Tático'),
    (r'\bLiga\s+Prata\s+-\s+Tático\s+suboficial\'s\b', 'do Suboficial Tático'),
    (r'\bLiga\s+Prata\s+-\s+(?:do\s+)?Tático\s+suboficial\b', 'do Suboficial Tático'),

    # Elementos invertidos
    (r'^Alma\s+Maça$', 'Maça da Alma'),
    (r'^Alma\s+Espada\s+Grande$', 'Espadão da Alma'),
    (r'^Morte\s+Espada\s+Grande$', 'Espadão da Morte'),

    # Materiais antes de tipo de armadura
    (r'\bPlacas\s+Grevas\b', 'Grevas de Placa'),
    (r'\bPlaca\s+Grevas\b', 'Grevas de Placa'),
    (r'\bPlacas\s+Botas\b', 'Botas de Placa'),
    (r'\bPlaca\s+Botas\b', 'Botas de Placa'),
    (r'\bMalha\s+Manoplas\b', 'Manoplas de Malha'),
    (r'\bMalha\s+Calções\b', 'Calções de Malha'),
    (r'\bMalha\s+Botas\b', 'Botas de Malha'),
    (r'\bTecido\s+Calções\b', 'Calções de Tecido'),
    (r'\bTecido\s+Sapatos\b', 'Sapatos de Tecido'),
    (r'\bCouro\s+Sapatos\b', 'Sapatos de Couro'),
    (r'\bCouro\s+Luvas\b', 'Luvas de Couro'),
    (r'\bEspada\s+Grande\b', 'Espadão'),
    
    # Joias
    (r'\b(Brinco|Colar|Anel)\s+joia\b', r'\1 de Joia'),
    (r'\b(Brinco|Colar|Anel)\s+Cristal\b', r'\1 de Cristal'),
    (r'\bNobre\s+Rosa\s+Brinco\s+Quartzo\b', 'Brinco Nobre de Quartzo Rosa'),
]

PATENTE_PAT = re.compile(
    r'^(do\s+(?:Comandante\s+de\s+Batalha\s+(?:Guardião|Arconte)|'
    r'Comandante\s+da\s+Legião\s+Condenada|'
    r'Centurião\s+Guardião|Centurião\s+Arconte|'
    r'Oficial\s+Tático|Suboficial\s+Tático|'
    r'Oficial\s+Guardião|Oficial\s+Arconte|'
    r'Centurião|Comandante|Tribuno|Soldado|General|Guardião|Arconte))\s+'
    r'(.+)$',
    re.IGNORECASE
)

ADJ_MAP = {
    'Nobre': ('Nobres', 'Nobre'),
    'Divino': ('Divinas', 'Divina', 'Divinos', 'Divino'),
    'Brilhante': ('Brilhantes', 'Brilhante'),
    'Glorioso': ('Gloriosas', 'Gloriosa', 'Gloriosos', 'Glorioso'),
    'Antigo': ('Antigas', 'Antiga', 'Antigos', 'Antigo'),
    'Especial': ('Especiais', 'Especial'),
    'Lendário': ('Lendárias', 'Lendária', 'Lendários', 'Lendário'),
    'Mítico': ('Míticas', 'Mítica', 'Míticos', 'Mítico'),
    'Resplandecente': ('Resplandecentes', 'Resplandecente'),
}

PLURAL_FEM_NOUNS = {'Botas', 'Luvas', 'Manoplas', 'Calças', 'Ombreiras', 'Grevas', 'Perneiras', 'Braceletes', 'Cotas'}
PLURAL_MASC_NOUNS = {'Sapatos', 'Calções', 'Brincos', 'Anéis'}
SING_FEM_NOUNS = {'Adaga', 'Maça', 'Orbe', 'Lança', 'Túnica', 'Cota', 'Tiara'}
SING_MASC_NOUNS = {'Cajado', 'Arco', 'Escudo', 'Elmo', 'Capuz', 'Anel', 'Colar', 'Cinto', 'Espadão', 'Grimório'}

# Padrão: "Digno Durável Adamantio Espada" -> "Espada de Adamantio Digna e Durável"
END_NOUN_PAT = re.compile(
    r'^(Nobre|Divino|Digno|Brilhante)\s+(Durável|Forte)\s+([A-Za-zÀ-ÖØ-öø-ÿ]+)\s+('
    r'Cajado|Espada|Adaga|Maça|Arco|Escudo|Orbe|Grimório|Alabarda|Espadão|'
    r'Perneiras|Botas|Luvas|Manoplas|Ombreiras|Grevas|Sapatos|Calções|Cotas|Túnica|Elmo|Capuz|Tiara|Anel|Brinco|Colar|Cinto'
    r')$',
    re.IGNORECASE
)

def refine_item(txt: str) -> str:
    # 1. Regras comuns
    for p, r in COMMON_REPLACEMENTS:
        txt = re.sub(p, r, txt)

    # 2. Regras de itens
    for p, r in ITEM_REPLACEMENTS:
        txt = re.sub(p, r, txt)

    # 3. Substantivo no final com adjetivo e material no meio (ex: "Digno Durável Adamantio Espada")
    m_end = END_NOUN_PAT.match(txt)
    if m_end:
        adj1, adj2, mat, noun = m_end.groups()
        noun_cap = noun.capitalize()
        if noun_cap in PLURAL_FEM_NOUNS:
            adj1_f = 'Nobres' if adj1.lower() == 'nobre' else ('Divinas' if adj1.lower() == 'divino' else ('Dignas' if adj1.lower() == 'digno' else 'Brilhantes'))
            adj2_f = 'Duráveis' if adj2.lower() == 'durável' else 'Fortes'
            txt = f"{noun_cap} de {mat.capitalize()} {adj1_f} e {adj2_f}"
        elif noun_cap in PLURAL_MASC_NOUNS:
            adj1_m = 'Nobres' if adj1.lower() == 'nobre' else ('Divinos' if adj1.lower() == 'divino' else ('Dignos' if adj1.lower() == 'digno' else 'Brilhantes'))
            adj2_m = 'Duráveis' if adj2.lower() == 'durável' else 'Fortes'
            txt = f"{noun_cap} de {mat.capitalize()} {adj1_m} e {adj2_m}"
        elif noun_cap in SING_FEM_NOUNS:
            adj1_f = 'Nobre' if adj1.lower() == 'nobre' else ('Divina' if adj1.lower() == 'divino' else ('Digna' if adj1.lower() == 'digno' else 'Brilhante'))
            adj2_f = 'Durável' if adj2.lower() == 'durável' else 'Forte'
            txt = f"{noun_cap} de {mat.capitalize()} {adj1_f} e {adj2_f}"
        else:
            adj1_m = 'Nobre' if adj1.lower() == 'nobre' else ('Divino' if adj1.lower() == 'divino' else ('Digno' if adj1.lower() == 'digno' else 'Brilhante'))
            adj2_m = 'Durável' if adj2.lower() == 'durável' else 'Forte'
            txt = f"{noun_cap} de {mat.capitalize()} {adj1_m} e {adj2_m}"

    # 4. Inversão de patente no início
    m_pat = PATENTE_PAT.match(txt)
    if m_pat:
        patente = m_pat.group(1).strip()
        resto = m_pat.group(2).strip()
        for p, r in ITEM_REPLACEMENTS:
            resto = re.sub(p, r, resto)
        txt = f"{resto} {patente}"

    # 5. Inversão de adjetivo inicial simples
    words = txt.split(' ', 1)
    if len(words) == 2:
        adj, remainder = words[0], words[1]
        if adj in ADJ_MAP:
            sub_words = remainder.split(' ', 1)
            noun = sub_words[0]
            sub_rest = f" {sub_words[1]}" if len(sub_words) > 1 else ""
            
            if noun in PLURAL_FEM_NOUNS:
                new_adj = ADJ_MAP[adj][0]
                txt = f"{noun} {new_adj}{sub_rest}"
            elif noun in PLURAL_MASC_NOUNS:
                forms = ADJ_MAP[adj]
                new_adj = forms[2] if len(forms) > 2 else forms[0]
                txt = f"{noun} {new_adj}{sub_rest}"
            elif noun in SING_FEM_NOUNS:
                forms = ADJ_MAP[adj]
                new_adj = forms[1] if len(forms) > 1 else forms[0]
                txt = f"{noun} {new_adj}{sub_rest}"
            elif noun in SING_MASC_NOUNS:
                forms = ADJ_MAP[adj]
                new_adj = forms[-1]
                txt = f"{noun} {new_adj}{sub_rest}"

    # 6. Limpeza de duplicatas
    txt = clean_duplicate_words(txt)

    # 7. Espaços múltiplos
    txt = re.sub(r'[ \t]{2,}', ' ', txt).strip()

    # 8. Letra maiúscula inicial
    if txt and txt[0].islower():
        txt = txt[0].upper() + txt[1:]

    return txt


SKILL_REPLACEMENTS = [
    (r'\bPoderoso\s+cobrança\b', 'Investida Poderosa'),
    (r'\bCobranças\s+a\s+uma\s+meta\b', 'Avança contra um alvo'),
    (r'\bAura:\s*El\s+el\s+santo\s+escudo\b', 'Aura: Escudo Sagrado'),
    (r'\bPoderoso\s+golpe\b', 'Golpe Poderoso'),
    (r'\bGrande\s+golpe\b', 'Golpe Pesado'),
    (r'\bPoderoso\s+Empurrão\b', 'Empurrão Poderoso'),
    (r'\bDivina\s+Faísca\b', 'Faísca Divina'),
    (r'\bDivina\s+Vitalidade\b', 'Vitalidade Celestial'),
    (r'\bDivino\s+Golpe\b', 'Golpe Divino'),
    (r'\bDivina\s+Runa\b', 'Runa Divina'),
    (r'\bDivina\s+Grama\b', 'Aprisionamento Divino'),
    (r'\bTerrível\s+uivo\b', 'Uivo Terrível'),
    (r'\bTerrível\s+Uivo\b', 'Uivo Terrível'),
    (r'\bMágico\s+esmagamento\b', 'Esmagamento Mágico'),
    (r'\bMágico\s+Ajuda\b', 'Potencialização Mágica'),
    (r'\bGrande\s+clivagem\b', 'Clivagem Maior'),
    (r'\bGrande\s+erupção\s+de\s+magma\b', 'Grande Erupção de Magma'),
    (r'\bProficiência\s+avançada\s+de\s+armadura\s+de\s+cadeia\b', 'Proficiência Avançada em Armadura de Malha'),
    (r'\bArmadura\s+avançada\s+de\s+placa\b', 'Proficiência Avançada em Armadura de Placa'),
    (r'\bAvançado\s+com\s+dupla\s+mistura\b', 'Empunhadura Dupla Avançada'),
    (r'\bBorda\s+rápida\b', 'Lâmina Rápida'),
    (r'\bParafuso\s+de\s+chama\b', 'Dardo de Chamas'),
    (r'\bBLAST\s+atrasada\b', 'Explosão Retardada'),
    (r'\bescudo\s+queimado\b', 'Escudo Flamejante'),
    (r'\bContador\s+de\s+escudo\b', 'Contra-Ataque com Escudo'),
    (r'\bOnda\s+de\s+terremoto\b', 'Onda Sísmica'),
    (r'\bi\s+I\b', 'I'),
    (r'\bI\.\s+I\b', 'I'),
    (r'\bi\s+II\b', 'II'),
    (r'\bii\s+II\b', 'II'),
    (r'\bi\s+III\b', 'III'),
    (r'\biii\s+III\b', 'III'),
    (r'\biv\s+IV\b', 'IV'),
    (r'\bv\s+V\b', 'V'),
    (r'\bvi\s+VI\b', 'VI'),
    (r'\bIV\s+IV\b', 'IV'),
]

def refine_skill(txt: str) -> str:
    for p, r in COMMON_REPLACEMENTS:
        txt = re.sub(p, r, txt)
    for p, r in SKILL_REPLACEMENTS:
        txt = re.sub(p, r, txt, flags=re.IGNORECASE if not p.startswith(r'\b[ivx]') else 0)
    txt = clean_duplicate_words(txt)
    txt = re.sub(r'[ \t]{2,}', ' ', txt).strip()
    return txt

NPC_REPLACEMENTS = [
    (r'\bFeroz\s+cinza\s+Worg\b', 'Worg Cinzento Feroz'),
    (r'\bFeroz\s+Rynoce\b', 'Rynoce Feroz'),
    (r'\bFeroz\s+mosabre\b', 'Mosabre Feroz'),
    (r'\bFeroz\s+Draco\b', 'Draco Feroz'),
    (r'\bPequeno\s+Arachna\b', 'Arachna Pequena'),
    (r'\bPequeno\s+animalia\b', 'Pequeno Animal'),
    (r'\bCarcaça\s+de\s+animalia\s+semi-roteado\b', 'Carcaça de Animal Semipodre'),
    (r'\bGrande\s+saída\s+do\s+convés\s+de\s+pistola\b', 'Saída Principal do Convés de Canhões'),
    (r'\bEntrada\s+grande\s+no\s+convés\s+de\s+pistola\b', 'Entrada Principal do Convés de Canhões'),
    (r'\bTundra\s+Kisk\s+pessoal\b', 'Kisk Individual de Tundra'),
    (r'\bKisk\s+marinho\s+pessoal\b', 'Kisk Individual Marinho'),
    (r'\bGrande\s+chefe\s+de\s+Tursin\b', 'Grande Chefe Tursin'),
    (r'\bGrande\s+caixa\s+de\s+carga\b', 'Caixa Grande de Carga'),
    (r'\b<Preto\s+nuvem\s+Envoy>\b', '<Emissário da Nuvem Negra>'),
    (r'\b<Preto\s+nuvem\s+espião>\b', '<Espião da Nuvem Negra>'),
    (r'\b<Preto\s+nuvem\s+Mate>\b', '<Imediato da Nuvem Negra>'),
]

def refine_npc(txt: str) -> str:
    for p, r in COMMON_REPLACEMENTS:
        txt = re.sub(p, r, txt)
    for p, r in NPC_REPLACEMENTS:
        txt = re.sub(p, r, txt, flags=re.IGNORECASE)
    txt = clean_duplicate_words(txt)
    txt = re.sub(r'[ \t]{2,}', ' ', txt).strip()
    return txt

def refine_general(txt: str) -> str:
    for p, r in COMMON_REPLACEMENTS:
        txt = re.sub(p, r, txt)
    txt = clean_duplicate_words(txt)
    txt = re.sub(r'[ \t]{2,}', ' ', txt).strip()
    return txt


def get_refine_func_for_file(filename: str):
    fn = filename.lower()
    if 'item' in fn:
        return refine_item
    elif 'skill' in fn:
        return refine_skill
    elif 'monster' in fn or 'npc' in fn:
        return refine_npc
    else:
        return refine_general


def apply_refinements(dry_run: bool = True):
    total_refined = 0
    refined_by_file = {}

    for fname in sorted(os.listdir(STRINGS_DIR)):
        if not fname.endswith('.xml'): continue
        fpath = os.path.join(STRINGS_DIR, fname)
        content, enc = read_file(fpath)
        refine_func = get_refine_func_for_file(fname)
        
        file_count = 0
        new_content_pieces = []
        last_end = 0

        for m in STRING_PAT.finditer(content):
            new_content_pieces.append(content[last_end:m.start()])
            prefix = m.group(1)
            sid = int(m.group(2))
            sname = m.group(3)
            body = m.group(4)
            suffix = m.group(5)

            new_body = refine_func(body)
            if new_body != body:
                total_refined += 1
                file_count += 1
                new_content_pieces.append(f"{prefix}{new_body}{suffix}")
            else:
                new_content_pieces.append(m.group(0))
            last_end = m.end()

        new_content_pieces.append(content[last_end:])
        refined_by_file[fname] = file_count

        if not dry_run and file_count > 0:
            final_content = "".join(new_content_pieces)
            if enc == 'utf-16le':
                with open(fpath, 'wb') as fp:
                    fp.write(b'\xff\xfe' + final_content.encode('utf-16le'))
            else:
                with open(fpath, 'w', encoding='utf-8') as fp:
                    fp.write(final_content)

    mode = "SIMULAÇÃO" if dry_run else "APLICAÇÃO REAL"
    print(f"\n=======================================================")
    print(f"REFINAMENTO INTEGRAL CONCLUÍDO ({mode})")
    print(f"TOTAL DE STRINGS REFINADAS: {total_refined:,}")
    print(f"=======================================================")
    for fn, cnt in refined_by_file.items():
        if cnt > 0:
            print(f"  {fn}: {cnt:,} strings")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pipeline Integral de Refinamento Gramatical PT-BR (Aion Classic 5.0)")
    parser.add_argument("--aplicar", action="store_true", help="Aplica as correções diretamente nos arquivos XML")
    parser.add_argument("--verificar", action="store_true", help="Apenas simula e exibe contagem de alterações")
    args = parser.parse_args()

    dry_run = not args.aplicar
    apply_refinements(dry_run=dry_run)
