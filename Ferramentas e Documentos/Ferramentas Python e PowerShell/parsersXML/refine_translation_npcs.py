# -*- coding: utf-8 -*-
"""
Script de Refinamento de Qualidade - Nomes de NPCs, Títulos e Monstros (Aion Classic 5.0 PT-BR)
Foco exclusivo em:
1. NPCs de Cidades e Serviços (client_strings_npc.xml):
   - Mestre/Mercador de Artesanato (Handicrafting) eliminando 'deficiência' e 'desvantagem'
   - Correção de teletransportadores corrompidos ('Londres interbank...', 'Os mortos', 'Saberá', 'Uma rede')
   - Suportes de Armas de Kaliga ('Kaliga é minha rack feminina' -> 'Suporte de Maças de Kaliga', etc.)
   - Baús de Fortaleza e Abismo ('Caixote' -> 'Baú', ordem correta de adjetivos)
   - Correção de 'Quartel-General' ('Quartel- idéia') e títulos de patentes
2. Monstros e Chefes (client_strings_monster.xml):
   - 77 monstros com 'crack' militar -> 'de Elite' (Patrulha Kaidan de Elite, etc.)
   - Correção de 'Wallarm' -> 'Guarda-Muralha'
   - Eliminação de 'idéia' -> 'General' (General Luhut, General Naduka, General Primus, etc.)
   - Títulos de chefes com possessivo ('s) -> De / Da (Fragmento de Ômega, Agente de Kaisinel)
   - Inversão de adjetivos (Sombrio Daeva Guerreiro -> Guerreiro Daeva Sombrio, Divino Trico -> Trico Divino)
3. Enciclopédia de Personagens e Monstros (client_strings_dic_people.xml, client_strings_dic_monster.xml):
   - Eliminação de 'deficiência/desvantagem' para Artesanato
   - Restauração de 'General de Brigada'
4. Quests de Profissão (client_strings_quest.xml):
   - 'Missão de desvantagem' -> 'Missão de Artesanato'
   - 'especialista em deficiência' -> 'especialista em Artesanato'
   - 'mestre de serralheiro' -> 'mestre de ferraria de armaduras'
"""

import os
import sys
import re
import argparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')

