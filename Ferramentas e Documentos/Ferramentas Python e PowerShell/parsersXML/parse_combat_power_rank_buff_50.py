"""ranking/combat_power_rank_buff.xml: buff que se compra do 1º lugar do ranking de Combat Talent (ícone laranja), a partir do cliente 5.0.

Fonte: system/client_combat_power_rank_buff.xml (28 linhas). As cópias special/special2 têm preços menores (5.800/3.700); os
preços cobrados no oficial são os do system:
  captura 06_Sistemas_Novos 2026-10-20 02:17, aba 1002 (todos, servidor local): o Kinah caiu 11.500 (= buff_kina);
  captura 06_Sistemas_Novos 2026-10-20 02:23, aba 1003 (por classe, local): o Kinah caiu 7.300 (= buff_kina).
O buff aplicado foi o skill do combat_power_buff_skill (S 0x31 com 3914 = Ranking_Buff_L_G1 e 3923 = Ranking_Buff_L_G4_09).

job_type -> id de classe do PlayerClass (as do 5.0 no ranking por classe, RankingService.ORDERED_CLASSES).
basic_kina vai junto, mas o que ele mede não está provado (não é o preço).

Uso: python parse_combat_power_rank_buff_50.py [--dry]   (grava nas duas árvores)
"""
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS

DESTINOS = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data"),
]

CLASSES = {
    "all": 0,
    "fighter": 1,  # GLADIATOR
    "knight": 2,  # TEMPLAR
    "assassin": 4,
    "ranger": 5,
    "wizard": 7,  # SORCERER
    "elementalist": 8,  # SPIRIT_MASTER
    "priest": 10,  # CLERIC
    "chanter": 11,
    "thunderer": 13,  # REVENANT
    "battlemaster": 16,  # BRAWLER
    "lumines": 19,  # LUMINESS
    "gunner": 22,  # PHOENIX
    "runeblade": 25,  # SOUL_REAPER
}


def main():
    seco = "--dry" in sys.argv
    stacks = {}
    for m in re.finditer(r'<skill_template skill_id="(\d+)"[^>]*\sstack="([^"]+)"',
                         open(os.path.join(DESTINOS[0], "skills", "skill_templates.xml"), encoding="utf-8").read()):
        stacks.setdefault(m.group(2).upper(), int(m.group(1)))

    linhas = ['<?xml version="1.0" encoding="utf-8"?>',
              '<combat_power_rank_buffs xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="combat_power_rank_buff.xsd">']
    n = 0
    t = open(os.path.join(XMLS, "system", "client_combat_power_rank_buff.xml"), encoding="utf-8").read()
    for b in re.findall(r"<client_combat_power_rank_buff>(.*?)</client_combat_power_rank_buff>", t, re.S):
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        job = f["job_type"].lower()
        if job not in CLASSES:
            raise SystemExit("job_type sem mapa: %s" % job)
        skill = stacks.get(f["combat_power_buff_skill"].upper())
        if skill is None:
            raise SystemExit("skill sem template: %s" % f["combat_power_buff_skill"])
        linhas.append('\t<buff id="%s" rank_id="%s" class_id="%d" rank="%s" price="%s" skill_id="%d" basic_kina="%s" /><!-- %s -->' % (
            f["id"], f["rank_id"], CLASSES[job], f["rank"], f["buff_kina"], skill, f["basic_kina"], f["combat_power_buff_skill"]))
        n += 1
    linhas.append("</combat_power_rank_buffs>")
    texto = "\n".join(linhas) + "\n"
    print("buffs:", n)
    if seco:
        print(texto)
        return
    for d in DESTINOS:
        os.makedirs(os.path.join(d, "ranking"), exist_ok=True)
        with open(os.path.join(d, "ranking", "combat_power_rank_buff.xml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print("gravado", os.path.join(d, "ranking", "combat_power_rank_buff.xml"))


if __name__ == "__main__":
    main()
