"""Rotas e andar aleatório dos NPCs de Sanctum e Pandaemonium pelas capturas oficiais 5.0.

Verdade = S_MOVE (opcode 55 decodificado) das capturas em 110010000 / 120010000:
  [D obj][fff posição][C h][C mask][fff alvo]  (30 b; 18 b = parada, sem alvo)
  mask 0xE8/0xEA = rota (0xEA sai de uma ponta), 0xE0/0xE2/0xE4 = andar aleatório.
O oficial manda o pacote quando o NPC sai de um ponto: a posição é exatamente o alvo
anterior, então cada pacote é uma ligação ponto -> próximo ponto.

Por spot do servidor (NPC da captura -> spot do mesmo npc mais perto, até 40 m):
  - rota fechada (o sucessor dominante volta ao início): walker NORMAL com todos os pontos;
  - rota aberta (trecho que nenhuma captura cobriu): WALK_BACK só pelos pontos vistos,
    sem ligar as pontas em linha reta (não inventa caminho);
  - pausa (rest_time, ms) = mediana de (intervalo entre saídas - distância / velocidade
    do S_PUT_NPC), zerada abaixo de 400 ms;
  - andar aleatório: random_walk = raio máximo medido (n >= 10) ou p90 do npc no mapa
    (n < 10, arena), arredondado para cima, mínimo 1.
Spots que já têm rota batendo com a oficial (>= 80% dos alvos a 2 m) ficam como estão.
Spawns comentados como "DESATIVADO (Alerta Walker ...)" de NPC visto andando voltam.

route_id = SHA-1 de "captura50:<mapa>:<npc>:<x>:<y>" (40 hex, como as rotas herdadas).
Grava em spawns/Npcs/<capital>.xml e npc_walker/npc_walker.xml nas duas árvores.

Uso: python gera_50_capitais_movimento.py [--aplica]
"""
import collections, glob, hashlib, json, math, os, re, statistics, struct, sys

import backup_manager

sys.path.insert(0, backup_manager.TOOLS_DIR)
import aion_pcap  # noqa: E402

COLETAS = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas")
CAPTURAS = os.path.join(COLETAS, "Wireshark - Oficial Classic 5.0")
CACHE = os.path.join(backup_manager.PARSERS_DIR, "backups", "cache_movimento_capitais.json")
CAPITAIS = {"110010000": "110010000_Sanctum", "120010000": "120010000_Pandaemonium"}
ARVORES = [backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR]
TOL = 0.01          # o oficial repete o alvo exato
PAUSA_MIN = 1500    # ms: abaixo disso é o atraso do próprio servidor entre chegar e sair (0,1–0,5 s), não pausa de script
LIGA_MAX = 20.0     # m: maior buraco entre trechos capturados que é ligado em linha reta
ROTA_OK = 0.8


# ---------------------------------------------------------------- capturas

def le_capturas():
    arqs = sorted(glob.glob(CAPTURAS + "/**/*.pcapng", recursive=True))
    nomes = [os.path.basename(f) for f in arqs]
    if os.path.exists(CACHE):
        dados = json.load(open(CACHE, encoding="utf-8"))
        if dados.get("arquivos") == nomes:
            return dados
    mov = collections.defaultdict(list)
    info = {}
    for i, f in enumerate(arqs, 1):
        print(f"   captura {i}/{len(arqs)}: {os.path.basename(f)}", flush=True)
        try:
            sessoes = aion_pcap.abre_todas(f)
        except Exception as e:  # captura quebrada não derruba o resto
            print(f"      ignorada: {e}")
            continue
        for si, s in enumerate(sessoes):
            mapa, objs = None, {}
            for t, lado, op, p in aion_pcap.intercalado(s):
                if lado != "servidor":
                    continue
                if op == 0x0F and len(p) >= 4:
                    v = struct.unpack_from("<I", p, 0)[0]
                    if v > 100000000:
                        mapa, objs = str(v), {}
                elif mapa not in CAPITAIS:
                    continue
                elif op == 0x0E and len(p) >= 48:
                    x, y, z, obj, npc = struct.unpack_from("<fffII", p, 0)
                    k = f"{mapa}:{npc}:{os.path.basename(f)}:{si}:{obj}"
                    objs[obj] = k
                    info.setdefault(k, {"vel": struct.unpack_from("<f", p, len(p) - 40)[0]})
                elif op == 55 and len(p) >= 30:
                    obj = struct.unpack_from("<I", p, 0)[0]
                    if obj in objs:
                        x, y, z = struct.unpack_from("<fff", p, 4)
                        tx, ty, tz = struct.unpack_from("<fff", p, 18)
                        mov[objs[obj]].append((t, p[17], x, y, z, tx, ty, tz))
    dados = {"arquivos": nomes, "mov": mov, "info": info}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(dados, open(CACHE, "w", encoding="utf-8"))
    return dados


