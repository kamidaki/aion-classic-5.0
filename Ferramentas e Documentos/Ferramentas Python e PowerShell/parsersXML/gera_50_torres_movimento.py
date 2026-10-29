"""Rotas dos NPCs das torres de Tiamaranta Mesa (guardas e minas) pelas capturas oficiais 5.0.

Mesma verdade e mesma montagem do gera_50_capitais_movimento.py (S_MOVE 55, ligação ponto -> próximo ponto, monta_rota):
  - só pacote de rota (mask 0xE8/0xEA). O 0xE0 de guarda é a perseguição em combate (0,66 s); vira raio de andar
    aleatório falso, então fica de fora e este gerador nunca põe random_walk;
  - NPC alvo: guardas de torre (LDF4b_<torre>_Guard_* no cliente) e minas que voam em volta delas (220979, 220980);
    esses npcIds só existem em Tiamaranta, então sessão sem S_KEY que não pegou o S 0x0F (mapa) entra também;
  - rota só com MIN_PACOTES saídas e MIN_PONTOS pontos (abaixo disso é um pedaço de combate);
  - spot que já tem rota batendo >= 80% dos alvos a 2 m fica como está.

Grava, em cada árvore separadamente:
  - npc_walker/npc_walker.xml: as walker_template entre os marcadores (rodar de novo troca o bloco);
  - walker_id nos spots de spawns/Bases/800040000_Tiamaranta.xml e spawns/Npcs/800040000_Tiamaranta_Mesa.xml;
  - torres_rotas_50.json (aqui): "npc:x:y" -> route_id, lido pelo fix_50_tiamaranta_torres.py para a rota sobreviver
    quando as torres forem regeradas.

Uso: python gera_50_torres_movimento.py [--aplica]
"""
import collections, json, math, os, re, struct, sys

import backup_manager
import gera_50_capitais_movimento as cap

sys.path.insert(0, backup_manager.TOOLS_DIR)
import aion_pcap  # noqa: E402

MAPA = "800040000"
CACHE = os.path.join(backup_manager.PARSERS_DIR, "backups", "cache_movimento_torres.json")
MAPA_ROTAS = os.path.join(backup_manager.PARSERS_DIR, "torres_rotas_50.json")
CLIENTE = os.path.join(cap.COLETAS, "Client 5.0 - Dados Extraidos", "data", "npcs", "client_npcs.xml")
ARQUIVOS = [os.path.join("spawns", "Bases", "800040000_Tiamaranta.xml"), os.path.join("spawns", "Npcs", "800040000_Tiamaranta_Mesa.xml")]
MINAS = {220979, 220980}
ROTA = (0xE8, 0xEA)
MIN_PACOTES, MIN_PONTOS = 10, 3
INICIO, FIM = "<!-- gera_50_torres_movimento: inicio -->", "<!-- gera_50_torres_movimento: fim -->"


def alvos():
    txt = open(CLIENTE, encoding="utf-8").read()
    ids = {int(i) for i, n in re.findall(r"<id>(\d+)</id>\s*<name>([^<]*)</name>", txt) if re.match(r"LDF4b_\d+_Guard_", n)}
    return ids | MINAS


def le_capturas(ids):
    arqs = sorted(cap.glob.glob(cap.CAPTURAS + "/**/*.pcapng", recursive=True))
    nomes = [os.path.basename(f) for f in arqs]
    if os.path.exists(CACHE):
        dados = json.load(open(CACHE, encoding="utf-8"))
        if dados.get("arquivos") == nomes:
            return dados
    mov, info = collections.defaultdict(list), {}
    for i, f in enumerate(arqs, 1):
        print(f"   captura {i}/{len(arqs)}: {os.path.basename(f)}", flush=True)
        try:
            sessoes = aion_pcap.abre_todas(f, sem_skey=True)
        except Exception as e:
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
                elif mapa not in (MAPA, None):
                    continue
                elif op == 0x0E and len(p) >= 48:
                    x, y, z, obj, npc = struct.unpack_from("<fffII", p, 0)
                    if npc in ids:
                        k = f"{MAPA}:{npc}:{os.path.basename(f)}:{si}:{obj}"
                        objs[obj] = k
                        info.setdefault(k, {"vel": struct.unpack_from("<f", p, len(p) - 40)[0]})
                elif op == 55 and len(p) >= 30 and p[17] in ROTA:
                    obj = struct.unpack_from("<I", p, 0)[0]
                    if obj in objs:
                        x, y, z = struct.unpack_from("<fff", p, 4)
                        tx, ty, tz = struct.unpack_from("<fff", p, 18)
                        mov[objs[obj]].append((t, p[17], x, y, z, tx, ty, tz))
    dados = {"arquivos": nomes, "mov": mov, "info": info}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(dados, open(CACHE, "w", encoding="utf-8"))
    return dados


def chave(s):
    return f"{s['npc']}:{s['x']:.2f}:{s['y']:.2f}"


