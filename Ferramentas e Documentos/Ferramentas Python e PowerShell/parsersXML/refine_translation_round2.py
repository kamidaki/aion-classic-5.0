# -*- coding: utf-8 -*-
"""
Script de Refinamento e Qualidade de Localização Round 2 - Aion Classic 5.0 PT-BR
Focado em:
1. Lugares e Zonas (client_strings_level.xml, dic_place.xml) - Capitais, Reshanta, Elysea, Asmodae, Verteron, Hotspots
2. NPCs e Títulos (client_strings_npc.xml) - Patentes, possessivos ('s), teletransporte entre zonas
3. Monstros (client_strings_monster.xml) - Remoção de ': n. elite', artefatos, nomes invertidos
4. Magias e Habilidades (client_strings_skill.xml) - Aprisionamento do Éter, Cajados, Posturas, termos de combate
5. Itens e Equipamentos (client_strings_item.xml, item2.xml) - 'Funcionários' -> 'Cajado', 'deveriam/deveres' -> 'Ombreiras',
   'Eles derramam' -> 'Verteron', 'Manastone' -> 'Pedra de Mana', remoção de ': n. elite', conversão de possessivos 's
6. Limpeza geral do artefato 'Bedotia geayi' -> 'Zona' em todos os 15 arquivos XML afetados
"""

import os
import sys
import re
import argparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')
EN_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Client 5.0 - Dados Extraidos', 'Idioma em Inglês', 'strings')

# Mapeamento estrito de Hotspots corrompidos em client_strings_level.xml
HOTSPOT_FIXES = {
    'STR_HOTSPOT_LC1_01': 'Caminho Exaltado',
    'STR_HOTSPOT_LC1_02': 'Praça Elyos Oeste',
    'STR_HOTSPOT_LC1_03': 'Praça Elyos Leste',
    'STR_HOTSPOT_LC1_04': 'Liceu',
    'STR_HOTSPOT_LC1_05': 'Coliseu',
    'STR_HOTSPOT_LC1_06': 'Salão da Prosperidade',
    'STR_HOTSPOT_LC1_07': 'Biblioteca dos Sábios',
    'STR_HOTSPOT_LC1_08': 'Temporário',
    'STR_HOTSPOT_DC1_01': 'Praça de Pandaemônio',
    'STR_HOTSPOT_DC1_02': 'Praça de Pandaemônio Sul',
    'STR_HOTSPOT_DC1_03': 'Praça de Pandaemônio Norte',
    'STR_HOTSPOT_DC1_04': 'Grande Templo de Pandaemônio',
    'STR_HOTSPOT_DC1_05': 'Templo de Ouro',
    'STR_HOTSPOT_DC1_06': 'Coliseu Triniel',
    'STR_HOTSPOT_DC1_07': 'Templo do Conhecimento',
    'STR_HOTSPOT_LF4_01': 'Fortaleza da Ilusão de Inggison',
    'STR_HOTSPOT_LF4_02': 'Acampamento dos Investigadores',
    'STR_HOTSPOT_LF4_03': 'Vale de Phanoe',
    'STR_HOTSPOT_LF4_04': 'Acampamento de Philon',
    'STR_HOTSPOT_LF4_05': 'Santuário de Soteria',
    'STR_HOTSPOT_LF4_06': 'Rocha das Duas Mãos',
    'STR_HOTSPOT_LF4_07': 'Base de Instalação de Obelisco',
    'STR_HOTSPOT_LF4_08': 'Posto de Observação de Undirborg',
    'STR_HOTSPOT_LF4_09': 'Posto Avançado de Inggison',
    'STR_HOTSPOT_LF4_10': 'Posto de Observação de Angrief',
    'STR_HOTSPOT_LF4_11': 'Portão Desmoronado',
    'STR_HOTSPOT_LF4_12': 'Fossa de Inggison',
    'STR_HOTSPOT_LF4_13': 'Posto de Observação de Hanarkand',
    'STR_HOTSPOT_DF4_01': 'Fortaleza de Gelkmaros',
    'STR_HOTSPOT_DF4_02': 'Campo de Batalha de Antagor',
    'STR_HOTSPOT_DF4_03': 'Acampamento de Pesquisa de Éter',
    'STR_HOTSPOT_DF4_04': 'Encruzilhada Queda de Espírito',
    'STR_HOTSPOT_DF4_05': 'Vila dos Refugiados de Rhonnam',
    'STR_HOTSPOT_DF4_06': 'Acampamento Farbin',
    'STR_HOTSPOT_DF4_07': 'Posto de Guarda de Antagor',
    'STR_HOTSPOT_DF4_08': 'Cânion Submerso',
    'STR_HOTSPOT_DF4_09': 'Posto de Observação Subterrâneo',
    'STR_HOTSPOT_DF4_10': 'Base de Defesa de Gelkmaros',
    'STR_HOTSPOT_DF4_11': 'Acampamento da Expedição',
    'STR_HOTSPOT_DF4_12': 'Acampamento de Batalrion',
    'STR_HOTSPOT_DF4_13': 'Laboratório Biológico de Naduka',
    'STR_HOTSPOT_DF4_14': 'Posto de Batedores de Vorgaltem',
    'STR_HOTSPOT_DF4_15': 'Posto de Observação da Fazenda de Drana',
    'STR_HOTSPOT_LDF4_Teva_01': 'Zona de Controle: Ruínas da Gravidade',
    'STR_HOTSPOT_LDF4_Teva_02': 'Zona de Controle: Divisor de Fendas',
    'STR_HOTSPOT_LDF4_Teva_03': 'Zona de Controle: Santuário da Petrificação',
    'STR_HOTSPOT_LDF4_Teva_04': 'Zona de Controle: Brasão da Ira'
}

