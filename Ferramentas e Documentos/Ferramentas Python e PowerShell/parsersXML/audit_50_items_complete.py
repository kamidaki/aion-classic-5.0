#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria reproduzivel e individual do catalogo de itens Classic 5.0 EU.

O programa nao altera dados do emulador. Ele compara campos cuja equivalencia e
direta, cataloga funcoes que dependem de outras tabelas e gera inventarios de
arquitetura e evidencias. Qualquer campo sem mapeamento oficial demonstravel e
registrado como pendente, nunca inferido como correto.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import rebuild_50_item_templates as templates


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CLIENT = PROJECT_ROOT / "5 - Documentação e Referências" / "3 - Client 5.0 - Dados Extraidos"
DEFAULT_CATALOG = Path("data") / "europe" / "Items" / "client_items.xml"
SERVER_ITEMS = PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data" / "items" / "item_templates.xml"
PRODUCT_ITEMS = PROJECT_ROOT / "Emulador - Produto Final" / "GameServer" / "data" / "static_data" / "items" / "item_templates.xml"
DEFAULT_OUTPUT = PROJECT_ROOT / "5 - Documentação e Referências" / "4 - Auditoria de Itens Classic 5.0"
TEST_GROUPS = (
    "Adquirir, equipar e desequipar itens", "Trocar armas e conjuntos de equipamentos",
    "Fundir e desfazer a fusao de armas", "Aplicar e remover manastones e melhorias",
    "Utilizar consumiveis, livros e itens especiais", "Dividir, juntar, mover e descartar pilhas",
    "Guardar e retirar itens do Warehouse", "Comprar, vender e negociar itens",
    "Abrir pacotes e selecionar recompensas", "Produzir e combinar itens",
    "Realizar encantamento e extracao", "Coletar loot de monstros e recompensas",
    "Desconectar e reconectar durante operacoes", "Trocar de personagem e reiniciar o servidor",
    "Verificar atributos, aparencia e persistencia",
)

QUALITY = {"junk": "JUNK", "common": "COMMON", "rare": "RARE", "legend": "LEGEND", "legendary": "LEGEND",
           "unique": "UNIQUE", "epic": "EPIC", "mythic": "MYTHIC", "divinity": "DIVINITY"}
ITEM_TYPE = {"normal": "NORMAL", "abyss": "ABYSS", "draconic": "DRACONIC", "devanion": "DEVANION"}
RACE = {"pc_light": "ELYOS", "pc_dark": "ASMODIANS", "pc_light pc_dark": "PC_ALL", "all": "PC_ALL", "": "PC_ALL"}
ATTACK = {"physical": "PHYSICAL", "magic": "MAGICAL", "magical": "MAGICAL"}
CLASS_FIELDS = ("warrior", "fighter", "knight", "scout", "assassin", "ranger", "mage", "wizard", "elementalist",
                "cleric", "priest", "chanter", "monk", "thunderer", "striker", "battlemaster", "orchestrator",
                "lumines", "engineer", "gunner", "runewarrior", "runeblade")
RESTRICT_SOURCES = ("warrior", "fighter", "knight", "scout", "assassin", "ranger", "mage", "wizard", "elementalist",
                    "cleric", "priest", "chanter", "monk", "thunderer", "thunderer", "striker", "battlemaster",
                    "orchestrator", "lumines", "engineer", "gunner", "runewarrior", "runeblade", None, "gunner")
BOOL_MASK = ((1, "lore"), (2, "can_exchange"), (4, "can_sell_to_npc"),
             (8, "can_deposit_to_character_warehouse"), (16, "can_deposit_to_account_warehouse"),
             (32, "can_deposit_to_guild_warehouse"), (64, "breakable"), (128, "soul_bind"),
             (256, "remove_when_logout"), (512, "no_enchant"), (1024, "can_proc_enchant"),
             (2048, "can_composite_weapon"), (8192, "can_split"), (16384, "breakable"))
