"""
fix_50_skillbooks.py
Reconstrói as tags <actions><skilllearn .../></actions> para todos os Skill Books 5.0
a partir dos dados oficiais do Client 5.0 (client_items.xml, client_skills.xml, client_skill_learns.xml).

Idempotente, com backup_manager e validação XSD estrita.
"""
import collections
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402
from fix_50_energia_sp_ep import XMLS  # noqa: E402

REL_XML = os.path.join("items", "item_templates.xml")
REL_XSD = os.path.join("items", "item_templates.xsd")
RELATORIO = os.path.join(AQUI, "relatorio_skillbooks_50.txt")

CLASS_REMAP_LEARNS = {
    'gladiator': 'fighter',
    'templar': 'knight',
    'sorcerer': 'wizard',
    'spirit_master': 'elementallist',
    'spiritmaster': 'elementallist',
    'elementalist': 'elementallist',
    'gunslinger': 'gunner',
    'aethertech': 'thunderer',
    'rider': 'thunderer',
    'songweaver': 'lumines',
    'bard': 'lumines',
    'brawler': 'striker'
}

CLASS_TO_PLAYERCLASS = {
    'warrior': 'WARRIOR',
    'fighter': 'GLADIATOR',
    'gladiator': 'GLADIATOR',
    'knight': 'TEMPLAR',
    'templar': 'TEMPLAR',
    'scout': 'SCOUT',
    'assassin': 'ASSASSIN',
    'ranger': 'RANGER',
    'mage': 'MAGE',
    'wizard': 'SORCERER',
    'sorcerer': 'SORCERER',
    'elementallist': 'SPIRIT_MASTER',
    'elementalist': 'SPIRIT_MASTER',
    'spirit_master': 'SPIRIT_MASTER',
    'priest': 'PRIEST',
    'cleric': 'CLERIC',
    'chanter': 'CHANTER',
    'engineer': 'ENGINEER',
    'gunner': 'GUNNER',
    'thunderer': 'THUNDERER',
    'striker': 'BRAWLER',
    'brawler': 'BRAWLER',
    'lumines': 'LUMINESS',
    'luminess': 'LUMINESS',
}

CLASS_COMBOS = {
    frozenset(['fighter', 'knight']): 'WARRIOR',
    frozenset(['fighter', 'knight', 'warrior']): 'WARRIOR',
    frozenset(['assassin', 'ranger']): 'SCOUT',
    frozenset(['assassin', 'ranger', 'scout']): 'SCOUT',
    frozenset(['elementalist', 'wizard']): 'MAGE',
    frozenset(['elementalist', 'mage', 'wizard']): 'MAGE',
    frozenset(['chanter', 'cleric']): 'PRIEST',
    frozenset(['chanter', 'priest']): 'PRIEST',
    frozenset(['chanter', 'cleric', 'priest']): 'PRIEST',
    frozenset(['engineer', 'gunner']): 'ENGINEER',
}

POS_TAGS = re.compile(r"</(?:modifiers)>|<(?:actions|godstone|stigma|weapon_stats|tradein_list|acquisition|disposition|improve|uselimits|inventory|idian)\b")

