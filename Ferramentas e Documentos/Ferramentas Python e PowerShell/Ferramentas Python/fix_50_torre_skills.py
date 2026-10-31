"""Rotação de skills dos guardas de torre de Tiamaranta Mesa, medida na captura oficial -> npc_skills (cadeia em laço).

Fonte: "Wireshark - Oficial Classic 5.0/06_Sistemas_Novos_5.0/torre mobs.pcapng" (29/10), S_USE_SKILL 0x21
([D quem][H skill][C nível]...), início a início. `--medir` reimprime a sequência e os intervalos de cada guarda.

O que a captura mostra (Balaur, igual nas torres 4401 MistOn, 4412 e 4413):
  - abre com 18166 (Powerful Ankle Snare) de longe, antes do 1º golpe normal;
  - depois gira sempre na mesma ordem, com um tempo fixo por passo; quando uma skill não sai, a vez passa igual
    (17326 -> 17332 em 18,2 s = dois passos).
Elyos: medido nos MistOn da 4401 (274027-274030), um guarda de cada; entra só o laço que se repetiu, sem as skills vistas
uma vez no começo da luta (17083, 17064, 17078, 17124, 17122, 17128, 17117, 17114, 17107, 17113, 17287). Vale para todo
guarda Li e também para os Da (sem captura; as skills G* não têm raça no cliente).
Fora: Seeker (17701 duas vezes, 88 s entre elas).
Também põe ai="simple_abyssguard" em todo guarda de torre (ver AI_GUARDA).

No emulador: abertura com chain_id 0 (a única que a escolha normal pega) e o laço em chain_id 1..n, todos com prob 100;
next_skill_time = mediana do intervalo início a início para a próxima; max_chain_time = 2 passos + 3 s (a vez que não sai
não quebra o laço). Se o laço quebrar, a próxima skill volta a ser a abertura, como no começo de cada luta oficial.

Uso:
    python fix_50_torre_skills.py            # mostra o bloco
    python fix_50_torre_skills.py --aplicar  # grava nas duas árvores
    python fix_50_torre_skills.py --medir    # refaz a medição na captura
"""
import os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CAPTURA = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0", "06_Sistemas_Novos_5.0",
                       "torre mobs.pcapng")
CLIENTE = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data", "npcs", "client_npcs.xml")
REL = os.path.join("npc_skills", "open_worlds", "800040000_Tiamaranta_Mesa.xml")
ARVORES = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", REL),
           os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", REL)]
INICIO, FIM = "<!-- fix_50_torre_skills: inicio -->", "<!-- fix_50_torre_skills: fim -->"
LV = 46

# (abertura, [(skill, ms até a próxima, alvo)]) ; abertura = (skill, ms até a 1ª do laço) ou None
BALAUR = {
    "As": ((18166, 11300), [(17332, 7700, None), (17326, 7700, None), (17689, 10600, None)]),
    "Fi": ((18166, 11200), [(17305, 8100, None), (17307, 7700, None), (17577, 10100, None)]),
    # 17365 -> 17367 nunca visto (as duas lutas acabaram antes): 10,1 s, o passo de fechamento das outras três classes
    "Pr": ((18166, 10500), [(17367, 8500, None), (17365, 10100, "FRIEND")]),
    "Wi": ((18166, 9300), [(17340, 8600, None), (17336, 8100, None), (17719, 10100, None)]),
}
# Medido nos MistOn Elyos da 4401 (274027-274030). As skills são G* (guarda sem raça: GFI_, GAS_, GPR_, GWI_); o cliente
# não tem versão Asmodiana, então Li e Da usam a mesma rotação (pedido do usuário em 29/10, sem captura de Da).
ELYOS = {
    "As": ((17059, 15000), [(17191, 15100, None)]),
    "Fi": (None, [(17081, 5200, None), (17082, 3200, None)]),
    "Pr": (None, [(17133, 4800, None), (17126, 5500, "ME")]),
    "Wi": (None, [(17108, 5300, None), (17115, 6000, None)]),
}
ROTACAO = {"Dr": BALAUR, "Li": ELYOS, "Da": ELYOS}
RACA = {"Dr": "Balaur", "Li": "Elyos", "Da": "Asmodiano"}
# Todo guarda de torre (inclusive Seeker): no cliente cada classe tem uma ai_name só (LGuard_FeA, DGuard_FeA,
# LDF4b_4402_Guard_MistOn_Dr_Fi...); no servidor os irmãos estavam divididos entre simple_abyssguard e general (nunca entra
# em combate) ou aggressive. simple_abyssguard = AggressiveNpcAI (usa a lista de skills) + aggro contra NPC inimigo.
AI_GUARDA = "simple_abyssguard"
TEMPLATES = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "npcs", "npc_templates.xml"),
             os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "npcs", "npc_templates.xml")]
