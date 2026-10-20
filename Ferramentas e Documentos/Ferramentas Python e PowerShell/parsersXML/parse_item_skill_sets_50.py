"""items/item_skill_sets.xml: skill de equipamento (tooltip "Assign Skill on Loot", diálogo Reassign) a partir do cliente 5.0.

Fontes:
  client_items.xml                    <skill_set_name> do item, <quality>, <equipment_slots>
  client_item_skill_enchant.xml       conjunto -> <skill_name> + <skill_prob> por mil (soma 1000)
  client_item_skill_enchant_cost.xml  quality + equipment_slots -> item_add_skill_cost (tipo 0 = Quna, 60 em todos os épicos).
                                      O special/ (tipo 1, 386000) é de outra região e não é usado.

Na captura oficial de 2026-10-18 13:42, a skill sorteada vai no D do offset 60 do bloco 0x0B do item. O C 0x107 gasta os 60 Quna do custo
(S 0x11B com H 0x15C). Nas capturas, 130 de 130 itens com skill tinham uma skill do conjunto do próprio item.

Skill que o cliente não tem (classic_wind_shoulderflyspeed_phy_shoulder_g1/g2) ou que falta no skill_templates do servidor fica de
fora, com aviso. Ela não entra no sorteio, que usa só o peso das que restam.

Uso: python parse_item_skill_sets_50.py [--dry]   (grava nas duas árvores)
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS

DESTINOS = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data"),
]


# equipment_slots do item -> o da tabela de custo (o cliente usa nomes diferentes nas duas)
SLOT_CUSTO = {"glove": "hand", "main_or_sub": "weapon", "main": "weapon", "sub": "weapon"}


def campos(bloco):
    return dict(re.findall(r"<(\w+)>([^<]*)</\1>", bloco))


def main():
    seco = "--dry" in sys.argv
    skills = {}
    for b in open(os.path.join(XMLS, "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read().split("<skill_base_client>")[1:]:
        f = campos(b)
        skills[f["name"].lower()] = int(f["id"])
    servidor = set(int(x) for x in re.findall(r'<skill_template skill_id="(\d+)"',
                                                open(os.path.join(DESTINOS[0], "skills", "skill_templates.xml"), encoding="utf-8").read()))

    custo = {}
    for m in re.finditer(r"<quality>(\w+)</quality>\s*<equipment_slots>(\w+)</equipment_slots>\s*<item_add_skill_cost_type>(\d+)</item_add_skill_cost_type>"
                         r"\s*<item_add_skill_cost>(\d+)</item_add_skill_cost>",
                         open(os.path.join(XMLS, "items", "client_item_skill_enchant_cost.xml"), encoding="utf-8").read()):
        if m.group(3) != "0":
            raise SystemExit("custo de tipo %s sem prova (só o 0 = Quna está nas capturas)" % m.group(3))
        custo[(m.group(1).lower(), m.group(2).lower())] = int(m.group(4))

    conjuntos = collections.OrderedDict()
    avisos = []
    t = open(os.path.join(XMLS, "items", "client_item_skill_enchant.xml"), encoding="utf-8").read()
    for b in re.findall(r"<client_item_skill_enchant>(.*?)</client_item_skill_enchant>", t, re.S):
        nome = re.search(r"<name>([^<]+)</name>", b).group(1)
        lista = []
        for s, p in re.findall(r"<skill_name>([^<]+)</skill_name>\s*<skill_prob>(\d+)</skill_prob>", b):
            sid = skills.get(s.lower())
            if sid is None or sid not in servidor:
                avisos.append("%s: %s %s" % (nome, s, "não está no cliente" if sid is None else "sem template no servidor"))
                continue
            lista.append((sid, int(p)))
        conjuntos[nome.lower()] = (nome, lista, [], set())

    for b in open(os.path.join(XMLS, "items", "client_items.xml"), encoding="utf-8", errors="replace").read().split("<client_item>")[1:]:
        f = campos(b)
        nome = f.get("skill_set_name", "").lower()
        if not nome:
            continue
        if nome not in conjuntos:
            avisos.append("item %s: conjunto %s não existe" % (f["id"], nome))
            continue
        slot = f.get("equipment_slots", "").lower()
        chave = (f.get("quality", "").lower(), SLOT_CUSTO.get(slot, slot))
        if chave not in custo:
            avisos.append("item %s: sem custo para %s" % (f["id"], chave))
            continue
        conjuntos[nome][2].append(int(f["id"]))
        conjuntos[nome][3].add(custo[chave])

    linhas = ['<?xml version="1.0" encoding="utf-8"?>',
              '<item_skill_sets xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="item_skill_sets.xsd">']
    n_itens = 0
    for nome, lista, itens, custos in conjuntos.values():
        if not itens or not lista:
            continue
        if len(custos) != 1:
            raise SystemExit("%s: custos diferentes entre os itens %s" % (nome, sorted(custos)))
        n_itens += len(itens)
        linhas.append('\t<skill_set name="%s" quna="%d">' % (nome, custos.pop()))
        linhas.append("\t\t<items>%s</items>" % " ".join(str(i) for i in sorted(itens)))
        for sid, p in lista:
            linhas.append('\t\t<skill id="%d" prob="%d" />' % (sid, p))
        linhas.append("\t</skill_set>")
    linhas.append("</item_skill_sets>")
    texto = "\n".join(linhas) + "\n"

    print("conjuntos com itens:", sum(1 for c in conjuntos.values() if c[2] and c[1]), "itens:", n_itens)
    for a in avisos:
        print("aviso:", a)
    if seco:
        return
    for d in DESTINOS:
        with open(os.path.join(d, "items", "item_skill_sets.xml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print("gravado", os.path.join(d, "items", "item_skill_sets.xml"))


if __name__ == "__main__":
    main()