# ---------------------------------------------------------------- servidor

def sem_comentarios(txt):
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), txt, flags=re.S)


def spots(txt):
    out = []
    limpo = sem_comentarios(txt)
    for sp in re.finditer(r"<spawn\b([^>]*)>(.*?)</spawn>", limpo, re.S):
        npc = int(re.search(r'npc_id="(\d+)"', sp.group(1)).group(1))
        for s in re.finditer(r"<spot\b([^>]*?)\s*/>", sp.group(2)):
            a = dict(re.findall(r'(\w+)="([^"]*)"', s.group(1)))
            ini = sp.start(2) + s.start()
            out.append({"npc": npc, "x": float(a["x"]), "y": float(a["y"]), "z": float(a["z"]),
                        "walker": a.get("walker_id"), "rw": a.get("random_walk"), "indice": a.get("walker_index"),
                        "ini": ini, "fim": sp.start(2) + s.end()})
    return out


def rotas_servidor(txt):
    rotas = {}
    for m in re.finditer(r"<walker_template\b([^>]*)>(.*?)</walker_template>", txt, re.S):
        rid = re.search(r'route_id="([^"]+)"', m.group(1)).group(1)
        rotas[rid] = [tuple(map(float, s)) for s in re.findall(r'<routestep x="([^"]+)" y="([^"]+)" z="([^"]+)"', m.group(2))]
    return rotas


def reativa_desativados(txt, vistos):
    """Spawns inteiros comentados como DESATIVADO (Alerta Walker) de NPC visto andando."""
    volta = []

    def troca(m):
        corpo = m.group(1)
        npc = re.search(r'<spawn npc_id="(\d+)"', corpo)
        if npc and int(npc.group(1)) in vistos and "<!--" not in corpo:
            volta.append(int(npc.group(1)))
            return corpo.strip("\r\n")
        return m.group(0)
    txt = re.sub(r"<!-- DESATIVADO \(Alerta Walker: [0-9A-F]{40}\)\s*(<spawn\b.*?</spawn>)\s*-->", troca, txt, flags=re.S)
    return txt, volta


# ---------------------------------------------------------------- análise