NOMES = {18166: "Powerful Ankle Snare", 17332: "Swift Edge", 17326: "Fall", 17689: "Ranged Ferocious Strike I",
         17305: "Wide Area Wrathful Strike", 17307: "Wide Area Crippling Cut", 17577: "Fire Burst", 17367: "Wide Area Stun",
         17365: "Healing Wind II", 17340: "Winter Binding", 17336: "Fire Burst", 17719: "Summon Holy Servant", 17059: "Cleave",
         17191: "Soul Slash", 17081: "Wide Area Wrathful Strike", 17082: "Crippling Cut", 17133: "Wide Area Stun",
         17126: "Radiant Cure I", 17108: "Winter Binding", 17115: "Fire Burst"}


def guardas():
    """(raça, classe) -> npcIds LDF4b_<torre>_Guard_[MistOn_|MistOff_]<Li|Da|Dr>_<classe> do cliente (classe inclui Seeker)."""
    por = {}
    txt = open(CLIENTE, encoding="utf-8").read()
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", txt, re.S):
        b = m.group(1)
        i, n = re.search(r"<id>(\d+)<", b), re.search(r"<name>([^<]*)<", b)
        g = n and re.match(r"LDF4b_\d+_Guard_(?:Mist(?:On|Off)_)?(Li|Da|Dr)_(As|Fi|Pr|Wi|Seeker)$", n.group(1))
        if i and g:
            por.setdefault((g.group(1), g.group(2)), []).append(int(i.group(1)))
    return {k: sorted(v) for k, v in por.items()}


def linhas(ids, abertura, laco):
    out = [f'\t<npc_skills npc_ids="{" ".join(map(str, ids))}">']
    n = len(laco)

    def entrada(sk, prox_ms, alvo, chain, prox_chain, prox_passo_ms):
        a = f'id="{sk}" lv="{LV}" prob="100"' + (f' chain_id="{chain}"' if chain else "")
        a += f' next_chain_id="{prox_chain}" next_skill_time="{prox_ms}" max_chain_time="{prox_ms + prox_passo_ms + 3000}"'
        a += f' target="{alvo}"' if alvo else ""
        return f"\t\t<npc_skill {a} /><!-- {NOMES.get(sk, '')} -->"

    if abertura:
        sk, ms = abertura
        out.append(entrada(sk, ms, None, 0, 1, laco[0][1]))
        for k, (sk, ms, alvo) in enumerate(laco):
            out.append(entrada(sk, ms, alvo, k + 1, (k + 1) % n + 1, laco[(k + 1) % n][1]))
    else:  # sem abertura: a 1ª do laço abre (chain 0) e tem uma cópia como fechamento
        assert n > 1, "laço de uma skill só precisa de abertura"
        sk, ms, alvo = laco[0]
        out.append(entrada(sk, ms, alvo, 0, 1, laco[1][1]))
        for k in range(1, n):
            sk, ms, alvo = laco[k]
            out.append(entrada(sk, ms, alvo, k, k + 1, laco[(k + 1) % n][1]))
        sk, ms, alvo = laco[0]
        out.append(entrada(sk, ms, alvo, n, 1, laco[1][1]))
    out.append("\t</npc_skills>")
    return out


def bloco(g):
    L = [f"\t{INICIO}",
         "\t<!-- Guardas de torre: rotação medida no S_USE_SKILL de \"torre mobs.pcapng\" (29/10), gerada por fix_50_torre_skills.py.",
         "\t     Balaur: igual nas torres 4401, 4412 e 4413. Elyos: MistOn da 4401, aplicada a todo guarda Li e Da da classe",
         "\t     (skills G* sem raça no cliente). Seeker sem lista (amostra pequena). -->"]
    for raca, tab in ROTACAO.items():
        for c, (ab, laco) in tab.items():
            L.append(f"\t<!-- Guarda {RACA[raca]} {c} ({len(g[(raca, c)])}) -->")
            L += linhas(g[(raca, c)], ab, laco)
    L.append(f"\t{FIM}")
    return "\n".join(L)


