# -*- coding: utf-8 -*-
"""
Script de Refinamento de Qualidade - Mensagens do Sistema, Dicas (Tips), Níveis e Falas (Aion Classic 5.0 PT-BR)

Foco exclusivo em:
1. Dicas de Tela de Carregamento (stringtable_tip.xml):
   - Correção de teclas e atalhos corrompidos (usando entidades XML &lt; e &gt;):
     * '&lt;geada-z&gt;' -> '&lt;Shift + Z&gt;'
     * '&lt;flue-f12&gt;' -> '&lt;Shift + F12&gt;'
     * '&lt;baw&gt;' -> '&lt;Tab&gt;'
     * '&lt;Mumlock&gt;' -> '&lt;NumLock&gt;'
     * 'Ctrl-Agora' -> 'Ctrl + Botão Direito'
   - Correção de termos bizarros:
     * 'do mus' -> 'do mouse'
     * 'Fuir 2 armas' -> 'Fundir duas armas'
     * 'Manatone' / 'Manatones' -> 'Pedra de Mana' / 'Pedras de Mana'
     * 'Encantment Pedra' -> 'Pedra de Encantamento'
     * 'tomada encantadora ou de Manatone' -> 'encantamento ou inserção de Pedras de Mana'
     * 'Ao encantador, você deve usar' -> 'Ao encantar, você deve usar'
     * 'quanto andamento' / 'período de andamento' / 'ao mesmo andamento' -> 'quanto tempo' / 'período de tempo' / 'ao mesmo tempo'
     * 'formar uma festa' -> 'formar um grupo'
     * 'cardápio Iniciar' -> 'Menu Iniciar'
     * 'e -correio' / 'e-mails' -> 'mensagens de correio'
     * 'bedotia geayi' -> 'canal de servidor'
     * 'daevasas' -> 'Daevas'
     * 'as brecha são corredores... número de caracteres' -> 'as fendas são passagens... número de personagens'
     * 'as dragiões se interessem pela corrida' -> 'as Dredgions ataquem a facção'
     * 'gêiseador' / 'gêisere' -> 'gêiser'

2. Mensagens do Sistema (client_strings_msg.xml):
   - Eliminação da aberração 'bedotia geayi' (67 ocorrências) -> 'zona' (zona segura, zona de batalha, zona sem lei, canal de zona, etc.)
   - Correção de 'andamento' no sentido temporal:
     * 'muito andamento' -> 'muito tempo'
     * 'tanto andamento' -> 'tanto tempo'
     * 'Andamento restante' / 'andamento restante' -> 'Tempo restante' / 'tempo restante'
     * 'andamento de vôo' -> 'tempo de voo'
     * 'andamento de espera' -> 'tempo de espera'
     * 'andamento limite' -> 'tempo limite'
     * 'poupe em um local seguro' -> 'pouse em um local seguro'
   - Restauração de Mana / MP:
     * 'O deputado de [%SkillCaster]' -> 'O MP de [%SkillCaster]'
   - Correção de 'Manatone' -> 'Pedra de Mana'
   - Correção de 'do mus' -> 'do mouse'
   - Correção de 'outros caracteres' -> 'outros personagens'

3. Zonas e Níveis (client_strings_level.xml):
   - 'Caverna de região autónoma da madeira de Kasaka' -> 'Caverna de Madeira de Kasaka'
   - 'há muito andamento' -> 'há muito tempo'
   - 'Já faz muito andamento' -> 'Já faz muito tempo'

4. Falas de NPCs e Fofocas (client_strings_gossip.xml):
   - Eliminação de 'ágora' -> 'agora' (25 ocorrências)
   - 'nas areias do andamento' -> 'nas areias do tempo'
   - 'tanto andamento' -> 'tanto tempo'
   - 'muito andamento' -> 'muito tempo'
   - 'mais andamento para' -> 'mais tempo para'

5. Enciclopédia Restante (client_strings_dic_etc.xml):
   - 'ágora' -> 'agora'
   - 'andamento' temporal -> 'tempo'
"""

import os
import sys
import re
import argparse
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')

