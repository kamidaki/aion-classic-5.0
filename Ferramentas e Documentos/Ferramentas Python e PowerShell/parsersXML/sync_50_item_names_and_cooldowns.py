#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_50_item_names_and_cooldowns.py

Sincroniza 100% das descrições (nomes oficiais PT-BR e IDs de texto) e cooldowns
(usedelay e usedelayid no bloco <uselimits>) entre os dados oficiais do Classic 5.0
(client_items.xml e Strings) e o item_templates.xml do servidor.

Validação:
  - Mantém ordenação estrita da sequência XSD do ItemTemplate:
    modifiers -> actions -> godstone -> stigma -> weapon_stats ->
    tradein_list -> acquisition -> disposition -> improve -> uselimits ->
    inventory -> idian
  - Valida contra item_templates.xsd com lxml.
  - Backup automático em backup_manager no modo --aplicar.

Uso:
  python sync_50_item_names_and_cooldowns.py --verificar
  python sync_50_item_names_and_cooldowns.py --aplicar
"""

from __future__ import annotations

import argparse
import glob
import html
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PARSERS_DIR))
import backup_manager  # noqa: E402

PROJECT_ROOT = Path(backup_manager.PROJECT_ROOT)
CLIENT_DIR = PROJECT_ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Client 5.0 - Dados Extraidos"
CLIENT_ITEMS_XML = CLIENT_DIR / "data" / "items" / "client_items.xml"
CLIENT_STRINGS_DIR = CLIENT_DIR / "data" / "Strings"
PT_STRINGS_DIR = PROJECT_ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Tradução - Português Brasil" / "strings"

REL_TEMPLATE = "items/item_templates.xml"
REL_XSD = "items/item_templates.xsd"
SOURCE_XML = Path(backup_manager.SERVER_DATA_DIR) / REL_TEMPLATE
PRODUCT_XML = Path(backup_manager.PRODUTO_FINAL_DATA_DIR) / REL_TEMPLATE
XSD_PATH = Path(backup_manager.SERVER_DATA_DIR) / REL_XSD

BLOCK_RE = re.compile(r'\t<item_template\b([^>]*?)(/>|>(.*?)</item_template>)', re.S)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
STRING_PAT = re.compile(r'<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>([^<]*)</body>)?', re.S)


def esc(v: str) -> str:
    """Escapa caracteres especiais XML para atributos."""
    return str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_strings() -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    """
    Carrega:
      1. n2id: Nome de string (ex: 'STR_SWORD_CIRCULOUS') -> String ID (ex: '700558')
      2. key2pt: Nome de string (ex: 'STR_SWORD_CIRCULOUS') -> Tradução PT-BR
      3. id2pt: String ID -> Tradução PT-BR
      4. key2fallback: Nome de string -> Texto Fallback
      5. id2fallback: String ID -> Texto Fallback
    """
    n2id: dict[str, str] = {}
    key2pt: dict[str, str] = {}
    id2pt: dict[str, str] = {}
    key2fallback: dict[str, str] = {}
    id2fallback: dict[str, str] = {}

    # 1. Carrega Strings do Cliente Oficial (IDs e Fallback)
    for p in sorted(glob.glob(str(CLIENT_STRINGS_DIR / "*.xml"))):
        raw = open(p, "rb").read()
        text = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
        for sid, sname, body in STRING_PAT.findall(text):
            k = sname.strip().upper()
            n2id[k] = sid
            if body and body.strip():
                clean_body = html.unescape(body.strip())
                key2fallback[k] = clean_body
                id2fallback[sid] = clean_body

    # 2. Carrega Strings PT-BR oficiais (indexadas por chave k e por sid)
    if PT_STRINGS_DIR.is_dir():
        for p in sorted(glob.glob(str(PT_STRINGS_DIR / "*.xml"))):
            raw = open(p, "rb").read()
            text = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
            for sid, sname, body in STRING_PAT.findall(text):
                k = sname.strip().upper()
                if k not in n2id:
                    n2id[k] = sid
                if body and body.strip():
                    clean_body = html.unescape(body.strip())
                    key2pt[k] = clean_body
                    id2pt[sid] = clean_body

    return n2id, key2pt, id2pt, key2fallback, id2fallback


def load_client_items(n2id: dict[str, str]) -> dict[str, dict]:
    """Carrega dados oficiais de client_items.xml."""
    items: dict[str, dict] = {}
    for event, elem in ET.iterparse(str(CLIENT_ITEMS_XML), events=("end",)):
        if elem.tag == "client_item":
            iid = elem.findtext("id")
            if iid:
                cname = elem.findtext("name") or ""
                desc_key = (elem.findtext("desc") or "").strip().upper()
                use_delay = int(elem.findtext("use_delay") or "0")
                use_delay_type_id = int(elem.findtext("use_delay_type_id") or "0")
                desc_id = n2id.get(desc_key, "0")

                items[iid] = {
                    "cname": cname,
                    "desc_key": desc_key,
                    "desc_id": desc_id,
                    "use_delay": use_delay,
                    "use_delay_type_id": use_delay_type_id,
                }
            elem.clear()
    return items


def set_attribute(head: str, attr_name: str, attr_value: str) -> str:
    """Atualiza ou insere atributo no cabeçalho <item_template ...>."""
    pattern = rf'\s+{attr_name}="[^"]*"'
    new_fragment = f' {attr_name}="{esc(attr_value)}"'
    if re.search(pattern, head):
        return re.sub(pattern, new_fragment, head, count=1)
    return head.rstrip() + new_fragment


def update_uselimits_element(limits_tag: str, delay_ms: int, delay_id: int) -> str:
    """Atualiza atributos usedelay e usedelayid mantendo outros atributos existentes."""
    tag = limits_tag
    # usedelay
    if delay_ms > 0:
        if 'usedelay="' in tag:
            tag = re.sub(r'\busedelay="[^"]*"', f'usedelay="{delay_ms}"', tag)
        else:
            tag = re.sub(r'<uselimits\b', f'<uselimits usedelay="{delay_ms}"', tag)
    else:
        # Se delay_ms == 0, remove se houver
        tag = re.sub(r'\s+usedelay="[^"]*"', '', tag)

    # usedelayid
    if delay_id > 0:
        if 'usedelayid="' in tag:
            tag = re.sub(r'\busedelayid="[^"]*"', f'usedelayid="{delay_id}"', tag)
        else:
            tag = re.sub(r'<uselimits\b', f'<uselimits usedelayid="{delay_id}"', tag)
    else:
        tag = re.sub(r'\s+usedelayid="[^"]*"', '', tag)

    return tag


def build_uselimits_xml(delay_ms: int, delay_id: int) -> str:
    """Cria elemento <uselimits .../> formatado."""
    attrs = []
    if delay_ms > 0:
        attrs.append(f'usedelay="{delay_ms}"')
    if delay_id > 0:
        attrs.append(f'usedelayid="{delay_id}"')
    return f'<uselimits {" ".join(attrs)}/>'


def insert_uselimits_in_body(body: str, delay_ms: int, delay_id: int) -> str:
    """
    Insere <uselimits .../> no body respeitando a sequência do ItemTemplate XSD:
    modifiers -> actions -> godstone -> stigma -> weapon_stats ->
    tradein_list -> acquisition -> disposition -> improve -> [uselimits] ->
    inventory -> idian
    """
    limits_line = f"\t\t{build_uselimits_xml(delay_ms, delay_id)}\r\n"
    lines = body.splitlines(keepends=True)

    # Verifica se há elementos que devem vir DEPOIS de uselimits: <inventory> ou <idian>
    insert_idx = -1
    for i, line in enumerate(lines):
        if re.search(r'^\s*<(inventory|idian)\b', line):
            insert_idx = i
            break

    if insert_idx != -1:
        lines.insert(insert_idx, limits_line)
        return "".join(lines)
    else:
        content = body.rstrip()
        return f"{content}\r\n{limits_line}"


def process_item_template(match: re.Match, client_items: dict[str, dict], key2pt: dict[str, str], id2pt: dict[str, str], key2fallback: dict[str, str], id2fallback: dict[str, str], stats: dict) -> str:
    raw_head = match.group(1)
    is_self_closing = match.group(2) == '/>'
    inner_body = match.group(3) or ''

    attrs = dict(ATTR_RE.findall(raw_head))
    iid = attrs.get('id')
    if not iid:
        return match.group(0)

    citem = client_items.get(iid)
    if not citem:
        return match.group(0)

    modified = False
    head = raw_head
    body = inner_body

    # 1. SINCRONIZAÇÃO DE DESCRIÇÃO E NOME
    # Atributo 'desc': deve bater com o ID oficial da tabela de strings
    official_desc_id = citem["desc_id"]
    current_desc_id = attrs.get("desc", "0")
    if official_desc_id != "0" and current_desc_id != official_desc_id:
        head = set_attribute(head, "desc", official_desc_id)
        current_desc_id = official_desc_id
        modified = True
        stats["desc_updated"] += 1

    # Atributo 'name': busca primeiro pela chave STR_... no PT-BR, depois por ID, e por fim fallback
    desc_key = citem["desc_key"]
    best_name = key2pt.get(desc_key) or id2pt.get(current_desc_id) or key2fallback.get(desc_key) or id2fallback.get(current_desc_id)
    if best_name:
        current_name = attrs.get("name", "")
        if current_name != best_name:
            head = set_attribute(head, "name", best_name)
            modified = True
            stats["name_updated"] += 1

    # 2. SINCRONIZAÇÃO DE COOLDOWN (<uselimits>)
    c_delay = citem["use_delay"]
    c_delay_id = citem["use_delay_type_id"]
    c_has_cd = (c_delay > 0 or c_delay_id > 0)

    limits_match = re.search(r'<uselimits\b([^>]*)/?>', body) if not is_self_closing else None

    if limits_match:
        # <uselimits> já existe no body
        l_attrs = dict(ATTR_RE.findall(limits_match.group(1)))
        s_delay = int(l_attrs.get("usedelay", "0")) if l_attrs.get("usedelay", "").isdigit() else 0
        s_delay_id = int(l_attrs.get("usedelayid", "0")) if l_attrs.get("usedelayid", "").isdigit() else 0

        # Se o cliente oficial tem CD e difere do servidor
        if c_has_cd and (s_delay != c_delay or s_delay_id != c_delay_id):
            updated_tag = update_uselimits_element(limits_match.group(0), c_delay, c_delay_id)
            body = body[:limits_match.start()] + updated_tag + body[limits_match.end():]
            modified = True
            stats["cd_updated"] += 1
    elif c_has_cd:
        # <uselimits> NÃO existe, mas o cliente oficial tem CD ativo
        if is_self_closing:
            # Expande tag auto-fechada
            head_clean = head.rstrip()
            limits_str = build_uselimits_xml(c_delay, c_delay_id)
            new_block = f"\t<item_template{head_clean}>\r\n\t\t{limits_str}\r\n\t</item_template>"
            stats["cd_inserted"] += 1
            return new_block
        else:
            # Insere no body na ordem certa da sequência XSD
            body = insert_uselimits_in_body(body, c_delay, c_delay_id)
            modified = True
            stats["cd_inserted"] += 1

    if not modified:
        return match.group(0)

    # Reconstrói bloco
    if is_self_closing:
        return f"\t<item_template{head}/>"
    else:
        inner_content = body.rstrip()
        if not inner_content.startswith("\r\n") and not inner_content.startswith("\n"):
            inner_content = "\r\n" + inner_content
        return f"\t<item_template{head}>{inner_content}\r\n\t</item_template>"


def run_sync(verificar: bool = True) -> None:
    print(f"=== Sincronizador de Nomes e Cooldowns Classic 5.0 ({'VERIFICAÇÃO' if verificar else 'APLICAÇÃO'}) ===")
    print(f"Alvo Fonte: {SOURCE_XML}")
    print(f"Alvo Produto Final: {PRODUCT_XML}")

    print("\n1. Carregando catálogo de Strings...")
    n2id, key2pt, id2pt, key2fallback, id2fallback = load_strings()
    print(f"   - Mapeamentos de ID: {len(n2id)}")
    print(f"   - Chaves PT-BR: {len(key2pt)}")
    print(f"   - IDs PT-BR: {len(id2pt)}")
    print(f"   - Textos Fallback: {len(key2fallback)}")

    print("2. Carregando dados oficiais do cliente (client_items.xml)...")
    client_items = load_client_items(n2id)
    print(f"   - Itens de cliente carregados: {len(client_items)}")

    print("3. Processando item_templates.xml do servidor...")
    raw_bytes = SOURCE_XML.read_bytes()
    raw_text = raw_bytes.decode("utf-8")

    stats = {
        "total_templates": 0,
        "name_updated": 0,
        "desc_updated": 0,
        "cd_updated": 0,
        "cd_inserted": 0,
    }

    def repl(m: re.Match) -> str:
        stats["total_templates"] += 1
        return process_item_template(m, client_items, key2pt, id2pt, key2fallback, id2fallback, stats)

    new_text = BLOCK_RE.sub(repl, raw_text)
    new_bytes = new_text.encode("utf-8")

    print("\n=== RELATÓRIO DE ALTERAÇÕES ===")
    print(f"Templates inspecionados: {stats['total_templates']}")
    print(f"Nomes atualizados com PT-BR oficial: {stats['name_updated']}")
    print(f"IDs de descrição ('desc') corrigidos: {stats['desc_updated']}")
    print(f"CDs corrigidos (<uselimits> já existente): {stats['cd_updated']}")
    print(f"CDs inseridos (<uselimits> novos): {stats['cd_inserted']}")
    total_cd_fixes = stats['cd_updated'] + stats['cd_inserted']
    print(f"Total de correções de CD aplicadas: {total_cd_fixes}")

    print("\n4. Validando conformidade com o XSD (item_templates.xsd)...")
    schema_doc = etree.parse(str(XSD_PATH))
    schema = etree.XMLSchema(schema_doc)
    
    xml_doc = etree.fromstring(new_bytes)
    schema.assertValid(xml_doc)
    print("   [OK] O XML gerado é 100% VÁLIDO contra o schema item_templates.xsd!")

    if verificar:
        print("\nModo --verificar concluído com sucesso. NENHUM arquivo foi alterado.")
        print("Para aplicar as alterações, execute com --aplicar.")
        return

    print("\n5. Criando backups seguros via backup_manager...")
    backup_manager.backup_file_before_modification(REL_TEMPLATE)

    print("6. Escrevendo arquivos atualizados no Fonte e Produto Final...")
    SOURCE_XML.write_bytes(new_bytes)
    PRODUCT_XML.write_bytes(new_bytes)
    print("   [OK] Arquivos gravados com sucesso!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza nomes, descrições e cooldowns dos itens 5.0.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verificar", action="store_true", help="Executa verificação em memória e valida XSD sem gravar.")
    group.add_argument("--aplicar", action="store_true", help="Gera backup e aplica as alterações nos arquivos.")
    args = parser.parse_args()

    run_sync(verificar=args.verificar)


if __name__ == "__main__":
    main()
