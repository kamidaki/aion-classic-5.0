"""Ataque de mob sem medicao pela grade oficial (hpgauge) -> <stats attack="..."> no npc_templates.

Grade oficial: hpgauge_level do client_npcs, convertido pela tabela do Game.dll EU 5.0 (RVA 0x1059F60, codigo em
0x6C58EA: primeira chave >= hpgauge). E o "Normal / Elite / Maximum / Legendary + Level" da janela de alvo; conferido
em 7 mobs em 29/10. O rating/rank do npc_templates nao e oficial (quase tudo NORMAL/DISCIPLINED).

Fator da grade = mediana de (ataque medido / curva base do nivel) nos mobs medidos por fix_50_npc_ataque.py
(npc_ataque_medido_50.json), com a forma de nivel do NpcStatCalculation (-0,0007n^3 + 0,1n^2 + 5,3n) sem rating/rank.
So entram grades com MIN_MEDIDOS ou mais mobs medidos de nivel >= 10 (template de nivel 1 dos Reian Basrasa e erro
conhecido). Alvo: npc_type Monster no cliente, sem attack medido. Decisao de 29/10: todos os niveis, embora todo
fator venha de mobs ~65.

Os ids gravados ficam em npc_ataque_grade_50.json; rodar de novo recalcula esses mesmos mobs (e os novos), nunca
mexe num medido nem num attack que ja existia antes deste script (exceto as familias de SOBRESCREVE_TITULO).

FATOR_PROVISORIO: grade sem MIN_MEDIDOS mobs medidos, com fator de poucos golpes oficiais; sai quando houver medicao.
  Maximum L1 3,96 = Fragment of Wrath 220705 (nivel 70), 2 golpes normais (2.043 e 2.443) -> ataque 2.166-2.748,
  meio 2.457 / curva 620,9 (29/10).
SOBRESCREVE_TITULO: familia em que o attack antigo do template foi desmentido pela captura de um membro. Mutantes
  das ilhas de Tiamaranta (titulo 345836): template 638, oficial 2.166-2.748 no Fragment of Wrath (29/10).

Uso:
    python fix_50_npc_ataque_grade.py            # so mostra
    python fix_50_npc_ataque_grade.py --aplicar  # grava nas duas arvores
"""
import json, os, re, statistics as st, sys
from collections import Counter, defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CLI = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data", "npcs", "client_npcs.xml")
ARVORES = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "npcs", "npc_templates.xml"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data", "npcs", "npc_templates.xml"),
]
MEDIDOS = os.path.join(AQUI, "npc_ataque_medido_50.json")
GRAVADOS = os.path.join(AQUI, "npc_ataque_grade_50.json")
MIN_MEDIDOS = 3
FATOR_PROVISORIO = {"Maximum L1": 3.96}
SOBRESCREVE_TITULO = {"345836"}

TABELA = [(2, "Normal", 1), (3, "Normal", 2), (4, "Normal", 4), (9, "Normal", 5), (10, "Elite", 1), (11, "Elite", 2),
          (12, "Elite", 3), (13, "Elite", 4), (19, "Elite", 5), (20, "Maximum", 1), (21, "Maximum", 2), (25, "Maximum", 3),
          (26, "Legendary", 1), (27, "Legendary", 2), (32, "Legendary", 3)]


def grade(hpgauge):
    for chave, gr, lv in TABELA:
        if hpgauge <= chave:
            return f"{gr} L{lv}"
    return None


def base(nivel):
    return -0.0007 * nivel ** 3 + 0.1 * nivel ** 2 + 5.3 * nivel


def le_cliente():
    cli = {}
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", open(CLI, encoding="utf-8").read(), re.S):
        b = m.group(1)
        i, h, t = re.search(r"<id>(\d+)<", b), re.search(r"<hpgauge_level>(\d+)<", b), re.search(r"<npc_type>([^<]*)<", b)
        if i and h:
            cli[i.group(1)] = (int(h.group(1)), t.group(1) if t else "")
    return cli


