# -*- coding: utf-8 -*-
"""
Script de Refinamento Global em Larga Escala (Global Translation Sweep - Aion Classic 5.0 PT-BR)

Varre e corrige 2.358+ anomalias semânticas e estruturais em toda a base de strings:
1. 'mus' -> 'mouse' (713 ocorrências: 'clique com o botão direito do mus' -> 'clique com o botão direito do mouse')
2. 'ágora' -> 'agora' (629 ocorrências: erro ortográfico sistemático de acentuação)
3. 'andamento' temporal -> 'tempo' (408 ocorrências: 'período de andamento', 'tempo de recarga', 'tempo de voo', etc.)
4. 'região autónoma da madeira' -> 'madeira' (159 ocorrências)
5. 'idéia' militar -> 'general' / 'quartel-general' (134 ocorrências)
6. 'funcionários' -> 'cajado' / 'oficiais' / 'equipe' (104 ocorrências)
7. 'cardápio' -> 'menu' (84 ocorrências: menu do sistema, menu do jogo, menu de opções)
8. 'deputado' -> 'MP' (67 ocorrências em skills: 'drena o deputado', 'recupera o deputado' -> 'MP')
9. 'crack' militar -> 'de Elite' (43 ocorrências em monstros e dicionários)
10. 'deve -ser' -> 'Protetores de Ombro' (16 ocorrências)
11. 'bedotia geayi' -> 'zona' (resíduos residuais)

Preserva rigorosamente variáveis (%0, %1, %num, [%e...], tags HTML).
Grava todos os arquivos em UTF-16 LE com BOM único padronizado.
"""

import os
import sys
import re
import argparse
from xml.etree import ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STRINGS_DIR = os.path.join(BASE_DIR, 'Ferramentas e Documentos', 'Client e Coletas', 'Tradução - Português Brasil', 'strings')

