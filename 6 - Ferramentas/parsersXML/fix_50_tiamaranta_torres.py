#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_tiamaranta_torres.py

Monta as torres "Watching Eye" de Tiamaranta Mesa (camp war 5.0) a partir das capturas oficiais: base_spawn por
ocupante, base_locations e os templates dos NPCs. Substitui o fix_50_tiamaranta_torre.py, que so fazia a 4413.

Como cada NPC e atribuido a uma torre e a um papel
--------------------------------------------------
Pelo nome interno do client_npcs.xml, que e sistematico:
  LDF4b_Tower_{S|M|L}_<nn>_{L|D|Dr}                        estrutura (FLAG); L/D/Dr = Elyos/Asmo/Balaur
  LDF4b_<torre>_Boss_{Li|Da|Dr}_<nivel>                    Watching Eye (BOSS)
  LDF4b_<torre>_Guard_[MistOn_|MistOff_]{Li|Da|Dr}_<papel> guarnicao (As/Fi/Pr/Wi/Seeker)
  LDF4b_WindBox_Setting_Tower_{S|M|L}_<nn>                 geiser de subida
  LDF4b_WindBox_Setting_Tower_L_<nn>_UP                    segundo geiser das Greater, so com dono de raca
  LDF4b_MistOn_Tower_{S|M|L}_<nn>                          MistOn (so vulneravel)
  LDF4b_{Small|Middle|Big}Tower_Teleport_<nn>              estatua de teleporte (so de raca)
  LDF4b_Quest_NPC_{Li|Da}_{Small|Middle|Big}_<n>           NPC de quest da raca dona (tribo USEALL, ver TRIBO_QUEST)
  802222 LDF4b_Placeable_OBJ_LINK_Noshow_NPC               corredor de avanco, pela torre mais proxima
S/Small = Lesser (40000+n), M/Middle = Medium (4410+n), L/Big = Greater (4400+n). Quest_NPC_*_Completion_* nao e de
torre: nasce sempre, no spawn comum.

Estatua e NPC de quest sem captura com dono de raca saem do client_world_ldf4b.xml: o <npc_info> deles traz
<abyss_info> ALi (Elyos) ou ADa (Asmodiano). Ajuste feito em jogo com //fixspawn no Bases (so z/h, no
mesmo npc e x/y) e preservado: spot de mesmo npc e x/y fica com o z/h que ja esta no arquivo.

Regras medidas (captura de 2026-09-13 com a chave 0x87546CA107DC27B8, 2026-09-15, 2026-09-16 e 2026-09-17):
  * a guarnicao tem os mesmos pontos para qualquer dono (4413 e 40010, capturadas com dois donos);
  * WindBox e corredores mudam de lugar entre Balaur e raca (4413);
  * boss e MistOn so existem vulneraveis; estatua e NPC de quest so quando a torre e de uma raca;
  * dono de cada instante sai do S_ABYSS_INFO (lista no login e atualizacoes), nao de chute;
  * p[-32] == 1 no S_PUT_NPC e o ponto exato de nascimento; patrulheiro visto no meio do caminho so vale
    quando o papel nao tem nenhum ponto melhor (sai marcado como aproximado no relatorio).

Templates: corrigidos ou criados **em cada arvore separadamente**. O npc_templates.xml da fonte nao tem os 55
NPCs de housing (810002-810056) que os dados de housing das duas arvores usam; gravar uma arvore por cima da
outra -- como o import_missing_50_npcs.py faz -- apagaria esses NPCs do servidor que roda.

Uso:
    python fix_50_tiamaranta_torres.py [--dry]
