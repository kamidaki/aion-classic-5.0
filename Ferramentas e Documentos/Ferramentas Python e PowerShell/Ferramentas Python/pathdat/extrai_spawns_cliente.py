"""Extrai os spawns dos mapas do cliente 5.0 (levels/<mapa>/mission_mission0.xml, objetos Type="SP" e "HSP").

Uso: extrai_spawns_cliente.py <saida> [--cliente <Client 5.0 - Dados Extraidos>] [--mapas 220070000,800040000]

Por ponto SP (NPC/mob) ou HSP (coleta): npc (nome no client_npcs.xml / gather_src.xml); SP com npc vazio e SeedPoint ficam de fora, Pos, Angles, Ignore_heightcheck, iidle_range.
  - mapa: WorldId.xml (id -> nome do level);
  - z: com Ignore_heightcheck=0 (112.661 de 112.662 pontos do cliente) o jogo cola o spawn no chão: z = piso livre da grade
    (path.dat) mais perto do z do editor, na célula ou nas 8 vizinhas (borda). Tipos que o oficial põe no ar
    (oficial_altura_por_npc.pkl, mediana > 1 m acima do piso) mantêm o z do editor;
  - h: floor((Angles z + 0,5) / 3) - 30, em 120 passos (95,8% exato contra o S_PUT_NPC oficial);
  - random_walk: iidle_range > 0;
  - respawn_time: o do spawn atual do servidor para o mesmo NPC no mesmo mapa (o cliente não tem; medir nas capturas),
    senão 295.
Saída: <saida>/Npcs/<mapa>_<level>.xml e <saida>/Gather/<mapa>_<level>.xml, no formato de data/static_data/spawns.
"""
import argparse, collections, glob, math, os, pickle, re, sys
from xml.etree import ElementTree as ET

from pathdat_50 import PathDat, RAIZ

AQUI = os.path.dirname(os.path.abspath(__file__))
CLIENTE = os.path.normpath(os.path.join(RAIZ, "../../../Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos"))
SPAWNS_SERVIDOR = os.path.join(RAIZ, "static_data/spawns")


def nomes_para_id(arq, tag):
    """nome (minúsculo) -> id, primeira ocorrência, como o cliente resolve."""
    out = {}
    for _, el in ET.iterparse(arq, events=("end",)):
        if el.tag == tag:
            n, i = el.findtext("name"), el.findtext("id")
            if n and i:
                out.setdefault(n.strip().lower(), int(i))
            el.clear()
    return out


def heading(angles):
    """Angles "x,y,z" (graus) -> h do servidor (0-119): floor((z + 0,5) / 3) - 30.
    Conferido contra o S_PUT_NPC (byte 27) de 1.885 NPCs parados no ponto (Tiamaranta Mesa e Gelkmaros): 95,8% exato e só 4 com
    +-1; o resto (giraram depois de andar/lutar, ou ângulo padrão 89,999992) erra 20-60. A conta do SpawnParser (trunca) acertava 76%."""
    try:
        v = float(angles.split(",")[2])
    except (AttributeError, IndexError, ValueError):
        return 0
    return (math.floor((v + 0.5) / 3) - 30) % 120


def respawns_atuais():
    """(mapa, npc) -> respawn_time dos spawns atuais do servidor."""
    out = {}
    for f in glob.glob(os.path.join(SPAWNS_SERVIDOR, "**", "*.xml"), recursive=True):
        x = re.sub(r"(?s)<!--.*?-->", "", open(f, encoding="utf-8").read())
        for mapa, corpo in re.findall(r'(?s)<spawn_map\b[^>]*map_id="(\d+)"[^>]*>(.*?)</spawn_map>', x):
            for tag in re.findall(r"<spawn\b[^>]*>", corpo):
                n, r = re.search(r'npc_id="(\d+)"', tag), re.search(r'respawn_time="(\d+)"', tag)
                if n and r:
                    out.setdefault((int(mapa), int(n.group(1))), int(r.group(1)))
    return out


