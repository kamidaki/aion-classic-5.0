#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_50_skill_cooldowns.py

Sincroniza 100% dos cooldowns (cooldown e delayId) entre os dados oficiais
do cliente Classic 5.0 (client_skills.xml) e o skill_templates.xml do servidor.

Validação:
  - Corrige o erro do fator 10 (cooldowns preenchidos em segundos em vez de décimos de segundo).
  - Sincroniza delayId de habilidades ativas.
  - Valida contra skills.xsd com lxml.
  - Cria backup prévio via backup_manager no modo --aplicar.

Uso:
  python sync_50_skill_cooldowns.py --verificar
  python sync_50_skill_cooldowns.py --aplicar
"""

from __future__ import annotations

import argparse
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
CLIENT_SKILLS_XML = PROJECT_ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Client 5.0 - Dados Extraidos" / "data" / "skills" / "client_skills.xml"

REL_TEMPLATE = "skills/skill_templates.xml"
REL_XSD = "skills/skills.xsd"
SOURCE_XML = Path(backup_manager.SERVER_DATA_DIR) / REL_TEMPLATE
PRODUCT_XML = Path(backup_manager.PRODUTO_FINAL_DATA_DIR) / REL_TEMPLATE
XSD_PATH = Path(backup_manager.SERVER_DATA_DIR) / REL_XSD

SKILL_HEAD_RE = re.compile(r'<skill_template\b([^>]*?)>', re.S)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def load_client_skills() -> dict[str, dict]:
    """Carrega dados oficiais de client_skills.xml."""
    skills: dict[str, dict] = {}
    for event, elem in ET.iterparse(str(CLIENT_SKILLS_XML), events=("end",)):
        if elem.tag == "skill_base_client":
            sid = elem.findtext("id")
            if sid:
                act = (elem.findtext("activation_attribute") or "").strip()
                dt = int(elem.findtext("delay_time") or "0")
                did = int(elem.findtext("delay_id") or "0")
                name = elem.findtext("name") or ""
                skills[sid] = {
                    "name": name,
                    "activation": act,
                    "delay_time": dt,
                    "delay_id": did,
                }
            elem.clear()
    return skills


def set_attribute(head: str, attr_name: str, attr_value: str) -> str:
    """Atualiza ou insere atributo no cabeçalho <skill_template ...>."""
    pattern = rf'\s+{attr_name}="[^"]*"'
    new_fragment = f' {attr_name}="{attr_value}"'
    if re.search(pattern, head):
        return re.sub(pattern, new_fragment, head, count=1)
    return head.rstrip() + new_fragment


def process_skill_template(match: re.Match, client_skills: dict[str, dict], stats: dict) -> str:
    raw_head = match.group(1)
    attrs = dict(ATTR_RE.findall(raw_head))
    sid = attrs.get("skill_id")
    if not sid or sid not in client_skills:
        return match.group(0)

    c = client_skills[sid]
    modified = False
    head = raw_head

    # 1. Correção de Cooldown (décimos de segundo: 100ms)
    c_delay_ms = c["delay_time"]
    exp_cd = round(c_delay_ms / 100)
    current_cd = int(attrs.get("cooldown", "0")) if attrs.get("cooldown", "").isdigit() else 0

    if c_delay_ms > 0 and current_cd != exp_cd:
        head = set_attribute(head, "cooldown", str(exp_cd))
        modified = True
        stats["cooldown_updated"] += 1
        stats["diff_details"].append((sid, attrs.get("name", ""), c["name"], current_cd, exp_cd, c_delay_ms))

    # 2. Correção de DelayId (Grupo de Cooldown para habilidades ativas)
    c_did = c["delay_id"]
    current_did = int(attrs.get("delayId", "0")) if attrs.get("delayId", "").isdigit() else 0
    s_act = attrs.get("activation", "").upper()

    if (c["activation"].upper() in ("ACTIVE", "PROVOKED", "MAINTAIN") or s_act in ("ACTIVE", "PROVOKED", "MAINTAIN")) and c_did > 0:
        if current_did != c_did:
            head = set_attribute(head, "delayId", str(c_did))
            modified = True
            stats["delay_id_updated"] += 1

    if not modified:
        return match.group(0)

    return f"<skill_template{head}>"


def run_sync(verificar: bool = True) -> None:
    print(f"=== Sincronizador de Cooldowns de Skills Classic 5.0 ({'VERIFICAÇÃO' if verificar else 'APLICAÇÃO'}) ===")
    print(f"Alvo Fonte: {SOURCE_XML}")
    print(f"Alvo Produto Final: {PRODUCT_XML}")

    print("\n1. Carregando habilidades do cliente oficial (client_skills.xml)...")
    client_skills = load_client_skills()
    print(f"   - Habilidades carregadas do cliente: {len(client_skills)}")

    print("2. Processando skill_templates.xml do servidor...")
    raw_bytes = SOURCE_XML.read_bytes()
    raw_text = raw_bytes.decode("utf-8")

    stats = {
        "total_templates": 0,
        "cooldown_updated": 0,
        "delay_id_updated": 0,
        "diff_details": [],
    }

    def repl(m: re.Match) -> str:
        stats["total_templates"] += 1
        return process_skill_template(m, client_skills, stats)

    new_text = SKILL_HEAD_RE.sub(repl, raw_text)
    new_bytes = new_text.encode("utf-8")

    print("\n=== RELATÓRIO DE ALTERAÇÕES ===")
    print(f"Templates inspecionados: {stats['total_templates']}")
    print(f"Habilidades com Cooldown corrigido (décimos de segundo): {stats['cooldown_updated']}")
    print(f"Habilidades com delayId (grupo de CD) corrigido: {stats['delay_id_updated']}")

    if stats["diff_details"]:
        print("\n--- AMOSTRA DAS CORREÇÕES DE COOLDOWN (Primeiras 15) ---")
        for sid, s_name, c_name, old_cd, new_cd, ms in stats["diff_details"][:15]:
            print(f"  Skill {sid:6} ({s_name:30} | {c_name:30}):")
            print(f"     Antes: cooldown=\"{old_cd}\" ({old_cd/10:5.1f}s) -> Corrigido: cooldown=\"{new_cd}\" ({new_cd/10:5.1f}s) [Oficial: {ms}ms]")

    print("\n3. Validando conformidade com o XSD (skills.xsd)...")
    schema_doc = etree.parse(str(XSD_PATH))
    schema = etree.XMLSchema(schema_doc)

    xml_doc = etree.fromstring(new_bytes)
    schema.assertValid(xml_doc)
    print("   [OK] O XML gerado é 100% VÁLIDO contra o schema skills.xsd!")

    if verificar:
        print("\nModo --verificar concluído com sucesso. NENHUM arquivo foi alterado.")
        print("Para aplicar as alterações, execute com --aplicar.")
        return

    print("\n4. Criando backups seguros via backup_manager...")
    backup_manager.backup_file_before_modification(REL_TEMPLATE)

    print("5. Escrevendo arquivos atualizados no Fonte e Produto Final...")
    SOURCE_XML.write_bytes(new_bytes)
    PRODUCT_XML.write_bytes(new_bytes)
    print("   [OK] Arquivos gravados com sucesso!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza cooldowns das habilidades Classic 5.0.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verificar", action="store_true", help="Executa verificação em memória e valida XSD sem gravar.")
    group.add_argument("--aplicar", action="store_true", help="Gera backup e aplica as alterações nos arquivos.")
    args = parser.parse_args()

    run_sync(verificar=args.verificar)


if __name__ == "__main__":
    main()
