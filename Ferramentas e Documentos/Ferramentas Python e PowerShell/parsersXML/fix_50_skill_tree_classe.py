"""Tira do skill_tree.xml as entradas de skill que o client_skill_learns 5.0 não dá para aquela classe.

Em 18/10/2026, as skills do Gladiador (FI_*) estavam copiadas em classId="TEMPLAR" e em classId="WARRIOR". Eram 257 skills
(1.453 entradas) no Templar e 341 (1.980) no Warrior. O Templar aprende a árvore dele e a da classe inicial (WARRIOR), então a
janela K mostrava skills do Gladiador que a lista de skills do cliente não tem. Nenhuma outra classe tinha entradas fora dela.

Uma entrada fica quando o cliente ensina a skill (pelo nome) para a própria classe, para a classe inicial dela ou para ALL. Antes
de remover, conferido que nenhuma skill que fica faltando na especialização é perdida: as 8 passivas compartilhadas
(P_StatBoost*, P_BoostHate) que saem de WARRIOR já estão no TEMPLAR, nos níveis do KNIGHT do cliente. As de WARRIOR usavam os
níveis do FIGHTER.

Idempotente. Uso: python fix_50_skill_tree_classe.py [--dry] [skill_tree.xml ...]   (padrão: o do Código Fonte)
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS

TREE = os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "skill_tree", "skill_tree.xml")

# classId do servidor -> classes do client_skill_learns (especialização + classe inicial)
CLASSES = {
    "WARRIOR": {"WARRIOR"}, "GLADIATOR": {"FIGHTER", "WARRIOR"}, "TEMPLAR": {"KNIGHT", "WARRIOR"},
    "SCOUT": {"SCOUT"}, "ASSASSIN": {"ASSASSIN", "SCOUT"}, "RANGER": {"RANGER", "SCOUT"},
    "MAGE": {"MAGE"}, "SORCERER": {"WIZARD", "MAGE"}, "SPIRIT_MASTER": {"ELEMENTALLIST", "MAGE"},
    "PRIEST": {"PRIEST"}, "CLERIC": {"CLERIC", "PRIEST"}, "CHANTER": {"CHANTER", "PRIEST"},
    "MONK": {"MONK"}, "THUNDERER": {"THUNDERER", "MONK"}, "REVENANT": {"THUNDERER", "MONK"},
    "BRAWLER": {"STRIKER", "BATTLEMASTER"}, "LUMINESS": {"LUMINES"}, "PHOENIX": {"GUNNER"},
    "SOUL_REAPER": {"RUNEBLADE"}, "BARD": {"BARD"},
}


def classes_do_cliente():
    t = open(os.path.join(XMLS, "skills", "client_skill_learns.xml"), encoding="utf-8", errors="replace").read()
    cli = collections.defaultdict(set)
    for b in re.findall(r"<client_skill_learn>(.*?)</client_skill_learn>", t, re.S):
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        if "skill" in f:
            cli[f["skill"].lower()].add(f.get("class", "").upper())
    return cli


def aplica(caminho, cli, seco):
    raw = open(caminho, encoding="utf-8", newline="").read()
    contagem = collections.Counter()

    def edita(m):
        nome = re.search(r'\bname="([^"]+)"', m.group(2))
        classe = re.search(r'\bclassId="([A-Z_]+)"', m.group(2))
        if not nome or not classe or classe.group(1) not in CLASSES:
            return m.group(0)
        if cli.get(nome.group(1).lower(), set()) & (CLASSES[classe.group(1)] | {"ALL"}):
            return m.group(0)
        contagem[classe.group(1)] += 1
        return ""

    novo = re.sub(r"(?m)^([ \t]*)<skill (\b[^>]*)/>[ \t]*\r?\n", edita, raw)
    print(caminho, "removidas:", dict(contagem) or "nada a mudar")
    if novo != raw and not seco:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or [TREE]
    cli = classes_do_cliente()
    for caminho in caminhos:
        aplica(caminho, cli, seco)


if __name__ == "__main__":
    main()
