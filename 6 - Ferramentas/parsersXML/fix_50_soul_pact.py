"""Soul Pact do Soul Reaper (RB_SoulRemnant_G1/G2) no skill_templates.xml, a partir do client_skills 5.0.

O gerador 4.x tinha deixado <rebirth resurrect_percent skill_id=9653 effectid=160> nas duas graduações. No emulador isso é a
autorressurreição do menu de morte, não o pacto. O Soul Rest I (9653) era só resistência elemental e o II (9654) um stub.

Cliente 5.0:
  RB_SoulRemnant_G1/G2          DeathTriggerBuff  remain2 = 240000, reserved1 = skill do Soul Rest, reserved3 = % do HP (100 / 150)
  RB_SoulRemnant_G1/G2_Effect   DeathTrialState   reserved2 = % do HP máximo por tick (7), reserved3 = intervalo (1000 ms),
                                                  reserved6 = skill do fim (RB_SoulRemnant_G1_Heal, cura de 100%)
                                StatUp e2         arAll +3000 (resistência a todos os estados anormais), 120000 ms

O script, idempotente (rodar de novo não muda nada):
  1. troca o <effects> das skills com DeathTriggerBuff por <deathtriggerbuff value skill_id>
  2. escreve o Soul Rest que elas apontam com <deathtrialstate value checktime skill_id> e o <statup> de arAll, tslot BUFF
  3. acerta name/nameId pelo client_strings_skill (4435 e 4437 estavam sem nameId)

Uso: python fix_50_soul_pact.py [--dry]
"""
import os
import re
import sys
from xml.sax.saxutils import escape

from fix_50_energia_sp_ep import ELEMENTOS, TEMPLATES, XMLS, Template, le_cliente, pre_efeito

STRINGS = os.path.join(os.path.dirname(XMLS), "Strings", "strings", "client_strings_skill.xml")
# arAll: CreatureGameStats#getAbnormalResistance lê ABNORMAL_RESISTANCE_ALL
STAT_TOKEN = {"arall": "ABNORMAL_RESISTANCE_ALL"}
PROPS_ME = '<properties first_target="ME" target_type="ONLYONE" />'


def le_strings():
    raw = open(STRINGS, "rb").read()
    texto = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", errors="replace")
    return {m.group(2).lower(): (int(m.group(1)), m.group(3))
            for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>\s*<body>([^<]*)</body>", texto)}


def elemento(c, n):
    e = ELEMENTOS.get(c.get("effect%d_reserved10" % n, "").lower())
    return ' element="%s"' % e if e else ""


def linhas_trigger(c, ids):
    return ['<deathtriggerbuff value="%s" skill_id="%d" duration2="%s" effectid="%s" basiclvl="%s" e="1" noresist="true"%s />' % (
        c.get("effect1_reserved3", "100"), ids[c["effect1_reserved1"].lower()], c.get("effect1_remain2", "0"),
        c.get("effect1_effectid", "0"), c.get("effect1_basiclv", "0"), elemento(c, 1))]


def linhas_trial(c, ids):
    linhas = ['<deathtrialstate value="%s" checktime="%s" skill_id="%d" duration2="%s" effectid="%s" basiclvl="%s" e="1" noresist="true"%s />' % (
        c.get("effect1_reserved2", "0"), c.get("effect1_reserved3", "1000"), ids.get(c.get("effect1_reserved6", "").lower(), 0),
        c.get("effect1_remain2", "0"), c.get("effect1_effectid", "0"), c.get("effect1_basiclv", "0"), elemento(c, 1))]
    if c.get("effect2_type", "").lower() == "statup":
        token = c.get("effect2_reserved13", "")
        stat = STAT_TOKEN.get(token.lower())
        if stat is None:
            raise SystemExit("token de stat sem StatEnum conhecido no Soul Rest %s: %s" % (c.get("id"), token))
        linhas += ['<statup duration2="%s" effectid="%s" basiclvl="%s" e="2" noresist="true"%s%s>' % (
                       c.get("effect2_remain2", "0"), c.get("effect2_effectid", "0"), c.get("effect2_basiclv", "0"), pre_efeito(c, 2), elemento(c, 2)),
                   '\t<change stat="%s" func="%s" value="%s" />' % (stat, "PERCENT" if c.get("effect2_reserved6") == "1" else "ADD", c.get("effect2_reserved2", "0")),
                   '</statup>']
    return linhas


def filhos(corpo, nome):
    m = re.search(r"<%s>(.*?)</%s>" % (nome, nome), corpo, re.S)
    return re.findall(r"<[^<>]+/>", m.group(1)) if m else []


def monta(cabeca, props, corpo_antigo, efeitos, eol):
    partes = [eol, "\t\t", props, eol]
    for nome, linhas in (("startconditions", filhos(corpo_antigo, "startconditions")), ("useconditions", filhos(corpo_antigo, "useconditions")),
                         ("effects", efeitos), ("actions", filhos(corpo_antigo, "actions"))):
        if linhas:
            partes.append("\t\t<%s>%s" % (nome, eol) + "".join("\t\t\t" + x + eol for x in linhas) + "\t\t</%s>%s" % (nome, eol))
    return cabeca + "".join(partes) + "\t"


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    ids = {d["name"].lower(): i for i, d in cli.items()}
    strings = le_strings()
    alvos = {}
    for i, c in cli.items():
        if c.get("effect1_type", "").lower() == "deathtriggerbuff":
            alvos[i] = "trigger"
            estado = ids.get(c.get("effect1_reserved1", "").lower())
            if estado:
                alvos[estado] = "trial"

    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    mudou = []

    def edita(m):
        sid = int(m.group(2))
        tipo = alvos.get(sid)
        if tipo is None:
            return m.group(0)
        c = cli[sid]
        tp = Template(m.group(1), "", eol)
        nome = strings.get(c.get("desc", "").lower())
        if nome:
            tp.attr("name", escape(nome[1]))
            tp.attr("nameId", str(nome[0]))
        tp.attr("tslot", "BUFF")
        tp.attr("duration", str(int(c.get("casting_delay") or 0)))  # duration do template é o tempo de cast, não a duração do buff
        if tipo == "trigger":
            props = re.search(r"<properties\b[^>]*/>", m.group(3))
            novo = monta(tp.cabeca, props.group(0) if props else PROPS_ME, m.group(3), linhas_trigger(c, ids), eol)
        else:
            tp.attr("skillsubtype", "BUFF")
            if c.get("target_slot_level"):
                tp.attr("tslot_level", c["target_slot_level"])
            if c.get("dispel_category", "").lower() == "buff":
                tp.attr("dispel_category", "BUFF")
            if c.get("required_dispel_level"):
                tp.attr("req_dispel_level", c["required_dispel_level"])
            if c.get("no_save_on_logout") == "1":
                tp.attr("no_save_on_logout", "true")
            novo = monta(tp.cabeca, PROPS_ME, m.group(3), linhas_trial(c, ids), eol)
        novo += m.group(4)
        if novo != m.group(0):
            mudou.append(sid)
        return novo

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    print("alvos:", sorted(alvos.items()))
    print("mudaram:", mudou)
    if novo == raw:
        print("nada a mudar")
        return
    if seco:
        print("--dry: nada gravado")
        return
    with open(TEMPLATES, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print("gravado", TEMPLATES)


if __name__ == "__main__":
    main()
