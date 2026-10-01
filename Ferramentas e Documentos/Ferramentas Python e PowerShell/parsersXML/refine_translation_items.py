#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria e Refinamento Cirúrgico de Nomes de Itens (Aion Classic 5.0 PT-BR)
Corrige sistematicamente em client_strings_item.xml, client_strings_item2.xml e client_strings_dic_item.xml:
1. Resíduo de tradução automática 'região autónoma da madeira' -> 'madeira' (120+ itens)
2. Resíduo de armas 'funcionários' (Staff) -> 'Cajado' (50+ itens)
3. Resíduo de patentes 'Idéia de Brigada' (Brigade General) -> 'General de Brigada' (330+ itens)
4. Armadura de Placa: 'de Placas' -> 'de Placa' (1.600+ itens)
5. Baús e Caixas corrompidas com '[X]’Baú de s [ITEM]' -> 'Baú de [ITEM] de [X]' (540+ itens)
6. Artesanato Bálico (Balic Craft) e Dragões com 's e termos corrompidos (Gunslets, Avambraço, etc.)
7. Série Rei Dragão (Dragon King): 'Nobre Sábio do Rei Dragão Espada' -> 'Espada Nobre do Rei Dragão Sábio'
8. Possessivos anglo-saxões ('s e ’s) em equipamentos (Almirante, Tribuno, Centurião, Padmarashka, etc.)
9. Preserva integralmente sintaxe XML e BOM UTF-16 LE
"""

import os
import sys
import re
import argparse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

CLIENT_STRINGS_DIR = "Ferramentas e Documentos/Client e Coletas/Tradução - Português Brasil/strings"

# Dicionário de substituições pontuais críticas
EXACT_ITEM_REPLACEMENTS = {
    # Oficial Tático (exemplo do usuário)
    'STR_PL_SHOULDER_D_N_E1_55D': 'Placas de Ombro Nobres do Oficial Tático',
    'STR_PL_SHOULDER_N_E1_55D': 'Placas de Ombro Nobres do Oficial Tático',
    'STR_CH_SHOES_D_N_E1_55D': 'Botas Nobres de Malha do Oficial Tático',
    'STR_CH_SHOES_N_E1_55D': 'Botas Nobres de Malha do Oficial Tático',
    'STR_SHIELD_N_E1_55H': 'Escudo Nobre de Aço do Oficial Tático',
    'STR_SHIELD_D_N_E1_55H': 'Escudo Nobre de Aço do Oficial Tático',
    'STR_SHIELD_N_E1_55G': 'Escudo Nobre do Oficial Tático',
    'STR_SHIELD_D_N_E1_55G': 'Escudo Nobre do Oficial Tático',
    'STR_SHIELD_N_E1_55F': 'Escudo Nobre de Aço do Oficial Tático',
    'STR_SHIELD_D_N_E1_55F': 'Escudo Nobre de Aço do Oficial Tático',
    'STR_PL_HEAD_N_E1_55D': 'Elmo Nobre de Placa do Oficial Tático',
    'STR_PL_HEAD_D_N_E1_55D': 'Elmo Nobre de Placa do Oficial Tático',
    'STR_RB_TORSO_N_E1_55B': 'Túnica Divina do Oficial Tático',
    'STR_RB_TORSO_D_N_E1_55B': 'Túnica Divina do Oficial Tático',
    
    # Itens corrompidos / bizarros
    'STR_2HSWORD_N_R2_47A': 'Espadão de Takun',
    'STR_CH_SHOES_N_L1_24A': 'Botas de Keruru',
    'STR_PL_SHOES_D_N_R2_18A': 'Botas do Guerreiro Mau',
    'STR_RING_N_E1_Q41855_60A': 'Anel Antigo de Relíquias',
    'STR_skillbook_All_passive_speed_G1': 'Caminhada nas Asas',
    'STR_SKILLBOOK_AS_AS_WINDWALK_G1': 'Passo do Vento I',
    'STR_RMC_DYE_DEEP_PURPLE_01': '[Recompensa da Guilda] Tintura: Púrpura Intenso',
    'STR_UNDEAD_PRINCESS_TORSO_01': 'Vestido da Princesa Karemiwen',
    'STR_BOOK_N_R2_47B': 'Tomo de Koar',
    'STR_CH_GLOVE_N_R2_47A': 'Manoplas de Malha de Koar',
    'STR_SALE_NEWC_OTHER_ITEMS': 'Mercadorias Gerais',
    
    # Koa Log / Junk Antigos
    'STR_GB_SOURCE_TREE_20A': 'Tora de Koa',
    'STR_TREE_N_C_20A': 'Tora de Koa',
    'STR_JUNK_L_S_13D': 'Grilhão Antigo',
    'STR_JUNK_L_S_37A': 'Bandeira Antiga de Krall',
    
    # Baús específicos residuais
    'STR_WRAP_RETURN_LIVECARE_A_E1_60_AMORTBOX_02': '[Evento] Caixa de Seleção de Peitoral/Armadura de Pernas do Almirante',
    'STR_WRAP_RETURN_LIVECARE_L_A_E1_60_AMORTBOX_02': '[Evento] Caixa de Seleção de Peitoral/Armadura de Pernas do Almirante Guardião',
    'STR_WRAP_RETURN_LIVECARE_D_A_E1_60_AMORTBOX_02': '[Evento] Caixa de Seleção de Peitoral/Armadura de Pernas do Almirante do Arconte',
    'STR_WRAP_EVENT_LDF10_DRA_02_DRAKANRA_NAMED_BONUS_BOX': '[Evento] Baú de Varatar',
    'STR_WRAP_WIND_ABYSS_EARRING_PROTO_BOX_E_60': 'Baú de Protótipo de Brinco do Comandante de Batalha',
    'STR_WRAP_WIND_ABYSS_NECKLACE_PROTO_BOX_E_60': 'Baú de Protótipo de Colar do Comandante de Batalha',
    'STR_WRAP_WIND_ABYSS_RING_PROTO_BOX_E_60': 'Baú de Protótipo de Anel do Comandante de Batalha',
    
    # Fighter / Templar de teste
    'STR_PL_TEST_TORSO_15A': 'Peitoral de Placa do Lutador de Nível 15',
    'STR_PL_TEST_TORSO_25A': 'Peitoral de Placa do Lutador de Nível 25',
    'STR_PL_TEST_TORSO_15B': 'Peitoral de Placa do Templário de Nível 15',
    'STR_PL_TEST_TORSO_25B': 'Peitoral de Placa do Templário de Nível 25',
    'STR_PL_TEST_SHOES_15A': 'Botas de Placa do Lutador de Nível 15',
    'STR_PL_TEST_SHOES_25A': 'Botas de Placa do Lutador de Nível 25',
    'STR_PL_TEST_SHOES_15B': 'Botas de Placa do Templário de Nível 15',
    'STR_PL_TEST_SHOES_25B': 'Botas de Placa do Templário de Nível 25',
}

# Mapa de peças de equipamento
EQUIP_MAP = {
    'Baú Armadura': 'Peitoral',
    'Ombreiras Armadura': 'Ombreiras',
    'Mão Armadura': 'Manoplas',
    'Perna Armadura': 'Grevas',
    'pé Armadura': 'Botas',
    'Armadura': 'Armadura',
    'armas': 'Armas',
    'Arma': 'Arma',
    'Asas': 'Asas',
    'Cinto': 'Cinto',
    'Vestimenta': 'Vestimenta',
    'acessórios': 'Acessórios',
    'Florete': 'Florete',
    'Espada Longa': 'Espada Longa',
    'Adaga': 'Adaga',
    'Orbe': 'Orbe',
    'Grimório': 'Grimório',
    'Espadão': 'Espadão',
    'Alabarda': 'Alabarda',
    'Cajado': 'Cajado',
    'Arco': 'Arco',
    'escudo': 'Escudo',
    'escudo de Escamas': 'Escudo de Escamas',
    'Arma Aparência': 'Aparência de Arma',
    'Chama Revólver': 'Revólver da Chama',
    'Encantamento': 'Encantamento',
    'Resgate': 'Resgate',
    'Brinco': 'Brincos',
    'Colar': 'Colar',
    'Anel': 'Anéis',
}

# Regras regex gerais
ITEM_REGEX_RULES = [
    # 1. Região Autónoma da Madeira -> Madeira
    (r'\bde região autónoma da madeira\b', 'de madeira'),
    (r'\bDe região autónoma da madeira\b', 'De madeira'),
    (r'\bde Região autónoma da madeira\b', 'de Madeira'),
    (r'\bDe Região autónoma da madeira\b', 'De Madeira'),
    (r'\bRegião autónoma da madeira\b', 'Madeira'),
    (r'\bregião autónoma da madeira\b', 'madeira'),
    (r'\bRegião Autónoma da Madeira\b', 'Madeira'),
    
    # 2. Funcionários -> Cajado
    (r'\bOferecendo funcionários\b', 'Cajado de Oferenda'),
    (r'\bFuncionário do rei\b', 'Cajado do Rei'),
    (r'\bFuncionários de Treinamento\b', 'Cajado de Treinamento'),
    (r'\bClassificação (\d+) funcionários asmodianos\b', r'Cajado Asmodiano de Grau \1'),
    (r'\bPosto (\d+) funcionários asmodianos\b', r'Cajado Asmodiano de Grau \1'),
    (r'\bClassificação (\d+) funcionários Elyos\b', r'Cajado Elyos de Grau \1'),
    (r'\bPosto (\d+) funcionários Elyos\b', r'Cajado Elyos de Grau \1'),
    (r'\bfuncionários asmodianos\b', 'Cajado Asmodiano'),
    (r'\bfuncionários Elyos\b', 'Cajado Elyos'),
    
    # 3. Idéia -> General
    (r'\bIdéia de Brigada\b', 'General de Brigada'),
    (r'\bidéia de Brigada\b', 'General de Brigada'),
    (r'\bidéia de brigada\b', 'General de Brigada'),
    (r'\bArconte idéia de Brigada\b', 'General de Brigada do Arconte'),
    (r'\bArconte Idéia de Brigada\b', 'General de Brigada do Arconte'),
    (r'\bGuardião idéia\b', 'General Guardião'),
    (r'\bguardião idéia\b', 'General Guardião'),
    (r'\bDemónio idéia\b', 'General Demoníaco'),
    (r'\bDivino idéia\b', 'General Divino'),
    (r'\bIdéia Mercadorias\b', 'Mercadorias Gerais'),
    (r'\bidéia Mercadorias\b', 'Mercadorias Gerais'),
    (r'\bDragão Divindade idéia\b', 'General Divino Dragão'),

    # 4. Armadura de Placa (de Placas -> de Placa)
    (r'\b([Mm]anoplas)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Bb]otas)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Ee]lmo)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Pp]eitoral)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Gg]revas)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Oo]mbreiras)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Cc]onjunto)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Aa]rmadura)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Cc]alças)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Pp]rotetor)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),
    (r'\b([Ee]scudo)\s+de\s+[Pp]lacas\b', r'\1 de Placa'),

    # 5. Artesanato Bálico e Termos Bálicos
    (r'Artesanato Balic:\s*Verdadeiro Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Dragão Branco[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Dragão Negro[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Sábio Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Sombrio Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Estrela Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Celeste Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Celeste Dragão imperador[’\']s\s*', 'Artesanato Bálico: '),
    (r'Artesanato Balic:\s*Chifrudo Dragão[’\']s\s*', 'Artesanato Bálico: '),
    (r'\bHandputards\b', 'Manoplas de Malha'),
    (r'\bGunslets\b', 'Manoplas de Placa'),
    (r'\bPeamplate\b', 'Peitoral de Placa'),
    (r'\bdeve -ser\b', 'Protetores de Ombro'),
    (r'\bombreistas\b', 'Ombreiras de Placa'),
    (r'\bMufferGuards\b', 'Protetores de Ombro'),
    (r'\bBeleches\b', 'Calções'),
    (r'\bSapath\b', 'Sapatos de Tecido'),
    (r'\bLuves\b', 'Luvas de Tecido'),
    (r'\bAvambraço\b', 'Braçadeiras'),
    (r'\bJewelis\b', 'Óculos de Joia'),
    (r'\bMithrils Óculos\b', 'Óculos de Mitril'),
    (r'\bColar Mithricil\b', 'Colar de Mitril'),

    # 6. Possessivos frequentes
    (r'\bAlmirante[’\']s\b', 'do Almirante'),
    (r'\bCenturião[’\']s\b', 'do Centurião'),
    (r'\bTribuno[’\']s\b', 'do Tribuno'),
    (r'\bPadmarashka[’\']s\b', 'de Padmarashka'),
    (r'\bPirata[’\']s\b', 'do Pirata'),
    (r'\bTiamat[’\']s\b', 'de Tiamat'),
    (r'\bKaisinel[’\']s\b', 'de Kaisinel'),
    (r'\bLumiel[’\']s\b', 'de Lumiel'),
    (r'\bSiel[’\']s\b', 'de Siel'),
    (r'\bDaeva[’\']s\b', 'do Daeva'),
    (r'\bDragão[’\']s\b', 'do Dragão'),
]


def fix_chest_patterns(text):
    # 1. Chest Guard do Coliseu
    if "Campeão'Baú de s Malha Guarda" in text:
        return text.replace("Campeão'Baú de s Malha Guarda", "Peitoral de Malha do Campeão do Coliseu").replace("N sublime Coliseu ", "Coliseu Sublime ").replace("Imponente Coliseu ", "Coliseu Imponente ")
    if "Campeão'Baú de s Couro Guarda" in text:
        return text.replace("Campeão'Baú de s Couro Guarda", "Peitoral de Couro do Campeão do Coliseu").replace("N sublime Coliseu ", "Coliseu Sublime ").replace("Imponente Coliseu ", "Coliseu Imponente ")

    # 2. Baús de Ascensão Assistente
    m_asc = re.search(r'\[(Evento|Event)\]\s*([A-Za-zÀ-Úà-ú]+)[’\']Baú de s N(?:vel|ível)\s*(\d+)\s*Ascensão Assistente', text)
    if m_asc:
        tag, entity, lvl = m_asc.group(1), m_asc.group(2), m_asc.group(3)
        prep = 'do' if entity == 'Senhor' else 'de'
        return f"[{tag}] Baú de Auxílio à Ascensão {prep} {entity} (Nível {lvl})"

    m_asc_nv = re.search(r'\[(Evento|Event)\]\s*([A-Za-zÀ-Úà-ú]+)[’\']Baú de s Ascensão Assistente\s*\(nv\.\s*(\d+)\)', text)
    if m_asc_nv:
        tag, entity, lvl = m_asc_nv.group(1), m_asc_nv.group(2), m_asc_nv.group(3)
        prep = 'do' if entity == 'Senhor' else 'de'
        return f"[{tag}] Baú de Auxílio à Ascensão {prep} {entity} (Nível {lvl})"

    # 3. Baús simples com [X]'Baú de [ITEM] s
    m_single = re.match(r'^(.*?)(\b[A-Za-zÀ-Úà-ú0-9\+\s]+)[’\']Baú de ([A-Za-zÀ-Úà-ú]+)\s+s$', text)
    if m_single:
        pref, entity, item = m_single.group(1), m_single.group(2).strip(), m_single.group(3).strip()
        item_pt = EQUIP_MAP.get(item, item)
        prep = 'do' if entity in ['Tribuno', 'Almirante', 'Centurião', 'Prefeito', 'Senhor', 'General de Brigada'] else 'de'
        return f"{pref}Baú de {item_pt} {prep} {entity}".strip()

    m_box_single = re.match(r'^(.*?)(\b[A-Za-zÀ-Úà-ú0-9\+\s]+)[’\']Caixa de ([A-Za-zÀ-Úà-ú]+)\s+s$', text)
    if m_box_single:
        pref, entity, item = m_box_single.group(1), m_box_single.group(2).strip(), m_box_single.group(3).strip()
        item_pt = EQUIP_MAP.get(item, item)
        prep = 'do' if entity in ['Tribuno', 'Almirante', 'Centurião', 'Prefeito', 'Senhor', 'General de Brigada'] else 'de'
        return f"{pref}Caixa de {item_pt} {prep} {entity}".strip()

    # 4. Tratar [X]'Baú de s [ITEM]
    m = re.match(r'^(.*?)(\b[A-Za-zÀ-Úà-ú0-9\+\s]+)[’\']Baú de s\s+(.*)$', text)
    if m:
        pref = m.group(1)
        entity = m.group(2).strip()
        item_raw = m.group(3).strip()
        item_pt = EQUIP_MAP.get(item_raw, item_raw)
        
        if entity in ['Almirante', 'Tribuno', 'Centurião', 'Prefeito', 'Senhor', 'Recruta', 'Comodoro', 'General de Brigada', 'Idéia de Brigada', 'idéia de Brigada']:
            prep = 'do'
            if 'Idéia' in entity or 'idéia' in entity:
                entity = 'General de Brigada'
        elif entity in ['Princesa', 'Rainha']:
            prep = 'da'
        else:
            prep = 'de'
            
        return f"{pref}Baú de {item_pt} {prep} {entity}".strip()

    return text


def fix_dragon_king(text):
    # Tratar Nobre X do Rei Dragão Y
    m_noble = re.match(r'^Nobre\s+(Sábio|Branco|Preto|Negro|Sombrio|Celeste|Chifrudo)\s+do\s+Rei\s+Dragão\s+([A-Za-zÀ-Úà-ú]+.*)$', text)
    if m_noble:
        dragon_type = m_noble.group(1)
        if dragon_type == 'Preto': dragon_type = 'Negro'
        item = m_noble.group(2).strip()
        item = EQUIP_MAP.get(item, item)
        adj = 'Nobres' if (item.endswith('s') or 'Protetores' in item) else 'Nobre'
        return f"{item} {adj} do Rei Dragão {dragon_type}"

    # Tratar X do Rei Dragão Y
    m_simple = re.match(r'^(Sábio|Branco|Preto|Negro|Sombrio|Celeste|Chifrudo)\s+do\s+Rei\s+Dragão\s+([A-Za-zÀ-Úà-ú]+.*)$', text)
    if m_simple:
        dragon_type = m_simple.group(1)
        if dragon_type == 'Preto': dragon_type = 'Negro'
        item = m_simple.group(2).strip()
        item = EQUIP_MAP.get(item, item)
        return f"{item} do Rei Dragão {dragon_type}"

    if 'Maça Dragão do Rei Dragão nobre' in text:
        return 'Maça Nobre do Rei Dragão Sábio'
    if 'Maça DO Dragão do Rei Dragão' in text:
        return 'Maça do Rei Dragão Sombrio'
    if 'Nobre Dragão do Rei Dragão Plearm' in text:
        return 'Alabarda Nobre do Rei Dragão Sombrio'
    if 'Nobre Dragão do Rei Dragão do rei' in text:
        return 'Cajado Nobre do Rei Dragão Sombrio'
    if 'Nobre Dragão do Rei Dragão Handleards' in text:
        return 'Manoplas de Malha Nobres do Rei Dragão Sombrio'
    if 'Nobre Dragão do Rei Dragão Mirseguards' in text:
        return 'Protetores de Ombro Nobres do Rei Dragão Sombrio'

    return text


def read_xml_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    while data.startswith(b'\xff\xfe'):
        data = data[2:]
    return data.decode('utf-16le', errors='ignore')


def write_xml_file(filepath, content):
    data = content.encode('utf-16le')
    with open(filepath, 'wb') as f:
        f.write(b'\xff\xfe' + data)


def validate_xml_string(xml_str):
    clean = xml_str.strip()
    if clean.startswith('<?xml'):
        clean = clean[clean.find('?>')+2:].strip()
    return ET.fromstring(clean)


def refine_file(filepath, apply_changes=False):
    filename = os.path.basename(filepath)
    print(f"\n--- Processando {filename} ---")
    text = read_xml_file(filepath)
    
    exact_count = 0
    # 1. Substituições exatas
    for k, v in EXACT_ITEM_REPLACEMENTS.items():
        pat = rf'(<string>\s*<id>\d+</id>\s*<name>{re.escape(k)}</name>\s*<body>)([^<]*)(</body>\s*</string>)'
        m = re.search(pat, text)
        if m and m.group(2) != v:
            text = re.sub(pat, rf'\g<1>{v}\g<3>', text)
            exact_count += 1

    # 2. Regras regex e funções contextuais
    # Itera sobre cada tag <string>...<body>...</body>...</string>
    pattern_string = re.compile(r'(<string>\s*<id>\d+</id>\s*(?:<name>[^<]*</name>\s*)?<body>)([^<]*)(</body>\s*</string>)')
    
    modified_bodies = 0
    def replacer(match):
        nonlocal modified_bodies
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        orig_body = body
        
        # A. Baús
        body = fix_chest_patterns(body)
        
        # B. Dragon King
        body = fix_dragon_king(body)
        
        # C. Regex gerais
        for r_pat, r_rep in ITEM_REGEX_RULES:
            if re.search(r_pat, body):
                body = re.sub(r_pat, r_rep, body)
                
        if body != orig_body:
            modified_bodies += 1
            
        return f"{prefix}{body}{suffix}"

    text = pattern_string.sub(replacer, text)
    
    print(f"[{filename}]: {exact_count} substituições exatas | {modified_bodies} strings modificadas por regras contextuais")
    
    # 3. Validação XML
    try:
        root = validate_xml_string(text)
        print(f"[SUCESSO] {filename} é sintaticamente válido ({len(root)} nós).")
    except Exception as e:
        print(f"[ERRO CRÍTICO] {filename} ficou inválido: {e}")
        return False
        
    if apply_changes:
        write_xml_file(filepath, text)
        print(f"[CONCLUÍDO] {filename} gravado com sucesso (UTF-16 LE com BOM).")
    else:
        print(f"[SIMULAÇÃO] Nenhuma alteração gravada em {filename}.")
        
    return True


def apply_refinements(apply_changes=False):
    print("=" * 70)
    print("AUDITORIA E REFINAMENTO DE NOMES DE ITENS (PT-BR)")
    print("=" * 70)
    
    target_files = [
        'client_strings_item.xml',
        'client_strings_item2.xml',
        'client_strings_dic_item.xml',
    ]
    
    all_ok = True
    for f in target_files:
        path = os.path.join(CLIENT_STRINGS_DIR, f)
        if os.path.exists(path):
            ok = refine_file(path, apply_changes=apply_changes)
            if not ok:
                all_ok = False
        else:
            print(f"[AVISO] Arquivo {f} não encontrado.")
            
    return all_ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Refinamento de Nomes de Itens PT-BR")
    parser.add_argument('--aplicar', action='store_true', help="Grava as alterações em disco")
    args = parser.parse_args()
    
    apply_refinements(apply_changes=args.aplicar)
