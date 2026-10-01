#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refine_translation_grammar.py

Aprimora a qualidade gramatical e estilística da tradução PT-BR (Aion Classic 5.0):
- Corrige ordem de adjetivos em itens (ex: "Nobre Manoplas de Placas do Oficial Tático" -> "Manoplas Nobres de Placa do Oficial Tático")
- Corrige ordens possessivas invertidas de sets e patentes (do Oficial Tático, do Comandante, dos Namorados, do Rei Dragão)
- Corrige traduções literais em armas e armaduras (Staff traduzido como "Pessoal" -> "Cajado")
- Corrige termos de combate e magias ("Poderoso cobrança" -> "Investida Poderosa", "Parafuso de chama" -> "Dardo de Chamas")
- Corrige numerais romanos e capitalização em skills ("i I" -> "I", "i II" -> "II")
- Corrige nomes de facções icônicas ("Preto nuvem" -> "Nuvem Negra")
- Corrige adjetivos invertidos em monstros e NPCs ("Feroz cinza Worg" -> "Worg Cinzento Feroz")

Uso:
    python refine_translation_grammar.py --verificar
    python refine_translation_grammar.py --aplicar
"""

import os
import sys
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
STRINGS_DIR = os.path.join(REPO_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Tradução - Português Brasil", "strings")


def refine_item(text: str) -> str:
    if not text:
        return text

    # 1. Correções de Staff ("Pessoal" -> "Cajado")
    text = re.sub(r'\bNobre pessoal de Batua\b', 'Cajado Nobre de Batua', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal do Andarilho\b', 'Cajado do Andarilho', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal do Pôr do Sol\b', 'Cajado do Pôr do Sol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal escuro\b', 'Cajado Escuro', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal infame\b', 'Cajado Infame', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal de beatua\b', 'Cajado de Batua', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal de Perseguidor\b', 'Cajado do Perseguidor', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal de julgamento\b', 'Cajado do Julgamento', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTambém pessoal\b', 'Cajado Adicional', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBandeja de pessoal\b', 'Cajado de Bandeja', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPessoal Sultouched\b', 'Cajado Tocado pelo Sol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfabricar pessoal durável de Betua\b', 'fabricar cajado durável de Betua', text, flags=re.IGNORECASE)

    # 2. Correções de "Preto nuvem" -> "Nuvem Negra"
    text = re.sub(r'\bPreto nuvem Chapéu\b', 'Chapéu da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPreto nuvem Baú de Suprimentos\b', 'Baú de Suprimentos da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBilhete do\(a\) Preto nuvem comerciante\b', 'Bilhete do Mercador da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNobre Preto nuvem comerciante Kit de ferramentas\b', 'Kit de Ferramentas Nobre dos Mercadores Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSimples Preto nuvem comerciante Kit de ferramentas\b', 'Kit de Ferramentas Simples dos Mercadores Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPremium Preto nuvem comerciante Kit de ferramentas\b', 'Kit de Ferramentas Premium dos Mercadores Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPreto nuvem Musterguards\b', 'Protetores de Ombro da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPreto nuvem ombreistas\b', 'Ombreiras da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPreto nuvem Asa Pluma\b', 'Asa Pluma da Nuvem Negra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPreto nuvem Ilha\b', 'Ilha Nuvem Negra', text, flags=re.IGNORECASE)

    # 3. Possessivos invertidos com qualidade (Divino | Eterno)
    # Ex: "do Oficial Tático Divino Manoplas de Placas" -> "Manoplas Divinas de Placa do Oficial Tático"
    m = re.match(r'^(?:Nobre\s+)?(do|da|dos|das)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)?)\s+(Divin[oa]|Etern[oa])\s+(?:(Malha|Placas?|Tecido|Couro|Aço)\s+)?(.+)$', text)
    if m:
        prep, owner, adj, mat, slot = m.groups()
        is_nobre = text.startswith('Nobre ')
        slot_clean = slot.strip()
        mat_part = f' de {mat.capitalize().replace("Placas", "Placa")}' if mat else ''
        
        fem_plural = ['Manoplas', 'Luvas', 'Braçadeiras', 'Botas', 'Polainas', 'Ombreiras', 'Grevas', 'Brafoneiras']
        masc_plural = ['Sapatos', 'Calções', 'Protetores de Ombro', 'Protetores', 'Brogans']
        fem_sing = ['Túnica', 'Cota de Malha', 'Bandana', 'Espada', 'Adaga', 'Maça', 'Alabarda', 'Arma de Haste']
        
        adj_stem = adj[:-1]
        if any(slot_clean.startswith(w) for w in fem_plural):
            adj_agree = adj_stem + 'as'
            nobre_agree = ' Nobres' if is_nobre else ''
        elif any(slot_clean.startswith(w) for w in masc_plural):
            adj_agree = adj_stem + 'os'
            nobre_agree = ' Nobres' if is_nobre else ''
        elif any(slot_clean.startswith(w) for w in fem_sing):
            adj_agree = adj_stem + 'a'
            nobre_agree = ' Nobre' if is_nobre else ''
        else:
            adj_agree = adj_stem + 'o'
            nobre_agree = ' Nobre' if is_nobre else ''
            
        if slot_clean.lower() in ['escudo', 'aço escudo']:
            slot_clean = 'Escudo'
            if mat == 'Aço' or 'aço' in slot.lower():
                mat_part = ' de Aço'
        elif slot_clean.lower() == 'placas de ombro':
            slot_clean = 'Ombreiras'
            mat_part = ' de Placa'
        elif slot_clean.lower() == 'manoplas de placas':
            slot_clean = 'Manoplas'
            mat_part = ' de Placa'
        elif slot_clean.lower() == 'botas de placas':
            slot_clean = 'Botas'
            mat_part = ' de Placa'
        elif slot_clean.lower() == 'elmo de placas':
            slot_clean = 'Elmo'
            mat_part = ' de Placa'

        return f'{slot_clean}{nobre_agree} {adj_agree}{mat_part} {prep} {owner}'

    # 4. Possessivos invertidos com material: "Nobre do Oficial Tático Malha Manoplas" -> "Manoplas Nobres de Malha do Oficial Tático"
    m2 = re.match(r'^(?:Nobre\s+)?(do|da|dos|das)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)?)\s+(Malha|Placas?|Tecido|Couro|Aço)\s+(.+)$', text)
    if m2:
        prep, owner, mat, slot = m2.groups()
        is_nobre = text.startswith('Nobre ')
        slot_clean = slot.strip().capitalize()
        mat_clean = mat.capitalize().replace('Placas', 'Placa')
        
        fem_plural = ['Manoplas', 'Luvas', 'Braçadeiras', 'Botas', 'Polainas', 'Ombreiras', 'Grevas', 'Brafoneiras']
        masc_plural = ['Sapatos', 'Calções', 'Protetores', 'Brogans']
        if any(slot_clean.startswith(w) for w in fem_plural + masc_plural):
            nobre_agree = ' Nobres' if is_nobre else ''
        else:
            nobre_agree = ' Nobre' if is_nobre else ''
            
        return f'{slot_clean}{nobre_agree} de {mat_clean} {prep} {owner}'

    # 5. Possessivos específicos sem slot no meio (Namorados, Rei Dragão, etc.)
    m3 = re.match(r'^(do|da|dos|das)\s+(Namorados|Rei\s+Dragão(?:\s+Sábio|\s+Sombrio)?|Guarda|Comandante|Oficial\s+Tático|Almirante(?:\s+Guardião)?|Protetor)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Úa-zà-ú]+)*)$', text)
    if m3:
        prep, owner, item = m3.groups()
        if not any(item.lower().startswith(w) for w in ['caixa', 'pacote', 'fardo']):
            return f'{item} {prep} {owner}'

    # 6. Exemplo do Usuário: "Nobre Manoplas de Placas do Oficial Tático" -> "Manoplas Nobres de Placa do Oficial Tático"
    m4 = re.match(r'^Nobre\s+(Manoplas|Luvas|Braçadeiras|Botas|Polainas|Ombreiras|Grevas|Brafoneiras|Protetores\s+de\s+Ombro|Calções|Sapatos)\s+(de\s+Placas?|de\s+Malha|de\s+Tecido|de\s+Couro)?\s*(do|da|dos|das)\s+(.+)$', text)
    if m4:
        slot, mat_de, prep, rest = m4.groups()
        mat_clean = f' {mat_de.replace("Placas", "Placa")}' if mat_de else ''
        return f'{slot} Nobres{mat_clean} {prep} {rest}'

    # 7. "Nobre [Slot Singular] do/da [Owner]"
    m5 = re.match(r'^Nobre\s+(Espada\s+Grande|Arma\s+de\s+Haste|Cota\s+de\s+Malha|Livro\s+de\s+Feitiços|Espada|Adaga|Maça|Martelo|Orbe|Tomo|Grimório|Cajado|Arco|Alabarda|Peitoral|Túnica|Gibão|Elmo|Escudo|Capuz|Diadema|Tiara|Colar|Brinco|Anel|Cinto|Faixa)\s+(do|da|dos|das)\s+(.+)$', text)
    if m5:
        slot, prep, rest = m5.groups()
        return f'{slot} Nobre {prep} {rest}'

    # 8. "Nobre [Slot Plural] de/do ..." geral
    m6 = re.match(r'^Nobre\s+(Manoplas|Luvas|Braçadeiras|Botas|Polainas|Ombreiras|Grevas|Brafoneiras|Calções|Sapatos)\s+(de\s+.+)$', text)
    if m6:
        slot, rest = m6.groups()
        rest_clean = rest.replace('de Placas', 'de Placa')
        return f'{slot} Nobres {rest_clean}'

    # 9. "Nobre [Slot Singular] de ..." geral
    m7 = re.match(r'^Nobre\s+(Espada\s+Grande|Arma\s+de\s+Haste|Cota\s+de\s+Malha|Livro\s+de\s+Feitiços|Espada|Adaga|Maça|Martelo|Orbe|Tomo|Grimório|Cajado|Arco|Alabarda|Peitoral|Túnica|Gibão|Elmo|Escudo|Capuz|Diadema|Tiara|Colar|Brinco|Anel|Cinto|Faixa)\s+(de\s+.+)$', text)
    if m7:
        slot, rest = m7.groups()
        return f'{slot} Nobre {rest}'

    # 10. "Nobre [Slot Plural]" simples
    m8 = re.match(r'^Nobre\s+(Manoplas|Luvas|Braçadeiras|Botas|Polainas|Ombreiras|Grevas|Brafoneiras|Calções|Sapatos)$', text)
    if m8:
        slot = m8.group(1)
        return f'{slot} Nobres'

    # 11. "Nobre [Slot Singular]" simples
    m9 = re.match(r'^Nobre\s+(Espada\s+Grande|Arma\s+de\s+Haste|Cota\s+de\s+Malha|Livro\s+de\s+Feitiços|Espada|Adaga|Maça|Martelo|Orbe|Tomo|Grimório|Cajado|Arco|Alabarda|Peitoral|Túnica|Gibão|Elmo|Escudo|Capuz|Diadema|Tiara|Colar|Brinco|Anel|Cinto|Faixa)$', text)
    if m9:
        slot = m9.group(1)
        return f'{slot} Nobre'

    # 12. "Nobre [Material] [Slot]"
    m10 = re.match(r'^Nobre\s+(Durável\s+)?(Adamantio|Titânio|Dencrima|Mithril|Ouro|Prata|Ferro|Madeira|Betua|Tecoma)\s+(Espada\s+Grande|Arma\s+de\s+Haste|Cota\s+de\s+Malha|Espada|Adaga|Maça|Martelo|Orbe|Tomo|Grimório|Cajado|Arco|Alabarda|Peitoral|Túnica|Gibão|Elmo|Escudo)$', text)
    if m10:
        dur, mat, slot = m10.groups()
        dur_part = ' Durável' if dur else ''
        return f'{slot} Nobre{dur_part} de {mat}'

    # 13. Tomos
    if text.lower() == 'nobre verdade tome':
        return 'Tomo Nobre da Verdade'
    if text.lower() == 'nobre durável verdade tome':
        return 'Tomo Nobre Durável da Verdade'

    # 14. Joias
    text = re.sub(r'\b(Brinco|Colar|Anel)\s+joia\b', r'\1 de Joia', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(Brinco|Colar|Anel)\s+Cristal\b', r'\1 de Cristal', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNobre Rosa Brinco Quartzo\b', 'Brinco Nobre de Quartzo Rosa', text, flags=re.IGNORECASE)

    # 15. Capitalização inicial
    if text.startswith('escudo '):
        text = 'Escudo ' + text[7:]

    return text


def refine_skill(text: str) -> str:
    if not text:
        return text

    # Correções de termos conceituais
    text = re.sub(r'\bPoderoso cobrança\b', 'Investida Poderosa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCobranças a uma meta\b', 'Avança contra um alvo', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAura:\s*El el santo escudo\b', 'Aura: Escudo Sagrado', text, flags=re.IGNORECASE)

    # Ordem dos nomes de magias
    text = re.sub(r'\bPoderoso golpe\b', 'Golpe Poderoso', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande golpe\b', 'Golpe Pesado', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPoderoso Empurrão\b', 'Empurrão Poderoso', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDivina Faísca\b', 'Faísca Divina', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDivina Vitalidade\b', 'Vitalidade Celestial', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDivino Golpe\b', 'Golpe Divino', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDivina Runa\b', 'Runa Divina', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDivina Grama\b', 'Aprisionamento Divino', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTerrível uivo\b', 'Uivo Terrível', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTerrível Uivo\b', 'Uivo Terrível', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMágico esmagamento\b', 'Esmagamento Mágico', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMágico Ajuda\b', 'Potencialização Mágica', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande clivagem\b', 'Clivagem Maior', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande erupção de magma\b', 'Grande Erupção de Magma', text, flags=re.IGNORECASE)

    # Erros mecânicos em habilidades
    text = re.sub(r'\bProficiência avançada de armadura de cadeia\b', 'Proficiência Avançada em Armadura de Malha', text, flags=re.IGNORECASE)
    text = re.sub(r'\bArmadura avançada de placa\b', 'Proficiência Avançada em Armadura de Placa', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAvançado com dupla mistura\b', 'Empunhadura Dupla Avançada', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBorda rápida\b', 'Lâmina Rápida', text, flags=re.IGNORECASE)
    text = re.sub(r'\bParafuso de chama\b', 'Dardo de Chamas', text, flags=re.IGNORECASE)
    text = re.sub(r'\bBLAST atrasada\b', 'Explosão Retardada', text, flags=re.IGNORECASE)
    text = re.sub(r'\bescudo queimado\b', 'Escudo Flamejante', text, flags=re.IGNORECASE)
    text = re.sub(r'\bContador de escudo\b', 'Contra-Ataque com Escudo', text, flags=re.IGNORECASE)
    text = re.sub(r'\bOnda de terremoto\b', 'Onda Sísmica', text, flags=re.IGNORECASE)

    # Anomalias de numerais romanos
    text = re.sub(r'\bi\s+I\b', 'I', text)
    text = re.sub(r'\bI\.\s+I\b', 'I', text)
    text = re.sub(r'\bi\s+II\b', 'II', text)
    text = re.sub(r'\bii\s+II\b', 'II', text)
    text = re.sub(r'\bi\s+III\b', 'III', text)
    text = re.sub(r'\biii\s+III\b', 'III', text)
    text = re.sub(r'\biv\s+IV\b', 'IV', text)
    text = re.sub(r'\bv\s+V\b', 'V', text)

    return text


def refine_npc(text: str) -> str:
    if not text:
        return text

    text = re.sub(r'\bFeroz cinza Worg\b', 'Worg Cinzento Feroz', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFeroz Rynoce\b', 'Rynoce Feroz', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFeroz mosabre\b', 'Mosabre Feroz', text, flags=re.IGNORECASE)
    text = re.sub(r'\bFeroz Draco\b', 'Draco Feroz', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPequeno Arachna\b', 'Arachna Pequena', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPequeno animalia\b', 'Pequeno Animal', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCarcaça de animalia semi-roteado\b', 'Carcaça de Animal Semipodre', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande saída do convés de pistola\b', 'Saída Principal do Convés de Canhões', text, flags=re.IGNORECASE)
    text = re.sub(r'\bEntrada grande no convés de pistola\b', 'Entrada Principal do Convés de Canhões', text, flags=re.IGNORECASE)
    text = re.sub(r'\bTundra Kisk pessoal\b', 'Kisk Individual de Tundra', text, flags=re.IGNORECASE)
    text = re.sub(r'\bKisk marinho pessoal\b', 'Kisk Individual Marinho', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande chefe de Tursin\b', 'Grande Chefe Tursin', text, flags=re.IGNORECASE)
    text = re.sub(r'\bGrande caixa de carga\b', 'Caixa Grande de Carga', text, flags=re.IGNORECASE)
    text = re.sub(r'\b<Preto nuvem Envoy>\b', '<Emissário da Nuvem Negra>', text, flags=re.IGNORECASE)
    text = re.sub(r'\b<Preto nuvem espião>\b', '<Espião da Nuvem Negra>', text, flags=re.IGNORECASE)
    text = re.sub(r'\b<Preto nuvem Mate>\b', '<Imediato da Nuvem Negra>', text, flags=re.IGNORECASE)

    return text


def process_xml_file(filepath: str, refine_func, apply_changes: bool) -> int:
    if not os.path.exists(filepath):
        print(f"[AVISO] Arquivo não encontrado: {filepath}")
        return 0

    with open(filepath, 'rb') as f:
        raw = f.read()

    encoding = 'utf-16' if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff') else 'utf-8'
    content = raw.decode(encoding, errors='replace')

    # Processar cada tag <body>...</body>
    pattern = re.compile(r'(<body[^>]*>)(.*?)(</body>)', re.DOTALL)
    changes_count = 0

    def replacer(match):
        nonlocal changes_count
        prefix = match.group(1)
        body_text = match.group(2)
        suffix = match.group(3)

        refined = refine_func(body_text)
        if refined != body_text:
            changes_count += 1
            return f"{prefix}{refined}{suffix}"
        return match.group(0)

    new_content = pattern.sub(replacer, content)

    if changes_count > 0 and apply_changes:
        with open(filepath, 'w', encoding=encoding, newline='\r\n') as f:
            f.write(new_content)
        print(f"[ATUALIZADO] {os.path.basename(filepath)} ({encoding}): {changes_count} strings refinadas com sucesso.")
    else:
        print(f"[VERIFICADO] {os.path.basename(filepath)} ({encoding}): {changes_count} strings elegíveis para refinamento.")

    return changes_count


def main():
    parser = argparse.ArgumentParser(description="Aprimoramento Gramatical de Traduções PT-BR (Aion Classic 5.0)")
    parser.add_argument("--aplicar", action="store_true", help="Aplica as correções diretamente nos arquivos XML")
    parser.add_argument("--verificar", action="store_true", help="Apenas simula e exibe contagem de alterações")
    args = parser.parse_args()

    if not args.aplicar and not args.verificar:
        print("Especifique --verificar ou --aplicar.")
        sys.exit(1)

    print("=" * 70)
    print("APRIMORAMENTO GRAMATICAL DE TRADUÇÕES PT-BR (Aion Classic 5.0)")
    print("Modo:", "APLICAÇÃO DIRETA" if args.aplicar else "VERIFICAÇÃO / SIMULAÇÃO")
    print("=" * 70)

    targets = [
        ("client_strings_item2.xml", refine_item),
        ("client_strings_item.xml", refine_item),
        ("client_strings_dic_item.xml", refine_item),
        ("client_strings_skill.xml", refine_skill),
        ("client_strings_monster.xml", refine_npc),
        ("client_strings_npc.xml", refine_npc),
        ("client_strings_dic_monster.xml", refine_npc),
        ("client_strings_quest.xml", refine_item)
    ]

    total_changes = 0
    for filename, fn in targets:
        fp = os.path.join(STRINGS_DIR, filename)
        count = process_xml_file(fp, fn, args.aplicar)
        total_changes += count

    print("=" * 70)
    print(f"TOTAL DE STRINGS REFINADAS: {total_changes}")
    print("=" * 70)


if __name__ == "__main__":
    main()
