#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_50_npc_templates_captura.py

Cria npc_template para NPC que aparece nas capturas oficiais 5.0 e nao tem template em uma das arvores.

De onde vem cada campo (o mesmo metodo do import_missing_50_npcs.py, trocando o level/maxHp informado a mao pela
captura):
  cliente           name, name_id, tribe, ai, type, race, arange, srange, attack_speed, hpgauge, height, speeds e
                    bound_radius -- pelas tabelas aprendidas do rebuild_50_npc_templates, em cada arvore
  captura           level e maxHp (S_PUT_NPC, constantes por npcId)
  irmao             rank, rating, race e group_drop, que nenhum arquivo do cliente tem. O irmao e o template da mesma
                    arvore com o mesmo npc_type, a mesma tribo e o mesmo sufixo de grau no nome interno do cliente
                    (_An, _Ae, ...), no mesmo prefixo de mapa (LDF4b_...), com o npc_id mais proximo. Sem irmao, o
                    npcId fica de fora e sai no relatorio.
Depois deste, rodar o fix_50_npc_captura.py acerta titulo, equipamento, altura e raio pelo que a captura mediu.

Cada arvore e lida, montada e gravada separadamente (os npc_templates das duas nao sao iguais).

Uso:
    python create_50_npc_templates_captura.py --npc 220462 220582-220585 220717            (mostra)
    python create_50_npc_templates_captura.py --npc 220462 220582-220585 220717 --aplicar  (grava, com backup)
"""

import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402
import fix_50_npc_captura as captura  # noqa: E402
import import_missing_50_npcs as importador  # noqa: E402
import rebuild_50_npc_templates as R  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR, iter_depth1, load_strings  # noqa: E402
from sync_50_npc_templates_arvores import blocos, insere  # noqa: E402

REL_XML = os.path.join("npcs", "npc_templates.xml")
REL_XSD = os.path.join("npcs", "npcs.xsd")
importador.NL = "\n"                     # os dois npc_templates.xml estao em LF


def grau(nome):
    m = re.search(r"_(A[a-z])$", nome or "")
    return m.group(1) if m else None


def prefixo(nome):
    return (nome or "").split("_")[0]


def irmao_de(npc, cli, srv):
    d = cli[npc]
    candidatos = [i for i in srv if i in cli and i != npc
                  and (cli[i].get("npc_type") or "").lower() == (d.get("npc_type") or "").lower()
                  and (cli[i].get("tribe") or "").lower() == (d.get("tribe") or "").lower()
                  and grau(cli[i].get("name")) == grau(d.get("name"))
                  and prefixo(cli[i].get("name")) == prefixo(d.get("name"))]
    return min(candidatos, key=lambda i: abs(int(i) - int(npc)), default=None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npc", nargs="+", required=True, help="npcIds ou faixas (220582-220585)")
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()
    alvos = sorted(str(i) for i in _ids(args.npc))

    print("[1/3] Level e maxHp nas capturas oficiais...")
    medidas, _ = captura.colhe()
    print("[2/3] Lendo o cliente...")
    n2id, n2b = load_strings(args.cliente)
    cli = {d["id"]: d for d in iter_depth1(os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")) if d.get("id")}

    print("[3/3] Montando em cada arvore...")
    for nome_arv, base_dir in captura.ARVORES:
        caminho = os.path.join(base_dir, REL_XML)
        texto, srv = R.le_servidor(caminho)
        comuns = set(srv) & set(cli)
        bons = [i for i in comuns if n2id.get((cli[i].get("desc") or "").upper()) == srv[i]["attrs"].get("name_id")]
        tabs = {a: R.aprende(bons, srv, cli, a, c) for a, c in (("tribe", "tribe"), ("ai", "ai_name"),
                                                                ("race", "race_type"), ("type", "npc_type"))}
        base = R.bases_por_mesh(bons, srv, cli)
        novos = {}
        print("   %s:" % nome_arv)
        for npc in alvos:
            if npc in srv:
                print("      %s ja tem template" % npc)
                continue
            m = medidas.get(int(npc))
            if npc not in cli or not m or len(m["lvl"]) != 1 or len(m["maxhp"]) != 1:
                print("      %s FORA: %s" % (npc, "nao esta no cliente" if npc not in cli else "sem level/maxHp unico na captura"))
                continue
            irmao = irmao_de(npc, cli, srv)
            if not irmao:
                print("      %s FORA: sem irmao (npc_type/tribo/grau) na arvore" % npc)
                continue
            level, hp = next(iter(m["lvl"])), next(iter(m["maxhp"]))
            attrs_irmao = srv[irmao]["attrs"]
            bloco = importador.render(npc, cli[npc], attrs_irmao, level, hp, attrs_irmao.get("ai", "general"), {}, tabs, base, n2id, n2b)
            novos[int(npc)] = bloco.rstrip("\n")
            print("      %s %-36s level %d maxHp %d  irmao %s (%s)" % (npc, cli[npc].get("name", "")[:36], level, hp, irmao,
                                                                     cli[irmao].get("name")))
            print("         " + re.sub(r"\s+", " ", bloco.strip())[:220])
        if not novos:
            continue
        novo = insere(texto, novos)
        if len(blocos(novo)) != len(blocos(texto)) + len(novos):
            sys.exit("ABORTADO: contagem de templates nao fecha em %s" % caminho)
        from lxml import etree
        xsd = etree.XMLSchema(etree.parse(os.path.join(base_dir, REL_XSD)))
        if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
            sys.exit("ABORTADO: %s nao valida no npcs.xsd: %s" % (caminho, xsd.error_log.last_error))
        print("      +%d templates, valida no npcs.xsd" % len(novos))
        if args.aplicar:
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
            print("      gravado")
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


def _ids(argumentos):
    out = set()
    for a in argumentos:
        if "-" in a:
            i, f = map(int, a.split("-"))
            out.update(range(i, f + 1))
        else:
            out.add(int(a))
    return out


if __name__ == "__main__":
    main()
