# -*- coding: utf-8 -*-
"""
Script de Refinamento de Qualidade - Strings de Interface de Usuário (UI) e Mensagens (Aion Classic 5.0 PT-BR)

Foco exclusivo em:
1. Interface do Usuário (client_strings_ui.xml):
   - Eliminação de "Deputado atual" -> "MP Atual"
   - Correção de "Cardápio do sistema" -> "Menu do Sistema" e "Cardápio do Jogo" -> "Menu do Jogo"
   - Correção de botões: "Arte" -> "Fabricar", "Papel n reunião social os dados" -> "Rolar Dados", "Deixe masmorra" -> "Sair da Masmorra"
   - Correção de "Entre no quarto do chefe" -> "Entrar na Sala do Chefe"
   - Correção de "Compartilhar" -> "Dividir" (separar pilha de itens)
   - Correção de "Arma de região autónoma da madeira" -> "Armas de Madeira"
   - Correção de "Grande idéia" -> "Grande General" (Rank 16 do Abismo)
   - Correção de patentes e títulos militares do Pass: "idéia de Brigada" -> "General de Brigada"
   - Correção de "Moreth, Crônica do Andamento" -> "Moros, Crônica da Criação"
   - Limpeza de resíduos: "parte n inferior" -> "parte inferior", "cardápio Martelo de Siel" -> "menu Martelo de Siel"

2. Mensagens de Combate e do Sistema (client_strings_msg.xml):
   - Restauração de MP: "Você trocou seu deputado com seu HP" -> "Você trocou seu MP com seu HP", "deputado de [%SkillTarget]" -> "MP de [%SkillTarget]"
   - Correção de estados de combate (Stagger, Stumble, Stun, Blind, Disease, Fear):
     * "Você não é mais impressionante" / "[%SkillTarget] não é mais impressionante" -> "recuperou-se do cambaleio"
     * "Você não está mais chocado" / "caiu de choque" -> "recuperou-se da queda" / "tropeçou e caiu"
     * "Você ficou surpreso" -> "Você ficou atordoado"
     * "Você cego" -> "Você cegou", "Você doente" -> "Você adoeceu", "Você atordoado" -> "Você atordoou"
     * "Você fica impressionado com medo" -> "Você foi dominado pelo medo"
     * "Você pode ver novamente" -> "Sua visão retornou."
   - Correção de cancelamentos e conflitos: "foi cancelado como" -> "foi cancelado porque"
   - Padronização do Sistema de Legião (STR_GUILD_*): substituição de "Guilda" por "Legião" (General de Brigada, Centurião, Legionário, Depósito da Legião)
   - Correção de chefes e avisos: "Grande idéia" -> "Grande General", "idéia Sunayaka" -> "General Sunayaka"
   - Eliminação de erro ortográfico: "ágora" -> "agora" (76 ocorrências)

3. Enciclopédia de Conhecimento e ETC (client_strings_dic_etc.xml, client_strings_etc.xml):
   - Eliminação de "região autónoma da madeira"
   - Correção de "General Guardião"
   - Correção de "Bancada de Artesanato"
   - Correção de "Tursin de Elite" (eliminando "Crack Tursin" e "quebrar forças")

4. Normalização de Codificação:
   - Remoção de múltiplos BOMs duplicados/triplicados, garantindo exatamente 1 BOM UTF-16 LE padrão.
"""

import os
import sys
import re
import argparse
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')

