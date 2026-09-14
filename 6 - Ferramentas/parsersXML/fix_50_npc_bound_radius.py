"""Corrige o bound_radius do npc_templates.xml a partir do client_npcs 5.0.

O emulador guarda front e side como raio do cliente × scale / 200 (33.480 NPCs batem). Os que divergem trazem valor velho ou o scale
aplicado duas vezes (201062: 0,72 onde o cliente dá 0,30), e o dash e o flash do jogador param no lugar errado neles.

5.0 oficial (subida 1-60 e combate do Brawler, 33 NPCs): o dash para a max(front, side) do alvo + 1,25 m, com o raio do cliente × scale / 200.

O upper segue a regra que mais bate nos NPCs em que front e side já estão certos. Só os divergentes mudam; rodar de novo não muda nada.

Uso: python fix_50_npc_bound_radius.py [--dry]
"""
import collections
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
CLIENT_NPCS = r"G:\Projetos AION\XMLS AION CLASSIC\data\npcs\client_npcs.xml"
TEMPLATES = os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data", "npcs", "npc_templates.xml")
TOLERANCIA = 0.011


def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def le_cliente():
    cli = {}
    for b in open(CLIENT_NPCS, encoding="utf-8", errors="replace").read().split("<npc_client>")[1:]:
        m = re.search(r"<id>(\d+)</id>", b)
        br = re.search(r"<bound_radius>\s*<front>([\d.]+)</front>\s*<side>([\d.]+)</side>\s*<upper>([\d.]+)</upper>", b)
        sc = re.search(r"<scale>(\d+)</scale>", b)
        if m and br:
            cli[int(m.group(1))] = (float(br.group(1)), float(br.group(2)), float(br.group(3)), int(sc.group(1)) if sc else 100)
    return cli


REGRAS_UPPER = {"upper*scale/100": lambda u, sc: u * sc / 100, "upper*scale/200": lambda u, sc: u * sc / 200, "upper": lambda u, sc: u}


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    padrao = re.compile(r'(<npc_template[^>]*\bnpc_id="(\d+)"[^>]*>(?:(?!</npc_template>).)*?)(<bound_radius front="([\d.]+)" side="([\d.]+)"(?: upper="([\d.]+)")? />)', re.S)

    # upper: aprende nos que já estão certos em front e side
    votos = collections.Counter()
    for m in padrao.finditer(raw):
        i = int(m.group(2))
        if i not in cli or m.group(6) is None:
            continue
        f, s, u, sc = cli[i]
        if abs(float(m.group(4)) - f * sc / 200) < TOLERANCIA and abs(float(m.group(5)) - s * sc / 200) < TOLERANCIA:
            for nome, regra in REGRAS_UPPER.items():
                if abs(float(m.group(6)) - regra(u, sc)) < TOLERANCIA:
                    votos[nome] += 1
    regra_upper = votos.most_common(1)[0][0] if votos else "upper*scale/100"
    print("upper:", dict(votos), "->", regra_upper)

    contagem = collections.Counter()
    exemplos = []

    def troca(m):
        i = int(m.group(2))
        if i not in cli:
            return m.group(0)
        f, s, u, sc = cli[i]
        certo_f, certo_s = f * sc / 200, s * sc / 200
        if abs(float(m.group(4)) - certo_f) < TOLERANCIA and abs(float(m.group(5)) - certo_s) < TOLERANCIA:
            contagem["ja certo"] += 1
            return m.group(0)
        upper = REGRAS_UPPER[regra_upper](u, sc)
        novo = '<bound_radius front="%s" side="%s" upper="%s" />' % (num(certo_f), num(certo_s), num(upper))
        contagem["corrigido"] += 1
        if len(exemplos) < 12:
            exemplos.append((i, m.group(3), novo))
        return m.group(1) + novo

    novo_raw = padrao.sub(troca, raw)
    print(dict(contagem))
    for e in exemplos:
        print("  ", e)
    if novo_raw == raw:
        print("nada a mudar")
        return
    if seco:
        print("--dry: nada gravado")
        return
    with open(TEMPLATES, "w", encoding="utf-8", newline="") as f:
        f.write(novo_raw)
    print("gravado", TEMPLATES)


if __name__ == "__main__":
    main()