def piso(M, x, y, z):
    """Piso livre mais perto de z na célula; sem piso na célula, nas 8 vizinhas. (z, caso)"""
    if M is None or not (0 <= x < M.tam and 0 <= y < M.tam):
        return None, "sem grade"
    fl = [p[0] for p in M.pisos(x, y) if p[1] and not math.isnan(p[0])]
    caso = "célula"
    if not fl:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                fl += [p[0] for p in M.pisos(x + dx * 0.5, y + dy * 0.5) if p[1] and not math.isnan(p[0])]
        caso = "borda"
    if not fl:
        return None, "sem piso"
    return min(fl, key=lambda q: abs(q - z)), caso


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def extrai(cliente, mapas_filtro=None, log=print):
    npcs = nomes_para_id(os.path.join(cliente, "data/npcs/client_npcs.xml"), "npc_client")
    gathers = nomes_para_id(os.path.join(cliente, "data/Gather/gather_src.xml"), "gather_src")
    level_id = {}
    for el in ET.parse(os.path.join(cliente, "data/world/WorldId.xml")).getroot().iter("data"):
        if el.text and el.get("id"):
            level_id.setdefault(el.text.strip().lower(), int(el.get("id")))
    alt = pickle.load(open(os.path.join(AQUI, "oficial_altura_por_npc.pkl"), "rb"))
    resp = respawns_atuais()
    log(f"client_npcs: {len(npcs)} nomes, gather_src: {len(gathers)}, WorldId: {len(level_id)} levels, respawns atuais: {len(resp)}")
    res, st = {}, collections.Counter()
    sem_nome = collections.Counter()
    for mf in sorted(glob.glob(os.path.join(cliente, "levels", "*", "mission_mission0.xml"))):
        level = os.path.basename(os.path.dirname(mf))
        mapa = level_id.get(level.lower())
        if mapa is None:
            st["level sem worldId"] += 1
            log(f"  {level}: sem id no WorldId.xml, ignorado")
            continue
        if mapas_filtro and mapa not in mapas_filtro:
            continue
        try:
            M = PathDat(mapa)
        except FileNotFoundError:
            M = None
        grupos = {"Npcs": collections.OrderedDict(), "Gather": collections.OrderedDict()}
        for _, el in ET.iterparse(mf, events=("end",)):
            if el.tag != "Object":
                continue
            tipo = (el.get("Type") or "").upper()
            if tipo not in ("SP", "HSP"):       # SP = NPC/mob, HSP = ponto de coleta (gather_src)
                el.clear()
                continue
            nome = (el.get("npc") or "").strip()
            pos = (el.get("Pos") or "").split(",")
            if not nome or len(pos) < 3:
                st["SP sem npc/Pos"] += 1
                el.clear()
                continue
            if tipo == "SP" and nome.lower() in npcs:
                cat, nid = "Npcs", npcs[nome.lower()]
            elif nome.lower() in gathers:
                cat, nid = "Gather", gathers[nome.lower()]
            else:
                sem_nome[nome] += 1
                st["SP com npc desconhecido"] += 1
                el.clear()
                continue
            x, y, z = (float(v) for v in pos[:3])
            h = heading(el.get("Angles"))
            ignora = el.get("Ignore_heightcheck") == "1"
            rw = el.get("iidle_range")
            rw = int(rw) if rw and rw.lstrip("-").isdigit() and int(rw) > 0 else 0
            zf, caso = z, "editor"
            of = alt.get(nid)
            if ignora:
                caso = "Ignore_heightcheck=1"
            elif of is not None and of > 1:
                caso = "voa no oficial"
            else:
                p, caso = piso(M, x, y, z)
                if p is not None:
                    zf = p
            st["z: " + caso] += 1
            st["pontos " + cat] += 1
            grupos[cat].setdefault(nid, {"nome": nome, "spots": []})["spots"].append((x, y, zf, h, rw, z))
            el.clear()
        res[mapa] = (level, grupos, resp)
        log(f"  {mapa} {level}: {sum(len(g['spots']) for g in grupos['Npcs'].values())} NPCs em {len(grupos['Npcs'])} tipos, "
            f"{sum(len(g['spots']) for g in grupos['Gather'].values())} coletas")
    return res, st, sem_nome


def grava(res, saida):
    n = 0
    for mapa, (level, grupos, resp) in res.items():
        for cat, g in grupos.items():
            if not g:
                continue
            os.makedirs(os.path.join(saida, cat), exist_ok=True)
            linhas = ['<?xml version="1.0" encoding="utf-8"?>', "<spawns>", f'\t<spawn_map map_id="{mapa}">']
            for nid, info in g.items():
                linhas.append(f"\t\t<!-- {info['nome']} -->")
                linhas.append(f'\t\t<spawn npc_id="{nid}" respawn_time="{resp.get((mapa, nid), 295)}">')
                for x, y, z, h, rw, _ in info["spots"]:
                    extra = f' random_walk="{rw}"' if rw else ""
                    linhas.append(f'\t\t\t<spot x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}" h="{h}"{extra}/>')
                linhas.append("\t\t</spawn>")
            linhas += ["\t</spawn_map>", "</spawns>", ""]
            arq = os.path.join(saida, cat, f"{mapa}_{level}.xml")
            open(arq, "w", encoding="utf-8", newline="\n").write("\n".join(linhas))
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("saida")
    ap.add_argument("--cliente", default=CLIENTE)
    ap.add_argument("--mapas")
    a = ap.parse_args()
    filtro = {int(m) for m in a.mapas.split(",")} if a.mapas else None
    res, st, sem = extrai(a.cliente, filtro)
    print("\nResumo:")
    for k, v in sorted(st.items()):
        print(f"  {v:7d}  {k}")
    if sem:
        print(f"  nomes de npc do mission sem id no cliente: {len(sem)} (ex.: {', '.join(f'{k} x{v}' for k, v in sem.most_common(5))})")
    pickle.dump(res, open(os.path.join(AQUI, "extrai_spawns_cliente.pkl"), "wb"))
    print(f"{grava(res, a.saida)} arquivos em {a.saida}")


if __name__ == "__main__":
    sys.exit(main())
