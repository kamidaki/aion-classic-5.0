#!/usr/bin/env python3
"""Audita mensagens de Skill e caminhos que contornam defesa/resistencia.

Usa somente o cliente Classic 5.0 extraido e o codigo/dados locais. O relatorio
nao presume que um bypass seja incorreto: ele enumera exatamente onde o motor
o faz para que cada caso seja validado por evidencia oficial.
"""

from __future__ import annotations

import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "Código Fonte - Emulador" / "game-server"
JAVA = SOURCE / "src" / "com" / "aionemu" / "gameserver"
TEMPLATES = SOURCE / "data" / "static_data" / "skills" / "skill_templates.xml"
CLIENT = ROOT / "Ferramentas e Documentos" / "Client e Coletas" / "Client 5.0 - Dados Extraidos"
CLIENT_MESSAGES = CLIENT / "data" / "Strings" / "client_strings_msg.xml"
CLIENT_SKILLS = CLIENT / "data" / "skills" / "client_skills.xml"
ITEM_TEMPLATES = SOURCE / "data" / "static_data" / "items" / "item_templates.xml"
OUT_JSON = HERE / "auditoria_mensagens_defesa_skills_50.json"
OUT_MD = HERE / "auditoria_mensagens_defesa_skills_50.md"


DAMAGE_TAGS = {
    "bleed", "delaydamage", "dispelbuffcounteratk", "fpatk", "fpatkinstant",
    "magiccounteratk", "noreducespellatk", "poison", "procatk_instant",
    "signetburst", "skillatk", "skillatkdraininstant", "spellatk",
    "spellatkinstant", "spellatkdrain", "spellatkdraininstant",
}