def analisa_arvore(d, raiz, rotas):
    """-> (templates {rid: (desc, loop, passos)}, trocas {arquivo: {indice_spot: rid}}, mapa {chave: rid}, relatório)."""
    templates, trocas, mapa, rel = {}, {}, {}, []
    for arq in ARQUIVOS:
        txt = cap.le(os.path.join(raiz, arq))
        srv, regs = cap.analisa(d, MAPA, txt, rotas)
        trocas[arq] = {}
        for r in regs:
            s = r["spot"]
            if r["tipo"] != "rota":  # o filtro só deixa pacote de rota; aqui não sobra andar aleatório
                continue
            if r["pontos"] < MIN_PONTOS or len(r["passos"]) < MIN_PONTOS:
                rel.append(f"{os.path.basename(arq)}: npc {s['npc']} ({s['x']:.1f},{s['y']:.1f}) ignorado: {r['pontos']} pontos")
                continue
            if s["walker"] and r.get("casa", 0) >= cap.ROTA_OK:
                rel.append(f"{os.path.basename(arq)}: npc {s['npc']} ({s['x']:.1f},{s['y']:.1f}) rota {s['walker'][:8]} já certa ({r['casa']:.0%})")
                mapa[chave(s)] = s["walker"]
                continue
            rid = cap.route_id(MAPA, s)
            loop = "NORMAL" if r["fechou"] else "WALK_BACK"
            templates[rid] = (f"{os.path.basename(arq)} npc {s['npc']} ({s['x']:.0f},{s['y']:.0f})", loop, r["passos"])
            trocas[arq][r["i"]] = rid
            mapa[chave(s)] = rid
            rel.append(f"{os.path.basename(arq)}: npc {s['npc']} ({s['x']:.1f},{s['y']:.1f}) rota {loop}, {len(r['passos'])}/{r['pontos']} pontos"
                       + ("" if r["fechou"] else f", trecho não capturado de {r['lacuna']:.1f} m")
                       + (f", substitui {s['walker'][:8]} ({r.get('casa', 0):.0%})" if s["walker"] else ""))
    return templates, trocas, mapa, rel


def filtra(d):
    """Só objeto com MIN_PACOTES saídas de rota (menos que isso é pedaço de combate ou de volta para casa)."""
    mov = {k: v for k, v in d["mov"].items() if len(v) >= MIN_PACOTES}
    return dict(d, mov=mov)


def bloco_walker(templates, nl):
    linhas = [f"\t{INICIO}", "\t<!-- Torres de Tiamaranta Mesa: rotas das capturas oficiais 5.0 (gera_50_torres_movimento.py) -->"]
    for rid, (desc, loop, passos) in sorted(templates.items(), key=lambda kv: kv[1][0]):
        linhas.append(cap.texto_template(desc, rid, loop, passos, nl))
    linhas.append(f"\t{FIM}")
    return nl.join(linhas)


def main():
    aplica = "--aplica" in sys.argv
    d = filtra(le_capturas(alvos()))
    print(f"objetos com rota: {len(d['mov'])}")
    saida = {}
    for raiz in cap.ARVORES:
        wpath = os.path.join(raiz, "npc_walker", "npc_walker.xml")
        wtxt = cap.le(wpath)
        limpo = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIM), "", wtxt, flags=re.S)  # rotas próprias não contam como "já certa"
        templates, trocas, mapa, rel = analisa_arvore(d, raiz, cap.rotas_servidor(limpo))
        nl = "\r\n" if "\r\n" in wtxt else "\n"
        bloco = bloco_walker(templates, nl)
        if INICIO in wtxt:
            novo_w = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIM), lambda _: bloco.lstrip("\t"), wtxt, count=1, flags=re.S)
        else:
            novo_w = wtxt.replace("</npc_walker>", bloco + nl + "</npc_walker>")
        novos = {}
        for arq, tr in trocas.items():
            txt = cap.le(os.path.join(raiz, arq))
            srv = cap.spots(txt)
            for j in sorted(tr, key=lambda j: srv[j]["ini"], reverse=True):
                o = srv[j]
                txt = txt[:o["ini"]] + cap.troca_spot(txt[o["ini"]:o["fim"]], walker=tr[j]) + txt[o["fim"]:]
            novos[arq] = txt
        saida[raiz] = (wpath, novo_w, novos, mapa)
        print(f"\n== {raiz}\n" + "\n".join(rel) + f"\nrotas: {len(templates)}, spots trocados: {sum(len(t) for t in trocas.values())}")
    if not aplica:
        print("\n(simulação; --aplica grava)")
        return
    backup_manager.init_backup_session("gera_50_torres_movimento")
    mapa_total = {}
    for raiz, (wpath, novo_w, novos, mapa) in saida.items():
        cap.grava(wpath, novo_w)
        for arq, txt in novos.items():
            cap.grava(os.path.join(raiz, arq), txt)
        mapa_total.update(mapa)
    json.dump(dict(sorted(mapa_total.items())), open(MAPA_ROTAS, "w", encoding="utf-8"), indent=0)
    print("gravado nas duas árvores;", MAPA_ROTAS)


if __name__ == "__main__":
    main()