# Correções exatas para stringtable_tip.xml (usando entidades XML &lt; e &gt;)
TIP_EXACT_FIXES = {
    'STR_TIP_BASIC014': 'Dica: alterne a corrida automática pressionando &lt;NumLock&gt;.',
    'STR_TIP_BASIC015': 'História: O Senhor Empírio do Espaço, Israphel, defendeu negociações de paz com os Balaur.\nQuando a torre ruiu, ele se sacrificou para proteger Atreia.',
    'STR_TIP_BASIC016': 'Dica: cidades e aldeias têm caixas de correio onde você pode enviar e receber correspondências.',
    'STR_TIP_BASIC017': 'Dica: cair de uma grande altura causará dano ao seu personagem ou até mesmo a morte.',
    'STR_TIP_BASIC018': 'Dica: você ascenderá como Daeva e escolherá sua subclasse definitiva ao atingir o nível 10.',
    'STR_TIP_BASIC019': 'Dica: a barra ao redor do botão de voo (ícone de asas) exibe o tempo de voo restante.',
    'STR_TIP_BASIC020': 'Dica: os Daevas podem planar pressionando a &lt;Barra de Espaço&gt; durante um salto.',
    'STR_TIP_BASIC021': 'Dica: zonas muito povoadas podem possuir múltiplos canais. Membros do mesmo grupo devem estar no mesmo canal.',
    'STR_TIP_BASIC022': 'Dica: o botão de voo alterna entre voar e pousar. Passar o mouse sobre ele mostra os controles e o tempo de voo restante.',
    'STR_TIP_BASIC027': 'Dica: o botão de menu na parte inferior da tela oferece acesso a todas as janelas do jogo.\nAtalho padrão &lt;Esc&gt; ou &lt;O&gt;.',
    'STR_TIP_BASIC028': 'Dica: líderes de grupo podem marcar alvos clicando com o botão direito do mouse, usando comandos ou atalhos numéricos.',
    'STR_TIP_BASIC031': 'Dica: para visualizar o mapa e a tela do jogo ao mesmo tempo, use a sobreposição de mapa transparente.\nAtalho padrão &lt;M&gt; ou &lt;N&gt;.',
    'STR_TIP_BASIC032': 'Dica: para marcar coordenadas no mapa e compartilhá-las no chat, clique com Ctrl + Botão Direito no mapa.',
    'STR_TIP_BASIC033': 'Dica: clicar com o botão direito do mouse em uma marca criada no mapa abre o menu de opções do ponto.',
    'STR_TIP_BASIC036': 'Dica: para visualizar as classificações atuais de Legiões ou personagens, use a janela de Ranking.\nAtalho padrão &lt;J&gt;.',
    'STR_TIP_BASIC046': 'Dica: itens de materiais agrupados podem ser divididos em materiais de grau correspondente.',
    'STR_TIP_BASIC047': 'Dica: Fundir duas armas de duas mãos combina seus atributos e adiciona slots de Pedra de Mana.\nVisite o oficial de fusão nas capitais.',
    'STR_TIP_BASIC050': 'Dica: certos comerciantes alugam equipamentos especiais que podem ser utilizados por um período de tempo determinado.',
    'STR_TIP_BASIC051': 'Dica: itens alugados não podem ser aprimorados com Pedras de Mana ou Pedras de Encantamento, expirando após o término do tempo de uso.',
    'STR_TIP_BASIC052': 'Dica: o uso de suplementos aumenta a taxa de sucesso no encantamento e na inserção de Pedras de Mana.\nSuplementos são vendidos nas cidades.',
    'STR_TIP_BASIC053': 'Dica: ao encantar, utilize suplementos de nível correspondente ao equipamento para maximizar as chances.',
    'STR_TIP_BASIC055': 'Dica: Balaurea possui correntes de vento (Windstreams) para deslocamento rápido.\nPlana sobre elas para ingressar na rota.',
    'STR_TIP_BASIC056': 'Dica: encontre grupos facilmente usando o atalho &lt;Shift + V&gt; para abrir a janela Localizar Grupo.',
    'STR_TIP_BASIC058': 'Dica: verifique o tempo de recarga de instâncias pelo menu de informações de instância ou pelo comando /checkentry.',
    'STR_TIP_BASIC059': 'Dica: você pode verificar seu correio regular na caixa de correio das cidades mesmo sem avisos urgentes na tela.',
    'STR_TIP_BASIC060': 'Dica: esvazie sua caixa de correio periodicamente para não impedir a chegada de novas correspondências.',
    'STR_TIP_BASIC061': 'Dica: no Corretor Comercial (Broker), clicar com o botão direito do mouse em um item insere seu nome diretamente na busca.',
    'STR_TIP_BASIC063': 'Dica: ao se tornar um mentor, você pode formar um grupo com personagens mais de 10 níveis abaixo do seu para auxiliá-los.',
    'STR_TIP_ADVANCED001': 'Dica: as Fendas (Rifts) são passagens para o território inimigo com limite no número de personagens que podem atravessar.',
    'STR_TIP_ADVANCED002': 'Dica: trave a altitude de voo pressionando a tecla &lt;Scroll Lock&gt;.',
    'STR_TIP_ADVANCED007': 'Dica: você pode consumir alimentos e bebidas simultaneamente para acumular diferentes bônus.',
    'STR_TIP_ADVANCED011': 'Dica: engastar Pedras de Mana Antigas requer equipamentos adequados e auxílio de especialistas nas capitais.',
    'STR_TIP_ADVANCED015': 'Dica: você pode alternar rapidamente entre dois conjuntos de armas utilizando o atalho &lt;Shift + Z&gt;.',
    'STR_TIP_ADVANCED019': 'Dica: alterne entre alvos inimigos próximos pressionando a tecla &lt;Tab&gt;.',
    'STR_TIP_ADVANCED023': 'Dica: ao atingir o nível 3, uma Legião pode registrar seu próprio emblema personalizado no Conselho da Legião.',
    'STR_TIP_ADVANCED024': 'Dica: os Pontos Divinos (DP) são mantidos enquanto você estiver conectado e só decaem após logout prolongado.',
    'STR_TIP_ADVANCED025': 'Dica: habilidades bem cronometradas podem interromper conjurações de feitiços inimigos.',
    'STR_TIP_ADVANCED030': 'Dica: enquanto estiver sob o efeito de transformação em animal, habilidades normais ficam temporariamente bloqueadas.',
    'STR_TIP_ADVANCED031': 'Dica: navios de guerra Dredgion atacam com mais frequência a facção que detém a maior taxa de influência no Abismo.',
    'STR_TIP_ADVANCED064': 'Dica: para ocultar outros personagens na tela e aumentar o desempenho, utilize o atalho &lt;Shift + F12&gt;.',
    'STR_TIP_ADVANCED087': 'Dica: para consultar o tempo restante, vínculos e ressurreições disponíveis em um Kisk, passe o mouse sobre ele.',
    'STR_TIP_ADVANCED088': 'Dica: removedores de Pedra de Mana nas cidades permitem extrair pedras engastadas para inserir novas.',
    'STR_TIP_ADVANCED099': 'Dica: para desafiar outro jogador para um duelo, clique com o botão direito do mouse nele ou digite /duelo.',
    'STR_TIP_ADVANCED101': 'Dica: para enviar um sussurro privado, digite "/w NomeDoPersonagem mensagem" no chat.',
    'STR_TIP_ADVANCED104': 'Dica: após derrotar certos inimigos, correntes de ar ascendentes ou gêiseres podem se formar, permitindo planar a grandes alturas.',
}