# Correções cruciais de zonas e regiões em client_strings_level.xml
LEVEL_EXACT_FIXES = {
    'STR_WORLD_NAME_LIGHT': 'Elísea',
    'STR_WORLD_NAME_DARK': 'Asmodae',
    'STR_WORLD_NAME_ABYSS': 'Reshanta',
    'STR_SZ_LF1_VERTERRON_STRONGHOLD': 'Cidadela de Verteron',
    'STR_SIGN_RS_LF1A_01': 'Cidadela de Verteron',
    'STR_LF1A_Airport_SUB_Verterron': 'Cidadela de Verteron',
    'STR_LF4_SZ_Sky': 'Céus de Inggison',
    'STR_LF4_Airport_ZONE': 'Porto Externo de Inggison',
    'STR_SZ_IDAb1_Dreadgion_19': 'Área Especial',
    'STR_SZ_iddreadgion_02_19': 'Área Especial',
    'STR_ZONE_NAME_LDF4b': 'Platô de Tiamaranta',
    'STR_LDF4b_SZ_All': 'Platô de Tiamaranta',
    'STR_LDF4b_SZ_T2_S11': 'Portão Oeste do Olho de Tiamaranta',
    'STR_LDF4b_SZ_T3_S8': 'Portão Leste do Olho de Tiamaranta',
    'STR_LDF4b_SZ_T4_S7': 'Portão Sul do Olho de Tiamaranta',
    'STR_TP_toLDF4B': 'Movendo-se para Sarpan.',
    'STR_LDF4b_Airport_ZONE_OP_L': 'Tiamaranta',
    'STR_LDF4b_Airport_ZONE_OP_D': 'Tiamaranta',
    'STR_UI_ZONE_MAP_LDF4B_TOP': 'Céus do Platô de Tiamaranta',
    'STR_UI_ZONE_MAP_LDF4B_BOTTOM': 'Solo do Platô de Tiamaranta',
    'STR_UI_ZONE_MAP_LDF4B_DOWN': 'Caverna Basilika do Platô de Tiamaranta',
    'STR_Tiamat_Down_Entrance_L': 'Entrada do Olho de Tiamaranta (Elyos)',
    'STR_Tiamat_Down_Entrance_D': 'Entrada do Olho de Tiamaranta (Asmodiano)',
    'STR_Tiamat_Down_Exit_L': 'Saída do Olho de Tiamaranta (Elyos)',
    'STR_Tiamat_Down_Exit_D': 'Saída do Olho de Tiamaranta (Asmodiano)',
    'STR_TP_toLC1': 'Teleporte para o Caminho Exaltado de Sanctum',
    'STR_TP_toDC1': 'Teleporte para a Ponte Vifrost de Pandaemônio',
    'STR_SZ_DC1_SUB_C': 'Praça de Pandaemônio',
    'STR_LF3_SZ_A1': 'Novo Portão de Heiron',
    'STR_LF3_SZ_D1': 'Observatório de Heiron',
    'STR_LF3_Airport_SUB_Interdica': 'Novo Portão de Heiron',
    'STR_LF3_Airport_SUB_Tower': 'Observatório de Heiron',
    'STR_SIGN_RS_LF3_A1': 'Novo Portão de Heiron',
    'STR_SIGN_RS_LF3_D1': 'Observatório de Heiron',
    'STR_TP_toLF3': 'Viajando para Heiron.',
    'STR_SIGN_RS_LF2_ToLF3': 'Estrada para Heiron',
    'STR_LF2_SZ_LF2_ToLF3': 'Estrada para Heiron',
    'STR_Ab1_SZ_1211_I': 'Fissura Ocidental de Reshanta',
    'STR_ZONE_NAME_LC1a': 'Portão de Sanctum',
    'STR_ZONE_NAME_DC1a': 'Entrada de Pandaemônio',
    'STR_SZ_DC1_SUB_9': 'Entrada de Pandaemônio',
    'STR_SZ_DC1_SUB_1': 'Grande Templo de Pandaemônio',
    'STR_DF3_Airport_SUB_Amsnir': 'Campo de Refugiados de Besfer',
    'STR_SIGN_RS_DF3_E1': 'Campo de Refugiados de Besfer',
    'STR_DF3_SZ_E1': 'Campo de Refugiados de Besfer',
    'STR_IDTiamatLab_War_SZ_C_SUB_01': 'Acampamento Nuvem Negra',
    'STR_LDF4b_SZ_OP_A2': 'Campo de Batalha de Kamar',
    'STR_LDF4b_SZ_OP_A3': 'Campo de Batalha de Kamar',
    'STR_ZONE_IDdranamine_War_SZ_03': 'Campo de Batalha de Tiamat',
    'STR_LDF4b_SZ_Tower_Near_L_1': 'Campo de Batalha de Tiamat'
}

