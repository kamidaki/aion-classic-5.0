"""Ataque básico de NPC como o oficial: alcance, animações (hitpoint) e velocidade do projétil, pelo cliente 5.0.

Uso: fix_50_npc_ataque.py [--aplica]   (sem --aplica só mostra; edita as duas árvores, só o cabeçalho <npc_template>)

Prova (S_ATTACK oficial, opcode 54, 1.172 ataques de 51 tipos de mob nas capturas de 10/2026):
  [D atacante][C nº][H time][C tipo][C mão][D alvo]...
  - mão = qual animação de ataque toca: 0 -> cattack_<arma>_001, 1 -> _002, 2 -> _003; o oficial sorteia só entre as que o
    modelo tem (a Balic Aether Cannon, que só tem _001, recebe sempre 0);
  - time = hitpoint (ms) dessa animação no data/AnimationMarkers/<modelo>.xml (+ distância / ammo_speed nos de longe);
    551 de 556 ataques oficiais batem;
  - tipo = 0 sempre.
Modelo: <mesh>, senão o último pedaço de <dir>; NPC humano (sem dir/mesh) usa o arquivo do personagem pelo <pc_type>
(Light_m -> lm, Light_f -> lf, Dark_m -> dm, Dark_f -> df). Arma: weapon_type do item <main> do <visible_equipments>
(bow, 2h_orb -> orb, 2h_staff -> staff, 2h_book -> book, 2h_* -> 2hand, 1h_* -> 1hand, duas de 1h -> 2weapon, nenhuma -> noweapon);
se o modelo não tem a categoria, noweapon.

Grava no <npc_template>:
  - arange: só quando falta e o cliente tem <attack_range> > 0 (sem arange o servidor usa alcance 0 e o mob nunca ataca);
  - attack_anims="h1,h2[,h3]": hitpoints em ms;
  - ammo_speed: o <ammo_speed> do cliente, quando houver.
"""
import os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CLIENTE = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data")
ARVORES = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "npcs", "npc_templates.xml"),
           os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "npcs", "npc_templates.xml")]
PC = {"light_m": "lm", "light_f": "lf", "dark_m": "dm", "dark_f": "df"}
CAT = {"bow": "bow", "2h_orb": "orb", "2h_staff": "staff", "2h_book": "book"}


def cliente():
    t = open(os.path.join(CLIENTE, "npcs", "client_npcs.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for b in re.findall(r"(?s)<npc_client>.*?</npc_client>", t):
        g = lambda k: (re.search(r"<%s>([^<]*)</%s>" % (k, k), b) or [None, None])[1]
        ve = re.search(r"(?s)<visible_equipments>(.*?)</visible_equipments>", b)
        out[int(g("id"))] = dict(dir=g("dir"), mesh=g("mesh"), pc=g("pc_type"), ar=g("attack_range"), ammo=g("ammo_speed"),
                                 main=(re.search(r"<main>([^<]+)</main>", ve.group(1)) or [None, None])[1] if ve else None,
                                 sub=(re.search(r"<sub>([^<]+)</sub>", ve.group(1)) or [None, None])[1] if ve else None)
    return out


def itens():
    t = open(os.path.join(CLIENTE, "items", "client_items.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for b in re.findall(r"(?s)<client_item>.*?</client_item>", t):
        n, w = re.search(r"<name>([^<]+)</name>", b), re.search(r"<weapon_type>([^<]+)</weapon_type>", b)
        if n:
            out[n.group(1).lower()] = w.group(1).lower() if w else None
    return out


_marc = {}


def marcadores(nome):
    if nome not in _marc:
        f, r = os.path.join(CLIENTE, "AnimationMarkers", nome + ".xml"), {}
        if os.path.exists(f):
            t = open(f, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'(?s)<animation animation_length="([^"]*)" name="([^"]*)">(.*?)</animation>', t):
                hp = re.search(r'<hitpoint[^>]*when="([^"]*)"', m.group(3))
                r[m.group(2).lower()] = float(hp.group(1)) if hp else None
        _marc[nome] = r
    return _marc[nome]


def categoria(c, its):
    wm = its.get((c["main"] or "").lower())
    ws = its.get((c["sub"] or "").lower())
    if wm and ws and wm.startswith("1h") and ws.startswith("1h"):
        return "2weapon"
    if not wm:
        return "noweapon"
    return CAT.get(wm) or ("2hand" if wm.startswith("2h") else "1hand" if wm.startswith("1h") else wm)


def animacoes(c, its):
    d = (c["dir"] or "").replace("\\", "/")
    nomes = [c["mesh"], d.split("/")[-1] if d else None]
    if not c["mesh"] and not d and c["pc"]:
        nomes.append(PC.get(c["pc"].lower()))
    for k in nomes:
        m = marcadores(k) if k else {}
        if not m:
            continue
        for cat in (categoria(c, its), "noweapon"):
            l = []
            for i in (1, 2, 3):
                hp = m.get("cattack_%s_%03d" % (cat, i), -1)
                if hp == -1 or hp is None:
                    break
                l.append(int(hp * 1000))   # o oficial trunca: 0,39999998 -> 399
            if l:
                return l
        return []
    return []


def ajusta(cab, c, its, cont):
    novo = cab
    if 'arange="' not in novo and c["ar"] and round(float(c["ar"])) > 0:
        novo = novo.replace(' srange="', ' arange="%d" srange="' % round(float(c["ar"])), 1) if ' srange="' in novo else \
            novo.replace("<npc_template ", '<npc_template arange="%d" ' % round(float(c["ar"])), 1)
        cont["arange posto"] += 1
    l = animacoes(c, its)
    if l:
        v = ",".join(map(str, l))
        novo = re.sub(r'\s*attack_anims="[^"]*"', "", novo)
        novo = re.sub(r"(\s*/?>)$", lambda m: ' attack_anims="%s"' % v + m.group(1), novo, count=1)
        cont["attack_anims (%d)" % len(l)] += 1
    if c["ammo"] and int(float(c["ammo"])) > 0:
        novo = re.sub(r'\s*ammo_speed="[^"]*"', "", novo)
        novo = re.sub(r"(\s*/?>)$", lambda m: ' ammo_speed="%d"' % int(float(c["ammo"])) + m.group(1), novo, count=1)
        cont["ammo_speed"] += 1
    return novo


def main():
    cli, its = cliente(), itens()
    for arq in ARVORES:
        t = open(arq, encoding="utf-8", newline="").read()
        cont = {}
        cont_ = __import__("collections").Counter()

        def troca(m):
            cab = m.group(0)
            i = int(re.search(r'npc_id="(\d+)"', cab).group(1))
            return ajusta(cab, cli[i], its, cont_) if i in cli else cab
        novo = re.sub(r"<npc_template\b[^>]*>", troca, t)
        print(arq[-80:], dict(cont_))
        if "--aplica" in sys.argv and novo != t:
            open(arq, "w", encoding="utf-8", newline="").write(novo)


if __name__ == "__main__":
    main()
