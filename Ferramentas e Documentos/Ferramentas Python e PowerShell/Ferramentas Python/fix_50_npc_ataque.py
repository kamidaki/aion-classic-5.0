"""Ataque oficial de NPC medido nas capturas 5.0 -> <stats attack="..."> no npc_templates.

O servidor tira o ataque de NPC de uma curva da comunidade (NpcStatCalculation) quando o template nao
tem `attack`. Nas capturas, mobs do mesmo nivel e rank vao de ~500 a ~2.200: o oficial e por template.

Medicao (golpe normal de mao principal, S_ATTACK 0x36, mob -> o proprio personagem):
    dano = ataque * rnd(0,8..1,2) - PDef/10        (as duas partes conferidas nas capturas, 28/10)
    => ataque = meio da faixa [max(dano + PDef/10) / 1,2 ; min(dano + PDef/10) / 0,8]
       (sorteio uniforme: todo golpe tem de caber; faixa vazia = golpes que nao fecham, mob fica de fora)
Rodar de novo sobrescreve o attack dos medidos, mas nao apaga o de um mob que passou a ser descartado.
PDef sai do S_STATUS 0x01 (offset 110); npcId do S_PUT_NPC 0x0E (obj @12, id @16).

Descartes: menos de 8 golpes, golpe de 1 (mob roteirizado de tutorial) e espalhamento p90/p10 acima
de 1,6 (o oficial da 1,5; acima disso ha buff/debuff no meio e a media nao e confiavel).

Uso:
    python fix_50_npc_ataque.py            # so mede e mostra
    python fix_50_npc_ataque.py --aplicar  # grava nas duas arvores (por id; nunca copia o arquivo)
    python fix_50_npc_ataque.py --exportar-golpes <csv>  # golpes oficiais para o NpcAttackReplayTest
"""
import glob, json, os, re, statistics as st, struct, sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import aion_pcap  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CAPS = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0")
ARVORES = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "npcs", "npc_templates.xml"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "npcs", "npc_templates.xml"),
]
SAIDA = os.path.join(AQUI, "npc_ataque_medido_50.json")
MIN_GOLPES, MAX_ESPALHAMENTO = 8, 1.6


def parse_attack(p):
    """S_ATTACK 0x36 = SM_ATTACK do emulador: devolve (atacante, alvo, flag, [(dano, status, escudo)])."""
    if len(p) < 26:
        return None
    att, tgt = struct.unpack_from("<I", p, 0)[0], struct.unpack_from("<I", p, 9)[0]
    flag = struct.unpack_from("<H", p, 15)[0]
    off = 19 + (12 if flag in (1, 2, 1025, 1026) else 0)
    if off >= len(p):
        return None
    n, off, hits = p[off], off + 1, []
    for _ in range(n):
        if off + 6 > len(p):
            return None
        dmg, status, shield = struct.unpack_from("<i", p, off)[0], struct.unpack_from("<b", p, off + 4)[0], p[off + 5]
        off += 6 + (12 if shield in (8, 10) else 0 if shield in (0, 2) else 28)
        hits.append((dmg, status, shield))
    return att, tgt, flag, hits


