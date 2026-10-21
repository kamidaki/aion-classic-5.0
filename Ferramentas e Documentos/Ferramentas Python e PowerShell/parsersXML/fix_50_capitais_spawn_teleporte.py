#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_capitais_spawn_teleporte.py

Teleportadores de NPC e spawns de Sanctum (110010000) e Pandaemonium (120010000) pelos arquivos do cliente 5.0 e pelas capturas oficiais.

Teleportadores (npc_teleporter.xml)
  O cliente manda C_DESTINATION_AIRPORT (dec 0x5C, [D npc][D airport][H 0]) com o id do client_airports da rota que ele mesmo mostra, e o
  servidor recusava todo destino que não estava na lista antiga (ex.: estátua 730016 com 132/133/135, audit de 01/10 e 21/10).
  - NPC -> rota: <airlines_name> do client_npcs.xml (europe), rota -> id pelo client_airline.xml.
  - Destinos, preço (fee / pvpon_fee) e required_quest saem do client_airline.xml, na ordem do cliente.
  - flight_path_group_id > 0 = FLIGHT com teleportid = grupo*1000+1 (o S_ACTION oficial de voo traz 102001 para o grupo 102);
    entrada sem o campo vale 0 (REGULAR), como nas rotas mistas 117/216 que o servidor já tinha certas.
  - Modelo do servidor cujo NPC não tem rota no cliente fica como está, a menos que use o id de uma rota do cliente (ex.: 800396 com 129):
    nesse caso o NPC é outro (Theobomos/Heiron) e o modelo sai.

Destinos (teleport_location.xml)
  O 5.0 reaproveitou os ids 138-178 para Tiamaranta (LDF4b_Airport_*) e Teva; no servidor eles eram as vilas de housing (700010000/710010000),
  que o 5.0 não tem. Os pares 0x5C -> S_REQUEST_TELEPORT (0x14, [C anim][D mapa][D mapa][F x][F y][F z][C h]) das capturas dão o ponto oficial;
  id do 5.0 sem ponto conhecido sai do arquivo (o servidor responde "sem rota" em vez de levar para uma vila de housing).

Spawns das capitais (spawns/Npcs/1100/1200*)
  O merge_city_spawns.py somou os pontos do client_world aos antigos sem tirar nada: o mesmo NPC ficou na posição da 4.x e na do 5.0.
  A captura confirma a do 5.0 (ex.: 203700 Fasimedes em 1480,1697,576; a cópia em 1876,1511,813 não existe).
  Verdade = <npc_info> do client_world_{lc1,dc1}.xml + objetos SP do mission_mission0.xml + S_PUT_NPC das capturas.
  - fica: ponto a <=2 m (e |dz| <= 5) de um ponto da verdade do mesmo NPC; ponto com static_id (objeto do mapa);
          NPC que anda (walker_id/random_walk) e existe em algum lugar da verdade; NPC só da captura sem ponto que bata (o servidor cria).
  - sai:  todo o resto (posição antiga, NPC que não está em nenhum arquivo do jogo nem na captura).
  - entra: ponto do npc_info sem ponto do servidor a <=2 m (com h do SP mais próximo, se houver).
  - h = dir/3 do SP no mesmo lugar quando o servidor tem h 0 (dir/3 bate com o heading da captura em 526 de 552 pontos).
  spawns/Npcs/Custom fica de fora.

Uso:
    python fix_50_capitais_spawn_teleporte.py --verificar
    python fix_50_capitais_spawn_teleporte.py --aplicar
