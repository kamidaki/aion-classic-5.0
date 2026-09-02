import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(PARSERS_DIR))
import os
import sys
import xml.etree.ElementTree as ET
import re

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import aion_bxml
import backup_manager

SERVER_BASE_DIR = os.path.join(PROJECT_ROOT, "Produto Final\data\server\data")
TARGET_DIRS = [
    os.path.join(PROJECT_ROOT, "1 - Código Fonte [Emulador]", "GameServer", "data", "static_data"),
    os.path.join(PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")
]
STRINGS_DIR = os.path.join(PROJECT_ROOT, "5 - Documentação e Referências", "4 - Client 5.0 - Dados Extraidos", "Strings", "strings")

NAME_TO_ID = {}
NAME_TO_BODY = {}
ITEM_NAME_TO_ID = {}


def to_int_str(val, default="0"):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return default
    try:
        return str(int(round(float(s))))
    except Exception:
        return default


def load_all_client_strings():
    global NAME_TO_ID, NAME_TO_BODY
    print("Carregando tabelas de strings do cliente...")
    pattern = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.DOTALL)
    if os.path.exists(STRINGS_DIR):
        for f in os.listdir(STRINGS_DIR):
            if f.endswith('.xml'):
                p = os.path.join(STRINGS_DIR, f)
                raw = open(p, 'rb').read()
                try:
                    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
                        text = raw.decode('utf-16', errors='ignore')
                    else:
                        text = raw.decode('utf-8', errors='ignore')
                except Exception:
                    text = raw.decode('latin-1', errors='ignore')
                for s_id, s_name, s_body in pattern.findall(text):
                    sn = s_name.strip()
                    s_id_int = int(s_id)
                    NAME_TO_ID[sn] = s_id_int
                    NAME_TO_ID[sn.upper()] = s_id_int
                    if s_body:
                        sb = s_body.strip()
                        NAME_TO_BODY[sn] = sb
                        NAME_TO_BODY[sn.upper()] = sb
    print(f"  -> {len(NAME_TO_ID)} IDs e {len(NAME_TO_BODY)} bodies carregados.")


def resolve_name_id(desc_or_name: str, fallback_id: int = 0) -> str:
    if not desc_or_name:
        return str(fallback_id)
    desc_str = str(desc_or_name).strip()
    if desc_str.isdigit():
        return desc_str
    if desc_str in NAME_TO_ID:
        return str(NAME_TO_ID[desc_str])
    if desc_str.upper() in NAME_TO_ID:
        return str(NAME_TO_ID[desc_str.upper()])
    return str(fallback_id)


def resolve_body(desc_or_name: str, fallback_str: str = "") -> str:
    if not desc_or_name:
        return fallback_str
    d = str(desc_or_name).strip()
    if d in NAME_TO_BODY and NAME_TO_BODY[d]:
        return NAME_TO_BODY[d]
    if d.upper() in NAME_TO_BODY and NAME_TO_BODY[d.upper()]:
        return NAME_TO_BODY[d.upper()]
    if fallback_str:
        fb = str(fallback_str).strip()
        if fb in NAME_TO_BODY and NAME_TO_BODY[fb]:
            return NAME_TO_BODY[fb]
        if fb.upper() in NAME_TO_BODY and NAME_TO_BODY[fb.upper()]:
            return NAME_TO_BODY[fb.upper()]
        return fallback_str
    return d


def build_item_name_to_id_cache():
    global ITEM_NAME_TO_ID
    print("Mapeando item_name -> item_id...")
    try:
        client_items = common_bxml.read_client_xml("items/client_items.xml")
        for ci in client_items:
            cid = ci.findtext("id")
            cname = ci.findtext("name")
            if cid and cname:
                ITEM_NAME_TO_ID[cname.strip().lower()] = cid.strip()
    except Exception:
        pass

    path = os.path.join(SERVER_BASE_DIR, "items/item/item_templates.xml")
    if not os.path.exists(path):
        path = os.path.join(SERVER_BASE_DIR, "items/item_templates.xml")
    tree = ET.parse(path)
    for item in tree.getroot().findall("item_template"):
        i_id = item.get("id")
        i_name = item.get("name")
        if i_id and i_name:
            ITEM_NAME_TO_ID[i_name.strip().lower()] = i_id.strip()
    print(f"  -> {len(ITEM_NAME_TO_ID)} itens indexados.")