def carregar_dados_cliente():
    print("1. Lendo dados do Client 5.0...")
    
    # 1. client_skills: name.lower() -> skill_id
    skills_path = os.path.join(XMLS, "skills", "client_skills.xml")
    t_skills = open(skills_path, "r", encoding="utf-8", errors="replace").read()
    skill_name_to_id = {}
    for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", t_skills):
        skill_name_to_id[m.group(2).strip().lower()] = int(m.group(1))
    skill_name_to_id['ch_phoenixstep_ad_g1'] = skill_name_to_id.get('ch_phoenixstep_g1', 2221)
    
    # 2. client_skill_learns: (skill_name_lower, class_str_lower) -> list of (pc_level, skill_level)
    learns_path = os.path.join(XMLS, "skills", "client_skill_learns.xml")
    t_learns = open(learns_path, "r", encoding="utf-8", errors="replace").read()
    learns_map = collections.defaultdict(list)
    for m in re.finditer(r"<client_skill_learn>.*?<class>([^<]+)</class>.*?<pc_level>(\d+)</pc_level>.*?<skill>([^<]+)</skill>.*?<skill_level>(\d+)</skill_level>", t_learns, re.S):
        cls = m.group(1).strip().lower()
        pc_lvl = int(m.group(2))
        s_name = m.group(3).strip().lower()
        s_lvl = int(m.group(4))
        learns_map[(s_name, cls)].append((pc_lvl, s_lvl))
        
    for k in learns_map:
        learns_map[k].sort(key=lambda x: x[0])
        
    # 3. client_items: mapear livros de habilidade
    items_path = os.path.join(XMLS, "items", "client_items.xml")
    t_items = open(items_path, "r", encoding="utf-8", errors="replace").read()
    
    class_candidates = ['warrior', 'fighter', 'knight', 'scout', 'assassin', 'ranger', 'mage', 'wizard', 'elementalist', 'priest', 'cleric', 'chanter', 'gunner', 'engineer', 'runeblade', 'runewarrior', 'thunderer', 'lumines', 'striker', 'brawler']
    
    livros_cliente = {}
    for m in re.finditer(r"<client_item>.*?</client_item>", t_items, re.S):
        txt = m.group(0)
        if "<skill_to_learn>" not in txt:
            continue
        iid = int(re.search(r"<id>(\d+)</id>", txt).group(1))
        s_to_learn = re.search(r"<skill_to_learn>([^<]+)</skill_to_learn>", txt).group(1).strip()
        s_key = s_to_learn.lower()
        item_lvl = int(re.search(r"<level>(\d+)</level>", txt).group(1))
        
        # Classes com requisito > 0
        classes_raw = []
        for c in class_candidates:
            cm = re.search(rf"<{c}>(\d+)</{c}>", txt)
            if cm and int(cm.group(1)) > 0:
                classes_raw.append((c, int(cm.group(1))))
                
        skill_id = skill_name_to_id.get(s_key)
        if not skill_id:
            continue
            
        # Determinar PlayerClass do enum
        active_class_names = [c for c, _ in classes_raw]
        fs = frozenset(active_class_names)
        player_class = None
        if len(active_class_names) == 1:
            player_class = CLASS_TO_PLAYERCLASS.get(active_class_names[0])
        elif fs in CLASS_COMBOS:
            player_class = CLASS_COMBOS[fs]
        elif len(active_class_names) > 10 or len(active_class_names) == 0:
            player_class = None # Todas as classes / sem restrição única
            
        # Determinar skill_level a partir de client_skill_learns
        skill_lvl = 1
        found_learn = False
        for c_raw, req_lvl in classes_raw:
            check_classes = [c_raw, CLASS_REMAP_LEARNS.get(c_raw, c_raw), 'all']
            for cc in check_classes:
                if (s_key, cc) in learns_map:
                    entries = learns_map[(s_key, cc)]
                    ref_lvl = max(req_lvl, item_lvl)
                    valid = [sl for pl, sl in entries if pl <= ref_lvl]
                    if valid:
                        skill_lvl = max(valid)
                        found_learn = True
                        break
            if found_learn:
                break
                
        livros_cliente[iid] = {
            'item_id': iid,
            'skill_id': skill_id,
            'skill_name': s_to_learn,
            'level': item_lvl,
            'player_class': player_class,
            'skill_level': skill_lvl,
            'from_learn': found_learn
        }
        
    print(f"   Livros mapeados no cliente: {len(livros_cliente)}")
    return livros_cliente

def montar_skilllearn_tag(livro):
    cls_attr = f' class="{livro["player_class"]}"' if livro["player_class"] else ""
    return f'<skilllearn skillid="{livro["skill_id"]}" level="{livro["level"]}"{cls_attr} skill_level="{livro["skill_level"]}" />'

