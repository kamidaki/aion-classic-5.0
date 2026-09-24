import os
import sys
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(PARSERS_DIR)))
import os
import re
import shutil
import xml.etree.ElementTree as ET

# Paths
BASE_GS = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "GameServer")
PROD_GS = os.path.join(PROJECT_ROOT, "Emulador - Produto Final", "GameServer")

AI_DIR = os.path.join(BASE_GS, r"data\scripts\system\handlers\ai")
WORLDS_DIR = os.path.join(AI_DIR, "worlds")

SPAWNS_DIR = os.path.join(BASE_GS, r"data\static_data\spawns")
WORLD_MAPS_XML = os.path.join(BASE_GS, r"data\static_data\world_maps.xml")
NPC_TEMPLATES_XML = os.path.join(BASE_GS, r"data\static_data\npcs\npc_templates.xml")

# Map ID to World Folder mapping
MAP_TO_FOLDER = {
    "110010000": "sanctum",
    "110020000": "kaisinel",
    "110070000": "sanctum",
    "120010000": "pandaemonium",
    "120020000": "marchutan",
    "120080000": "pandaemonium",
    "210010000": "poeta",
    "210020000": "eltnen",
    "210030000": "verteron",
    "210040000": "heiron",
    "210050000": "inggison",
    "210060000": "theobomos",
    "210070000": "telos",
    "220010000": "ishalgen",
    "220020000": "morheim",
    "220030000": "altgard",
    "220040000": "beluslan",
    "220050000": "brusthonin",
    "220070000": "gelkmaros",
    "220080000": "telos",
    "400010000": "reshanta",
    "510010000": "sanctum",
    "520010000": "pandaemonium",
    "600010000": "silentera_canyon",
    # Instance maps
    "300030000": "nochsana",
    "300040000": "darkPoeta",
    "300050000": "asteria",
    "300070000": "chamberOfRoah",
    "300080000": "leftWing",
    "300100000": "steelRake",
    "300110000": "dredgion",
    "300150000": "udasTemple",
    "300151000": "udasTemple",
    "300160000": "lowerUdasTemple",
    "300161000": "lowerUdasTemple",
    "300170000": "beshmundirTemple",
    "300190000": "tallocsHollow",
    "300200000": "kromedesTrial",
    "300210000": "dredgion",
    "300220000": "abyssalSplinter",
    "300230000": "kromedesTrial",
    "300250000": "esoterrace",
    "300300000": "arena",
    "300310000": "raksha",
    "300320000": "arena",
    "300350000": "empyreanCrucible",
    "300360000": "crucibleChallenge",
    "300420000": "arena",
    "300430000": "arena",
    "300440000": "terathDredgion",
    "300460000": "tiakResearchBase",
    "300470000": "arena",
    "300500000": "esoterrace",
    "300510000": "esoterrace",
    "300540000": "telos",
    "300550000": "telos",
    "300560000": "telos",
    "310050000": "indratuFortress",
    "310090000": "indratuFortress",
    "310100000": "lepharistResearchCenter",
    "310110000": "alquimiaResearchCenter",
    "320080000": "draupnirCave",
    "320100000": "fireTemple",
    "320110000": "aetherogeneticsLab",
    "320130000": "admaStronghold",
    "320140000": "ataxiar",
    "320150000": "padmarashkaCave",
}

def sanitize_class_name(name):
    # Strip any whitespace
    clean = name.strip()
    # Replace any non-alphanumeric/underscore char with underscore
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', clean)
    # Ensure it doesn't start with digit
    if clean and clean[0].isdigit():
        clean = "AI_" + clean
    if not clean.endswith("AI2"):
        clean += "AI2"
    return clean

def infer_folder_from_name(ai_name):
    upper = ai_name.upper()
    if upper.startswith("AB1_") or upper.startswith("AB_") or "RESHANTA" in upper or "ABYSS" in upper:
        return "reshanta"
    if upper.startswith("LF1_") or "POETA" in upper:
        return "poeta"
    if upper.startswith("LF2_") or "ELTNEN" in upper:
        return "eltnen"
    if upper.startswith("LF1A_") or "VERTERON" in upper:
        return "verteron"
    if upper.startswith("LF3_") or "HEIRON" in upper:
        return "heiron"
    if upper.startswith("LF4_") or "INGGISON" in upper:
        return "inggison"
    if upper.startswith("LF2A_") or "THEOBOMOS" in upper:
        return "theobomos"
    if upper.startswith("LDF1_") or "TELOS" in upper:
        return "telos"
    if upper.startswith("DF1_") or "ISHALGEN" in upper:
        return "ishalgen"
    if upper.startswith("DF2_") or "MORHEIM" in upper:
        return "morheim"
    if upper.startswith("DF1A_") or "ALTGARD" in upper:
        return "altgard"
    if upper.startswith("DF3_") or "BELUSLAN" in upper:
        return "beluslan"
    if upper.startswith("DF2A_") or "BRUSTHONIN" in upper:
        return "brusthonin"
    if upper.startswith("DF4_") or "GELKMAROS" in upper:
        return "gelkmaros"
    if upper.startswith("LC1_") or "SANCTUM" in upper:
        return "sanctum"
    if upper.startswith("DC1_") or "PANDAEMONIUM" in upper:
        return "pandaemonium"
    if "SILENTERA" in upper or "UNDERPASS" in upper:
        return "silentera_canyon"
    if upper.startswith("ID") or "DUNGEON" in upper or "INSTANCE" in upper:
        return "instances"
    return "general"