AI_BOSS = "ldf4b_tower_boss"  # Watching Eye: TowerWatchingEyeAI (base_protector sem golpe nem movimento; o oficial só guarda o aggro)


def bosses():
    """npcIds com <ai_name>LDF4b_Tower_Boss</ai_name> no cliente (Watching Eye de toda torre e variante)."""
    txt = open(CLIENTE, encoding="utf-8").read()
    return sorted(int(re.search(r"<id>(\d+)<", m.group(1)).group(1)) for m in re.finditer(r"<npc_client>(.*?)</npc_client>", txt, re.S)
                  if "<ai_name>LDF4b_Tower_Boss</ai_name>" in m.group(1))


def aplica_ai(caminho, ids, ai=AI_GUARDA):
    """ai nos templates; só o atributo ai da tag de abertura muda."""
    AI_GUARDA = ai  # noqa: N806 (o troca abaixo usa este nome)
    txt = open(caminho, encoding="utf-8", newline="").read()
    alvo, mudou = set(map(str, ids)), {}

    def troca(m):
        tag, nid = m.group(0), m.group(1)
        if nid not in alvo:
            return tag
        a = re.search(r'\bai="([^"]*)"', tag)
        if a and a.group(1) == AI_GUARDA:
            return tag
        mudou[a.group(1) if a else "(sem ai)"] = mudou.get(a.group(1) if a else "(sem ai)", 0) + 1
        return tag.replace(a.group(0), f'ai="{AI_GUARDA}"') if a else tag.replace(f'npc_id="{nid}"', f'npc_id="{nid}" ai="{AI_GUARDA}"', 1)

    novo = re.sub(r'<npc_template npc_id="(\d+)"[^>]*>', troca, txt)
    open(caminho, "w", encoding="utf-8", newline="").write(novo)
    return mudou


def aplica(caminho, novo):
    txt = open(caminho, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in txt else "\n"
    novo = novo.replace("\n", nl)
    if INICIO in txt:  # o "\t" antes do INICIO fica no arquivo
        txt = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIM), lambda _: novo.lstrip("\t"), txt, count=1, flags=re.S)
    else:
        txt = txt.replace("</npc_skill_templates>", novo + nl + "</npc_skill_templates>")
    open(caminho, "w", encoding="utf-8", newline="").write(txt)


def medir():
    import struct, collections, statistics as st
    sys.path.insert(0, AQUI)
    import aion_pcap
    from fix_50_npc_ataque import parse_attack
    obj2npc, ev = {}, collections.defaultdict(list)
    for s in aion_pcap.abre_todas(CAPTURA, sem_skey=True):
        for (op, p, ok), t in zip(s["servidor"], s["tempo_servidor"]):
            if op == 0x0E and len(p) >= 20:
                obj2npc[struct.unpack_from("<I", p, 12)[0]] = struct.unpack_from("<I", p, 16)[0]
            elif op == 0x21 and len(p) >= 12 and struct.unpack_from("<I", p, 0)[0] in obj2npc:
                ev[struct.unpack_from("<I", p, 0)[0]].append((t, struct.unpack_from("<H", p, 4)[0]))
    for o, e in sorted(ev.items(), key=lambda x: obj2npc[x[0]]):
        if not 274000 <= obj2npc[o] < 275000:
            continue
        e = sorted(set(e))
        tr = collections.defaultdict(list)
        for (ta, a), (tb, b) in zip(e, e[1:]):
            tr[(a, b)].append((tb - ta) / 1e9)
        print(obj2npc[o], [s for _, s in e])
        print("    ", {f"{a}>{b}": (len(v), round(st.median(v), 1)) for (a, b), v in tr.items()})


if __name__ == "__main__":
    if "--medir" in sys.argv:
        medir()
        sys.exit()
    g = guardas()
    b = bloco(g)
    print(b)
    todos = sorted(i for v in g.values() for i in v)
    print(f"guardas de torre no cliente: {len(todos)}")
    if "--aplicar" in sys.argv:
        for arv in ARVORES:
            aplica(arv, b)
            print("gravado:", arv)
        bs = bosses()
        for tpl in TEMPLATES:
            print("ai ->", AI_GUARDA, tpl, aplica_ai(tpl, todos))
            print("ai ->", AI_BOSS, f"({len(bs)} Watching Eye no cliente)", tpl, aplica_ai(tpl, bs, AI_BOSS))