def monta_rota(obs, d, spot):
    pontos = []

    def pid(x, y, z):
        for j, q in enumerate(pontos):
            if math.dist(q[:2], (x, y)) < TOL and abs(q[2] - z) < 2:
                return j
        pontos.append((x, y, z))
        return len(pontos) - 1

    for _k, v in obs:
        for e in v:
            pid(e[5], e[6], e[7])
    suc = collections.defaultdict(collections.Counter)
    pausas = collections.defaultdict(list)
    for k, v in obs:
        vel = d["info"].get(k, {}).get("vel") or 1.0
        anterior = None
        for e in v:
            pb = pid(e[5], e[6], e[7])
            pa = next((j for j, q in enumerate(pontos) if math.dist(q[:2], (e[2], e[3])) < TOL and abs(q[2] - e[4]) < 2), None)
            if pa is not None and pa != pb:
                suc[pa][pb] += 1
                if anterior and anterior[1] == pa and anterior[2] is not None:
                    seg = math.dist(pontos[anterior[2]], pontos[pa]) / vel
                    dt = (e[0] - anterior[0]) / 1e9
                    if dt < seg + 60:
                        pausas[pa].append(max(0.0, dt - seg))
            anterior = (e[0], pb, pa)

    def cadeia(j, usados=()):
        c = []
        while j is not None and j not in c and j not in usados:
            c.append(j)
            j = suc[j].most_common(1)[0][0] if suc[j] else None
        return c, j

    ini = min(range(len(pontos)), key=lambda j: math.dist(pontos[j][:2], (spot["x"], spot["y"])))
    ciclo, volta = cadeia(ini)
    fechou = volta is not None and volta in ciclo
    if fechou:
        ciclo = ciclo[ciclo.index(volta):]
    ligacoes = []
    if not fechou or len(ciclo) < len(pontos) * 0.9:
        # Trechos contínuos vistos nas capturas (onde algum pacote ligou um ponto ao seguinte). Entre eles há buracos que nenhuma
        # captura cobriu; buraco de até LIGA_MAX entre o fim de um trecho e o início de outro é ligado em linha reta (o NPC
        # passa por ali para ir de um ao outro). Fecha o circuito se o último fim cai perto do primeiro início.
        pred = collections.Counter(b for a in suc for b in suc[a])
        trechos, usados = [], set()
        for s in [j for j in range(len(pontos)) if not pred[j]] + list(range(len(pontos))):
            if s in usados:
                continue
            c, _ = cadeia(s, usados)
            usados |= set(c)
            if len(c) > 1:
                trechos.append(c)
        melhor = None
        for primeiro in trechos:
            ordem, livres, liga = list(primeiro), [t for t in trechos if t is not primeiro], []
            while True:
                fim = pontos[ordem[-1]]
                cand = [(math.dist(fim[:2], pontos[t[0]][:2]), t) for t in livres]
                cand = [ct for ct in cand if ct[0] <= LIGA_MAX]
                if not cand:
                    break
                dd, t = min(cand, key=lambda ct: ct[0])
                liga.append(dd)
                ordem += [p for p in t if p not in ordem]
                livres.remove(t)
            if melhor is None or len(ordem) > len(melhor[0]):
                melhor = (ordem, liga)
        if melhor and (not fechou or len(melhor[0]) > len(ciclo)):
            ciclo, ligacoes = melhor
            fim_ini = math.dist(pontos[ciclo[-1]][:2], pontos[ciclo[0]][:2])
            fechou = suc[ciclo[-1]].most_common(1)[0][0] == ciclo[0] if suc[ciclo[-1]] else fim_ini <= LIGA_MAX
            if fechou and fim_ini > TOL:
                ligacoes.append(fim_ini)
    passos = []
    for c in ciclo:
        r = int(round(statistics.median(pausas[c]) * 1000)) if pausas[c] else 0
        passos.append((pontos[c][0], pontos[c][1], pontos[c][2], r if r >= PAUSA_MIN else 0))
    lacuna = 0.0 if fechou else math.dist(pontos[ciclo[-1]][:2], pontos[ciclo[0]][:2])
    return {"passos": passos, "fechou": fechou, "pontos": len(pontos), "lacuna": lacuna, "ligacoes": ligacoes}


ANDAR_Z = 5.0  # m: diferença máxima de altura entre o spot e o objeto da captura para serem o mesmo NPC


def analisa(d, mapa, txt, rotas):
    srv = spots(txt)
    grupos = collections.defaultdict(list)
    for k, v in d["mov"].items():
        m, npc = k.split(":")[:2]
        if m != mapa:
            continue
        npc = int(npc)
        # só spot no mesmo andar do objeto: torre de Tiamaranta tem o mesmo npc a 80 m de altura no mesmo x/y (30/10: guarda do
        # térreo z 309 levou a rota do andar z 388 e andava no ar)
        zs = [e[4] for e in v] + [e[7] for e in v]
        cand = [i for i, s in enumerate(srv) if s["npc"] == npc and min(abs(s["z"] - z) for z in zs) <= ANDAR_Z]
        if not cand:
            continue
        pts = [(e[5], e[6]) for e in v] + [(e[2], e[3]) for e in v]
        best = min(cand, key=lambda i: min(math.dist((srv[i]["x"], srv[i]["y"]), p) for p in pts))
        # NPC com um spot só: todo objeto dele é desse spot (rota longa pode ter sido vista só longe do spawn)
        if len(cand) == 1 or min(math.dist((srv[best]["x"], srv[best]["y"]), p) for p in pts) <= 40:
            grupos[best].append((k, v))
    regs = []
    for i, obs in sorted(grupos.items()):
        s = srv[i]
        rota = sum(e[1] in (0xE8, 0xEA) for _, v in obs for e in v)
        aleat = sum(e[1] not in (0xE8, 0xEA) for _, v in obs for e in v)
        reg = {"i": i, "spot": s, "tipo": "rota" if rota > aleat else "aleat"}
        if reg["tipo"] == "aleat":
            reg["dist"] = sorted(math.dist((s["x"], s["y"]), (e[5], e[6])) for _, v in obs for e in v)
        else:
            reg.update(monta_rota(obs, d, s))
            if s["walker"] in rotas:
                st = rotas[s["walker"]]
                alvos = [(e[5], e[6]) for _, v in obs for e in v]
                reg["casa"] = sum(min(math.dist(a, r[:2]) for r in st) < 2 for a in alvos) / len(alvos)
        regs.append(reg)
    # raio do andar aleatório; com poucas amostras usa o p90 do npc no mapa
    por_npc = collections.defaultdict(list)
    for r in regs:
        if r["tipo"] == "aleat":
            por_npc[r["spot"]["npc"]] += r["dist"]
    for r in regs:
        if r["tipo"] != "aleat":
            continue
        if len(r["dist"]) >= 10:
            r["raio"] = max(1, math.ceil(r["dist"][-1] - 0.05))
        else:
            todos = sorted(por_npc[r["spot"]["npc"]])
            r["raio"] = max(1, math.ceil(todos[int(len(todos) * 0.9) - 1] - 0.05))
    return srv, regs


