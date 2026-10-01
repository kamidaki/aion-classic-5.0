#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_xml_dual_language.py

Realiza a normalização integral de nomes em XMLs de static_data do Aion Classic 5.0,
migrando do atributo legado 'name' para a representação dual-language 'name_en' e 'name_pt'.

Fontes canônicas:
- PT-BR: Ferramentas e Documentos/Client e Coletas/Tradução - Português Brasil/strings/*.xml
- EN: Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/Idioma em Inglês/strings/*.xml

Uso:
    python normalize_xml_dual_language.py --verificar
    python normalize_xml_dual_language.py --aplicar
"""

import os
import sys
import re
import html
import argparse
from typing import Dict, Tuple, Optional

# Garantir codificação UTF-8 no stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Raiz do repositório (4 níveis acima de parsersXML)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

PT_STRINGS_DIR = os.path.join(REPO_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Tradução - Português Brasil", "strings")
EN_STRINGS_DIR = os.path.join(REPO_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "Idioma em Inglês", "strings")

STATIC_DATA_DIR = os.path.join(REPO_ROOT, "Código Fonte - Emulador", "game-server", "data", "static_data")
PROD_STATIC_DATA_DIR = os.path.join(REPO_ROOT, "Emulador - Produto Final", "GameServer", "data", "static_data")

# Regex para carregar strings oficiais
STRING_PAT = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>(.*?)</body>)?', re.S)

# Mapa de reparo de Mojibake (quando bytes UTF-8 foram interpretados como Windows-1252 / Latin-1)
MOJIBAKE_REPLACEMENTS = {
    'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
    'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì', 'Ã²': 'ò', 'Ã¹': 'ù',
    'Ã¢': 'â', 'Ãª': 'ê', 'Ã®': 'î', 'Ã´': 'ô', 'Ã»': 'û',
    'Ã£': 'ã', 'Ãµ': 'õ', 'Ã±': 'ñ', 'Ã§': 'ç',
    'Ã': 'Á', 'Ã‰': 'É', 'Ã': 'Í', 'Ã“': 'Ó', 'Ãš': 'Ú',
    'Ã€': 'À', 'Ãˆ': 'È', 'ÃŒ': 'Ì', 'Ã’': 'Ò', 'Ã™': 'Ù',
    'Ã‚': 'Â', 'ÃŠ': 'Ê', 'ÃŽ': 'Î', 'Ã”': 'Ô', 'Ã›': 'Û',
    'Ãƒ': 'Ã', 'Ã•': 'Õ', 'Ã‘': 'Ñ', 'Ã‡': 'Ç',
}

def fix_mojibake(text: str) -> str:
    if not text:
        return ""
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        if bad in text:
            text = text.replace(bad, good)
    return text

def clean_text(raw_text: Optional[str]) -> str:
    if not raw_text:
        return ""
    txt = raw_text.strip()
    # Preservar nós de dummy com apenas espaço
    if txt == "":
        return ""
    txt = html.unescape(txt)
    txt = fix_mojibake(txt)
    return txt.strip()

def escape_xml_attr(val: str) -> str:
    if not val:
        return ""
    return (val.replace("&", "&amp;")
               .replace('"', "&quot;")
               .replace("<", "&lt;")
               .replace(">", "&gt;"))

def extract_existing_raw_names(attrs: str) -> Tuple[str, str]:
    m_en = re.search(r'\bname_en\s*=\s*"([^"]*)"', attrs)
    m_pt = re.search(r'\bname_pt\s*=\s*"([^"]*)"', attrs)
    m_legacy = re.search(r'\bname\s*=\s*"([^"]*)"', attrs)

    en = m_en.group(1) if m_en else ""
    pt = m_pt.group(1) if m_pt else ""
    legacy = m_legacy.group(1) if m_legacy else ""

    final_en = en if en != "" else legacy
    final_pt = pt if pt != "" else legacy
    return final_en, final_pt

def extract_existing_raw_descs(attrs: str) -> Tuple[str, str]:
    m_en = re.search(r'\bdesc_en\s*=\s*"([^"]*)"', attrs)
    m_pt = re.search(r'\bdesc_pt\s*=\s*"([^"]*)"', attrs)
    m_legacy = re.search(r'\bdesc\s*=\s*"([^"]*)"', attrs)

    en = m_en.group(1) if m_en else ""
    pt = m_pt.group(1) if m_pt else ""
    legacy = m_legacy.group(1) if m_legacy else ""

    final_en = en if en != "" else legacy
    final_pt = pt if pt != "" else legacy
    return final_en, final_pt

def update_dual_name_attrs(attrs: str, name_en: str, name_pt: str) -> str:
    m = re.search(r'\s+\b(?:name_en|name_pt|name)\b\s*=\s*"[^"]*"', attrs)
    clean_en = escape_xml_attr(name_en)
    clean_pt = escape_xml_attr(name_pt)
    replacement = f' name_en="{clean_en}" name_pt="{clean_pt}"'
    if m:
        pos = m.start()
        stripped = re.sub(r'\s+\b(?:name_en|name_pt|name)\b\s*=\s*"[^"]*"', '', attrs)
        return stripped[:pos] + replacement + stripped[pos:]
    else:
        return replacement + attrs

def update_dual_desc_attrs(attrs: str, desc_en: str, desc_pt: str) -> str:
    m = re.search(r'\s+\b(?:desc_en|desc_pt|desc)\b\s*=\s*"[^"]*"', attrs)
    clean_en = escape_xml_attr(desc_en)
    clean_pt = escape_xml_attr(desc_pt)
    replacement = f' desc_en="{clean_en}" desc_pt="{clean_pt}"'
    if m:
        pos = m.start()
        stripped = re.sub(r'\s+\b(?:desc_en|desc_pt|desc)\b\s*=\s*"[^"]*"', '', attrs)
        return stripped[:pos] + replacement + stripped[pos:]
    else:
        return replacement + attrs

def load_string_tables(dir_path: str) -> Tuple[Dict[int, str], Dict[str, str]]:
    id_map: Dict[int, str] = {}
    name_map: Dict[str, str] = {}
    if not os.path.isdir(dir_path):
        print(f"AVISO: Diretório de strings não encontrado: {dir_path}")
        return id_map, name_map

    for fname in sorted(os.listdir(dir_path)):
        if fname.endswith('.xml'):
            fpath = os.path.join(dir_path, fname)
            try:
                with open(fpath, 'rb') as fp:
                    raw = fp.read()
                if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
                    content = raw.decode('utf-16le', errors='replace')
                else:
                    content = raw.decode('utf-8', errors='replace')
                
                for sid, sname, sbody in STRING_PAT.findall(content):
                    body = clean_text(sbody)
                    num_id = int(sid)
                    id_map[num_id] = body
                    name_map[sname.strip().upper()] = body
            except Exception as e:
                print(f"Erro ao ler {fname}: {e}")
    return id_map, name_map

class DualLanguageNormalizer:
    def __init__(self, pt_dir: str, en_dir: str, static_dir: str):
        self.static_dir = static_dir
        print("-> Carregando tabelas de strings em Português...")
        self.pt_id, self.pt_name = load_string_tables(pt_dir)
        print(f"   Carregadas {len(self.pt_id):,} strings PT-BR.")

        print("-> Carregando tabelas de strings em Inglês...")
        self.en_id, self.en_name = load_string_tables(en_dir)
        print(f"   Carregadas {len(self.en_id):,} strings EN.")

        self.stats = {
            'items': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'npcs': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'skills': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'quests': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'gatherables': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'materials': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'pets': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'maps': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'teleports': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'titles': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
            'item_sets': {'total': 0, 'resolved_pt': 0, 'resolved_en': 0},
        }

    # -------------------------------------------------------------------------
    # 1. ITENS (items/item_templates.xml)
    # -------------------------------------------------------------------------
    def process_item_templates(self, dry_run: bool = False):
        rel_path = os.path.join("items", "item_templates.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[1/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['items']
        pat = re.compile(r'(<item_template\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        desc_pat = re.compile(r'\bdesc="(\d+)"')
        cname_pat = re.compile(r'\bcName="([^"]*)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                desc_m = desc_pat.search(attrs)
                desc_id = int(desc_m.group(1)) if desc_m else None

                cname_m = cname_pat.search(attrs)
                cname = cname_m.group(1).strip() if cname_m else ""

                # Resolução PT
                name_pt = ""
                if desc_id and desc_id in self.pt_id and self.pt_id[desc_id]:
                    name_pt = self.pt_id[desc_id]
                elif cname:
                    sym1 = f"STR_{cname.upper()}"
                    sym2 = cname.upper()
                    if sym1 in self.pt_name and self.pt_name[sym1]:
                        name_pt = self.pt_name[sym1]
                    elif sym2 in self.pt_name and self.pt_name[sym2]:
                        name_pt = self.pt_name[sym2]

                # Resolução EN
                name_en = ""
                if desc_id and desc_id in self.en_id and self.en_id[desc_id]:
                    name_en = self.en_id[desc_id]
                elif cname:
                    sym1 = f"STR_{cname.upper()}"
                    sym2 = cname.upper()
                    if sym1 in self.en_name and self.en_name[sym1]:
                        name_en = self.en_name[sym1]
                    elif sym2 in self.en_name and self.en_name[sym2]:
                        name_en = self.en_name[sym2]

                # Fallback defensivo
                if name_pt:
                    st['resolved_pt'] += 1
                else:
                    name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Item"))

                if name_en:
                    st['resolved_en'] += 1
                else:
                    name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Item"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total itens: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} ({st['resolved_pt']/st['total']*100:.2f}%) | Resolvidos EN: {st['resolved_en']:,} ({st['resolved_en']/st['total']*100:.2f}%)")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 2. NPCs (npcs/npc_templates.xml)
    # -------------------------------------------------------------------------
    def process_npc_templates(self, dry_run: bool = False):
        rel_path = os.path.join("npcs", "npc_templates.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[2/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['npcs']
        pat = re.compile(r'(<npc_template\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bname_id="(\d+)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                raw_name = raw_pt if raw_pt is not None and raw_pt != "" else raw_en
                
                nameid_m = nameid_pat.search(attrs)
                name_id = int(nameid_m.group(1)) if nameid_m else None

                # Caso especial: nós invisíveis com name=" " ou name=""
                if raw_name == " " or (raw_name == "" and not name_id):
                    name_en = " " if raw_name == " " else ""
                    name_pt = " " if raw_name == " " else ""
                    st['resolved_pt'] += 1
                    st['resolved_en'] += 1
                else:
                    current_name = clean_text(raw_name)
                    name_pt = ""
                    if name_id and name_id in self.pt_id and self.pt_id[name_id]:
                        name_pt = self.pt_id[name_id]

                    name_en = ""
                    if name_id and name_id in self.en_id and self.en_id[name_id]:
                        name_en = self.en_id[name_id]

                    if name_pt:
                        st['resolved_pt'] += 1
                    else:
                        name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "NPC"))

                    if name_en:
                        st['resolved_en'] += 1
                    else:
                        name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "NPC"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total NPCs: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} ({st['resolved_pt']/st['total']*100:.2f}%) | Resolvidos EN: {st['resolved_en']:,} ({st['resolved_en']/st['total']*100:.2f}%)")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 3. SKILLS (skills/skill_templates.xml)
    # -------------------------------------------------------------------------
    def process_skill_templates(self, dry_run: bool = False):
        rel_path = os.path.join("skills", "skill_templates.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[3/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['skills']
        pat = re.compile(r'(<skill_template\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bnameId="(\d+)"')
        stack_pat = re.compile(r'\bstack="([^"]*)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                nameid_m = nameid_pat.search(attrs)
                name_id = int(nameid_m.group(1)) if nameid_m else None

                stack_m = stack_pat.search(attrs)
                stack = stack_m.group(1).strip() if stack_m else ""

                name_pt = ""
                if name_id and name_id in self.pt_id and self.pt_id[name_id]:
                    name_pt = self.pt_id[name_id]
                elif stack:
                    sym = f"STR_SKILL_{stack.upper()}"
                    if sym in self.pt_name and self.pt_name[sym]:
                        name_pt = self.pt_name[sym]

                name_en = ""
                if name_id and name_id in self.en_id and self.en_id[name_id]:
                    name_en = self.en_id[name_id]
                elif stack:
                    sym = f"STR_SKILL_{stack.upper()}"
                    if sym in self.en_name and self.en_name[sym]:
                        name_en = self.en_name[sym]

                if name_pt:
                    st['resolved_pt'] += 1
                else:
                    name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Skill"))

                if name_en:
                    st['resolved_en'] += 1
                else:
                    name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Skill"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Skills: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} ({st['resolved_pt']/st['total']*100:.2f}%) | Resolvidos EN: {st['resolved_en']:,} ({st['resolved_en']/st['total']*100:.2f}%)")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 4. QUESTS (quest_data/quest_data.xml)
    # -------------------------------------------------------------------------
    def process_quests(self, dry_run: bool = False):
        rel_path = os.path.join("quest_data", "quest_data.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[4/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['quests']
        pat = re.compile(r'(<quest\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bnameId="(\d+)"')
        id_pat = re.compile(r'\bid="(\d+)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                nameid_m = nameid_pat.search(attrs)
                name_id = int(nameid_m.group(1)) if nameid_m else None

                id_m = id_pat.search(attrs)
                qid = id_m.group(1) if id_m else ""

                name_pt = ""
                if name_id and name_id in self.pt_id and self.pt_id[name_id]:
                    name_pt = self.pt_id[name_id]
                elif qid:
                    sym = f"STR_QUEST_NAME_Q{qid}"
                    if sym in self.pt_name and self.pt_name[sym]:
                        name_pt = self.pt_name[sym]

                name_en = ""
                if name_id and name_id in self.en_id and self.en_id[name_id]:
                    name_en = self.en_id[name_id]
                elif qid:
                    sym = f"STR_QUEST_NAME_Q{qid}"
                    if sym in self.en_name and self.en_name[sym]:
                        name_en = self.en_name[sym]

                if name_pt:
                    st['resolved_pt'] += 1
                else:
                    name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else f"Quest {qid}"))

                if name_en:
                    st['resolved_en'] += 1
                else:
                    name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else f"Quest {qid}"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Quests: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} ({st['resolved_pt']/st['total']*100:.2f}%) | Resolvidos EN: {st['resolved_en']:,} ({st['resolved_en']/st['total']*100:.2f}%)")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 5. GATHERABLES & MATERIALS (gatherables/gatherable_templates.xml)
    # -------------------------------------------------------------------------
    def process_gatherables(self, dry_run: bool = False):
        rel_path = os.path.join("gatherables", "gatherable_templates.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[5/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st_g = self.stats['gatherables']
        st_m = self.stats['materials']
        
        g_pat = re.compile(r'(<gatherable_template\b)([^>]*)(>)')
        mat_pat = re.compile(r'(<material\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bnameId="(\d+)"', re.IGNORECASE)
        mat_nameid_pat = re.compile(r'\bnameid="(\d+)"', re.IGNORECASE)
        mat_itemid_pat = re.compile(r'\bitemid="(\d+)"', re.IGNORECASE)

        for line in lines:
            gm = g_pat.search(line)
            mm = mat_pat.search(line)
            if gm:
                st_g['total'] += 1
                prefix, attrs, suffix = gm.group(1), gm.group(2), gm.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                nid_m = nameid_pat.search(attrs)
                nid = int(nid_m.group(1)) if nid_m else None

                name_pt = self.pt_id.get(nid, "") if nid else ""
                name_en = self.en_id.get(nid, "") if nid else ""

                if name_pt: st_g['resolved_pt'] += 1
                else: name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Gatherable"))

                if name_en: st_g['resolved_en'] += 1
                else: name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Gatherable"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:gm.start(1)] + prefix + new_attrs + suffix + line[gm.end(3):]
                new_lines.append(new_line)

            elif mm:
                st_m['total'] += 1
                prefix, attrs, suffix = mm.group(1), mm.group(2), mm.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)

                nid_m = mat_nameid_pat.search(attrs)
                nid = int(nid_m.group(1)) if nid_m else None

                name_pt = self.pt_id.get(nid, "") if nid else ""
                name_en = self.en_id.get(nid, "") if nid else ""

                if name_pt: st_m['resolved_pt'] += 1
                else: name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Material"))

                if name_en: st_m['resolved_en'] += 1
                else: name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Material"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:mm.start(1)] + prefix + new_attrs + suffix + line[mm.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Coletáveis: {st_g['total']:,} | Resolvidos PT: {st_g['resolved_pt']:,} | Resolvidos EN: {st_g['resolved_en']:,}")
        print(f"   Total Materiais: {st_m['total']:,} | Resolvidos PT: {st_m['resolved_pt']:,} | Resolvidos EN: {st_m['resolved_en']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 6. PETS (pets/pets.xml)
    # -------------------------------------------------------------------------
    def process_pets(self, dry_run: bool = False):
        rel_path = os.path.join("pets", "pets.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[6/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['pets']
        pat = re.compile(r'(<pet\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bnameid="(\d+)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                nid_m = nameid_pat.search(attrs)
                nid = int(nid_m.group(1)) if nid_m else None

                name_pt = self.pt_id.get(nid, "") if nid else ""
                name_en = self.en_id.get(nid, "") if nid else ""

                if name_pt: st['resolved_pt'] += 1
                else: name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Pet"))

                if name_en: st['resolved_en'] += 1
                else: name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Pet"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Pets: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} | Resolvidos EN: {st['resolved_en']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 7. WORLD MAPS (world_maps.xml)
    # -------------------------------------------------------------------------
    def process_world_maps(self, dry_run: bool = False):
        rel_path = "world_maps.xml"
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[7/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['maps']
        pat = re.compile(r'(<map\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        cname_pat = re.compile(r'\bcName="([^"]*)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                cname_m = cname_pat.search(attrs)
                cname = cname_m.group(1).strip() if cname_m else ""

                name_pt = ""
                name_en = ""
                if cname:
                    syms = [f"STR_ZONE_NAME_{cname.upper()}", f"STR_{cname.upper()}", f"STR_MAP_{cname.upper()}"]
                    for s in syms:
                        if s in self.pt_name and self.pt_name[s]:
                            name_pt = self.pt_name[s]
                            break
                    for s in syms:
                        if s in self.en_name and self.en_name[s]:
                            name_en = self.en_name[s]
                            break

                if name_pt: st['resolved_pt'] += 1
                else: name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Map"))

                if name_en: st['resolved_en'] += 1
                else: name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Map"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Mapas: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} | Resolvidos EN: {st['resolved_en']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 8. TELEPORT LOCATION (teleport_location.xml)
    # -------------------------------------------------------------------------
    def process_teleports(self, dry_run: bool = False):
        rel_path = "teleport_location.xml"
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[8/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['teleports']
        pat = re.compile(r'(<teleloc_template\b)([^>]*)(>)')
        name_attr_pat = re.compile(r'\s+name="([^"]*)"')
        nameid_pat = re.compile(r'\bname_id="(\d+)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)
                
                nid_m = nameid_pat.search(attrs)
                nid = int(nid_m.group(1)) if nid_m else None

                name_pt = self.pt_id.get(nid, "") if nid else ""
                name_en = self.en_id.get(nid, "") if nid else ""

                if name_pt: st['resolved_pt'] += 1
                else: name_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (name_en if name_en else "Teleport"))

                if name_en: st['resolved_en'] += 1
                else: name_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (name_pt if name_pt else "Teleport"))

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Teleportes: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} | Resolvidos EN: {st['resolved_en']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 9. PLAYER TITLES (player_titles.xml)
    # -------------------------------------------------------------------------
    def process_player_titles(self, dry_run: bool = False):
        rel_path = "player_titles.xml"
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[9/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['titles']
        pat = re.compile(r'(<title\b)([^>]*)(>)')
        nameid_pat = re.compile(r'\bnameId="(\d+)"')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                raw_en, raw_pt = extract_existing_raw_descs(attrs)
                
                nid_m = nameid_pat.search(attrs)
                nid = int(nid_m.group(1)) if nid_m else None

                desc_pt = self.pt_id.get(nid, "") if nid else ""
                desc_en = self.en_id.get(nid, "") if nid else ""

                if desc_pt: st['resolved_pt'] += 1
                else: desc_pt = clean_text(raw_pt) if raw_pt else (clean_text(raw_en) if raw_en else (desc_en if desc_en else "Title"))

                if desc_en: st['resolved_en'] += 1
                else: desc_en = clean_text(raw_en) if raw_en else (clean_text(raw_pt) if raw_pt else (desc_pt if desc_pt else "Title"))

                new_attrs = update_dual_desc_attrs(attrs, desc_en, desc_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Títulos: {st['total']:,} | Resolvidos PT: {st['resolved_pt']:,} | Resolvidos EN: {st['resolved_en']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    # -------------------------------------------------------------------------
    # 10. ITEM SETS (item_sets/item_sets.xml)
    # -------------------------------------------------------------------------
    def process_item_sets(self, dry_run: bool = False):
        rel_path = os.path.join("item_sets", "item_sets.xml")
        file_path = os.path.join(self.static_dir, rel_path)
        if not os.path.isfile(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return

        print(f"\n[10/10] Processando {rel_path}...")
        with open(file_path, "r", encoding="utf-8") as fp:
            lines = fp.readlines()

        new_lines = []
        st = self.stats['item_sets']
        pat = re.compile(r'(<itemset\b)([^>]*)(>)')

        for line in lines:
            m = pat.search(line)
            if m:
                st['total'] += 1
                prefix, attrs, suffix = m.group(1), m.group(2), m.group(3)
                raw_en, raw_pt = extract_existing_raw_names(attrs)

                name_pt = clean_text(raw_pt) if raw_pt else clean_text(raw_en)
                name_en = clean_text(raw_en) if raw_en else clean_text(raw_pt)

                st['resolved_pt'] += 1
                st['resolved_en'] += 1

                new_attrs = update_dual_name_attrs(attrs, name_en, name_pt)
                new_line = line[:m.start(1)] + prefix + new_attrs + suffix + line[m.end(3):]
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        print(f"   Total Item Sets: {st['total']:,} | Processados: {st['resolved_pt']:,}")
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.writelines(new_lines)

    def run_all(self, dry_run: bool = False):
        self.process_item_templates(dry_run)
        self.process_npc_templates(dry_run)
        self.process_skill_templates(dry_run)
        self.process_quests(dry_run)
        self.process_gatherables(dry_run)
        self.process_pets(dry_run)
        self.process_world_maps(dry_run)
        self.process_teleports(dry_run)
        self.process_player_titles(dry_run)
        self.process_item_sets(dry_run)
        print("\n=======================================================")
        print("NORMALIZAÇÃO DUAL-LANGUAGE CONCLUÍDA COM SUCESSO!")
        print("=======================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalizador Dual-Language de XMLs do Aion Classic 5.0")
    parser.add_argument("--aplicar", action="store_true", help="Aplica as alterações nos arquivos XML")
    parser.add_argument("--verificar", action="store_true", help="Apenas audita e exibe métricas sem alterar")
    args = parser.parse_args()

    dry_run = not args.aplicar
    normalizer = DualLanguageNormalizer(PT_STRINGS_DIR, EN_STRINGS_DIR, STATIC_DATA_DIR)
    normalizer.run_all(dry_run=dry_run)