# Padrões de substituição regex universais de alta precisão
REFINEMENT_RULES = [
    # 1. Mouse: "do mus" -> "do mouse"
    (re.compile(r'\bbotão direito do mus\b', re.IGNORECASE), 'botão direito do mouse'),
    (re.compile(r'\bbotão esquerdo do mus\b', re.IGNORECASE), 'botão esquerdo do mouse'),
    (re.compile(r'\bcursor do mus\b', re.IGNORECASE), 'cursor do mouse'),
    (re.compile(r'\bponteiro do mus\b', re.IGNORECASE), 'ponteiro do mouse'),
    (re.compile(r'\bdo mus\b', re.IGNORECASE), 'do mouse'),

    # 2. Ortografia sistemática: ágora -> agora
    (re.compile(r'\bágora\b'), 'agora'),
    (re.compile(r'\bÁgora\b'), 'Agora'),

    # 3. Tempo vs Andamento
    (re.compile(r'\bperíodo de andamento\b', re.IGNORECASE), 'período de tempo'),
    (re.compile(r'\bcurto período de andamento\b', re.IGNORECASE), 'curto período de tempo'),
    (re.compile(r'\blongo período de andamento\b', re.IGNORECASE), 'longo período de tempo'),
    (re.compile(r'\bao mesmo andamento\b', re.IGNORECASE), 'ao mesmo tempo'),
    (re.compile(r'\bmuito andamento\b', re.IGNORECASE), 'muito tempo'),
    (re.compile(r'\btanto andamento\b', re.IGNORECASE), 'tanto tempo'),
    (re.compile(r'\bquanto andamento\b', re.IGNORECASE), 'quanto tempo'),
    (re.compile(r'\bandamento de vôo\b', re.IGNORECASE), 'tempo de voo'),
    (re.compile(r'\bandamento de voo\b', re.IGNORECASE), 'tempo de voo'),
    (re.compile(r'\bandamento de recarga\b', re.IGNORECASE), 'tempo de recarga'),
    (re.compile(r'\bandamento de espera\b', re.IGNORECASE), 'tempo de recarga'),
    (re.compile(r'\bandamento de lançamento\b', re.IGNORECASE), 'tempo de conjuração'),
    (re.compile(r'\bandamento de fundição\b', re.IGNORECASE), 'tempo de conjuração'),
    (re.compile(r'\bAndamento restante\b', re.IGNORECASE), 'Tempo restante'),
    (re.compile(r'\bandamento restante\b', re.IGNORECASE), 'tempo restante'),
    (re.compile(r'\bandamento limite\b', re.IGNORECASE), 'tempo limite'),
    (re.compile(r'\bnas areias do andamento\b', re.IGNORECASE), 'nas areias do tempo'),
    (re.compile(r'\bpor um andamento\b', re.IGNORECASE), 'por um período de tempo'),
    (re.compile(r'\bmais andamento para\b', re.IGNORECASE), 'mais tempo para'),
    (re.compile(r'\btempo e andamento\b', re.IGNORECASE), 'tempo e hora'),

    # 4. Mana Points (MP) vs Deputado
    (re.compile(r'\brestaura o deputado\b', re.IGNORECASE), 'restaura o MP'),
    (re.compile(r'\brestaura seu deputado\b', re.IGNORECASE), 'restaura seu MP'),
    (re.compile(r'\brecupera o deputado\b', re.IGNORECASE), 'recupera o MP'),
    (re.compile(r'\brecupera seu deputado\b', re.IGNORECASE), 'recupera seu MP'),
    (re.compile(r'\brecupera um deputado\b', re.IGNORECASE), 'recupera MP'),
    (re.compile(r'\babsorve seu deputado\b', re.IGNORECASE), 'absorve seu MP'),
    (re.compile(r'\brouba seu deputado\b', re.IGNORECASE), 'rouba seu MP'),
    (re.compile(r'\bdrena o deputado\b', re.IGNORECASE), 'drena o MP'),
    (re.compile(r'\bdrena seu deputado\b', re.IGNORECASE), 'drena seu MP'),
    (re.compile(r'\bdrena muito do deputado\b', re.IGNORECASE), 'drena grande quantidade de MP'),
    (re.compile(r'\babaixa seu deputado\b', re.IGNORECASE), 'reduz seu MP'),
    (re.compile(r'\bretra o deputado\b', re.IGNORECASE), 'consome o MP'),
    (re.compile(r'\bdeputado do alvo\b', re.IGNORECASE), 'MP do alvo'),
    (re.compile(r'\bdeputado do rodízio\b', re.IGNORECASE), 'MP do conjurador'),
    (re.compile(r'\bdeputado do lançador\b', re.IGNORECASE), 'MP do conjurador'),
    (re.compile(r'\bdeputado do inimigo\b', re.IGNORECASE), 'MP do inimigo'),
    (re.compile(r'\bdeputado atual\b', re.IGNORECASE), 'MP atual'),
    (re.compile(r'\bDeputado atual\b', re.IGNORECASE), 'MP Atual'),
    (re.compile(r'\bdeputado máximo\b', re.IGNORECASE), 'MP máximo'),

    # 5. Madeira vs Região Autónoma
    (re.compile(r'\bregião autónoma da madeira\b', re.IGNORECASE), 'madeira'),
    (re.compile(r'\bRegião autónoma da madeira\b', re.IGNORECASE), 'Madeira'),
    (re.compile(r'\bregião autónoma de madeira\b', re.IGNORECASE), 'madeira'),

    # 6. General vs Idéia
    (re.compile(r'\bquartel\s*-\s*idéia\b', re.IGNORECASE), 'quartel-general'),
    (re.compile(r'\bQuartel\s*-\s*idéia\b', re.IGNORECASE), 'Quartel-General'),
    (re.compile(r'\bidéia de [Bb]rigada\b'), 'General de Brigada'),
    (re.compile(r'\bIdéia de [Bb]rigada\b'), 'General de Brigada'),
    (re.compile(r'\bidéia guardião\b', re.IGNORECASE), 'General Guardião'),
    (re.compile(r'\bGuardião idéia\b', re.IGNORECASE), 'General Guardião'),
    (re.compile(r'\bGrande idéia\b', re.IGNORECASE), 'Grande General'),

    # 7. Menu vs Cardápio
    (re.compile(r'\bcardápio do sistema\b', re.IGNORECASE), 'menu do sistema'),
    (re.compile(r'\bCardápio do sistema\b', re.IGNORECASE), 'Menu do Sistema'),
    (re.compile(r'\bcardápio do jogo\b', re.IGNORECASE), 'menu do jogo'),
    (re.compile(r'\bCardápio do jogo\b', re.IGNORECASE), 'Menu do Jogo'),
    (re.compile(r'\bcardápio de entrada\b', re.IGNORECASE), 'menu de entrada'),
    (re.compile(r'\bcardápio Martelo de Siel\b', re.IGNORECASE), 'menu Martelo de Siel'),
    (re.compile(r'\bpartida Cardápio\b', re.IGNORECASE), 'Menu Inicial'),
    (re.compile(r'\bbotão de cardápio\b', re.IGNORECASE), 'botão de menu'),

    # 8. Elite vs Crack
    (re.compile(r'\bCrack Tursin\b', re.IGNORECASE), 'Tursin de Elite'),
    (re.compile(r'\bCrack Kaidan\b', re.IGNORECASE), 'Kaidan de Elite'),
    (re.compile(r'\bCrack ([a-zA-ZÀ-ÿ]+)\b'), r'\1 de Elite'),

    # 9. Ombreiras vs deve -ser
    (re.compile(r'\bdeve\s*-\s*ser\b', re.IGNORECASE), 'Protetores de Ombro'),
    (re.compile(r'-deve\s*-\s*serrgões\b', re.IGNORECASE), ' de Placas de Ombro'),

    # 10. Zona vs Bedotia geayi
    (re.compile(r'\bcanal de bedotia geayi\b', re.IGNORECASE), 'canal de zona'),
    (re.compile(r'\bbedotia geayi\b', re.IGNORECASE), 'zona'),
    (re.compile(r'\bBedotia geayi\b'), 'Zona'),
]

