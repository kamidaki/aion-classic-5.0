#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_50_land_of_shadows_mobs.py

Cria os templates dos mobs da Land of Shadows (IDTutorialQ, 390000000) que o servidor nao tinha: 224300..224320 e os
tres bosses 224333..224335. Todos aparecem no S_PUT_NPC da captura oficial subida-1-60-2026-08-28.pcapng; sem template
a instancia ficava sem nenhum mob.

De onde vem cada campo
  captura (fix_50_npc_captura.colhe, todas as capturas)   level, maxHp e title_id -- constantes por npcId
  cliente (client_npcs.xml, tabelas do rebuild_50_npc_templates)
                                                          name, name_id, type, race, srange, arange, attack_speed,
                                                          hpgauge, height, speeds e bound_radius
  cliente, direto                                         tribe = tribe do cliente em maiusculas (IDTUTORIALQ_MONSTER,
                                                          criada pelo fix_50_land_of_shadows_tribos.py); o ai_name
                                                          (IDTutorialQ_Monster_01/_02 e o de cada boss) nao existe no
                                                          servidor: vira aggressive, a unica ai que testa aggro por tribo
                                                          (CreatureEventHandler.checkAggro)
  gabarito (NPCs de npc_type Monster cujo name_id bate com o cliente)
                                                          rank e rating pelo grau do nome interno (_An/_Ae/_Ah ou nenhum)
                                                          e pelo hpgauge_level do cliente, o par mais comum; sem par
                                                          exato, o hpgauge mais proximo do mesmo grau. Medido em
                                                          23/09: (nenhum, 3) -> DISCIPLINED/NORMAL (632 de 717),
                                                          (Ah, 20) -> EXPERT/HERO; (Ah, 22) nao tem par e cai no
                                                          hpgauge vizinho do mesmo grau -> MASTER/HERO.
  group_drop                                              NONE (drop da instancia nao faz parte desta correcao)

Ajuste em template que ja existia
  224328 IDTutorialQ_Deco_Monster_01 (fogo de cenario, mesh FXMon_IDinfinity_Flower_Fire, ui_type noshow_skillnpc):
          ai noaction. Na captura ele nunca ataca: apanha uma vez do jogador (1.012,7 s), morre e reacende no mesmo ponto
          15 s depois lancando a 19389 em si (isso fica no LandOfShadowsInstance). Com a ai general ele revidava toda
          skill de area que o pegava.

Cada arvore e lida, montada, validada no npcs.xsd e gravada separadamente (os npc_templates.xml das duas divergem).

Uso:
    python create_50_land_of_shadows_mobs.py              (mostra e valida)
    python create_50_land_of_shadows_mobs.py --aplicar    (grava, com backup)
