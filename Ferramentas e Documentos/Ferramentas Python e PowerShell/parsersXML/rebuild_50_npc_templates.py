#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_npc_templates.py

Conserta os npc_templates cujo npc_id passou a significar outro NPC na 5.0. A NCSoft reaproveitou ids, entao o
template herdado da 4.8 descreve outra criatura: nome, tribo, IA, alcances e tamanho do bicho errado.

Identidade: o npc_id e o mesmo NPC se o name_id do servidor for o id da string que o desc do cliente aponta.
Divergiu, o template e reconstruido -- nos campos que o cliente prova.

O que vem do cliente (acerto medido nos NPCs cujo id NAO mudou, que servem de gabarito):
    name, name_id <- desc                         100%  (por construcao)
    arange        <- attack_range                 100%
    type          <- npc_type                    99.9%  tabela aprendida do gabarito
    race          <- race_type                   99.8%  tabela aprendida
    speeds        <- move_speed_*                97-99%
    tribe         <- tribe                       97.6%  tabela aprendida
    srange        <- sensory_range               97.5%
    attack_speed  <- attack_delay                92.0%
    ai            <- ai_name                     90.9%  tabela aprendida
    height        <- base(mesh) x scale/100      90.8%
    bound_radius  <- base(mesh) x scale/100      88-90%
As tabelas de enum sao aprendidas do gabarito de proposito: so produzem valor que ja existe no servidor, entao o
resultado nunca quebra o npcs.xsd.

O que NAO vem: level, maxHp, rank, rating e group_drop nao existem em arquivo nenhum do cliente. Estimar foi testado
e reprovado (level por familia/mesh/numero no nome: 43-67%; maxHp por level+rating+rank: 37%), entao esses campos e os
filhos herdados (equipment, talk_info) ficam como estao e saem no relatorio, comecando pelos que tem spawn no mundo.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_npc_templates.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra, valida, gera relatorio)
    python rebuild_50_npc_templates.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import ATTR_RE, DEFAULT_CLIENT_DIR, esc, iter_depth1, load_strings, low  # noqa: E402

REL_XML = "npcs/npc_templates.xml"
REL_XSD = "npcs/npcs.xsd"
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_npc_templates_50.txt")
NL = "\r\n"
BLOCK_RE = re.compile(r"\t<npc_template\b([^>]*?)(/>|>(.*?)</npc_template>)", re.S)
SPEEDS = (("walk", "move_speed_normal_walk"), ("group_walk", "art_org_move_speed_normal_walk"),
          ("run", "move_speed_normal_run"), ("run_fight", "move_speed_combat_run"),
          ("group_run_fight", "art_org_speed_combat_run"))
EIXOS = ("front", "side", "upper")
COMBATE = ("monster", "abyss_guard")


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def limpa(v):
    """0.30000001 -> 0.3, 2.0 -> 2 (e assim que o arquivo do servidor escreve)."""
    s = f"{round(v, 4):.4f}"
    return (s.rstrip("0").rstrip(".") or "0")


def aprende(bons, srv, cli, attr, campo):
    """Tabela valor-do-cliente -> valor-do-servidor, pelo que e mais comum no gabarito."""
    tab = collections.defaultdict(collections.Counter)
    for i in bons:
        a, b = srv[i]["attrs"].get(attr), cli[i].get(campo)
        if a and b:
            tab[b.lower()][a] += 1
    return {k: v.most_common(1)[0][0] for k, v in tab.items()}


def bases_por_mesh(bons, srv, cli):
    """Tamanho do modelo com scale 100, por mesh: height e bound_radius escalam com o scale do cliente."""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for i in bons:
        s, mesh = fnum(cli[i].get("scale")), cli[i].get("mesh")
        if not s or not mesh:
            continue
        alvos = [("height", fnum(srv[i]["attrs"].get("height")))]
        alvos += [(e, fnum(srv[i]["br"].get(e))) for e in EIXOS]
        for chave, v in alvos:
            if v:
                acc[mesh][chave].append(v / (s / 100))
    return {m: {k: statistics.median(v) for k, v in d.items() if len(v) >= 2} for m, d in acc.items()}