CLIENTE_WORLD = os.path.join(COLETAS, "Client 5.0 - Dados Extraidos", "data", "world")
MAPA_CLIENTE = {"110010000": "lc1", "120010000": "dc1"}


def unicos_no_oficial(d, mapa):
    """npcs com um objeto só em toda sessão das capturas e um ponto só no npc_info."""
    por_sessao = collections.defaultdict(lambda: collections.defaultdict(set))
    for k in d["info"]:
        m, npc, f, si, obj = k.split(":")
        if m == mapa:
            por_sessao[int(npc)][(f, si)].add(obj)
    txt = open(os.path.join(CLIENTE_WORLD, f"client_world_{MAPA_CLIENTE[mapa]}.xml"), encoding="utf-8").read()
    pontos = collections.Counter(int(n) for n in re.findall(r"<npc_info>.*?<nameid>(\d+)</nameid>", txt, re.S))
    return {npc for npc, ss in por_sessao.items() if max(len(o) for o in ss.values()) == 1 and pontos[npc] == 1}


def route_id(mapa, s):
    return hashlib.sha1(f"captura50:{mapa}:{s['npc']}:{s['x']:.2f}:{s['y']:.2f}".encode()).hexdigest().upper()


# ---------------------------------------------------------------- escrita

def le(path):
    return open(path, encoding="utf-8", newline="").read()


def grava(path, txt):
    backup_manager.backup_file_before_modification(path)
    open(path, "w", encoding="utf-8", newline="").write(txt)


def troca_spot(tag, walker=None, raio=None):
    tag = re.sub(r'\s+(walker_id|walker_index|random_walk)="[^"]*"', "", tag)
    extra = f' walker_id="{walker}"' if walker else f' random_walk="{raio}"'
    return re.sub(r'(\s*/>)$', extra + r"\1", tag)


def texto_template(desc, rid, loop, passos, nl, extra=""):
    """extra: atributos de grupo já gravados (pool, formation, offsets), mantidos como estão."""
    linhas = [f"\t<!-- {desc} -->", f'\t<walker_template route_id="{rid}"{extra}' + ("" if loop == "NORMAL" else f' loop_type="{loop}"') + ">"]
    for x, y, z, rest in passos:
        linhas.append(f'\t\t<routestep x="{x:.2f}" y="{y:.2f}" z="{z:.3f}"' + (f' rest_time="{rest}"' if rest else "") + " />")
    linhas.append("\t</walker_template>")
    return nl.join(linhas)