# Substituições exatas por ID/Name para client_strings_ui.xml
UI_EXACT_FIXES = {
    'STR_curMP': 'MP Atual',
    'STR_WINDOW_SYSTEM': 'Menu do Sistema',
    'STR_KEYMAP_TOGGLEDIALOG_SYSTEM_MENU': 'Menu do Sistema',
    'STR_KEYMAP_TOGGLEDIALOG_GAME_MENU': 'Menu do Jogo',
    'STR_BUTTON_CRAFT': 'Fabricar',
    'STR_VENDOR_KIND_MAKING': 'Fabricação',
    'STR_CRAFTWINDOW_TREEWEAPON': 'Armas de Madeira',
    'STR_Abyssrank_light_16': 'Grande General',
    'STR_Abyssrank_dark_16': 'Grande General',
    'STR_UI_LOOT_TITLE_ROLL': 'Rolar Dados',
    'STR_UI_LOOT_BUTTON_ROLL': 'Rolar Dados',
    'STR_PARTY_MSG_LOOT_DIST_ROLL': 'Rolar Dados',
    'STR_INDUN_ACCOUNT_INFO_PVE_BUTTON_SUCCEED': 'Entrar na Sala do Chefe',
    'STR_INDUN_ACCOUNT_INFO_PVE_BUTTON_FAILED': 'Sair da Masmorra',
    'STR_INDUN_ACCOUNT_INFO_PVE_BUTTON_PLAYING': 'Sair da Masmorra',
    'STR_INDUN_ACCOUNT_INFO_PVP_BUTTON_SUCCEED': 'Sair da Masmorra',
    'STR_INDUN_ACCOUNT_INFO_PVP_BUTTON_FAILED': 'Sair da Masmorra',
    'STR_INDUN_ACCOUNT_INFO_PVP_BUTTON_PLAYING': 'Sair da Masmorra',
    'STR_QUICKMENU_SPLIT': 'Dividir',
    'STR_QUICKMENU_MOROS': 'Moros',
    'STR_MENU_MOROS': 'Moros, Crônica da Criação',
    'STR_DIALOG_UPGRADE_BUTTON': 'Ascender',
    'STR_MSG_SHARE_QUEST': '%0 compartilhou a missão [%questname]. Deseja aceitar?',
    'STR_CHAT_MODE_CMD_GENERAL': 'geral,g,s,fala,normal',
    'STR_TOOLTIP_CANNOT_SPLIT_ITEM': 'Não pode ser dividido',
    'STR_Task_130001_DESC': '<p>Obtenha a arma de um General de Brigada.</p>\n<p>A missão estará concluída assim que você obtiver qualquer arma do General de Brigada.</p>',
    'STR_Task_130001_HTML': 'Obtenha a arma de um General de Brigada',
    'STR_Task_130010_HTML': 'Adquira um Anel do General de Brigada',
    'STR_Task_130011_HTML': 'Adquira um Cinto do General de Brigada',
    'STR_Task_160015_DESC': '<p>Derrote o General de Brigada Tahabata no Santuário de Tiamat.</p>\n<p>Aparece no 3º nível: Altar da Destruição.</p>',
    'STR_RACE_CHANGE_BTN_HELP_TOOLTIP_IN_FACTION': 'Membro de Organização (Ordem de Alabastro / Operações Radiantes / Cruzada de Sangue / Sortudos): Não é membro',
}

# Substituições exatas por ID/Name para client_strings_msg.xml
MSG_EXACT_FIXES = {
    'STR_SKILL_SUCC_SwitchHPMP_Instant_ME_TO_SELF': 'Você trocou seu MP com seu HP usando [%SkillName].',
    'STR_SKILL_SUCC_MPHeal_ME_TO_B': 'O MP de [%SkillTarget] está sendo recuperado continuamente porque você lançou [%SkillName].',
    'STR_SKILL_SUCC_MPHeal_A_TO_ME': '[%SkillCaster] está restaurando continuamente seu MP usando [%SkillName].',
    'STR_SKILL_SUCC_Stun_ME_TO_SELF': 'Você ficou atordoado após usar [%SkillName].',
    'STR_SKILL_SUCC_Stun_ME_TO_B': 'Você atordoou [%SkillTarget] usando [%SkillName].',
    'STR_SKILL_SUCC_Blind_ME_TO_B': 'Você cegou [%SkillTarget] usando [%SkillName].',
    'STR_SKILL_SUCC_Disease_ME_TO_B': 'Você adoeceu [%SkillTarget] usando [%SkillName].',
    'STR_SKILL_SUCC_Fear_ME_TO_SELF': 'Você foi dominado pelo medo após usar [%SkillName].',
    'STR_SKILL_SUCC_Blind_END_ME_TO_SELF': 'Sua visão retornou.',
    'STR_SOUL_BOUND_ITEM_FAILED': 'Falha ao vincular a alma de %0.',
    'STR_MSG_IDDokkaebi_Imoog_04': 'Meu Deus, o Grande General está agindo de forma terrível!',
    'STR_MSG_LDF10_Sunayaka_01': 'O General Sunayaka apareceu em Laphsaran.',
    'STR_GUILD_CHANGE_LEVEL_DONT_HAVE_RIGHT': 'Somente o General de Brigada pode solicitar o aumento de nível da Legião.',
    'STR_GUILD_CHANGE_MASTER_SENT_OFFER_MSG_TO_HIM': 'Você nomeou %0 como o novo General de Brigada da Legião.',
    'STR_GUILD_BANSIH_HE_BANISHED_HIM': '%0 expulsou %1 da Legião.',
    'STR_GUILD_BANISHIED_FROM_GUILD_BY_HIM': 'Você foi expulso da Legião %0.',
    'STR_GUILD_CHANGE_MEMBER_RANK_DONT_HAVE_RIGHT': 'Você não pode alterar os postos dos membros da Legião, porque você não é o General de Brigada.',
    'STR_GUILD_CHANGE_MEMBER_RANK_DONE_2_GUILD_OFFICER': '%0 se tornou um Centurião da Legião.',
    'STR_GUILD_CHANGE_MEMBER_RANK_DONE_3_GUILD_MEMBER': '%0 se tornou um Legionário.',
    'STR_GUILD_DISPERSE_REQUESTED': 'O General de Brigada solicitou a dissolução da Legião. O momento previsto para dissolução é %DATETIME0.',
    'STR_GUILD_INTRO': 'Informações da Legião: %0',
    'STR_GUILD_NOTICE': 'Anúncio da Legião: %0 %DATETIME1',
    'STR_GUILD_INVITE_I_JOINED': 'Você se juntou à Legião %0.\nDigite os comandos /G ou /Legião na janela de bate-papo para iniciar o bate-papo da Legião.',
}