def le_servidor(path):
    text = open(path, encoding="utf-8").read()
    srv = {}
    for m in BLOCK_RE.finditer(text):
        attrs = dict(ATTR_RE.findall(m.group(1)))
        if not attrs.get("npc_id"):
            continue
        inner = m.group(3) or ""
        br = re.search(r"<bound_radius\b([^>]*)/>", inner)
        srv[attrs["npc_id"]] = {"attrs": attrs, "ordem": ATTR_RE.findall(m.group(1)), "inner": inner,
                                "head": m.span(1), "head_txt": m.group(1), "corpo": m.span(2),
                                "br": dict(ATTR_RE.findall(br.group(1))) if br else {}}
    return text, srv


def spawnados(base_dir):
    ids = set()
    for raiz, _, arqs in os.walk(os.path.join(base_dir, "spawns")):
        for a in arqs:
            if a.endswith(".xml"):
                with open(os.path.join(raiz, a), encoding="utf-8", errors="replace") as f:
                    ids.update(re.findall(r'npc_id="(\d+)"', f.read()))
    return ids


def novos_atributos(d, tabs, base):
    """So o que o cliente prova. level, rank, rating e group_drop ficam como estao."""
    out = {}
    for attr, campo in (("tribe", "tribe"), ("ai", "ai_name"), ("race", "race_type"), ("type", "npc_type")):
        v = tabs[attr].get(low(d, campo))
        if v:
            out[attr] = v
    for attr, campo in (("arange", "attack_range"), ("srange", "sensory_range"),
                        ("attack_speed", "attack_delay"), ("hpgauge", "hpgauge_level")):
        v = fnum(d.get(campo))
        if v is not None:
            out[attr] = str(int(round(v)))
    sc, mesh = fnum(d.get("scale")), d.get("mesh")
    if sc and mesh and base.get(mesh, {}).get("height"):
        out["height"] = limpa(base[mesh]["height"] * sc / 100)
    return out


def render_head(s, novos):
    pares, vistos = [], set()
    for k, v in s["ordem"]:
        vistos.add(k)
        pares.append((k, novos.get(k, v)))
    pares += [(k, v) for k, v in novos.items() if k not in vistos]
    # preserva o espacamento do original: quem fecha em "/>" tem espaco no fim, quem fecha em ">" nao
    fim = " " if s["head_txt"].endswith((" ", "\t")) else ""
    return " " + " ".join('{}="{}"'.format(k, esc(v)) for k, v in pares) + fim