def main():
    seco = "--dry" in sys.argv
    livros = carregar_dados_cliente()
    
    print("2. Processando item_templates.xml...")
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    with open(caminho, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    
    bloco_re = re.compile(r'(\t<item_template id="(\d+)"(?:[^>"]|"[^"]*")*?)(/>|>(.*?)</item_template>)', re.S)
    
    estatisticas = collections.Counter()
    detalhes_modificados = []
    
    def processar_item(m):
        head = m.group(1)
        iid = int(m.group(2))
        tail = m.group(3)
        
        livro = livros.get(iid)
        if not livro:
            return m.group(0)
            
        sk_tag = montar_skilllearn_tag(livro)
        
        if tail == "/>":
            # Item sem corpo
            estatisticas["criado_item_sem_corpo"] += 1
            detalhes_modificados.append((iid, "criado_item_sem_corpo", sk_tag))
            actions_block = f"\t\t<actions>{eol}\t\t\t{sk_tag}{eol}\t\t</actions>"
            return f"{head.rstrip()}>{eol}{actions_block}{eol}\t</item_template>"
            
        corpo = m.group(4)
        
        # Caso 1: Item já tem <actions>...</actions>
        actions_match = re.search(r"<actions>(.*?)</actions>", corpo, re.S)
        if actions_match:
            actions_content = actions_match.group(1)
            # Se já tem <skilllearn.../>, substitui
            if "<skilllearn" in actions_content:
                novo_actions_content = re.sub(r"<skilllearn[^>]*/>", sk_tag, actions_content)
                if novo_actions_content == actions_content:
                    return m.group(0) # Inalterado
                estatisticas["substituido_skilllearn_existente"] += 1
                detalhes_modificados.append((iid, "substituido_skilllearn_existente", sk_tag))
            else:
                # Adiciona skilllearn dentro de actions existente
                novo_actions_content = actions_content.rstrip() + f"{eol}\t\t\t{sk_tag}"
                estatisticas["adicionado_em_actions_existente"] += 1
                detalhes_modificados.append((iid, "adicionado_em_actions_existente", sk_tag))
                
            novo_corpo = corpo[:actions_match.start(1)] + novo_actions_content + corpo[actions_match.end(1):]
            return f"{head}>{novo_corpo}</item_template>"
            
        # Caso 2: Item tem corpo mas não tem <actions>
        estatisticas["criado_actions_em_corpo"] += 1
        detalhes_modificados.append((iid, "criado_actions_em_corpo", sk_tag))
        actions_block = f"\t\t<actions>{eol}\t\t\t{sk_tag}{eol}\t\t</actions>"
        
        # Encontrar posição válida de acordo com o XSD:
        # Modifiers -> Actions -> Godstone -> Stigma -> ...
        m_tag = POS_TAGS.search(corpo)
        if m_tag:
            if m_tag.group(0).startswith("</modifiers>"):
                pos = m_tag.end()
                novo_corpo = corpo[:pos] + eol + actions_block + corpo[pos:]
            else:
                pos = m_tag.start()
                novo_corpo = corpo[:pos] + actions_block + eol + corpo[pos:]
        else:
            novo_corpo = eol + actions_block + corpo
            
        return f"{head}>{novo_corpo}</item_template>"

    novo = bloco_re.sub(processar_item, raw)
    print("   Estatísticas de atualização:")
    for k, v in estatisticas.items():
        print(f"     - {k}: {v}")
    print(f"   Total de livros modificados: {len(detalhes_modificados)}")

    print("3. Validando XML resultante contra item_templates.xsd...")
    from lxml import etree
    schema_doc = etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD))
    schema = etree.XMLSchema(schema_doc)
    parsed_xml = etree.fromstring(novo.encode("utf-8"))
    if not schema.validate(parsed_xml):
        for e in list(schema.error_log)[:20]:
            print(f"   XSD linha {e.line}: {e.message}")
        sys.exit("ERRO: Validação XSD falhou! Nenhum arquivo modificado.")
    print("   XSD validado com SUCESSO absoluto!")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("=== RELATÓRIO DE ATUALIZAÇÃO DE SKILL BOOKS 5.0 ===\n\n")
        f.write("Estatísticas:\n")
        for k, v in estatisticas.items():
            f.write(f"  {k}: {v}\n")
        f.write(f"\nTotal processados: {len(detalhes_modificados)}\n\n")
        f.write("Amostra de livros atualizados:\n")
        for iid, motivo, tag in detalhes_modificados[:30]:
            f.write(f"Item {iid} [{motivo}]: {tag}\n")
    print(f"   Relatório salvo em: {RELATORIO}")

    if novo == raw:
        print("Nenhuma alteração necessária.")
        return

    if seco:
        print("--dry ativado: nenhum arquivo gravado.")
        return

    print("4. Gravando nos repositórios com backup...")
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print(f"   Gravado: {p}")

if __name__ == "__main__":
    main()