# Correções exatas para client_strings_level.xml
LEVEL_EXACT_FIXES = {
    'STR_SZ_DF2_SUB_E4_3': 'Caverna de Madeira de Kasaka',
    'STR_ZONE_COMMENT_FF3': 'Essa área geotérmica costumava ser um terreno comum há muito tempo, mas o cataclismo a transformou.',
    'STR_ZONE_COMMENT_EE2': 'Já faz muito tempo desde que o povo construiu o castelo externo e começou a desenvolver a região.',
}

# Correções exatas para client_strings_msg.xml
MSG_EXACT_FIXES = {
    'STR_SKILL_SUCC_MPHeal_A_TO_SELF': 'O MP de [%SkillCaster] está sendo continuamente recuperado por [%SkillName].',
    'STR_MSG_WARNING_FLY': 'Você não tem muito tempo de voo restante. Por favor, pouse em um local seguro.',
    'STR_MSG_WARNING_FLY_Notice': 'Aviso! Você não tem muito tempo de voo restante.',
    'STR_PARTY_HE_BECOME_OFFLINE_TIMEOUT': '%0 está offline há muito tempo e foi removido do grupo.',
    'STR_PARTY_ALLIANCE_HE_LEAVED_PARTY_OFFLINE_TIMEOUT': '%0 está offline há muito tempo e foi expulso do grupo e da aliança.',
    'STR_GUILD_DISPERSE_TIME': 'Tempo restante até a dissolução: %DURATIONTIME0',
    'STR_MSG_IDElemental1_Prime_Debuff_Dispel': 'Clique com o botão direito do mouse no lacaio de Tuali para remover o dano da seiva.',
    'STR_REMOVE_ITEM_OPTION_FAR_FROM_NPC': 'Você está muito longe do NPC para remover a Pedra de Mana.',
    'STR_REMOVE_ITEM_OPTION_IT_CAN_NOT_BE_GIVEN_OPTION': 'A inserção / remoção de Pedra de Mana não é permitida para o item %0.',
    'STR_REMOVE_ITEM_OPTION_NO_OPTION_TO_REMOVE': '%0 não possui Pedras de Mana equipadas.',
    'STR_REMOVE_ITEM_OPTION_INVALID_OPTION_SLOT_NUMBER': 'O slot selecionado em %0 não possui Pedra de Mana equipada.',
    'STR_REMOVE_ITEM_OPTION_NOT_ENOUGH_GOLD': 'Você não possui Kinah suficiente para remover a Pedra de Mana de %0.',
    'STR_REMOVE_ITEM_OPTION_SUCCEED': 'Você removeu a Pedra de Mana de %0 com sucesso.',
    'STR_GIVE_ITEM_OPTION_NEED_IDENTIFY': '%0 deve ser avaliado antes que a Pedra de Mana possa ser inserida.',
    'STR_LOGIN_WARNING_GET_ITEM2': 'Após receber este item, ele não poderá ser transferido para outros personagens. Deseja continuar?',
}