def client_records(path: Path) -> dict[int, dict[str, str]]:
    result = {}
    for entry in ET.parse(path).getroot():
        raw_id = entry.findtext("id")
        if raw_id and raw_id.isdigit():
            result[int(raw_id)] = {child.tag: (child.text or "").strip() for child in entry}
    return result


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def strip_java_comments(text: str) -> str:
    """Remove comentarios sem deslocar offsets/linhas usados no relatorio."""
    result = list(text)
    index = 0
    state = "code"
    while index < len(text):
        char = text[index]
        following = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "/" and following == "/":
                result[index] = result[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if char == "/" and following == "*":
                result[index] = result[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if char == '"':
                state = "string"
            elif char == "'":
                state = "character"
        elif state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                result[index] = " "
        elif state == "block_comment":
            if char == "*" and following == "/":
                result[index] = result[index + 1] = " "
                index += 2
                state = "code"
                continue
            if char != "\n":
                result[index] = " "
        elif state in {"string", "character"}:
            if char == "\\":
                index += 2
                continue
            if (state == "string" and char == '"') or (state == "character" and char == "'"):
                state = "code"
        index += 1
    return "".join(result)


def audit_breakable_godstones() -> list[dict[str, object]]:
    rows = []
    for item in ET.parse(ITEM_TEMPLATES).getroot():
        godstone = item.find("godstone")
        if godstone is None or int(godstone.get("breakprob", "0")) <= 0:
            continue
        rows.append({
            "item_id": int(item.get("id", "0")),
            "nome": item.get("name"),
            "breakprob": int(godstone.get("breakprob", "0")),
            "existe_cliente_oficial": False,
            "breakable_cliente": None,
        })

    pending = {row["item_id"]: row for row in rows}
    for client_items in CLIENT.rglob("client_items.xml"):
        if not pending:
            break
        for _, entry in ET.iterparse(client_items, events=("end",)):
            if entry.tag.lower() not in {"client_item", "item"}:
                continue
            raw_id = entry.findtext("id")
            item_id = int(raw_id) if raw_id and raw_id.isdigit() else 0
            if item_id in pending:
                pending[item_id]["existe_cliente_oficial"] = True
                pending[item_id]["breakable_cliente"] = entry.findtext("breakable")
                pending.pop(item_id)
            entry.clear()
    return rows


def audit_messages() -> dict[str, object]:
    official_entries = client_records(CLIENT_MESSAGES)
    official_by_id = {msg_id: row.get("name", "") for msg_id, row in official_entries.items()}
    packet_path = JAVA / "network" / "aion" / "serverpackets" / "SM_SYSTEM_MESSAGE.java"
    packet_text = packet_path.read_text(encoding="utf-8")
    factories = {}
    factory_pattern = re.compile(
        r"public static SM_SYSTEM_MESSAGE\s+(\w+)\([^)]*\)\s*\{.*?new SM_SYSTEM_MESSAGE\((\d+)",
        re.DOTALL,
    )
    for match in factory_pattern.finditer(packet_text):
        factories[match.group(1)] = {
            "id": int(match.group(2)),
            "linha_definicao": line_number(packet_text, match.start()),
        }

    usages: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    usage_pattern = re.compile(r"SM_SYSTEM_MESSAGE\.(\w+)\(")
    for path in JAVA.rglob("*.java"):
        if path == packet_path:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        executable_text = strip_java_comments(text)
        for match in usage_pattern.finditer(executable_text):
            usages[match.group(1)].append({
                "arquivo": path.relative_to(ROOT).as_posix(),
                "linha": line_number(text, match.start()),
            })

    invalid = []
    mismatched = []
    for name, definition in sorted(factories.items()):
        msg_id = definition["id"]
        used_at = usages.get(name, [])
        if msg_id not in official_by_id:
            invalid.append({"metodo": name, **definition, "usos": used_at})
        else:
            official_name = official_by_id[msg_id]
            if official_name and official_name.upper() != name.upper():
                mismatched.append({
                    "metodo": name,
                    **definition,
                    "nome_oficial": official_name,
                    "usos": used_at,
                })

    return {
        "mensagens_oficiais": len(official_by_id),
        "factories_java": len(factories),
        "ids_java_ausentes_cliente": invalid,
        "usos_invalidos_no_motor_de_skills": [
            {"metodo": row["metodo"], "id": row["id"], "uso": usage}
            for row in invalid
            for usage in row["usos"]
            if "/skillengine/" in usage["arquivo"]
        ],
        "ids_existentes_com_nome_divergente": mismatched,
        "factories_usadas_sem_definicao_java": [
            {"metodo": name, "usos": refs}
            for name, refs in sorted(usages.items())
            if name not in factories
        ],
        "godstones_com_quebra": audit_breakable_godstones(),
    }


def parse_always_no_resist() -> set[str]:
    text = (JAVA / "skillengine" / "effect" / "Effects.java").read_text(encoding="utf-8")
    match = re.search(r"ALWAYS_NO_RESIST\s*=\s*EnumSet\.of\((.*?)\);", text, re.DOTALL)
    if not match:
        return set()
    return {token for token in re.findall(r"\b[A-Z][A-Z0-9_]+\b", match.group(1))}


def parse_fixed_damage_stacks() -> set[str]:
    text = (JAVA / "controllers" / "attack" / "AttackUtil.java").read_text(encoding="utf-8")
    method = re.search(r"private static boolean isUseTemplateDmg\(.*?\n\t\}", text, re.DOTALL)
    if not method:
        return set()
    return {value.lower() for value in re.findall(r'case\s+"([^"]+)"', method.group(0))}


def audit_defense() -> dict[str, object]:
    official = client_records(CLIENT_SKILLS)
    always_no_resist = parse_always_no_resist()
    fixed_damage_stacks = parse_fixed_damage_stacks()
    findings = []
    reason_counts = collections.Counter()

    for template in ET.parse(TEMPLATES).getroot():
        skill_id = int(template.get("skill_id", "0"))
        stack = template.get("stack", "")
        skill_type = template.get("skilltype", "")
        effects = template.find("effects")
        if effects is None:
            continue
        for effect in effects:
            tag = effect.tag
            reasons = []
            if effect.get("noresist", "false").lower() == "true":
                reasons.append("NORESIST_XML")
            effect_enum = re.sub(r"[^A-Za-z0-9]", "", tag).upper()
            if effect_enum in always_no_resist:
                reasons.append("NORESIST_FORCADO_JAVA")
            if tag == "noreducespellatk":
                reasons.append("DANO_FIXO_SEM_DEFESAS_BASE")
            if tag == "procatk_instant" and stack.lower() in fixed_damage_stacks:
                reasons.append("DANO_FIXO_HARDCODE_STACK")
            if tag == "delaydamage":
                reasons.append("IGNORA_ESCUDOS")
            if tag == "skillatk" and effect.get("cannotmiss", "false").lower() == "true":
                reasons.append("CANNOTMISS_XML")
            if tag in DAMAGE_TAGS and not effect.get("element") and skill_type == "MAGICAL":
                reasons.append("DANO_MAGICO_SEM_ELEMENTO_USA_DEFESA_FISICA_OU_NENHUMA")
            if not reasons:
                continue

            official_row = official.get(skill_id, {})
            position = int(effect.get("e", "0"))
            official_no_resist = official_row.get(f"effect{position}_noresist")
            for reason in set(reasons):
                reason_counts[reason] += 1
            findings.append({
                "skill_id": skill_id,
                "nome_oficial": official_row.get("name"),
                "stack": stack,
                "skilltype": skill_type,
                "efeito": tag,
                "posicao": position,
                "elemento": effect.get("element"),
                "noresist_xml": effect.get("noresist"),
                "noresist_cliente": official_no_resist,
                "subtipo_cliente": official_row.get("sub_type"),
                "primeiro_alvo_cliente": official_row.get("first_target"),
                "relacao_alvo_cliente": official_row.get("target_relation_restriction"),
                "motivos": sorted(set(reasons)),
            })

    noresist_conflicts = [
        row for row in findings
        if ("NORESIST_XML" in row["motivos"] or "NORESIST_FORCADO_JAVA" in row["motivos"])
        and row["noresist_cliente"] == "0"
    ]
    hostile_noresist_conflicts = [
        row for row in noresist_conflicts
        if row["relacao_alvo_cliente"] == "Enemy"
    ]
    return {
        "always_no_resist_java": sorted(always_no_resist),
        "stacks_dano_fixo_hardcoded": sorted(fixed_damage_stacks),
        "contagem_por_motivo": dict(sorted(reason_counts.items())),
        "skills_unicas_por_motivo": {
            reason: len({row["skill_id"] for row in findings if reason in row["motivos"]})
            for reason in sorted(reason_counts)
        },
        "efeitos_sinalizados": findings,
        "noresist_servidor_contra_cliente_zero": noresist_conflicts,
        "noresist_hostil_servidor_contra_cliente_zero": hostile_noresist_conflicts,
    }


def main() -> None:
    messages = audit_messages()
    defense = audit_defense()
    payload = {"mensagens": messages, "defesa_resistencia": defense}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    invalid = messages["ids_java_ausentes_cliente"]
    invalid_used = [row for row in invalid if row["usos"]]
    invalid_skill_engine = messages["usos_invalidos_no_motor_de_skills"]
    mismatched_used = [row for row in messages["ids_existentes_com_nome_divergente"] if row["usos"]]
    breakable_godstones = messages["godstones_com_quebra"]
    breakable_official = [row for row in breakable_godstones if row["existe_cliente_oficial"]]
    lines = [
        "# Auditoria de mensagens e defesas das Skills — Classic 5.0",
        "",
        "## Mensagens `???`",
        "",
        f"O cliente oficial contém **{messages['mensagens_oficiais']} mensagens**. O Java declara **{messages['factories_java']} factories**; **{len(invalid)}** apontam para IDs inexistentes no cliente Classic 5.0 e **{len(invalid_used)}** delas são chamadas pelo código atual.",
        "Um ID ausente é causa direta e reproduzível para o cliente exibir `???`. Nome divergente com ID existente é risco de texto/parâmetros incorretos, não necessariamente `???`.",
        f"Após substituir o ID legado de distância por `STR_SKILL_TOO_FAR` (`1300022`), o motor de Skills possui **{len(invalid_skill_engine)} chamada(s)** para IDs ausentes. As demais chamadas inválidas pertencem a outros subsistemas e não foram alteradas sem correspondência oficial comprovada.",
        "",
        "### IDs inexistentes que possuem chamadas",
        "",
        "| ID | Factory | Usos |",
        "|---:|---|---:|",
    ]
    lines.extend(f"| {row['id']} | `{row['metodo']}` | {len(row['usos'])} |" for row in invalid_used)
    lines += [
        "",
        f"Também existem **{len(mismatched_used)} factories usadas cujo ID existe, mas o nome oficial associado ao número é diferente**. Elas permanecem no JSON para revisão de parâmetros.",
        "",
        f"O outro emissor ativo relacionado ao combate, `STR_MSG_BREAK_PROC` (`1402237`), só é alcançado pelos **{len(breakable_godstones)} Godstones de teste** com `breakprob` no servidor. **{len(breakable_official)} deles existem nos arquivos de itens do cliente oficial**; portanto, esse caminho legado não explica o uso de Skills/itens oficiais normais.",
        "",
        "## Defesa e resistência",
        "",
        "Os itens abaixo são caminhos de bypass encontrados no código e nos templates. A presença na lista não prova erro: efeitos de dano fixo, efeitos benéficos e certos danos atrasados podem legitimamente contornar uma camada defensiva.",
        "",
        "| Motivo técnico | Efeitos | Skills únicas |",
        "|---|---:|---:|",
    ]
    lines.extend(
        f"| `{reason}` | {count} | {defense['skills_unicas_por_motivo'][reason]} |"
        for reason, count in defense["contagem_por_motivo"].items()
    )
    lines += [
        "",
        f"Há **{len(defense['noresist_servidor_contra_cliente_zero'])} efeitos** em que o servidor força/declara `noresist`, mas o campo oficial correspondente é `0`. Esses são os candidatos prioritários para teste, pois a divergência é direta.",
        f"Desses, **{len(defense['noresist_hostil_servidor_contra_cliente_zero'])} efeitos** pertencem a Skills cuja relação oficial de alvo é `Enemy`; continuam pendentes porque efeitos secundários podem herdar o acerto do primeiro efeito, algo que o XML do cliente sozinho não comprova.",
        "",
        "### Caminho defensivo normal confirmado no código",
        "",
        "- Antes de aplicar um efeito não forçado, `EffectTemplate` testa evasão para elemento `NONE` e resistência mágica para efeitos elementais.",
        "- Dano físico comum desconta `PHYSICAL_DEFENSE / 10`; dano mágico elemental aplica defesa elemental e depois `MAGICAL_DEFEND / 10`.",
        "- Os ratios defensivos PvP/PvE e escudos são aplicados depois, salvo nos bypasses enumerados abaixo.",
        "- Portanto, Skills comuns não ignoram defesa globalmente. O risco está concentrado em efeitos/flags e hardcodes específicos.",
        "",
        "### Semântica dos motivos",
        "",
        "- `NORESIST_XML`: o template impede esquiva/resistência do efeito.",
        "- `NORESIST_FORCADO_JAVA`: `Effects` muda o efeito para `noresist` durante o carregamento, mesmo sem essa ordem no XML.",
        "- `DANO_FIXO_SEM_DEFESAS_BASE`: `NoReduceSpellATKInstantEffect` pula ataque, defesa física/mágica, defesa elemental e ratios ofensivos/defensivos; mantém apenas o modificador PvP geral.",
        "- `DANO_FIXO_HARDCODE_STACK`: o mesmo bypass é ativado por nome de stack hardcoded.",
        "- `IGNORA_ESCUDOS`: dano atrasado chama o cálculo com `ignoreShield=true`; defesa e resistência continuam em outros estágios.",
        "- `DANO_MAGICO_SEM_ELEMENTO_USA_DEFESA_FISICA_OU_NENHUMA`: combinação que exige revisão individual do tipo convertido.",
        "",
        "## Limites desta evidência",
        "",
        "O cliente prova flags e parâmetros estáticos, mas não toda a lógica exclusiva do servidor. Nenhum bypass foi removido automaticamente. O JSON contém cada Skill, efeito, posição, stack, flag do cliente e motivo técnico para validação por PCAP/teste.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "mensagens_invalidas": len(invalid),
        "mensagens_invalidas_usadas": len(invalid_used),
        "mensagens_invalidas_no_motor_skills": len(invalid_skill_engine),
        "factories_nome_divergente_usadas": len(mismatched_used),
        "bypasses": defense["contagem_por_motivo"],
        "noresist_contra_cliente_zero": len(defense["noresist_servidor_contra_cliente_zero"]),
        "noresist_hostil_contra_cliente_zero": len(defense["noresist_hostil_servidor_contra_cliente_zero"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
