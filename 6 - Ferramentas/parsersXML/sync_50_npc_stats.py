#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_50_npc_stats.py

Auditoria e sincronização canônica de níveis e atributos de NPCs entre o cliente oficial
Aion Classic 5.0 (client_npcs.xml) e os templates do emulador (npc_templates.xml).
Restaura também os templates de Housing (810000-810056) perdidos em versões anteriores.
"""

import os
import sys
import re
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_DIR = os.path.join(PROJECT_ROOT, "6 - Ferramentas")
sys.path.insert(0, TOOLS_DIR)
import aion_bxml

CLIENT_EXTRACTED = os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
CLIENT_NPCS_PATH = os.path.join(CLIENT_EXTRACTED, "data", "npcs", "client_npcs.xml")

SRC_NPC_TEMPLATES = os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data", "npcs", "npc_templates.xml")
PROD_NPC_TEMPLATES = os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data", "npcs", "npc_templates.xml")
HOUSING_SCRATCH = os.path.join(os.environ.get("USERPROFILE", ""), ".gemini", "antigravity-ide", "brain", "03ad6347-d2c8-417b-a958-ae8f7e13fce0", "scratch", "housing_templates_to_restore.xml")


def parse_client_npcs():
    print("[1/4] Carregando e analisando client_npcs.xml do cliente oficial 5.0...")
    raw = open(CLIENT_NPCS_PATH, "rb").read()
    xml_str = aion_bxml.decodifica(raw)
    root = ET.fromstring(xml_str)

    regexes = [
        re.compile(r'_(\d{1,2})_([a-zA-Z]+)(?:_\d+)?$'),
        re.compile(r'_(\d{1,2})$')
    ]

    rating_map = {
        'j': 'JUNK',
        'n': 'NORMAL',
        'e': 'ELITE',
        'h': 'HERO',
        'l': 'LEGENDARY'
    }

    client_data = {}
    for n in root.findall("npc_client"):
        nid_str = n.findtext("id")
        if not nid_str or not nid_str.isdigit():
            continue
        nid = int(nid_str)
        name = n.findtext("name", "")
        desc = n.findtext("desc", "")

        level = None
        rating = None
        for r in regexes:
            m = r.search(name) or r.search(desc)
            if m:
                lvl = int(m.group(1))
                if 1 <= lvl <= 100:
                    level = lvl
                    if len(m.groups()) >= 2:
                        suf = m.group(2).lower()
                        # Última letra indica o rating (ex: an -> n, ah -> h, ae -> e, al -> l)
                        last_char = suf[-1]
                        if last_char in rating_map:
                            rating = rating_map[last_char]
                    break

        hpgauge_str = n.findtext("hpgauge_level")
        hpgauge = int(hpgauge_str) if hpgauge_str and hpgauge_str.isdigit() else None

        srange_str = n.findtext("sensory_range")
        try:
            srange = int(round(float(srange_str))) if srange_str else None
        except Exception:
            srange = None

        sangle_str = n.findtext("stare_angle")
        try:
            sangle = int(round(float(sangle_str))) if sangle_str else None
        except Exception:
            sangle = None

        arange_str = n.findtext("attack_range")
        try:
            arange = int(round(float(arange_str))) if arange_str else None
        except Exception:
            arange = None

        atk_speed_str = n.findtext("attack_delay")
        try:
            atk_speed = int(round(float(atk_speed_str))) if atk_speed_str else None
        except Exception:
            atk_speed = None

        client_data[nid] = {
            "name": name,
            "desc": desc,
            "level": level,
            "rating": rating,
            "hpgauge": hpgauge,
            "srange": srange,
            "sangle": sangle,
            "arange": arange,
            "attack_speed": atk_speed
        }

    print(f"      {len(client_data)} NPCs do cliente analisados. Níveis canônicos encontrados: {sum(1 for d in client_data.values() if d['level'] is not None)}.")
    return client_data


def sync_templates(client_data):
    print("[2/4] Sincronizando npc_templates.xml do emulador...")
    tree = ET.parse(SRC_NPC_TEMPLATES)
    root = tree.getroot()

    existing_ids = set()
    levels_updated = 0
    ratings_updated = 0
    hpgauges_updated = 0

    for elem in root.findall("npc_template"):
        nid_str = elem.get("npc_id")
        if not nid_str or not nid_str.isdigit():
            continue
        nid = int(nid_str)
        existing_ids.add(nid)

        if nid in client_data:
            cinfo = client_data[nid]

            # 1. Level
            if cinfo["level"] is not None:
                old_lvl = int(elem.get("level", "1"))
                new_lvl = cinfo["level"]
                if old_lvl != new_lvl:
                    elem.set("level", str(new_lvl))
                    levels_updated += 1

            # 2. Rating
            if cinfo["rating"] is not None:
                old_rating = elem.get("rating")
                new_rating = cinfo["rating"]
                if old_rating != new_rating:
                    elem.set("rating", new_rating)
                    ratings_updated += 1

            # 3. HP Gauge
            if cinfo["hpgauge"] is not None and cinfo["hpgauge"] > 0:
                old_hpgauge = elem.get("hpgauge")
                if not old_hpgauge or int(old_hpgauge) != cinfo["hpgauge"]:
                    elem.set("hpgauge", str(cinfo["hpgauge"]))
                    hpgauges_updated += 1

            # 4. Sensory Range & Angle
            if cinfo["srange"] is not None and cinfo["srange"] > 0:
                elem.set("srange", str(cinfo["srange"]))
            if cinfo["sangle"] is not None and cinfo["sangle"] > 0:
                elem.set("sangle", str(cinfo["sangle"]))

            # 5. Attack speed & range
            if cinfo["attack_speed"] is not None and cinfo["attack_speed"] > 0:
                elem.set("attack_speed", str(cinfo["attack_speed"]))
            if cinfo["arange"] is not None and cinfo["arange"] > 0:
                elem.set("arange", str(cinfo["arange"]))

    print(f"      Atualizações nos templates existentes: {levels_updated} níveis corrigidos, {ratings_updated} ratings alinhados, {hpgauges_updated} hpgauges atualizados.")

    # Restauração de Housing
    print("[3/4] Restaurando templates de Housing ausentes (810000-810056)...")
    housing_added = 0
    if os.path.exists(HOUSING_SCRATCH):
        h_tree = ET.parse(HOUSING_SCRATCH)
        for h_elem in h_tree.getroot() if h_tree.getroot().tag == "npc_templates" else [h_tree.getroot()]:
            for tmpl in ([h_elem] if h_elem.tag == "npc_template" else h_elem.findall(".//npc_template")):
                hid = int(tmpl.get("npc_id"))
                if hid not in existing_ids:
                    root.append(tmpl)
                    existing_ids.add(hid)
                    housing_added += 1
    else:
        # Fallback se não estiver no scratch
        print(f"      [AVISO] {HOUSING_SCRATCH} não encontrado.")

    print(f"      {housing_added} templates de Housing adicionados com sucesso.")

    # Ordena elementos por npc_id
    root[:] = sorted(root, key=lambda x: int(x.get("npc_id", 0)))

    print("[4/4] Gravando npc_templates.xml atualizado (Código Fonte e Produto Final)...")
    tree.write(SRC_NPC_TEMPLATES, encoding="utf-8", xml_declaration=True)
    tree.write(PROD_NPC_TEMPLATES, encoding="utf-8", xml_declaration=True)
    print(f"      [OK] Gravado com sucesso em:")
    print(f"           - {SRC_NPC_TEMPLATES}")
    print(f"           - {PROD_NPC_TEMPLATES}")


def main():
    print("=" * 80)
    print("Sincronização de Estatísticas e Níveis de NPCs 5.0 (Autoritativo do Cliente)")
    print("=" * 80)
    client_data = parse_client_npcs()
    sync_templates(client_data)
    print("=" * 80)
    print("Concluído com Sucesso!")
    print("=" * 80)


if __name__ == "__main__":
    main()