# Regras regex contextuais para mensagens e falas
CONTEXTUAL_RULES = [
    # 1. Eliminação de 'bedotia geayi' -> 'zona'
    (re.compile(r'\bcanal de bedotia geayi\b', re.IGNORECASE), 'canal de zona'),
    (re.compile(r'\bbedotia geayi instanciada\b', re.IGNORECASE), 'zona instanciada'),
    (re.compile(r'\bbedotia geayi de ataque do andamento e do espaço\b', re.IGNORECASE), 'Fenda do Tempo e Espaço'),
    (re.compile(r'\bbedotia geayi de batalha\b', re.IGNORECASE), 'zona de batalha'),
    (re.compile(r'\bbedotia geayi neutra\b', re.IGNORECASE), 'zona neutra'),
    (re.compile(r'\bbedotia geayi segura\b', re.IGNORECASE), 'zona segura'),
    (re.compile(r'\bbedotia geayi sem lei\b', re.IGNORECASE), 'zona sem lei'),
    (re.compile(r'\bda Bedotia geayi\b', re.IGNORECASE), 'da Zona'),
    (re.compile(r'\bna Bedotia geayi\b', re.IGNORECASE), 'na Zona'),
    (re.compile(r'\bbedotia geayi\b', re.IGNORECASE), 'zona'),
    (re.compile(r'\bBedotia geayi\b'), 'Zona'),

    # 2. Correções de tempo no lugar de 'andamento'
    (re.compile(r'\bhá muito andamento\b', re.IGNORECASE), 'há muito tempo'),
    (re.compile(r'\bmuito andamento\b', re.IGNORECASE), 'muito tempo'),
    (re.compile(r'\btanto andamento\b', re.IGNORECASE), 'tanto tempo'),
    (re.compile(r'\bpor um andamento especificado\b', re.IGNORECASE), 'por um período determinado'),
    (re.compile(r'\(Andamento restante: (%[0-9]+ seg)\)', re.IGNORECASE), r'(Tempo restante: \1)'),
    (re.compile(r'\(andamento restante: (%[0-9]+ seg)\)', re.IGNORECASE), r'(tempo restante: \1)'),
    (re.compile(r'\bandamento restante\b', re.IGNORECASE), 'tempo restante'),
    (re.compile(r'\bAndamento restante\b', re.IGNORECASE), 'Tempo restante'),
    (re.compile(r'\bandamento de recarga\b', re.IGNORECASE), 'tempo de recarga'),
    (re.compile(r'\bandamento de espera\b', re.IGNORECASE), 'tempo de recarga'),
    (re.compile(r'\bandamento de vôo\b', re.IGNORECASE), 'tempo de voo'),
    (re.compile(r'\bandamento de voo\b', re.IGNORECASE), 'tempo de voo'),
    (re.compile(r'\bao mesmo andamento\b', re.IGNORECASE), 'ao mesmo tempo'),
    (re.compile(r'\bnas areias do andamento\b', re.IGNORECASE), 'nas areias do tempo'),
    (re.compile(r'\bmais andamento para\b', re.IGNORECASE), 'mais tempo para'),
    (re.compile(r'\bperíodo de andamento\b', re.IGNORECASE), 'período de tempo'),

    # 3. Manatone -> Pedra de Mana
    (re.compile(r'\bManatone Socketing\b', re.IGNORECASE), 'Engaste de Pedra de Mana'),
    (re.compile(r'\bum Manatone\b', re.IGNORECASE), 'uma Pedra de Mana'),
    (re.compile(r'\bo Manatone\b', re.IGNORECASE), 'a Pedra de Mana'),
    (re.compile(r'\bNenhum Manatone\b', re.IGNORECASE), 'Nenhuma Pedra de Mana'),
    (re.compile(r'\bNenhuma Manatone\b', re.IGNORECASE), 'Nenhuma Pedra de Mana'),
    (re.compile(r'\bManatone\b', re.IGNORECASE), 'Pedra de Mana'),
    (re.compile(r'\bManatones\b', re.IGNORECASE), 'Pedras de Mana'),

    # 4. Mouse
    (re.compile(r'\bdo mus\b', re.IGNORECASE), 'do mouse'),

    # 5. Ortografia ágora -> agora
    (re.compile(r'\bágora\b'), 'agora'),
    (re.compile(r'\bÁgora\b'), 'Agora'),

    # 6. E-correio
    (re.compile(r'\bum e-correio\b', re.IGNORECASE), 'uma mensagem de correio'),
    (re.compile(r'\be-correio\b', re.IGNORECASE), 'correio'),

    # 7. Personagens
    (re.compile(r'\boutros caracteres\b', re.IGNORECASE), 'outros personagens'),
]