def mede():
    golpes = defaultdict(list)  # npcId -> [(dano, pdef)]
    for arq in sorted(glob.glob(os.path.join(CAPS, "**", "*.pcapng"), recursive=True)):
        try:
            sessoes = aion_pcap.abre_todas(arq, sem_skey=True)  # captura com o jogo já logado também (torre mobs, 29/10)
        except Exception:
            continue
        for s in sessoes:
            eu, pdef, npc = None, None, {}
            for op, p, ok in s["servidor"]:
                if not ok:
                    continue
                if op == 0x01 and len(p) >= 112:
                    eu, pdef = struct.unpack_from("<I", p, 0)[0], struct.unpack_from("<H", p, 110)[0]
                elif op == 0x0E and len(p) >= 20:
                    npc[struct.unpack_from("<I", p, 12)[0]] = struct.unpack_from("<I", p, 16)[0]
                elif op == 0x36 and eu is not None:
                    r = parse_attack(p)
                    if not r or not r[3]:
                        continue
                    att, tgt, flag, hits = r
                    dmg, status, shield = hits[0]
                    if tgt == eu and att in npc and flag == 0 and status == 10 and shield == 0 and dmg > 0:
                        golpes[npc[att]].append((dmg, pdef))
    mede.golpes = golpes
    medidos, descartes = {}, {}
    for nid, v in golpes.items():
        danos = sorted(d for d, _ in v)
        if len(v) < MIN_GOLPES:
            descartes[nid] = f"{len(v)} golpes"
            continue
        if danos[0] <= 1:
            descartes[nid] = "golpe de 1 (roteirizado)"
            continue
        p10, p90 = danos[len(danos) // 10], danos[(len(danos) * 9) // 10]
        if p90 / p10 > MAX_ESPALHAMENTO:
            descartes[nid] = f"espalhamento {p90 / p10:.2f}"
            continue
        # sorteio uniforme 80-120%: todo golpe tem de caber, entao ataque fica entre max/1,2 e min/0,8
        impl = [d + pd / 10 for d, pd in v]
        lo, hi = max(impl) / 1.2, min(impl) / 0.8
        if lo > hi:
            descartes[nid] = f"faixa vazia ({lo:.0f} > {hi:.0f})"
            continue
        medidos[nid] = {"attack": round((lo + hi) / 2), "faixa": [round(lo), round(hi)], "golpes": len(v),
                        "espalhamento": round(p90 / p10, 2)}
    return medidos, descartes


def aplica(caminho, medidos):
    txt = open(caminho, encoding="utf-8", newline="").read()  # preserva CRLF
    feitos, faltam = 0, []
    for nid, m in medidos.items():
        ini = re.search(r'<npc_template npc_id="%d"[^>]*?(/?)>' % nid, txt)
        if not ini or ini.group(1) == "/":
            faltam.append(nid)
            continue
        fim = txt.find("</npc_template>", ini.end())
        bloco = txt[ini.end():fim]
        st_m = re.search(r"<stats\b[^>]*?/?>", bloco)
        if not st_m:
            faltam.append(nid)
            continue
        tag = st_m.group(0)
        if re.search(r'\battack="\d+"', tag):
            nova = re.sub(r'\battack="\d+"', 'attack="%d"' % m["attack"], tag)
        else:
            nova = re.sub(r"<stats\b", '<stats attack="%d"' % m["attack"], tag, count=1)
        bloco = bloco[:st_m.start()] + nova + bloco[st_m.end():]
        txt = txt[:ini.end()] + bloco + txt[fim:]
        feitos += 1
    open(caminho, "w", encoding="utf-8", newline="").write(txt)
    return feitos, faltam


if __name__ == "__main__":
    medidos, descartes = mede()
    json.dump({"medidos": {str(k): v for k, v in sorted(medidos.items())},
               "descartes": {str(k): v for k, v in sorted(descartes.items())}},
              open(SAIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(medidos)} NPCs medidos, {len(descartes)} descartados -> {SAIDA}")
    for nid, m in sorted(medidos.items()):
        print(f"  {nid}: attack {m['attack']}  ({m['golpes']} golpes, espalhamento {m['espalhamento']})")
    if "--exportar-golpes" in sys.argv:  # fixture do NpcAttackReplayTest: npcId;dano;pdef de todo golpe normal
        csv = sys.argv[sys.argv.index("--exportar-golpes") + 1]
        with open(csv, "w", encoding="utf-8", newline="\n") as f:
            f.write("npc_id;dano;pdef\n")
            for nid, v in sorted(mede.golpes.items()):
                for d, pd in v:
                    f.write(f"{nid};{d};{pd}\n")
        print("golpes exportados ->", csv)
    if "--aplicar" in sys.argv:
        for arv in ARVORES:
            feitos, faltam = aplica(arv, medidos)
            print(f"{arv}: {feitos} gravados" + (f", sem template/stats: {faltam}" if faltam else ""))
