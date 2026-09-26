#!/usr/bin/env python3
"""Inventario rastreavel de Skills do Aion Classic 5.0 EU.

O auditor e estritamente somente-leitura para os dados do cliente e do
emulador. Ele nao escolhe silenciosamente entre os overlays ``special`` e
``special2``: qualquer diferenca entre variantes permanece marcada como
pendencia de fonte ate que uma captura ou outra evidencia oficial determine a
variante usada pelo servidor.

Saidas:

* ``auditoria_skills_50_completa.json``: evidencia detalhada por Skill;
* ``matriz_rastreabilidade_skills_50.csv``: uma linha por ID;
* ``auditoria_skills_50_completa.md``: resumo executivo reproduzivel.
"""

from __future__ import annotations

import collections
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATIC = ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data"
JAVA = ROOT / "Código Fonte - Emulador" / "game-server" / "src" / "com" / "aionemu" / "gameserver"
TESTS = ROOT / "Código Fonte - Emulador" / "game-server" / "test"
CLIENT_ROOT = ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Client 5.0 - Dados Extraidos"
CLIENT_SKILLS = CLIENT_ROOT / "data" / "skills"
CLIENT_ITEMS = CLIENT_ROOT / "data" / "items" / "client_items.xml"
PCAPS = ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Wireshark - Oficial Classic 5.0"
PCAP_TOOLS = ROOT / "Ferramentas e Documentos" / "Ferramentas Python e PowerShell" / "Ferramentas Python"

OUT_JSON = HERE / "auditoria_skills_50_completa.json"
OUT_CSV = HERE / "matriz_rastreabilidade_skills_50.csv"
OUT_MD = HERE / "auditoria_skills_50_completa.md"


ALIASES = {
    "skillatkinstant": {"skillatk"},
    "amrmastery": {"armormastery"},
    "dashatk": {"dash"},
    "movebehindatk": {"movebehind"},
    "blinkatk": {"movebehind"},
    "backdashatk": {"backdash"},
    "returnhome": {"return"},
    "delayedspellatkinstant": {"delaydamage"},
    "deboosthealamount": {"deboostheal"},
    "mpatkdraininstant": {"spellatkdraininstant"},
    "healcastoronattacked": {"healcastoronatk"},
    "boosthealeffect": {"boostheal"},
    "onetimeboosthealeffect": {"onetimeboostheal"},
    "extendaurarange": {"extendedaurarange"},
    "switchhpmpinstant": {"switchhpmp"},
    "boostspellattackeffect": {"boostspellattack"},
    "noreducespellatkinstant": {"noreducespellatk"},
    "resurrectpositional": {"resurrectpos"},
}


def norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def records(path: Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for entry in ET.parse(path).getroot():
        raw_id = entry.findtext("id")
        if raw_id and raw_id.isdigit():
            result[int(raw_id)] = {child.tag: (child.text or "").strip() for child in entry}
    return result


def variant_diff(base: dict[str, str], other: dict[str, str] | None) -> dict[str, list[str | None]]:
    if other is None:
        return {"__record__": ["presente", None]}
    result = {}
    for field in sorted(set(base) | set(other)):
        if base.get(field) != other.get(field):
            result[field] = [base.get(field), other.get(field)]
    return result


def official_effects(row: dict[str, str]) -> dict[int, str]:
    result = {}
    for field, value in row.items():
        match = re.fullmatch(r"effect(\d+)_type", field)
        if match and value:
            result[int(match.group(1))] = value
    return result


def server_effects(template: ET.Element | None) -> dict[int, list[str]]:
    result: dict[int, list[str]] = collections.defaultdict(list)
    if template is not None:
        effects = template.find("effects")
        if effects is not None:
            for effect in effects:
                result[int(effect.get("e", "0"))].append(effect.tag)
    return dict(result)


def load_effect_registry() -> tuple[dict[str, str], set[str]]:
    text = (JAVA / "skillengine" / "effect" / "Effects.java").read_text(encoding="utf-8")
    registry = dict(re.findall(r'@XmlElement\(name\s*=\s*"([^"]+)"\s*,\s*type\s*=\s*(\w+)\.class', text))
    stubs = set()
    for xml_type, class_name in registry.items():
        path = JAVA / "skillengine" / "effect" / f"{class_name}.java"
        if not path.exists() or "TODO Auto-generated method stub" in path.read_text(encoding="utf-8", errors="replace"):
            stubs.add(xml_type)
    return registry, stubs


def load_tree() -> tuple[dict[int, list[dict[str, str]]], set[int]]:
    by_skill: dict[int, list[dict[str, str]]] = collections.defaultdict(list)
    stigma = set()
    for entry in ET.parse(STATIC / "skill_tree" / "skill_tree.xml").getroot():
        skill_id = int(entry.get("skillId"))
        row = dict(entry.attrib)
        by_skill[skill_id].append(row)
        if entry.get("stigma") == "true":
            stigma.add(skill_id)
    return dict(by_skill), stigma


def load_npc_refs() -> dict[int, set[int]]:
    result: dict[int, set[int]] = collections.defaultdict(set)
    for group in ET.parse(STATIC / "npc_skills" / "npc_skills.xml").getroot():
        npc_ids = {int(value) for value in re.findall(r"\d+", group.get("npc_ids", ""))}
        for skill in group:
            raw = skill.get("id")
            if raw and raw.isdigit():
                result[int(raw)].update(npc_ids)
    return result


def load_server_item_refs() -> tuple[dict[int, set[int]], set[int]]:
    refs: dict[int, set[int]] = collections.defaultdict(set)
    stigma = set()
    root = ET.parse(STATIC / "items" / "item_templates.xml").getroot()
    skill_attr = re.compile(r"(?:^|_)(?:skill|skillid|skill_id)(?:\d+)?$", re.I)
    for item in root:
        item_id = int(item.get("id"))
        for node in item.iter():
            for key, value in node.attrib.items():
                if value.isdigit() and skill_attr.search(key):
                    skill_id = int(value)
                    if skill_id > 0:
                        refs[skill_id].add(item_id)
                        if node.tag == "stigma":
                            stigma.add(skill_id)
    return refs, stigma


def load_client_item_refs(name_to_id: dict[str, int]) -> tuple[dict[int, set[str]], list[str]]:
    result: dict[int, set[str]] = collections.defaultdict(set)
    unresolved = []
    if not CLIENT_ITEMS.exists():
        return result, unresolved
    fields = {
        "skill_to_learn", "gain_skill1", "gain_skill2", "proc_enchant_skill",
        "gain_skill_costume1", "gain_skill_costume2", "skin_skill", "activation_skill",
    }
    for item in ET.parse(CLIENT_ITEMS).getroot():
        item_name = (item.findtext("name") or "").strip()
        for field in fields:
            value = (item.findtext(field) or "").strip()
            if not value:
                continue
            # activation_skill tambem contem pequenos codigos numericos que nao
            # sao IDs. Sem um dicionario oficial que prove a semantica, eles
            # devem permanecer pendentes em vez de virar referencias falsas.
            skill_id = None if value.isdigit() else name_to_id.get(value.lower())
            if skill_id:
                result[skill_id].add(f"{field}:{item_name}")
            else:
                unresolved.append(f"{field}:{item_name}:{value}")
    return result, sorted(set(unresolved))


def load_test_refs(all_ids: set[int], effect_classes: set[str]) -> tuple[dict[int, set[str]], dict[str, set[str]]]:
    by_id: dict[int, set[str]] = collections.defaultdict(set)
    by_effect: dict[str, set[str]] = collections.defaultdict(set)
    if not TESTS.exists():
        return by_id, by_effect
    for path in TESTS.rglob("*.java"):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        id_patterns = [
            r"(?:skillId|skill_id|skillid)\s*[,=(]\s*(\d{1,5})",
            r"getSkillTemplate\(\s*(\d{1,5})",
            r"applyEffectDirectly\(\s*(\d{1,5})",
        ]
        referenced = {raw for pattern in id_patterns for raw in re.findall(pattern, text, re.I)}
        for raw in referenced:
            skill_id = int(raw)
            if skill_id in all_ids:
                by_id[skill_id].add(rel)
        for class_name in effect_classes:
            if re.search(rf"\b{re.escape(class_name)}\b", text):
                by_effect[class_name].add(rel)
    return by_id, by_effect


def load_pcap_refs() -> tuple[collections.Counter[int], collections.Counter[int], dict[str, object]]:
    client = collections.Counter()
    server = collections.Counter()
    meta = {"files": 0, "sessions": 0, "files_with_sessions": 0, "login_port_packets": 0}
    if not PCAPS.exists():
        return client, server, meta
    sys.path.insert(0, str(PCAP_TOOLS))
    import aion_pcap  # type: ignore

    for path in PCAPS.rglob("*.pcapng"):
        meta["files"] += 1
        # Somente sessoes cuja S_KEY foi capturada entram automaticamente. A
        # recuperacao heuristica de chave para sessoes iniciadas antes da
        # captura e deliberadamente excluida: ela e muito cara e, sobretudo,
        # nao oferece a mesma prova criptografica reproduzivel do checksum.
        sessions = aion_pcap.abre_todas(str(path), sem_skey=False)
        if sessions:
            meta["files_with_sessions"] += 1
        meta["sessions"] += len(sessions)
        for session in sessions:
            for opcode, payload, valid in session["cliente"]:
                if valid and opcode == 33 and payload is not None and len(payload) >= 2:
                    client[int.from_bytes(payload[0:2], "little")] += 1
            for opcode, payload, valid in session["servidor"]:
                if valid and opcode == 33 and payload is not None and len(payload) >= 6:
                    server[int.from_bytes(payload[4:6], "little")] += 1
        # As capturas fornecidas nao contem login na porta 2106. Manter este
        # censo torna o limite de evidencia verificavel em execucoes futuras.
        for linktype, frame, _ in aion_pcap.blocos(str(path)):
            tcp = aion_pcap.tcp_de(linktype, frame)
            if tcp and tcp[-1] and 2106 in (tcp[1], tcp[3]):
                meta["login_port_packets"] += 1
    return client, server, meta


def structural_differences(official: dict[str, str], template: ET.Element | None) -> list[str]:
    if template is None:
        return ["template_ausente"]
    differences = []
    mappings = {
        "type": ("skilltype", None),
        "sub_type": ("skillsubtype", None),
        "activation_attribute": ("activation", None),
        "target_slot": ("tslot", {"special": "spec", "special2": "spec2"}),
        "delay_id": ("delayId", None),
        "casting_delay": ("duration", None),
        "pvp_damage_ratio": ("pvp_damage", None),
    }
    for client_field, (server_field, aliases) in mappings.items():
        if client_field not in official:
            continue
        expected = norm(official.get(client_field))
        if aliases:
            expected = aliases.get(expected, expected)
        if server_field == "tslot":
            actual = norm(template.get(server_field, "NONE"))
        elif server_field == "delayId":
            actual = norm(template.get(server_field, "0"))
        elif server_field == "pvp_damage":
            # No motor, zero/ausente significa multiplicador neutro (100%).
            actual = norm(template.get(server_field, "100"))
            if actual == "0":
                actual = "100"
        else:
            actual = norm(template.get(server_field))
        if expected != actual:
            differences.append(f"{server_field}:{template.get(server_field)}!={official.get(client_field)}")
    if "delay_time" in official:
        expected_cooldown = str(int(float(official.get("delay_time") or 0)) // 100)
        if template.get("cooldown", "0") != expected_cooldown:
            differences.append(f"cooldown:{template.get('cooldown')}!={expected_cooldown}")
    # O modelo atual tem pvp_damage, mas nao possui atributo pve_damage. O
    # valor pode eventualmente estar incorporado a outro coeficiente; ate essa
    # equivalencia ser demonstrada, a lacuna de representacao fica explicita.
    if official.get("pve_damage_ratio") not in {None, "", "100"}:
        differences.append(f"pve_damage_ratio:{official['pve_damage_ratio']}:sem_representacao_no_template")
    props = template.find("properties")
    prop_mappings = {
        "first_target_valid_distance": "first_target_range",
        "target_range_opt1": "target_distance",
        "target_maxcount": "target_maxcount",
    }
    if "first_target" in official:
        actual_first_target = norm(props.get("first_target") if props is not None else None)
        if actual_first_target != norm(official["first_target"]):
            differences.append(f"properties.first_target:{actual_first_target}!={official['first_target']}")
    for client_field, server_field in prop_mappings.items():
        if client_field in official:
            actual = int(props.get(server_field, "0")) if props is not None else 0
            expected = int(float(official[client_field] or 0))
            if actual != expected:
                differences.append(f"properties.{server_field}:{actual}!={expected}")

    expected_effects = official_effects(official)
    actual_effects = server_effects(template)
    for slot, effect_type in expected_effects.items():
        accepted = {norm(effect_type)} | ALIASES.get(norm(effect_type), set())
        if not any(norm(tag) in accepted for tag in actual_effects.get(slot, [])):
            differences.append(f"effect{slot}:{actual_effects.get(slot, [])}!={effect_type}")
    for slot in set(actual_effects) - set(expected_effects):
        differences.append(f"effect{slot}:sem_slot_oficial")
    return differences


def main() -> None:
    base = records(CLIENT_SKILLS / "client_skills.xml")
    special = records(CLIENT_SKILLS / "special" / "client_skills.xml")
    special2 = records(CLIENT_SKILLS / "special2" / "client_skills.xml")
    templates = {int(entry.get("skill_id")): entry for entry in ET.parse(STATIC / "skills" / "skill_templates.xml").getroot()}
    tree, tree_stigmas = load_tree()
    npc_refs = load_npc_refs()
    server_item_refs, item_stigmas = load_server_item_refs()
    name_to_id = {row.get("name", "").lower(): skill_id for skill_id, row in base.items() if row.get("name")}
    client_item_refs, unresolved_client_item_refs = load_client_item_refs(name_to_id)
    registry, stub_types = load_effect_registry()
    effect_classes = set(registry.values())
    all_ids = set(base) | set(special) | set(special2) | set(templates)
    test_refs, tests_by_effect = load_test_refs(all_ids, effect_classes)
    pcap_client, pcap_server, pcap_meta = load_pcap_refs()

    inventory = []
    status_counts = collections.Counter()
    category_counts = collections.Counter()
    overlay_fields = collections.Counter()
    structural_fields = collections.Counter()
    for skill_id in sorted(all_ids):
        official = base.get(skill_id)
        template = templates.get(skill_id)
        special_diff = variant_diff(official, special.get(skill_id)) if official else {}
        special2_diff = variant_diff(official, special2.get(skill_id)) if official else {}
        for field in special2_diff:
            overlay_fields[field] += 1

        official_fx = official_effects(official or {})
        server_fx = server_effects(template)
        missing_registry = []
        stub_effects = []
        effect_code = []
        for effect_type in official_fx.values():
            accepted = {norm(effect_type)} | ALIASES.get(norm(effect_type), set())
            matched = [(tag, cls) for tag, cls in registry.items() if norm(tag) in accepted]
            if not matched:
                missing_registry.append(effect_type)
            for tag, class_name in matched:
                effect_code.append(f"{tag}:{class_name}")
                if tag in stub_types:
                    stub_effects.append(effect_type)

        differences = structural_differences(official, template) if official else []
        for difference in differences:
            structural_fields[difference.split(":", 1)[0]] += 1
        statuses = []
        if official is None:
            statuses.append("SEM_DEFINICAO_CLIENTE_BASE")
        if template is None:
            statuses.append("AUSENTE_EMULADOR")
            if official and not any(
                official.get(field)
                for field in ("activation_attribute", "type", "sub_type")
            ) and not official_fx:
                statuses.append("ENTRADA_CLIENTE_NAO_EXECUTAVEL_SEM_TEMPLATE")
        if special_diff or special2_diff:
            statuses.append("PENDENTE_VARIANTE_CLIENTE")
        if differences and template is not None:
            statuses.append("DIVERGENTE_ESTRUTURAL")
        if missing_registry:
            statuses.append("EFEITO_SEM_REGISTRO_JAVA")
        if stub_effects:
            statuses.append("EFEITO_JAVA_STUB")
        if not statuses:
            statuses.append("ALINHADO_ESTATICAMENTE_NAO_VALIDADO")
        if pcap_client[skill_id] or pcap_server[skill_id]:
            statuses.append("OBSERVADA_EM_PCAP")

        categories = set()
        if skill_id in tree:
            categories.add("jogador")
        activation = norm((official or {}).get("activation_attribute"))
        if activation == "passive":
            categories.add("passiva")
        elif activation in {"active", "provoked", "maintain", "toggle"}:
            categories.add("ativa")
        if skill_id in tree_stigmas or skill_id in item_stigmas:
            categories.add("stigma")
        if skill_id in npc_refs:
            categories.add("npc_boss")
        if skill_id in server_item_refs or skill_id in client_item_refs:
            categories.add("item_equipamento")
        if "ENTRADA_CLIENTE_NAO_EXECUTAVEL_SEM_TEMPLATE" in statuses:
            categories.add("acao_cliente")
        subtype = norm((official or {}).get("sub_type"))
        if subtype == "buff":
            categories.add("buff")
        elif subtype == "debuff":
            categories.add("debuff")
        if any("transform" in norm(value) or "shapechange" in norm(value) or "polymorph" in norm(value) for value in official_fx.values()):
            categories.add("transformacao")
        special_markers = {
            "resurrect", "teleport", "return", "summon", "counter", "reflect",
            "shield", "absorb", "fly", "recall", "portal", "movebehind", "dash",
        }
        if any(any(marker in norm(value) for marker in special_markers) for value in official_fx.values()):
            categories.add("especial")
        if not categories:
            categories.add("especial_ou_interna")

        for status in statuses:
            status_counts[status] += 1
        for category in categories:
            category_counts[category] += 1

        tree_rows = tree.get(skill_id, [])
        inventory.append({
            "skill_id": skill_id,
            "nome_oficial_base": (official or {}).get("name"),
            "nome_template": template.get("name") if template is not None else None,
            "classes": sorted({row.get("classId", "") for row in tree_rows}),
            "niveis_aprendizado": sorted({int(row.get("minLevel", "1")) for row in tree_rows}),
            "categorias": sorted(categories),
            "status": statuses,
            "cliente": {
                "presente_base": skill_id in base,
                "presente_special": skill_id in special,
                "presente_special2": skill_id in special2,
                "diferencas_special": special_diff,
                "diferencas_special2": special2_diff,
                "ativacao": (official or {}).get("activation_attribute"),
                "tipo": (official or {}).get("type"),
                "subtipo": (official or {}).get("sub_type"),
                "efeitos": official_fx,
            },
            "emulador": {
                "template": skill_id in templates,
                "stack": template.get("stack") if template is not None else None,
                "efeitos": server_fx,
                "divergencias_estruturais": differences,
            },
            "origens": {
                "arvore": tree_rows,
                "itens_servidor": sorted(server_item_refs.get(skill_id, set())),
                "itens_cliente": sorted(client_item_refs.get(skill_id, set())),
                "npcs_servidor": sorted(npc_refs.get(skill_id, set())),
            },
            "execucao": {
                "efeitos_java": sorted(set(effect_code)),
                "efeitos_sem_registro": sorted(set(missing_registry)),
                "efeitos_stub": sorted(set(stub_effects)),
            },
            "evidencia_pcap": {
                "casts_cliente": pcap_client[skill_id],
                "casts_servidor": pcap_server[skill_id],
            },
            "testes": sorted(test_refs.get(skill_id, set()) | {
                test for code in effect_code for test in tests_by_effect.get(code.split(":", 1)[1], set())
            }),
        })

    payload = {
        "metodologia": {
            "cliente_base": str((CLIENT_SKILLS / "client_skills.xml").relative_to(ROOT)).replace("\\", "/"),
            "overlays": ["special", "special2"],
            "regra_overlay": "nao selecionar sem evidencia oficial",
            "pcap": pcap_meta,
            "observacao": "OBSERVADA_EM_PCAP comprova uso do ID, nao equivalencia integral de comportamento.",
            "referencias_itens_cliente_nao_resolvidas": unresolved_client_item_refs,
        },
        "contagens": {
            "ids_uniao": len(all_ids),
            "cliente_base": len(base),
            "cliente_special": len(special),
            "cliente_special2": len(special2),
            "templates_emulador": len(templates),
            "skills_arvore_jogador": len(tree),
            "skills_npc_referenciadas": len(npc_refs),
            "skills_item_referenciadas_servidor": len(server_item_refs),
            "skills_item_referenciadas_cliente": len(client_item_refs),
            "referencias_itens_cliente_nao_resolvidas": len(unresolved_client_item_refs),
            "skills_observadas_cliente_pcap": len(pcap_client),
            "skills_observadas_servidor_pcap": len(pcap_server),
        },
        "status": dict(sorted(status_counts.items())),
        "categorias": dict(sorted(category_counts.items())),
        "campos_divergentes_special2": dict(overlay_fields.most_common()),
        "divergencias_estruturais_por_campo": dict(structural_fields.most_common()),
        "skills": inventory,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    columns = [
        "skill_id", "nome_oficial_base", "nome_template", "classes", "niveis", "categorias", "status",
        "template", "efeitos_oficiais", "efeitos_servidor", "divergencias", "itens_servidor", "npcs_servidor",
        "casts_cliente_pcap", "casts_servidor_pcap", "efeitos_java", "testes",
    ]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for row in inventory:
            writer.writerow({
                "skill_id": row["skill_id"],
                "nome_oficial_base": row["nome_oficial_base"],
                "nome_template": row["nome_template"],
                "classes": ",".join(row["classes"]),
                "niveis": ",".join(map(str, row["niveis_aprendizado"])),
                "categorias": ",".join(row["categorias"]),
                "status": ",".join(row["status"]),
                "template": row["emulador"]["template"],
                "efeitos_oficiais": json.dumps(row["cliente"]["efeitos"], ensure_ascii=False, separators=(",", ":")),
                "efeitos_servidor": json.dumps(row["emulador"]["efeitos"], ensure_ascii=False, separators=(",", ":")),
                "divergencias": " | ".join(row["emulador"]["divergencias_estruturais"]),
                "itens_servidor": ",".join(map(str, row["origens"]["itens_servidor"])),
                "npcs_servidor": ",".join(map(str, row["origens"]["npcs_servidor"])),
                "casts_cliente_pcap": row["evidencia_pcap"]["casts_cliente"],
                "casts_servidor_pcap": row["evidencia_pcap"]["casts_servidor"],
                "efeitos_java": ",".join(row["execucao"]["efeitos_java"]),
                "testes": ",".join(row["testes"]),
            })

    missing = [row for row in inventory if "AUSENTE_EMULADOR" in row["status"]]
    non_executable_missing = [
        row for row in missing
        if "ENTRADA_CLIENTE_NAO_EXECUTAVEL_SEM_TEMPLATE" in row["status"]
    ]
    extras = [row for row in inventory if "SEM_DEFINICAO_CLIENTE_BASE" in row["status"]]
    overlay = [row for row in inventory if "PENDENTE_VARIANTE_CLIENTE" in row["status"]]
    no_tests = [row for row in inventory if row["emulador"]["template"] and not row["testes"]]
    lines = [
        "# Auditoria rastreável das Skills — Aion Classic 5.0 EU",
        "",
        "## Resultado desta etapa",
        "",
        f"O inventário contém **{len(inventory)} IDs** na união das fontes: {len(base)} no cliente base e {len(templates)} no emulador.",
        f"Há **{len(missing)} ID oficial ausente no emulador**, **{len(extras)} templates sem definição na base do cliente** e **{len(overlay)} Skills com divergência entre variantes do mesmo cliente**.",
        "Nenhuma dessas categorias autoriza remoção ou correção automática. O relatório registra evidência e mantém lacunas como pendências.",
        "",
        "### Lacunas de definição por ID",
        "",
        "- Oficial sem template: " + (", ".join(f"`{row['skill_id']}`" for row in missing) or "nenhum") + ".",
        "- Entrada oficial sem dados executáveis e sem template: " + (", ".join(f"`{row['skill_id']}`" for row in non_executable_missing) or "nenhum") + ".",
        "- Template sem definição na base oficial: " + (", ".join(f"`{row['skill_id']}`" for row in extras) or "nenhum") + ".",
        "A classificação de entrada não executável exige ausência simultânea de ativação, tipo, subtipo e efeitos no cliente. Ela documenta a lacuna, mas não autoriza inventar um template.",
        "",
        "## Bloqueio de fonte identificado",
        "",
        f"O overlay `special2` diverge da base em {len([row for row in inventory if row['cliente']['diferencas_special2']])} Skills. As capturas disponíveis contêm **{pcap_meta['login_port_packets']} pacotes na porta 2106**, portanto não comprovam qual overlay foi selecionado pela lista oficial de servidores.",
        "O emulador anuncia o bit Classic, mas isso não demonstra sozinho se o cliente usa `base`, `special` ou `special2`. Até essa seleção ser comprovada, os valores divergentes ficam classificados como `PENDENTE_VARIANTE_CLIENTE`.",
        "",
        "## Cobertura verificável",
        "",
        f"Foram lidos {pcap_meta['files']} PCAPs, com {pcap_meta['sessions']} sessões de jogo decodificadas. Há {len(pcap_client)} IDs lançados pelo cliente e {len(pcap_server)} IDs anunciados pelo servidor nas capturas.",
        "A presença no PCAP comprova que o ID foi usado; não comprova por si só dano, duração, prioridade, persistência ou todas as transições internas.",
        f"Há {len(unresolved_client_item_refs)} referências de itens não resolvidas no namespace principal de Skills; elas permanecem enumeradas no JSON e não foram descartadas.",
        f"Existem {len(no_tests)} templates sem referência direta ou indireta encontrada nos testes Java atuais.",
        "",
        "## Estado por classificação",
        "",
        "| Classificação | Skills |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in sorted(status_counts.items()))
    lines += [
        "",
        "## Divergências estruturais por campo",
        "",
        "| Campo | Skills |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in structural_fields.most_common())
    lines += [
        "",
        "## Categorias (sobrepostas)",
        "",
        "| Categoria | Skills |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in sorted(category_counts.items()))
    lines += [
        "",
        "## Critério de conclusão",
        "",
        "`ALINHADO_ESTATICAMENTE_NAO_VALIDADO` não significa compatibilidade funcional. Uma Skill só poderá ser promovida a validada após teste de execução e, quando aplicável, comparação com PCAP oficial. Nenhuma Skill sem evidência foi contada como correta.",
        "",
        "## Artefatos",
        "",
        "- `auditoria_skills_50_completa.json`: evidência completa, inclusive diferenças de overlays.",
        "- `matriz_rastreabilidade_skills_50.csv`: matriz por ID para triagem e acompanhamento.",
        "- `audit_50_skills_complete.py`: gerador reproduzível e somente-leitura sobre as fontes.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"contagens": payload["contagens"], "status": payload["status"], "pcap": pcap_meta}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