# Substituições exatas por ID/Name para client_strings_dic_etc.xml
DIC_ETC_EXACT_FIXES = {
    'STR_DIC_LF3_gb_source_tree_40a': 'Egrasi; uma madeira com muitos usos. Cresce em toda a região de Hmoson.',
    'STR_DIC_E_tree_n_c_20b': 'Tora de Ulmus; uma tora de uma árvore famosa por sua densidade. Pode ser encontrado perto do [%dic:STR_DIC_W_LF3_SZ_20].',
    'STR_DIC_E_LF3_Q1612': 'Trabalho de pesquisa; um artigo de pesquisa que contém os resultados de pesquisas importantes feitas na floresta.',
    'STR_DIC_E_QUEST_9640a': 'Árvore Rotron Amaldiçoada; madeira rara com alta ressonância etérea.',
    'STR_DIC_E_LF3_Work_production': 'Bancada de Artesanato; uma bancada no [%dic:STR_DIC_W_DC1_5] usada para confeccionar itens de Artesanato.',
    'STR_DIC_E_Q11215': 'General Guardião do Templo das Escalas; refere-se ao General Guardião que outrora ocupou o Templo das Escalas.',
    'STR_DIC_M_QUEST_11201': 'General Guardião do Altar; o General Guardião que protege o altar [%dic:STR_DIC_W_LF4_SZ_E2].',
    'STR_DIC_M_QUEST_21228': 'General Guardião da Cidadela de Vorgaltem; o General Guardião que protege a fortaleza [%dic:STR_DIC_W_DF4_SZ_B1].',
    'STR_DIC_M_IDDreadgion_02_Adjutant': 'Oficiais Adjuntos; oficiais que auxiliam os comandantes da Dredgion Chantra.',
    'STR_DIC_M_37001all': 'Soldados veteranos de elite da guarnição Kaidan Krall guardando [%dic:STR_DIC_FLA22].',
    'STR_DIC_M_37002all': 'Guarnição de Elite; Soldados Tursin Krall de Elite guardando [%dic:STR_DIC_FLA23].',
    'STR_DIC_M_37102': 'Tursin de Elite; Krall veteranos de elite guardando [%dic:STR_DIC_FLA23].',
}

# Padrões contextuais regex para UI e Mensagens
CONTEXTUAL_PATTERNS = [
    # Recuperação de cambaleio (Stagger)
    (re.compile(r'Você não é mais impressionante\.', re.IGNORECASE), 'Você se recuperou do cambaleio.'),
    (re.compile(r'(\[%SkillTarget\]|\b\w+\b) não é mais impressionante\.', re.IGNORECASE), r'\1 se recuperou do cambaleio.'),

    # Recuperação de queda (Stumble)
    (re.compile(r'Você não está mais chocado\.', re.IGNORECASE), 'Você levantou-se da queda.'),
    (re.compile(r'(\[%SkillTarget\]|\b\w+\b) não está mais chocado\.', re.IGNORECASE), r'\1 levantou-se da queda.'),
    (re.compile(r'Você caiu de choque depois de usar', re.IGNORECASE), 'Você tropeçou e caiu após usar'),
    (re.compile(r'caiu de choque porque ele usou', re.IGNORECASE), 'tropeçou e caiu porque usou'),

    # Cancelamentos e Conflitos
    (re.compile(r'foi cancelad[oa] como (\[%SkillTarget\]|você)', re.IGNORECASE), r'foi cancelado porque \1'),
    (re.compile(r'foi cancelada como (%1|\w+) já está sob', re.IGNORECASE), r'foi cancelada porque \1 já está sob'),

    # Resíduos de interface
    (re.compile(r'\bparte n inferior\b', re.IGNORECASE), 'parte inferior'),
    (re.compile(r'\bparte n superior\b', re.IGNORECASE), 'parte superior'),
    (re.compile(r'\bcardápio Martelo de Siel\b', re.IGNORECASE), 'menu Martelo de Siel'),
    (re.compile(r'\bcardápio do sistema\b', re.IGNORECASE), 'menu do sistema'),
    (re.compile(r'\bcardápio do jogo\b', re.IGNORECASE), 'menu do jogo'),

    # Ortografia sistemática ágora -> agora
    (re.compile(r'\bágora\b'), 'agora'),
    (re.compile(r'\bÁgora\b'), 'Agora'),

    # Protetores de ombro
    (re.compile(r'\bdeve\s*-\s*ser\b', re.IGNORECASE), 'Protetores de Ombro'),
]

