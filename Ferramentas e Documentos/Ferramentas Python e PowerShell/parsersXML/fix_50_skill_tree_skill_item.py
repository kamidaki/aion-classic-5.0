"""Tira do skill_tree.xml as skills de equipamento (Reassign), que o generate_skill_tree_50.py gravava como estigma.

No client_skill_learns 5.0, learntype=1 só aparece em 702 regras, todas classe ALL, nível 1 e stigma_display 0: são as skills
que a armadura dá (client_item_skill_enchant / item_skill_sets.xml), não estigmas. O gerador lia learntype=1 como estigma e
gravava stigma="true". O PlayerSkillEntry então marcava a skill como estigma (tipo 1) no S 0x2C, e o cliente a mostrava na aba
de estigma. Na captura oficial de 2026-10-18 13:42 o 0x2C da skill 10938 vem com tipo 0 e flag 0.

A skill é do item: o ItemSkillService a dá ao equipar e tira ao desequipar, então ela não tem lugar na árvore. Sai toda
entrada cujo nome é de uma regra learntype=1 do cliente.

Idempotente. Uso: python fix_50_skill_tree_skill_item.py [--dry] [skill_tree.xml ...]   (padrão: Código Fonte e Produto Final)
"""
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS

TREES = [os.path.join(RAIZ, pasta, "data", "static_data", "skill_tree", "skill_tree.xml")
         for pasta in (os.path.join("Código Fonte - Emulador", "game-server"), os.path.join("Emulador - Produto Final", "GameServer"))]


def skills_de_item():
    t = open(os.path.join(XMLS, "skills", "client_skill_learns.xml"), encoding="utf-8", errors="replace").read()
    nomes = set()
    for b in re.findall(r"<client_skill_learn>(.*?)</client_skill_learn>", t, re.S):
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        if f.get("learntype") == "1" and "skill" in f:
            nomes.add(f["skill"].lower())
    return nomes


def aplica(caminho, nomes, seco):
    raw = open(caminho, encoding="utf-8", newline="").read()
    removidas = []

    def edita(m):
        nome = re.search(r'\bname="([^"]+)"', m.group(2))
        if not nome or nome.group(1).lower() not in nomes:
            return m.group(0)
        removidas.append(m.group(2))
        return ""

    novo = re.sub(r"(?m)^([ \t]*)<skill (\b[^>]*)/>[ \t]*\r?\n", edita, raw)
    fora_do_padrao = [r for r in removidas if 'classId="ALL"' not in r or 'stigma="true"' not in r]
    print(caminho, "removidas:", len(removidas), "| fora de ALL/stigma:", len(fora_do_padrao))
    if novo != raw and not seco:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or TREES
    nomes = skills_de_item()
    print("regras learntype=1 no cliente:", len(nomes))
    for caminho in caminhos:
        aplica(caminho, nomes, seco)


if __name__ == "__main__":
    main()
