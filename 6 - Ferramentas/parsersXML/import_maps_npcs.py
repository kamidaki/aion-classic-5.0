#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_maps_npcs.py

Gera e importa automaticamente templates para todos os NPCs e Monstros que existem nos mapas
Tiamaranta (LDF4b), Tiamat Down (Tiamat_Down) e Teva (ldf4_teva), mas que ainda não constam no
npc_templates.xml do servidor.

Extração de Atributos:
  - Visual & Físico: client_npcs.xml e Strings/ (name, name_id, mesh, height, bound_radius, speeds)
  - Enums (tribe, ai, type, race): mapeados pelas tabelas aprendidas do gabarito 5.0
  - Nível e Rank/Rating: extraídos da convenção de nomenclatura oficial da NCSoft (ex: _60_An, _60_Ae, _70_Ah)
  - MaxHP: calculado pela tabela canônica de HP mediano por nível e rating do Classic 5.0

Uso:
  python import_maps_npcs.py            (modo dry-run: analisa e valida)
  python import_maps_npcs.py --aplicar  (grava no servidor com backup atomico)
"""

import argparse
import collections
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
sys.path.insert(0, PARSERS_DIR)

import backup_manager as bm
import rebuild_50_npc_templates as R
from rebuild_50_item_templates import iter_depth1, load_strings

REL_XML = "npcs/npc_templates.xml"
REL_XSD = "npcs/npcs.xsd"
NL = "\r\n"

CLIENT_XML_DIR = r"G:\Projetos AION\XMLS AION CLASSIC"
LEVELS_DIR = os.path.join(PROJECT_ROOT, r"5 - Documentação e Referências\3 - Client 5.0 - Dados Extraidos\levels")

MAPS = [
    ("Tiamaranta (LDF4b)", os.path.join(LEVELS_DIR, r"LDF4b\mission_mission0.xml"), 58),
    ("Tiamat Down", os.path.join(LEVELS_DIR, r"Tiamat_Down\mission_mission0.xml"), 60),
    ("Teva", os.path.join(LEVELS_DIR, r"ldf4_teva\mission_mission0.xml"), 70)
]

# Tabela Canônica de MaxHP por (Level, Rating)
HP_TABLE = {
    55: {"JUNK": 150, "NORMAL": 18756, "ELITE": 71191, "HERO": 319181, "LEGENDARY": 6219649},
    58: {"JUNK": 2000, "NORMAL": 14000, "ELITE": 55000, "HERO": 2425615, "LEGENDARY": 7000000},
    59: {"JUNK": 3600, "NORMAL": 16034, "ELITE": 79622, "HERO": 1799379, "LEGENDARY": 8000000},
    60: {"JUNK": 6001, "NORMAL": 23691, "ELITE": 107415, "HERO": 459876, "LEGENDARY": 10340535},
    65: {"JUNK": 4649, "NORMAL": 28386, "ELITE": 223597, "HERO": 1170333, "LEGENDARY": 34612964},
    70: {"JUNK": 5500, "NORMAL": 35000, "ELITE": 280000, "HERO": 1500000, "LEGENDARY": 5000000},
}

DEFAULT_BASE = {"height": 2.0, "front": 0.25, "side": 0.35, "upper": 2.0}

def get_canonical_hp(level, rating):
    """Obtém ou interpola o HP canônico para o nível e rating."""
    rating = rating.upper()
    known_lvls = sorted(HP_TABLE.keys())
    if level in HP_TABLE and rating in HP_TABLE[level]:
        return HP_TABLE[level][rating]
    
    # Se fora dos limites
    if level <= known_lvls[0]:
        return HP_TABLE[known_lvls[0]].get(rating, 18756)
    if level >= known_lvls[-1]:
        base_hp = HP_TABLE[known_lvls[-1]].get(rating, 35000)
        # Crescimento moderado para níveis acima de 70
        return int(base_hp * (1.0 + (level - known_lvls[-1]) * 0.05))
    
    # Interpolação entre os dois níveis conhecidos mais próximos
    for i in range(len(known_lvls) - 1):
        l1, l2 = known_lvls[i], known_lvls[i + 1]
        if l1 <= level <= l2:
            hp1 = HP_TABLE[l1].get(rating, 20000)
            hp2 = HP_TABLE[l2].get(rating, 25000)
            f = (level - l1) / (l2 - l1)
            return int(hp1 + f * (hp2 - hp1))
            
    return 20000

def parse_npc_name_for_stats(name, default_level):
    """
    Analisa o nome interno para deduzir level, rating e rank.
    Exemplos:
      LDF4b_T4_Basilisk_60_An -> (60, 'NORMAL', 'SEASONED')
      TDown_DrakanGiant_60_Ae -> (60, 'ELITE', 'EXPERT')
      LDF4_TEVA_Seiren_Queen_70_Ah -> (70, 'HERO', 'VETERAN')
    """
    name_upper = name.upper()
    # 1. Se for objeto, caixa, torre, trigger, porta, semente estática
    is_object = any(k in name_upper for k in [
        "TREASUREBOX", "CHEST", "WINDBOX", "TOWER", "DOOR", "WALL", "TRIGGER",
        "BARRIER", "DEVICE", "GATE_SUMMONER", "FOBJ", "SEED"
    ])
    if is_object:
        return default_level, "JUNK", "NOVICE"

    # 2. Padrão oficial NCSoft com sufixo de nível e rank (ex: _60_An, _60_Ae, _70_Ah, _60_Af)
    m = re.search(r'_(\d+)_A([nehjlfNEHJLF])\b', name)
    if not m:
        m = re.search(r'_(\d+)_([nehjlfNEHJLF])\b', name)
    if m:
        lvl = int(m.group(1))
        kind = m.group(2).lower()
        rating_map = {
            "n": ("NORMAL", "SEASONED" if lvl >= 60 else "DISCIPLINED"),
            "e": ("ELITE", "EXPERT"),
            "h": ("HERO", "VETERAN"),
            "f": ("HERO", "VETERAN"),
            "l": ("LEGENDARY", "MASTER"),
            "j": ("JUNK", "NOVICE")
        }
        rat, rk = rating_map.get(kind, ("NORMAL", "DISCIPLINED"))
        return lvl, rat, rk

    # 3. Se tiver número de nível plausível (50 a 85 para Balaurea/Classic 5.0)
    m = re.search(r'_([5-8]\d)\b', name)
    if m:
        lvl = int(m.group(1))
        is_hero = any(k in name_upper for k in ["BOSS", "QUEEN", "KING", "LORD", "HERO"])
        is_elite = any(k in name_upper for k in ["ELITE", "NAMED", "GUARD"])
        if is_hero:
            return lvl, "HERO", "VETERAN"
        if is_elite:
            return lvl, "ELITE", "EXPERT"
        return lvl, "NORMAL", "SEASONED" if lvl >= 60 else "DISCIPLINED"

    # 4. Fallback padrão
    is_hero = any(k in name_upper for k in ["BOSS", "QUEEN", "KING", "LORD", "HERO"])
    is_elite = any(k in name_upper for k in ["ELITE", "NAMED", "GUARD"])
    if is_hero:
        return default_level, "HERO", "VETERAN"
    if is_elite:
        return default_level, "ELITE", "EXPERT"
    return default_level, "NORMAL", "DISCIPLINED"

def render_template(npc_id, d, level, rating, rank, hp, tabs, base, n2id, n2b):
    chave = (d.get("desc") or "").upper()
    a = [("npc_id", str(npc_id)), ("level", str(level))]
    
    nome_exibicao = n2b.get(chave) or d.get("name") or "NPC"
    a.append(("name", nome_exibicao))
    
    name_id = n2id.get(chave) or 0
    a.append(("name_id", str(name_id)))

    sc, mesh = R.fnum(d.get("scale")), d.get("mesh")
    b = base.get(mesh or "") or DEFAULT_BASE
    
    doCliente = R.novos_atributos(d, tabs, base)
    doCliente.setdefault("ai", "general" if rating == "JUNK" else "aggressive" if "A" in d.get("name", "") else "general")
    doCliente.setdefault("tribe", "GENERAL")
    doCliente.setdefault("type", "MONSTER" if rating in ["NORMAL", "ELITE", "HERO", "LEGENDARY"] else "GENERAL")
    
    if "height" not in doCliente and sc and b.get("height"):
        doCliente["height"] = R.limpa(b["height"] * sc / 100)
        
    for k in ("height", "tribe", "type", "ai", "srange", "arange", "attack_speed", "hpgauge"):
        if k in doCliente:
            a.append((k, doCliente[k]))
            
    a.append(("rating", rating))
    a.append(("rank", rank))
    if "race" in doCliente:
        a.append(("race", doCliente["race"]))
    a.append(("group_drop", "NONE"))

    cabeca = "\t<npc_template " + " ".join('{}="{}"'.format(k, R.esc(str(v))) for k, v in a) + ">"
    filhos = []
    
    vel = [(sk, R.limpa(v)) for sk, ck in R.SPEEDS if (v := R.fnum(d.get(ck))) is not None]
    if vel:
        filhos.append(f'\t\t<stats maxHp="{hp}">')
        filhos.append("\t\t\t<speeds " + " ".join('{}="{}"'.format(k, v) for k, v in vel) + " />")
        filhos.append("\t\t</stats>")
    else:
        filhos.append(f'\t\t<stats maxHp="{hp}" />')
        
    if sc and all(e in b for e in R.EIXOS):
        filhos.append("\t\t<bound_radius " + " ".join('{}="{}"'.format(e, R.limpa(b[e] * sc / 100)) for e in R.EIXOS) + " />")
        
    return cabeca + NL + NL.join(filhos) + NL + "\t</npc_template>" + NL

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cliente", default=CLIENT_XML_DIR, help="Diretório dos dados XML do cliente 5.0")
    parser.add_argument("--aplicar", action="store_true", help="Aplica as modificações no npc_templates.xml com backup")
    args = parser.parse_args()

    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit(f"Arquivo client_npcs.xml não encontrado em: {npcs_xml}")

    print("1. Lendo banco de dados do cliente e servidor...")
    n2id, n2b = load_strings(args.cliente)
    
    print("   Lendo client_npcs.xml...")
    cli = {}
    cli_by_name = {}
    for d in iter_depth1(npcs_xml):
        nid = d.get("id")
        name = d.get("name")
        if nid:
            cli[nid] = d
        if name and nid:
            cli_by_name[name.lower()] = d

    server_xml_path = os.path.join(bm.SERVER_DATA_DIR, REL_XML)
    text, srv = R.le_servidor(server_xml_path)
    print(f"   Templates existentes no servidor: {len(srv)}")

    print("2. Aprendendo tabelas de conversão a partir do gabarito...")
    comuns = set(srv) & set(cli)
    bons = [i for i in comuns if n2id.get((cli[i].get("desc") or "").upper()) == srv[i]["attrs"].get("name_id")]
    tabs = {a: R.aprende(bons, srv, cli, a, c) for a, c in (("tribe", "tribe"), ("ai", "ai_name"),
                                                            ("race", "race_type"), ("type", "npc_type"))}
    base = R.bases_por_mesh(bons, srv, cli)

    print("3. Avaliando spawns dos 3 mapas...")
    missing_targets = {} # npc_id -> (client_dict, level, rating, rank, max_hp, map_name, count)

    for map_label, mission_file, default_lvl in MAPS:
        if not os.path.isfile(mission_file):
            print(f"   [AVISO] Arquivo não encontrado: {mission_file}")
            continue
        
        tree = ET.parse(mission_file)
        for obj in tree.getroot().findall(".//Object"):
            t = (obj.get("Type") or obj.get("type") or "").upper()
            if t in ["SP", "NPC", "MONSTER"]:
                obj_name = obj.get("Name") or obj.get("name") or ""
                npc_attr = (obj.get("npc") or obj.get("Entity") or obj.get("entity") or "").strip()
                candidates = []
                if npc_attr:
                    candidates.append(npc_attr)
                if obj_name:
                    candidates.append(obj_name)
                    c = re.sub(r'^(SP_|SMP_|HSP_)', '', obj_name, flags=re.IGNORECASE)
                    candidates.append(c)
                    candidates.append(re.sub(r'_\d+$', '', c))
                    candidates.append(re.sub(r'\d+$', '', c))
                
                info = None
                for cand in candidates:
                    info = cli_by_name.get(cand.lower())
                    if info:
                        break
                if not info:
                    continue
                
                nid = info.get("id")
                if nid and nid not in srv and nid not in missing_targets:
                    lvl, rating, rank = parse_npc_name_for_stats(info.get("name", ""), default_lvl)
                    hp = get_canonical_hp(lvl, rating)
                    missing_targets[nid] = (info, lvl, rating, rank, hp, map_label)

    print(f"\nTotal de NPCs faltantes identificados para os 3 mapas: {len(missing_targets)}")
    
    # Sumário por mapa e rating
    summary = collections.defaultdict(int)
    for nid, (info, lvl, rating, rank, hp, map_label) in missing_targets.items():
        summary[(map_label, rating)] += 1
        
    for (m_label, rat), cnt in sorted(summary.items()):
        print(f"   [{m_label}] Rating {rat:9}: {cnt:3} NPCs")

    print("\nExemplos de templates a serem criados:")
    for nid, (info, lvl, rating, rank, hp, map_label) in list(missing_targets.items())[:8]:
        nome = info.get("name", "")
        desc = info.get("desc", "")
        print(f"   ID: {nid:7} | Nível: {lvl:2} | {rating:7} ({rank:11}) | HP: {hp:8} | {nome} ({desc}) [{map_label}]")

    if not missing_targets:
        print("\nNenhum NPC faltando. Tudo sincronizado.")
        return

    # insere cada um mantendo a ordem por npc_id
    novo = text
    for nid in sorted(missing_targets.keys(), key=int):
        info, lvl, rating, rank, hp, map_label = missing_targets[nid]
        bloco = render_template(nid, info, lvl, rating, rank, hp, tabs, base, n2id, n2b)
        pos = [m.start() for m in re.finditer(r'\t<npc_template npc_id="(\d+)"', novo) if int(m.group(1)) > int(nid)]
        corte = pos[0] if pos else novo.rindex("</npc_templates>")
        novo = novo[:corte] + bloco + novo[corte:]

    try:
        from lxml import etree
        schema = etree.XMLSchema(etree.parse(os.path.join(bm.SERVER_DATA_DIR, REL_XSD)))
        if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print(f"   XSD linha {e.line}: {e.message}")
            sys.exit("XSD inválido: nada foi gravado.")
        print(f"   XSD validado com sucesso! Templates: {len(srv)} -> {len(srv) + len(missing_targets)}")
    except ImportError:
        print("   [AVISO] lxml não disponível para validação XSD estrita; conferindo formato XML...")
        ET.fromstring(novo.encode("utf-8"))
        print(f"   XML sintaticamente válido! Templates: {len(srv)} -> {len(srv) + len(missing_targets)}")

    if not args.aplicar:
        print("\n[DRY-RUN] Nenhuma alteração gravada. Para aplicar, execute com --aplicar.")
        return

    import shutil
    print("\n5. Aplicando alterações em npc_templates.xml com backup...")
    sess = bm.init_backup_session("import_maps_npcs_50")
    for rotulo, b in (("GameServer", bm.SERVER_DATA_DIR), ("ProdutoFinal", bm.PRODUTO_FINAL_DATA_DIR)):
        p = os.path.join(b, REL_XML)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(sess, rotulo + "_npc_templates.xml"))
            with open(p, "wb") as f:
                f.write(novo.encode("utf-8"))
            print("   Gravado com sucesso: " + p)
    print(f"\nConcluído! {len(missing_targets)} novos templates foram adicionados.")

if __name__ == "__main__":
    main()