# Correções de Skills
SKILL_EXACT_FIXES = {
    'STR_SYSTEM_SKILL_OpenAerial': 'Aprisionamento do Éter',
    'STR_SKILL_WI_WizardryHook_G1': 'Aprisionamento do Éter I',
    'STR_SKILL_WI_WizardryHook_G2': 'Aprisionamento do Éter II',
    'STR_SKILL_WI_WizardryHook_G3': 'Aprisionamento do Éter III',
    'STR_SKILL_WI_WizardryHook_G4': 'Aprisionamento do Éter IV',
    'STR_SKILL_WI_WizardryHook_G5': 'Aprisionamento do Éter V',
    'STR_SKILL_WI_WizardryHook_G6': 'Aprisionamento do Éter VI',
    'STR_SKILL_P_EQUIP_Staff_G1': 'Treinamento Avançado com Cajado I',
    'STR_SKILL_CH_EQUIP_Staff': 'Treinamento Avançado com Cajado I',
    'STR_SKILL_RA_MarksmanMode_G1': 'Postura de Atirador de Elite I',
    'STR_SKILL_HolyWraith': 'Aparição Sagrada',
    'STR_SKILL_HolyWraith_DESC': 'Aparição Sagrada',
    'STR_Arena_pvp01_S1_heal': 'Aura da Bênção',
    'STR_BNFI_SanctuaryStatup_IDRW_Abnormal': 'Você está protegido pelo Santuário. Você não pode ser ferido por nenhum meio.'
}

