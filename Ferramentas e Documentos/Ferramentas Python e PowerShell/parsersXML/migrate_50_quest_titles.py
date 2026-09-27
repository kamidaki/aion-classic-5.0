#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove recompensas de quests que apontam para títulos fora do Classic 5.0.

O catálogo ``client_titles.xml`` é a autoridade de existência. Os templates
1..300 continuam no servidor somente para compatibilidade com personagens já
persistidos; esta migração impede novas concessões por quests legadas.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import shutil
import sys
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CLIENT_ROOT = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos"
CLIENT_TITLES = CLIENT_ROOT / "data" / "PC" / "client_titles.xml"
CLIENT_QUESTS = CLIENT_ROOT / "data" / "Quest" / "quest.xml"
SOURCE = PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data" / "quest_data" / "quest_data.xml"
PRODUCT = PROJECT_ROOT / "Emulador - Produto Final" / "GameServer" / "data" / "static_data" / "quest_data" / "quest_data.xml"
REPORT = PROJECT_ROOT / "5 - Documentação e Referências" / "4 - Auditoria de Itens Classic 5.0" / "rastreabilidade_recompensas_titulos_quests_50.csv"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REWARD_WITH_TITLE = re.compile(r'(<(?:rewards|extended_rewards)\b[^>]*?)\s+title="(\d+)"')


def official_titles() -> tuple[set[int], dict[str, int]]:
    ids: set[int] = set()
    names: dict[str, int] = {}
    for node in ET.parse(CLIENT_TITLES).getroot().findall("client_title"):
        title_id = int(node.findtext("id", "0"))
        name = node.findtext("name", "").strip().lower()
        ids.add(title_id)
        if name:
            names[name] = title_id
    return ids, names


def official_quests() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for quest in ET.parse(CLIENT_QUESTS).getroot().findall("quest"):
        quest_id = quest.findtext("id", "").strip()
        fields = [
            f"{child.tag}={child.text.strip()}"
            for child in quest
            if child.tag.startswith("reward_title") and child.text and child.text.strip()
        ]
        result[quest_id] = fields
    return result


def inventory(valid_ids: set[int], client_quests: dict[str, list[str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    root = ET.parse(SOURCE).getroot()
    for quest in root.findall("quest"):
        quest_id = quest.get("id", "")
        official_fields = client_quests.get(quest_id)
        for group in ("rewards", "extended_rewards"):
            for reward in quest.findall(group):
                raw_title = reward.get("title")
                if raw_title is None:
                    continue
                title_id = int(raw_title)
                if title_id in valid_ids:
                    status = "PRESERVADO_TITULO_ATUAL"
                elif official_fields:
                    status = "REMOVIDO_CAMPO_RESIDUAL_SEM_TITULO_ATUAL"
                elif quest_id in client_quests:
                    status = "REMOVIDO_DIVERGENTE_DO_CLIENTE_ATUAL"
                else:
                    status = "REMOVIDO_QUEST_LEGADA_AUSENTE_DO_CLIENTE"
                rows.append({
                    "quest_id": quest_id,
                    "quest_nome_servidor": quest.get("name", ""),
                    "grupo_recompensa": group,
                    "titulo_legado_id": raw_title,
                    "quest_no_cliente_atual": "sim" if quest_id in client_quests else "não",
                    "campo_oficial_residual": "|".join(official_fields or []),
                    "status": status,
                    "fonte_oficial": "data/Quest/quest.xml;data/PC/client_titles.xml",
                    "fonte_servidor": "data/static_data/quest_data/quest_data.xml",
                })
    return rows


def remove_invalid_titles(text: str, valid_ids: set[int]) -> tuple[str, int]:
    removed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal removed
        if int(match.group(2)) in valid_ids:
            return match.group(0)
        removed += 1
        return match.group(1)

    return REWARD_WITH_TITLE.sub(replace, text), removed


def write_report(rows: list[dict[str, str]]) -> None:
    if not rows and REPORT.exists():
        return
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "quest_id", "quest_nome_servidor", "grupo_recompensa", "titulo_legado_id",
            "quest_no_cliente_atual", "campo_oficial_residual", "status",
            "fonte_oficial", "fonte_servidor",
        ], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="aplica a remoção na fonte e no produto final")
    args = parser.parse_args()

    valid_ids, _ = official_titles()
    client_quests = official_quests()
    rows = inventory(valid_ids, client_quests)
    invalid_rows = [row for row in rows if row["status"].startswith("REMOVIDO_")]
    write_report(rows)

    source_text = SOURCE.read_text(encoding="utf-8")
    updated_text, removed = remove_invalid_titles(source_text, valid_ids)
    if removed != len(invalid_rows):
        raise RuntimeError(f"inventário encontrou {len(invalid_rows)} inválidos, mas a edição encontrou {removed}")

    if args.apply:
        SOURCE.write_text(updated_text, encoding="utf-8", newline="")
        shutil.copyfile(SOURCE, PRODUCT)
        ET.parse(SOURCE)
        ET.parse(PRODUCT)

    current = sum(1 for row in rows if row["status"] == "PRESERVADO_TITULO_ATUAL")
    residual = sum(1 for row in rows if row["status"] == "REMOVIDO_CAMPO_RESIDUAL_SEM_TITULO_ATUAL")
    absent = sum(1 for row in rows if row["status"] == "REMOVIDO_QUEST_LEGADA_AUSENTE_DO_CLIENTE")
    print(f"Catálogo oficial atual: {len(valid_ids)} títulos")
    print(f"Recompensas inventariadas: {len(rows)}")
    print(f"Títulos atuais preservados: {current}")
    print(f"Campos oficiais residuais removíveis: {residual}")
    print(f"Recompensas de quests ausentes removíveis: {absent}")
    print(f"Aplicado: {'sim' if args.apply else 'não'}")
    print(f"Relatório: {REPORT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