# Padrões de Legião aplicados em STR_GUILD_* (client_strings_msg.xml)
GUILD_TO_LEGION_PATTERNS = [
    (re.compile(r'\bà sua Guilda\b'), 'à sua Legião'),
    (re.compile(r'\bda sua Guilda\b'), 'da sua Legião'),
    (re.compile(r'\bna sua Guilda\b'), 'na sua Legião'),
    (re.compile(r'\bpara sua Guilda\b'), 'para sua Legião'),
    (re.compile(r'\bSua Guilda\b'), 'Sua Legião'),
    (re.compile(r'\bsua Guilda\b'), 'sua Legião'),
    (re.compile(r'\bda Guilda\b'), 'da Legião'),
    (re.compile(r'\bà Guilda\b'), 'à Legião'),
    (re.compile(r'\bna Guilda\b'), 'na Legião'),
    (re.compile(r'\buma Guilda\b'), 'uma Legião'),
    (re.compile(r'\bA Guilda\b'), 'A Legião'),
    (re.compile(r'\ba Guilda\b'), 'a Legião'),
    (re.compile(r'\barmazém da Guilda\b'), 'depósito da Legião'),
    (re.compile(r'\barmazém Guilda\b'), 'depósito da Legião'),
    (re.compile(r'\bmembros da Guilda\b'), 'membros da Legião'),
    (re.compile(r'\bmembro da Guilda\b'), 'membro da Legião'),
    (re.compile(r'\bconvite da Guilda\b'), 'convite da Legião'),
    (re.compile(r'\bconvites da Guilda\b'), 'convites da Legião'),
    (re.compile(r'\bnível da Guilda\b'), 'nível da Legião'),
    (re.compile(r'\bponto da Guilda\b'), 'pontos de Legião'),
    (re.compile(r'\bGuilda\b'), 'Legião'),
    (re.compile(r'\bguilda\b'), 'legião'),
]

def clean_body_text(name, body, fname):
    """Aplica regras de limpeza e refinamento contextuais no corpo da string."""
    modified = False
    new_body = body

    # 1. Checa correções exatas pelo nome
    if fname == 'client_strings_ui.xml' and name in UI_EXACT_FIXES:
        return UI_EXACT_FIXES[name], True
    if fname == 'client_strings_msg.xml' and name in MSG_EXACT_FIXES:
        return MSG_EXACT_FIXES[name], True
    if fname == 'client_strings_dic_etc.xml' and name in DIC_ETC_EXACT_FIXES:
        return DIC_ETC_EXACT_FIXES[name], True

    # 2. Padrões contextuais gerais
    for regex, repl in CONTEXTUAL_PATTERNS:
        if regex.search(new_body):
            new_body = regex.sub(repl, new_body)
            modified = True

    # 3. Padrões de Legião para strings de sistema STR_GUILD_* ou STR_NO_GUILD_* ou STR_CANT_USE_GUILD_*
    if fname in ('client_strings_msg.xml', 'client_strings_ui.xml'):
        if name.startswith('STR_GUILD_') or name.startswith('STR_NO_GUILD_') or name.startswith('STR_CANT_USE_GUILD_'):
            for regex, repl in GUILD_TO_LEGION_PATTERNS:
                if regex.search(new_body):
                    new_body = regex.sub(repl, new_body)
                    modified = True

    return new_body, modified

