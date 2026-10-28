"""Tira das ilhas de Tiamaranta Mesa os mobs genéricos que o oficial troca pela versão "Island of ...".

Uso: limpa_genericos_ilhas_tiamaranta.py [--aplica]   (sem --aplica só mostra)

Prova (capturas oficiais de 15-17/09 e 28/10, 367 aparições de mobs de ilha):
  - as ilhas são as subzonas LDF4b_SZ_Island_* do client_world_ldf4b.xml (polígono + bottom/top);
  - dentro delas o oficial só mostra a versão de ilha (LDF4b_Island_<tipo>_65) e nenhuma vez a genérica
    (LDF4b_<tipo>_58/59/60), que o mission_mission0.xml ainda põe lá;
  - fora das ilhas as genéricas existem no oficial (Enraged Maeki, Flame Leowasp, Leuco Skyray...), então só sai o spot dentro.
Genérica <-> ilha pelo nome interno do client_npcs.xml (mesmo nome sem "Island_" e sem o nível): 16 de ilha, 26 genéricas.
Edita as duas árvores (spawns/Npcs/800040000_Tiamaranta_Mesa.xml); spawn sem spot nenhum sai inteiro com o comentário.
Rodar depois do corrige_spawns_mapa.py (a posição já tem de estar no andar certo).
"""
import os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CLIENTE = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data")
ARQS = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "spawns", "Npcs", "800040000_Tiamaranta_Mesa.xml"),
        os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "spawns", "Npcs", "800040000_Tiamaranta_Mesa.xml")]


def genericas():
    """id genérico -> id de ilha."""
    t = open(os.path.join(CLIENTE, "npcs", "client_npcs.xml"), encoding="utf-8", errors="replace").read()
    nm = {int(i): n for i, n in re.findall(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", t)}
    base = lambda n: re.sub(r"_\d+_(An|Ae|Dr|Ad)?$", "", n)
    ilha = {base(n): i for i, n in nm.items() if n.startswith("LDF4b_Island_")}
    out = {}
    for i, n in nm.items():
        if n.startswith("LDF4b_") and not n.startswith("LDF4b_Island_"):
            k = base(n).replace("LDF4b_", "LDF4b_Island_", 1)
            if k in ilha:
                out[i] = ilha[k]
    return out


def subzonas():
    t = open(os.path.join(CLIENTE, "world", "client_world_ldf4b.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for b in re.findall(r"(?s)<subzone>(.*?)</subzone>", t):
        n = re.search(r"<name>([^<]+)</name>", b).group(1)
        if n.startswith("LDF4b_SZ_Island_"):
            pts = [(float(x), float(y)) for x, y in re.findall(r"<x>([-\d.]+)</x>\s*<y>([-\d.]+)</y>", b)]
            out[n] = (pts, float(re.search(r"<bottom>([-\d.]+)</bottom>", b).group(1)), float(re.search(r"<top>([-\d.]+)</top>", b).group(1)))
    return out


def dentro(pts, x, y):
    c, j = False, len(pts) - 1
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def ilha_de(SZ, x, y, z):
    for n, (p, b, t) in SZ.items():
        if b <= z <= t and dentro(p, x, y):
            return n
    return None


def processa(texto, gen, SZ, rel):
    nl = "\r\n" if "\r\n" in texto else "\n"
    edits = []
    for sm in re.finditer(r'(?s)<spawn\b[^>]*npc_id="(\d+)"[^>]*>(.*?)</spawn>', texto):
        npc = int(sm.group(1))
        if npc not in gen:
            continue
        spots = list(re.finditer(r"[ \t]*<spot\b[^>]*>[ \t]*\r?\n", sm.group(2)))
        sai = []
        for sp in spots:
            g = lambda k: float(re.search(r'\b%s="([-\d.eE]+)"' % k, sp.group(0)).group(1))
            z = ilha_de(SZ, g("x"), g("y"), g("z"))
            if z:
                sai.append(sp)
                rel[(npc, z)] = rel.get((npc, z), 0) + 1
        if not sai:
            continue
        if len(sai) == len(spots):
            ini = texto.rfind(nl, 0, sm.start()) + len(nl)
            ant = texto.rfind(nl, 0, ini - len(nl)) + len(nl)
            if texto[ant:ini].strip().startswith("<!--"):        # comentário com o nome logo acima
                ini = ant
            fim = texto.index(nl, sm.end()) + len(nl)
            edits.append((ini, fim))
        else:
            edits += [(sm.start(2) + s.start(), sm.start(2) + s.end()) for s in sai]
    for i, f in sorted(edits, reverse=True):
        texto = texto[:i] + texto[f:]
    return texto


def main():
    gen, SZ = genericas(), subzonas()
    print(f"genéricas com versão de ilha: {len(gen)}; subzonas de ilha: {sorted(SZ)}")
    saidas = []
    for arq in ARQS:
        txt = open(arq, encoding="utf-8", newline="").read()
        rel = {}
        novo = processa(txt, gen, SZ, rel)
        saidas.append(novo)
        print(arq[-75:], "spots removidos:", sum(rel.values()))
        for (n, z), c in sorted(rel.items()):
            print(f"   {c:4d}  {n} -> ilha {gen[n]}  ({z})")
        if "--aplica" in sys.argv and novo != txt:
            open(arq, "w", encoding="utf-8", newline="").write(novo)
    if len(set(saidas)) > 1:
        print("ATENÇÃO: as árvores ficaram diferentes")


if __name__ == "__main__":
    main()