DIRECT_FIELDS = {
    "level": ("level", lambda value: value or "1"),
    "price": ("price", lambda value: value or "0"),
    "max_stack_count": ("max_stack_count", lambda value: value or "1"),
    "quality": ("quality", lambda value: QUALITY.get(value.lower(), "COMMON")),
    "item_type": ("item_type", lambda value: ITEM_TYPE.get(value.lower(), "NORMAL")),
    "race_permitted": ("race", lambda value: RACE.get(value.lower(), value.upper())),
    "enchant_group": ("enchant_group", lambda value: value),
    "activation_count": ("activate_count", lambda value: value),
    "casting_delay": ("casting_delay", lambda value: value),
    "expire_time": ("expire_time", lambda value: value),
    "return_alias": ("return_alias", lambda value: value.upper()),
    "return_worldid": ("return_world", lambda value: value),
}
ACTION_FIELDS = {
    "activation_skill": "skilluse", "skill_to_learn": "skilllearn", "gain_skill1": "stigma",
    "craft_recipe_info": "craftlearn", "disassembly_item": "decompose", "cosmetic_name": "cosmetic",
    "toy_pet_name": "toypetspawn", "func_pet_name": "adoptpet", "extra_inventory": "expandinventory",
    "assembly_item": "assemble", "reset_instance_coolt_sync_id": "instancetimeclear",
    "cash_title": "titleadd", "dyeing_color": "dye", "quest": "queststart",
}
CLIENT_FIELDS = set(DIRECT_FIELDS) | set(ACTION_FIELDS) | set(CLASS_FIELDS) | {
    "id", "name", "desc", "weapon_type", "armor_type", "equipment_slots", "attack_type", "activate_target",
    "max_enchant_level", "option_slot_bonus", "m_slots", "mgrouptag", "tag", "icon_name", "quest",
    "min_damage", "max_damage", "attack_delay", "critical", "hit_accuracy", "parry", "attack_range", "hit_count",
    "magical_hit_accuracy", "magical_skill_boost", "reduce_max", "cannot_changeskin", "can_dye", "item_drop_permitted",
    "cannot_extraction", "cash_item",
    "stat_enchant_type", "stat_enchant_value", "abyss_point", "abyss_item", "charge_level",
} | set(templates.BASE_MODS) | {name for _, name in BOOL_MASK} | {name + "_max" for name in CLASS_FIELDS}