# Correções exatas para client_strings_npc.xml
NPC_EXACT_FIXES = {
    # Artesanato (Handicrafting)
    'STR_NPC_TEST_Matest6': 'Mestre de Artesanato Asmodiano (Teste)',
    'STR_NPC_TEST_Matest12': 'Comerciante de Artesanato Asmodiano (Teste)',
    'STR_NPC_TEST_PRODUCE_L4': 'Mercador de Artesanato (Elyos)',
    'STR_NPC_TEST_PRODUCE_D4': 'Mercador de Artesanato (Asmodiano)',
    'STR_Guide_Handiwork_Guildmaster_DESC': 'Mestre de Artesanato',
    'STR_Guide_Handiwork_Seller_DESC': 'Comerciante de Artesanato',
    'STR_NPCTITLE_Handicrafting_Guildmaster': '&lt;Mestre de Artesanato&gt;',
    'STR_NPCTITLE_Handicrafting_Merchant': '&lt;Comerciante de Artesanato&gt;',

    # Teletransportadores e Fendas corrompidos
    'STR_NPCTITLE_LF4_Combine_Teva_Teleport_01': '&lt;Comerciante Nuvem Negra&gt;',
    'STR_NPCTITLE_DF4_Combine_Teva_Teleport_01': '&lt;Comerciante Nuvem Negra&gt;',
    'STR_Teva_Combine_LDF4_Teleport_01': 'Fenda do Abismo',
    'STR_NPCTITLE_2_Teleporter_DC1': '&lt;Teletransportador de Pandaemônio&gt;',
    'STR_OBJ_Ab1_to_DC1_Teleport_01': 'Teletransportador de Pandaemônio',
    'STR_IDDragonlord_Teleport_03': 'Teletransportador para o 3º Nível',
    'STR_LDF4b_to_Teva_Teleport_L_01': '&lt;Para a Base&gt;',
    'STR_LDF4b_to_Teva_Teleport_D_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_LDF4b_to_Teva_Teleport_L_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_LDF4b_to_Teva_Teleport_D_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_from_LDF4b_to_Tiamat_Down_R_Teleport_03': '&lt;Para a Base&gt;',
    'STR_OBJ_Teva_Combine_LF4_Teleport_01': '&lt;Para a Base&gt;',
    'STR_OBJ_Teva_Combine_DF4_Teleport_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_from_LDF4b_to_Tiamat_Down_R_Teleport_03_W': '&lt;Para a Base&gt;',
    'STR_OBJ_LDF4_Teva_FOBJ_Mission_Teleport_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_from_LDF4b_to_Tiamat_Down_R_Teleport_01_W': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_from_LDF4b_to_Tiamat_Down_R_Teleport_02_W': '&lt;Para a Base&gt;',
    'STR_LDF4b_to_Teva_Teleport_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_LDF4b_to_Teva_Teleport_01': '&lt;Para a Base&gt;',
    'STR_Teva_to_Teva_OP_Teleport_01': '&lt;Para a Base&gt;',
    'STR_NPCTITLE_Teva_to_Teva_OP_Teleport_01': '&lt;Para a Base&gt;',

    # Suportes de Armas de Kaliga
    'STR_OBJ_Grass_Locker_sword': 'Suporte de Espadas de Kaliga',
    'STR_OBJ_Grass_Locker_2hsword': 'Suporte de Espadões de Kaliga',
    'STR_OBJ_Grass_Locker_dagger': 'Suporte de Adagas de Kaliga',
    'STR_OBJ_Grass_Locker_polearm': 'Suporte de Armas de Haste de Kaliga',
    'STR_OBJ_Grass_Locker_bow': 'Suporte de Arcos de Kaliga',
    'STR_OBJ_Grass_Locker_mace': 'Suporte de Maças de Kaliga',
    'STR_OBJ_Grass_Locker_staff': 'Suporte de Cajados de Kaliga',
    'STR_OBJ_Grass_Locker_book': 'Suporte de Livros de Feitiço de Kaliga',
    'STR_OBJ_Grass_Locker_orb': 'Suporte de Orbes de Kaliga',
    'STR_OBJ_Grass_Locker_shield': 'Suporte de Escudos de Kaliga',

    # Baús de Fortaleza e Abismo
    'STR_OBJ_Ab1_1211_TreasureBox_SuscessA': 'Baú Dourado da Fortaleza',
    'STR_OBJ_Ab1_1211_TreasureBox_SuscessC': 'Baú Mágico da Fortaleza',
    'STR_OBJ_Ab1_1251_TreasureBox_SuscessA': 'Baú Dourado do Abismo',
    'STR_OBJ_Ab1_1251_TreasureBox_SuscessB': 'Baú de Joias do Abismo',
    'STR_OBJ_Ab1_1251_TreasureBox_SuscessC': 'Baú Mágico do Abismo',
    'STR_OBJ_TDown_TreasureBoxB': 'Baú do Tesouro do Protetorado',

    # Quartel-General e Outros Objetos
    'STR_IDTiamatLab_War_Attackable_Door_05': 'Muralhas do Quartel-General',
    'STR_OBJ_HolyServent_Devanion': 'Servo Sagrado do General Guardião',
    'STR_OBJ_DC1_StoryBook_8': 'Mulher Fatal da História 9',
    'STR_OBJ_DC1_StoryBook_20': 'Mulher Fatal da História 2',
    'STR_OBJ_DC1_StoryBook_21': 'Mulher Fatal da História 10',
    'STR_OBJ_IDRaksha_1F_Line2': 'Segunda Corda de Raksang',
    'STR_OBJ_IDRaksha_1F_Line3': 'Terceira Corda de Raksang',
    'STR_OBJ_IDLF1_exit': 'Portão do Abismo de Dark Poeta',
    'STR_OBJ_IDElemental_FOBJ_Pinwheel': 'Moinho de Vento',
    'STR_OBJ_Ab1_GiganticCore_Q2783': 'Núcleo de Petralith',

    # Títulos e Guardas
    'STR_NPCTITLE_GorteaFollower': '&lt;Atendente de Davlin&gt;',
    'STR_NPCTITLE_Loptr': '&lt;Amigo de Ariate&gt;',
    'STR_NPCTITLE_2_EVENT_WIND_MATTER_ENCHANT_SELLER': 'Acampamento de Senea',
    'STR_NPCTITLE_BountyHunter_Da_EN_title': '&lt;Guardião do Portão de Charlirunerk&gt;',
    'STR_NPC_F_Scale_150': 'Feminino 150%',
    'STR_NPC_F_Scale_120': 'Feminino 120%',
    'STR_NPC_F_Scale_110': 'Feminino 110%',
    'STR_NPC_F_Scale_90': 'Feminino 90%',
    'STR_NPC_F_Scale_70': 'Feminino 70%',
    'STR_NPC_F_Scale_50': 'Feminino 50%',
    'STR_Guard_HolyServant_45_An': 'Servo Sagrado',
    'STR_LGuard_HolyServantAtk_An_lv42': 'Servo Sagrado',
    'STR_LGuard_HolyServantAtk_An_lv52': 'Servo Sagrado',
    'STR_DGuard_HolyServantAtk_An_lv42': 'Servo Sagrado',
    'STR_DGuard_HolyServantAtk_An_lv52': 'Servo Sagrado',
    'STR_LGuard_HolyServantAtk_An_lv43': 'Servo Sagrado',
    'STR_DGuard_HolyServantAtk_An_lv43': 'Servo Sagrado',
    'STR_LGuard_HolyServantAtk_An_lv53': 'Servo Sagrado',
    'STR_DGuard_HolyServantAtk_An_lv53': 'Servo Sagrado',
    'STR_LGuard_HolyServantAtk_An_lv56': 'Servo Sagrado',
    'STR_DGuard_HolyServantAtk_An_lv56': 'Servo Sagrado'
}