"""

import collections
import math
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "6 - Ferramentas"))
import aion_pcap  # noqa: E402

CAP = os.path.join(RAIZ, "5 - Documentação e Referências", "2 - Wireshark - Oficial Classic 5.0")
CAPTURAS = [
    (os.path.join(CAP, "06_Sistemas_Novos_5.0",
                  "06_Sistemas_Novos_Tiamaranta_ZonaNeutra_Asmo_5.0_2026-09-13_01-26-03_00001_20260913012603.pcapng"),
     0x87546CA107DC27B8),   # sem S_KEY; a chave antiga (...07B927B8) tem o byte 2 errado
    (os.path.join(CAP, "08_Spawns_Mapas", "Tiamaranta_Mesa",
                  "08_Spawns_Mapas_Tiamaranta_Mesa_2026-09-15_05-09-38_00001_20260915050938.pcapng"), None),
    (os.path.join(CAP, "06_Sistemas_Novos_5.0", "06_Sistemas_Novos_5.0_2026-09-16_05-01-15_00001_20260916050115.pcapng"), None),
    (os.path.join(CAP, "08_Spawns_Mapas", "Tiamaranta_Mesa",
                  "08_Spawns_Mapas_Tiamaranta_Mesa_2026-09-16_05-22-24_00001_20260916052224.pcapng"), None),   # sem S_KEY
    (os.path.join(CAP, "08_Spawns_Mapas", "Tiamaranta_Mesa",
                  "08_Spawns_Mapas_Tiamaranta_Mesa_2026-09-17_07-13-15_00001_20260917071315.pcapng"), None),
]
CLIENTE = os.path.join(RAIZ, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos", "data")
FONTE = os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data")
PRODUTO = os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data")
ARVORES = (FONTE, PRODUTO)
MAPA = 800040000
CORREDOR = 802222
OCUPANTES = ("ELYOS", "ASMODIANS", "BALAUR")
GUARDAS = ("FIGHTER", "PRIEST", "WIZARD", "ASSASSIN", "SEEKER")
PATRULHAM = ("ASSASSIN", "SEEKER")          # medido na 4413: ~35 m e ~12 m
POR_DONO = ("WINDBOX", "CORREDOR")          # ponto muda entre Balaur e raca
SO_DE_RACA = ("TELEPORT", "QUEST")
SIGLA = {"L": 0, "Li": 0, "D": 1, "Da": 1, "Dr": 2}
TAMANHO = {"S": 40000, "Small": 40000, "M": 4410, "Middle": 4410, "L": 4400, "Large": 4400, "Big": 4400}
# WindBox da fase de raca das Greater (LDF4b_WindBox_Setting_Tower_L_<n>_UP): nas capturas convive com o WindBox normal
# (4402 Asmodiana e 4403 Elyos, 2,5-3,8 m em x) e nao aparece com Balaur. A 4401 nunca foi vista de raca com ele na visao;
# o ponto vem do dump oficial do SpawnParser (spawn_0_Monster/NPC.xml, 2026-09-16), o mesmo padrao de deslocamento.
WINDBOX_UP_SEM_CAPTURA = {4401: dict(x=1089.7, y=1514.4, z=282.1, h=0)}
# NPC de quest nasce pela base com tribo GENERAL/GENERAL_DARK, e o checkSiegeRelation torna esse NPC atacavel para a
# outra raca. O oficial manda o NPC de quest da raca inimiga como FRIEND (tipo 38 em 35 de 37 S_PUT_NPC, 2 em PEACE):
# USEALL e amigo das duas racas e fica fora do checkSiegeRelation.
TRIBO_QUEST = "USEALL"
PAPEL_GUARDA = {"As": "ASSASSIN", "Fi": "FIGHTER", "Pr": "PRIEST", "Wi": "WIZARD", "Seeker": "SEEKER"}
# irmao que ja existe nos dois npc_templates e serve de molde para criar o que faltar (mesmo papel e dono)
MOLDE = {("BOSS", 0): 274208, ("BOSS", 1): 274213, ("BOSS", 2): 274218,
         ("ASSASSIN", 0): 274219, ("ASSASSIN", 1): 274223, ("ASSASSIN", 2): 274227,
         ("FIGHTER", 0): 274220, ("FIGHTER", 1): 274224, ("FIGHTER", 2): 274228,
         ("PRIEST", 0): 274221, ("PRIEST", 1): 274225, ("PRIEST", 2): 274229,
         ("WIZARD", 0): 274222, ("WIZARD", 1): 274226, ("WIZARD", 2): 274230,
         ("SEEKER", 0): 274231, ("SEEKER", 1): 274232, ("SEEKER", 2): 274233,
         ("TORRE", 0): 802313, ("TORRE", 1): 802314, ("TORRE", 2): 802315,
         ("QUEST", 0): 802235, ("QUEST", 1): 802257,
         ("WINDBOX", None): 802282, ("WINDBOX_UP", None): 802282, ("MISTON", None): 802366, ("TELEPORT", None): 802456,
         ("CORREDOR", None): 802222}
# guarnicao por tamanho, confirmada entre torres independentes: Greater 4401 = 4402, Medium 4413 = 4414, Lesser
# 40008 = 40010 = 40012 (e depois 4403, 4411, 4412, 40001, 40002, 40005 na captura de 17/09)
GUARNICAO = {"L": dict(FIGHTER=5, PRIEST=5, WIZARD=8, ASSASSIN=3, SEEKER=1),
             "M": dict(FIGHTER=6, PRIEST=5, WIZARD=5, ASSASSIN=2, SEEKER=1),
             "S": dict(FIGHTER=2, PRIEST=2, WIZARD=2, ASSASSIN=1, SEEKER=1)}


def tamanho_de(torre):
    return "L" if 4400 < torre < 4410 else "M" if 4410 < torre < 4420 else "S" if 40000 < torre < 40100 else None


# ---------------------------------------------------------------- cliente
def le_cliente():
    """npcId -> dict(name, desc, npc_title, front, side, upper) com o bound ja na convencao do emulador."""
    out, buf, dentro = {}, [], False
    for linha in open(os.path.join(CLIENTE, "npcs", "client_npcs.xml"), encoding="utf-8", errors="replace"):
        if "<npc_client>" in linha:
            buf, dentro = [], True
            continue
        if not dentro:
            continue
        buf.append(linha)
        if "</npc_client>" not in linha:
            continue
        b, dentro = "".join(buf), False
        mi, mn = re.search(r"<id>(\d+)</id>", b), re.search(r"<name>(.*?)</name>", b)
        if not (mi and mn and mn.group(1).startswith("LDF4b_") or (mi and mi.group(1) == str(CORREDOR))):
            continue
        g = lambda c: (re.search(r"<%s>(.*?)</%s>" % (c, c), b, re.S).group(1).strip()
                       if re.search(r"<%s>(.*?)</%s>" % (c, c), b, re.S) else None)
        br = re.search(r"<bound_radius>\s*<front>([\d.]+)</front>\s*<side>([\d.]+)</side>\s*<upper>([\d.]+)</upper>", b)
        sc = int(g("scale") or 100)
        d = dict(name=mn.group(1), desc=g("desc"), npc_title=g("npc_title"))
        if br:
            f, s, u = map(float, br.groups())
            d.update(front=f * sc / 200, side=s * sc / 200, upper=u * sc / 100)
        out[int(mi.group(1))] = d
    return out


def le_mundo():
    """npcId -> [(x, y, z, abyss_info)] dos <npc_info> de Tiamaranta que so existem com um dono (ALi, ADa, ADr)."""
    caminho = os.path.join(CLIENTE, "world", "client_world_ldf4b.xml")
    bruto = open(caminho, "rb").read()
    import aion_bxml
    texto = aion_bxml.decodifica(bruto) if aion_bxml.e_bxml(caminho) else bruto.decode("utf-8", "ignore")
    out = collections.defaultdict(list)
    for m in re.finditer(r"<npc_info>(.*?)</npc_info>", texto, re.S):
        dono = re.search(r"<abyss_info>([^<]*)</abyss_info>", m.group(1))
        if not dono:
            continue
        n = int(re.search(r"<nameid>(\d+)</nameid>", m.group(1)).group(1))
        x, y, z = (float(v) for v in re.search(r"<x>([^<]+)</x>\s*<y>([^<]+)</y>\s*<z>([^<]+)</z>", m.group(1)).groups())
        out[n].append((x, y, z, dono.group(1)))
    return out


MUNDO = {}


def le_strings():
    """STR_... -> id, de todos os client_strings."""
    out = {}
    pasta = os.path.join(CLIENTE, "Strings")
    for arq in os.listdir(pasta):
        if not arq.endswith(".xml"):
            continue
        t = open(os.path.join(pasta, arq), encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", t):
            out.setdefault(m.group(2).strip().upper(), int(m.group(1)))
    return out


def papel_de(nome):
    """(torre, papel, dono, variante) pelo nome interno; torre None para o corredor."""
    m = re.match(r"LDF4b_Tower_([SML])_(\d+)_(L|D|Dr)$", nome)
    if m:
        return TAMANHO[m.group(1)] + int(m.group(2)), "TORRE", SIGLA[m.group(3)], None
    m = re.match(r"LDF4b_(\d{4,5})_Boss_(Li|Da|Dr)_(\d)$", nome)
    if m:
        return int(m.group(1)), "BOSS", SIGLA[m.group(2)], m.group(3)
    m = re.match(r"LDF4b_(\d{4,5})_Guard_((?:Mist(?:On|Off)_)?)(Li|Da|Dr)_(As|Fi|Pr|Wi|Seeker)$", nome)
    if m:
        return int(m.group(1)), PAPEL_GUARDA[m.group(4)], SIGLA[m.group(3)], m.group(2)
    m = re.match(r"LDF4b_WindBox_Setting_Tower_([SML])_(\d+)(_UP)?$", nome)
    if m:
        return TAMANHO[m.group(1)] + int(m.group(2)), "WINDBOX_UP" if m.group(3) else "WINDBOX", None, None
    m = re.match(r"LDF4b_MistOn_Tower_([SML])_(\d+)$", nome)
    if m:
        return TAMANHO[m.group(1)] + int(m.group(2)), "MISTON", None, None
    m = re.match(r"LDF4b_(Small|Middle|Large|Big)Tower_Teleport_(\d+)$", nome)
    if m:
        return TAMANHO[m.group(1)] + int(m.group(2)), "TELEPORT", None, None
    m = re.match(r"LDF4b_Quest_NPC_(Li|Da)_(Small|Middle|Large|Big)_(\d+)$", nome)
    if m:
        return TAMANHO[m.group(2)] + int(m.group(3)), "QUEST", SIGLA[m.group(1)], None
    if nome == "LDF4b_Placeable_OBJ_LINK_Noshow_NPC":
        return None, "CORREDOR", None, None
    return None, None, None, None


def catalogo(cli):
    """(torre, papel, dono, variante) -> npcId, para espelhar um papel medido numa raca nas outras."""
    cat = {}
    for npc, d in cli.items():
        t, r, dono, var = papel_de(d["name"])
        if r and t is not None:
            cat[(t, r, dono, var)] = npc
    return cat


# ---------------------------------------------------------------- captura
class Cifra:
    def __init__(self, chave):
        self.key = bytearray(struct.pack("<Q", chave))

    def decrypt(self, dados):
        d, primeiro = bytearray(dados), self.key[0]
        for i in range(len(d) - 1, 0, -1):
            d[i] ^= self.key[i & 7] ^ aion_pcap.STATIC_KEY[i & 63] ^ d[i - 1]
        self.key[:] = struct.pack("<Q", (struct.unpack("<Q", bytes(self.key))[0] + len(d)) & 0xFFFFFFFFFFFFFFFF)
        if d:
            d[0] ^= primeiro
        return bytes(d)


def sessoes(caminho, chave):
    """Uma lista de pacotes do servidor (opcode, payload) por sessao."""
    if chave is None:
        for s in aion_pcap.abre_todas(caminho, sem_skey=True):
            yield [(op, p) for op, p, _ in s["servidor"]]
        return
    todos = aion_pcap.fluxos(caminho, 7777, com_tempo=True)
    lado = next((k for k in todos if k[1] == 7777), None)
    fluxo, _ = todos[lado]
    cifra, off, pk = Cifra(chave), 0, []
    while off + 2 <= len(fluxo):
        ln = struct.unpack_from("<H", fluxo, off)[0]
        if ln < 7 or off + ln > len(fluxo):
            break
        c = cifra.decrypt(fluxo[off + 2: off + ln])
        op, _s, chk = struct.unpack_from("<HBH", c, 0)
        if chk == (~op & 0xFFFF):
            pk.append((aion_pcap.opcode_servidor(op), c[5:]))
        off += ln
    yield pk


def le_put(p):
    x, y, z, oid, npc = struct.unpack_from("<fffII", p, 0)
    if not all(map(math.isfinite, (x, y, z))):
        return None
    if len(p) < 107 or struct.unpack_from("<I", p, 43)[0]:
        return None                                   # curto demais, ou invocacao de jogador (criador != 0)
    cauda, off = p[-48:], 47
    while p[off:off + 2] != b"\0\0":                  # nome do dono: UTF-16 terminado em 00 00, vazio fora de invocacao
        off += 2
        if off + 2 > len(p):
            return None
    off += 2
    return dict(npc=npc, oid=oid, x=x, y=y, z=z, h=p[27], nome_id=struct.unpack_from("<I", p, 28)[0],
                titulo=struct.unpack_from("<I", p, 32)[0], nasceu=cauda[16] == 1,
                static=struct.unpack_from("<H", cauda, 30)[0], raio=struct.unpack_from("<f", cauda, 0)[0],
                alt=struct.unpack_from("<f", cauda, 4)[0], lvl=p[off + 5], maxhp=struct.unpack_from("<I", p, off + 1)[0])


def colhe(cli):
    """Todos os objetos de torre das capturas, com dono do instante e movimento."""
    centros, objetos = {}, {}
    for n, (caminho, chave) in enumerate(CAPTURAS):
        for s, pk in enumerate(sessoes(caminho, chave)):
            dono, moveu = {}, set()
            for op, p in pk:
                if op == 0xD0 and len(p) >= 3:
                    q = struct.unpack_from("<H", p, 1)[0]
                    if q and (len(p) - 3) % q == 0:
                        sz = (len(p) - 3) // q
                        for i in range(q):
                            e = p[3 + i * sz: 3 + (i + 1) * sz]
                            dono[struct.unpack_from("<I", e, 0)[0]] = e[16]
                elif op == 0x37 and len(p) >= 4:
                    moveu.add(struct.unpack_from("<I", p, 0)[0])
                elif op == 0x0E and len(p) >= 49:
                    d = le_put(p)
                    if d is None or d["npc"] not in cli:
                        continue
                    t, r, don, var = papel_de(cli[d["npc"]]["name"])
                    if r is None:
                        continue
                    if r == "TORRE":
                        centros[t] = (d["x"], d["y"], d["z"])
                    if don is not None and t is not None:
                        # a captura de 13/09 comeca sem a lista do login: o dono sai do NPC de raca que aparece
                        dono[t] = don
                    if r == "CORREDOR":
                        if not centros:
                            continue
                        t = min(centros, key=lambda c: math.dist(centros[c][:2], (d["x"], d["y"])))
                        if math.dist(centros[t][:2], (d["x"], d["y"])) > 40:
                            continue
                    if don is None:
                        don = dono.get(t)
                        if don is None and r in POR_DONO:
                            continue            # sem saber o dono nao da para dizer de qual fase e o ponto
                    o = objetos.setdefault((n, s, d["oid"]), dict(torre=t, papel=r, dono=don, var=var, npc=d["npc"], vistos=[]))
                    d["dono"] = don
                    o["vistos"].append(d)
            for (cn, cs, oid), o in objetos.items():
                if cn == n and cs == s and oid in moveu:
                    o["moveu"] = True
    return centros, objetos


# ---------------------------------------------------------------- canonizacao
def canoniza(objetos):
    """torre -> papel -> classe_de_dono -> {chave: ponto}; e as medidas por (torre, papel, variante)."""
    pontos = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
    medidas, donos_vistos, aproximados = {}, collections.defaultdict(set), []
    for o in objetos.values():
        vs = o["vistos"]
        base = next((v for v in vs if v["nasceu"]), vs[0])
        raio = max(math.dist((base["x"], base["y"]), (v["x"], v["y"])) for v in vs)
        anda = o.get("moveu") or raio > 0.3
        t, r = o["torre"], o["papel"]
        donos_vistos[t].add(base["dono"])
        medidas.setdefault((t, r, o["var"] if r != "BOSS" else None), dict(lvl=base["lvl"], maxhp=base["maxhp"]))
        medidas.setdefault(("npc", o["npc"]), dict(lvl=base["lvl"], maxhp=base["maxhp"], titulo=base["titulo"], nome_id=base["nome_id"]))
        if r in GUARDAS or r in ("BOSS", "TORRE", "MISTON"):
            classe = "TODOS"
        elif r in POR_DONO:
            classe = "BALAUR" if base["dono"] == 2 else "RACA"
        else:
            classe = "RACA"
        qualidade = 2 if base["nasceu"] else (1 if not anda else 0)
        chave = (round(base["x"], 1), round(base["y"], 1))
        ant = pontos[t][r][classe].get(chave)
        novo = dict(x=base["x"], y=base["y"], z=base["z"], h=base["h"], static=base["static"], raio=raio,
                    q=qualidade, var=o["var"], dono=base["dono"], papel=r)
        if ant is None or (qualidade, raio) > (ant["q"], ant["raio"]):
            pontos[t][r][classe][chave] = novo
    # fica so o melhor nivel de evidencia de cada papel; patrulha vista no meio do caminho so entra se nao houver outra
    for t in pontos:
        for r in pontos[t]:
            for classe, mapa in pontos[t][r].items():
                melhor = max((p["q"] for p in mapa.values()), default=0)
                # com nascimento, o que foi visto andando e o mesmo NPC fora do ponto (4413). Sem nascimento, cada
                # objeto em movimento e um guarda distinto (4402: guerreiro deslocado 2,7 m num ponto que nenhum
                # parado ocupa), entao fica, com o primeiro avistamento como ponto.
                # quem patrulha e foi visto nascer: so o nascimento vale -- parado uma vez no caminho nao e ponto
                corte = (2 if r in PATRULHAM else 1) if melhor == 2 else 0
                for k in [k for k, p in mapa.items() if p["q"] < corte]:
                    del mapa[k]
    # guarda fixo visto so andando e abaixo do piso mais baixo com guarda parado foi arrastado em combate, nao e posto.
    # Nas duas Greater (4401 e 4402) isso tira exatamente os que estavam 15-20 m abaixo do piso, e as duas ficam com a
    # mesma guarnicao: 5 guerreiros, 5 sacerdotes, 8 magos, 3 assassinos e 1 seeker.
    for t in pontos:
        pisos = [p["z"] for r in GUARDAS if r not in PATRULHAM
                 for p in pontos[t].get(r, {}).get("TODOS", {}).values() if p["q"] >= 1]
        if not pisos:
            continue
        piso = min(pisos)
        for r in GUARDAS:
            if r in PATRULHAM:
                continue
            mapa = pontos[t].get(r, {}).get("TODOS", {})
            for k in [k for k, p in mapa.items() if p["q"] == 0 and p["z"] < piso - 5]:
                del mapa[k]
    # com mais capturas, o mesmo guarda visto andando em lugares diferentes virava guarda a mais (4401 com 28 e 4402 com
    # 31 depois da captura de 17/09). A guarnicao de cada tamanho de torre e a mesma entre torres independentes, entao
    # acima dela sai primeiro o ponto so visto andando que esta mais perto de outro da mesma classe; parado e nascimento
    # nunca saem.
    for t in pontos:
        esperado = GUARNICAO.get(tamanho_de(t))
        if not esperado:
            continue
        for r in GUARDAS:
            mapa = pontos[t].get(r, {}).get("TODOS", {})
            while len(mapa) > esperado[r]:
                andando = [k for k, p in mapa.items() if p["q"] == 0]
                if not andando:
                    break
                vizinho = lambda k: min((math.dist(k, o) for o in mapa if o != k), default=float("inf"))
                del mapa[min(andando, key=vizinho)]
    for t in pontos:
        for r in pontos[t]:
            for classe, mapa in pontos[t][r].items():
                n_aprox = sum(1 for p in mapa.values() if p["q"] == 0)
                if n_aprox:
                    aproximados.append((t, r, classe, n_aprox))
    return pontos, medidas, donos_vistos, aproximados


# ---------------------------------------------------------------- xml de spawn
def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return s if s else "0"


def spot(p):
    extra = ' static_id="%d"' % p["static"] if p["static"] else ""
    if p["papel"] in PATRULHAM and p["raio"] > 5:   # guerreiro deslocado e combate, nao patrulha
        extra += ' random_walk="%d"' % max(1, round(p["raio"] / math.sqrt(2)))
    return '\t\t\t\t\t<spot x="%s" y="%s" z="%s" h="%d"%s />' % (num(p["x"]), num(p["y"]), num(p["z"]), p["h"], extra)


def grupo(handler, npc, pts, respawn=None):
    r = ' respawn_time="%d"' % respawn if respawn else ""
    pts = sorted(pts, key=lambda p: (-p["z"], p["x"], p["y"]))
    return "\n".join(['\t\t\t\t<spawn handler="%s" npc_id="%d"%s>' % (handler, npc, r)] + [spot(p) for p in pts]
                     + ["\t\t\t\t</spawn>"])


def camps_do_servidor():
    """torre -> (ativa?, dono padrao) do siege_locations.xml."""
    t = open(os.path.join(FONTE, "siege", "siege_locations.xml"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<siege_location id="(\d+)" type="CAMP"[^>]*/>', t):
        a = m.group(0)
        reset = int(re.search(r'camp_reset_time="(\d+)"', a).group(1))
        dono = re.search(r'camp_default_race="(\w+)"', a).group(1)
        out[int(m.group(1))] = (reset > 0, dono)
    return out


def monta_torre(t, pontos, cat, camps, rel):
    ativa, dono_fixo = camps[t]
    ocupantes = OCUPANTES if ativa else (dono_fixo,)
    corpo = []
    for ocupante in ocupantes:
        i = OCUPANTES.index(ocupante)
        blocos = []

        def pega(papel, classe):
            mapa = pontos[t].get(papel, {})
            pts = list(mapa.get(classe, {}).values())
            if not pts and classe in ("RACA", "BALAUR"):       # a outra classe e melhor que nada
                outra = "BALAUR" if classe == "RACA" else "RACA"
                pts = list(mapa.get(outra, {}).values())
                if pts:
                    rel.append("  %d %s %s: sem ponto de %s, usei o de %s" % (t, ocupante, papel, classe, outra))
            return pts

        def npc_de(papel, var=None):
            npc = cat.get((t, papel, i, var))
            if npc is None and papel in GUARDAS:           # variante de nevoa que nao existe para esta raca
                npc = next((cat[k] for k in cat if k[:3] == (t, papel, i)), None)
            return npc

        classe = "BALAUR" if i == 2 else "RACA"
        estr = pega("TORRE", "TODOS")
        if not estr:
            rel.append("  %d: sem estrutura capturada, torre ignorada" % t)
            return None
        blocos.append(grupo("FLAG", npc_de("TORRE"), estr[:1]))
        if ativa:
            boss = pega("BOSS", "TODOS")
            if boss:
                nivel = boss[0]["var"]
                npc = cat.get((t, "BOSS", i, nivel))
                if npc:
                    blocos.append(grupo("BOSS", npc, boss[:1]))
            mist = pega("MISTON", "TODOS")
            if mist:
                blocos.append(grupo("GUARDIAN", cat[(t, "MISTON", None, None)], mist[:1]))
        for papel in ("WINDBOX", "CORREDOR"):
            pts = pega(papel, classe)
            if pts:
                npc = CORREDOR if papel == "CORREDOR" else cat.get((t, papel, None, None))
                blocos.append(grupo("MERCHANT", npc, pts))
        if i != 2:
            npc = cat.get((t, "WINDBOX_UP", None, None))
            if npc:
                pts = pega("WINDBOX_UP", "RACA")
                if not pts and t in WINDBOX_UP_SEM_CAPTURA:
                    pts = [dict(WINDBOX_UP_SEM_CAPTURA[t], static=0, raio=0, papel="WINDBOX_UP")]
                if pts:
                    blocos.append(grupo("MERCHANT", npc, pts[:1]))
            for papel in SO_DE_RACA:
                npc = cat.get((t, papel, None if papel == "TELEPORT" else i, None))
                pts = pega(papel, "RACA")
                if not pts and npc:
                    # a captura nao viu esta torre com dono de raca: o npc_info do cliente marca o ponto com abyss_info
                    pts = [dict(x=x, y=y, z=z, h=0, static=0, raio=0, papel=papel)
                           for x, y, z, dono in MUNDO.get(npc, []) if dono == ("ALi", "ADa")[i]]
                    if pts:
                        rel.append("  %d %s %s: ponto do client_world (abyss_info), sem captura" % (t, ocupante, papel))
                if pts and npc:
                    blocos.append(grupo("MERCHANT", npc, pts[:1]))
        for papel in GUARDAS:
            pts = pega(papel, "TODOS")
            if not pts:
                continue
            var = pts[0]["var"]
            npc = npc_de(papel, var)
            if npc:
                blocos.append(grupo("SENTINEL", npc, pts, 60))
        corpo.append('\t\t\t<occupier_template occupier="%s">\n%s\n\t\t\t</occupier_template>' % (ocupante, "\n".join(blocos)))
    return '\t\t<base_spawn id="%d">\n%s\n\t\t</base_spawn>' % (t, "\n".join(corpo))


# ---------------------------------------------------------------- templates
def bloco_template(texto, npc):
    m = re.search(r'(\t?<npc_template npc_id="%d"[ >].*?</npc_template>)' % npc, texto, re.S)
    return m.group(1) if m else None


def ajusta(bloco, npc, cli, strings, medida, criando=False, padrao=None):
    """Aplica ao bloco (existente ou copiado do molde) o que o cliente e a captura dizem deste npcId."""
    d = cli[npc]
    novo = re.sub(r'(<npc_template npc_id=")\d+(")', lambda m: m.group(1) + str(npc) + m.group(2), bloco, count=1)
    cab = novo.split(">")[0]

    def atr(nome, valor):
        nonlocal novo, cab
        if valor is None:
            return
        if re.search(r'\b%s="' % nome, cab):
            novo = re.sub(r'(\b%s=")[^"]*(")' % nome, lambda m: m.group(1) + str(valor) + m.group(2), novo, count=1)
        else:
            novo = re.sub(r'(<npc_template npc_id="\d+")', lambda m: m.group(1) + ' %s="%s"' % (nome, valor), novo, count=1)
        cab = novo.split(">")[0]

    nome_id = medida.get("nome_id") or strings.get((d.get("desc") or "").upper())
    titulo = medida.get("titulo")
    if titulo is None:
        titulo = strings.get((d.get("npc_title") or "").upper(), 0)
    if criando:            # template que ja existe fica com o nome dele (a localizacao pt-BR traduz esse campo)
        atr("name", d["name"])
    atr("name_id", nome_id)
    for nome_atr, valor in (padrao or {}).items():
        atr(nome_atr, valor)
    atr("title_id", titulo)
    atr("level", medida.get("lvl"))
    if "upper" in d:
        atr("height", num(d["upper"]))
        alvo = '<bound_radius front="%s" side="%s" upper="%s" />' % (num(d["front"]), num(d["side"]), num(d["upper"]))
        novo = re.sub(r"<bound_radius[^/]*/>", alvo, novo, count=1)
    if medida.get("maxhp"):
        novo = re.sub(r'(maxHp=")[^"]*(")', lambda m: m.group(1) + str(medida["maxhp"]) + m.group(2), novo, count=1)
    return novo


def insere(texto, npc, bloco):
    bloco = "\t" + bloco.lstrip("\t")
    for m in re.finditer(r'\t<npc_template npc_id="(\d+)"', texto):
        if int(m.group(1)) > npc:
            return texto[:m.start()] + bloco + "\n" + texto[m.start():]
    fim = texto.rindex("</npc_templates>")
    return texto[:fim] + bloco + "\n" + texto[fim:]


def comportamento_do_molde(molde, papel):
    """tribo, ai e tipo do molde (4413, a torre validada em jogo); raca so para guarda e Watching Eye, que tem uma por dono.

    Os templates herdados divergiam entre torres: Watching Eye Balaur da 40001/40002 com GENERAL/general (verde, nao
    atacavel para Elyos -- o oficial manda tipo 0), guardas de raca com ai general (nunca atacam), teleporte com tribo
    GENERAL (atacavel pela outra raca pelo checkSiegeRelation)."""
    if not molde:
        return {}
    cab = dict(re.findall(r'(\w+)="([^"]*)"', re.match(r"\t?<npc_template\b[^>]*>", molde).group(0)))
    chaves = ("tribe", "ai", "type") + (("race",) if papel in GUARDAS or papel == "BOSS" else ())
    padrao = {k: cab[k] for k in chaves if k in cab}
    if papel == "QUEST":
        padrao["tribe"] = TRIBO_QUEST
    return padrao


def templates(usados, cli, cat, strings, medidas, seco):
    inv = {v: k for k, v in cat.items()}
    for arvore in ARVORES:
        caminho = os.path.join(arvore, "npcs", "npc_templates.xml")
        texto = novo = open(caminho, encoding="utf-8", errors="replace").read()
        criados, corrigidos, sem_molde = [], 0, []
        for npc in sorted(usados):
            chave = inv.get(npc, (None, "CORREDOR", None, None))
            t, papel, dono, var = chave
            medida = dict(medidas.get(("npc", npc), {}))
            geral = medidas.get((t, papel, var if papel != "BOSS" else None)) or {}
            for k in ("lvl", "maxhp"):
                medida.setdefault(k, geral.get(k))
            existente = bloco_template(novo, npc)
            molde_id = MOLDE.get((papel, dono)) or MOLDE.get((papel, None))
            molde = bloco_template(novo, molde_id) if molde_id else None
            padrao = comportamento_do_molde(molde, papel)
            if existente:
                ajustado = ajusta(existente, npc, cli, strings, medida, padrao=padrao)
                if ajustado != existente:
                    novo = novo.replace(existente, ajustado, 1)
                    corrigidos += 1
                continue
            if not molde:
                sem_molde.append(npc)
                continue
            novo = insere(novo, npc, ajusta(molde, npc, cli, strings, medida, criando=True, padrao=padrao))
            criados.append(npc)
        antes, depois = len(re.findall(r"<npc_template npc_id=", texto)), len(re.findall(r"<npc_template npc_id=", novo))
        if depois != antes + len(criados) or not novo.rstrip().endswith("</npc_templates>"):
            sys.exit("ABORTADO: %s ficaria com %d templates (esperado %d)" % (caminho, depois, antes + len(criados)))
        print("   %s\n      criados %d, corrigidos %d%s" % (caminho, len(criados), corrigidos,
              (", SEM MOLDE: %s" % sem_molde) if sem_molde else ""))
        if not seco and novo != texto:
            open(caminho, "w", encoding="utf-8", newline="\n").write(novo)


# ---------------------------------------------------------------- spawn comum e base_locations
def limpa_spawn_comum(torres, centros, cli, seco, balaur_fixo=()):
    """Tira do spawn comum do mapa o que agora nasce pela base: NPC da torre (pelo nome) e corredor a ate 40 m.

    Tambem sai o que so existe com dono de raca (estatua, NPC de quest, WindBox _UP) das torres que sao sempre Balaur
    (camp_default_race BALAUR sem camp_reset_time; no S_ABYSS_INFO oficial elas vem com dono 2 e sem ciclo)."""
    for arvore in ARVORES:
        caminho = os.path.join(arvore, "spawns", "Npcs", "800040000_Tiamaranta_Mesa.xml")
        texto = novo = open(caminho, encoding="utf-8", errors="replace").read()
        tirados = collections.Counter()
        for m in list(re.finditer(r'\t\t<spawn npc_id="(\d+)"[^>]*>(.*?)</spawn>\n', texto, re.S)):
            npc = int(m.group(1))
            nome = cli.get(npc, {}).get("name", "")
            t, papel, _d, _v = papel_de(nome) if nome else (None, None, None, None)
            if papel is None:
                continue
            so_de_raca = t in balaur_fixo and (papel in SO_DE_RACA or papel == "WINDBOX_UP")
            spots = re.findall(r'\t\t\t<spot [^>]*/>\n', m.group(2))
            fica = []
            for s in spots:
                x, y = float(re.search(r'x="([^"]+)"', s).group(1)), float(re.search(r'y="([^"]+)"', s).group(1))
                dono_do_ponto = t if t is not None else min(centros, key=lambda c: math.dist(centros[c][:2], (x, y)))
                perto = t is not None or math.dist(centros[dono_do_ponto][:2], (x, y)) <= 40
                if (dono_do_ponto in torres and perto) or so_de_raca:
                    tirados[npc] += 1
                else:
                    fica.append(s)
            if len(fica) == len(spots):
                continue
            substituto = "" if not fica else m.group(0).replace(m.group(2), "\n" + "".join(fica) + "\t\t")
            novo = novo.replace(m.group(0), substituto, 1)
        print("   %s\n      spots removidos: %d em %d NPCs" % (caminho, sum(tirados.values()), len(tirados)))
        if not seco and novo != texto:
            open(caminho, "w", encoding="utf-8", newline="\n").write(novo)


SPOT_BASE = re.compile(r'(<spot x="([^"]+)" y="([^"]+)" z=")([^"]+)(" h=")(\d+)(")')


def spots_por_npc(texto):
    """(npc_id, x, y) -> (z, h) de cada spot do arquivo de base."""
    out = {}
    for m in re.finditer(r'<spawn [^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', texto, re.S):
        for s in SPOT_BASE.finditer(m.group(2)):
            out[(m.group(1), s.group(2), s.group(3))] = (s.group(4), s.group(6))
    return out


def ajustes_manuais(caminho):
    """z/h de cada spot que o arquivo ja tem. O //fixspawn so muda z/h, e dado novo de captura muda x/y; entao spot do
    mesmo npc e x/y fica com o z/h do arquivo -- comparar com o HEAD perdia o ajuste assim que ele era commitado."""
    if not os.path.exists(caminho):
        return {}
    return spots_por_npc(open(caminho, encoding="utf-8").read())


def reaplica(xml, ajustes):
    """xml com o z/h do arquivo nos spots de mesmo npc_id e x/y; devolve tambem quantos o gerador teria mudado."""
    aplicados = 0

    def no_bloco(m):
        def no_spot(s):
            nonlocal aplicados
            v = ajustes.get((m.group(1), s.group(2), s.group(3)))
            if not v or v == (s.group(4), s.group(6)):
                return s.group(0)
            aplicados += 1
            return s.group(1) + v[0] + s.group(5) + v[1] + s.group(7)
        return m.group(0).replace(m.group(2), SPOT_BASE.sub(no_spot, m.group(2)))
    return re.sub(r'<spawn [^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', no_bloco, xml, flags=re.S), aplicados


def grava_base_locations(torres, camps, seco):
    for arvore in ARVORES:
        caminho = os.path.join(arvore, "base", "base_locations.xml")
        texto = open(caminho, encoding="utf-8").read()
        # tira todo base_location do mapa e os dois comentarios que ja marcaram o bloco; so tirar o comentario antigo
        # duplicava o bloco a cada execucao (4401 chegou a 4 entradas)
        texto = re.sub(r'\t<!-- Tiamaranta Mesa[^\n]*-->\n', "", texto)
        texto = re.sub(r'\t<base_location [^>]*world="%d"[^>]*/>\n' % MAPA, "", texto)
        linhas = ["\t<!-- Tiamaranta Mesa: torres do camp war com guarnicao capturada (fix_50_tiamaranta_torres.py) -->"]
        for t in sorted(torres):
            linhas.append('\t<base_location id="%d" type="CASUAL" world="%d" default_occupier="%s" />' % (t, MAPA, camps[t][1]))
        novo = texto.replace("</base_locations>", "\n".join(linhas) + "\n</base_locations>", 1)
        if not seco:
            open(caminho, "w", encoding="utf-8", newline="\n").write(novo)
        print("   " + caminho)


# ---------------------------------------------------------------- main
def main():
    seco = "--dry" in sys.argv
    print("1. Cliente...")
    cli, strings = le_cliente(), le_strings()
    cat = catalogo(cli)
    MUNDO.update(le_mundo())
    camps = camps_do_servidor()
    print("   %d NPCs de LDF4b, %d strings, %d torres no siege_locations" % (len(cli), len(strings), len(camps)))

    print("2. Capturas...")
    centros, objetos = colhe(cli)
    pontos, medidas, donos, aproximados = canoniza(objetos)

    print("3. Torres...")
    rel, blocos, usados, torres = [], [], set(), []
    for t in sorted(pontos):
        if t not in camps:
            continue
        guardas = sum(len(pontos[t].get(r, {}).get("TODOS", {})) for r in GUARDAS)
        if not guardas:
            rel.append("  %d: sem guarnicao capturada, torre ignorada" % t)
            continue
        b = monta_torre(t, pontos, cat, camps, rel)
        if not b:
            continue
        blocos.append(b)
        torres.append(t)
        usados.update(int(n) for n in re.findall(r'npc_id="(\d+)"', b))
        print("   %-6d %-7s donos capturados=%-18s guardas=%d" % (t, "ativa" if camps[t][0] else "fixa",
              sorted({("ELY", "ASM", "BAL")[d] for d in donos[t] if d is not None}), guardas))
    for t, r, classe, n in aproximados:
        if t in torres:
            rel.append("  %d %s: %d ponto(s) aproximado(s), so visto patrulhando (sem nascimento nem parado)" % (t, r, n))

    xml = ("<?xml version='1.0' encoding='utf-8'?>\n"
           '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../spawns.xsd">\n'
           '\t<spawn_map map_id="%d">\n'
           "\t\t<!-- Torres Watching Eye de Tiamaranta Mesa. x/y/z/heading/static_id lidos dos S_PUT_NPC oficiais 5.0.\n"
           "\t\t     Gerado por 6 - Ferramentas/parsersXML/fix_50_tiamaranta_torres.py; nao editar a mao. -->\n"
           "%s\n\t</spawn_map>\n</spawns>\n") % (MAPA, "\n".join(blocos))
    for arvore in ARVORES:
        caminho = os.path.join(arvore, "spawns", "Bases", "800040000_Tiamaranta.xml")
        ajustes = ajustes_manuais(caminho)
        final, aplicados = reaplica(xml, ajustes)
        if not seco:
            open(caminho, "w", encoding="utf-8", newline="\n").write(final)
        print("   %s\n      z/h do arquivo mantido (//fixspawn): %d spot(s)" % (caminho, aplicados))

    print("4. base_locations...")
    grava_base_locations(torres, camps, seco)
    print("5. Spawn comum do mapa...")
    limpa_spawn_comum(set(torres), centros, cli, seco, {t for t, (ativa, dono) in camps.items() if not ativa and dono == "BALAUR"})
    print("6. Templates (por arvore)...")
    templates(usados, cli, cat, strings, medidas, seco)
    if rel:
        print("Observacoes:")
        print("\n".join(sorted(set(rel))))


if __name__ == "__main__":
    main()
