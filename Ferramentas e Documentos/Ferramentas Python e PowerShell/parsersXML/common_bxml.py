"""
Módulo utilitário compartilhado para a suite de parsers XML 5.0 (tools/parsersXML/)
Fornece decodificação BXML de alta performance, leitura de XMLs do cliente e servidor,
resolução de strings (IDs e bodies), mapeamento de equipamentos, formatação e escrita segura
nos diretórios do GameServer e PRODUTO FINAL.
"""

import os
import sys
import xml.etree.ElementTree as ET
import re

TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Ferramentas Python')
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

PROJECT_ROOT = os.path.dirname(TOOLS_DIR)

import aion_bxml
import backup_manager

# Dynamic Client Directory resolution (supports AION_CLIENT_XML_DIR, workspace XMLS AION CLASSIC, or docs)
ALT_CLIENT_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "XMLS AION CLASSIC")
if os.environ.get("AION_CLIENT_XML_DIR") and os.path.exists(os.environ.get("AION_CLIENT_XML_DIR")):
    BASE_CLIENT = os.environ.get("AION_CLIENT_XML_DIR")
elif os.path.exists(os.path.join(ALT_CLIENT_DIR, "data", "skills", "client_skills.xml")):
    BASE_CLIENT = ALT_CLIENT_DIR
else:
    BASE_CLIENT = os.path.join(PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos")

CLIENT_DATA_DIR = os.path.join(BASE_CLIENT, "data")
CLIENT_STRINGS_DIR = os.path.join(BASE_CLIENT, "Strings", "strings")
SERVER_DATA_DIR = os.path.join(PROJECT_ROOT, "Código Fonte - Emulador", "game-server", "data", "static_data")
PRODUTO_FINAL_DATA_DIR = os.path.join(PROJECT_ROOT, "Emulador - Produto Final", "GameServer", "data", "static_data")

# String and Item Caches
_NAME_TO_ID = None
_NAME_TO_BODY = None
_ITEM_NAME_TO_ID = None


def load_strings():
    """Carrega todas as tabelas de strings do cliente para resolução de name_id e body."""
    global _NAME_TO_ID, _NAME_TO_BODY
    if _NAME_TO_ID is not None and _NAME_TO_BODY is not None:
        return _NAME_TO_ID, _NAME_TO_BODY

    _NAME_TO_ID = {}
    _NAME_TO_BODY = {}
    pattern = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.DOTALL)
    
    if os.path.exists(CLIENT_STRINGS_DIR):
        for f in os.listdir(CLIENT_STRINGS_DIR):
            if f.endswith('.xml'):
                p = os.path.join(CLIENT_STRINGS_DIR, f)
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
                    _NAME_TO_ID[sn] = s_id_int
                    _NAME_TO_ID[sn.upper()] = s_id_int
                    if s_body:
                        sb = s_body.strip()
                        _NAME_TO_BODY[sn] = sb
                        _NAME_TO_BODY[sn.upper()] = sb
    return _NAME_TO_ID, _NAME_TO_BODY


def resolve_name_id(desc_or_name: str, fallback_id: int = 0) -> str:
    """Resolve o ID numérico da string (usado em name_id, nameId, desc numérico)."""
    if not desc_or_name:
        return str(fallback_id)
    desc_str = str(desc_or_name).strip()
    if desc_str.isdigit():
        return desc_str
    n2id, _ = load_strings()
    if desc_str in n2id:
        return str(n2id[desc_str])
    if desc_str.upper() in n2id:
        return str(n2id[desc_str.upper()])
    return str(fallback_id)


def resolve_body(desc_or_name: str, fallback_str: str = "") -> str:
    """Resolve o texto descritivo real da tag body da string (usado no atributo name)."""
    if not desc_or_name:
        return fallback_str
    d = str(desc_or_name).strip()
    _, n2b = load_strings()
    if d in n2b and n2b[d]:
        return n2b[d]
    if d.upper() in n2b and n2b[d.upper()]:
        return n2b[d.upper()]
    if fallback_str:
        fb = str(fallback_str).strip()
        if fb in n2b and n2b[fb]:
            return n2b[fb]
        if fb.upper() in n2b and n2b[fb.upper()]:
            return n2b[fb.upper()]
        return fallback_str
    return d


def get_item_id_by_name(item_name: str) -> str:
    """Mapeia o nome interno do item (usado em visible_equipments) para o ID numérico do item."""
    global _ITEM_NAME_TO_ID
    if _ITEM_NAME_TO_ID is None:
        _ITEM_NAME_TO_ID = {}
        c_items = read_client_xml("items/client_items.xml")
        for c_item in c_items:
            i_id = c_item.findtext("id")
            i_name = c_item.findtext("name")
            if i_id and i_name:
                _ITEM_NAME_TO_ID[i_name.strip().lower()] = i_id.strip()
    return _ITEM_NAME_TO_ID.get(item_name.strip().lower(), "")


def read_client_xml(rel_path: str) -> ET.Element:
    """Lê e decodifica um XML binário ou de texto da pasta client/data, retornando a raiz ElementTree."""
    full_path = os.path.join(CLIENT_DATA_DIR, rel_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Arquivo do cliente não encontrado: {full_path}")

    raw_data = open(full_path, "rb").read()
    if aion_bxml.e_bxml(full_path):
        xml_str = aion_bxml.decodifica(raw_data)
    else:
        xml_str = raw_data.decode("utf-8", errors="ignore")

    return ET.fromstring(xml_str)


def read_server_xml(rel_path: str) -> tuple[ET.ElementTree, ET.Element]:
    """Lê um XML do servidor, retornando (Tree, Root). Cria uma árvore básica se não existir."""
    full_path = os.path.join(SERVER_DATA_DIR, rel_path)
    if not os.path.exists(full_path):
        tag_name = os.path.splitext(os.path.basename(rel_path))[0]
        root = ET.Element(tag_name)
        tree = ET.ElementTree(root)
        return tree, root

    tree = ET.parse(full_path)
    return tree, tree.getroot()


def write_server_xml(rel_path: str, root_elem: ET.Element) -> int:
    """Grava o XML formatado de alta performance no GameServer e PRODUTO FINAL com backup prévio obrigatório."""
    # BACKUP OBRIGATÓRIO: salva os arquivos originais com data/hora antes de qualquer modificação
    backup_manager.backup_file_before_modification(rel_path)

    ET.indent(root_elem, space="\t")
    tree = ET.ElementTree(root_elem)
    
    for base_dir in [SERVER_DATA_DIR, PRODUTO_FINAL_DATA_DIR]:
        full_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        tree.write(full_path, encoding="utf-8", xml_declaration=True)
        
    return len(root_elem)


def log_step(name: str, total_orig: int, added: int, updated: int, total_final: int):
    """Exibe no console o resumo estatístico padronizado da execução."""
    print(f"[{name:20s}] Original: {total_orig:6d} | Adicionados 5.0: +{added:5d} | Atualizados: ~{updated:5d} | Total Final: {total_final:6d}")
