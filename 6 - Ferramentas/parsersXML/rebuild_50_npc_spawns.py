#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_npc_spawns.py

Poe os spawns de NPC nas coordenadas do cliente 5.0 (client_world_*.xml, <npc_info>), mantendo o h e todos os
outros atributos do servidor. E um passo intermediario: a captura de pacotes de cada mapa e instancia vai trazer
posicao, altura e direcao exatas; ate la, isto corrige o que o cliente prova e deixa o resto listado.

O que o cliente prova e o que nao prova (medido, 2026-09-12):
  * Ele NAO lista todos os spawns. Eltnen tem 4413 spots no servidor e 689 pontos no cliente; Dark Poeta 642
    contra 27. Entao nada e apagado nem criado: so spots que tem par no cliente mudam.
  * x,y sim. z nao. Nos mapas herdados da 4.8, o z do servidor fica exatamente no terreno (mediana +0,00 m,
    p10 -0,01 contra o heightmap de data/geo/*.png) e o do cliente e um marcador +1,81 m acima (mediana). Onde
    os dois tem o mesmo x,y e alturas diferentes, so o servidor esta no chao em 1620 casos e so o cliente em 2.
    O bringIntoWorld usa o z como vem, sem corrigir por geodata -- copiar o z do cliente faria NPC flutuar.
    Por isso a altura sai assim, nesta ordem:
      mesmo x,y (<=0,1 m)                  z do servidor; se o proprio spot veio do cliente e flutua 0,3-4 m
                                            sobre o terreno, desce para o terreno
      moveu e ha terreno no ponto novo     z do terreno, se o marcador do cliente estiver 0-4 m acima dele
      moveu <=2 m sem terreno util         z do servidor (mesmo piso)
      moveu >2 m sem terreno util          NAO mexe: mesh, ponte ou mapa sem heightmap, sem como saber o andar
    --z-do-cliente desliga isso e usa o z do cliente em tudo, se for o que se quer.
  * Emparelhamento por npc_id, guloso pela menor distancia horizontal, um-para-um. Ate R_LOCAL metros e sempre
    correcao local. Acima disso so move npc com 1 spot de cada lado. "Mesma quantidade dos dois lados" parecia
    bastar e nao basta: quando a contagem so fica igual porque o import_50_npc_spawns acrescentou o excedente, o
    que sobra do emparelhamento guloso e arbitrario -- o spot antigo solitario ia parar a mais de 1 km, em
    Heiron, Beluslan e Rentus Base. static_id e walker_id nunca andam mais que R_LOCAL: estao presos a um objeto
    da geometria e a uma rota.

Fora do escopo: Npcs/Custom (spawns proprios do emulador) e os mapas em FORA, por decisao do usuario.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_npc_spawns.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python rebuild_50_npc_spawns.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import glob
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR  # noqa: E402

REL_SPAWNS = "spawns"
PASTAS = ("Npcs", "Instances", "Rifts", "Bases")
FORA = {"110030000", "120030000"}  # Sanctum_Gate e Pandaemonium_Entrance: o usuario pediu para nao mexer (2026-09-12)
GEO_DIR = os.path.join(backup_manager.PROJECT_ROOT, "2 - Emulador [Produto Final]", "GameServer", "data", "geo")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_spawns_50.txt")
R_LOCAL = 10.0
MESMO_LUGAR = 0.1
SPAWN_RE = re.compile(r'<spawn\b[^>]*\bnpc_id="(\d+)"[^>]*>(.*?)</spawn>', re.S)
SPOT_RE = re.compile(r"<spot\b[^>]*>")
MAP_RE = re.compile(r'<spawn_map\b[^>]*\bmap_id="(\d+)"[^>]*>(.*?)</spawn_map>', re.S)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def num(v):
    s = "{:.4f}".format(round(v, 4))
    return s.rstrip("0").rstrip(".") if "." in s else s


# ---------------------------------------------------------------- terreno (mesma conta do geoEngine.models.Terrain)
class Terrenos:
    """Heightmap 16 bits por mapa: pixel * 2048 / 65536 metros, celulas de 2 m, arr[xIndex, yIndex], borda = 0."""

    def __init__(self, geo_dir):
        import numpy as np
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        self.np, self.Image, self.cache, self.arq = np, Image, {}, {}
        for p in glob.glob(os.path.join(glob.escape(geo_dir), "*.png")):
            nome = os.path.basename(p)[:-4]
            if not nome.endswith("_materials"):
                for mid in nome.split(","):
                    self.arq[mid] = p

    def _mapa(self, mid):
        if mid not in self.cache:
            arr = None
            if mid in self.arq:
                im = self.Image.open(self.arq[mid])
                if im.mode.startswith("I"):
                    arr = self.np.array(im, dtype=self.np.uint32)
            self.cache[mid] = arr
        return self.cache[mid]

    @staticmethod
    def _ponto(a, xi, yi):
        tx, ty = a.shape
        if xi < 0 or yi < 0 or xi > tx or yi > ty:
            return float("nan")
        if xi in (0, tx) or yi in (0, ty):
            return 0.0
        v = int(a[xi, yi])
        return float("nan") if v == 0xFFFF else v * 2048 / 65536

    def z(self, mid, x, y):
        a = self._mapa(mid)
        if a is None:
            return None
        xn, yw = int(x // 2), int(y // 2)
        fx, fy = (x - xn * 2) / 2, (y - yw * 2) / 2
        z1, z2 = self._ponto(a, xn, yw), self._ponto(a, xn, yw + 1)
        z3, z4 = self._ponto(a, xn + 1, yw), self._ponto(a, xn + 1, yw + 1)
        z = z1 + fy * (z2 - z1) + fx * (z3 - z1) if fx + fy <= 1 else z4 + (1 - fy) * (z3 - z4) + (1 - fx) * (z2 - z4)
        return None if math.isnan(z) or z <= 0 else z


# ---------------------------------------------------------------- leitura
def le_cliente(cdir):
    """map_id -> npc_id -> [(x, y, z)]."""
    wdir = os.path.join(cdir, "data", "world")
    nomes = {}
    for m in re.finditer(r"<data\b([^>]*)>([^<]+)</data>", open(os.path.join(wdir, "WorldId.xml"), encoding="utf-8", errors="replace").read()):
        a = dict(ATTR_RE.findall(m.group(1)))
        if a.get("id"):
            nomes[a["id"]] = m.group(2).strip().lower()
    arqs = {os.path.basename(f)[len("client_world_"):-4].lower(): f
            for f in glob.glob(os.path.join(glob.escape(wdir), "client_world_*.xml"))}
    out = {}
    for mid, nome in nomes.items():
        if nome not in arqs:
            continue
        pts = collections.defaultdict(list)
        for b in re.findall(r"<npc_info>(.*?)</npc_info>", open(arqs[nome], encoding="utf-8", errors="replace").read(), re.S):
            i = re.search(r"<nameid>(\d+)</nameid>", b)
            c = [re.search(r"<" + k + r">([-\d.]+)</" + k + r">", b) for k in "xyz"]
            if i and all(c):
                pts[i.group(1)].append(tuple(float(v.group(1)) for v in c))
        out[mid] = pts
    return out


def arquivos_servidor():
    base = os.path.join(backup_manager.SERVER_DATA_DIR, REL_SPAWNS)
    for pasta in PASTAS:
        for p in sorted(glob.glob(os.path.join(glob.escape(base), pasta, "*.xml"))):  # sem recursao: Npcs/Custom fica fora
            yield os.path.relpath(p, backup_manager.SERVER_DATA_DIR)


def le_servidor():
    """Texto de cada arquivo e os spots, com a posicao absoluta da tag para editar no lugar."""
    textos, spots = {}, collections.defaultdict(lambda: collections.defaultdict(list))
    for rel in arquivos_servidor():
        with open(os.path.join(backup_manager.SERVER_DATA_DIR, rel), encoding="utf-8", newline="") as f:
            t = f.read()
        textos[rel] = t
        for sm in MAP_RE.finditer(t):
            mid = sm.group(1)
            if mid in FORA:
                continue
            for sp in SPAWN_RE.finditer(t, sm.start(2), sm.end(2)):
                for tag in SPOT_RE.finditer(t, sp.start(2), sp.end(2)):
                    a = dict(ATTR_RE.findall(tag.group(0)))
                    try:
                        pos = (float(a["x"]), float(a["y"]), float(a["z"]))
                    except (KeyError, ValueError):
                        continue
                    spots[mid][sp.group(1)].append({"rel": rel, "span": tag.span(), "tag": tag.group(0), "a": a, "pos": pos})
    return textos, spots


# ---------------------------------------------------------------- decisao
def decide(mid, npc, sv, cl, terr, z_cliente):
    """Emparelha e devolve [(spot, nova_pos | None, motivo)] e quantos pontos do cliente sobraram."""
    ns, nc = len(sv), len(cl)
    cand = sorted((math.dist(s["pos"][:2], c[:2]), i, j) for i, s in enumerate(sv) for j, c in enumerate(cl))
    us, uc, out = set(), set(), []
    for d2, i, j in cand:
        if i in us or j in uc:
            continue
        us.add(i)
        uc.add(j)
        s, c = sv[i], cl[j]
        preso = "static_id" in s["a"] or "walker_id" in s["a"]
        if d2 > R_LOCAL:
            if preso:
                out.append((s, None, "preso a static_id/walker_id, cliente a {:.0f} m".format(d2), c))
                continue
            if not (ns == 1 and nc == 1):
                out.append((s, None, "ambiguo: {} spots no servidor, {} no cliente, a {:.0f} m".format(ns, nc, d2), c))
                continue
        x, y = c[0], c[1]
        if z_cliente:
            out.append((s, (x, y, c[2]), "z do cliente (forcado)", c))
            continue
        voa = s["a"].get("aerial_spawn") == "true"
        t = None if voa else terr.z(mid, x, y)
        sz = s["pos"][2]
        if d2 <= MESMO_LUGAR:
            if t is not None and 0.3 < sz - t <= 4.0 and abs(sz - c[2]) <= 0.3:
                out.append((s, (x, y, t), "flutuava sobre o terreno", c))
            else:
                out.append((s, (x, y, sz), "mesmo lugar", c))
        elif t is not None and -0.5 <= c[2] - t <= 4.0:
            out.append((s, (x, y, t), "moveu, z do terreno", c))
        elif d2 <= 2.0:
            out.append((s, (x, y, sz), "moveu <=2 m, z do servidor", c))
        else:
            out.append((s, None, "sem altura confiavel: moveu {:.1f} m fora do terreno".format(d2), c))
    return out, nc - len(uc)


def reescreve_tag(tag, pos):
    """Troca x, y, z no lugar. O que nao mudou fica com o texto original: o z mantido do servidor nao e rearredondado."""
    for k, v in zip("xyz", pos):
        atual = re.search(r'\b' + k + r'="([^"]*)"', tag)
        if atual and abs(float(atual.group(1)) - v) < 1e-6:
            continue
        tag = re.sub(r'(\b' + k + r'=")[^"]*(")', lambda m, v=v: m.group(1) + num(v) + m.group(2), tag, count=1)
    return tag


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--z-do-cliente", action="store_true", help="usa o z do cliente em vez de medir contra o terreno")
    args = ap.parse_args()
    if not os.path.isfile(os.path.join(args.cliente, "data", "world", "WorldId.xml")):
        sys.exit("WorldId.xml do cliente nao encontrado em " + args.cliente + ". Informe --cliente ou AION_CLIENT_XML_DIR.")
    if not args.z_do_cliente and not os.path.isdir(GEO_DIR):
        sys.exit("Sem " + GEO_DIR + ": o heightmap e o que impede o NPC de flutuar. Use --z-do-cliente para ignorar.")

    print("1. Lendo cliente, servidor e terreno...")
    cli = le_cliente(args.cliente)
    textos, spots = le_servidor()
    terr = Terrenos(GEO_DIR)
    print("   {} arquivos de spawn | {} mapas com spot | {} mapas com npc_info no cliente".format(
        len(textos), len(spots), len(cli)))

    print("2. Emparelhando e decidindo...")
    edits = collections.defaultdict(list)
    cont = collections.Counter()
    por_mapa = collections.defaultdict(collections.Counter)
    pendentes, longe, so_cliente = [], [], collections.defaultdict(list)
    for mid in sorted(spots):
        cl = cli.get(mid)
        if cl is None:
            n = sum(len(v) for v in spots[mid].values())
            cont["mapa sem client_world"] += n
            por_mapa[mid]["sem client_world"] += n
            continue
        for npc, sv in spots[mid].items():
            decisoes, sobra = decide(mid, npc, sv, cl.get(npc, []), terr, args.z_do_cliente)
            if sobra:
                so_cliente[mid].append((npc, sobra))
            cont["sem par no cliente"] += len(sv) - len(decisoes)
            por_mapa[mid]["sem par no cliente"] += len(sv) - len(decisoes)
            for s, pos, motivo, c in decisoes:
                if pos is None:
                    chave = motivo.split(":")[0].split(",")[0]
                    cont[chave] += 1
                    por_mapa[mid][chave] += 1
                    pendentes.append((mid, npc, motivo, s["pos"], c))
                    continue
                nova = reescreve_tag(s["tag"], pos)
                if nova == s["tag"]:
                    cont["ja estava certo"] += 1
                    continue
                edits[s["rel"]].append((s["span"], nova))
                cont[motivo] += 1
                por_mapa[mid]["alterado"] += 1
                d2 = math.dist(s["pos"][:2], pos[:2])
                if d2 > 50:
                    longe.append((mid, npc, d2, s["pos"], pos))
        for npc in set(cl) - set(spots[mid]):
            so_cliente[mid].append((npc, len(cl[npc])))
    for k, v in cont.most_common():
        print("   {:48} {}".format(k, v))

    print("3. Montando e validando {} arquivos...".format(len(edits)))
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_SPAWNS, "spawns.xsd")))
    novos = {}
    for rel, lista in edits.items():
        t, out, pos = textos[rel], [], 0
        for (a, b), nova in sorted(lista):
            out.append(t[pos:a])
            out.append(nova)
            pos = b
        out.append(t[pos:])
        novo = "".join(out)
        if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
            for e in list(schema.error_log)[:10]:
                print("   {} linha {}: {}".format(rel, e.line, e.message))
            sys.exit("XSD invalido em " + rel + ": nada foi gravado.")
        novos[rel] = novo
    print("   XSD valido.")

    if novos:
        relatorio(cont, por_mapa, pendentes, longe, so_cliente, args.z_do_cliente)
    else:
        print("   nada a mudar; relatorio anterior mantido.")

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    for rel, novo in sorted(novos.items()):
        backup_manager.backup_file_before_modification(rel)
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            destino = caminho_existente(base, rel)
            with open(destino, "w", encoding="utf-8", newline="") as f:
                f.write(novo)
    print("Gravados {} arquivos nas duas arvores.".format(len(novos)))


def caminho_existente(base, rel):
    """Escreve no nome que ja existe na arvore: 7 arquivos tem maiusculas diferentes entre as duas e o git versiona cada grafia."""
    pasta = os.path.join(base, os.path.dirname(rel))
    alvo = os.path.basename(rel).lower()
    for n in os.listdir(pasta) if os.path.isdir(pasta) else ():
        if n.lower() == alvo:
            return os.path.join(pasta, n)
    return os.path.join(base, rel)


def relatorio(cont, por_mapa, pendentes, longe, so_cliente, z_cliente):
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Spawns de NPC nas coordenadas do cliente 5.0, h e demais atributos do servidor.\n")
        f.write("Altura: {}.\n".format("z do cliente (forcado por --z-do-cliente)" if z_cliente else
                                        "medida contra o heightmap -- o z do cliente e um marcador ~1,8 m acima do chao"))
        f.write("Nada foi apagado nem criado; o que nao tem par seguro fica como esta, para a captura de pacotes.\n\n")
        f.write("== totais ==\n")
        for k, v in cont.most_common():
            f.write("  {:48} {}\n".format(k, v))
        f.write("\n== por mapa ==\n")
        for mid in sorted(por_mapa):
            f.write("  {:10} {}\n".format(mid, ", ".join("{} {}".format(k, v) for k, v in por_mapa[mid].most_common())))
        f.write("\n== spots que o cliente indica em outro lugar mas nao foram movidos ({}) ==\n".format(len(pendentes)))
        f.write("  (mapa, npc_id, motivo, servidor x/y/z, cliente x/y/z)\n")
        for mid, npc, motivo, ps, pc in sorted(pendentes, key=lambda r: (r[0], int(r[1]))):
            f.write("  {} {:>7}  {:52} ({:.1f}, {:.1f}, {:.1f}) -> ({:.1f}, {:.1f}, {:.1f})\n".format(mid, npc, motivo, *ps, *pc))
        f.write("\n== movidos mais de 50 m ({}) -- npc com 1 spot de cada lado; os que mais valem a captura ==\n".format(
            len(longe)))
        for mid, npc, d2, ps, pn in sorted(longe, key=lambda r: -r[2]):
            f.write("  {} {:>7}  {:6.0f} m  ({:.1f}, {:.1f}, {:.1f}) -> ({:.1f}, {:.1f}, {:.1f})\n".format(mid, npc, d2, *ps, *pn))
        total = sum(n for v in so_cliente.values() for _i, n in v)
        f.write("\n== pontos do cliente sem spot no servidor ({}) -- o que a captura precisa confirmar ==\n".format(total))
        for mid in sorted(so_cliente):
            v = so_cliente[mid]
            f.write("  {} {} pontos: {}\n".format(mid, sum(n for _i, n in v),
                                                 " ".join("{}x{}".format(i, n) for i, n in sorted(v, key=lambda r: int(r[0])))))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