# Correções exatas para client_strings_monster.xml
MONSTER_EXACT_FIXES = {
    # Generais corrigidos de 'idéia'
    'STR_Ab1_1132_UndeadDWizNamed_26_An': 'General Luhut',
    'STR_BAb1_NM_UndeadWizard_Da_26_An': 'General Luhut',
    'STR_BIDTP_DrakanBoss_55_Ah': 'General Kane',
    'STR_DF4_DrakanFi_DR_55_Ae': 'General Naduka',
    'STR_LycanHunterMNNM_39_Ae': 'General da Crina da Névoa',
    'STR_Ab1_1131_GuardCh_Li_Pr_1': 'General Primus',
    'STR_Ab1_1221_GuardCh_Da_Pr_2': 'General Primus',
    'STR_Ab1_1221_GuardCh_Dr_Pr_1': 'General Primus',
    'STR_Ab1_1221_GuardCh_Dr_Pr_2': 'General Primus',
    'STR_Branch_Event_DrakanFi_25_An': 'General Esquivo de Nochsana',
    'STR_LDF3_01_4011_Boss_Da_1': 'General Guardião Asmodiano',
    'STR_LDF3_01_4011_Boss_Da_2': 'General Guardião Asmodiano',
    'STR_LDF3_01_4011_Boss_Da_3': 'General Guardião Asmodiano',
    'STR_LDF3_01_4011_Boss_Da_4': 'General Guardião Asmodiano',
    'STR_LDF3_01_4011_Boss_Da_5': 'General Guardião Asmodiano',
    'STR_LDF4b_T2_Dragon_General_Named_59_Ae': 'General de Brigada Naduka',
    'STR_LDF4b_T3_Dragon_General_Named_60_Ae': 'General de Brigada Basrasa',
    'STR_LDF4b_T4_Dragon_General_Named_60_Ae': 'General de Brigada Satra',
    'STR_IDYun_Vasharti_Glove_ControllerA': 'General de Brigada Vasharti',
    'STR_IDYun_Vasharti_Glove_ControllerC': 'General de Brigada Vasharti',
    'STR_IDYun_Vasharti_Glove_ControllerD': 'General de Brigada Vasharti',
    'STR_IDYun_Vasharti_Glove_ControllerE': 'General de Brigada Vasharti',
    'STR_IDYun_Vasharti_Glove_Buffer': 'General de Brigada Vasharti',
    'STR_Event_Dragon_Sunayaka_Al': 'General Sunayaka',
    'STR_LDF10_Castle_DrakanFi_F_Tiamat_60_Ae': 'Supervisor de Batalha do Quartel-General de Henash',
    'STR_LDF10_Castle_DrakanRi_M_Tiamat_60_Ae': 'Oficial de Combate Aéreo do Quartel-General de Henash',
    'STR_Kisk_D_Legion_Emblem_03_4h': 'General Guardião Balaur',
    'STR_Ettin_31_An': 'Ettin Dente-Rachado',
    'STR_LehparWaD_35_An': 'Guerreiro Halabana',
    'STR_LF3F3_Lich_45_Ae': 'Lich Mago Sombrio',
    'STR_DarkDevaFi_25_Ae': 'Guerreiro Daeva Sombrio',
    'STR_DF2A_TriconD_48_An': 'Trico Divino',
    'STR_DF2A_TriconD_49_An': 'Trico Divino',
    'STR_HolyServantAmethystD_34_An': 'Ametista Sagrada',

    # Títulos de chefes com possessivos
    'STR_NPCTITLE_LF4_Raidsum': '&lt;Fragmento de Ômega&gt;',
    'STR_NPCTITLE_LF4_BOSS': '&lt;Agente de Kaisinel&gt;',
    'STR_NPCTITLE_IDCromede_1_Boss': '&lt;Legião da Lança de Siel&gt;',
    'STR_NPCTITLE_DF4_Raidsum': '&lt;Fragmento de Ragnarok&gt;',
    'STR_NPCTITLE_NejakanShild_a': '&lt;Legionário do Escudo de Nezekan&gt;',
    'STR_Ab1_12231_Artfact_Core_Li': 'Núcleo do Artefato Efluxo Daévico',
    'STR_Ab1_12231_Artfact_Core_Da': 'Núcleo do Artefato Efluxo Daévico',
    'STR_Ab1_12231_Artfact_Core_Dr': 'Núcleo do Artefato Efluxo Daévico'
}