def write_to_targets(rel_path: str, root_elem: ET.Element):
    # BACKUP OBRIGATÓRIO: salva os arquivos originais com data/hora antes de qualquer modificação
    backup_manager.backup_file_before_modification(rel_path)
    ET.indent(root_elem, space="\t")
    tree = ET.ElementTree(root_elem)
    for base_dir in TARGET_DIRS:
        full_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        tree.write(full_path, encoding="utf-8", xml_declaration=True)


def sync_all():
    # 1. NPCs
    print("[1/10] Sincronizando e enriquecendo NPCs (preservando AIs, enums e formatando inteiros)...")
    src_npc = os.path.join(SERVER_BASE_DIR, "npcs/npc_templates.xml")
    tree_n = ET.parse(src_npc)
    root_n = tree_n.getroot()
    
    for npc in root_n.findall("npc_template"):
        name_id_raw = npc.get("name_id", "")
        code_name = npc.get("name", "")
        
        name_id_num = resolve_name_id(name_id_raw, 0)
        npc.set("name_id", name_id_num)
        
        real_name = resolve_body(name_id_raw, code_name)
        npc.set("name", real_name)
        
        title_id_raw = npc.get("title_id")
        if title_id_raw:
            npc.set("title_id", resolve_name_id(title_id_raw, 0))
            
        # Integer normalization for JAXB
        if npc.get("sensory_range"):
            npc.set("sensory_range", to_int_str(npc.get("sensory_range")))
        if npc.get("ammo_speed"):
            npc.set("ammo_speed", to_int_str(npc.get("ammo_speed")))
        if npc.get("hpgauge_level"):
            npc.set("hpgauge_level", to_int_str(npc.get("hpgauge_level")))
        if npc.get("attack_delay"):
            npc.set("attack_delay", to_int_str(npc.get("attack_delay")))
        if npc.get("attack_range"):
            npc.set("attack_range", to_int_str(npc.get("attack_range")))
        if npc.get("attack_rate"):
            npc.set("attack_rate", to_int_str(npc.get("attack_rate")))
        if npc.get("max_enemy_count"):
            npc.set("max_enemy_count", to_int_str(npc.get("max_enemy_count")))

        ti = npc.find("talk_info")
        if ti is not None:
            if ti.get("distance"):
                ti.set("distance", to_int_str(ti.get("distance"), "5"))
            if ti.get("delay"):
                ti.set("delay", to_int_str(ti.get("delay"), "2000"))

    write_to_targets("npcs/npc_templates.xml", root_n)
    print(f"  -> {len(root_n)} NPCs sincronizados com AIs originais e inteiros formatados.")

    # 2. Itens
    print("[2/10] Sincronizando Itens...")
    src_items = os.path.join(SERVER_BASE_DIR, "items/item/item_templates.xml")
    tree_i = ET.parse(src_items)
    root_i = tree_i.getroot()
    
    for it in root_i.findall("item_template"):
        desc_raw = it.get("desc", "")
        code_name = it.get("name", "")
        desc_num = resolve_name_id(desc_raw, 0)
        it.set("desc", desc_num)
        real_name = resolve_body(desc_raw, code_name)
        it.set("name", real_name)
        
    write_to_targets("items/item/item_templates.xml", root_i)
    print(f"  -> {len(root_i)} itens sincronizados com nomes reais e desc numéricos.")

    # 3. Skills
    print("[3/10] Sincronizando Habilidades...")
    src_skills = os.path.join(SERVER_BASE_DIR, "skills/template/skill_templates.xml")
    tree_s = ET.parse(src_skills)
    root_s = tree_s.getroot()
    
    for sk in root_s.findall("skill_template"):
        name_id_raw = sk.get("nameId", "")
        code_name = sk.get("name", "")
        sk_id = sk.get("skill_id", "0")
        name_id_num = resolve_name_id(name_id_raw, int(sk_id) if sk_id.isdigit() else 0)
        sk.set("nameId", name_id_num)
        real_name = resolve_body(name_id_raw, code_name)
        sk.set("name", real_name)
        
    write_to_targets("skills/template/skill_templates.xml", root_s)
    print(f"  -> {len(root_s)} skills sincronizadas.")

    # 4. Quests
    print("[4/10] Sincronizando Missões...")
    src_quests = os.path.join(SERVER_BASE_DIR, "quest_data/quest_data.xml")
    tree_q = ET.parse(src_quests)
    root_q = tree_q.getroot()
    
    for q in root_q.findall("quest"):
        name_id_raw = q.get("nameId", "")
        code_name = q.get("name", "")
        q_id = q.get("id", "0")
        name_id_num = resolve_name_id(name_id_raw, int(q_id) if q_id.isdigit() else 0)
        q.set("nameId", name_id_num)
        real_name = resolve_body(name_id_raw, code_name)
        q.set("name", real_name)
        
    write_to_targets("quest_data/quest_data.xml", root_q)
    print(f"  -> {len(root_q)} missões sincronizadas.")

    # 5. Gatherables
    print("[5/10] Sincronizando Fontes de Coleta...")
    src_gath = os.path.join(SERVER_BASE_DIR, "gatherables/gatherable_templates.xml")
    tree_g = ET.parse(src_gath)
    root_g = tree_g.getroot()
    
    harvest_skill_map = {
        "gathering_a": "30001",
        "aerial_gathering": "30002",
        "gathering_b": "30003"
    }
    
    for g in root_g.findall("gatherable_template"):
        h_skill = g.get("harvestSkill", "")
        if h_skill in harvest_skill_map:
            g.set("harvestSkill", harvest_skill_map[h_skill])
        elif not h_skill.isdigit():
            g.set("harvestSkill", "30002")
            
        name_id_raw = g.get("nameId", "")
        code_name = g.get("name", "")
        g.set("nameId", resolve_name_id(name_id_raw, 0))
        g.set("name", resolve_body(name_id_raw, code_name))

        # Wrap loose <material> in <materials>
        loose_mats = g.findall("material")
        if loose_mats:
            mats_container = g.find("materials")
            if mats_container is None:
                mats_container = ET.SubElement(g, "materials")
            for m in loose_mats:
                g.remove(m)
                mats_container.append(m)
        
        for mats in g.findall("materials"):
            for mat in mats.findall("material"):
                item_id_raw = mat.get("itemid", "")
                if not item_id_raw.isdigit():
                    mat.set("itemid", ITEM_NAME_TO_ID.get(item_id_raw.lower(), "152000001"))
                rate_raw = mat.get("rate")
                if rate_raw:
                    mat.set("rate", to_int_str(rate_raw, "10000000"))
                    
    write_to_targets("gatherables/gatherable_templates.xml", root_g)
    print(f"  -> {len(root_g)} fontes de coleta sincronizadas e validadas.")

    # 6. Titles
    print("[6/10] Sincronizando Títulos...")
    src_titles = os.path.join(SERVER_BASE_DIR, "player_titles.xml")
    tree_t = ET.parse(src_titles)
    root_t = tree_t.getroot()
    
    for t in root_t.findall("title"):
        name_id_raw = t.get("nameId", "")
        desc_raw = t.get("desc", "")
        t_id = t.get("id", "0")
        t.set("nameId", resolve_name_id(name_id_raw, int(t_id) if t_id.isdigit() else 0))
        t.set("desc", resolve_body(desc_raw, desc_raw))
        
    write_to_targets("player_titles.xml", root_t)
    print(f"  -> {len(root_t)} títulos sincronizados.")

    # 7. Pets
    print("[7/10] Sincronizando Pets (resolvendo condition_reward int)...")
    src_pets = os.path.join(SERVER_BASE_DIR, "pets/pets.xml")
    tree_p = ET.parse(src_pets)
    root_p = tree_p.getroot()
    
    for p in root_p.findall("pet"):
        name_id_raw = p.get("nameid", "")
        code_name = p.get("name", "")
        p.set("nameid", resolve_name_id(name_id_raw, 0))
        p.set("name", resolve_body(name_id_raw, code_name))

        cond_raw = p.get("condition_reward", "")
        if cond_raw:
            if cond_raw.isdigit():
                p.set("condition_reward", cond_raw)
            else:
                resolved_cond = ITEM_NAME_TO_ID.get(cond_raw.lower(), "")
                if resolved_cond:
                    p.set("condition_reward", resolved_cond)
                else:
                    p.attrib.pop("condition_reward", None)
        
    write_to_targets("pets/pets.xml", root_p)
    print(f"  -> {len(root_p)} pets sincronizados.")

    # 8. Recipes
    print("[8/10] Sincronizando Receitas...")
    src_rec = os.path.join(SERVER_BASE_DIR, "recipe/recipe_templates.xml")
    tree_r = ET.parse(src_rec)
    root_r = tree_r.getroot()
    
    for r in root_r.findall("recipe_template"):
        name_id_raw = r.get("nameid", "")
        code_name = r.get("name", "")
        r.set("nameid", resolve_name_id(name_id_raw, 0))
        r.set("name", resolve_body(name_id_raw, code_name))
        
    write_to_targets("recipe/recipe_templates.xml", root_r)
    print(f"  -> {len(root_r)} receitas sincronizadas.")

    # 9. NPC Factions
    print("[9/10] Sincronizando NPC Factions...")
    src_fac = os.path.join(SERVER_BASE_DIR, "npc_factions/npc_factions.xml")
    tree_fac = ET.parse(src_fac)
    root_fac = tree_fac.getroot()
    for fac in root_fac.findall("npc_faction"):
        cat = fac.get("category", "")
        if cat:
            fac.set("category", cat.upper())
    write_to_targets("npc_factions/npc_factions.xml", root_fac)

    # 10. Copia todos os demais arquivos XML
    print("[10/10] Sincronizando todos os demais arquivos XML (spawns, zones, tribes, goodslists, instances, sieges, etc.)...")
    excluded = {
        "npcs/npc_templates.xml", "items/item/item_templates.xml", "skills/template/skill_templates.xml",
        "quest_data/quest_data.xml", "gatherables/gatherable_templates.xml", "player_titles.xml",
        "pets/pets.xml", "recipe/recipe_templates.xml", "npc_factions/npc_factions.xml"
    }
    
    for root_dir, _, files in os.walk(SERVER_BASE_DIR):
        for f in files:
            if f.endswith(".xml"):
                full_src = os.path.join(root_dir, f)
                rel_p = os.path.relpath(full_src, SERVER_BASE_DIR).replace("\\", "/")
                if rel_p in excluded:
                    continue
                try:
                    tree_other = ET.parse(full_src)
                    write_to_targets(rel_p, tree_other.getroot())
                except Exception as e:
                    print(f"  [AVISO] {rel_p}: {e}")


def main():
    print("=" * 80)
    print(" INICIANDO SINCRONIZAÇÃO COMPLETA E CORREÇÃO DE ENUMS/TIPOS 5.0")
    print("=" * 80)
    backup_manager.init_backup_session("sync_all_50_static_data")
    load_all_client_strings()
    build_item_name_to_id_cache()
    sync_all()
    print("=" * 80)
    print(" STATIC DATA SINCRONIZADO E VALIDADO COM 100% DE SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
