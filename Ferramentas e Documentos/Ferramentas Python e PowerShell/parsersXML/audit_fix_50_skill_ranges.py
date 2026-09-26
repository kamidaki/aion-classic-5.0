#!/usr/bin/env python3
"""Audita e sincroniza alcances de Skills com o cliente Classic 5.0.

Os campos oficiais usados são os mesmos em base, special e special2. O modo
``--apply`` altera somente atributos de alcance e mantém a formatação canônica
do XML; depois replica o resultado no produto final.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLIENT_ROOTS = (
    ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos",
    ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Client 5.0 - Dados Extraidos",
)
CLIENT_ROOT = next((path for path in CLIENT_ROOTS if path.exists()), CLIENT_ROOTS[0])
CLIENT_DIR = CLIENT_ROOT / "data" / "skills"
SOURCE_XML = ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data" / "skills" / "skill_templates.xml"
PRODUCT_XML = ROOT / "Emulador - Produto Final" / "GameServer" / "data" / "static_data" / "skills" / "skill_templates.xml"
OUT_JSON = HERE / "auditoria_alcances_skills_50.json"
OUT_MD = HERE / "auditoria_alcances_skills_50.md"

RANGE_FIELDS = (
    "first_target_valid_distance", "add_wpn_range", "revision_distance",
    "target_range", "target_range_area_type", "target_range_opt1",
    "target_range_opt2", "target_range_opt3", "target_range_opt4",
)
SHAPE_ATTRIBUTES = ("effective_range", "effective_dist", "effective_angle", "effective_altitude", "direction")
FIRST_TARGETS = {"TARGETORME", "ME", "MYPET", "MYMASTER", "TARGET", "PASSIVE", "TARGET_MYPARTY_NONVISIBLE", "POINT"}
TARGET_TYPES = {"ONLYONE", "PARTY", "AREA", "PARTY_WITHPET", "POINT"}


def records(path: Path) -> dict[int, dict[str, str]]:
    result = {}
    for entry in ET.parse(path).getroot():
        raw_id = entry.findtext("id")
        if raw_id and raw_id.isdigit():
            result[int(raw_id)] = {child.tag: (child.text or "").strip() for child in entry}
    return result


def integer(value: str | None) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def set_attribute(attributes: str, name: str, value: int | str | None) -> str:
    pattern = rf'\s{name}="[^"]*"'
    if value in (None, 0, "", "NONE", False):
        return re.sub(pattern, "", attributes)
    replacement = f' {name}="{value}"'
    if re.search(pattern, attributes):
        return re.sub(pattern, replacement, attributes)
    return attributes + replacement


def expected_shape(client: dict[str, str]) -> tuple[set[str], dict[str, int | str]] | None:
    target_range = client.get("target_range", "").upper()
    area_type = client.get("target_range_area_type", "").upper()
    opt1 = integer(client.get("target_range_opt1"))
    opt2 = integer(client.get("target_range_opt2"))
    opt3 = integer(client.get("target_range_opt3"))
    back = client.get("target_range_opt4", "").upper() == "BACK"
    if target_range in {"PARTY", "PARTY_WITHPET"}:
        return {"PARTY", "PARTY_WITHPET"}, {"effective_range": opt1}
    if target_range != "AREA":
        return None
    if area_type == "FIREBALL":
        return {"AREA"}, {"effective_range": opt1, "effective_altitude": opt3}
    if area_type == "FIRESTORM":
        return {"AREA"}, {
            "effective_dist": opt1, "effective_angle": opt2,
            "effective_altitude": opt3, "direction": "BACK" if back else "NONE",
        }
    if area_type == "LIGHTNINGBOLT":
        return {"AREA"}, {
            "effective_dist": opt2, "effective_range": opt1 * 2,
            "effective_altitude": opt3, "direction": "BACK" if back else "NONE",
        }
    return None


def variant_conflicts(base: dict[int, dict[str, str]], variants: list[dict[int, dict[str, str]]]) -> list[dict[str, object]]:
    conflicts = []
    for variant_index, variant in enumerate(variants, 1):
        for skill_id, row in variant.items():
            if skill_id not in base:
                continue
            fields = {
                field: {"base": base[skill_id].get(field), "variante": row.get(field)}
                for field in RANGE_FIELDS
                if (base[skill_id].get(field) or "") != (row.get(field) or "")
            }
            if fields:
                conflicts.append({"skill_id": skill_id, "variante": variant_index, "campos": fields})
    return conflicts


def synchronize(raw: str, client: dict[int, dict[str, str]]) -> tuple[str, dict[str, object]]:
    changes = collections.Counter()
    changed_skills = set()
    missing_properties = []
    incompatible_shapes = []

    def edit_template(match: re.Match[str]) -> str:
        skill_id = int(match.group(2))
        official = client.get(skill_id)
        if official is None:
            return match.group(0)
        body = match.group(3)
        property_match = re.search(r"(<properties\b)([^>]*?)(\s*/>)", body)
        expected_direct = {
            "first_target_range": integer(official.get("first_target_valid_distance")),
            "awr": "true" if official.get("add_wpn_range") == "1" else None,
            "revision_distance": integer(official.get("revision_distance")),
            "target_distance": integer(official.get("target_range_opt1")),
        }
        if property_match is None:
            if any(value not in (None, 0) for value in expected_direct.values()):
                missing_properties.append(skill_id)
            return match.group(0)

        attributes = property_match.group(2)
        updated = attributes
        official_first_target = official.get("first_target", "").upper().replace("_OR_", "OR")
        if official_first_target in FIRST_TARGETS:
            candidate = set_attribute(updated, "first_target", official_first_target)
            if candidate != updated:
                changes["first_target"] += 1
                updated = candidate
        official_target_type = official.get("target_range", "").upper()
        if official_target_type in TARGET_TYPES:
            candidate = set_attribute(updated, "target_type", official_target_type)
            if candidate != updated:
                changes["target_type"] += 1
                updated = candidate
        for name, value in expected_direct.items():
            candidate = set_attribute(updated, name, value)
            if candidate != updated:
                changes[name] += 1
                updated = candidate

        shape = expected_shape(official)
        if shape is not None:
            accepted_types, expected = shape
            target_type_match = re.search(r'\starget_type="([A-Z_]+)"', updated)
            actual_target_type = target_type_match.group(1) if target_type_match else None
            if actual_target_type not in accepted_types:
                incompatible_shapes.append({
                    "skill_id": skill_id,
                    "target_type_servidor": actual_target_type,
                    "target_range_cliente": official.get("target_range"),
                })
            else:
                for name in SHAPE_ATTRIBUTES:
                    candidate = set_attribute(updated, name, expected.get(name))
                    if candidate != updated:
                        changes[name] += 1
                        updated = candidate

        if updated == attributes:
            return match.group(0)
        changed_skills.add(skill_id)
        body = body[:property_match.start(2)] + updated + body[property_match.end(2):]
        return match.group(1) + body + match.group(4)

    updated_raw = re.sub(
        r'(\t<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)',
        edit_template,
        raw,
        flags=re.DOTALL,
    )
    return updated_raw, {
        "skills_alteradas": len(changed_skills),
        "alteracoes_por_atributo": dict(sorted(changes.items())),
        "skills_sem_properties": missing_properties,
        "formas_com_target_type_incompativel": incompatible_shapes,
    }


def write_report(result: dict[str, object]) -> None:
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    changes = result["sincronizacao"]["alteracoes_por_atributo"]
    lines = [
        "# Auditoria de alcance das Skills — Classic 5.0",
        "",
        f"Foram comparados **{result['skills_cliente']} IDs oficiais** com **{result['skills_servidor']} templates**.",
        f"As variantes `special`/`special2` possuem **{len(result['conflitos_variantes'])} divergências de alcance** contra a base.",
        f"A sincronização corrigiu **{result['sincronizacao']['skills_alteradas']} Skills**.",
        "",
        "| Atributo do servidor | Correções | Fonte oficial |",
        "|---|---:|---|",
    ]
    source = {
        "first_target_range": "first_target_valid_distance",
        "first_target": "first_target",
        "target_type": "target_range",
        "awr": "add_wpn_range",
        "revision_distance": "revision_distance",
        "target_distance": "target_range_opt1",
        "effective_range": "target_range_area_type + opt1",
        "effective_dist": "target_range_area_type + opt1/opt2",
        "effective_angle": "target_range_area_type + opt2",
        "effective_altitude": "target_range_area_type + opt3",
        "direction": "target_range_area_type + opt4",
    }
    for name, count in changes.items():
        lines.append(f"| `{name}` | {count} | `{source[name]}` |")
    lines += [
        "",
        "A flag `add_wpn_range` significa soma: alcance-base oficial + alcance atual da arma. O contorno legado que substituía alcances maiores pelo alcance da arma reduzia, por exemplo, 15 m para aproximadamente 2 m.",
        "",
        f"Restaram **{len(result['sincronizacao']['formas_com_target_type_incompativel'])} Skills** cuja forma de área não concorda com o `target_type`; elas ficam enumeradas no JSON sem conversão inferida.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="grava fonte e produto final")
    args = parser.parse_args()

    base = records(CLIENT_DIR / "client_skills.xml")
    variants = [records(CLIENT_DIR / name / "client_skills.xml") for name in ("special", "special2")]
    conflicts = variant_conflicts(base, variants)
    raw = SOURCE_XML.read_text(encoding="utf-8")
    updated, synchronization = synchronize(raw, base)
    server_count = len(ET.parse(SOURCE_XML).getroot())
    result = {
        "skills_cliente": len(base),
        "skills_servidor": server_count,
        "conflitos_variantes": conflicts,
        "sincronizacao": synchronization,
        "aplicado": args.apply,
    }
    write_report(result)
    if args.apply and updated != raw:
        SOURCE_XML.write_text(updated, encoding="utf-8", newline="")
        PRODUCT_XML.write_text(updated, encoding="utf-8", newline="")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
