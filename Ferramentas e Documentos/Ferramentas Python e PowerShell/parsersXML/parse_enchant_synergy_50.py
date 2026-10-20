"""items/enchant_synergy.xml: sinergia de encantamento ("Current Synergy Level") a partir do cliente 5.0.

Fontes:
  client_accumulated_enchant_effect.xml  105 níveis: enchant_sum, enchant_attr1..11 e activation_skill (60+)
  client_items.xml                       <accumulated_enchant_effect>TRUE (4.961 itens)

Strings do cliente:
  STR_EQUIP_ENCHANT_BONUS_ALL "nível atual de sinergia: %0" (o cliente calcula e mostra);
  STR_EQUIP_ENCHANT_BONUS_CONDITION_DESC: grau Único ou acima, item com efeito de sinergia, ao menos um equipado.
O nível é a soma dos encantamentos dos itens equipados com o flag; vale o maior nível com enchant_sum <= soma.

Atributos. Pelos nomes das skills Enchant_Effect_* do cliente, Stun/Silence/Paralyze/BlindDuration e ProcDamageReduce valem para
Godstone ("Reduces the duration of Godstone stuns", "Godstone Elemental Damage -50%"). Os ratios são por mil, como no
StatFunctions.

Uso: python parse_enchant_synergy_50.py [--dry]   (grava nas duas árvores)
"""
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS

DESTINOS = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data"),
]

STATS = {
    "maxhp": "MAXHP",
    "pveattackratio": "PVE_ATTACK_RATIO",
    "pvedefendratio": "PVE_DEFEND_RATIO",
    "pvpattackratio": "PVP_ATTACK_RATIO",
    "pvpdefendratio": "PVP_DEFEND_RATIO",
    "pveattackratio_bosstarget": "PVE_ATTACK_RATIO_BOSS",
    "procdamagereduce": "PROC_DAMAGE_REDUCE",
    "stunduration": "PROC_STUN_DURATION",
    "silenceduration": "PROC_SILENCE_DURATION",
    "paralyzeduration": "PROC_PARALYZE_DURATION",
    "blindduration": "PROC_BLIND_DURATION",
}


def main():
    seco = "--dry" in sys.argv
    skills = {}
    for b in open(os.path.join(XMLS, "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read().split("<skill_base_client>")[1:]:
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        skills[f["name"].lower()] = int(f["id"])
    servidor = set(int(x) for x in re.findall(r'<skill_template skill_id="(\d+)"',
                                                open(os.path.join(DESTINOS[0], "skills", "skill_templates.xml"), encoding="utf-8").read()))

    niveis = []
    t = open(os.path.join(XMLS, "items", "client_accumulated_enchant_effect.xml"), encoding="utf-8").read()
    for b in re.findall(r"<client_accumulated_enchant_effect>(.*?)</client_accumulated_enchant_effect>", t, re.S):
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        attrs = []
        for k in sorted((k for k in f if k.startswith("enchant_attr")), key=lambda k: int(k[12:])):
            m = re.fullmatch(r"\s*(\w+)\s+([+-]?\d+)%?\s*", f[k])
            if not m or m.group(1).lower() not in STATS:
                raise SystemExit("atributo sem mapa no nível %s: %r" % (f["enchant_sum"], f[k]))
            attrs.append((STATS[m.group(1).lower()], int(m.group(2))))
        skill = None
        if f.get("activation_skill"):
            skill = skills.get(f["activation_skill"].lower())
            if skill is None or skill not in servidor:
                raise SystemExit("skill de ativação sem template: %s" % f["activation_skill"])
        niveis.append((int(f["enchant_sum"]), attrs, skill))

    itens = []
    for b in open(os.path.join(XMLS, "items", "client_items.xml"), encoding="utf-8", errors="replace").read().split("<client_item>")[1:]:
        if "<accumulated_enchant_effect>TRUE</accumulated_enchant_effect>" in b:
            itens.append(int(re.search(r"<id>(\d+)</id>", b).group(1)))

    linhas = ['<?xml version="1.0" encoding="utf-8"?>',
              '<enchant_synergy xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="enchant_synergy.xsd">',
              "\t<items>%s</items>" % " ".join(str(i) for i in sorted(itens))]
    for soma, attrs, skill in sorted(niveis):
        linhas.append('\t<level sum="%d"%s>' % (soma, ' skill_id="%d"' % skill if skill else ""))
        linhas.append("\t\t<modifiers>")
        for nome, valor in attrs:
            linhas.append('\t\t\t<add name="%s" value="%d" bonus="true" />' % (nome, valor))
        linhas.append("\t\t</modifiers>")
        linhas.append("\t</level>")
    linhas.append("</enchant_synergy>")
    texto = "\n".join(linhas) + "\n"
    print("níveis:", len(niveis), "itens:", len(itens), "com skill:", sum(1 for n in niveis if n[2]))
    if seco:
        return
    for d in DESTINOS:
        with open(os.path.join(d, "items", "enchant_synergy.xml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print("gravado", os.path.join(d, "items", "enchant_synergy.xml"))


if __name__ == "__main__":
    main()