def atualiza(aplica):
    """Refaz passos, pausas e loop das rotas que este gerador já gravou (mesmo route_id; spawns não mudam)."""
    d = le_capturas()
    base = backup_manager.SERVER_DATA_DIR
    walker_txt = le(os.path.join(base, "npc_walker", "npc_walker.xml"))
    nl = "\r\n" if "\r\n" in walker_txt else "\n"
    marca = walker_txt.index("gera_50_capitais_movimento.py")
    padrao = re.compile(r"\t<!-- ([^\r\n]*?) -->\r?\n\t<walker_template route_id=\"(\w+)\"[^>]*>.*?</walker_template>", re.S)
    nossos = {m.group(2): m for m in padrao.finditer(walker_txt, marca)}
    rotas = rotas_servidor(walker_txt)
    novos, rel = {}, []
    for mapa, arq in CAPITAIS.items():
        txt = le(os.path.join(base, "spawns", "Npcs", arq + ".xml"))
        _srv, regs = analisa(d, mapa, txt, rotas)
        # membros de grupo sem rota própria: as pausas deles servem para separar a parada de script (todos param) da espera
        # do líder pelas crianças (só ele "para"); na rota do grupo fica só a pausa que todos os membros têm no mesmo passo
        membros = collections.defaultdict(list)
        for r in regs:
            if r["tipo"] == "rota" and r["spot"]["walker"] in nossos and r["spot"].get("indice") not in (None, "0"):
                membros[r["spot"]["walker"]].append(r)
        for r in regs:
            rid = r["spot"]["walker"]
            if r["tipo"] != "rota" or rid not in nossos:
                continue
            if r["spot"].get("indice") in (None, "0") and membros.get(rid):
                outros = [o for o in membros[rid] if len(o["passos"]) == len(r["passos"])]
                r["passos"] = [(x, y, z, rest if rest and all(o["passos"][i][3] for o in outros) else 0)
                               for i, (x, y, z, rest) in enumerate(r["passos"])]
            if r["spot"].get("indice") not in (None, "0"):
                # membro de grupo: se a rota do grupo lista uma rota própria para ele (member_routes), é ela que se recalcula
                abertura = re.search(r"<walker_template route_id=\"\w+\"([^>]*)>", nossos[rid].group(0)).group(1)
                mr = re.search(r'member_routes="([^"]*)"', abertura)
                lista = mr.group(1).split(";") if mr else []
                i = int(r["spot"]["indice"])
                if i >= len(lista) or lista[i] not in nossos:
                    continue
                rid = lista[i]
            loop = "NORMAL" if r["fechou"] else "WALK_BACK"
            m = nossos[rid]
            abertura = re.search(r"<walker_template route_id=\"\w+\"([^>]*)>", m.group(0)).group(1)
            extra = "".join(f' {a}="{v}"' for a, v in re.findall(r'(\w+)="([^"]*)"', abertura) if a in ("pool", "formation", "offsets", "rows", "member_routes"))
            novos[rid] = texto_template(m.group(1), rid, loop, r["passos"], nl, extra)
            antes = rotas[rid]
            liga = r.get("ligacoes") or []
            rel.append(f"{m.group(1)}: {len(antes)} -> {len(r['passos'])} passos, {loop}"
                       + (f", ligações {', '.join(f'{x:.1f}' for x in liga)} m" if liga else "")
                       + (f", trecho sem dado {r['lacuna']:.1f} m" if not r["fechou"] else "")
                       + f", pausas {[p[3] for p in r['passos'] if p[3]]}")
    for rid in nossos:
        if rid not in novos:
            rel.append(f"{nossos[rid].group(1)}: sem spot usando a rota, fica como está")
    print("\n".join(rel))
    if not aplica:
        print("(simulação; --aplica grava)")
        return
    novo = walker_txt
    for rid, m in sorted(nossos.items(), key=lambda kv: kv[1].start(), reverse=True):
        if rid in novos:
            novo = novo[:m.start()] + novos[rid] + novo[m.end():]
    backup_manager.init_backup_session("gera_50_capitais_movimento_atualiza")
    for raiz in ARVORES:
        grava(os.path.join(raiz, "npc_walker", "npc_walker.xml"), novo)
    print("gravado nas duas árvores")