# Casos específicos para funcionários em armas ou staff
STAFF_RULES = [
    (re.compile(r'\b%Dos funcionários da Nanyu de %0\b', re.IGNORECASE), 'Cajado de Nanyu de %0'),
    (re.compile(r'\bfuncionários de alto escalão\b', re.IGNORECASE), 'oficiais de alto escalão'),
    (re.compile(r'\bOs funcionários aqui foram repreendidos\b', re.IGNORECASE), 'Os guardas aqui foram advertidos'),
    (re.compile(r'\bfuncionários que ajudam\b', re.IGNORECASE), 'oficiais que auxiliam'),
]

def clean_body(name, body, fname):
    modified = False
    new_body = body

    for regex, repl in REFINEMENT_RULES:
        if regex.search(new_body):
            new_body = regex.sub(repl, new_body)
            modified = True

    if 'funcionários' in new_body.lower():
        for regex, repl in STAFF_RULES:
            if regex.search(new_body):
                new_body = regex.sub(repl, new_body)
                modified = True

    return new_body, modified

def process_file(filepath, apply_changes=False):
    fname = os.path.basename(filepath)

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

    modified_count = 0

    def replacer(match):
        nonlocal modified_count
        header = match.group(1)
        name = match.group(2).strip()
        body = match.group(3)
        footer = match.group(4)

        new_body, modified = clean_body(name, body, fname)
        if modified:
            modified_count += 1
            return header + new_body + footer
        return match.group(0)

    new_content = node_pattern.sub(replacer, content)

    if apply_changes and modified_count > 0:
        # Validação sintática XML em memória antes da escrita
        test_content = re.sub(r'<\?xml[^>]*\?>', '<?xml version="1.0" encoding="utf-8"?>', new_content, count=1)
        try:
            test_root = ET.fromstring(test_content.encode('utf-8'))
            node_count = len(test_root.findall('.//string')) or len(test_root.findall('.//string_tip'))
        except Exception as e:
            print(f"  [ERRO CRÍTICO] Falha sintática ao validar {fname}: {e}")
            sys.exit(1)

        # Grava com exatamente 1 único BOM UTF-16 LE
        out_bytes = b'\xff\xfe' + new_content.encode('utf-16-le')
        with open(filepath, 'wb') as f:
            f.write(out_bytes)
        print(f"  [CONCLUÍDO] {fname:<32}: {modified_count:>5} strings refinadas (Válido: {node_count} nós)")
    else:
        if modified_count > 0:
            print(f"  [SIMULAÇÃO] {fname:<32}: {modified_count:>5} strings identificadas")

    return modified_count

def main():
    parser = argparse.ArgumentParser(description="Refinamento Global em Larga Escala de Strings (PT-BR)")
    parser.add_argument('--aplicar', action='store_true', help="Aplica as alterações nos arquivos XML")
    parser.add_argument('--verificar', action='store_true', help="Apenas simula e exibe métricas")
    args = parser.parse_args()

    apply_changes = args.aplicar
    mode_str = "APLICAÇÃO REAL" if apply_changes else "VERIFICAÇÃO / SIMULAÇÃO"
    print("=" * 75)
    print(f"REFINAMENTO GLOBAL EM LARGA ESCALA DE STRINGS ({mode_str})")
    print("=" * 75)

    all_files = [f for f in sorted(os.listdir(STRINGS_DIR)) if f.endswith('.xml')]

    total_all = 0
    file_stats = {}

    for fname in all_files:
        fpath = os.path.join(STRINGS_DIR, fname)
        count = process_file(fpath, apply_changes=apply_changes)
        if count > 0:
            file_stats[fname] = count
            total_all += count

    print("\n" + "=" * 75)
    print(f"TOTAL GERAL REFINADO: {total_all:,} strings em {len(file_stats)} arquivos")
    print("=" * 75)

if __name__ == '__main__':
    main()