def meaningful(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in ("", "0", "false", "none", "no")


def expected_restriction(item: dict[str, str], suffix: str = "") -> list[int]:
    present = any(source and source + suffix in item for source in RESTRICT_SOURCES)
    if not present:
        return [0 if suffix else 1] * len(RESTRICT_SOURCES)
    return [int(item.get(source + suffix, "0") or 0) if source else 0 for source in RESTRICT_SOURCES]


def effective_server_restriction(raw: str | None, maximum: bool = False) -> list[int]:
    size = len(RESTRICT_SOURCES)
    if raw is None:
        return [0 if maximum else 1] * size
    values = [int(value) for value in raw.split()]
    if len(values) >= size:
        return values[:size]
    result = values + [0] * (size - len(values))
    if values and all(values):
        fill = max(values) if maximum else min(values)
        result[len(values):] = [fill] * (size - len(values))
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_client(path: Path) -> dict[str, dict[str, str]]:
    items = {}
    for event, element in ET.iterparse(path, events=("end",)):
        if element.tag != "client_item":
            continue
        data = {child.tag: (child.text or "").strip() for child in element if child.tag in CLIENT_FIELDS or child.tag.startswith("bonus_attr")}
        if data.get("id"):
            items[data["id"]] = data
        element.clear()
    return items


def read_server(path: Path) -> dict[str, dict]:
    items = {}
    for event, element in ET.iterparse(path, events=("end",)):
        if element.tag != "item_template":
            continue
        actions = set()
        action_root = element.find("actions")
        if action_root is not None:
            actions = {child.tag for child in action_root}
        if element.find("stigma") is not None:
            actions.add("stigma")
        weapon = element.find("weapon_stats")
        modifiers = element.find("modifiers")
        modifier_values = collections.Counter()
        if modifiers is not None:
            for modifier in modifiers.iter():
                if modifier.tag not in ("add", "sub", "rate", "set", "abs", "mean"):
                    continue
                try:
                    value = int(float(modifier.attrib.get("value", "")))
                except ValueError:
                    continue
                modifier_values[(modifier.tag, modifier.attrib.get("name"), value,
                                 modifier.attrib.get("bonus", "false") == "true")] += 1
        items[element.attrib["id"]] = {
            "attrs": dict(element.attrib),
            "actions": actions,
            "weapon": dict(weapon.attrib) if weapon is not None else {},
            "modifier_count": len(modifiers) if modifiers is not None else 0,
            "modifiers": modifier_values,
            "children": {child.tag for child in element},
        }
        element.clear()
    return items


def load_strings(client_root: Path, wanted: set[str]) -> dict[str, tuple[str, str]]:
    strings_dir = client_root / "data" / "Strings"
    found = {}
    if not strings_dir.is_dir():
        return found
    pattern = re.compile(r"<string>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>(?:\s*<body>(.*?)</body>)?", re.S | re.I)
    for path in sorted(strings_dir.glob("*.xml")):
        raw = path.read_bytes()
        text = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
        for string_id, name, body in pattern.findall(text):
            key = name.strip().upper()
            if key in wanted:
                clean_body = re.sub(r"<[^>]+>", "", body or "").strip()
                found[key] = (string_id, clean_body)
    return found


def category(item: dict[str, str]) -> str:
    weapon = item.get("weapon_type", "").lower()
    armor = item.get("armor_type", "").lower()
    slots = item.get("equipment_slots", "").lower()
    group = (item.get("mgrouptag", "") + " " + item.get("tag", "")).lower()
    if weapon and weapon != "none": return "armas"
    if armor == "shield": return "escudos"
    if slots == "seed": return "arcament"
    if slots == "right_or_left_battery": return "power_shards"
    if slots in ("right_or_left_ear", "right_or_left_finger", "neck", "waist"): return "acessorios"
    if armor and armor != "none": return "armaduras"
    if "stigma" in group or meaningful(item.get("gain_skill1")): return "stigmas"
    if meaningful(item.get("skill_to_learn")): return "skill_books"
    if meaningful(item.get("craft_recipe_info")): return "receitas"
    if any(token in group for token in ("potion", "food", "drink", "candy", "scroll", "jelly", "cure")): return "consumiveis"
    if any(token in group for token in ("enchant", "option", "proc_all")): return "melhorias"
    if meaningful(item.get("quest")) or "i_q_" in group: return "missao"
    if meaningful(item.get("activation_skill")): return "utilizaveis"
    if any(token in group for token in ("material", "harvest", "gather", "dr_material")): return "materiais"
    return "outros"


def expected_mask(item: dict[str, str]) -> str:
    mask = 0
    for bit, field in BOOL_MASK:
        if item.get(field, "").upper() == "TRUE":
            mask |= bit
    if item.get("cannot_changeskin") == "0": mask |= 4096
    if meaningful(item.get("can_dye")): mask |= 32768
    return str(mask)


def expected_client_mask(item: dict[str, str]) -> str:
    flags = ((0, "lore"), (1, "can_exchange"), (2, "can_sell_to_npc"),
             (3, "can_deposit_to_character_warehouse"), (4, "can_deposit_to_account_warehouse"),
             (5, "breakable"), (6, "soul_bind"), (9, "can_deposit_to_guild_warehouse"),
             (13, "can_split"), (15, "cannot_extraction"))
    value = sum(1 << bit for bit, field in flags if item.get(field, "").upper() == "TRUE")
    if item.get("no_enchant", "TRUE").upper() != "FALSE": value |= 1 << 8
    if meaningful(item.get("quest")): value |= 1 << 10
    if item.get("weapon_type", "none").lower() != "none": value |= 1 << 11
    if item.get("cash_item") == "1": value |= 1 << 12
    if item.get("cannot_changeskin", "1") != "0": value |= 1 << 14
    return str(value)


def compare_item(client: dict[str, str] | None, server: dict | None, strings: dict[str, tuple[str, str]]) -> dict:
    if client is None:
        return {"status": "LEGADO_SO_EMULADOR", "differences": ["id ausente no cliente oficial"], "pending": []}
    if server is None:
        return {"status": "AUSENTE_NO_EMULADOR", "differences": ["id ausente no item_templates.xml"], "pending": []}
    attrs = server["attrs"]
    differences, pending = [], []
    if attrs.get("cName", "").lower() != client.get("name", "").lower():
        differences.append(f"cName:{client.get('name', '')}!={attrs.get('cName', '')}")
    desc_key = client.get("desc", "").upper()
    if desc_key in strings and attrs.get("desc", "0") != strings[desc_key][0]:
        differences.append(f"desc:{strings[desc_key][0]}!={attrs.get('desc', '0')}")
    server_defaults = {"price": "0", "max_stack_count": "1", "activate_count": "0", "casting_delay": "0",
                       "expire_time": "0", "return_world": "0", "item_type": "NORMAL", "race": "PC_ALL"}
    for source, (target, transform) in DIRECT_FIELDS.items():
        raw = client.get(source)
        if raw is None or raw == "":
            continue
        if source == "casting_delay" and int(raw) > 2_147_483_647:
            pending.append(f"casting_delay={raw} excede xs:int/Java int")
            continue
        if source == "max_stack_count" and int(raw) < 1:
            pending.append(f"max_stack_count={raw} requer semantica operacional oficial")
            continue
        expected, actual = transform(raw), attrs.get(target, server_defaults.get(target))
        if str(expected) != str(actual):
            differences.append(f"{target}:{expected}!={actual or '<ausente>'}")
    attack = client.get("attack_type", "").lower()
    if attack and ATTACK.get(attack, attack.upper()) != attrs.get("attack_type"):
        differences.append(f"attack_type:{ATTACK.get(attack, attack.upper())}!={attrs.get('attack_type', '<ausente>')}")
    target = client.get("activate_target", "")
    if target and target.upper() != attrs.get("activate_target", "NONE"):
        differences.append(f"activate_target:{target.upper()}!={attrs.get('activate_target', 'NONE')}")
    if expected_mask(client) != attrs.get("mask"):
        differences.append(f"mask:{expected_mask(client)}!={attrs.get('mask', '<ausente>')}")
    if expected_client_mask(client) != attrs.get("client_mask"):
        differences.append(f"client_mask:{expected_client_mask(client)}!={attrs.get('client_mask', '<ausente>')}")
    weapon_map = (("min_damage", "min_damage", 1), ("max_damage", "max_damage", 1),
                  ("attack_delay", "attack_speed", 1), ("critical", "critical", 1),
                  ("hit_accuracy", "physical_accuracy", 1), ("parry", "parry", 1),
                  ("magical_hit_accuracy", "magical_accuracy", 1),
                  ("magical_skill_boost", "boost_magical_skill", 1),
                  ("attack_range", "attack_range", 1000), ("hit_count", "hit_count", 1),
                  ("reduce_max", "reduce_max", 1))
    for source, target_name, multiplier in weapon_map:
        raw = client.get(source)
        if raw in (None, ""):
            continue
        try:
            expected = str(int(round(float(raw) * multiplier)))
        except ValueError:
            continue
        actual = server["weapon"].get(target_name, "0")
        if actual != expected:
            differences.append(f"weapon.{target_name}:{expected}!={actual}")
    expected_min = expected_restriction(client)
    actual_min = effective_server_restriction(attrs.get("restrict"))
    if any(expected_min[i] != actual_min[i] for i in range(len(RESTRICT_SOURCES)) if i != 23):
        differences.append("restrict:" + " ".join(map(str, expected_min)) + "!=" + " ".join(map(str, actual_min)))
    expected_max = expected_restriction(client, "_max")
    actual_max = effective_server_restriction(attrs.get("restrict_max"), maximum=True)
    if any(expected_max[i] != actual_max[i] for i in range(len(RESTRICT_SOURCES)) if i != 23):
        differences.append("restrict_max:" + " ".join(map(str, expected_max)) + "!=" + " ".join(map(str, actual_max)))
    for field, action in ACTION_FIELDS.items():
        if meaningful(client.get(field)) and action not in server["actions"]:
            pending.append(f"acao {action} indicada por {field}")
    unmapped = collections.Counter()
    expected_modifiers = collections.Counter(templates.gen_mods(client, unmapped))
    for name, count in sorted(unmapped.items()):
        pending.append(f"modifier oficial sem mapeamento:{name} ({count}x)")
    for (operation, stat, value, bonus), count in sorted((expected_modifiers - server["modifiers"]).items()):
        pending.append(f"modifier oficial ausente:{operation}:{stat}:{value}:bonus={str(bonus).lower()} ({count}x)")
    if differences:
        status = "DIVERGENTE_COMPROVADO"
    elif pending:
        status = "PENDENTE_RELACAO"
    else:
        status = "COMPATIVEL_NOS_CAMPOS_AUDITADOS"
    return {"status": status, "differences": differences, "pending": pending}


def associated_systems(item: dict[str, str], server: dict | None) -> list[str]:
    systems = []
    if item.get("equipment_slots"): systems.append("equipamento")
    if item.get("enchant_group") or meaningful(item.get("no_enchant")): systems.append("encantamento")
    if meaningful(item.get("can_composite_weapon")): systems.append("fusao")
    if meaningful(item.get("craft_recipe_info")): systems.append("crafting")
    if meaningful(item.get("activation_skill")): systems.extend(("uso", "skills"))
    if meaningful(item.get("expire_time")): systems.append("temporarios")
    if meaningful(item.get("can_exchange")): systems.append("comercio")
    if server:
        systems.extend(sorted(server["actions"]))
    return sorted(set(systems))


def inventory_architecture(output: Path) -> dict:
    roots = [PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "src",
             PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "data" / "static_data",
             PROJECT_ROOT / "Código Fonte - Emulador" / "game-server" / "sql",
             PROJECT_ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Wireshark - Oficial Classic 5.0"]
    pattern = re.compile(r"item|inventory|equipment|warehouse|broker|trade|loot|craft|enchant|manastone|godstone|compose|fusion|recipe|reward", re.I)
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            is_capture = path.suffix.lower() in (".pcap", ".pcapng")
            if path.is_file() and (is_capture or pattern.search(path.as_posix())):
                suffix = path.suffix.lower()
                layer = "pcap" if suffix in (".pcap", ".pcapng") else "java" if suffix == ".java" else "sql" if suffix == ".sql" else "dados"
                rows.append((layer, relative(path), path.stat().st_size))
    with (output / "inventario_arquitetura_itens_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("camada", "arquivo", "bytes"))
        writer.writerows(sorted(rows))
    return dict(collections.Counter(row[0] for row in rows))


def compare_catalog_variants(client_root: Path, canonical: dict[str, dict[str, str]], output: Path) -> dict[str, int]:
    counts = {}
    rows = []
    canonical_rel = DEFAULT_CATALOG.as_posix()
    for path in sorted(client_root.glob("data/**/client_items.xml")):
        rel = path.relative_to(client_root).as_posix()
        if rel == canonical_rel:
            continue
        variant = read_client(path)
        changed = 0
        for item_id in sorted(set(canonical) | set(variant), key=int):
            base, other = canonical.get(item_id), variant.get(item_id)
            if base == other:
                continue
            changed += 1
            fields = sorted(key for key in set(base or {}) | set(other or {}) if (base or {}).get(key) != (other or {}).get(key))
            rows.append((item_id, rel, ",".join(fields), "ausente" if base is None else "presente",
                         "ausente" if other is None else "presente"))
        counts[rel] = changed
    with (output / "comparacao_variantes_catalogo_itens_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "variante_comparada", "campos_diferentes", "camada_europe", "variante"))
        writer.writerows(rows)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cliente", type=Path, default=DEFAULT_CLIENT)
    parser.add_argument("--catalogo", type=Path, default=DEFAULT_CATALOG,
                        help="Caminho relativo do client_items.xml; por padrao usa a camada Europe do cliente EU")
    parser.add_argument("--saida", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    client_root = args.cliente.resolve()
    output = args.saida.resolve()
    client_path = client_root / args.catalogo
    for path in (client_path, SERVER_ITEMS, PRODUCT_ITEMS):
        if not path.is_file():
            raise SystemExit(f"Arquivo obrigatorio ausente: {path}")
    if sha256(SERVER_ITEMS) != sha256(PRODUCT_ITEMS):
        raise SystemExit("item_templates.xml do fonte e do produto final nao estao sincronizados")
    output.mkdir(parents=True, exist_ok=True)
    client = read_client(client_path)
    server = read_server(SERVER_ITEMS)
    wanted_strings = {item.get("desc", "").upper() for item in client.values() if item.get("desc")}
    strings = load_strings(client_root, wanted_strings)
    ids = sorted(set(client) | set(server), key=int)
    status_count, category_count, rows = collections.Counter(), collections.Counter(), []
    for item_id in ids:
        ci, si = client.get(item_id), server.get(item_id)
        result = compare_item(ci, si, strings)
        cat = category(ci) if ci else "legado"
        status_count[result["status"]] += 1
        category_count[cat] += 1
        attrs = si["attrs"] if si else {}
        desc_key = ci.get("desc", "").upper() if ci else ""
        rows.append((item_id, ci.get("name", "") if ci else attrs.get("cName", ""),
                     strings.get(desc_key, ("", attrs.get("name", "")))[1], cat, result["status"],
                     " | ".join(result["differences"]), " | ".join(result["pending"]),
                     ",".join(associated_systems(ci or {}, si)),
                     relative(client_path) if ci else "", relative(SERVER_ITEMS) if si else ""))
    csv_path = output / "matriz_rastreabilidade_itens_50.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("id", "nome_interno", "nome_localizado", "categoria", "status", "diferencas_comprovadas",
                         "pendencias", "sistemas_associados", "fonte_cliente", "fonte_emulador"))
        writer.writerows(rows)
    with (output / "matriz_testes_itens_50.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(("grupo", "status", "cenario", "resultado_esperado", "resultado_obtido", "evidencia", "regressoes"))
        for group in TEST_GROUPS:
            writer.writerow((group, "PENDENTE_END_TO_END", "Executar no cliente oficial com item representativo de cada categoria aplicavel",
                             "Estado visual, memoria, banco e pacotes permanecem consistentes", "Nao executado nesta etapa",
                             "PCAP + log do GameServer + consulta antes/depois + captura do cliente", "Nao avaliadas"))
    architecture = inventory_architecture(output)
    variant_differences = compare_catalog_variants(client_root, client, output)
    catalog_variants = {}
    for path in sorted(client_root.glob("data/**/client_items.xml")):
        catalog_variants[relative(path)] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    summary = {
        "fonte_cliente": relative(client_path), "sha256_cliente": sha256(client_path),
        "fonte_emulador": relative(SERVER_ITEMS), "sha256_emulador": sha256(SERVER_ITEMS),
        "itens_oficiais": len(client), "itens_emulador": len(server),
        "itens_por_status": dict(sorted(status_count.items())),
        "itens_por_categoria": dict(sorted(category_count.items())),
        "strings_de_item_resolvidas": len(strings), "arquitetura_por_camada": architecture,
        "variantes_catalogo_cliente": catalog_variants,
        "itens_diferentes_por_variante_contra_europe": variant_differences,
        "criterio": "Compatibilidade limitada aos campos de equivalencia direta; pendencias nao contam como validadas.",
    }
    (output / "resumo_auditoria_itens_50.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# Auditoria integral de itens — Aion Classic 5.0 EU", "", "## Linha de base", "",
          f"- Itens oficiais: **{len(client)}**.", f"- Templates do emulador: **{len(server)}**.",
          f"- Strings oficiais resolvidas: **{len(strings)}**.", f"- Fonte e produto final sincronizados: **sim** (`{sha256(SERVER_ITEMS)}`).", "",
          "## Classificacao individual", ""]
    md += [f"- {key}: **{value}**" for key, value in sorted(status_count.items())]
    md += ["", "A matriz CSV contém uma linha para cada ID e registra diferenças, pendências, sistemas e arquivos de origem.", "",
           "## Categorias", ""]
    md += [f"- {key}: **{value}**" for key, value in sorted(category_count.items())]
    md += ["", "## Arquitetura inventariada", ""]
    md += [f"- {key}: **{value} arquivos**" for key, value in sorted(architecture.items())]
    md += ["", "## Limites probatorios", "",
           "Esta execução não declara funcionamento em jogo. Campos diretos divergentes são comprovados pelos XMLs; ações e relações sem mapeamento inequívoco permanecem pendentes de tabela oficial, PCAP ou análise do binário. Os 15 grupos de testes manuais permanecem não concluídos até haver evidência executada e registrada.", ""]
    md += ["## Checklist end-to-end", "", "**0 de 15 concluídos (0%)**.", ""]
    md += [f"- [ ] {group}" for group in TEST_GROUPS]
    md += [""]
    (output / "relatorio_auditoria_itens_50.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