def main():
    print("=" * 80)
    print(" INICIANDO GERADOR DE IA FALTANTES (WORLD AI HANDLERS)")
    print("=" * 80)

    # 1. Carregar mapeamento de Spawns (npc_id -> set(map_id))
    print("[1/5] Carregando mapa de spawns...")
    npc_to_maps = {}
    for f in os.listdir(SPAWNS_DIR):
        if f.endswith(".xml"):
            map_id = f.replace(".xml", "")
            p = os.path.join(SPAWNS_DIR, f)
            try:
                tree_s = ET.parse(p)
                for spawn in tree_s.getroot().findall(".//spawn"):
                    nid = spawn.get("npc_id")
                    if nid:
                        if nid not in npc_to_maps:
                            npc_to_maps[nid] = set()
                        npc_to_maps[nid].add(map_id)
            except Exception as e:
                pass
    print(f"  -> {len(npc_to_maps)} NPCs com spawn mapeado.")

    # 2. Carregar AIs já existentes em handlers/ai
    print("[2/5] Mapeando AIs já existentes...")
    existing_ais = set()
    existing_filenames = set()
    for root, dirs, files in os.walk(AI_DIR):
        for f in files:
            if f.endswith('.java'):
                existing_filenames.add(f.lower())
                with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    matches = re.findall(r'@AIName\s*\(\s*"([^"]+)"\s*\)', content)
                    for m in matches:
                        existing_ais.add(m)
                        existing_ais.add(m.strip())
                        existing_ais.add(m.lower())
                        existing_ais.add(m.strip().lower())
    print(f"  -> {len(existing_ais)//4} AIs já registradas.")

    # 3. Ler todos os NPCs em npc_templates.xml
    print("[3/5] Analisando npc_templates.xml...")
    tree_npc = ET.parse(NPC_TEMPLATES_XML)
    ai_to_npcs = {}
    ai_to_maps = {}

    for npc in tree_npc.getroot().findall("npc_template"):
        ai = npc.get("ai")
        nid = npc.get("npc_id")
        if ai:
            ai_clean = ai.strip()
            if not ai_clean:
                continue
            if ai_clean not in ai_to_npcs:
                ai_to_npcs[ai_clean] = []
                ai_to_maps[ai_clean] = set()
            ai_to_npcs[ai_clean].append(nid)
            if nid in npc_to_maps:
                for mid in npc_to_maps[nid]:
                    ai_to_maps[ai_clean].add(mid)

    # Identificar as que faltam
    missing_ais = {}
    for ai, npcs in ai_to_npcs.items():
        if ai not in existing_ais and ai.lower() not in existing_ais:
            missing_ais[ai] = {
                "npcs": npcs,
                "maps": ai_to_maps[ai]
            }

    print(f"  -> Total de AIs únicas faltantes para gerar: {len(missing_ais)}")

    # 4. Gerar os arquivos .java nas pastas de mundos
    print("[4/5] Gerando handlers de IA em data/scripts/system/handlers/ai/worlds/...")
    
    # Garantir pasta worlds
    if not os.path.exists(WORLDS_DIR):
        os.makedirs(WORLDS_DIR)

    created_count = 0
    folder_stats = {}
    used_classes_per_folder = {}

    for ai_name, data in missing_ais.items():
        # Determinar a pasta de destino
        target_folder = None
        maps = data["maps"]
        if maps:
            # Pegar o primeiro mapa com mapeamento conhecido
            for mid in maps:
                if mid in MAP_TO_FOLDER:
                    target_folder = MAP_TO_FOLDER[mid]
                    break
        
        if not target_folder:
            # Inferir pelo prefixo da IA
            target_folder = infer_folder_from_name(ai_name)

        # Pasta no filesystem
        folder_path = os.path.join(WORLDS_DIR, target_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if target_folder not in used_classes_per_folder:
            used_classes_per_folder[target_folder] = set()

        # Nome da classe
        base_class_name = sanitize_class_name(ai_name)
        class_name = base_class_name
        suffix = 1
        while class_name.lower() in used_classes_per_folder[target_folder]:
            suffix += 1
            class_name = f"{base_class_name}_{suffix}"
        
        used_classes_per_folder[target_folder].add(class_name.lower())

        file_path = os.path.join(folder_path, f"{class_name}.java")
        
        # Conteúdo da classe Java
        java_code = f"""package ai.worlds.{target_folder};

import ai.AggressiveNpcAI2;
import com.aionemu.gameserver.ai2.AIName;

/**
 * Auto-generated 5.0 AI Handler based on AggressiveNpcAI2
 * Original AI Name: {ai_name}
 */
@AIName("{ai_name}")
public class {class_name} extends AggressiveNpcAI2
{{
}}
"""
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write(java_code)

        created_count += 1
        folder_stats[target_folder] = folder_stats.get(target_folder, 0) + 1

    print(f"  -> Sucesso: {created_count} arquivos de IA gerados em {len(folder_stats)} pastas de mundos!")
    for folder, count in sorted(folder_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"     • worlds/{folder}: {count} IAs")

    # 5. Sincronizar para PRODUTO FINAL
    print("[5/5] Sincronizando scripts de IA para PRODUTO FINAL...")
    prod_ai_worlds = os.path.join(PROD_GS, r"data\scripts\system\handlers\ai\worlds")
    if not os.path.exists(prod_ai_worlds):
        os.makedirs(prod_ai_worlds)

    for root, dirs, files in os.walk(WORLDS_DIR):
        rel = os.path.relpath(root, WORLDS_DIR)
        dest_root = os.path.join(prod_ai_worlds, rel) if rel != "." else prod_ai_worlds
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)
        for f in files:
            if f.endswith(".java"):
                src_file = os.path.join(root, f)
                dest_file = os.path.join(dest_root, f)
                shutil.copy2(src_file, dest_file)

    print("  -> PRODUTO FINAL sincronizado com 100% de sucesso!")
    print("=" * 80)

if __name__ == "__main__":
    main()