def clean_npc_body(filename, sname, body):
    # 1. Checagens exatas
    if filename == 'client_strings_npc.xml' and sname in NPC_EXACT_FIXES:
        return NPC_EXACT_FIXES[sname]
    if filename == 'client_strings_monster.xml' and sname in MONSTER_EXACT_FIXES:
        return MONSTER_EXACT_FIXES[sname]

    # 2. Em client_strings_monster.xml: Ajustar monstros "Crack" (tropa militar de elite)
    if filename == 'client_strings_monster.xml':
        if 'crack' in body.lower():
            body = re.sub(r'\bPatrulha\s+Kaidan\s+de\s+crack\b', 'Patrulha Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bBloqueador\s+de\s+crack\s+Kaidan\b', 'Bloqueador Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Kaidan\s+Guerreiro\b', 'Guerreiro Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Kaidan\s+Batedor\b', 'Batedor Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Kaidan\s+Capitão\b', 'Capitão Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Kaidan\s+Plantygrunt\b', 'Grunhidor Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Kaidan\s+Outlider\b', 'Batedor Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Outlider\s+Chefe\b', 'Chefe Batedor de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+kaidan\s+retalhador\b', 'Retalhador Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+kaidan\s+lanceiro\b', 'Lanceiro Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+kaidan\s+n\s+pedação\b', 'Esmagador Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+kaidan\s+skullcracker\b', 'Quebra-Crânios Kaidan de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+kishar\s+Desbocado\b', 'Desbocado Kishar de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bWallarm\s+de\s+crack\s+kishar\b', 'Guarda-Muralha Kishar de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bWallarm\s+da\s+torre\s+Krall\s+crack\b', 'Guarda-Muralha da Torre Krall de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+Pathrunner\b', 'Corredor de Trilhas de Elite', body, flags=re.IGNORECASE)
            body = re.sub(r'\bCrack\s+([A-Za-zÀ-ÿ]+)\b', r'\1 de Elite', body)

        # Wallarm -> Guarda-Muralha
        if 'wallarm' in body.lower():
            body = re.sub(r'\bWallarm\b', 'Guarda-Muralha', body, flags=re.IGNORECASE)

        # Idéia -> General remanescente
        if 'idéia' in body.lower():
            body = re.sub(r'\bidéia\s+de\s+Brigada\b', 'General de Brigada', body, flags=re.IGNORECASE)
            body = re.sub(r'\bGuardião\s+idéia\b', 'General Guardião', body, flags=re.IGNORECASE)
            body = re.sub(r'\bidéia\s+Guardião\b', 'General Guardião', body, flags=re.IGNORECASE)
            body = re.sub(r'\bidéia\s+([A-ZÀ-Ú][a-zà-ú]+)\b', r'General \1', body)

    # 3. Enciclopédia de Pessoas (dic_people.xml) e Monstros (dic_monster.xml)
    if filename in ['client_strings_dic_people.xml', 'client_strings_dic_monster.xml']:
        if 'idéia' in body.lower():
            body = body.replace('um idéia aposentado da brigada', 'um General de Brigada aposentado')
            body = body.replace('idéia de Brigada', 'General de Brigada')
            body = body.replace('Guardião idéia', 'General Guardião')
            body = body.replace('Nochsana idéia', 'General de Nochsana')
        if 'deficiência' in body.lower() or 'desvantagem' in body.lower():
            body = body.replace('Mestre de Handicafting', 'Mestre de Artesanato')
            body = body.replace('mestre de desvantagem', 'Mestre de Artesanato')
            body = body.replace('comerciante de deficiência', 'Comerciante de Artesanato')
            body = body.replace('artístico é a coisa mais importante em deficiência', 'artístico é a coisa mais importante no artesanato')
        if "Charlirunerk's" in body:
            body = body.replace("Funcionário da Charlirunerk's", "Funcionário dos Demônios de Charlirunerk")
            body = body.replace("Rhonam Refugiado Vila", "Vila dos Refugiados de Rhonnam")
        if "Elim's Campos" in body:
            body = body.replace("Elim's Campos", "Campos dos Elims")
        if "ADMA FORTHOLD PASSAGEM" in body:
            body = body.replace("ADMA FORTHOLD PASSAGEM", "Passagem Secreta da Fortaleza de Adma")
            body = body.replace("fortaleza da ADMA", "Fortaleza de Adma")
        if "Carak's Covil" in body:
            body = body.replace("Carak's Covil", "Covil de Carak")
        if "Tiamat’s invasor" in body:
            body = body.replace("Tiamat’s invasor", "Invasor de Tiamat")
        if "Apsu’s Buscador" in body:
            body = body.replace("Apsu’s Buscador", "Buscador de Apsu")

    # 4. Quests de Artesanato (client_strings_quest.xml)
    if filename == 'client_strings_quest.xml':
        if 'Missão de desvantagem' in body:
            body = body.replace('Missão de desvantagem', 'Missão de Artesanato')
        if 'especialista em deficiência' in body:
            body = body.replace('especialista em deficiência', 'especialista em Artesanato')
        if 'mestre de deficiência' in body:
            body = body.replace('mestre de deficiência', 'mestre de Artesanato')
        if 'mestre de serralheiro' in body:
            body = body.replace('mestre de serralheiro', 'mestre de ferraria de armaduras')

    # 5. Guardas Elyos de Elite em client_strings_npc.xml
    if filename == 'client_strings_npc.xml':
        m_grd = re.match(r'^Elyos\s+Guarda\s+(Lutador|Feiticeiro)\s+Elite\s+padrão\s+Lv3\s+(\d+)\s+Nível$', body)
        if m_grd:
            classe = 'Guerreiro' if m_grd.group(1) == 'Lutador' else 'Feiticeiro'
            lvl = m_grd.group(2)
            body = f"Guarda {classe} Elyos de Elite (Nv. {lvl})"

    # Limpeza de espaços redundantes
    body = re.sub(r'[ \t]{2,}', ' ', body).strip()
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

        new_body = clean_npc_body(filename, s_name.strip(), s_body)
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
    parser = argparse.ArgumentParser(description="Refinamento de Nomes de NPCs, Títulos e Monstros")
    parser.add_argument('--aplicar', action='store_true', help="Aplica as alterações nos arquivos XML")
    parser.add_argument('--verificar', action='store_true', help="Apenas simula e exibe métricas")
    args = parser.parse_args()

    apply_changes = args.aplicar
    mode_str = "APLICAÇÃO REAL" if apply_changes else "VERIFICAÇÃO / SIMULAÇÃO"
    print(f"=======================================================")
    print(f"REFINAMENTO DE NOMES DE NPCS E MONSTROS ({mode_str})")
    print(f"=======================================================")

    files = [
        'client_strings_npc.xml',
        'client_strings_monster.xml',
        'client_strings_dic_people.xml',
        'client_strings_dic_monster.xml',
        'client_strings_quest.xml'
    ]

    total_modified = 0
    file_counts = {}

    for fname in files:
        fpath = os.path.join(STRINGS_DIR, fname)
        if os.path.isfile(fpath):
            count = process_file(fpath, apply_changes=apply_changes)
            if count > 0:
                file_counts[fname] = count
                total_modified += count

    for fname, count in file_counts.items():
        print(f"  {fname}: {count:,} strings refinadas")

    print(f"=======================================================")
    print(f"TOTAL DE STRINGS DE NPCS/MONSTROS REFINADAS: {total_modified:,}")
    print(f"=======================================================")

if __name__ == '__main__':
    main()