def process_file(filepath, apply_changes=False):
    fname = os.path.basename(filepath)
    print(f"\n--- Processando {fname} ---")

    with open(filepath, 'rb') as f:
        raw_bytes = f.read()

    # Sanitização defensiva de múltiplos BOMs
    bom_count = 0
    while raw_bytes.startswith(b'\xff\xfe'):
        bom_count += 1
        raw_bytes = raw_bytes[2:]
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        bom_count += 1
        raw_bytes = raw_bytes[3:]
        content = raw_bytes.decode('utf-8', errors='replace')
    else:
        try:
            content = raw_bytes.decode('utf-16-le')
        except:
            content = raw_bytes.decode('utf-8', errors='replace')

    # Regex para capturar e substituir nós <string> mantendo identação e tags intactas
    # Padrão flexível para cobrir <string> ou <string_tip>
    node_pattern = re.compile(
        r'(<(?:string|string_tip)>[\s\S]*?<name>([^<]+)</name>[\s\S]*?<body>)([\s\S]*?)(</body>[\s\S]*?</(?:string|string_tip)>)',
        re.MULTILINE
    )

    exact_count = 0
    context_count = 0

    def replacer(match):
        nonlocal exact_count, context_count
        header = match.group(1)
        name = match.group(2).strip()
        body = match.group(3)
        footer = match.group(4)

        new_body, modified = clean_body_text(name, body, fname)
        if modified:
            if fname == 'client_strings_ui.xml' and name in UI_EXACT_FIXES:
                exact_count += 1
            elif fname == 'client_strings_msg.xml' and name in MSG_EXACT_FIXES:
                exact_count += 1
            elif fname == 'client_strings_dic_etc.xml' and name in DIC_ETC_EXACT_FIXES:
                exact_count += 1
            else:
                context_count += 1
            return header + new_body + footer
        return match.group(0)

    new_content = node_pattern.sub(replacer, content)
    total_modified = exact_count + context_count

    print(f"[{fname}]: {exact_count} substituições exatas | {context_count} modificações contextuais (Total: {total_modified})")

    if apply_changes and total_modified > 0:
        # Validação sintática XML em memória antes de gravar em disco
        test_content = re.sub(r'<\?xml[^>]*\?>', '<?xml version="1.0" encoding="utf-8"?>', new_content, count=1)
        try:
            test_root = ET.fromstring(test_content.encode('utf-8'))
            node_count = len(test_root.findall('.//string')) or len(test_root.findall('.//string_tip'))
            print(f"[SUCESSO] {fname} é sintaticamente válido ({node_count} nós).")
        except Exception as e:
            print(f"[ERRO CRÍTICO] Falha sintática ao validar {fname}: {e}")
            sys.exit(1)

        # Grava com exatamente 1 único BOM UTF-16 LE
        out_bytes = b'\xff\xfe' + new_content.encode('utf-16-le')
        with open(filepath, 'wb') as f:
            f.write(out_bytes)
        print(f"[CONCLUÍDO] {fname} gravado com sucesso (UTF-16 LE com BOM único).")

    return total_modified

def main():
    parser = argparse.ArgumentParser(description="Refinamento de Nomes e Strings de UI / Mensagens (PT-BR)")
    parser.add_argument('--aplicar', action='store_true', help="Aplica as alterações nos arquivos XML")
    parser.add_argument('--verificar', action='store_true', help="Apenas simula e exibe métricas")
    args = parser.parse_args()

    apply_changes = args.aplicar
    mode_str = "APLICAÇÃO REAL" if apply_changes else "VERIFICAÇÃO / SIMULAÇÃO"
    print("=" * 70)
    print(f"AUDITORIA E REFINAMENTO DE UI E MENSAGENS ({mode_str})")
    print("=" * 70)

    target_files = [
        'client_strings_ui.xml',
        'client_strings_msg.xml',
        'client_strings_dic_etc.xml',
        'client_strings_etc.xml',
        'stringtable_tip.xml'
    ]

    total_all = 0
    file_stats = {}

    for fname in target_files:
        fpath = os.path.join(STRINGS_DIR, fname)
        if os.path.isfile(fpath):
            count = process_file(fpath, apply_changes=apply_changes)
            file_stats[fname] = count
            total_all += count

    print("\n" + "=" * 70)
    print(f"RESUMO FINAL: {total_all} STRINGS DE UI/MENSAGENS REFINADAS")
    for fname, count in file_stats.items():
        print(f"  {fname:<30}: {count:>5} modificações")
    print("=" * 70)

if __name__ == '__main__':
    main()