def render_inner(s, d, base):
    """Troca <speeds> e <bound_radius>; nao encosta em <stats maxHp>, <equipment> nem <talk_info>."""
    inner = s["inner"]
    vel = []
    for sk, ck in SPEEDS:
        v = fnum(d.get(ck))
        if v is not None:
            vel.append((sk, limpa(v)))
    if vel:
        novo = "<speeds " + " ".join('{}="{}"'.format(k, v) for k, v in vel) + " />"
        if re.search(r"<speeds\b[^>]*/>", inner):
            inner = re.sub(r"<speeds\b[^>]*/>", lambda _m: novo, inner, count=1)
        else:
            st = re.search(r"(\t+)<stats\b([^>]*)/>", inner)
            if st:
                tab = st.group(1)
                bloco = tab + "<stats" + st.group(2) + ">" + NL + tab + "\t" + novo + NL + tab + "</stats>"
                inner = inner[:st.start()] + bloco + inner[st.end():]
    sc, mesh = fnum(d.get("scale")), d.get("mesh")
    b = base.get(mesh or "", {})
    if sc and all(e in b for e in EIXOS) and re.search(r"<bound_radius\b[^>]*/>", inner):
        novo = "<bound_radius " + " ".join('{}="{}"'.format(e, limpa(b[e] * sc / 100)) for e in EIXOS) + " />"
        inner = re.sub(r"<bound_radius\b[^>]*/>", lambda _m: novo, inner, count=1)
    return inner


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + npcs_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo cliente e servidor...")
    n2id, n2b = load_strings(args.cliente)
    cli = {d["id"]: d for d in iter_depth1(npcs_xml) if d.get("id")}
    text, srv = le_servidor(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML))
    comuns = set(srv) & set(cli)

    def mesmo(i):
        return n2id.get((cli[i].get("desc") or "").upper()) == srv[i]["attrs"].get("name_id")

    bons = [i for i in comuns if mesmo(i)]
    trocados = sorted((i for i in comuns if not mesmo(i)), key=int)
    print("   cliente: {} | servidor: {} | mesmo NPC: {} | id trocado: {} | so no cliente: {}".format(
        len(cli), len(srv), len(bons), len(trocados), len(set(cli) - set(srv))))

    print("2. Aprendendo as tabelas do gabarito...")
    tabs = {a: aprende(bons, srv, cli, a, c) for a, c in (("tribe", "tribe"), ("ai", "ai_name"),
                                                          ("race", "race_type"), ("type", "npc_type"))}
    base = bases_por_mesh(bons, srv, cli)
    print("   " + " | ".join("{}: {}".format(a, len(t)) for a, t in tabs.items())
          + " | meshes com base: {}".format(len(base)))

    print("3. Reconstruindo os trocados...")
    no_mundo = spawnados(backup_manager.SERVER_DATA_DIR)
    edits, gen, linhas = [], collections.Counter(), []
    for i in trocados:
        d, s = cli[i], srv[i]
        chave = (d.get("desc") or "").upper()
        novos = novos_atributos(d, tabs, base)
        if chave in n2id:
            novos["name_id"] = n2id[chave]
        if chave in n2b:
            novos["name"] = n2b[chave]
        for k in novos:
            gen[k] += 1
        edits.append((s["head"][0], s["head"][1], render_head(s, novos)))
        inner = render_inner(s, d, base)
        if inner != s["inner"]:
            gen["speeds/bound_radius"] += 1
            edits.append((s["corpo"][0], s["corpo"][1], ">" + inner + "</npc_template>"))
        hp = re.search(r'maxHp="(\d+)"', s["inner"])
        herdado = ",".join(t for t in ("equipment", "talk_info") if "<" + t in s["inner"])
        linhas.append((i, i in no_mundo, d.get("npc_type") or "?", s["attrs"].get("name", ""),
                       novos.get("name", "?"), s["attrs"].get("level", "?"),
                       hp.group(1) if hp else "?", herdado))
    print("   campos gerados: {}".format(dict(gen.most_common())))

    out, pos = [], 0
    for a, b, novo in sorted(edits):
        out.append(text[pos:a])
        out.append(novo)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo_texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    if not linhas:  # rodar de novo depois de aplicar nao acha mais trocado: nao apagar o relatorio bom
        print("   nada a reconstruir; relatorio anterior mantido.")
        return

    linhas.sort(key=lambda r: (not r[1], r[2].lower() not in COMBATE, int(r[0])))
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Templates de NPC com id trocado na 5.0: identidade corrigida pelo cliente, level/maxHp mantidos.\n")
        f.write("level, maxHp, rank, rating e group_drop nao existem no cliente e nao sao estimaveis (ver docstring).\n")
        f.write("A coluna herdado marca filhos que sobraram do NPC antigo e tambem precisam de revisao.\n")
        f.write("Ordem: primeiro os que tem spawn no mundo, mobs de combate na frente.\n\n")
        f.write("{:>8}  {:5}  {:12}  {:>5}  {:>8}  {:20}  nome antigo -> novo\n".format(
            "npc_id", "spawn", "tipo", "level", "maxHp", "herdado"))
        for i, sp, tipo, antigo, novo, lvl, hp, herd in linhas:
            f.write("{:>8}  {:5}  {:12}  {:>5}  {:>8}  {:20}  {} -> {}\n".format(
                i, "SIM" if sp else "-", tipo[:12], lvl, hp, herd, antigo, novo))
    prio = sum(1 for r in linhas if r[1] and r[2].lower() in COMBATE)
    print("   relatorio: {} ({} linhas, {} mobs de combate spawnados no topo)".format(RELATORIO, len(linhas), prio))

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for b in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(b, REL_XML)
        with open(p, "wb") as f:
            f.write(novo_texto.encode("utf-8"))
        print("Gravado: " + p)


if __name__ == "__main__":
    main()