"""

import argparse
import collections
import glob
import json
import math
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

sys.path.insert(0, backup_manager.TOOLS_DIR)
import aion_pcap  # noqa: E402

COLETAS = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas")
CLIENTE = os.path.join(COLETAS, "Client 5.0 - Dados Extraidos")
CAPTURAS = os.path.join(COLETAS, "Wireshark - Oficial Classic 5.0")
TRADUCAO = os.path.join(COLETAS, "Tradução - Português Brasil", "strings", "client_strings_level.xml")
CACHE = os.path.join(PARSERS_DIR, "backups", "cache_capturas_capitais.json")

REL_TELEPORTER = "npc_teleporter.xml"
REL_TELELOC = "teleport_location.xml"
REL_TEMPLATES = "npcs/npc_templates.xml"
CAPITAIS = {
    110010000: ("lc1", "spawns/Npcs/110010000_Sanctum.xml"),
    120010000: ("dc1", "spawns/Npcs/120010000_Pandaemonium.xml"),
}
RAIO, RAIO_Z = 2.0, 5.0


# ---------------------------------------------------------------- cliente

def le_xml(caminho):
    return ET.parse(caminho).getroot()


def cliente_npcs():
    """id -> (nome interno, airlines_name)"""
    out = {}
    for _ev, el in ET.iterparse(os.path.join(CLIENTE, "data", "europe", "Npcs", "client_npcs.xml")):
        if el.find("id") is not None and el.find("name") is not None:
            out[int(el.findtext("id"))] = (el.findtext("name"), el.findtext("airlines_name"))
            el.clear()
    return out


def cliente_rotas():
    fp = os.path.join(CLIENTE, "data", "flightpath")
    airports = {}
    for e in le_xml(os.path.join(fp, "client_airports.xml")):
        airports[e.findtext("name").lower()] = (int(e.findtext("id")), e.findtext("name"), e.findtext("desc"))
    rotas = {}
    for a in le_xml(os.path.join(fp, "client_airline.xml")):
        destinos = []
        for d in a.iter("data"):
            aid = airports[d.findtext("airport_name").lower()][0]
            destinos.append({
                "loc": aid,
                "fee": int(d.findtext("fee") or 0),
                "pvp": int(d.findtext("pvpon_fee") or 0),
                "quest": int(d.findtext("required_quest") or 0),
                "grupo": int(d.findtext("flight_path_group_id") or 0),
            })
        rotas[a.findtext("name").lower()] = (int(a.findtext("id")), a.findtext("name"), destinos)
    return airports, rotas


def strings_cliente():
    """nome da string (minúsculo) -> id"""
    out = {}
    for f in glob.glob(os.path.join(CLIENTE, "data", "Strings", "*.xml")):
        try:
            for e in le_xml(f):
                n, i = e.findtext("name"), e.findtext("id")
                if n and i:
                    out[n.lower()] = int(i)
        except ET.ParseError:
            pass
    return out


def strings_pt():
    raw = open(TRADUCAO, "rb").read()
    for enc in ("utf-16", "utf-8"):
        try:
            texto = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    return {m.group(1).lower(): m.group(2) for m in re.finditer(r"<name>(.*?)</name>\s*<body>(.*?)</body>", texto, re.S)}


def npc_info(mapa):
    r = le_xml(os.path.join(CLIENTE, "data", "world", f"client_world_{mapa}.xml"))
    out = []
    for n in r.iter("npc_info"):
        p = n.find("pos")
        out.append((int(n.findtext("nameid")), float(p.findtext("x")), float(p.findtext("y")), float(p.findtext("z"))))
    return out


def pontos_sp(mapa, nome_para_id):
    texto = open(os.path.join(CLIENTE, "levels", mapa, "mission_mission0.xml"), encoding="utf-8", errors="replace").read()
    out = []
    for o in re.finditer(r'<Object ([^>]*Type="SP"[^>]*)/?>', texto):
        a = dict(re.findall(r'(\w+)="([^"]*)"', o.group(1)))
        npc = nome_para_id.get(a.get("npc", "").lower())
        if npc is None or "Pos" not in a:
            continue
        x, y, z = map(float, a["Pos"].split(","))
        out.append((npc, x, y, z, float(a.get("dir") or 0)))
    return out


# ---------------------------------------------------------------- capturas

def le_capturas():
    """S_PUT_NPC nas capitais e pares 0x5C -> 0x14 em todas as capturas oficiais."""
    if os.path.exists(CACHE):
        dados = json.load(open(CACHE, encoding="utf-8"))
        if dados.get("arquivos") == [os.path.basename(f) for f in sorted(glob.glob(CAPTURAS + "/**/*.pcapng", recursive=True))]:
            return dados
    puts = collections.defaultdict(list)
    destinos = collections.defaultdict(set)
    arquivos = sorted(glob.glob(CAPTURAS + "/**/*.pcapng", recursive=True))
    for i, f in enumerate(arquivos, 1):
        print(f"   captura {i}/{len(arquivos)}: {os.path.basename(f)}", flush=True)
        try:
            sessoes = aion_pcap.abre_todas(f)
        except Exception as e:  # captura quebrada não derruba o resto
            print(f"      ignorada: {e}")
            continue
        for s in sessoes:
            mapa = None
            for op, p, ok in s["servidor"]:
                if ok and op == 0x0F and len(p) >= 4:
                    v = struct.unpack_from("<I", p, 0)[0]
                    if v > 100000000:
                        mapa = v
                elif ok and op == 0x0E and len(p) >= 48 and mapa in CAPITAIS:
                    x, y, z, _obj, npc = struct.unpack_from("<fffII", p, 0)
                    puts[str(mapa)].append((npc, x, y, z, p[27]))
            pedido = None
            for _t, lado, op, p in aion_pcap.intercalado(s):
                if lado == "cliente" and op == 0x5C and len(p) == 10:
                    pedido = struct.unpack_from("<I", p, 4)[0]
                elif lado == "servidor" and op == 0x14 and len(p) == 22 and pedido is not None:
                    _a, m1, _m2, x, y, z, h = struct.unpack("<BIIfffB", p)
                    destinos[str(pedido)].add((m1, round(x, 4), round(y, 4), round(z, 4), h))
                    pedido = None
    dados = {
        "arquivos": [os.path.basename(f) for f in arquivos],
        "puts": puts,
        "destinos": {k: sorted(v) for k, v in destinos.items()},
    }
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(dados, open(CACHE, "w", encoding="utf-8"))
    return dados


# ---------------------------------------------------------------- npc_teleporter

def edita_teleporter(texto, npcs, rotas, relatorio):
    por_rota = collections.defaultdict(list)
    for nid, (_nome, rota) in npcs.items():
        if rota:
            if rota.lower() not in rotas:
                relatorio.append(f"npc {nid}: rota {rota} não existe no client_airline")
                continue
            por_rota[rotas[rota.lower()][0]].append(nid)
    ids_cliente = {v[0] for v in rotas.values()}
    rota_por_id = {v[0]: v for v in rotas.values()}

    def bloco_rota(tid, npc_ids):
        linhas = [f'\t<teleporter_template npc_ids="{" ".join(map(str, sorted(npc_ids)))}" teleportId="{tid}">', "\t\t<locations>"]
        for d in rota_por_id[tid][2]:
            attrs = f'loc_id="{d["loc"]}"'
            if d["grupo"]:
                attrs += f' teleportid="{d["grupo"] * 1000 + 1}"'
            attrs += f' price="{d["fee"]}" pricePvp="{d["pvp"]}"'
            if d["quest"]:
                attrs += f' required_quest="{d["quest"]}"'
            attrs += f' type="{"FLIGHT" if d["grupo"] else "REGULAR"}"'
            linhas.append(f"\t\t\t<telelocation {attrs}/>")
        linhas += ["\t\t</locations>", "\t</teleporter_template>"]
        return "\n".join(linhas) + "\n"

    feitos = set()
    saida = []
    padrao = re.compile(r'\t<teleporter_template npc_ids="([^"]*)" teleportId="(\d+)">.*?</teleporter_template>\n', re.S)
    pos = 0
    for m in padrao.finditer(texto):
        saida.append(texto[pos:m.start()])
        pos = m.end()
        npc_ids = [int(x) for x in m.group(1).split()]
        tid = int(m.group(2))
        if tid in por_rota:
            if tid not in feitos:
                saida.append(bloco_rota(tid, por_rota[tid]))
                feitos.add(tid)
            fora = [n for n in npc_ids if n not in por_rota[tid]]
            if fora:
                relatorio.append(f"rota {tid}: npc {fora} sem essa rota no cliente, sai")
            continue
        if tid in ids_cliente:
            relatorio.append(f"rota {tid} ({rota_por_id[tid][1]}): npc {npc_ids} não é dono dela no cliente, modelo sai")
            continue
        donos = [n for n in npc_ids if npcs.get(n, (None, None))[1]]
        if donos:
            relatorio.append(f"modelo {tid}: npc {donos} tem outra rota no cliente, sai deste")
            npc_ids = [n for n in npc_ids if n not in donos]
            if not npc_ids:
                continue
            saida.append(m.group(0).replace(m.group(1), " ".join(map(str, npc_ids)), 1))
            continue
        saida.append(m.group(0))
    saida.append(texto[pos:])
    novo = "".join(saida)
    faltam = [tid for tid in sorted(por_rota) if tid not in feitos]
    if faltam:
        ancora = "</npc_teleporter>"
        assert novo.count(ancora) == 1
        extra = "".join(bloco_rota(tid, por_rota[tid]) for tid in faltam)
        novo = novo.replace(ancora, extra + ancora)
        relatorio.append(f"rotas novas: {faltam}")
    return novo


# ---------------------------------------------------------------- teleport_location

def edita_teleloc(texto, airports, rotas, strs, pt, destinos_cap, relatorio):
    usados = {d["loc"] for v in rotas.values() for d in v[2]}
    por_id = {v[0]: (v[1], v[2]) for v in airports.values()}
    linhas = texto.split("\n")
    existentes = {}
    for i, l in enumerate(linhas):
        m = re.search(r'<teleloc_template loc_id="(\d+)"', l)
        if m:
            existentes[int(m.group(1))] = i
    novos = {}
    for aid in range(138, 179):
        nome, desc = por_id.get(aid, (None, None))
        if nome is None:
            continue
        pontos = destinos_cap.get(str(aid))
        if pontos:
            if len(pontos) > 1:
                relatorio.append(f"destino {aid}: {len(pontos)} pontos diferentes na captura, usando o primeiro: {pontos}")
            mapa, x, y, z, h = pontos[0]
            sid = strs.get((desc or "").lower(), 0)
            attrs = f'loc_id="{aid}" mapid="{mapa}" name_en="{nome}"'
            if pt.get((desc or "").lower()):
                attrs += f' name_pt="{pt[(desc or "").lower()]}"'
            attrs += f' name_id="{sid}" posX="{x}" posY="{y}" posZ="{z}" heading="{h}"'
            novos[aid] = f"\t<teleloc_template {attrs}/><!-- {nome}, captura oficial (0x5C -> S_REQUEST_TELEPORT) -->"
        elif aid in existentes:
            novos[aid] = None
            relatorio.append(f"destino {aid} ({nome}{', usado' if aid in usados else ''}): era vila de housing no servidor, sem ponto oficial, sai")
    for aid, linha in novos.items():
        if aid in existentes:
            linhas[existentes[aid]] = linha if linha is not None else "\0"
    faltam = [aid for aid, l in sorted(novos.items()) if l is not None and aid not in existentes]
    if faltam:
        fim = max(i for i, l in enumerate(linhas) if "<teleloc_template" in l)
        for k, aid in enumerate(faltam, 1):
            linhas.insert(fim + k, novos[aid])
    return "\n".join(l for l in linhas if l != "\0")


# ---------------------------------------------------------------- spawns

def perto(a, b):
    return math.dist(a[:2], b[:2]) <= RAIO and abs(a[2] - b[2]) <= RAIO_Z


def edita_spawn(texto, mapa_id, verdade, sp, cap, existem, com_template, relatorio):
    em_algum_lugar = {n for n in verdade}
    so_captura = {n for n in cap if n not in verdade}
    padrao = re.compile(r'(\t\t<spawn npc_id="(\d+)"[^>]*>\n)(.*?)(\t\t</spawn>\n)', re.S)
    servidor = collections.defaultdict(list)
    anda_no_servidor = set()
    for m in padrao.finditer(texto):
        for s in re.finditer(r'<spot x="([^"]+)" y="([^"]+)" z="([^"]+)"([^>]*)>', m.group(3)):
            servidor[int(m.group(2))].append(tuple(map(float, s.groups()[:3])))
            if "walker_id=" in s.group(4) or "random_walk=" in s.group(4):
                anda_no_servidor.add(int(m.group(2)))
    cont = collections.Counter()

    def novo_bloco(m):
        npc = int(m.group(2))
        corpo = []
        for linha in m.group(3).splitlines(keepends=True):
            s = re.search(r'<spot x="([^"]+)" y="([^"]+)" z="([^"]+)"', linha)
            if not s:
                corpo.append(linha)
                continue
            p = tuple(map(float, s.groups()))
            if npc not in existem:
                cont["sai: npc não existe no cliente"] += 1
                continue
            bate = any(perto(p, q) for q in verdade.get(npc, ())) or any(perto(p, q) for q in cap.get(npc, ()))
            anda = "walker_id=" in linha or "random_walk=" in linha
            # mesmo x/y e z errado (ex.: 802011 17 m abaixo do chão): fica, com o z do jogo (captura primeiro)
            so_xy = [q for q in list(cap.get(npc, ())) + list(verdade.get(npc, ())) if math.dist(p[:2], q[:2]) <= RAIO]
            if not bate and so_xy:
                linha = re.sub(r'z="[^"]+"', f'z="{so_xy[0][2]:.4f}"', linha, count=1)
                p = (p[0], p[1], so_xy[0][2])
                cont["fica: z corrigido pelo jogo"] += 1
            elif bate:
                cont["fica: bate com o jogo"] += 1
            elif 'static_id="' in linha:
                cont["fica: objeto do mapa (static_id)"] += 1
            elif anda and npc in em_algum_lugar:
                cont["fica: anda e existe no jogo"] += 1
            elif npc in so_captura and not any(perto(q, c) for q in servidor[npc] for c in cap[npc]):
                cont["fica: só na captura (criado pelo servidor)"] += 1
            else:
                cont["sai: posição que o jogo não tem"] += 1
                continue
            if ' h="0"' in linha:
                hs = [d for (n, x, y, z, d) in sp if n == npc and perto(p, (x, y, z))]
                if hs and round(hs[0] / 3) % 120:
                    linha = linha.replace(' h="0"', f' h="{round(hs[0] / 3) % 120}"', 1)
                    cont["h do SP"] += 1
            corpo.append(linha)
        # pontos do npc_info que o servidor não tem
        for q in npc_info_faltando.pop(npc, []):
            corpo.append(linha_spot(q, npc))
            cont["entra: ponto do npc_info"] += 1
        if not any("<spot" in l for l in corpo):
            return ""
        return m.group(1) + "".join(corpo) + m.group(4)

    def linha_spot(q, npc):
        hs = [d for (n, x, y, z, d) in sp if n == npc and perto(q, (x, y, z))]
        h = round(hs[0] / 3) % 120 if hs else 0
        return f'\t\t\t<spot x="{q[0]:.4f}" y="{q[1]:.4f}" z="{q[2]:.4f}" h="{h}" />\n'

    npc_info_faltando = collections.defaultdict(list)
    for npc, pts in verdade_npc_info.items():
        if npc in anda_no_servidor:
            continue  # o ponto do npc_info é um ponto da rota que o servidor já faz
        for q in pts:
            if not any(perto(q, p) for p in servidor.get(npc, ())):
                if npc not in com_template:
                    relatorio.append(f"{mapa_id}: npc {npc} do npc_info sem npc_template, não entra")
                    continue
                npc_info_faltando[npc].append(q)

    novo = padrao.sub(novo_bloco, texto)
    # NPC do npc_info que nem bloco tem
    if npc_info_faltando:
        extra = ""
        for npc in sorted(npc_info_faltando):
            extra += f'\t\t<spawn npc_id="{npc}" respawn_time="295">\n'
            for q in npc_info_faltando[npc]:
                extra += linha_spot(q, npc)
                cont["entra: ponto do npc_info"] += 1
            extra += "\t\t</spawn>\n"
        ancora = "\t</spawn_map>"
        assert novo.count(ancora) == 1
        novo = novo.replace(ancora, extra + ancora)
    novo = re.sub(r"\n(?:[ \t]*\n){2,}", "\n\n", novo)
    for k in sorted(cont):
        relatorio.append(f"{mapa_id}: {k}: {cont[k]}")
    return novo


# ---------------------------------------------------------------- main

verdade_npc_info = {}


def main():
    global verdade_npc_info
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))

    print("[1/4] cliente")
    npcs = cliente_npcs()
    airports, rotas = cliente_rotas()
    strs, pt = strings_cliente(), strings_pt()
    nome_para_id = {}
    for nid, (nome, _r) in npcs.items():
        nome_para_id.setdefault(nome.lower(), nid)
    print("[2/4] capturas")
    cap = le_capturas()

    relatorio = []
    print("[3/4] edições")
    edicoes = [
        (REL_TELEPORTER, lambda t: edita_teleporter(t, npcs, rotas, relatorio), True),
        (REL_TELELOC, lambda t: edita_teleloc(t, airports, rotas, strs, pt, cap["destinos"], relatorio), True),
    ]
    for mapa_id, (mapa, rel) in CAPITAIS.items():
        info = npc_info(mapa)
        sp = pontos_sp(mapa, nome_para_id)
        caps = collections.defaultdict(list)
        for npc, x, y, z, _h in cap["puts"].get(str(mapa_id), []):
            caps[npc].append((x, y, z))

        def edita(t, mapa_id=mapa_id, info=info, sp=sp, caps=caps):
            global verdade_npc_info
            verdade = collections.defaultdict(list)
            verdade_npc_info = collections.defaultdict(list)
            for n, x, y, z in info:
                verdade[n].append((x, y, z))
                verdade_npc_info[n].append((x, y, z))
            for n, x, y, z, _d in sp:
                verdade[n].append((x, y, z))
            tpl = os.path.join(base_atual[0], REL_TEMPLATES)
            com_template = {int(x) for x in re.findall(r'<npc_template npc_id="(\d+)"', open(tpl, encoding="utf-8").read())}
            return edita_spawn(t, mapa_id, verdade, sp, caps, set(npcs), com_template, relatorio)
        edicoes.append((rel, edita, False))

    gravar = []
    base_atual = [None]
    for rel, funcao, valida in edicoes:
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            base_atual[0] = base
            caminho = os.path.join(base, rel)
            texto = open(caminho, encoding="utf-8", newline="").read()
            crlf = "\r\n" in texto
            antes = len(relatorio)
            novo = funcao(texto.replace("\r\n", "\n"))
            if crlf:
                novo = novo.replace("\n", "\r\n")
            if base == backup_manager.PRODUTO_FINAL_DATA_DIR:
                del relatorio[antes:]  # o relatório da segunda árvore repete o da primeira
            doc = etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
            if valida and not schema.validate(doc):
                for e in list(schema.error_log)[:10]:
                    print(f"   {rel} linha {e.line}: {e.message}")
                sys.exit("   XSD INVALIDO")
            if novo != texto:
                gravar.append((rel, caminho, novo))

    print("[4/4] relatório")
    for linha in relatorio:
        print("   " + linha)
    print(f"\n   {len(gravar)} arquivo(s) mudam: " + ", ".join(sorted({os.path.relpath(c, backup_manager.PROJECT_ROOT) for _r, c, _n in gravar})))
    if args.aplicar:
        for rel, caminho, novo in gravar:
            backup_manager.backup_file_before_modification(rel)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
        print("   gravado")


if __name__ == "__main__":
    main()