A pasta do cliente (a que contem data/ e Strings/) pode vir de --cliente ou de AION_CLIENT_XML_DIR; a das capturas,
de AION_CAPTURAS_DIR (padrao: a pasta oficial dentro do projeto).
"""

import argparse
import collections
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
ALVOS = [str(i) for i in list(range(224300, 224321)) + [224333, 224334, 224335]]
AI = "aggressive"
AJUSTES = {"224328": {"ai": "noaction"}}  # fogo de cenario: ver a docstring


def grau(nome):
    m = re.search(r"_(A[a-z])$", nome or "")
    return m.group(1) if m else "-"


def tabela_rank(srv, cli, n2id):
    t = collections.defaultdict(collections.Counter)
    for i, s in srv.items():
        d = cli.get(i)
        if not d or n2id.get((d.get("desc") or "").upper()) != s["attrs"].get("name_id"):
            continue
        if (d.get("npc_type") or "").lower() != "monster" or not d.get("hpgauge_level"):
            continue
        a = s["attrs"]
        if a.get("rank") and a.get("rating"):
            t[(grau(d.get("name")), int(d["hpgauge_level"]))][(a["rank"], a["rating"])] += 1
    return t


def rank_de(tab, d):
    g, h = grau(d.get("name")), int(d.get("hpgauge_level") or 0)
    if (g, h) in tab:
        return tab[(g, h)].most_common(1)[0][0]
    vizinhos = sorted((abs(hh - h), hh) for gg, hh in tab if gg == g)
    return tab[(g, vizinhos[0][1])].most_common(1)[0][0] if vizinhos else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    if os.environ.get("AION_CAPTURAS_DIR"):
        captura.CAPTURAS = os.environ["AION_CAPTURAS_DIR"]

    print("[1/3] Level, maxHp e titulo nas capturas oficiais...")
    medidas, _ = captura.colhe()
    print("[2/3] Lendo o cliente...")
    n2id, n2b = load_strings(args.cliente)
    cli = {d["id"]: d for d in iter_depth1(os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")) if d.get("id")}

    print("[3/3] Montando em cada arvore...")
    for nome_arv, base_dir in captura.ARVORES:
        caminho = os.path.join(base_dir, REL_XML)
        texto, srv = R.le_servidor(caminho)
        nl = "\r\n" if "\r\n" in texto else "\n"
        importador.NL = nl
        comuns = set(srv) & set(cli)
        bons = [i for i in comuns if n2id.get((cli[i].get("desc") or "").upper()) == srv[i]["attrs"].get("name_id")]
        tabs = {a: R.aprende(bons, srv, cli, a, c) for a, c in (("tribe", "tribe"), ("ai", "ai_name"),
                                                                ("race", "race_type"), ("type", "npc_type"))}
        base = R.bases_por_mesh(bons, srv, cli)
        tab_rank = tabela_rank(srv, cli, n2id)
        novos = {}
        print("   %s:" % nome_arv)
        for npc in ALVOS:
            if npc in srv:
                print("      %s ja tem template" % npc)
                continue
            d, m = cli.get(npc), medidas.get(int(npc))
            if not d or not m or len(m["lvl"]) != 1 or len(m["maxhp"]) != 1:
                sys.exit("%s sem cliente ou sem level/maxHp unico na captura" % npc)
            rr = rank_de(tab_rank, d)
            if not rr:
                sys.exit("%s sem rank/rating no gabarito para o grau %s" % (npc, grau(d.get("name"))))
            level, hp = next(iter(m["lvl"])), next(iter(m["maxhp"]))
            familia = {"rank": rr[0], "rating": rr[1], "group_drop": "NONE"}
            bloco = importador.render(npc, d, familia, level, hp, AI, {}, tabs, base, n2id, n2b).rstrip("\r\n")
            # tribo e ai do cliente nao existem nas tabelas aprendidas: ficam as do cliente / aggressive
            tribo = (d.get("tribe") or "").upper()
            bloco = re.sub(r' tribe="[^"]*"', "", bloco, count=1)
            bloco = re.sub(r' ai="[^"]*"', ' ai="%s"' % AI, bloco, count=1)
            bloco = bloco.replace(' height="', ' tribe="%s" height="' % tribo, 1) if ' height="' in bloco else \
                bloco.replace(' type="', ' tribe="%s" type="' % tribo, 1)
            if len(m.get("titulo", ())) == 1:
                bloco = bloco.replace(' level="', ' title_id="%s" level="' % next(iter(m["titulo"])), 1)
            novos[int(npc)] = bloco
            print("      %s %-44s lvl %d hp %d %s/%s" % (npc, d.get("name", "")[:44], level, hp, rr[0], rr[1]))
        novo = insere(texto, novos) if novos else texto
        if len(blocos(novo)) != len(blocos(texto)) + len(novos):
            sys.exit("ABORTADO: contagem de templates nao fecha em %s" % caminho)
        for npc, attrs in AJUSTES.items():
            m = re.search(r'<npc_template npc_id="%s"[^>]*>' % npc, novo)
            if not m:
                sys.exit("ABORTADO: %s sem template para ajustar" % npc)
            cab = m.group(0)
            for k, v in attrs.items():
                cab = re.sub(r' %s="[^"]*"' % k, ' %s="%s"' % (k, v), cab, count=1)
            if cab != m.group(0):
                novo = novo[:m.start()] + cab + novo[m.end():]
                print("      %s ajustado: %s" % (npc, attrs))
        if novo == texto:
            continue
        from lxml import etree
        xsd = etree.XMLSchema(etree.parse(os.path.join(base_dir, REL_XSD)))
        if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
            sys.exit("ABORTADO: %s nao valida no npcs.xsd: %s" % (caminho, xsd.error_log.last_error))
        print("      +%d templates, valida no npcs.xsd" % len(novos))
        if novos:
            print("      exemplo: " + re.sub(r"\s+", " ", novos[min(novos)])[:400])
        if args.aplicar:
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
            print("      gravado")
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