def main():
    aplica = "--aplica" in sys.argv
    if "--atualiza" in sys.argv:
        return atualiza(aplica)
    d = le_capturas()
    base = backup_manager.SERVER_DATA_DIR
    walker_txt = le(os.path.join(base, "npc_walker", "npc_walker.xml"))
    rotas = rotas_servidor(walker_txt)
    nl = "\r\n" if "\r\n" in walker_txt else "\n"
    novos_spawns, templates, rel = {}, [], []
    for mapa, arq in CAPITAIS.items():
        path = os.path.join(base, "spawns", "Npcs", arq + ".xml")
        txt = le(path)
        vistos = {int(k.split(":")[1]) for k in d["mov"] if k.startswith(mapa + ":")}
        txt, volta = reativa_desativados(txt, vistos)
        for n in volta:
            rel.append(f"{arq}: spawn {n} reativado (estava DESATIVADO por Alerta Walker)")
        srv, regs = analisa(d, mapa, txt, rotas)
        trocas = {}
        cont = collections.Counter()
        for r in regs:
            s = r["spot"]
            if r["tipo"] == "rota":
                if s["walker"] and r.get("casa", 0) >= ROTA_OK:
                    cont["rota já certa"] += 1
                    continue
                rid = route_id(mapa, s)
                loop = "NORMAL" if r["fechou"] else "WALK_BACK"
                templates.append((f"{arq} npc {s['npc']} ({s['x']:.0f},{s['y']:.0f})", rid, loop, r["passos"]))
                trocas[r["i"]] = ("walker", rid)
                cont[f"rota {loop}"] += 1
                rel.append(f"{arq}: npc {s['npc']} ({s['x']:.1f},{s['y']:.1f}) rota {loop}, {len(r['passos'])}/{r['pontos']} pontos"
                           + ("" if r["fechou"] else f", trecho não capturado de {r['lacuna']:.1f} m")
                           + (f", substitui {s['walker'][:8]} ({r.get('casa', 0):.0%})" if s["walker"] else ""))
            else:
                if s["rw"] not in (None, "0") or s["walker"]:
                    cont["andar já ligado"] += 1
                    continue
                # cópias do mesmo npc no mesmo ponto recebem o mesmo raio
                for j, o in enumerate(srv):
                    if o["npc"] == s["npc"] and math.dist((o["x"], o["y"]), (s["x"], s["y"])) < 1 and not o["walker"] and o["rw"] in (None, "0"):
                        trocas[j] = ("raio", r["raio"])
                cont["random_walk"] += 1
                rel.append(f"{arq}: npc {s['npc']} ({s['x']:.1f},{s['y']:.1f}) random_walk={r['raio']} (n={len(r['dist'])}, máx {r['dist'][-1]:.1f} m)")
        # cópias da 4.x: NPC que o oficial mostra uma vez só (um objeto por sessão em todas as
        # capturas e um ponto só no npc_info) fica só no spot que casou com a captura
        unicos = unicos_no_oficial(d, mapa)
        casados = {r["i"] for r in regs if r["tipo"] == "rota"}
        for r in regs:
            if r["tipo"] != "rota" or r["spot"]["npc"] not in unicos:
                continue
            for j, o in enumerate(srv):
                if j != r["i"] and o["npc"] == r["spot"]["npc"] and j not in casados:
                    trocas[j] = ("sai", None)
                    rel.append(f"{arq}: npc {o['npc']} spot ({o['x']:.1f},{o['y']:.1f}) sai (cópia; o oficial tem um só, em ({r['spot']['x']:.1f},{r['spot']['y']:.1f}))")
                    cont["spot duplicado removido"] += 1
        for j in sorted(trocas, key=lambda j: srv[j]["ini"], reverse=True):
            o = srv[j]
            tipo, v = trocas[j]
            if tipo == "sai":
                ini = txt.rfind("\n", 0, o["ini"]) + 1
                fim = txt.find("\n", o["fim"]) + 1
                txt = txt[:ini] + txt[fim:]
                continue
            tag = txt[o["ini"]:o["fim"]]
            txt = txt[:o["ini"]] + (troca_spot(tag, walker=v) if tipo == "walker" else troca_spot(tag, raio=v)) + txt[o["fim"]:]
        novos_spawns[arq] = txt
        print(f"{arq}: {dict(cont)}, spots alterados {len(trocas)}, reativados {len(volta)}")
    # templates no fim do npc_walker.xml
    bloco = [f"\t<!-- Sanctum/Pandaemonium: rotas das capturas oficiais 5.0 (gera_50_capitais_movimento.py) -->"]
    for desc, rid, loop, passos in templates:
        bloco.append(f"\t<!-- {desc} -->")
        bloco.append(f'\t<walker_template route_id="{rid}"' + ("" if loop == "NORMAL" else f' loop_type="{loop}"') + ">")
        for x, y, z, rest in passos:
            bloco.append(f'\t\t<routestep x="{x:.2f}" y="{y:.2f}" z="{z:.3f}"' + (f' rest_time="{rest}"' if rest else "") + " />")
        bloco.append("\t</walker_template>")
    ja = [rid for _, rid, _, _ in templates if f'route_id="{rid}"' in walker_txt]
    if ja:
        sys.exit(f"route_id já existe no npc_walker.xml (rodar sobre arquivo limpo): {ja[:3]}")
    novo_walker = walker_txt.replace("</npc_walker>", nl.join(bloco) + nl + "</npc_walker>")
    print("\n".join(rel))
    print(f"rotas novas: {len(templates)}")
    if not aplica:
        print("(simulação; --aplica grava)")
        return
    backup_manager.init_backup_session("gera_50_capitais_movimento")
    for raiz in ARVORES:
        for arq, txt in novos_spawns.items():
            grava(os.path.join(raiz, "spawns", "Npcs", arq + ".xml"), txt)
        grava(os.path.join(raiz, "npc_walker", "npc_walker.xml"), novo_walker)
    print("gravado nas duas árvores")


if __name__ == "__main__":
    main()
