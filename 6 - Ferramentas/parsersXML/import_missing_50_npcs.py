#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_missing_50_npcs.py

Cria npc_templates para NPCs que existem no cliente 5.0 e nao existem no servidor. Importa **so os ids listados
em ALVOS**, de proposito: dos 2405 NPCs so-do-cliente, a maioria e conteudo de cerco/instancia que precisa de
decisao caso a caso, entao esse arquivo e a lista explicita do que ja foi decidido entrar.

De onde vem cada campo:
  cliente          name, name_id, tribe, ai, type, race, arange, srange, attack_speed, hpgauge, height,
                   speeds e bound_radius -- pelas mesmas tabelas medidas do rebuild_50_npc_templates.
  ALVOS            level e maxHp, que nao existem em arquivo nenhum do cliente.
  familia (irmas)  rank, rating e o que a tabela do cliente nao resolve (o ai_name desses bosses e unico
                   por NPC, entao nenhuma tabela aprendida tem entrada para ele).

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python import_missing_50_npcs.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e valida)
    python import_missing_50_npcs.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
"""

import argparse
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager as bm  # noqa: E402
import rebuild_50_npc_templates as R  # noqa: E402
from rebuild_50_item_templates import iter_depth1, load_strings  # noqa: E402

REL_XML = "npcs/npc_templates.xml"
REL_XSD = "npcs/npcs.xsd"
NL = "\r\n"

# npc_id -> (level, maxHp, npc_irmao_para_rank_rating, ai_de_fallback, ajustes)
# level/maxHp medidos no servidor oficial e informados pelo usuario em 2026-09-12; o cliente nao tem esses campos.
# O irmao e um NPC da mesma familia que ja existe no servidor: 259200/259400/259600 sao os tiers das mesmas
# Hearts dos Boss_1_GradeN; 281418 e um "invisible ctrl" equivalente aos dois NPCs de efeito do Fissure.
# `ajustes` corrige o que herdar do irmao erraria -- o irmao e uma amostra de um, nao uma regra.
ALVOS = {
    "221254": (55, 1269032, "259200", "aggressive", {}),  # ldf4b_4021_Boss_1_Grade1 - Gravity Incarnate
    "221255": (55, 1269032, "259400", "aggressive", {}),  # ldf4b_4031_Boss_1_Grade3 - Wrath Incarnate
    "221256": (55, 1269032, "259600", "aggressive", {}),  # ldf4b_4041_Boss_1_Grade2 - Petrification Incarnate
    # Os dois de efeito nao sao clicaveis (cursor_type=none no cliente), entao nao droparn: 34 dos 40
    # invisiveis nao-clicaveis do servidor usam NONE, e o irmao 281418 e um dos 6 fora do padrao.
    "220832": (75, 317470, "281418", "general", {"group_drop": "NONE"}),   # Tiamat_Crack_EarthQuake_invisible
    "220834": (75, 317470, "281418", "general", {"group_drop": "NONE"}),   # Tiamat_Crack_BrokenGround_invisible
}
# Atributos que nenhuma fonte do cliente cobre: saem do irmao da mesma familia, salvo ajuste explicito.
DA_FAMILIA = ("rank", "rating", "race", "group_drop")


def render(npc_id, d, irmao, level, hp, ai_fallback, ajustes, tabs, base, n2id, n2b):
    chave = (d.get("desc") or "").upper()
    a = [("npc_id", npc_id), ("level", str(level))]
    if chave in n2b:
        a.append(("name", n2b[chave]))
    if chave in n2id:
        a.append(("name_id", n2id[chave]))

    doCliente = R.novos_atributos(d, tabs, base)
    doCliente.setdefault("ai", ai_fallback)
    for k in ("height", "tribe", "type", "ai", "srange", "arange", "attack_speed", "hpgauge"):
        if k in doCliente:
            a.append((k, doCliente[k]))
    for k in DA_FAMILIA:
        v = ajustes.get(k, irmao.get(k))
        if v:
            a.append((k, v))

    cabeca = "\t<npc_template " + " ".join('{}="{}"'.format(k, R.esc(v)) for k, v in a) + ">"
    filhos = []
    vel = [(sk, R.limpa(v)) for sk, ck in R.SPEEDS if (v := R.fnum(d.get(ck))) is not None]
    if vel:
        filhos.append("\t\t<stats maxHp=\"{}\">".format(hp))
        filhos.append("\t\t\t<speeds " + " ".join('{}="{}"'.format(k, v) for k, v in vel) + " />")
        filhos.append("\t\t</stats>")
    else:
        filhos.append("\t\t<stats maxHp=\"{}\" />".format(hp))
    sc, mesh = R.fnum(d.get("scale")), d.get("mesh")
    b = base.get(mesh or "", {})
    if sc and all(e in b for e in R.EIXOS):
        filhos.append("\t\t<bound_radius " + " ".join('{}="{}"'.format(e, R.limpa(b[e] * sc / 100)) for e in R.EIXOS) + " />")
    return cabeca + NL + NL.join(filhos) + NL + "\t</npc_template>" + NL


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", R.DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + npcs_xml)

    print("1. Lendo cliente e servidor...")
    n2id, n2b = load_strings(args.cliente)
    cli = {d["id"]: d for d in iter_depth1(npcs_xml) if d.get("id")}
    text, srv = R.le_servidor(os.path.join(bm.SERVER_DATA_DIR, REL_XML))

    ja = [i for i in ALVOS if i in srv]
    if ja:
        print("   ja existem no servidor, nada a fazer para: " + ", ".join(ja))
    pendentes = [i for i in ALVOS if i not in srv]
    if not pendentes:
        print("Nada a importar.")
        return
    faltam_no_cliente = [i for i in pendentes if i not in cli]
    if faltam_no_cliente:
        sys.exit("Nao estao no cliente: " + ", ".join(faltam_no_cliente))

    print("2. Aprendendo as tabelas do gabarito...")
    comuns = set(srv) & set(cli)
    bons = [i for i in comuns if n2id.get((cli[i].get("desc") or "").upper()) == srv[i]["attrs"].get("name_id")]
    tabs = {a: R.aprende(bons, srv, cli, a, c) for a, c in (("tribe", "tribe"), ("ai", "ai_name"),
                                                            ("race", "race_type"), ("type", "npc_type"))}
    base = R.bases_por_mesh(bons, srv, cli)

    print("3. Montando os templates...")
    blocos = []
    for i in sorted(pendentes, key=int):
        level, hp, irmao_id, ai_fb, ajustes = ALVOS[i]
        irmao = srv.get(irmao_id, {}).get("attrs", {})
        if not irmao:
            sys.exit("NPC irmao {} nao existe no servidor; sem ele nao ha de onde tirar {}.".format(irmao_id, ", ".join(DA_FAMILIA)))
        bloco = render(i, cli[i], irmao, level, hp, ai_fb, ajustes, tabs, base, n2id, n2b)
        blocos.append((i, bloco))
        print("   " + re.sub(r"\s+", " ", bloco.strip())[:150])

    # insere cada um mantendo a ordem por npc_id
    novo = text
    for i, bloco in blocos:
        pos = [m.start() for m in re.finditer(r'\t<npc_template npc_id="(\d+)"', novo) if int(m.group(1)) > int(i)]
        corte = pos[0] if pos else novo.rindex("</npc_templates>")
        novo = novo[:corte] + bloco + novo[corte:]

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(bm.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo.encode("utf-8"))):
        for e in list(schema.error_log)[:10]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido. templates: {} -> {}".format(len(srv), len(srv) + len(blocos)))

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    sess = bm.init_backup_session("import_npcs_50")
    # rotulo explicito: as duas arvores terminam em "static_data", entao basename colide e uma cópia some
    for rotulo, b in (("GameServer", bm.SERVER_DATA_DIR), ("ProdutoFinal", bm.PRODUTO_FINAL_DATA_DIR)):
        p = os.path.join(b, REL_XML)
        shutil.copy2(p, os.path.join(sess, rotulo + "_npc_templates.xml"))
        with open(p, "wb") as f:
            f.write(novo.encode("utf-8"))
        print("Gravado: " + p)


if __name__ == "__main__":
    main()
