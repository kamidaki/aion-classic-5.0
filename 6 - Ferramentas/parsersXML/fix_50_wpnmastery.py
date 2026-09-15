"""<wpnmastery> sem weapon no skill_templates.xml, preenchido pelo reserved5 do client_skills 5.0.

Sem weapon o WeaponMasteryEffect estoura NullPointerException ao aplicar a passiva. Em 2026-09-14 isso impediu a Peipei de entrar no jogo,
quando o login passou a ensinar as skills automáticas que faltavam. Os 11 casos eram das armas das classes novas: Gun (3997-4001), Gauntlet
(2728, 4239, 4520), RuneSword (4401, 4490) e DimensionSword (3220).

Gabarito (90 templates com weapon): reserved5 sem o prefixo 1h_/2h_ é o ItemGroup, com três exceções que o próprio gabarito traz
(2h_Sword = GREATSWORD, 2h_Blade = CHAINBLADE, 2h_Book = SPELLBOOK). Token sem ItemGroup aborta o script sem gravar nada.

Uso: python fix_50_wpnmastery.py [--dry]
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

ITEM_GROUP_JAVA = os.path.join(os.path.dirname(TEMPLATES), "..", "..", "..", "src", "com", "aionemu", "gameserver", "model", "templates", "item",
                               "enums", "ItemGroup.java")


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    grupos = set(re.findall(r"^\s*([A-Z_0-9]+)\(", open(ITEM_GROUP_JAVA, encoding="utf-8").read(), re.M))
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()

    def token(sid, n):
        return (cli.get(sid, {}).get("effect%d_reserved5" % n) or "").lower()

    gabarito = collections.defaultdict(collections.Counter)
    for m in re.finditer(r'<skill_template skill_id="(\d+)".*?</skill_template>', raw, re.S):
        for tag in re.findall(r"<wpnmastery\b[^>]*>", m.group(0)):
            w = re.search(r'\bweapon="([^"]*)"', tag)
            e = re.search(r'\be="(\d+)"', tag)
            if w and token(int(m.group(1)), int(e.group(1)) if e else 1):
                gabarito[token(int(m.group(1)), int(e.group(1)) if e else 1)][w.group(1)] += 1
    mapa = {k: v.most_common(1)[0][0] for k, v in gabarito.items()}

    mudou, sem_grupo = [], []

    def edita(m):
        sid = int(m.group(1))
        bloco = m.group(0)
        for tag in re.findall(r"<wpnmastery\b[^>]*>", bloco):
            if re.search(r'\bweapon="', tag):
                continue
            e = re.search(r'\be="(\d+)"', tag)
            tok = token(sid, int(e.group(1)) if e else 1)
            grupo = mapa.get(tok) or re.sub(r"^[12]h_", "", tok).upper()
            if grupo not in grupos:
                sem_grupo.append((sid, tok))
                continue
            bloco = bloco.replace(tag, tag.replace("<wpnmastery ", '<wpnmastery weapon="%s" ' % grupo, 1), 1)
            mudou.append((sid, cli.get(sid, {}).get("name"), tok, grupo))
        return bloco

    novo = re.sub(r'<skill_template skill_id="(\d+)".*?</skill_template>', edita, raw, flags=re.S)
    for x in mudou:
        print("%5d %-30s %-20s -> %s" % x)
    if sem_grupo:
        raise SystemExit("reserved5 sem ItemGroup, nada gravado: %s" % sem_grupo)
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