def clean_body_text(filename, sname, body):
    orig = body
    
    # 1. Hotspots em level.xml
    if filename == 'client_strings_level.xml':
        if sname in HOTSPOT_FIXES:
            return HOTSPOT_FIXES[sname]
        if sname in LEVEL_EXACT_FIXES:
            return LEVEL_EXACT_FIXES[sname]
            
    # 2. Skills exatas
    if filename == 'client_strings_skill.xml':
        if sname in SKILL_EXACT_FIXES:
            return SKILL_EXACT_FIXES[sname]

    # 3. Eliminar "Bedotia geayi" (artefato que substituiu Zona/Região)
    if 'bedotia geayi' in body.lower():
        # Substituições contextuais elegantes
        body = re.sub(r'Sem\s+bedotia\s*geayi\s+PVP\b', 'Zona Segura (Não-PvP)', body, flags=re.IGNORECASE)
        body = re.sub(r'Sem\s+bedotia\s*geayi\s+de\s+duelo\b', 'Zona Sem Duelo', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+PVP\b', 'Zona PvP', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+de\s+Carga\b', 'Zona de Carga', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+de\s+queda\b', 'Zona de Salto', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+da\s+prisão\b', 'Zona Prisional', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+restrita\b', 'Zona Restrita', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+residencial\b', 'Área Residencial', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+instanciada\b', 'zona instanciada', body, flags=re.IGNORECASE)
        body = re.sub(r'bedotia\s*geayi\s+instanciada\b', 'zona instanciada', body, flags=re.IGNORECASE)
        body = re.sub(r'nesta\s+bedotia\s*geayi\b', 'nesta zona', body, flags=re.IGNORECASE)
        body = re.sub(r'da\s+bedotia\s*geayi\b', 'da zona', body, flags=re.IGNORECASE)
        body = re.sub(r'na\s+bedotia\s*geayi\b', 'na zona', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+de\s+teste\b', 'Zona de Teste', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\s+de\s+interceptação\b', 'Zona de Interceptação', body, flags=re.IGNORECASE)
        body = re.sub(r'Bedotia\s*geayi\b', 'Zona', body)
        body = re.sub(r'bedotia\s*geayi\b', 'zona', body)

    # 4. Eliminar ": n. elite" e variantes de dicionário
    if ': n. elite' in body.lower() or ':n. elite' in body.lower():
        body = re.sub(r':\s*n\.\s*elite\b', '', body, flags=re.IGNORECASE)
        # Se ficou 'Elite  Posto' ou 'Elite Posto'
        body = re.sub(r'\bElite\s+Posto\s+(\d+)\s+([A-Za-zÀ-ÿ]+)\s+(.+)$', r'\3 \2 de Elite de Posto \1', body)
        # Limpar repetições geradas como 'de elite de Elite'
        body = re.sub(r'\bde\s+elite\s+de\s+Elite\b', 'de Elite', body, flags=re.IGNORECASE)
        body = re.sub(r'\bElite:\s*', 'Elite ', body)

    # 5. Outros marcadores de dicionário
    if 'significa: n. meio' in body:
        body = body.replace('significa: n. meio', 'meio')
    if 'Internet: n. a internet café' in body:
        body = body.replace('Internet: n. a internet café', 'Lan House')
    if 'animalia de estimação' in body:
        body = body.replace('animalia de estimação', 'animal de estimação')
    if 'Moeda comerciante' in body:
        body = body.replace('Moeda comerciante', 'Comerciante de Moedas')
    if 'Comércio Corretor' in body:
        body = body.replace('Comércio Corretor', 'Corretor de Comércio')
    if 'o Fenda' in body:
        body = body.replace('o Fenda', 'a Fenda')
    if 'O idéia de Brigada' in body:
        body = body.replace('O idéia de Brigada', 'O General de Brigada')

    # 6. NPCs: Teletransporte entre zonas e patentes
    if filename == 'client_strings_npc.xml':
        if sname and sname.startswith('STR_OBJ_Zone_Teleport_'):
            body = re.sub(r'^.*?teletransporte de\s+(.+)$', r'Teletransporte Entre Zonas de \1', body, flags=re.IGNORECASE)
            body = body.replace('santuário', 'Sanctum').replace('poeta', 'Poeta').replace('verteron', 'Verteron').replace('heiron', 'Heiron')
        if "Fenris's Fangs" in body:
            body = body.replace("Fenris's Fangs", "Presas de Fenris").replace("de Presas de Fenris", "das Presas de Fenris")
        if "Manir's tio" in body:
            body = body.replace("Manir's tio", "Tio de Manir")
        if "Nezekan's Escudo Legionário" in body:
            body = body.replace("Nezekan's Escudo Legionário", "Legionário do Escudo de Nezekan")
        if "TALOC's Jovem Galho" in body or "Taloc's Jovem Galho" in body:
            body = body.replace("TALOC's Jovem Galho", "Broto de Taloc").replace("Taloc's Jovem Galho", "Broto de Taloc")
        if "Charlirunerk's Daemons" in body:
            body = re.sub(r"Charlirunerk's\s+Daemons.*", "Demônios de Charlirunerk", body)

    # 7. Monstros: Núcleos de artefato e chefes
    if filename == 'client_strings_monster.xml':
        if "Metamor's Grama" in body:
            body = body.replace("Metamor's Grama", "Restaurador")
        body = re.sub(r'^Feroz\s+([A-Za-zÀ-ÿ]+)$', r'\1 Feroz', body)
        body = re.sub(r'^Poderoso\s+(Petrahulk|Duque|Stallari)', r'\1 Poderoso', body)

    # 8. Skills: Combate, termos e descrições
    if filename == 'client_strings_skill.xml':
        body = body.replace('Éter\'s Manter', 'Aprisionamento do Éter')
        body = body.replace('n transferência de crédito (em banco).', 'giro')
        body = body.replace('puts ele em o', 'coloca-o no')
        body = body.replace('puts ele no', 'coloca-o no')
        body = body.replace('voador alvo', 'alvo voador')
        body = body.replace('Enters postura modo e blocks inimigo\'s Ataque por usando Bloqueio.', 'Entra no modo de postura e bloqueia ataques inimigos com Bloqueio.')
        body = body.replace("restaura o alvo's HP", "restaura o HP do alvo")
        body = body.replace("restaura o alvo’s HP", "restaura o HP do alvo")
        body = body.replace("o alvo's HP", "o HP do alvo")
        body = body.replace("o alvo’s HP", "o HP do alvo")
        body = body.replace("o alvo’s ", "o ")
        body = body.replace("o alvo's ", "o ")
        body = body.replace("inimigo's Ataque", "ataques inimigos")
        body = body.replace("inimigo’s Ataque", "ataques inimigos")
        body = body.replace("Sagrado Aparição", "Aparição Sagrada")
        body = body.replace("Mágico Implosão", "Implosão Mágica")
        body = body.replace("Mágico Mantra", "Mantra Mágico")

    # 9. Itens:
    if filename in ['client_strings_item.xml', 'client_strings_item2.xml']:
        # A. Manastone -> Pedra de Mana
        if 'Manastone' in body:
            body = re.sub(r'\bManastone:\s*', 'Pedra de Mana: ', body)
            body = re.sub(r'\bAleatrio\s+Manastone\b', 'Pedra de Mana Aleatória', body)
            body = re.sub(r'\bCaixa\s+de\s+Amor\s+Manastone\b', 'Caixa de Amor de Pedra de Mana', body)
            body = re.sub(r'\bManastone\b', 'Pedra de Mana', body)

        # B. 'Funcionários' para armas do tipo Cajado (Staff)
        if 'Funcionários' in body:
            body = re.sub(r'\bFuncionários\s+de\s+', 'Cajado de ', body)
            body = re.sub(r'\bFuncionários\s+do\s+', 'Cajado do ', body)
            body = re.sub(r'\bFuncionários\s+da\s+', 'Cajado da ', body)
            body = re.sub(r'\bFuncionários\s+asmodianos\b', 'Cajado Asmodiano', body)
            body = re.sub(r'\bFuncionários\s+sombreados\b', 'Cajado Sombreado', body)
            body = re.sub(r'\bFuncionários\s+do\s+PNJ\b', 'Cajado do PNJ', body)
            body = re.sub(r'\bFuncionários\s+avançados\b', 'Cajado Avançado', body)
            body = re.sub(r'\bFuncionários\b', 'Cajado', body)

        # C. Ombreiras traduzidas bizarramente como 'deveriam', 'deveres', 'deveriores', 'suergões de deveres', 'Devergúndios'
        if any(w in body.lower() for w in ['deveriam', 'deveriores', 'deveres', 'suergões', 'devergúndios', 'servanguard']):
            body = re.sub(r'\bEles derramam plantas deveriam\b', 'Ombreiras de Verteron', body)
            body = re.sub(r'\bDevergúndios de deveres de viajantes\b', 'Ombreiras do Viajante', body)
            body = re.sub(r'\bServiços de deveres do cultivador\b', 'Ombreiras do Cultivador', body)
            body = re.sub(r'\bPatriota\'s deveriores\b', 'Ombreiras do Patriota', body)
            body = re.sub(r'\bFlorestas deveriam ser criadas\b', 'Ombreiras da Floresta', body)
            body = re.sub(r'\bDesolação deveriam gerar\b', 'Ombreiras da Desolação', body)
            body = re.sub(r'\bPNJ Asmodiano deveriam\b', 'Ombreiras de PNJ Asmodiano', body)
            body = re.sub(r'\bKromede inspirou a masmorra NPC deveriam\b', 'Ombreiras de Masmorra de Kromede (PNJ)', body)
            body = re.sub(r'\bServiços de deveres de aventureiro\b', 'Ombreiras do Aventureiro', body)
            body = re.sub(r'\bServiços de deveres de conselhos sábios\b', 'Ombreiras do Sábio Conselho', body)
            body = re.sub(r'\bServiços de deveres do líder sábio\b', 'Ombreiras do Sábio Líder', body)
            body = re.sub(r'\bNobre grosso deveriores de servões\b', 'Ombreiras Nobres Grossas', body)
            body = re.sub(r'\bNobre Grost o grosso Durável deveriam ser criados\b', 'Ombreiras Nobres Duráveis Grossas', body)
            body = re.sub(r'\bsuergões de deveres duráveis\s*​​finos e finos\b', 'ombreiras finas e duráveis', body)
            body = re.sub(r'\b([A-Za-zÀ-ÿ]+)\'s\s+ServanGuards\b', r'Ombreiras de \1', body)
            body = re.sub(r'\b-deveriores\b', ' Ombreiras', body)
            body = re.sub(r'\bdeveriam\b', 'Ombreiras', body)

        # D. 'Eles derramam' -> Verteron em armas/itens
        if 'Eles derramam' in body:
            body = re.sub(r'Eles\s+derramam\s+espada\s+da\s+guarda', 'Espada do Guardião de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+maça\s+guardião', 'Maça do Guardião de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+Adaga\s+guardião', 'Adaga do Guardião de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+arco\s+do\s+guardião', 'Arco do Guardião de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+Arqueiro\s+Gibão', 'Gibão de Arqueiro de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+vambraces\s*\(Arqueiro\)', 'Braçadeiras de Arqueiro de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+calças\s*\(Arqueiro\)', 'Calças de Arqueiro de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+vambraces\s*\(assassino\)', 'Braçadeiras de Assassino de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+Grevas\s+de\s+Placas', 'Grevas de Placa de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+espada', 'Espada de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+maça', 'Maça de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+adaga', 'Adaga de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+arco', 'Arco de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+túnica', 'Túnica de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+sapatos', 'Sapatos de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+calças', 'Calças de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+brogans', 'Botas de Malha de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+gancho\s+de\s+cabelo', 'Grampo de Cabelo de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+para\s+baixo', 'Capuz de Penas de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+banda', 'Cinto de Verteron', body)
            body = re.sub(r'Eles\s+derramam\s+a\s+Cidadela', 'Cidadela de Verteron', body)
            body = re.sub(r'Eles\s+derramam', 'de Verteron', body)

        # E. Aberrações específicas
        if 'Os dias da sala de estar' in body:
            body = body.replace('Os dias da sala de estar', 'Adaga de Stua')
        if 'Abow Arco de Kaliga' in body:
            body = body.replace('Abow Arco de Kaliga', 'Arco de Kaliga')
        if 'Kromede inspirou Masmorra NPC Arco' in body:
            body = body.replace('Kromede inspirou Masmorra NPC Arco', 'Arco de Masmorra de Kromede (PNJ)')

        # F. Possessivos 's / ’s em nomes de itens (ex: "Poderoso Grogget's Adaga" -> "Adaga Poderosa de Grogget")
        if "'s " in body or "’s " in body:
            # Padrão: Poderoso Nome's Item
            m_pod = re.match(r'^Poderoso\s+([A-Za-zÀ-ÿ0-9\s\-]+?)[\'’]s\s+(.+)$', body)
            if m_pod:
                owner = m_pod.group(1).strip()
                item = m_pod.group(2).strip()
                fem_items = ['adaga', 'espada', 'maça', 'cota', 'túnica', 'luva', 'bota', 'ombreira', 'perneira', 'faixa', 'tiara', 'armadura']
                adj = 'Poderosa' if any(item.lower().startswith(x) for x in fem_items) else 'Poderoso'
                body = f"{item} {adj} de {owner}"
            else:
                # Padrão: [Prefixo: ]Nome's Item
                # Não aplicar se for descrição longa (ex: contém ponto final ou quebra de linha)
                if '\n' not in body and not body.endswith('.'):
                    m_gen = re.match(r'^(Projeto:\s*|Receita:\s*|Design:\s*)?([A-Za-zÀ-ÿ0-9\s\-]+?)[\'’]s\s+(.+)$', body)
                    if m_gen:
                        prefix = m_gen.group(1) or ''
                        owner = m_gen.group(2).strip()
                        item = m_gen.group(3).strip()
                        
                        # Artigo/Preposição
                        prep = "de"
                        if owner.lower() in ['caminhante', 'sentinela', 'assassino', 'patriota', 'membro', 'comandante', 'capitão']:
                            prep = "do"
                        elif owner.lower() in ['gárgula']:
                            prep = "da"
                            
                        body = f"{prefix}{item} {prep} {owner}".strip()

        # G. Preposições compostas robotizadas de o(a) / em o(a)
        if any(u in body for u in ['de o(a)', 'em o(a)', 'de a(o)', 'em a(o)', 'a o(a)']):
            body = body.replace('de o(a)', 'do(a)').replace('em o(a)', 'no(a)').replace('a o(a)', 'ao(à)')

    # Limpeza final de espaços redundantes mantendo tags
    body = re.sub(r'[ \t]{2,}', ' ', body)
    return body

def process_file(filepath, apply_changes=False):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        data = f.read()

    encoding = 'utf-16le' if data.startswith(b'\xff\xfe') else ('utf-8-sig' if data.startswith(b'\xef\xbb\xbf') else 'utf-8')
    text = data.decode(encoding, errors='ignore')

    modified_count = 0

    def replacer(match):
        nonlocal modified_count
        full_match = match.group(0)
        s_id = match.group(1)
        s_name = match.group(2) or ''
        s_body = match.group(3)

        new_body = clean_body_text(filename, s_name.strip(), s_body)
        if new_body != s_body:
            modified_count += 1
            name_part = f"<name>{s_name}</name>" if s_name else ""
            return f"<string><id>{s_id}</id>{name_part}<body>{new_body}</body></string>"
        return full_match

    pattern = re.compile(r'<string>\s*<id>([^<]*)</id>\s*(?:<name>([^<]*)</name>\s*)?<body>([^<]*)</body>\s*</string>')
    new_text = pattern.sub(replacer, text)

    if apply_changes and modified_count > 0:
        if encoding == 'utf-16le':
            out_bytes = b'\xff\xfe' + new_text.encode('utf-16le')
        elif encoding == 'utf-8-sig':
            out_bytes = b'\xef\xbb\xbf' + new_text.encode('utf-8')
        else:
            out_bytes = new_text.encode('utf-8')

        with open(filepath, 'wb') as f:
            f.write(out_bytes)

    return modified_count

def main():
    parser = argparse.ArgumentParser(description="Refinamento de Localização Round 2 - Itens, Skills, NPCs, Lugares")
    parser.add_argument('--aplicar', action='store_true', help="Aplica as alterações nos arquivos XML")
    parser.add_argument('--verificar', action='store_true', help="Apenas simula e exibe métricas")
    args = parser.parse_args()

    apply_changes = args.aplicar
    mode_str = "APLICAÇÃO REAL" if apply_changes else "VERIFICAÇÃO / SIMULAÇÃO"
    print(f"=======================================================")
    print(f"REFINAMENTO DE LOCALIZAÇÃO ROUND 2 ({mode_str})")
    print(f"=======================================================")

    total_modified = 0
    file_counts = {}

    for fname in sorted(os.listdir(STRINGS_DIR)):
        if fname.endswith('.xml'):
            fpath = os.path.join(STRINGS_DIR, fname)
            count = process_file(fpath, apply_changes=apply_changes)
            if count > 0:
                file_counts[fname] = count
                total_modified += count

    for fname, count in file_counts.items():
        print(f"  {fname}: {count:,} strings refinadas")

    print(f"=======================================================")
    print(f"TOTAL DE STRINGS REFINADAS (ROUND 2): {total_modified:,}")
    print(f"=======================================================")

if __name__ == '__main__':
    main()