BLOCO = re.compile(r'(<npc_template npc_id="(\d+)"[^>]*?(?<!/)>)(.*?</npc_template>)', re.S)


def niveis(txt):
    return {m.group(2): int(re.search(r'\blevel="(\d+)"', m.group(1)).group(1)) for m in BLOCO.finditer(txt)}


def fatores(txt, cli, medidos):
    nv, por = niveis(txt), defaultdict(list)
    for i, m in medidos.items():
        if i in cli and nv.get(i, 0) >= 10:
            por[grade(cli[i][0])].append(m["attack"] / base(nv[i]))
    fator = {g: st.median(v) for g, v in por.items() if len(v) >= MIN_MEDIDOS}
    for g, f in FATOR_PROVISORIO.items():
        fator.setdefault(g, f)
    return fator, por


def aplica(caminho, cli, medidos, fator, ja_gravados):
    txt = open(caminho, encoding="utf-8", newline="").read()  # preserva CRLF
    gravados, pulados = {}, Counter()

    def troca(m):
        abre, nid, resto = m.group(1), m.group(2), m.group(3)
        if nid in medidos or nid not in cli or cli[nid][1] != "Monster":
            return m.group(0)
        g = grade(cli[nid][0])
        if g not in fator:
            return m.group(0)
        st_m = re.search(r"<stats\b[^>]*?/?>", resto)
        if not st_m:
            pulados["sem <stats>"] += 1
            return m.group(0)
        tag = st_m.group(0)
        tem = re.search(r'\battack="(\d+)"', tag)
        titulo = re.search(r'title_id="(\d+)"', abre)
        livre = titulo and titulo.group(1) in SOBRESCREVE_TITULO
        if tem and int(tem.group(1)) and nid not in ja_gravados and not livre:
            pulados["attack anterior a este script"] += 1
            return m.group(0)
        nivel = int(re.search(r'\blevel="(\d+)"', abre).group(1))
        atk = max(1, round(base(nivel) * fator[g]))
        nova = re.sub(r'\battack="\d+"', f'attack="{atk}"', tag) if tem else tag.replace("<stats", f'<stats attack="{atk}"', 1)
        gravados[nid] = {"attack": atk, "grade": g, "nivel": nivel}
        return abre + resto[:st_m.start()] + nova + resto[st_m.end():]

    novo = BLOCO.sub(troca, txt)
    return novo, gravados, pulados


if __name__ == "__main__":
    cli = le_cliente()
    medidos = json.load(open(MEDIDOS, encoding="utf-8"))["medidos"]
    ja = set(json.load(open(GRAVADOS, encoding="utf-8"))) if os.path.exists(GRAVADOS) else set()
    fator, por = fatores(open(ARVORES[0], encoding="utf-8").read(), cli, medidos)
    for g, v in sorted(por.items()):
        print(f"{g:13} medidos {len(v):2}  " + (f"fator {fator[g]:.2f}" + (" (provisorio)" if len(v) < MIN_MEDIDOS else "") if g in fator else "fica na curva (poucos medidos)"))
    for g in FATOR_PROVISORIO:
        if g not in por:
            print(f"{g:13} medidos  0  fator {fator[g]:.2f} (provisorio)")
    todos = {}
    for arv in ARVORES:
        novo, gravados, pulados = aplica(arv, cli, medidos, fator, ja)
        print(f"{arv}: {len(gravados)} mobs" + (f", pulados {dict(pulados)}" if pulados else ""))
        if "--aplicar" in sys.argv:
            open(arv, "w", encoding="utf-8", newline="").write(novo)
        todos.update(gravados)
    if "--aplicar" in sys.argv:
        json.dump(dict(sorted(todos.items())), open(GRAVADOS, "w", encoding="utf-8"), indent=0)
        print("lista ->", GRAVADOS)
