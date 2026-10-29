"""Junta os dois arquivos de spawn do Balic Treasury (800070000) num só.

O 800070000 é mapa aberto (world_maps sem instance="true"), mas tinha spawn em dois arquivos:
  spawns/Npcs/800070000_Balic_Treasury.xml       (95 npcIds, 941 spots)
  spawns/Instances/800070000_Balic_Treasury.xml  (105 npcIds, 1052 spots; o mais completo, com os headings acertados em jogo)
O `<import file="spawns">` do static_data.xml carrega a pasta inteira e o SpawnsData.addRegularSpawns soma os grupos do
mesmo npc, então 815 spots nasciam em dobro.

Resultado: o arquivo de Instances (texto preservado) + os spots que só existiam no de Npcs (mesmo npc a mais de 1 m de
qualquer spot dele), gravado em spawns/Npcs/800070000_Balic_Treasury.xml; o de Instances é apagado. As duas árvores
(fonte e Produto Final) tinham os mesmos dois arquivos e recebem o mesmo resultado.

Uso:
    python fix_50_balic_spawns_junta.py            # mostra o que muda
    python fix_50_balic_spawns_junta.py --aplicar  # grava nas duas árvores
"""
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
BASES = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "spawns"),
         os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "spawns")]
NOME = "800070000_Balic_Treasury.xml"
RAIO = 1.0


def blocos(txt):
    """npc -> (match do <spawn>, [(x, y, tag do spot)])"""
    out = {}
    for m in re.finditer(r'(?s)(\t*)<spawn npc_id="(\d+)"[^>]*>.*?</spawn>', txt):
        spots = [(float(re.search(r'\bx="([-\d.]+)"', s).group(1)), float(re.search(r'\by="([-\d.]+)"', s).group(1)), s)
                 for s in re.findall(r"<spot\b[^>]*/>", m.group(0))]
        if int(m.group(2)) in out:
            sys.exit(f"npc {m.group(2)} repetido no mesmo arquivo")
        out[int(m.group(2))] = (m, spots)
    return out


def junta(inst, npcs):
    bi, bn = blocos(inst), blocos(npcs)
    novo, extra, novos_npcs = inst, 0, []
    # de trás para frente para os offsets do texto de Instances continuarem valendo
    for n, (m, spots) in sorted(bi.items(), key=lambda kv: -kv[1][0].start()):
        faltam = [tag for x, y, tag in bn.get(n, (None, []))[1] if all(math.hypot(x - a, y - b) > RAIO for a, b, _ in spots)]
        if not faltam:
            continue
        extra += len(faltam)
        fim = m.start() + m.group(0).rindex("</spawn>")
        ini = novo.rfind("\n", 0, fim)  # fim da linha do último spot; o </spawn> fica na linha seguinte
        ind = m.group(1) + "\t"
        novo = novo[:ini] + "".join(f"\n{ind}{t}" for t in faltam) + novo[ini:]
    for n in sorted(set(bn) - set(bi)):
        novos_npcs.append(n)
        extra += len(bn[n][1])
    if novos_npcs:
        add = "".join("\t\t" + bn[n][0].group(0).lstrip("\t") + "\n\n" for n in novos_npcs)
        i = novo.rindex("\n", 0, novo.rindex("</spawn_map>")) + 1  # começo da linha do </spawn_map>
        novo = novo[:i] + add + novo[i:]
    return novo, extra, novos_npcs


def main():
    from lxml import etree
    for base in BASES:
        ci, cn = os.path.join(base, "Instances", NOME), os.path.join(base, "Npcs", NOME)
        if not os.path.exists(ci):
            print("já junto:", base)
            continue
        inst = open(ci, encoding="utf-8", newline="").read()
        npcs = open(cn, encoding="utf-8", newline="").read()
        novo, extra, novos_npcs = junta(inst, npcs)
        etree.fromstring(novo.encode("utf-8"))
        bi, bf = blocos(inst), blocos(novo)
        n_spots = lambda b: sum(len(s) for _, s in b.values())
        print(f"{base}\n   Instances {len(bi)} npcs/{n_spots(bi)} spots + {extra} spots só do Npcs (npcs novos {novos_npcs})"
              f" -> {len(bf)} npcs/{n_spots(bf)} spots")
        if "--aplicar" in sys.argv:
            open(cn, "w", encoding="utf-8", newline="").write(novo)
            os.remove(ci)
            print("   gravado", cn, "e removido", ci)


if __name__ == "__main__":
    main()