def clean_node_body(name, body, fname):
    modified = False
    new_body = body

    # 1. Substituições exatas por nome
    if fname == 'stringtable_tip.xml' and name in TIP_EXACT_FIXES:
        return TIP_EXACT_FIXES[name], True
    if fname == 'client_strings_msg.xml' and name in MSG_EXACT_FIXES:
        return MSG_EXACT_FIXES[name], True
    if fname == 'client_strings_level.xml' and name in LEVEL_EXACT_FIXES:
        return LEVEL_EXACT_FIXES[name], True

    # 2. Regras contextuais
    for regex, repl in CONTEXTUAL_RULES:
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

    # Regex para nós <string> ou <string_tip>
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

        new_body, modified = clean_node_body(name, body, fname)
        if modified:
            if (fname == 'stringtable_tip.xml' and name in TIP_EXACT_FIXES) or \
               (fname == 'client_strings_msg.xml' and name in MSG_EXACT_FIXES) or \
               (fname == 'client_strings_level.xml' and name in LEVEL_EXACT_FIXES):
                exact_count += 1
            else:
                context_count += 1
            return header + new_body + footer
        return match.group(0)

    new_content = node_pattern.sub(replacer, content)
    total_modified = exact_count + context_count

    print(f"[{fname}]: {exact_count} exatas | {context_count} contextuais (Total: {total_modified})")

    if apply_changes and total_modified > 0:
        # Validação sintática XML em memória antes da escrita
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
    parser = argparse.ArgumentParser(description="Refinamento de Mensagens, Dicas (Tips), Níveis e Falas (PT-BR)")
    parser.add_argument('--aplicar', action='store_true', help="Aplica as alterações nos arquivos XML")
    parser.add_argument('--verificar', action='store_true', help="Apenas simula e exibe métricas")
    args = parser.parse_args()

    apply_changes = args.aplicar
    mode_str = "APLICAÇÃO REAL" if apply_changes else "VERIFICAÇÃO / SIMULAÇÃO"
    print("=" * 70)
    print(f"AUDITORIA E REFINAMENTO DE MSGS, TIPS, LEVEL E GOSSIP ({mode_str})")
    print("=" * 70)

    target_files = [
        'client_strings_msg.xml',
        'stringtable_tip.xml',
        'client_strings_level.xml',
        'client_strings_gossip.xml',
        'client_strings_dic_etc.xml',
        'client_strings_etc.xml'
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
    print(f"RESUMO FINAL: {total_all} STRINGS REFINADAS")
    for fname, count in file_stats.items():
        print(f"  {fname:<30}: {count:>5} modificações")
    print("=" * 70)

if __name__ == '__main__':
    main()
